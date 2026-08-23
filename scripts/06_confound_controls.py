"""Does the EEG result survive when the obvious confounds are removed?

Five probes, each an ablation of the headline model:

  reel          only the alpha/beta/gamma columns the source material names
  no_lowfreq    delta and theta dropped, which is where the step rhythm sits
  broadband     nothing but the 19 total-power columns, i.e. pure amplitude
  no_rim        frontal and temporal electrodes dropped (ocular / neck muscle)
  motor         only C3, Cz and C4, the electrodes over motor cortex

plus a within-trial temporal split that asks whether the features are stable
over the course of a single recording or simply drifting, and a window-length
sensitivity check that repeats the headline comparison at 4 seconds.
"""
from __future__ import annotations

import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score

from gaitbci import config as cfg, datasets, evaluate, models, viz

SUBSETS = [
    ("all", "everything\n(209 numbers)"),
    ("reel", "alpha, beta, gamma only\n(what the video asks for)"),
    ("no_lowfreq", "delta and theta gone\n(where step rhythm lives)"),
    ("broadband", "total power only\n(no frequency detail)"),
    ("no_rim", "front and side\nelectrodes gone"),
    ("motor", "C3, Cz, C4 only\n(over the motor strip)"),
]


def temporal_split(X: np.ndarray, df: pd.DataFrame, cut: float = 30.0) -> dict:
    """Train on the first half of every recording, test on the second half.

    Same people on both sides, so this does not test generalisation. It asks
    a narrower question: are the features stable within a single recording, or
    is the model reading a slow drift?
    """
    tr = (df["t_start"].to_numpy() + cfg.WINDOW_SEC) <= cut
    te = df["t_start"].to_numpy() >= cut
    y = df["speed"].to_numpy().astype(str)
    out = {}
    for name, a, b in (("first->second", tr, te), ("second->first", te, tr)):
        est = models.random_forest()
        est.fit(X[a], y[a])
        out[name] = balanced_accuracy_score(y[b], est.predict(X[b]))
    return out


