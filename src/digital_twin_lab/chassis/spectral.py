"""Bounded PSD/STFT observations; peaks are frequencies, never diagnoses."""
import numpy as np
import scipy
from scipy.signal import ShortTimeFFT, get_window, welch
from .signal_models import SignalSeries,SpectralOptions
from .suspension_signals import inspect_signal


def analyze_spectrum(series:SignalSeries, options:SpectralOptions)->dict:
    if len(series.values)>250000:raise ValueError('sample_limit_exceeded')
    q=inspect_signal(series)
    if q.status!='eligible':raise ValueError(','.join(q.reasons))
    n=options.nperseg
    if isinstance(n,bool) or n<256 or n>8192 or n&(n-1):raise ValueError('invalid_segment_size')
    if options.method not in ('welch','stft'):raise ValueError('unsupported_spectral_method')
    if series.unit not in ('m','m/s','m/s2'):raise ValueError('unsupported_spectral_unit')
    fs=q.effective_fs_hz
    lo,hi=options.band_hz
    if not np.isfinite([lo,hi]).all() or not 0<=lo<hi<fs/2 or (options.calibrated_bandwidth_hz is not None and hi>options.calibrated_bandwidth_hz):
        raise ValueError('unsupported_frequency_band')
    count=1+(len(series.values)-n)//(n//2)
    if count<3:raise ValueError('insufficient_welch_segments')
    if options.method=='stft' and (n//2+1)*(count+4)>262144:raise ValueError('stft_cell_limit_exceeded')
    win=get_window('hann',n,fftbins=True)
    f,p=welch(np.asarray(series.values,dtype=float),fs=fs,window=win,nperseg=n,noverlap=n//2,nfft=n,detrend='constant',return_onesided=True,scaling='density',average='mean')
    band=(f>=lo)&(f<=hi)&(f>0)
    if not band.any():raise ValueError('band_has_no_resolved_bins')
    peak=float(f[band][np.argmax(p[band])]) if np.max(p[band])>1e-25 else None
    verified_band=options.calibrated_bandwidth_hz is not None and bool(options.antialias_reference.strip())
    result={'method':options.method,'effective_fs_hz':fs,'nyquist_hz':fs/2,'resolution_hz':fs/n,'segment_count':count,
            'duration_s':series.times_s[-1]-series.times_s[0],'nperseg':n,'noverlap':n//2,'nfft':n,
            'window':'periodic_hann','detrend':'constant','scaling':'density','band_hz':[lo,hi],
            'density_unit':series.unit+'²/Hz','frequencies_hz':f.tolist(),'density':p.tolist(),
            'dominant_frequency_hz':peak,'observation_eligibility':'eligible_for_review' if verified_band else 'exploratory',
            'warnings':[] if verified_band else ['sensor_bandwidth_or_antialias_not_documented'],
            'backend_versions':{'numpy':np.__version__,'scipy':scipy.__version__}}
    if options.method=='stft':
        st=ShortTimeFFT(win,n//2,fs,fft_mode='onesided2X',scale_to='psd')
        centers=st.t(len(series.values))
        center_samples=(np.arange(len(centers))+st.p_min)*(n//2)
        valid=(center_samples-n//2>=0)&(center_samples+n//2<=len(series.values))
        # Only full windows are published. DC removal per observed window.
        matrix=st.spectrogram(np.asarray(series.values),detr='constant')[:,valid]
        result.update(times_s=(centers[valid]+series.times_s[0]).tolist(),density_matrix=matrix.tolist())
    return result
