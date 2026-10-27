"""Immutable signal containers; no storage, identity or clock repair."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SignalSeries:
    times_s: list[float]
    values: list[float]
    unit: str
    sensor_id: str
    provenance: dict = field(default_factory=dict)


@dataclass(frozen=True)
class SignalQuality:
    status: str
    reasons: list[str]
    dt_s: float | None
    effective_fs_hz: float | None
    max_relative_jitter: float | None
    contiguous_intervals: list[tuple[float, float]]
    sample_count: int


@dataclass(frozen=True)
class BenchConditions:
    force_definition: str = 'total_measured'
    synchronization_reference: str = ''
    work_convention: str = ''
    temperature_c: float | None = None
    mounting: str = ''
    correction_method: str = ''


@dataclass(frozen=True)
class SpectralOptions:
    method: str = 'welch'
    nperseg: int = 256
    band_hz: tuple[float, float] = (1, 40)
    calibrated_bandwidth_hz: float | None = None
    antialias_reference: str = ''
