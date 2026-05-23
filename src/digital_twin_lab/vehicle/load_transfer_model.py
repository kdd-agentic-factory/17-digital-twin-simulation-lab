from __future__ import annotations


class LoadTransferModel:
    """Very small longitudinal load-transfer estimator for the MVP."""

    def calculate_dynamic_axle_loads(
        self,
        *,
        total_mass_kg: float,
        acceleration_g: float,
        wheelbase_m: float = 1.4,
        cg_height_m: float = 0.55,
        static_front_ratio: float = 0.52,
    ) -> dict[str, float]:
        transfer_n = (total_mass_kg * 9.81) * acceleration_g * (cg_height_m / wheelbase_m)
        static_front_n = total_mass_kg * 9.81 * static_front_ratio
        static_rear_n = total_mass_kg * 9.81 - static_front_n
        return {
            "front_axle_load_n": round(static_front_n - transfer_n, 3),
            "rear_axle_load_n": round(static_rear_n + transfer_n, 3),
        }
