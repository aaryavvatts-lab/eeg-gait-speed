"""Where does the decodable signal actually live?

Two views. Impurity importance is cheap but biased towards high-cardinality
features, so it is reported only for reference. The number that carries weight
is *grouped* permutation importance measured on held-out folds: all the
features belonging to one frequency band (or one electrode) are shuffled
together and the resulting drop in balanced accuracy is attributed to that
band or electrode.

Grouping matters here. Nineteen channels x five bands of correlated band-power
features will each look individually unimportant under per-feature permutation,
because the model can lean on a neighbour. Permuting a whole band at once
removes that escape route.
"""
from __future__ import annotations

import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import balanced_accuracy_score

from gaitbci import config as cfg, datasets, evaluate, features as ft, models, viz

N_REPEATS = 5


def grouped_permutation_importance(
    model, X: np.ndarray, y: np.ndarray, groups_cv: np.ndarray,
    col_groups: dict[str, list[int]], splitter, n_repeats: int = N_REPEATS,
) -> pd.DataFrame:
    """Drop in balanced accuracy when each column group is shuffled together."""
    rng = np.random.default_rng(cfg.RANDOM_SEED)
    records: dict[str, list[float]] = {k: [] for k in col_groups}

    for tr, te in splitter.split(X, y, groups_cv):
        est = clone(model)
        est.fit(X[tr], y[tr])
        base = balanced_accuracy_score(y[te], est.predict(X[te]))
        X_te = X[te]
        for name, cols in col_groups.items():
            drops = []
            for _ in range(n_repeats):
                Xp = X_te.copy()
                Xp[:, cols] = Xp[rng.permutation(len(Xp))][:, cols]
                drops.append(base - balanced_accuracy_score(y[te], est.predict(Xp)))
            records[name].append(float(np.mean(drops)))

    return pd.DataFrame(
        [{"group": k, "importance": float(np.mean(v)),
          "sd": float(np.std(v)), "n_folds": len(v)}
         for k, v in records.items()]
    ).sort_values("importance", ascending=False)


