class TireThermalModel:
    """
    Handles thermal dissipation and management logic for tires.
    """

    def __init__(self, heat_capacity: float = 500.0, dissipation_coeff: float = 0.1, ambient_temp: float = 25.0):
        """
        Args:
            heat_capacity: Thermal capacity of the tire (J/K).
            dissipation_coeff: Coefficient for heat dissipation (W/K).
            ambient_temp: Ambient temperature in Celsius.
        """
        self.heat_capacity = heat_capacity
        self.dissipation_coeff = dissipation_coeff
        self.ambient_temp = ambient_temp

    def update_temperature(self, current_temp: float, heat_generated: float, dt: float) -> float:
        """
        Updates the tire temperature based on heat generation and dissipation.
        
        Args:
            current_temp: Current temperature in Celsius.
            heat_generated: Heat generated (Watts).
            dt: Time step in seconds.
            
        Returns:
            New temperature in Celsius.
        """
        # Heat dissipation: Q_out = k * (T - T_ambient)
        heat_dissipated = self.dissipation_coeff * (current_temp - self.ambient_temp)
        
        # Net heat change: dQ = (Q_in - Q_out) * dt
        net_heat = (heat_generated - heat_dissipated) * dt
        
        # Temperature change: dT = dQ / Capacity
        delta_t = net_heat / self.heat_capacity
        
        return current_temp + delta_t

    def set_ambient_temperature(self, ambient_temp: float):
        self.ambient_temp = ambient_temp
