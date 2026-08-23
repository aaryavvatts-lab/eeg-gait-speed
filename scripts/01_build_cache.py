"""Parse every raw EEG and EMG file once and cache them as arrays.

Everything downstream reads the cache, so the CSV parsing cost is paid a
single time. Run this first.
"""
from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd

from gaitbci import config as cfg, io_eeg, io_emg


def main() -> int:
    t0 = time.time()
    trials = io_eeg.list_eeg_trials()
    meta = pd.DataFrame(
        [{k: v for k, v in t.items() if k != "path"} for t in trials]
    )

    # ---- checks on the trial inventory ------------------------------------
    n_subj = meta["subject"].nunique()
    counts = meta["speed"].value_counts().to_dict()
    print(f"trials={len(meta)}  subjects={n_subj}  speeds={counts}")
    assert len(meta) == 174, f"expected 174 trials, got {len(meta)}"
    assert n_subj == 58, f"expected 58 subjects, got {n_subj}"
    assert set(counts.values()) == {58}, f"speed classes not balanced: {counts}"
    assert "S32" not in set(meta["subject"]), "S32 should have been excluded"

    # ---- EEG --------------------------------------------------------------
    eeg = io_eeg.load_all_eeg(trials)
    print(f"EEG array {eeg.shape} {eeg.dtype} "
          f"({eeg.nbytes / 1e6:.0f} MB)")

    assert np.isfinite(eeg).all(), "EEG cache contains NaN or inf"

    # Pz is reconstructed as -(A1+A2)/2; confirm on a random trial that this
    # actually happened rather than silently emitting zeros.
    pz = eeg[:, cfg.CHANNELS.index("Pz"), :]
    assert np.all(pz.std(axis=1) > 0), "Pz row is flat, so re-referencing failed"

    sd = eeg.std(axis=2)
    print(f"per-channel SD (uV): median={np.median(sd):.1f} "
          f"p5={np.percentile(sd, 5):.1f} p95={np.percentile(sd, 95):.1f} "
          f"max={sd.max():.1f}")

    np.save(cfg.CACHE / "eeg_raw.npy", eeg)
    meta.to_parquet(cfg.CACHE / "trials.parquet")

    # ---- EMG --------------------------------------------------------------
    emg = io_emg.load_all_emg(trials)
    print(f"EMG trials with data: {len(emg)} / {len(trials)}")
    missing = sorted({t["trial_id"] for t in trials} - set(emg))
    print(f"EMG missing: {missing}")

    # Store ragged EMG as a flat npz: one times/mav pair per trial id.
    flat = {}
    for tid, d in emg.items():
        flat[f"{tid}__t"] = d["times"]
        flat[f"{tid}__m"] = d["mav"]
    np.savez_compressed(cfg.CACHE / "emg_raw.npz", **flat)

    durs = np.array([d["times"][-1] for d in emg.values()])
    print(f"EMG duration (s): min={durs.min():.1f} median={np.median(durs):.1f} "
          f"max={durs.max():.1f}")

    print(f"\ndone in {time.time() - t0:.1f}s -> {cfg.CACHE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
