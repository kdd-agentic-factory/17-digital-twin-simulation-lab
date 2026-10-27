"""Monotone cubic Hermite linkage, matching PCHIP (Fritsch & Butland).

Continuous first derivative; second derivatives have explicit one-sided values
at knots. Coordinates are measured wheel and shock compression in metres.
"""
import math
from bisect import bisect_right

from .models import LinkageCurve, PhysicsResult
from .physics import spring_response


class LinkageInterpolator:
    def __init__(self, curve: LinkageCurve):
        self.curve = curve
        self.x = [p.wheel_m for p in curve.points]
        self.y = [p.shock_m for p in curve.points]
        h = [b-a for a,b in zip(self.x,self.x[1:])]
        d = [(b-a)/width for a,b,width in zip(self.y,self.y[1:],h)]
        def edge(h0,h1,d0,d1):
            value=((2*h0+h1)*d0-h0*d1)/(h0+h1)
            return 0.0 if value*d0 <= 0 else value
        slopes = [edge(h[0],h[1],d[0],d[1])]
        for i in range(1,len(self.x)-1):
            w1,w2=2*h[i]+h[i-1],h[i]+2*h[i-1]
            slopes.append((w1+w2)/(w1/d[i-1]+w2/d[i]))
        slopes.append(edge(h[-1],h[-2],d[-1],d[-2]))
        self.c = [(self.y[i],slopes[i],(3*d[i]-2*slopes[i]-slopes[i+1])/h[i],
                   (slopes[i]+slopes[i+1]-2*d[i])/(h[i]*h[i])) for i in range(len(h))]

    def at_shock(self, shock_m: float) -> dict:
        if not math.isfinite(shock_m):
            raise ValueError('Nonfinite shock displacement')
        epsilon = 8*max(math.ulp(shock_m),math.ulp(self.y[-1]))
        if shock_m < self.y[0]-epsilon or shock_m > self.y[-1]+epsilon:
            raise ValueError('Shock displacement outside measured linkage curve')
        shock_m = min(self.y[-1],max(self.y[0],shock_m))
        i = min(len(self.c)-1,max(0,bisect_right(self.y,shock_m)-1))
        knot = next((k for k in [i,i+1] if abs(self.y[k]-shock_m) <= epsilon), None)
        if knot is not None:
            wheel=self.x[knot]
            i=min(knot,len(self.c)-1)
        else:
            lo,hi=self.x[i],self.x[i+1]
            a,b,c,d=self.c[i]
            for _ in range(60):
                mid=(lo+hi)/2; t=mid-self.x[i]
                if ((d*t+c)*t+b)*t+a < shock_m: lo=mid
                else: hi=mid
                if hi-lo <= 1e-12: break
            wheel=(lo+hi)/2
        a,b,c,d=self.c[i]; t=wheel-self.x[i]
        q=b+2*c*t+3*d*t*t
        slope=2*c+6*d*t
        left=None
        if knot is not None and 0 < knot < len(self.x)-1:
            _,_,lc,ld=self.c[knot-1]
            left=2*lc+6*ld*(self.x[knot]-self.x[knot-1])
        if not all(math.isfinite(v) for v in [wheel,q,slope]) or q <= 0:
            raise ValueError('Nonpositive or invalid motion ratio')
        return {'wheel_m':wheel,'q':q,'dq_dz':slope,'left_dq_dz':left,'at_knot':knot is not None}

    def response(self,k_n_m:float,preload_m:float,shock_m:float) -> PhysicsResult:
        try:
            position=self.at_shock(shock_m)
        except ValueError as exc:
            return PhysicsResult(warnings=[str(exc)])
        result=spring_response(k_n_m,shock_m,preload_m,position['q'],position['dq_dz'])
        if not result.metrics: return result
        result.metrics.update(wheel_displacement_m=position['wheel_m'],motion_ratio=position['q'])
        left=position['left_dq_dz']
        result.metrics['wheel_rate_left_n_m']=result.metrics['wheel_rate_n_m']
        if left is not None:
            alt=spring_response(k_n_m,shock_m,preload_m,position['q'],left)
            if not alt.metrics: return alt
            result.metrics['wheel_rate_left_n_m']=alt.metrics['wheel_rate_n_m']
            result.warnings.append('second_derivative_has_one_sided_limits_at_knot')
        if self.curve.provenance == 'assumed': result.warnings.append('assumed:linkage_curve')
        if min(result.metrics['wheel_rate_n_m'],result.metrics['wheel_rate_left_n_m']) <= 0:
            result.warnings.append('nonpositive_tangent_wheel_rate')
        return result


def linkage_at_shock(curve: LinkageCurve,shock_m:float) -> dict:
    return LinkageInterpolator(curve).at_shock(shock_m)


def progressive_response(curve:LinkageCurve,k_n_m:float,preload_m:float,shock_m:float) -> PhysicsResult:
    return LinkageInterpolator(curve).response(k_n_m,preload_m,shock_m)
