"""Build and cache the windowed feature tables (main + sensitivity variant)."""
from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd

from gaitbci import config as cfg, datasets


def summarise(df: pd.DataFrame, label: str) -> pd.DataFrame:
    n_eeg = len(datasets.feature_columns(df, "eeg_"))
    n_emg = len(datasets.feature_columns(df, "emg_"))
    print(f"\n[{label}] rows={len(df)}  eeg_features={n_eeg}  emg_features={n_emg}")

    rej = (
        df.groupby("speed", observed=True)["kept"]
        .agg(windows="size", kept="sum")
        .assign(rejected_pct=lambda d: 100 * (1 - d["kept"] / d["windows"]))
        .reset_index()
    )
    print(rej.to_string(index=False))

    eeg_cols = datasets.feature_columns(df, "eeg_")
    assert np.isfinite(df[eeg_cols].to_numpy()).all(), "EEG features not finite"

    emg_cols = datasets.feature_columns(df, "emg_")
    n_emg_nan = int(df[emg_cols].isna().any(axis=1).sum())
    print(f"windows without usable EMG: {n_emg_nan} "
          f"({100 * n_emg_nan / len(df):.1f}%)")
    return rej


def main() -> int:
    t0 = time.time()

    df = datasets.build_feature_table()
    rej = summarise(df, f"{cfg.WINDOW_SEC:g}s windows")
    df.to_parquet(cfg.CACHE / "features_2s.parquet")
    rej.to_csv(cfg.TABLES / "rejection_by_speed.csv", index=False)

    alt = datasets.build_feature_table(
        window_sec=cfg.WINDOW_SEC_ALT, hop_sec=cfg.HOP_SEC_ALT
    )
    summarise(alt, f"{cfg.WINDOW_SEC_ALT:g}s windows")
    alt.to_parquet(cfg.CACHE / "features_4s.parquet")

    for name in ("all", "reel", "no_lowfreq", "broadband", "no_rim"):
        _, cols = datasets.eeg_matrix(df, name)
        print(f"subset {name:<11} -> {len(cols)} columns")

    print(f"\ndone in {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
