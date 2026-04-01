from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class LearnedModel:
    """Thin wrapper so we can keep sklearn optional."""

    pipeline: object

    def predict_proba(self, texts: list[str]):  # type: ignore[no-untyped-def]
        return self.pipeline.predict_proba(texts)


def train_optional_sklearn_model(training_rows: list[tuple[str, int]]) -> Optional[LearnedModel]:
    """
    Trains a simple text classifier (TF-IDF + LogisticRegression) if scikit-learn is available
    and there is enough feedback. Returns None otherwise.
    """
    if len(training_rows) < 20:
        return None

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
        from sklearn.linear_model import LogisticRegression  # type: ignore
        from sklearn.pipeline import Pipeline  # type: ignore
    except Exception:
        return None

    texts = [t for t, _ in training_rows]
    labels = [y for _, y in training_rows]

    # Balanced handles skew (most people like/dislike unevenly at first).
    clf = Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(max_features=20000, ngram_range=(1, 2), stop_words="english")),
            ("lr", LogisticRegression(max_iter=2000, class_weight="balanced")),
        ]
    )
    clf.fit(texts, labels)
    return LearnedModel(clf)

