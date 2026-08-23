"""How the train/test split alone changes the answer.

Same features, same model, same scoring. The only thing that moves is where
the line between training and testing gets drawn.
This is the experiment that decides whether anything else in the project can
be believed, so it runs first.

The result is not the simple "stricter split, lower score" story one might
expect. Grouping by *recording* lands at chance, below grouping by *subject*,
because subject identity dominates the feature space: with two of a person's
three trials in the training set, the model assigns their held-out trial to one
of the speeds it has already seen from them. The second experiment here
measures that identity signal directly.
"""
from __future__ import annotations

import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

from gaitbci import config as cfg, datasets, evaluate, models, viz

SCHEMES = [
    ("random", "Split at random\nover windows", "#C92A2A",
     "windows from one recording\nend up on both sides"),
    ("trial", "Split by\nrecording", "#F08C00",
     "whole recordings kept together,\nbut the person is still in training"),
    ("subject", "Split by\nperson", "#2B8A3E",
     "tested on people the model\nhas never seen"),
]


def subject_identifiability(X: np.ndarray, df: pd.DataFrame) -> float:
    """Accuracy of predicting *who* a window came from, on held-out recordings.

    Chance is 1/58. Anything far above it means the band-power features are
    dominated by things that stay fixed about a person, such as skull, hair
    and how the electrodes sat, and
    that is what makes recording-level grouping unsafe.
    """
    y = df["subject"].to_numpy()
    groups = df["trial_id"].to_numpy()
    pred = np.empty(len(y), dtype=object)
    for tr, te in GroupKFold(n_splits=cfg.CV_FOLDS).split(X, y, groups):
        est = models.random_forest()
        est.fit(X[tr], y[tr])
        pred[te] = est.predict(X[te])
    return float(np.mean(pred.astype(str) == y))


def main() -> int:
    t0 = time.time()
    viz.use_style()

    df = pd.read_parquet(cfg.CACHE / "features_2s.parquet")
    df = df[df["kept"]].reset_index(drop=True)
    X, cols = datasets.eeg_matrix(df, "all")
    print(f"windows={len(df)}  features={len(cols)}  subjects={df.subject.nunique()}")

    rows, results = [], {}
    for scheme, _, _, _ in SCHEMES:
        res = evaluate.evaluate(models.random_forest(), X, df, scheme)
        results[scheme] = res
        rows.append(
            {
                "scheme": scheme,
                "balanced_accuracy": res["balanced_accuracy"],
                "macro_f1": res["macro_f1"],
                "kappa": res["kappa"],
                "distant_error_rate": res["distant_error_rate"],
                "n_windows": res["n"],
            }
        )
        print(f"  {scheme:<8} balanced accuracy = {res['balanced_accuracy']:.3f}  "
              f"kappa = {res['kappa']:+.3f}  ({time.time() - t0:.0f}s)")

    table = pd.DataFrame(rows)
    table.to_csv(cfg.TABLES / "leakage_comparison.csv", index=False)

    honest = table.loc[table.scheme == "subject", "balanced_accuracy"].iloc[0]
    leaky = table.loc[table.scheme == "random", "balanced_accuracy"].iloc[0]
    print(f"\ninflation from leakage: {leaky:.3f} -> {honest:.3f} ({honest - leaky:+.3f})")
    if leaky - honest < 0.15:
        print("WARNING: the two splits agree too closely, check the grouping")

    id_acc = subject_identifiability(X, df)
    chance_id = 1 / df["subject"].nunique()
    print(f"subject identifiability: {id_acc:.3f} (chance {chance_id:.3f}, "
          f"{id_acc / chance_id:.0f}x)")
    pd.DataFrame(
        [{"subject_id_accuracy": id_acc, "chance": chance_id,
          "lift": id_acc / chance_id, "n_subjects": df["subject"].nunique()}]
    ).to_csv(cfg.TABLES / "subject_identifiability.csv", index=False)

    # ---- figure 1: the split decides the answer ---------------------------
    fig = plt.figure(figsize=(10, 6.9))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.3, 1], hspace=0.78, wspace=0.32)

    ax = fig.add_subplot(gs[0, :])
    viz.bar_with_values(
        ax,
        [lab for _, lab, _, _ in SCHEMES],
        [results[s]["balanced_accuracy"] for s, _, _, _ in SCHEMES],
        [c for _, _, c, _ in SCHEMES],
    )
    viz.chance_line(ax)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("balanced accuracy")
    ax.set_title(
        "One model, one set of features, three ways of splitting the data\n"
        "Only the green bar answers the question a real device would face"
    )
    ax.legend(loc="upper right")
    for i, (_, _, _, note) in enumerate(SCHEMES):
        ax.annotate(
            note, xy=(i, 0), xycoords=("data", "axes fraction"),
            xytext=(0, -34), textcoords="offset points",
            ha="center", va="top", fontsize=7.5, color="#495057", style="italic",
        )

    for i, (scheme, lab, _, _) in enumerate(SCHEMES):
        axc = fig.add_subplot(gs[1, i])
        viz.plot_confusion(
            axc, results[scheme]["confusion"],
            f"{lab.replace(chr(10), ' ')}\n"
            f"balanced acc = {results[scheme]['balanced_accuracy']:.3f}",
        )

    fig.suptitle("Random forest on EEG band power, two second windows",
                 fontsize=11, fontweight="bold", y=0.985)
    viz.save(fig, "01_leakage_comparison")

    # ---- figure 2: why recording-level grouping fails ---------------------
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.0),
                             gridspec_kw={"width_ratios": [1, 1.35], "wspace": 0.35})

    ax = axes[0]
    viz.bar_with_values(
        ax, ["name the\nwalking speed", "name the\nperson"],
        [honest, id_acc], ["#155288", "#B5651D"],
    )
    ax.axhline(cfg.SPEED_MS and 1 / 3, color=viz.ACCENT, ls="--", lw=1.2,
               label="chance, speed (33.3%)")
    ax.axhline(chance_id, color=GREY_LINE, ls=":", lw=1.2,
               label=f"chance, identity ({chance_id:.1%})")
    ax.set_ylim(0, 0.75)
    ax.set_ylabel("accuracy")
    ax.set_title("What the features really carry")
    ax.legend(loc="upper left")

    ax = axes[1]
    viz.plot_confusion(
        ax, results["trial"]["confusion"],
        "Split by recording: real 1.0 m/s gets\ncalled 0.75 m/s more often than it gets called right",
        cbar=True,
    )
    fig.suptitle(
        "EEG band power picks out the person far better than the speed,\n"
        "and that is what breaks the split by recording",
        fontsize=10.5, fontweight="bold", y=1.02,
    )
    viz.save(fig, "02_subject_fingerprint")

    print(f"\ndone in {time.time() - t0:.1f}s")
    return 0


GREY_LINE = "#868E96"

if __name__ == "__main__":
    sys.exit(main())
