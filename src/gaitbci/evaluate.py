"""Cross-validation schemes, metrics and the permutation test.

The central object is an out-of-fold prediction vector: every window is
predicted exactly once, by a model that never saw it during training. All
metrics are computed from that vector, which keeps the leaky and honest
evaluations structurally identical and therefore directly comparable.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.base import clone
from sklearn.metrics import (
    balanced_accuracy_score,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut, StratifiedKFold

from . import config as cfg

SPEED_ORDER = list(cfg.SPEEDS)
SPEED_RANK = {s: i for i, s in enumerate(SPEED_ORDER)}


# --------------------------------------------------------------------------
# Splitters
# --------------------------------------------------------------------------
def make_splitter(scheme: str, n_splits: int = cfg.CV_FOLDS):
    """Return ``(splitter, needs_groups)`` for a named CV scheme.

    ``random``   stratified K-fold over windows, ignoring who they came from.
                 This is the split implied by the source material and it leaks
                 badly: consecutive windows overlap by 50%, so near-duplicates
                 land on both sides of the split.
    ``trial``    grouped by recording. Removes within-trial duplication but a
                 subject's other two trials still sit in the training set.
    ``subject``  grouped by person. The only split that answers the question a
                 wheelchair actually poses: does this work on someone new?
    ``loso``     leave-one-subject-out; same idea, maximum folds.
    """
    if scheme == "random":
        return StratifiedKFold(
            n_splits=n_splits, shuffle=True, random_state=cfg.RANDOM_SEED
        ), False
    if scheme in ("trial", "subject"):
        return GroupKFold(n_splits=n_splits), True
    if scheme == "loso":
        return LeaveOneGroupOut(), True
    raise ValueError(f"unknown CV scheme: {scheme!r}")


def group_vector(df: pd.DataFrame, scheme: str) -> np.ndarray | None:
    if scheme == "random":
        return None
    if scheme == "trial":
        return df["trial_id"].to_numpy()
    return df["subject"].to_numpy()


# --------------------------------------------------------------------------
# Cross-validation
# --------------------------------------------------------------------------
def cross_val_predict_oof(
    model, X: np.ndarray, y: np.ndarray, groups: np.ndarray | None, splitter
) -> tuple[np.ndarray, np.ndarray]:
    """Out-of-fold predictions plus the fold index each row was tested in."""
    y_pred = np.empty(len(y), dtype=object)
    fold_of = np.full(len(y), -1, dtype=int)
    split = splitter.split(X, y, groups) if groups is not None else splitter.split(X, y)
    for k, (tr, te) in enumerate(split):
        est = clone(model)
        est.fit(X[tr], y[tr])
        y_pred[te] = est.predict(X[te])
        fold_of[te] = k
    if (fold_of < 0).any():
        raise RuntimeError("some rows were never held out")
    return y_pred.astype(str), fold_of


def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Standard classification metrics plus two ordinal ones.

    Speed is ordered, so not all errors are equal: calling a 1.0 m/s window
    0.5 m/s is a worse failure for a wheelchair than calling it 0.75 m/s.
    ``distant_error_rate`` counts only the two-step mistakes.
    """
    rt = np.array([SPEED_RANK[s] for s in y_true])
    rp = np.array([SPEED_RANK[s] for s in y_pred])
    rho = spearmanr(rt, rp).statistic if len(np.unique(rp)) > 1 else 0.0
    return {
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "accuracy": float(np.mean(y_true == y_pred)),
        "macro_f1": f1_score(y_true, y_pred, average="macro"),
        "kappa": cohen_kappa_score(y_true, y_pred),
        "distant_error_rate": float(np.mean(np.abs(rt - rp) == 2)),
        "spearman_rho": float(rho),
        "n": int(len(y_true)),
    }


def confusion(y_true: np.ndarray, y_pred: np.ndarray, normalize: str = "true"):
    return confusion_matrix(
        y_true, y_pred, labels=SPEED_ORDER, normalize=normalize
    )


