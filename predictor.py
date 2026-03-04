from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
from sklearn.linear_model import LogisticRegression


@dataclass
class Forecast:
    label: str
    probability: float


@dataclass
class PredictionResult:
    next_color: Forecast
    next_size: Forecast
    samples_used: int


def _encode_binary(values: Sequence[str], positive_label: str) -> np.ndarray:
    return np.array([1 if v == positive_label else 0 for v in values], dtype=np.int32)


def _build_windowed_dataset(values: Sequence[str], positive_label: str, window: int = 5) -> tuple[np.ndarray, np.ndarray]:
    if len(values) <= window:
        raise ValueError("Not enough samples for training.")

    numeric = _encode_binary(values, positive_label)
    X, y = [], []
    for i in range(window, len(numeric)):
        X.append(numeric[i - window : i])
        y.append(numeric[i])

    return np.asarray(X), np.asarray(y)


def _fallback_forecast(values: Sequence[str]) -> Forecast:
    counter = Counter(values)
    label, count = counter.most_common(1)[0]
    return Forecast(label=label, probability=count / len(values))


def _ml_forecast(values: Sequence[str], positive_label: str, negative_label: str, window: int = 5) -> Forecast:
    unique_labels = set(values)
    if len(unique_labels) < 2 or len(values) <= window + 1:
        return _fallback_forecast(values)

    X, y = _build_windowed_dataset(values, positive_label=positive_label, window=window)

    if len(set(y.tolist())) < 2:
        return _fallback_forecast(values)

    model = LogisticRegression(max_iter=500)
    model.fit(X, y)

    last_window = _encode_binary(values[-window:], positive_label=positive_label).reshape(1, -1)
    positive_probability = float(model.predict_proba(last_window)[0][1])

    if positive_probability >= 0.5:
        return Forecast(label=positive_label, probability=positive_probability)
    return Forecast(label=negative_label, probability=1.0 - positive_probability)


def predict_next(period_rows: Iterable[dict]) -> PredictionResult:
    rows = list(period_rows)
    if len(rows) < 10:
        raise ValueError("Need at least 10 rows of historical data.")

    colors = [row["color"] for row in rows]
    sizes = [row["size"] for row in rows]

    color_forecast = _ml_forecast(colors, positive_label="green", negative_label="red", window=5)
    size_forecast = _ml_forecast(sizes, positive_label="big", negative_label="small", window=5)

    return PredictionResult(
        next_color=color_forecast,
        next_size=size_forecast,
        samples_used=len(rows),
    )
