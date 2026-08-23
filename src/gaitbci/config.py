"""Paths, constants and analysis parameters.

Every magic number used anywhere in the pipeline lives here so that the
report can quote the configuration without hunting through modules.
"""
from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
DATASET = (
    ROOT
    / "a-multimodal-gait-dataset-of-brain-activity-muscle-activity-"
      "kinematics-and-ground-forces-in-young-adults-1.0.0"
    / "Dataset"
)
EEG_DIR = DATASET / "EEG_Data" / "EEG.csv"
EMG_DIR = DATASET / "EMG_Data"
SUBJECT_INFO = DATASET / "subject-info.csv"

CACHE = ROOT / "cache"
RESULTS = ROOT / "results"
FIGURES = RESULTS / "figures"
TABLES = RESULTS / "tables"
MODELS = RESULTS / "models"
REPORT = ROOT / "report"

for _d in (CACHE, FIGURES, TABLES, MODELS, REPORT):
    _d.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Acquisition constants (read from the EEG file headers, verified across all 177)
# --------------------------------------------------------------------------
EEG_SFREQ = 300.0          # Hz
EEG_N_SAMPLES = 17960      # identical in every file (59.87 s)
EEG_HEADER_LINES = 16      # lines 0-15; line 15 holds the column names
MAINS_HZ = 60.0            # from "# Mains_Frequency_(Hz) =,60"

EMG_SFREQ = 16.049         # nominal; per-file timestamps are used for alignment

SPEEDS = ("0.5", "0.75", "1")
SPEED_MS = {"0.5": 0.5, "0.75": 0.75, "1": 1.0}
SPEED_LABEL = {"0.5": "0.50 m/s", "0.75": "0.75 m/s", "1": "1.00 m/s"}

N_SUBJECTS_RAW = 59
# S32 excluded: EEG.csv/S32_1_raw.csv carries a corrupted montage header
# ("Time,P3,C3,F3,Fz,C4,T3,A2,F6,?,Fp1,?,?,C2,???,...") that does not match the
# other 176 files, so its column -> electrode mapping cannot be trusted.
# Dropping a single speed would leave the subject class-imbalanced, so all
# three of its trials are removed.
EXCLUDED_SUBJECTS = ("S32",)

# EMG recordings absent from the release (documented in EMG_Data/README.txt)
EMG_MISSING = (
    "S3_0.75", "S3_1", "S8_0.5", "S11_1",
    "S43_1", "S50_0.5", "S50_0.75", "S50_1",
)

# --------------------------------------------------------------------------
# EEG channel layout
# --------------------------------------------------------------------------
# Raw CSV column order (0-indexed), from header line 15:
#   0=Time 1=P3 2=C3 3=F3 4=Fz 5=F4 6=C4 7=P4 8=Cz 9=CM 10=A1 11=Fp1 12=Fp2
#   13=T3 14=T5 15=O1 16=O2 17=X3 18=X2 19=F7 20=F8 21=X1 22=A2 23=T6 24=T4
#   25=Trigger
COL_A1, COL_A2 = 10, 22

# Standard 10-20 output order. `None` marks Pz, which was the hardware
# reference and therefore has no column of its own. It is reconstructed as a
# zero vector, exactly as the dataset's own EEG_referencing.m does.
CHANNEL_COLUMNS: tuple[tuple[str, int | None], ...] = (
    ("Fp1", 11), ("Fp2", 12), ("F7", 19), ("F3", 3), ("Fz", 4),
    ("F4", 5), ("F8", 20), ("T7", 13), ("C3", 2), ("Cz", 8),
    ("C4", 6), ("T8", 24), ("P7", 14), ("P3", 1), ("Pz", None),
    ("P4", 7), ("P8", 23), ("O1", 15), ("O2", 16),
)
CHANNELS = tuple(name for name, _ in CHANNEL_COLUMNS)
N_CHANNELS = len(CHANNELS)  # 19

# Channels most exposed to ocular, neck-muscle and jaw contamination. Used by
# the frontal/temporal ablation in the confound analysis.
RIM_CHANNELS = ("Fp1", "Fp2", "F7", "F8", "T7", "T8")
MOTOR_CHANNELS = ("C3", "Cz", "C4")

# --------------------------------------------------------------------------
# Preprocessing
# --------------------------------------------------------------------------
BANDPASS = (1.0, 45.0)     # Hz; upper edge kept clear of the 60 Hz mains
NOTCH_HZ = (60.0, 120.0)
FILTER_ORDER = 4

WINDOW_SEC = 2.0
HOP_SEC = 1.0
WINDOW_SEC_ALT = 4.0       # sensitivity check
HOP_SEC_ALT = 2.0

# Window rejection: drop a window if any channel swings wider than
# median + REJECT_MAD * MAD of that channel's own swing across the same
# recording. Done per recording so it adapts to each headset fitting rather
# than punishing whoever happened to get a noisy one.
REJECT_MAD = 5.0

# --------------------------------------------------------------------------
# Features
# --------------------------------------------------------------------------
BANDS = {
    "delta": (1.0, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta": (13.0, 30.0),
    "gamma": (30.0, 45.0),
}
# The reel specifies only these three; kept as a named subset so the
# literal-recipe variant can be reproduced exactly.
REEL_BANDS = ("alpha", "beta", "gamma")
WELCH_NPERSEG = 300        # 1 Hz frequency resolution at 300 Hz

EMG_MUSCLES = (
    "R_tib_ant", "L_tib_ant", "R_vast_lat", "L_vast_lat",
    "R_rect_fem", "L_rect_fem", "R_gastroc_med", "L_gastroc_med",
    "R_semitend", "L_semitend", "R_gastroc_lat", "L_gastroc_lat",
)
N_MUSCLES = len(EMG_MUSCLES)  # 12
# Plausible step-frequency range while walking at 0.5-1.0 m/s
CADENCE_BAND = (0.4, 3.0)

# --------------------------------------------------------------------------
# Modelling
# --------------------------------------------------------------------------
RANDOM_SEED = 1337
N_TREES = 500
CV_FOLDS = 5
N_PERMUTATIONS = 200
N_JOBS = -1

# Real-time demo
SMOOTH_WINDOWS = 5         # rolling-mode length for command smoothing
