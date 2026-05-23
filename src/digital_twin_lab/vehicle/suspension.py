class SuspensionDynamics:
    """
    Handles simplified suspension damping and geometry impact.
    """

    def __init__(self, spring_constant: float, damping_coefficient: float):
        self.k = spring_constant
        self.c = damping_coefficient

    def calculate_suspension_force(self, displacement: float, velocity: float) -> float:
        """
        Calculates the suspension force based on displacement and velocity.
        
        Args:
            displacement: Suspension compression/extension in meters.
            velocity: Velocity of the suspension movement in m/s.
            
        Returns:
            Force in Newtons.
        """
        spring_force = self.k * displacement
        damping_force = self.c * velocity
        return spring_force + damping_force

    def calculate_geometry_impact(self, compression_pct: float) -> float:
        """
        Simulates a simplified geometry impact (e.g., camber change) based on compression.
        
        Args:
            compression_pct: Percentage of suspension compression (0.0 to 1.0).
            
        Returns:
            A multiplier for lateral grip based on geometry impact.
        """
        # Simplified: as suspension compresses, camber might change, affecting grip.
        # Assuming optimal is at 0.5 compression.
        impact = 1.0 - abs(0.5 - compression_pct) * 0.2
        return max(0.8, impact)
