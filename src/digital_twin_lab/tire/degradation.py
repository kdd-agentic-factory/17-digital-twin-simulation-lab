from typing import Dict, Any

class TireDegradationModel:
    """
    Implements the TireDegradationModel logic including spin, 
    temperature, TCS, and lap components.
    """

    def __init__(self, base_wear_rate: float = 0.01):
        """
        Args:
            base_wear_rate: Base wear rate per lap.
        """
        self.base_wear_rate = base_wear_rate

    def calculate_degradation(
        self, 
        current_wear: float, 
        temp_delta_c: float, 
        spin_delta_pct: float, 
        tcs_active: bool,
        lap_number: int
    ) -> float:
        """
        Calculates the new wear percentage.
        
        Args:
            current_wear: Current wear percentage (0.0 to 100.0).
            temp_delta_c: Change in temperature from optimal.
            spin_delta_pct: Change in spin percentage.
            tcs_active: Whether Traction Control System is active.
            lap_number: Current lap number.
            
        Returns:
            New wear percentage.
        """
        # 1. Base wear from lap
        wear_increment = self.base_wear_rate
        
        # 2. Temperature component
        # Higher temperature increases wear
        temp_impact = max(0.0, temp_delta_c * 0.005)
        
        # 3. Spin component
        # Higher spin increases wear
        spin_impact = max(0.0, spin_delta_pct * 0.01)
        
        # 4. TCS component
        # TCS reduces spin but might increase temperature/wear due to micro-slips
        tcs_impact = 0.0
        if tcs_active:
            # TCS reduces spin impact but adds a small penalty to wear due to friction
            spin_impact *= 0.5
            tcs_impact = 0.005
            
        # 5. Lap component (aging/cumulative effect)
        lap_factor = 1.0 + (lap_number * 0.001)
        
        total_increment = (wear_increment + temp_impact + spin_impact + tcs_impact) * lap_factor
        new_wear = current_wear + total_increment
        
        return min(100.0, new_wear)

    def estimate_degradation_delay(self, temp_delta_c: float, spin_delta_pct: float) -> int:
        """
        Estimates the delay in degradation in laps based on environmental factors.
        Based on simulator logic.
        """
        cooling_gain = max(0.0, -temp_delta_c) / 2.5
        traction_gain = max(0.0, -spin_delta_pct) / 6.0
        return round(min(5.0, cooling_gain + traction_gain))
