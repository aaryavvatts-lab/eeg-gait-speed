"""Assemble the windowed feature table that every experiment consumes."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as cfg, features as ft, preprocess as pp

META_COLS = [
    "trial_id", "subject", "subject_num", "speed", "speed_ms",
    "window_idx", "t_start", "kept",
]


def load_cache() -> tuple[np.ndarray, pd.DataFrame, dict]:
    """Return ``(eeg, trial_meta, emg)`` from the on-disk cache."""
    eeg = np.load(cfg.CACHE / "eeg_raw.npy")
    meta = pd.read_parquet(cfg.CACHE / "trials.parquet")
    npz = np.load(cfg.CACHE / "emg_raw.npz")
    emg: dict[str, dict] = {}
    for key in npz.files:
        tid, kind = key.rsplit("__", 1)
        emg.setdefault(tid, {})["times" if kind == "t" else "mav"] = npz[key]
    return eeg, meta, emg


def build_feature_table(
    window_sec: float = cfg.WINDOW_SEC,
    hop_sec: float = cfg.HOP_SEC,
    progress: bool = True,
) -> pd.DataFrame:
    """Filter, epoch, reject and featurise every trial into one long table.

    One row per window. EEG feature columns are prefixed ``eeg_``, EMG columns
    ``emg_``. The ``kept`` column carries the artifact-rejection verdict; rows
    are *not* dropped here so that rejection rates stay auditable per class.
    """
    from tqdm import tqdm

    eeg, meta, emg = load_cache()
    eeg_names = [f"eeg_{n}" for n in ft.eeg_feature_names()]
    emg_names = [f"emg_{n}" for n in ft.emg_feature_names()]

    rows, eeg_blocks, emg_blocks = [], [], []
    iterator = meta.itertuples()
    if progress:
        iterator = tqdm(iterator, total=len(meta), desc="features", unit="trial")

    for trial in iterator:
        filtered = pp.filter_trial(eeg[trial.Index])
        epochs, t_starts = pp.epoch_trial(
            filtered, window_sec=window_sec, hop_sec=hop_sec
        )
        keep = pp.rejection_mask(epochs)
        eeg_blocks.append(ft.eeg_features(epochs))

        rec = emg.get(trial.trial_id)
        if rec is None:
            emg_blocks.append(
                np.full((len(t_starts), len(emg_names)), np.nan, dtype=np.float32)
            )
        else:
            emg_blocks.append(
                ft.emg_features(rec["times"], rec["mav"], t_starts, window_sec)
            )

        for w, (t0, k) in enumerate(zip(t_starts, keep)):
            rows.append(
                (trial.trial_id, trial.subject, trial.subject_num, trial.speed,
                 trial.speed_ms, w, float(t0), bool(k))
            )

    return pd.concat(
        [
            pd.DataFrame(rows, columns=META_COLS),
            pd.DataFrame(np.concatenate(eeg_blocks, axis=0), columns=eeg_names),
            pd.DataFrame(np.concatenate(emg_blocks, axis=0), columns=emg_names),
        ],
        axis=1,
    )


def feature_columns(df: pd.DataFrame, prefix: str) -> list[str]:
    return [c for c in df.columns if c.startswith(prefix)]


def eeg_matrix(df: pd.DataFrame, subset: str = "all") -> tuple[np.ndarray, list[str]]:
    """EEG design matrix for a named feature subset.

    ``all``        every band plus relative power and total power (209 columns)
    ``reel``       only the absolute+relative alpha/beta/gamma columns, i.e. the
                   literal recipe from the source material
    ``no_lowfreq`` drops delta and theta, which carry the step-frequency artifact
    ``broadband``  only the 19 log total-power columns
    ``no_rim``     every band, but excluding the ocular/neck-contaminated
                   frontal and temporal electrodes
    ``motor``      only C3/Cz/C4, the electrodes over motor cortex
    """
    cols = feature_columns(df, "eeg_")
    if subset == "all":
        keep = cols
    elif subset == "reel":
        keep = [
            c for c in cols
            if any(f"_{b}_" in c for b in cfg.REEL_BANDS)
            and not c.startswith("eeg_total_")
        ]
    elif subset == "no_lowfreq":
        keep = [c for c in cols if "_delta_" not in c and "_theta_" not in c]
    elif subset == "broadband":
        keep = [c for c in cols if c.startswith("eeg_total_")]
    elif subset == "no_rim":
        keep = [
            c for c in cols
            if c.rsplit("_", 1)[-1] not in cfg.RIM_CHANNELS
        ]
    elif subset == "motor":
        keep = [c for c in cols if c.rsplit("_", 1)[-1] in cfg.MOTOR_CHANNELS]
    else:
        raise ValueError(f"unknown EEG feature subset: {subset!r}")
    return df[keep].to_numpy(dtype=np.float64), keep


def per_subject_zscore(X: np.ndarray, subjects: np.ndarray) -> np.ndarray:
    """Centre and scale features within each subject.

    Standard practice for cross-subject BCI: it removes each person's overall
    offset (skull thickness, electrode impedance, hair) while preserving the
    differences *between* their own speed conditions, which is the signal we
    actually want to generalise.
    """
    out = np.empty_like(X)
    for s in np.unique(subjects):
        m = subjects == s
        block = X[m]
        mu = block.mean(axis=0)
        sd = block.std(axis=0)
        out[m] = (block - mu) / np.where(sd > 1e-12, sd, 1.0)
    return out
