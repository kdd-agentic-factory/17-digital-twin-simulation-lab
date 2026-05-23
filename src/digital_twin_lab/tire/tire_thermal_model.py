from __future__ import annotations

from digital_twin_lab.tire.thermal import TireThermalModel


class TireThermalAdapter(TireThermalModel):
    """Spec-aligned adapter around the MVP thermal model."""


TireThermalModel = TireThermalAdapter
