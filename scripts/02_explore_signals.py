"""Look at the signals before any classifier gets a chance to hide the truth.

Three questions, answered visually:
  1. Is there a speed-dependent difference in the EEG spectrum at all?
  2. Does the EMG show the cadence increase we expect?
  3. Does that cadence appear in the EEG, i.e. is motion artifact present?
"""
from __future__ import annotations

import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal

from gaitbci import config as cfg, datasets, preprocess as pp, viz


def main() -> int:
    t0 = time.time()
    viz.use_style()
    eeg, meta, emg = datasets.load_cache()

    # ---- grand-average PSD per speed --------------------------------------
    psd_by_speed: dict[str, list] = {s: [] for s in cfg.SPEEDS}
    for i, trial in enumerate(meta.itertuples()):
        filtered = pp.filter_trial(eeg[i])
        freqs, psd = signal.welch(
            filtered.astype(np.float64), fs=cfg.EEG_SFREQ,
            nperseg=int(4 * cfg.EEG_SFREQ), axis=-1,
        )
        psd_by_speed[trial.speed].append(psd)
    grand = {s: np.mean(np.stack(v), axis=0) for s, v in psd_by_speed.items()}
    np.savez(cfg.CACHE / "psd_by_speed.npz", freqs=freqs,
             **{f"s{k}": v for k, v in grand.items()})

    band = (freqs >= 1) & (freqs <= 45)

    fig, axes = plt.subplots(1, 3, figsize=(11, 3.5), gridspec_kw={"wspace": 0.28})

    def smooth(v, k=5):
        return np.convolve(v, np.ones(k) / k, mode="same")

    ax = axes[0]
    for s in cfg.SPEEDS:
        ax.semilogy(freqs[band], grand[s][:, band].mean(axis=0),
                    color=viz.SPEED_COLORS[s], lw=1.4, label=cfg.SPEED_LABEL[s])
    for f0, _f1 in cfg.BANDS.values():
        ax.axvline(f0, color="#CED4DA", lw=0.6, zorder=0)
    ax.set_xlabel("frequency (Hz)")
    ax.set_ylabel(r"power spectral density ($\mu V^2$/Hz)")
    ax.set_title("Average EEG spectrum\n(19 channels, 58 people)")
    ax.legend(loc="lower left")
    ax.annotate(
        "the spikes below 10 Hz are the\nstep rhythm and its multiples,\npicked up as movement",
        xy=(4.5, grand["1"][:, band].mean(axis=0)[np.argmin(np.abs(freqs[band] - 4.5))]),
        xytext=(15, 6000), fontsize=7.5, color="#C92A2A", ha="left",
        arrowprops={"arrowstyle": "->", "color": "#C92A2A", "lw": 1.0},
    )

    ax = axes[1]
    ref = grand["0.5"][:, band].mean(axis=0)
    for s in ("0.75", "1"):
        rel = smooth(10 * np.log10(grand[s][:, band].mean(axis=0) / ref))
        ax.plot(freqs[band][3:-3], rel[3:-3], color=viz.SPEED_COLORS[s], lw=1.7,
                label=cfg.SPEED_LABEL[s])
    ax.axhline(0, color=viz.GREY, lw=1.0, ls="--", label="0.50 m/s (reference)")
    ax.set_xlabel("frequency (Hz)")
    ax.set_ylabel("power relative to 0.50 m/s (dB)")
    ax.set_title("Walking faster raises power at\nevery frequency, most below 10 Hz")
    ax.legend()

    # ---- cadence from the EMG envelopes -----------------------------------
    cad_rows = []
    for tid, rec in emg.items():
        speed = tid.rsplit("_", 1)[1]
        times, mav = rec["times"], rec["mav"]
        fs_env = 1.0 / float(np.median(np.diff(times)))
        centred = mav.astype(np.float64) - mav.mean(axis=1, keepdims=True)
        spec = np.abs(np.fft.rfft(centred, axis=1))
        fr = np.fft.rfftfreq(mav.shape[1], d=1.0 / fs_env)
        m = (fr >= cfg.CADENCE_BAND[0]) & (fr <= cfg.CADENCE_BAND[1])
        peak = fr[m][np.argmax(spec[:, m].mean(axis=0))]
        cad_rows.append({"trial_id": tid, "speed": speed, "cadence_hz": float(peak)})
    cad = pd.DataFrame(cad_rows)
    cad.to_csv(cfg.TABLES / "cadence_by_speed.csv", index=False)

    ax = axes[2]
    data = [cad.loc[cad.speed == s, "cadence_hz"].to_numpy() for s in cfg.SPEEDS]
    bp = ax.boxplot(data, patch_artist=True, widths=0.55,
                    medianprops={"color": "#212529", "lw": 1.5},
                    flierprops={"marker": "o", "ms": 3, "mfc": viz.GREY,
                                "mec": "none", "alpha": 0.6})
    for patch, s in zip(bp["boxes"], cfg.SPEEDS):
        patch.set_facecolor(viz.SPEED_COLORS[s])
        patch.set_alpha(0.8)
        patch.set_edgecolor("#343A40")
    ax.set_xticks(range(1, 4), [cfg.SPEED_LABEL[s] for s in cfg.SPEEDS])
    ax.set_ylabel("dominant EMG envelope frequency (Hz)")
    ax.set_title("Step rhythm speeds up as people\nwalk faster")

    means = [float(np.median(d)) for d in data]
    print("median cadence (Hz):",
          {cfg.SPEED_LABEL[s]: round(m, 2) for s, m in zip(cfg.SPEEDS, means)})

    fig.suptitle("The raw signals, before any model touches them",
                 fontsize=11, fontweight="bold", y=1.04)
    viz.save(fig, "04_signal_overview")

    # ---- one subject, raw vs filtered, all three speeds --------------------
    cz = cfg.CHANNELS.index("Cz")
    sel = meta[meta.subject == meta.subject.iloc[0]]
    fig, axes = plt.subplots(3, 1, figsize=(10, 5.2), sharex=True,
                             gridspec_kw={"hspace": 0.35})
    t = np.arange(int(6 * cfg.EEG_SFREQ)) / cfg.EEG_SFREQ + 20
    lo = int(20 * cfg.EEG_SFREQ)
    hi = lo + len(t)
    for ax, trial in zip(axes, sel.itertuples()):
        raw = eeg[trial.Index, cz, lo:hi]
        filt = pp.filter_trial(eeg[trial.Index])[cz, lo:hi]
        ax.plot(t, raw, color=viz.GREY, lw=0.7, label="raw", alpha=0.8)
        ax.plot(t, filt, color=viz.SPEED_COLORS[trial.speed], lw=1.0,
                label="after filtering")
        ax.set_ylabel(f"{cfg.SPEED_LABEL[trial.speed]}\n" + r"$\mu$V")
        if ax is axes[0]:
            ax.legend(ncols=2, loc="upper right")
    axes[-1].set_xlabel("time (s)")
    fig.suptitle(
        f"Channel Cz, person {sel.subject.iloc[0]}, six seconds at each speed",
        fontsize=11, fontweight="bold", y=0.98,
    )
    viz.save(fig, "05_raw_vs_filtered")

    print(f"done in {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
