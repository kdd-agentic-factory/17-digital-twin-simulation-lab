from __future__ import annotations

from digital_twin_lab.vehicle.engine_map_model import EngineMapModel
from digital_twin_lab.vehicle.lateral_model import LateralModel
from digital_twin_lab.vehicle.load_transfer_model import LoadTransferModel
from digital_twin_lab.vehicle.longitudinal_model import LongitudinalModel
from digital_twin_lab.vehicle.suspension_model import SuspensionModel


class SimplifiedVehicleModel:
    """Aggregates thin vehicle submodels into a stable simulation adapter."""

    def __init__(self) -> None:
        self.longitudinal = LongitudinalModel(157.0, 0.34, 0.58, 0.014)
        self.lateral = LateralModel(157.0, 92.0, 1.58)
        self.load_transfer = LoadTransferModel()
        self.suspension = SuspensionModel(18500.0, 1450.0)
        self.engine_map = EngineMapModel()

    def evaluate_setup_window(self, *, engine_map: str, rear_rebound: float, rear_ride_height_mm: float) -> dict[str, float]:
        engine = self.engine_map.get_map(engine_map)
        axle_loads = self.load_transfer.calculate_dynamic_axle_loads(total_mass_kg=157.0, acceleration_g=0.62)
        suspension_force = self.suspension.calculate_suspension_force(rear_ride_height_mm / 1000.0, rear_rebound / 100.0)
        return {
            "torque_factor": engine["torque_factor"],
            "thermal_delta_c": engine["thermal_delta_c"],
            "rear_axle_load_n": axle_loads["rear_axle_load_n"],
            "suspension_force_n": round(suspension_force, 3),
        }
