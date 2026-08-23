"""Filtering, epoching and artifact rejection for the EEG traces.

EEG recorded with dry electrodes during treadmill walking is heavily
contaminated. Per-channel standard deviations in this dataset run from about
40 to 500 uV. Rejection is therefore mandatory rather than cosmetic, and it is
done per trial so that it adapts to each individual headset fitting instead of
imposing one global amplitude threshold across 58 people.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from . import config as cfg


def design_filters(sfreq: float = cfg.EEG_SFREQ):
    """Return (bandpass_sos, [notch_ba, ...]) for the configured settings."""
    lo, hi = cfg.BANDPASS
    sos = signal.butter(
        cfg.FILTER_ORDER, [lo, hi], btype="bandpass", fs=sfreq, output="sos"
    )
    notches = []
    for f0 in cfg.NOTCH_HZ:
        if f0 < sfreq / 2:
            notches.append(signal.iirnotch(f0, Q=30.0, fs=sfreq))
    return sos, notches


def filter_trial(x: np.ndarray, sfreq: float = cfg.EEG_SFREQ) -> np.ndarray:
    """Detrend, notch the mains and its harmonic, then band-pass ``(n_ch, n)``.

    All filtering is zero-phase (``filtfilt``) so that band-power estimates are
    not shifted in time relative to the gait cycle.
    """
    sos, notches = design_filters(sfreq)
    y = signal.detrend(x.astype(np.float64), axis=-1, type="linear")
    for b, a in notches:
        y = signal.filtfilt(b, a, y, axis=-1)
    y = signal.sosfiltfilt(sos, y, axis=-1)
    return y.astype(np.float32)


def window_bounds(
    n_samples: int,
    sfreq: float = cfg.EEG_SFREQ,
    window_sec: float = cfg.WINDOW_SEC,
    hop_sec: float = cfg.HOP_SEC,
) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(starts, t_starts)`` sample indices and their times in seconds."""
    w = int(round(window_sec * sfreq))
    h = int(round(hop_sec * sfreq))
    starts = np.arange(0, n_samples - w + 1, h, dtype=int)
    return starts, starts / sfreq


def epoch_trial(
    x: np.ndarray,
    sfreq: float = cfg.EEG_SFREQ,
    window_sec: float = cfg.WINDOW_SEC,
    hop_sec: float = cfg.HOP_SEC,
) -> tuple[np.ndarray, np.ndarray]:
    """Slice ``(n_ch, n)`` into ``(n_windows, n_ch, w)`` plus window start times."""
    w = int(round(window_sec * sfreq))
    starts, t_starts = window_bounds(x.shape[1], sfreq, window_sec, hop_sec)
    epochs = np.stack([x[:, s : s + w] for s in starts], axis=0)
    return epochs, t_starts


def rejection_mask(epochs: np.ndarray, n_mad: float = cfg.REJECT_MAD) -> np.ndarray:
    """Flag windows whose peak-to-peak amplitude is an outlier within the trial.

    A window is kept only if *every* channel's peak-to-peak stays within
    ``median + n_mad * MAD`` of that channel's own distribution across the
    trial's windows. Returns a boolean keep-mask of length ``n_windows``.
    """
    p2p = epochs.max(axis=2) - epochs.min(axis=2)          # (n_windows, n_ch)
    med = np.median(p2p, axis=0)                            # per channel
    mad = np.median(np.abs(p2p - med), axis=0)
    # 1.4826 rescales MAD to a Gaussian-equivalent sigma; the floor keeps the
    # threshold finite for a channel whose p2p is almost constant.
    scale = np.maximum(1.4826 * mad, 1e-6)
    threshold = med + n_mad * scale
    return np.all(p2p <= threshold, axis=1)
