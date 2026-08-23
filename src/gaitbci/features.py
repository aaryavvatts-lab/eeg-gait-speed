"""Feature extraction: spectral band powers from EEG, envelope statistics from EMG."""
from __future__ import annotations

import numpy as np
from scipy import signal

from . import config as cfg

# --------------------------------------------------------------------------
# EEG
# --------------------------------------------------------------------------


def eeg_feature_names() -> list[str]:
    """Column names matching the layout produced by :func:`eeg_features`."""
    names = []
    for band in cfg.BANDS:
        names += [f"abs_{band}_{ch}" for ch in cfg.CHANNELS]
    for band in cfg.BANDS:
        names += [f"rel_{band}_{ch}" for ch in cfg.CHANNELS]
    names += [f"total_{ch}" for ch in cfg.CHANNELS]
    return names


def eeg_features(
    epochs: np.ndarray, sfreq: float = cfg.EEG_SFREQ
) -> np.ndarray:
    """Band powers for ``(n_windows, n_ch, w)`` epochs -> ``(n_windows, 209)``.

    Three blocks, in this order: log10 absolute power per band, relative power
    per band (band / total 1-45 Hz), and log10 total 1-45 Hz power. Absolute
    power is logged because band power is roughly log-normal; relative power is
    left linear because it is already a bounded ratio.

    Delta and theta are computed even though the source material only calls for
    alpha, beta and gamma. They carry the step rhythm, and the
    confound analysis needs to be able to remove them explicitly.
    """
    nperseg = min(cfg.WELCH_NPERSEG, epochs.shape[2])
    freqs, psd = signal.welch(
        epochs.astype(np.float64), fs=sfreq, nperseg=nperseg, axis=-1
    )  # psd: (n_windows, n_ch, n_freqs)

    lo, hi = cfg.BANDPASS
    total_mask = (freqs >= lo) & (freqs <= hi)
    df = freqs[1] - freqs[0]
    total = psd[..., total_mask].sum(axis=-1) * df           # (n_win, n_ch)
    total_safe = np.maximum(total, 1e-20)

    abs_blocks, rel_blocks = [], []
    for f_lo, f_hi in cfg.BANDS.values():
        mask = (freqs >= f_lo) & (freqs < f_hi)
        power = psd[..., mask].sum(axis=-1) * df
        abs_blocks.append(np.log10(np.maximum(power, 1e-20)))
        rel_blocks.append(power / total_safe)

    return np.concatenate(
        abs_blocks + rel_blocks + [np.log10(total_safe)], axis=1
    ).astype(np.float32)


def band_of_feature(name: str) -> str | None:
    """Band name encoded in a feature column, or None for the total-power block."""
    if name.startswith("total_"):
        return None
    return name.split("_")[1]


def channel_of_feature(name: str) -> str:
    """Channel name encoded in a feature column."""
    return name.split("_", 2)[-1] if not name.startswith("total_") else name[6:]


# --------------------------------------------------------------------------
# EMG
# --------------------------------------------------------------------------


def emg_feature_names() -> list[str]:
    names = []
    for stat in ("mean", "sd", "p90"):
        names += [f"mav_{stat}_{m}" for m in cfg.EMG_MUSCLES]
    names += [f"cadence_hz_{m}" for m in cfg.EMG_MUSCLES]
    names += [f"cadence_pow_{m}" for m in cfg.EMG_MUSCLES]
    return names


def emg_features(
    times: np.ndarray,
    mav: np.ndarray,
    t_starts: np.ndarray,
    window_sec: float = cfg.WINDOW_SEC,
) -> np.ndarray:
    """EMG features on windows aligned to the EEG windows by wall-clock time.

    Returns ``(n_windows, 60)``. Windows for which the EMG recording has no
    samples are filled with NaN so the caller can drop them explicitly rather
    than silently imputing.

    Alignment is by timestamp, not sample index: EMG trials run 60.4-70.4 s
    while every EEG trial is exactly 59.87 s, so index-based alignment would
    drift by up to ten seconds by the end of a trial.
    """
    n_win = len(t_starts)
    n_feat = 5 * cfg.N_MUSCLES
    out = np.full((n_win, n_feat), np.nan, dtype=np.float32)

    # Effective envelope sampling rate, measured from this file's own timestamps.
    if times.size > 1:
        fs_env = 1.0 / float(np.median(np.diff(times)))
    else:
        fs_env = cfg.EMG_SFREQ

    for i, t0 in enumerate(t_starts):
        sel = (times >= t0) & (times < t0 + window_sec)
        n_sel = int(sel.sum())
        if n_sel < 4:
            continue
        seg = mav[:, sel].astype(np.float64)                  # (12, n_sel)

        feats = [
            seg.mean(axis=1),
            seg.std(axis=1),
            np.percentile(seg, 90, axis=1),
        ]

        # Dominant envelope frequency = step rhythm. This is the feature that
        # most directly encodes walking speed, which is exactly why it is
        # isolated rather than buried in a generic spectral summary.
        centred = seg - seg.mean(axis=1, keepdims=True)
        spec = np.abs(np.fft.rfft(centred, axis=1))
        fr = np.fft.rfftfreq(n_sel, d=1.0 / fs_env)
        band = (fr >= cfg.CADENCE_BAND[0]) & (fr <= cfg.CADENCE_BAND[1])
        if band.sum() == 0:
            continue
        sub = spec[:, band]
        idx = np.argmax(sub, axis=1)
        feats.append(fr[band][idx])
        feats.append(np.log10(np.maximum(sub[np.arange(sub.shape[0]), idx], 1e-20)))

        out[i] = np.concatenate(feats).astype(np.float32)
    return out
