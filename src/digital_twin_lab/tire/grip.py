import math

class TireGripModel:
    """
    Handles friction and slip curve logic for tires.
    """

    def __init__(self, peak_mu: float = 1.5):
        """
        Args:
            peak_mu: The peak friction coefficient.
        """
        self.peak_mu = peak_mu

    def calculate_friction_coefficient(self, slip_ratio: float) -> float:
        """
        Calculates the friction coefficient for a given slip ratio using a simplified model.
        
        Args:
            slip_ratio: The slip ratio (usually between 0.0 and 0.2 for optimal grip).
            
        Returns:
            Friction coefficient.
        """
        # Simplified Pacejka-like curve: mu = peak_mu * sin(C * atan(B * slip))
        # Or simpler: mu = peak_mu * slip / (slip + K) for small slips, then decays.
        # Let's use a simple bell-shaped curve.
        
        abs_slip = abs(slip_ratio)
        
        if abs_slip < 0.001:
            return 0.0
            
        # Simple model: mu increases with slip, peaks, then decreases
        # peak at slip ~ 0.1
        peak_slip = 0.1
        mu = self.peak_mu * (abs_slip / peak_slip) * math.exp(-abs_slip / 0.1)
        
        return mu

    def calculate_lateral_force(self, slip_angle: float, normal_force: float, temp_factor: float = 1.0) -> float:
        """
        Calculates lateral force based on slip angle and normal force.
        
        Args:
            slip_angle: Slip angle in radians.
            normal_force: Normal force in Newtons.
            temp_factor: Multiplier for grip based on temperature.
            
        Returns:
            Lateral force in Newtons.
        """
        mu = self.calculate_friction_coefficient(slip_angle)
        return mu * normal_force * temp_factor
