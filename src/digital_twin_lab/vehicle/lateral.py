import math

class LateralDynamics:
    """
    Handles lateral vehicle dynamics including cornering and yaw.
    """

    def __init__(self, mass: float, inertia: float, grip_coefficient: float):
        self.mass = mass
        self.inertia = inertia
        self.mu = grip_coefficient
        self.g = 9.81

    def calculate_lateral_acceleration(self, velocity: float, radius: float) -> float:
        """
        Calculates lateral acceleration for a given velocity and corner radius.
        
        Args:
            velocity: Velocity in m/s.
            radius: Corner radius in meters.
            
        Returns:
            Lateral acceleration in m/s^2.
        """
        if radius <= 0:
            return 0.0
        return (velocity ** 2) / radius

    def calculate_max_cornering_velocity(self, radius: float) -> float:
        """
        Calculates the maximum velocity for a given radius before losing grip.
        
        Args:
            radius: Corner radius in meters.
            
        Returns:
            Max velocity in m/s.
        """
        if radius <= 0:
            return 0.0
        return math.sqrt(self.mu * self.g * radius)

    def calculate_yaw_rate(self, velocity: float, radius: float) -> float:
        """
        Calculates the yaw rate for a given velocity and corner radius.
        
        Args:
            velocity: Velocity in m/s.
            radius: Corner radius in meters.
            
        Returns:
            Yaw rate in rad/s.
        """
        if radius <= 0:
            return 0.0
        return velocity / radius
