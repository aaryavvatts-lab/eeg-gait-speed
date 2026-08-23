"""Shared plotting style and the figure builders used across the scripts."""
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from . import config as cfg

# Walking speed is ordinal, so the palette is a light-to-dark ramp of one hue
# rather than three arbitrary colours. Readable in greyscale and safe for the
# common colour-vision deficiencies.
SPEED_COLORS = {"0.5": "#8ECAE6", "0.75": "#219EBC", "1": "#023047"}
ARM_COLORS = {"EEG": "#155288", "EMG": "#2B8A3E", "EEG+EMG": "#B5651D"}
ACCENT = "#E8590C"
GREY = "#868E96"
CHANCE = 1 / 3


def use_style() -> None:
    mpl.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 150,
            "savefig.bbox": "tight",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#343A40",
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": "#DEE2E6",
            "grid.linewidth": 0.6,
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.titleweight": "bold",
            "axes.labelsize": 9,
            "legend.frameon": False,
            "legend.fontsize": 8,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
        }
    )


def save(fig, name: str) -> Path:
    path = cfg.FIGURES / f"{name}.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"  figure -> {path.relative_to(cfg.ROOT)}")
    return path


def chance_line(ax, label: str = "chance (33.3%)") -> None:
    ax.axhline(CHANCE, color=ACCENT, ls="--", lw=1.2, zorder=1, label=label)


def plot_confusion(ax, cm: np.ndarray, title: str, cbar: bool = False):
    """Row-normalised confusion matrix with the values written in."""
    im = ax.imshow(cm, cmap="Blues", vmin=0, vmax=1)
    labels = [cfg.SPEED_LABEL[s] for s in cfg.SPEEDS]
    ax.set_xticks(range(3), labels, rotation=30, ha="right")
    ax.set_yticks(range(3), labels)
    ax.set_xlabel("predicted")
    ax.set_ylabel("true")
    ax.set_title(title)
    ax.grid(False)
    for i in range(3):
        for j in range(3):
            ax.text(
                j, i, f"{cm[i, j]:.2f}",
                ha="center", va="center", fontsize=8,
                color="white" if cm[i, j] > 0.55 else "#212529",
                fontweight="bold" if i == j else "normal",
            )
    if cbar:
        plt.colorbar(im, ax=ax, fraction=0.046, shrink=0.85)
    return im


def bar_with_values(ax, labels, values, colors, fmt="{:.3f}", rotation=0):
    bars = ax.bar(labels, values, color=colors, width=0.62, zorder=2)
    # Offset scales with the data so the labels sit just above the bars whether
    # the axis runs 0-1 or 0-0.02.
    pad = 0.025 * max(abs(v) for v in values)
    for b, v in zip(bars, values):
        ax.text(
            b.get_x() + b.get_width() / 2, v + pad, fmt.format(v),
            ha="center", va="bottom", fontsize=8, fontweight="bold",
        )
    if rotation:
        plt.setp(ax.get_xticklabels(), rotation=rotation, ha="right")
    return bars


def montage_positions() -> tuple[np.ndarray, list[str]]:
    """2-D scalp coordinates for the 19-channel montage, via MNE's 10-20 layout."""
    import mne

    info = mne.create_info(list(cfg.CHANNELS), sfreq=cfg.EEG_SFREQ, ch_types="eeg")
    info.set_montage(mne.channels.make_standard_montage("standard_1020"))
    layout = mne.channels.find_layout(info, ch_type="eeg")
    order = [layout.names.index(ch) for ch in cfg.CHANNELS]
    return layout.pos[order, :2], list(cfg.CHANNELS)


def plot_topomap(ax, values: np.ndarray, title: str, cmap: str = "RdBu_r",
                 vlim=None, show_names: bool = False):
    """Scalp map of one value per channel, in :data:`config.CHANNELS` order."""
    import mne

    info = mne.create_info(list(cfg.CHANNELS), sfreq=cfg.EEG_SFREQ, ch_types="eeg")
    info.set_montage(mne.channels.make_standard_montage("standard_1020"))
    im, _ = mne.viz.plot_topomap(
        values, info, axes=ax, show=False, cmap=cmap,
        vlim=vlim if vlim is not None else (None, None),
        names=list(cfg.CHANNELS) if show_names else None,
        contours=4, sensors=True,
    )
    ax.set_title(title)
    return im
