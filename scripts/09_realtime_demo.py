"""Turn the classifier into something a wheelchair could actually run on.

A held-out person's three recordings are spliced end to end and pushed through
the model one 2-second window at a time, at 1-second hops. Raw per-window
predictions are then smoothed by a rolling mode and gated by a hold rule, so
the emitted command cannot chatter between speeds on a single noisy window.

The demo subject is the one whose leave-one-subject-out accuracy is closest to
the median, so the picture is representative rather than flattering. The splice
points are artificial, since these are three separate recordings rather than
one continuous walk, but they are the only speed changes the dataset has,
and they are what a controller would have to survive.
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

from gaitbci import config as cfg, datasets, models, viz

HOLD = 2  # consecutive agreeing windows required before the command changes


def rolling_mode(labels: np.ndarray, k: int) -> np.ndarray:
    """Majority vote over the trailing ``k`` predictions (causal)."""
    out = np.empty(len(labels), dtype=object)
    for i in range(len(labels)):
        window = labels[max(0, i - k + 1) : i + 1]
        vals, counts = np.unique(window, return_counts=True)
        out[i] = vals[np.argmax(counts)]
    return out.astype(str)


def apply_hold(smoothed: np.ndarray, hold: int = HOLD) -> np.ndarray:
    """Only switch the emitted command once a new value has persisted."""
    out = np.empty(len(smoothed), dtype=object)
    current = smoothed[0]
    streak = 0
    for i, v in enumerate(smoothed):
        if v == current:
            streak = 0
        else:
            streak += 1
            if streak >= hold:
                current = v
                streak = 0
        out[i] = current
    return out.astype(str)


def transition_latency(true: np.ndarray, command: np.ndarray,
                       hop: float = cfg.HOP_SEC) -> list[dict]:
    """Seconds from each speed change until the command settles on the new speed."""
    events = []
    changes = np.flatnonzero(true[1:] != true[:-1]) + 1
    for idx in changes:
        target = true[idx]
        end = len(true)
        nxt = changes[changes > idx]
        if len(nxt):
            end = int(nxt[0])
        settled = None
        for j in range(idx, end):
            if command[j] == target and np.all(command[j:end] == target):
                settled = j
                break
        events.append({
            "at_s": float(idx * hop),
            "to_speed": str(target),
            "latency_s": None if settled is None else float((settled - idx) * hop),
            "settled": settled is not None,
        })
    return events


def run_arm(arm: str, X_all: np.ndarray, df: pd.DataFrame,
            demo_subject: str) -> dict:
    subjects = df["subject"].to_numpy()
    train = subjects != demo_subject
    test = subjects == demo_subject

    Xz = datasets.per_subject_zscore(X_all, subjects)
    y = df["speed"].to_numpy().astype(str)

    est = models.random_forest()
    est.fit(Xz[train], y[train])

    demo = df[test].sort_values(["speed_ms", "t_start"]).reset_index()
    order = demo["index"].to_numpy()
    raw_pred = est.predict(Xz[order])
    true = y[order]

    smoothed = rolling_mode(raw_pred, cfg.SMOOTH_WINDOWS)
    command = apply_hold(smoothed)

    return {
        "arm": arm,
        "true": true,
        "raw": raw_pred,
        "command": command,
        "window_accuracy": float(np.mean(raw_pred == true)),
        "command_accuracy": float(np.mean(command == true)),
        "transitions": transition_latency(true, command),
    }


def main() -> int:
    t0 = time.time()
    viz.use_style()

    df = pd.read_parquet(cfg.CACHE / "features_2s.parquet")
    df = df[df["kept"]].reset_index(drop=True)
    emg_cols = datasets.feature_columns(df, "emg_")
    common = df[df[emg_cols].notna().all(axis=1)].reset_index(drop=True)

    per_subj = pd.read_csv(cfg.TABLES / "loso_per_subject.csv")
    eeg_scores = per_subj[per_subj.arm == "EEG"]
    median = eeg_scores["balanced_accuracy"].median()
    demo_subject = eeg_scores.iloc[
        (eeg_scores["balanced_accuracy"] - median).abs().argmin()
    ]["group"]
    print(f"demo subject = {demo_subject} "
          f"(LOSO balanced accuracy {float(eeg_scores.loc[eeg_scores.group == demo_subject, 'balanced_accuracy'].iloc[0]):.3f}, "
          f"cohort median {median:.3f})")

    X_eeg, _ = datasets.eeg_matrix(common, "all")
    X_emg = common[emg_cols].to_numpy(dtype=np.float64)
    arms = {"EEG": X_eeg, "EEG+EMG": np.hstack([X_eeg, X_emg])}

    results = [run_arm(a, X, common, demo_subject) for a, X in arms.items()]
    for r in results:
        lat = [e["latency_s"] for e in r["transitions"] if e["settled"]]
        print(f"  {r['arm']:<8} per-window {r['window_accuracy']:.3f}  "
              f"smoothed command {r['command_accuracy']:.3f}  "
              f"latencies {lat}")

    # Raw per-window guesses go out as their own file so the web page can redo
    # the smoothing live while somebody drags a slider. The guesses themselves
    # come from the model and never change; only the smoothing is redone.
    (cfg.TABLES / "realtime_stream.json").write_text(json.dumps({
        "demo_subject": str(demo_subject),
        "hop_s": cfg.HOP_SEC,
        "speeds": list(cfg.SPEEDS),
        "speed_labels": {k: v for k, v in cfg.SPEED_LABEL.items()},
        "truth": [str(v) for v in results[0]["true"]],
        "raw": {r["arm"]: [str(v) for v in r["raw"]] for r in results},
    }))

    (cfg.TABLES / "realtime_demo.json").write_text(json.dumps({
        "demo_subject": str(demo_subject),
        "hop_s": cfg.HOP_SEC,
        "smoothing_windows": cfg.SMOOTH_WINDOWS,
        "hold": HOLD,
        "arms": [{k: v for k, v in r.items()
                  if k not in ("true", "raw", "command")} for r in results],
    }, indent=2))

    # ---- figure -----------------------------------------------------------
    rank = {s: i for i, s in enumerate(cfg.SPEEDS)}
    fig, axes = plt.subplots(len(results), 1, figsize=(11, 5.4), sharex=True,
                             gridspec_kw={"hspace": 0.28})

    for ax, r in zip(np.atleast_1d(axes), results):
        t = np.arange(len(r["true"])) * cfg.HOP_SEC
        true_r = np.array([rank[v] for v in r["true"]], dtype=float)
        raw_r = np.array([rank[v] for v in r["raw"]], dtype=float)
        cmd_r = np.array([rank[v] for v in r["command"]], dtype=float)

        ax.step(t, true_r, where="post", color="#212529", lw=2.4,
                label="real treadmill speed", zorder=4)
        ax.scatter(t, raw_r, s=11, color=viz.GREY, alpha=0.65, linewidths=0,
                   label="raw guess, once a second", zorder=2)
        ax.step(t, cmd_r, where="post", color=viz.ARM_COLORS[r["arm"]], lw=1.9,
                label="smoothed chair command", zorder=3)

        for e in r["transitions"]:
            ax.axvline(e["at_s"], color=viz.ACCENT, ls=":", lw=1.0, zorder=1)

        ax.set_yticks(range(3), [cfg.SPEED_LABEL[s] for s in cfg.SPEEDS])
        ax.set_ylim(-0.45, 2.45)
        ax.set_ylabel("speed")
        ax.set_title(
            f"{r['arm']}: raw windows {r['window_accuracy']:.1%} right, "
            f"smoothed command {r['command_accuracy']:.1%} right",
            loc="left",
        )
        ax.legend(loc="upper left", ncols=3, fontsize=7.5)

    np.atleast_1d(axes)[-1].set_xlabel(
        "time in seconds, three recordings joined end to end")
    fig.suptitle(
        f"Person {demo_subject} streamed through the model, one window at a time\n"
        "The dotted lines are the speed changes the chair has to follow",
        fontsize=11, fontweight="bold", y=1.0,
    )
    viz.save(fig, "09_realtime_demo")

    print(f"\ndone in {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
