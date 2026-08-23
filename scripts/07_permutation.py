"""Is the decoding better than chance, or is it fold-structure luck?

Labels are shuffled *within subject*, so every person keeps their three
recordings and only the speed attached to each one is scrambled. That null
preserves the subject structure the honest CV has to cope with, which is
exactly what makes the resulting p-value meaningful.

The forest is reduced to PERM_TREES here purely for run time. The observed
value is recomputed with the identical reduced configuration, so observed and
null remain directly comparable.
"""
from __future__ import annotations

import json
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

from gaitbci import config as cfg, datasets, evaluate, viz

PERM_TREES = 200
N_PERM = 200


def forest() -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=PERM_TREES,
        class_weight="balanced_subsample",
        random_state=cfg.RANDOM_SEED,
        n_jobs=cfg.N_JOBS,
    )


def main() -> int:
    t0 = time.time()
    viz.use_style()

    if "--figure-only" in sys.argv:
        make_figure()
        return 0

    df = pd.read_parquet(cfg.CACHE / "features_2s.parquet")
    df = df[df["kept"]].reset_index(drop=True)
    emg_cols = datasets.feature_columns(df, "emg_")
    common = df[df[emg_cols].notna().all(axis=1)].reset_index(drop=True)
    subjects = common["subject"].to_numpy()

    X_eeg, _ = datasets.eeg_matrix(common, "all")
    X_emg = common[emg_cols].to_numpy(dtype=np.float64)
    arms = {
        "EEG": X_eeg,
        "EMG": X_emg,
        "EEG+EMG": np.hstack([X_eeg, X_emg]),
    }

    out, nulls = {}, {}
    for arm, X_raw in arms.items():
        X = datasets.per_subject_zscore(X_raw, subjects)
        splitter, _ = evaluate.make_splitter("subject")
        y = common["speed"].to_numpy().astype(str)
        y_pred, _ = evaluate.cross_val_predict_oof(forest(), X, y, subjects, splitter)
        observed = balanced_accuracy_score(y, y_pred)
        print(f"{arm}: observed = {observed:.3f} ({time.time() - t0:.0f}s)")

        res = evaluate.permutation_test(
            forest(), X, common, observed,
            n_permutations=N_PERM, scheme="subject",
        )
        out[arm] = {k: v for k, v in res.items() if k != "null"}
        nulls[arm] = res["null"]
        print(f"  null mean = {res['null_mean']:.3f}  "
              f"95th pct = {res['null_p95']:.3f}  "
              f"p = {res['p_value']:.4f}  ({time.time() - t0:.0f}s)")

    np.savez(cfg.CACHE / "permutation_nulls.npz",
             **{k.replace("+", "_"): v for k, v in nulls.items()})
    (cfg.TABLES / "permutation.json").write_text(json.dumps(
        {"n_permutations": N_PERM, "n_trees": PERM_TREES, "arms": out}, indent=2
    ))
    pd.DataFrame(
        [{"arm": k, **v} for k, v in out.items()]
    ).to_csv(cfg.TABLES / "permutation.csv", index=False)

    make_figure()

    print(f"\ndone in {time.time() - t0:.1f}s")
    return 0


def make_figure() -> None:
    """Rebuild the null-distribution figure from the cached permutation draws.

    Separate from the test itself so the layout can be revised without paying
    for another 69 minutes of refitting.
    """
    meta = json.loads((cfg.TABLES / "permutation.json").read_text())
    npz = np.load(cfg.CACHE / "permutation_nulls.npz")
    n = meta["n_permutations"]

    fig, axes = plt.subplots(1, 3, figsize=(11.2, 3.6), gridspec_kw={"wspace": 0.3})
    for ax, arm in zip(axes, ("EEG", "EMG", "EEG+EMG")):
        null = npz[arm.replace("+", "_")]
        obs = meta["arms"][arm]["observed"]
        ax.hist(null, bins=26, color=viz.GREY, alpha=0.75, zorder=2)

        ax.axvline(1 / 3, color=viz.ACCENT, ls="--", lw=1.2, zorder=3)
        ax.axvline(obs, color=viz.ARM_COLORS[arm], lw=2.4, zorder=3)

        hi = obs + 0.09
        ax.set_xlim(0.26, hi)
        top = ax.get_ylim()[1]
        # Label the two reference lines directly rather than in a legend box,
        # which the observed line would otherwise cut straight through.
        ax.text(1 / 3, top * 1.02, "chance", color=viz.ACCENT, fontsize=7.5,
                ha="center", va="bottom", fontweight="bold")
        ax.text(obs - (hi - 0.26) * 0.022, top * 0.55, f"real score {obs:.3f}",
                color=viz.ARM_COLORS[arm], fontsize=8, rotation=90,
                ha="right", va="center", fontweight="bold")

        p = meta["arms"][arm]["p_value"]
        ptxt = f"p = {p:.3f}" if p > 1 / (n + 1) else f"p < {1/n:.3f}"
        ax.set_xlabel("balanced accuracy")
        ax.set_ylabel("permutations")
        ax.set_title(f"{arm}\n{ptxt}")

    fig.suptitle(
        f"Speed labels shuffled inside each person, {n} times over.\n"
        "Every shuffled score lands on chance, so the test setup is not leaking",
        fontsize=10.5, fontweight="bold", y=1.1,
    )
    viz.save(fig, "07_permutation_null")


if __name__ == "__main__":
    sys.exit(main())
