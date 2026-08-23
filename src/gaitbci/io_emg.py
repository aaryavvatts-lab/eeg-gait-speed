"""Loading of the pre-computed EMG mean-absolute-value envelopes.

Each EMG file holds a timestamp column plus 12 lower-limb muscle channels
already reduced to MAV at roughly 16 Hz. Trial durations vary between about
60.4 s and 70.4 s, so every downstream operation aligns on the timestamp
column rather than on sample index.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as cfg


def emg_path(subject: str, speed: str):
    return cfg.EMG_DIR / f"EMG_{subject}_{speed}.csv"


def has_emg(subject: str, speed: str) -> bool:
    return emg_path(subject, speed).exists()


def load_emg_trial(subject: str, speed: str) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(times, mav)`` where ``mav`` is ``(12, n)`` in volts."""
    df = pd.read_csv(emg_path(subject, speed))
    arr = df.to_numpy(dtype=np.float64)
    times = arr[:, 0]
    mav = arr[:, 1 : 1 + cfg.N_MUSCLES].T.astype(np.float32)
    if mav.shape[0] != cfg.N_MUSCLES:
        raise ValueError(
            f"EMG_{subject}_{speed}: expected {cfg.N_MUSCLES} muscle columns, "
            f"got {mav.shape[0]}"
        )
    return times.astype(np.float32), mav


def load_all_emg(trials: list[dict], progress: bool = True) -> dict[str, dict]:
    """Load EMG for every trial that has it, keyed by ``trial_id``."""
    from tqdm import tqdm

    iterator = tqdm(trials, desc="EMG", unit="trial") if progress else trials
    out: dict[str, dict] = {}
    for trial in iterator:
        subject, speed = trial["subject"], trial["speed"]
        if not has_emg(subject, speed):
            continue
        times, mav = load_emg_trial(subject, speed)
        out[trial["trial_id"]] = {"times": times, "mav": mav}
    return out
