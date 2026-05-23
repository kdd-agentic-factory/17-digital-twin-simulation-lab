import math

class LongitudinalDynamics:
    """
    Handles longitudinal vehicle dynamics including acceleration and braking.
    """

    def __init__(self, mass: float, drag_coefficient: float, frontal_area: float, rolling_resistance: float):
        self.mass = mass
        self.cd = drag_coefficient
        self.area = frontal_area
        self.crr = rolling_resistance
        self.rho = 1.225  # air density in kg/m^3
        self.g = 9.81     # gravity in m/s^2

    def calculate_acceleration(self, engine_force: float, velocity: float) -> float:
        """
        Calculates acceleration given engine force and current velocity.
        
        Args:
            engine_force: Force applied by the engine in Newtons.
            velocity: Current velocity in m/s.
            
        Returns:
            Acceleration in m/s^2.
        """
        drag_force = 0.5 * self.rho * self.cd * self.area * (velocity ** 2)
        rolling_resistance_force = self.crr * self.mass * self.g
        
        net_force = engine_force - drag_force - rolling_resistance_force
        acceleration = net_force / self.mass
        return acceleration

    def calculate_braking_force(self, deceleration_g: float) -> float:
        """
        Calculates the braking force required for a given deceleration in g's.
        
        Args:
            deceleration_g: Deceleration in g's.
            
        Returns:
            Braking force in Newtons.
        """
        return deceleration_g * self.mass * self.g