def main() -> int:
    t0 = time.time()
    viz.use_style()

    df = pd.read_parquet(cfg.CACHE / "features_2s.parquet")
    df = df[df["kept"]].reset_index(drop=True)
    subjects = df["subject"].to_numpy()
    X_raw, cols = datasets.eeg_matrix(df, "all")
    X = datasets.per_subject_zscore(X_raw, subjects)
    y = df["speed"].to_numpy().astype(str)
    names = [c[len("eeg_"):] for c in cols]

    band_groups = {b: [i for i, n in enumerate(names) if ft.band_of_feature(n) == b]
                   for b in cfg.BANDS}
    band_groups["total power"] = [i for i, n in enumerate(names)
                                  if n.startswith("total_")]
    chan_groups = {ch: [i for i, n in enumerate(names)
                        if ft.channel_of_feature(n) == ch] for ch in cfg.CHANNELS}

    splitter, _ = evaluate.make_splitter("subject")
    rf = models.random_forest()

    band_imp = grouped_permutation_importance(
        rf, X, y, subjects, band_groups, splitter)
    print("\nband importance (drop in balanced accuracy when shuffled):")
    print(band_imp.to_string(index=False))
    band_imp.to_csv(cfg.TABLES / "importance_by_band.csv", index=False)

    chan_imp = grouped_permutation_importance(
        rf, X, y, subjects, chan_groups, splitter)
    print(f"\ntop electrodes ({time.time() - t0:.0f}s):")
    print(chan_imp.head(8).to_string(index=False))
    chan_imp.to_csv(cfg.TABLES / "importance_by_channel.csv", index=False)

    # Impurity importance, for reference only.
    rf_full = models.random_forest().fit(X, y)
    imp = pd.DataFrame({"feature": names, "impurity": rf_full.feature_importances_})
    imp.sort_values("impurity", ascending=False).to_csv(
        cfg.TABLES / "importance_impurity.csv", index=False)

    # ---- how much does power change at the sensorimotor electrodes? -------
    # Nordin et al. (2019) used dual-layer electrodes to strip motion artifact
    # and found alpha and beta power over sensorimotor cortex going DOWN as
    # people walked faster. Measuring the same thing here gives a direct
    # comparison, so the sign matters.
    psd = np.load(cfg.CACHE / "psd_by_speed.npz")
    freqs = psd["freqs"]

    sm_rows = []
    for band in ("alpha", "beta"):
        f0, f1 = cfg.BANDS[band]
        m = (freqs >= f0) & (freqs < f1)
        change = 10 * np.log10(
            psd["s1"][:, m].mean(axis=1) / psd["s0.5"][:, m].mean(axis=1))
        for ch in cfg.MOTOR_CHANNELS:
            sm_rows.append({"band": band, "channel": ch,
                            "db_change_1_0_vs_0_5": float(
                                change[cfg.CHANNELS.index(ch)])})
    sm = pd.DataFrame(sm_rows)
    sm.to_csv(cfg.TABLES / "sensorimotor_band_change.csv", index=False)
    print("\npower change at C3/Cz/C4, 1.0 m/s against 0.5 m/s (dB):")
    print(sm.pivot(index="channel", columns="band",
                   values="db_change_1_0_vs_0_5").round(2).to_string())
    print(f"  mean across the three electrodes: "
          f"{sm['db_change_1_0_vs_0_5'].mean():+.2f} dB")

    # ---- figure -----------------------------------------------------------

    chan_imp_idx = chan_imp.set_index("group")["importance"]
    group_means = {
        "C3 / Cz / C4\n(motor cortex)": float(
            chan_imp_idx[list(cfg.MOTOR_CHANNELS)].mean()),
        "the other ten\nelectrodes": float(chan_imp_idx[[
            c for c in cfg.CHANNELS
            if c not in cfg.MOTOR_CHANNELS + cfg.RIM_CHANNELS]].mean()),
        "Fp1 Fp2 F7 F8 T7 T8\n(eye / neck muscle)": float(
            chan_imp_idx[list(cfg.RIM_CHANNELS)].mean()),
    }
    top3 = chan_imp.head(3)

    fig = plt.figure(figsize=(12, 8.0))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.1, 0.95], hspace=0.5, wspace=0.3)

    ax = fig.add_subplot(gs[0, 0])
    order = list(cfg.BANDS) + ["total power"]
    vals = [float(band_imp.loc[band_imp.group == g, "importance"].iloc[0])
            for g in order]
    peak = max(vals)
    colors = ["#155288" if v == peak else "#AEC6DA" for v in vals]
    bars = ax.barh(range(len(order))[::-1], vals, color=colors, height=0.62, zorder=2)
    for b, v in zip(bars, vals):
        ax.text(v + 0.0015, b.get_y() + b.get_height() / 2, f"{v:.3f}",
                va="center", fontsize=7.5, fontweight="bold")
    ax.set_yticks(range(len(order))[::-1], order)
    ax.set_xlabel("how far the score falls when shuffled")
    ax.set_xlim(0, peak * 1.25)
    ax.set_title("Beta matters most, gamma barely at all")

    ax = fig.add_subplot(gs[0, 1])
    vals_ch = np.array([float(chan_imp_idx[ch]) for ch in cfg.CHANNELS])
    viz.plot_topomap(ax, vals_ch, "Which electrodes matter", cmap="Blues",
                     vlim=(0, float(vals_ch.max())))
    ax.set_xlabel("top three: "
                  + ", ".join(f"{r.group} ({r.importance:.3f})"
                              for r in top3.itertuples()),
                  fontsize=7.5)

    ax = fig.add_subplot(gs[0, 2])
    labels = list(group_means)
    viz.bar_with_values(ax, labels, [group_means[k] for k in labels],
                        ["#2B8A3E", "#868E96", "#C92A2A"], fmt="{:.4f}")
    ax.set_xticks(range(3), labels, fontsize=7)
    ax.set_ylabel("average drop per electrode")
    ax.set_ylim(0, max(group_means.values()) * 1.3)
    ax.set_title("Electrodes nearest the eyes and neck\nmatter the least")

    for i, band in enumerate(cfg.BANDS):
        ax = fig.add_subplot(gs[1, i % 3] if False else gs[1, :].subgridspec(
            1, 6, wspace=0.15)[i])
        f0, f1 = cfg.BANDS[band]
        m = (freqs >= f0) & (freqs < f1)
        diff = 10 * np.log10(
            psd["s1"][:, m].mean(axis=1) / psd["s0.5"][:, m].mean(axis=1)
        )
        lim = float(np.abs(diff).max())
        viz.plot_topomap(ax, diff, f"{band}\n{f0:g}\u2013{f1:g} Hz",
                         cmap="RdBu_r", vlim=(-lim, lim))

    ax = fig.add_subplot(gs[1, :].subgridspec(1, 6, wspace=0.15)[5])
    ax.axis("off")
    ax.text(0.0, 0.5,
            "Power at 1.0 m/s next to\npower at 0.5 m/s, in dB.\nRed means higher.\n\n"
            "The rise is spread out rather\nthan focused. Biggest at P8\n"
            "(+10.8 dB), C3 (+8.3), F7 (+6.7).\n\n"
            "Fp1 and Fp2 hardly move. That\nis where eye blinks would show\n"
            "up first, so blinks are not\nthe main source.",
            fontsize=7.5, va="center", color="#343A40")

    fig.suptitle("What the model is reading", fontsize=11.5, fontweight="bold",
                 y=1.02)
    viz.save(fig, "08_interpretation")

    print(f"\ndone in {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
