from __future__ import annotations

from digital_twin_lab.tire.degradation import TireDegradationModel


class TireDegradationAdapter(TireDegradationModel):
    """Spec-aligned adapter around the MVP tire degradation model."""


TireDegradationModel = TireDegradationAdapter