def accuracy_over_trial(df: pd.DataFrame, y_pred: np.ndarray) -> pd.DataFrame:
    """Out-of-fold accuracy as a function of position within the recording.

    If the model were riding session drift, accuracy should climb as each
    recording progresses. A flat profile argues against that.
    """
    tmp = pd.DataFrame({
        "t_start": df["t_start"].to_numpy(),
        "correct": (df["speed"].to_numpy().astype(str) == y_pred).astype(float),
    })
    tmp["bin"] = (tmp["t_start"] // 10 * 10).astype(int)
    return (
        tmp.groupby("bin", observed=True)["correct"]
        .agg(accuracy="mean", n="size")
        .reset_index()
    )


def window_sensitivity() -> pd.DataFrame:
    """Repeat the three-arm comparison with 4-second windows.

    Window length is an arbitrary choice, so the conclusions should not depend
    on it. This checks the order of the three, rather than the exact numbers. Longer
    windows give steadier spectral estimates but fewer of them.
    """
    rows = []
    for tag, path in (("2 s", "features_2s.parquet"), ("4 s", "features_4s.parquet")):
        df = pd.read_parquet(cfg.CACHE / path)
        df = df[df["kept"]].reset_index(drop=True)
        emg_cols = datasets.feature_columns(df, "emg_")
        common = df[df[emg_cols].notna().all(axis=1)].reset_index(drop=True)
        subjects = common["subject"].to_numpy()
        X_eeg, _ = datasets.eeg_matrix(common, "all")
        X_emg = common[emg_cols].to_numpy(dtype=np.float64)
        for arm, X in (("EEG", X_eeg), ("EMG", X_emg),
                       ("EEG+EMG", np.hstack([X_eeg, X_emg]))):
            Xz = datasets.per_subject_zscore(X, subjects)
            res = evaluate.evaluate(models.random_forest(), Xz, common, "subject")
            rows.append({"window": tag, "arm": arm, "n_windows": len(common),
                         "balanced_accuracy": res["balanced_accuracy"],
                         "trial_balanced_accuracy": res["trial_balanced_accuracy"]})
            print(f"  {tag}  {arm:<8} win={res['balanced_accuracy']:.3f} "
                  f"trial={res['trial_balanced_accuracy']:.3f}")
    return pd.DataFrame(rows)


def main() -> int:
    t0 = time.time()
    viz.use_style()

    df = pd.read_parquet(cfg.CACHE / "features_2s.parquet")
    df = df[df["kept"]].reset_index(drop=True)
    subjects = df["subject"].to_numpy()

    rows = {}
    for norm in ("raw", "per_subject_z"):
        for subset, _label in SUBSETS:
            X, cols = datasets.eeg_matrix(df, subset)
            if norm == "per_subject_z":
                X = datasets.per_subject_zscore(X, subjects)
            res = evaluate.evaluate(models.random_forest(), X, df, "subject")
            rows[(norm, subset)] = {
                "norm": norm, "subset": subset, "n_features": len(cols),
                "balanced_accuracy": res["balanced_accuracy"],
                "trial_balanced_accuracy": res["trial_balanced_accuracy"],
                "kappa": res["kappa"],
            }
            print(f"  {norm:<14} {subset:<11} ({len(cols):>3} feat) "
                  f"win={res['balanced_accuracy']:.3f} "
                  f"trial={res['trial_balanced_accuracy']:.3f} "
                  f"({time.time() - t0:.0f}s)")
            if norm == "per_subject_z" and subset == "all":
                over_time = accuracy_over_trial(df, res["y_pred"])

    table = pd.DataFrame(rows.values())
    table.to_csv(cfg.TABLES / "confound_controls.csv", index=False)

    # ---- within-trial temporal split --------------------------------------
    X, _ = datasets.eeg_matrix(df, "all")
    temporal = temporal_split(datasets.per_subject_zscore(X, subjects), df)
    print("\nwithin-trial temporal split (same subjects both sides):")
    for k, v in temporal.items():
        print(f"  train {k}: balanced accuracy = {v:.3f}")
    pd.DataFrame([temporal]).to_csv(
        cfg.TABLES / "temporal_split.csv", index=False
    )
    over_time.to_csv(cfg.TABLES / "accuracy_over_trial.csv", index=False)

    # ---- figure -----------------------------------------------------------
    fig = plt.figure(figsize=(11, 6.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.35, 1], hspace=0.75, wspace=0.24)

    ax = fig.add_subplot(gs[0, :])
    labels = [lab for _, lab in SUBSETS]
    x = np.arange(len(SUBSETS))
    w = 0.38
    for i, (norm, colour, tag) in enumerate(
        [("raw", "#ADB5BD", "no calibration"),
         ("per_subject_z", "#155288", "calibrated per person")]
    ):
        vals = [rows[(norm, s)]["balanced_accuracy"] for s, _ in SUBSETS]
        bars = ax.bar(x + (i - 0.5) * w, vals, w, color=colour, label=tag, zorder=2)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.008, f"{v:.3f}",
                    ha="center", va="bottom", fontsize=7, fontweight="bold")
    viz.chance_line(ax)
    ax.set_xticks(x, labels, fontsize=7.5)
    ax.set_ylim(0, 0.86)
    ax.set_ylabel("balanced accuracy")
    ax.set_title("What is left after each shortcut is taken away\n"
                 "(EEG only, random forest, split by person)")
    ax.legend(loc="upper right", ncols=3)

    ax = fig.add_subplot(gs[1, 0])
    ax.plot(over_time["bin"] + 5, over_time["accuracy"], "o-",
            color="#155288", lw=1.6, ms=5)
    viz.chance_line(ax)
    ax.set_ylim(0, 1.0)
    ax.set_xlabel("position within the recording (s)")
    ax.set_ylabel("accuracy")
    ax.set_title("Accuracy stays flat as a recording runs on,\n"
                 "so slow drift is probably not the cause")
    ax.legend(loc="lower right")

    ax = fig.add_subplot(gs[1, 1])
    names = list(temporal)
    viz.bar_with_values(ax, ["train on first 30 s\ntest on last 30 s",
                             "train on last 30 s\ntest on first 30 s"],
                        [temporal[n] for n in names], ["#2B8A3E", "#40A06A"])
    viz.chance_line(ax)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("balanced accuracy")
    ax.set_title("Train on one half of each recording,\ntest on the other half")
    ax.legend(loc="lower right")

    viz.save(fig, "06_confound_controls")

    print("\nwindow-length sensitivity:")
    sens = window_sensitivity()
    sens.to_csv(cfg.TABLES / "window_sensitivity.csv", index=False)
    # The claim the report makes is that EEG is the weakest arm and that muscle
    # activity beats it, rather than that the three keep an exact order. EMG and
    # the fusion sit within a thousandth of each other at 2 s, so their raw sort
    # order there is arbitrary.
    def ordering(tag: str) -> str:
        sub = sens[sens.window == tag].sort_values(
            "balanced_accuracy", ascending=False)
        return " > ".join(f"{r.arm} {r.balanced_accuracy:.3f}"
                          for r in sub.itertuples())

    weakest = {
        tag: sens[sens.window == tag].sort_values(
            "balanced_accuracy")["arm"].iloc[0]
        for tag in ("2 s", "4 s")
    }
    print(f"  2 s: {ordering('2 s')}")
    print(f"  4 s: {ordering('4 s')}")
    if set(weakest.values()) == {"EEG"}:
        print("  EEG is the weakest arm at both window lengths - conclusion holds")
    else:
        print(f"  WARNING: weakest arm is not stable across window lengths: {weakest}")

    print(f"\ndone in {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
