import numpy as np
import pytest
from digital_twin_lab.chassis.signal_models import SignalSeries,SpectralOptions
from digital_twin_lab.chassis.spectral import analyze_spectrum


def signal():
    t=np.arange(8192)/256
    return SignalSeries(t.tolist(),(np.sin(2*np.pi*16*t)+.5*np.sin(2*np.pi*32*t)).tolist(),'m','suspension_front',{})


def test_welch_multisine_bins_and_variance():
    r=analyze_spectrum(signal(),SpectralOptions(band_hz=(1,60)))
    assert r['dominant_frequency_hz']==pytest.approx(16,abs=1)
    assert np.trapezoid(r['density'],r['frequencies_hz'])==pytest.approx(.625,rel=.05)
    assert r['density_unit']=='m²/Hz'
    s=signal();s2=SignalSeries(s.times_s,[2*v for v in s.values],s.unit,s.sensor_id,{})
    r2=analyze_spectrum(s2,SpectralOptions(band_hz=(1,60)))
    assert max(r2['density'])==pytest.approx(4*max(r['density']))


def test_stft_localizes_burst_without_padding():
    s=signal();r=analyze_spectrum(s,SpectralOptions(method='stft',band_hz=(1,60)))
    assert min(r['times_s'])>=.5
    assert max(r['times_s'])<=s.times_s[-1]-.49
    assert len(r['density_matrix'])==len(r['frequencies_hz'])


def test_stft_keeps_last_complete_even_window():
    s=signal();s=SignalSeries(s.times_s[:1024],s.values[:1024],s.unit,s.sensor_id,{})
    r=analyze_spectrum(s,SpectralOptions(method='stft'))
    assert len(r['times_s'])==7
    assert r['times_s'][-1]==pytest.approx(896/256)


def test_reject_nyquist_and_unsupported_sensor_band():
    for opt in [SpectralOptions(band_hz=(1,128)),SpectralOptions(band_hz=(1,60),calibrated_bandwidth_hz=40)]:
        with pytest.raises(ValueError,match='band'):analyze_spectrum(signal(),opt)


def test_unknown_antialias_is_exploratory():
    assert analyze_spectrum(signal(),SpectralOptions())['observation_eligibility']=='exploratory'


def test_sample_and_cell_budgets():
    s=signal();large=SignalSeries((np.arange(250001)/256).tolist(),[0.]*250001,s.unit,s.sensor_id,{})
    with pytest.raises(ValueError,match='limit'):analyze_spectrum(large,SpectralOptions())
    with pytest.raises(ValueError,match='segments'):analyze_spectrum(SignalSeries(s.times_s[:256],s.values[:256],s.unit,s.sensor_id,{}),SpectralOptions())


def test_cell_budget_is_checked_before_scipy_allocation(monkeypatch):
    import digital_twin_lab.chassis.spectral as backend
    monkeypatch.setattr(backend,'welch',lambda *a,**kw:pytest.fail('allocated spectrum before budget guard'))
    s=SignalSeries((np.arange(250000)/1000).tolist(),[0.]*250000,'m','suspension_front',{})
    with pytest.raises(ValueError,match='cell_limit'):analyze_spectrum(s,SpectralOptions(method='stft',nperseg=8192,band_hz=(1,400)))
