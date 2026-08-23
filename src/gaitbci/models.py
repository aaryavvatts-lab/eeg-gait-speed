"""Classifier definitions.

The Random Forest is the model the source material specifies and is the one
whose numbers are reported as headline results. The others exist to make those
numbers interpretable: a stratified dummy fixes the floor, logistic regression
shows how much of the problem is linearly separable, and gradient boosting
indicates whether a stronger learner would change the conclusion.
"""
from __future__ import annotations

from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from . import config as cfg


def random_forest() -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=cfg.N_TREES,
        class_weight="balanced_subsample",
        random_state=cfg.RANDOM_SEED,
        n_jobs=cfg.N_JOBS,
    )


def dummy() -> DummyClassifier:
    return DummyClassifier(strategy="stratified", random_state=cfg.RANDOM_SEED)


def logistic() -> Pipeline:
    return Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=cfg.RANDOM_SEED,
                ),
            ),
        ]
    )


def gradient_boosting() -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(random_state=cfg.RANDOM_SEED)


REGISTRY = {
    "dummy": dummy,
    "logistic": logistic,
    "random_forest": random_forest,
    "gradient_boosting": gradient_boosting,
}


def build(name: str):
    return REGISTRY[name]()
