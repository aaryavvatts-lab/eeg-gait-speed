"""The headline result: EEG, EMG and their fusion under subject-wise CV.

All three run on the same rows, the windows that survive rejection and also
have a matching muscle recording, so they can be compared directly. The brain
model is also reported on the full set of windows, since it does not depend on
a muscle file being there.
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

from gaitbci import config as cfg, datasets, evaluate, models, viz

ARMS = ("EEG", "EMG", "EEG+EMG")
MODEL_ORDER = ("dummy", "logistic", "random_forest", "gradient_boosting")


def build_arms(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    """Restrict to rows usable by every arm and return each arm's matrix."""
    emg_cols = datasets.feature_columns(df, "emg_")
    common = df[df[emg_cols].notna().all(axis=1)].reset_index(drop=True)
    X_eeg, _ = datasets.eeg_matrix(common, "all")
    X_emg = common[emg_cols].to_numpy(dtype=np.float64)
    return common, {
        "EEG": X_eeg,
        "EMG": X_emg,
        "EEG+EMG": np.hstack([X_eeg, X_emg]),
    }


def main() -> int:
    t0 = time.time()
    viz.use_style()

    if "--figure-only" in sys.argv:
        make_figure()
        return 0

    df = pd.read_parquet(cfg.CACHE / "features_2s.parquet")
    df = df[df["kept"]].reset_index(drop=True)
    common, mats = build_arms(df)
    print(f"common rows={len(common)}  subjects={common.subject.nunique()}  "
          f"trials={common.trial_id.nunique()}")
    for arm, X in mats.items():
        print(f"  {arm:<8} {X.shape[1]:>4} features")

    subjects = common["subject"].to_numpy()

    # ---- grid: arm x model x normalisation -------------------------------
    rows = []
    for arm, X_raw in mats.items():
        variants = {
            "raw": X_raw,
            # Unsupervised: uses only each subject's own feature distribution,
            # never their labels. A deployed device could do the same from a
            # short calibration recording.
            "per_subject_z": datasets.per_subject_zscore(X_raw, subjects),
        }
        for norm, X in variants.items():
            for name in MODEL_ORDER:
                res = evaluate.evaluate(models.build(name), X, common, "subject")
                rows.append(
                    {
                        "arm": arm, "model": name, "norm": norm,
                        **{k: res[k] for k in (
                            "balanced_accuracy", "accuracy", "macro_f1", "kappa",
                            "distant_error_rate", "spearman_rho", "n")},
                        "trial_balanced_accuracy": res["trial_balanced_accuracy"],
                        "n_trials": res["n_trials"],
                    }
                )
                print(f"  {arm:<8} {name:<18} {norm:<14} "
                      f"win={res['balanced_accuracy']:.3f} "
                      f"trial={res['trial_balanced_accuracy']:.3f} "
                      f"({time.time() - t0:.0f}s)")

    grid = pd.DataFrame(rows)
    grid.to_csv(cfg.TABLES / "main_grid.csv", index=False)

    # ---- EEG on the full window set, for reference ------------------------
    X_all, _ = datasets.eeg_matrix(df, "all")
    ref = evaluate.evaluate(models.random_forest(), X_all, df, "subject")
    print(f"\nEEG on all {len(df)} windows: window={ref['balanced_accuracy']:.3f} "
          f"trial={ref['trial_balanced_accuracy']:.3f}")

    # ---- pick the best normalisation for the RF, then run LOSO -----------
    rf = grid[grid.model == "random_forest"]
    best_norm = (
        rf.groupby("norm")["balanced_accuracy"].mean().idxmax()
    )
    print(f"best normalisation for RF: {best_norm}")

    loso, confusions = {}, {}
    for arm, X_raw in mats.items():
        X = (datasets.per_subject_zscore(X_raw, subjects)
             if best_norm == "per_subject_z" else X_raw)
        res = evaluate.evaluate(models.random_forest(), X, common, "loso")
        per_subj = evaluate.per_group_scores(
            res["y_true"], res["y_pred"], subjects
        )
        loso[arm] = {
            "balanced_accuracy": res["balanced_accuracy"],
            "trial_balanced_accuracy": res["trial_balanced_accuracy"],
            "kappa": res["kappa"],
            "distant_error_rate": res["distant_error_rate"],
            "spearman_rho": res["spearman_rho"],
            "per_subject": per_subj,
        }
        confusions[arm] = res["confusion"]
        np.save(cfg.CACHE / f"loso_pred_{arm.replace('+', '_')}.npy", res["y_pred"])
        print(f"  LOSO {arm:<8} window={res['balanced_accuracy']:.3f} "
              f"trial={res['trial_balanced_accuracy']:.3f} "
              f"({time.time() - t0:.0f}s)")

    pd.concat(
        [v["per_subject"].assign(arm=k) for k, v in loso.items()]
    ).to_csv(cfg.TABLES / "loso_per_subject.csv", index=False)

    summary = pd.DataFrame(
        [{"arm": k, **{kk: vv for kk, vv in v.items() if kk != "per_subject"}}
         for k, v in loso.items()]
    )
    summary.to_csv(cfg.TABLES / "loso_summary.csv", index=False)
    print("\n" + summary.to_string(index=False))

    (cfg.TABLES / "main_context.json").write_text(json.dumps({
        "best_norm": best_norm,
        "n_common_windows": int(len(common)),
        "n_common_trials": int(common.trial_id.nunique()),
        "n_subjects": int(common.subject.nunique()),
        "eeg_all_windows_balanced_accuracy": float(ref["balanced_accuracy"]),
        "eeg_all_windows_trial_balanced_accuracy": float(
            ref["trial_balanced_accuracy"]),
        "n_all_windows": int(len(df)),
    }, indent=2))
    np.save(cfg.CACHE / "confusions_loso.npy",
            np.stack([confusions[a] for a in ARMS]))

    make_figure()

    print(f"\ndone in {time.time() - t0:.1f}s")
    return 0