def trial_level(df: pd.DataFrame, y_pred: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Collapse window predictions to one majority-vote verdict per recording.

    This is the number worth quoting for a device: a controller integrates over
    seconds, it does not act on a single 2-second window.
    """
    tmp = pd.DataFrame(
        {"trial_id": df["trial_id"].to_numpy(),
         "speed": df["speed"].to_numpy(),
         "pred": y_pred}
    )
    voted = (
        tmp.groupby("trial_id", observed=True)
        .agg(true=("speed", "first"),
             pred=("pred", lambda s: s.value_counts().idxmax()))
    )
    return voted["true"].to_numpy(), voted["pred"].to_numpy()


def per_group_scores(
    y_true: np.ndarray, y_pred: np.ndarray, groups: np.ndarray
) -> pd.DataFrame:
    """Balanced accuracy computed separately for each held-out group."""
    rows = []
    for g in pd.unique(groups):
        m = groups == g
        rows.append({"group": g,
                     "balanced_accuracy": balanced_accuracy_score(y_true[m], y_pred[m]),
                     "n": int(m.sum())})
    return pd.DataFrame(rows)


def evaluate(
    model, X: np.ndarray, df: pd.DataFrame, scheme: str,
    n_splits: int = cfg.CV_FOLDS,
) -> dict:
    """Run one CV scheme end to end and return metrics plus raw predictions."""
    y = df["speed"].to_numpy().astype(str)
    splitter, needs_groups = make_splitter(scheme, n_splits)
    groups = group_vector(df, scheme) if needs_groups else None
    y_pred, fold_of = cross_val_predict_oof(model, X, y, groups, splitter)

    out = metrics(y, y_pred)
    out["scheme"] = scheme
    out["confusion"] = confusion(y, y_pred)
    out["y_pred"] = y_pred
    out["y_true"] = y
    out["fold"] = fold_of

    t_true, t_pred = trial_level(df, y_pred)
    out["trial_balanced_accuracy"] = balanced_accuracy_score(t_true, t_pred)
    out["trial_confusion"] = confusion(t_true, t_pred)
    out["n_trials"] = int(len(t_true))
    return out


# --------------------------------------------------------------------------
# Permutation test
# --------------------------------------------------------------------------
def _permuted_labels(df: pd.DataFrame, rng: np.random.Generator) -> np.ndarray:
    """Shuffle the three speed labels *within* each subject.

    Permuting globally would also destroy the subject structure, producing an
    optimistically low null. Shuffling within subject keeps every person's
    three recordings intact and only scrambles which speed each one is called,
    so the null answers exactly the right question.
    """
    y = df["speed"].to_numpy().astype(str).copy()
    subjects = df["subject"].to_numpy()
    trials = df["trial_id"].to_numpy()
    for s in np.unique(subjects):
        m = subjects == s
        tids = pd.unique(trials[m])
        labels = [df.loc[df["trial_id"] == t, "speed"].iloc[0] for t in tids]
        shuffled = rng.permutation(labels)
        for tid, lab in zip(tids, shuffled):
            y[trials == tid] = lab
    return y


def permutation_test(
    model, X: np.ndarray, df: pd.DataFrame, observed: float,
    n_permutations: int = cfg.N_PERMUTATIONS, scheme: str = "subject",
    n_splits: int = cfg.CV_FOLDS, n_jobs: int = cfg.N_JOBS,
) -> dict:
    """Empirical p-value for a balanced-accuracy score under label permutation."""
    from joblib import Parallel, delayed

    splitter, needs_groups = make_splitter(scheme, n_splits)
    groups = group_vector(df, scheme) if needs_groups else None

    def one(seed: int) -> float:
        rng = np.random.default_rng(seed)
        y_perm = _permuted_labels(df, rng)
        est = clone(model)
        try:
            est.set_params(n_jobs=1)
        except ValueError:
            pass
        y_pred, _ = cross_val_predict_oof(est, X, y_perm, groups, splitter)
        return balanced_accuracy_score(y_perm, y_pred)

    null = Parallel(n_jobs=n_jobs, verbose=0)(
        delayed(one)(cfg.RANDOM_SEED + i) for i in range(n_permutations)
    )
    null = np.asarray(null)
    # +1 in numerator and denominator: the observed value is itself one draw
    # from the null under H0, so this keeps the p-value from ever being 0.
    p = (np.sum(null >= observed) + 1) / (n_permutations + 1)
    return {"null": null, "p_value": float(p), "observed": float(observed),
            "null_mean": float(null.mean()), "null_p95": float(np.percentile(null, 95))}
