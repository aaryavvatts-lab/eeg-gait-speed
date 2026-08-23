"""Loading and re-referencing of the raw EEG CSV files.

The dataset ships EEG referenced to the hardware reference Pz, which means the
files contain no Pz column at all. The bundled MATLAB helper
(``Dataset/EEG_Data/EEG_referencing.m``) re-references everything to linked
ears (the mean of the A1 and A2 earlobe electrodes) and reconstructs Pz as
a zero vector so that it becomes ``-LE`` after subtraction. This module is a
faithful Python translation of that procedure, with the channels emitted in
the standard 10-20 order rather than the acquisition order.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from . import config as cfg

# Columns actually needed: every mapped electrode plus the two earlobes.
_NEEDED_COLS = sorted(
    {col for _, col in cfg.CHANNEL_COLUMNS if col is not None}
    | {cfg.COL_A1, cfg.COL_A2}
)

_FNAME_RE = re.compile(r"^S(\d+)_(0\.5|0\.75|1)_raw\.csv$")


def parse_filename(path: Path) -> tuple[str, str] | None:
    """Return ``(subject, speed)`` for an EEG filename, or None if it isn't one."""
    m = _FNAME_RE.match(path.name)
    if m is None:
        return None
    return f"S{m.group(1)}", m.group(2)


def list_eeg_trials(exclude: tuple[str, ...] = cfg.EXCLUDED_SUBJECTS) -> list[dict]:
    """Enumerate usable EEG trials as sorted metadata dicts."""
    trials = []
    for path in sorted(cfg.EEG_DIR.glob("*.csv")):
        parsed = parse_filename(path)
        if parsed is None:
            continue
        subject, speed = parsed
        if subject in exclude:
            continue
        trials.append(
            {
                "trial_id": f"{subject}_{speed}",
                "subject": subject,
                "subject_num": int(subject[1:]),
                "speed": speed,
                "speed_ms": cfg.SPEED_MS[speed],
                "path": path,
            }
        )
    trials.sort(key=lambda t: (t["subject_num"], cfg.SPEED_MS[t["speed"]]))
    return trials


def load_eeg_trial(path: Path) -> np.ndarray:
    """Load one EEG CSV and return a linked-ears referenced ``(19, n)`` array in uV.

    Channels are returned in :data:`gaitbci.config.CHANNELS` order.
    """
    raw = pd.read_csv(
        path,
        skiprows=cfg.EEG_HEADER_LINES,
        header=None,
        usecols=_NEEDED_COLS,
        dtype=np.float64,
    )
    # `usecols` preserves the original column labels, so index by them directly.
    linked_ears = (raw[cfg.COL_A1].to_numpy() + raw[cfg.COL_A2].to_numpy()) / 2.0
    n = linked_ears.size

    out = np.empty((cfg.N_CHANNELS, n), dtype=np.float32)
    for i, (_name, col) in enumerate(cfg.CHANNEL_COLUMNS):
        if col is None:
            # Pz was the hardware reference: an all-zero trace minus the new
            # reference. Keeping it is what makes the montage a full 19.
            out[i] = -linked_ears
        else:
            out[i] = raw[col].to_numpy() - linked_ears
    return out


def load_all_eeg(trials: list[dict], progress: bool = True) -> np.ndarray:
    """Load every trial into one ``(n_trials, 19, n_samples)`` float32 array."""
    from tqdm import tqdm

    iterator = tqdm(trials, desc="EEG", unit="trial") if progress else trials
    data = np.empty(
        (len(trials), cfg.N_CHANNELS, cfg.EEG_N_SAMPLES), dtype=np.float32
    )
    for i, trial in enumerate(iterator):
        arr = load_eeg_trial(trial["path"])
        if arr.shape[1] != cfg.EEG_N_SAMPLES:
            raise ValueError(
                f"{trial['trial_id']}: expected {cfg.EEG_N_SAMPLES} samples, "
                f"got {arr.shape[1]}"
            )
        data[i] = arr
    return data
