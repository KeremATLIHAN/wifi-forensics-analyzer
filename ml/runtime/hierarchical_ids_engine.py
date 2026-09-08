from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import joblib
import numpy as np
import pandas as pd

from ml.runtime.ids_inference_contract import (
    INFERENCE_FEATURES,
    PRIMARY_MODEL_PATH,
    PRIMARY_THRESHOLD,
    ROUTING_FLOOR,
    SPECIALIST_MODEL_PATH,
    SPECIALIST_THRESHOLD,
    MINIMUM_TOTAL_PACKET_COUNT,
    validate_inference_contract,
)


@dataclass(frozen=True)
class IDSDecision:
    label: str
    prediction: int

    primary_probability: float
    specialist_probability: float | None

    decision_path: str
    specialist_used: bool


class HierarchicalIDSEngine:
    """
    CyberLab hierarchical IDS runtime engine.

    Decision policy:

        primary p < ROUTING_FLOOR
            -> BENIGN

        ROUTING_FLOOR <= primary p < PRIMARY_THRESHOLD
            -> SPECIALIST

        primary p >= PRIMARY_THRESHOLD
            -> ATTACK
    """

    def __init__(self) -> None:
        validate_inference_contract()

        primary_artifact = joblib.load(
            PRIMARY_MODEL_PATH
        )

        specialist_artifact = joblib.load(
            SPECIALIST_MODEL_PATH
        )

        self.primary_model = (
            primary_artifact["model"]
        )

        self.specialist_model = (
            specialist_artifact["model"]
        )

        self.features = tuple(
            INFERENCE_FEATURES
        )

        self._validate_artifact_features(
            "primary",
            primary_artifact,
        )

        self._validate_artifact_features(
            "specialist",
            specialist_artifact,
        )

    def _validate_artifact_features(
        self,
        name: str,
        artifact: dict,
    ) -> None:

        artifact_features = tuple(
            artifact["feature_columns"]
        )

        if artifact_features != self.features:
            raise ValueError(
                f"{name} model feature contract mismatch."
            )

    def _prepare_input(
        self,
        feature_values: Mapping[str, float],
    ) -> pd.DataFrame:

        supplied = set(
            feature_values.keys()
        )

        expected = set(
            self.features
        )

        missing = expected - supplied
        unexpected = supplied - expected

        if missing:
            raise ValueError(
                "Missing IDS features: "
                + ", ".join(sorted(missing))
            )

        if unexpected:
            raise ValueError(
                "Unexpected IDS features: "
                + ", ".join(
                    sorted(unexpected)
                )
            )

        values = []

        for feature in self.features:
            value = float(
                feature_values[feature]
            )

            if not np.isfinite(value):
                raise ValueError(
                    "Non-finite IDS feature: "
                    f"{feature}={value}"
                )

            values.append(value)

        return pd.DataFrame(
            [values],
            columns=self.features,
            dtype=np.float64,
        )

    @staticmethod
    def _attack_probability(
        model,
        X: pd.DataFrame,
    ) -> float:

        probability = model.predict_proba(
            X
        )

        if probability.shape != (1, 2):
            raise RuntimeError(
                "Unexpected predict_proba shape: "
                f"{probability.shape}"
            )

        value = float(
            probability[0, 1]
        )

        if not np.isfinite(value):
            raise RuntimeError(
                "Model returned non-finite probability."
            )

        return value

    def predict(
        self,
        feature_values: Mapping[str, float],
    ) -> IDSDecision | None:

        X = self._prepare_input(
            feature_values
        )

        total_packet_count = (
            int(feature_values["Total Fwd Packet"])
            + int(feature_values["Total Bwd packets"])
        )

        if total_packet_count < MINIMUM_TOTAL_PACKET_COUNT:
            return None

        primary_probability = (
            self._attack_probability(
                self.primary_model,
                X,
            )
        )

        # High-confidence benign.
        if primary_probability < ROUTING_FLOOR:
            return IDSDecision(
                label="BENIGN",
                prediction=0,
                primary_probability=(
                    primary_probability
                ),
                specialist_probability=None,
                decision_path="PRIMARY_BENIGN",
                specialist_used=False,
            )

        # High-confidence attack.
        if primary_probability >= PRIMARY_THRESHOLD:
            return IDSDecision(
                label="ATTACK",
                prediction=1,
                primary_probability=(
                    primary_probability
                ),
                specialist_probability=None,
                decision_path="PRIMARY_ATTACK",
                specialist_used=False,
            )

        # Ambiguous region -> specialist.
        specialist_probability = (
            self._attack_probability(
                self.specialist_model,
                X,
            )
        )

        if (
            specialist_probability
            >= SPECIALIST_THRESHOLD
        ):
            return IDSDecision(
                label="ATTACK",
                prediction=1,
                primary_probability=(
                    primary_probability
                ),
                specialist_probability=(
                    specialist_probability
                ),
                decision_path=(
                    "SPECIALIST_ATTACK"
                ),
                specialist_used=True,
            )

        return IDSDecision(
            label="BENIGN",
            prediction=0,
            primary_probability=(
                primary_probability
            ),
            specialist_probability=(
                specialist_probability
            ),
            decision_path=(
                "SPECIALIST_BENIGN"
            ),
            specialist_used=True,
        )


def main() -> None:
    engine = HierarchicalIDSEngine()

    print("=" * 78)
    print("CYBERLAB HIERARCHICAL IDS ENGINE")
    print("=" * 78)

    print(
        f"Features:              "
        f"{len(engine.features)}"
    )

    print(
        f"Primary threshold:     "
        f"{PRIMARY_THRESHOLD:.2f}"
    )

    print(
        f"Routing floor:         "
        f"{ROUTING_FLOOR:.2f}"
    )

    print(
        f"Specialist threshold:  "
        f"{SPECIALIST_THRESHOLD:.2f}"
    )

    print()
    print("Hierarchical IDS engine initialization: OK")


if __name__ == "__main__":
    main()