def make_figure() -> None:
    """Rebuild the modality figure from the saved tables.

    Kept separate from the fitting so layout can be revised without paying for
    another 13 minutes of leave-one-subject-out cross-validation.
    """
    summary = pd.read_csv(cfg.TABLES / "loso_summary.csv").set_index("arm")
    per_subj = pd.read_csv(cfg.TABLES / "loso_per_subject.csv")
    confusions = np.load(cfg.CACHE / "confusions_loso.npy")
    ctx = json.loads((cfg.TABLES / "main_context.json").read_text())

    # Eight EMG recordings are missing from the release, so a handful of people
    # contribute fewer than three speeds. Balanced accuracy is not comparable
    # for those, so the per-subject spread is drawn from complete subjects only.
    df = pd.read_parquet(cfg.CACHE / "features_2s.parquet")
    df = df[df["kept"]]
    emg_cols = datasets.feature_columns(df, "emg_")
    common = df[df[emg_cols].notna().all(axis=1)]
    speeds_per_subject = common.groupby("subject", observed=True)["speed"].nunique()
    complete = set(speeds_per_subject[speeds_per_subject == 3].index)
    per_subj = per_subj[per_subj["group"].isin(complete)]
    n_sub = ctx["n_subjects"]

    fig = plt.figure(figsize=(11, 7.6))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.1, 1], hspace=0.42, wspace=0.36)

    panels = [
        (0, "balanced_accuracy", "Every two second window", "upper center"),
        (1, "trial_balanced_accuracy", "Whole recording\n(vote across its windows)",
         "lower right"),
    ]
    for col, key, title, legend_loc in panels:
        ax = fig.add_subplot(gs[0, col])
        vals = [float(summary.loc[a, key]) for a in ARMS]
        viz.bar_with_values(ax, list(ARMS), vals, [viz.ARM_COLORS[a] for a in ARMS])
        viz.chance_line(ax)
        ax.set_ylim(0, 1.14)
        ax.set_yticks(np.arange(0, 1.01, 0.2))
        ax.set_ylabel("balanced accuracy")
        ax.set_title(title)
        ax.legend(loc=legend_loc, fontsize=7.5)

    ax = fig.add_subplot(gs[0, 2])
    data = [per_subj.loc[per_subj.arm == a, "balanced_accuracy"].to_numpy()
            for a in ARMS]
    parts = ax.violinplot(data, showmeans=False, showextrema=False, widths=0.8)
    for pc, arm in zip(parts["bodies"], ARMS):
        pc.set_facecolor(viz.ARM_COLORS[arm])
        pc.set_alpha(0.3)
    rng = np.random.default_rng(cfg.RANDOM_SEED)
    for i, (arm, d) in enumerate(zip(ARMS, data), start=1):
        ax.scatter(i + rng.uniform(-0.1, 0.1, len(d)), d, s=9,
                   color=viz.ARM_COLORS[arm], alpha=0.7, linewidths=0, zorder=3)
        ax.hlines(np.median(d), i - 0.3, i + 0.3, color="#212529", lw=1.8, zorder=4)
    viz.chance_line(ax)
    ax.set_xticks(range(1, 4), ARMS)
    ax.set_ylim(0, 1.14)
    ax.set_yticks(np.arange(0, 1.01, 0.2))
    ax.set_ylabel("balanced accuracy")
    ax.set_title(f"Spread across the {len(data[0])} people\n"
                 "who have all three speeds")
    ax.legend(loc="lower right", fontsize=7.5)

    for i, arm in enumerate(ARMS):
        axc = fig.add_subplot(gs[1, i])
        viz.plot_confusion(
            axc, confusions[i],
            f"{arm}\nbalanced acc = {float(summary.loc[arm, 'balanced_accuracy']):.3f}",
        )

    fig.suptitle(
        f"Guessing walking speed, holding out one person at a time, {n_sub} people\n"
        f"Random forest, features scaled per person, "
        f"{ctx['n_common_windows']} windows from {ctx['n_common_trials']} recordings",
        fontsize=11, fontweight="bold", y=0.99,
    )
    viz.save(fig, "03_modality_comparison")

if __name__ == "__main__":
    sys.exit(main())
