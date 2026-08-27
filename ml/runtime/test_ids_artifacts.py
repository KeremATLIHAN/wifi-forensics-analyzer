from __future__ import annotations

import joblib
import numpy as np
import pandas as pd

from ml.runtime.ids_inference_contract import (
    INFERENCE_FEATURES,
    PRIMARY_MODEL_PATH,
    SPECIALIST_MODEL_PATH,
    validate_inference_contract,
)


def validate_artifact(
    name: str,
    path,
) -> None:
    print()
    print("-" * 78)
    print(name)
    print("-" * 78)

    if not path.exists():
        raise FileNotFoundError(
            f"Model artifact bulunamadı: {path}"
        )

    artifact = joblib.load(path)

    if not isinstance(artifact, dict):
        raise TypeError(
            f"{name} artifact dict değil."
        )

    required_keys = {
        "model",
        "feature_columns",
        "model_name",
    }

    missing_keys = (
        required_keys - set(artifact)
    )

    if missing_keys:
        raise ValueError(
            f"{name} eksik artifact key: "
            + ", ".join(
                sorted(missing_keys)
            )
        )

    model = artifact["model"]

    artifact_features = tuple(
        artifact["feature_columns"]
    )

    if len(artifact_features) != len(
        INFERENCE_FEATURES
    ):
        raise ValueError(
            f"{name} feature count mismatch: "
            f"{len(artifact_features)} != "
            f"{len(INFERENCE_FEATURES)}"
        )

    if artifact_features != INFERENCE_FEATURES:
        expected = list(INFERENCE_FEATURES)
        actual = list(artifact_features)

        mismatches = []

        for index, (
            expected_feature,
            actual_feature,
        ) in enumerate(
            zip(expected, actual),
            start=1,
        ):
            if expected_feature != actual_feature:
                mismatches.append(
                    (
                        index,
                        expected_feature,
                        actual_feature,
                    )
                )

        message = [
            f"{name} feature order mismatch."
        ]

        for (
            index,
            expected_feature,
            actual_feature,
        ) in mismatches[:10]:
            message.append(
                f"  #{index}: "
                f"expected={expected_feature!r}, "
                f"actual={actual_feature!r}"
            )

        raise ValueError(
            "\n".join(message)
        )

    if not hasattr(
        model,
        "predict_proba",
    ):
        raise TypeError(
            f"{name} predict_proba desteklemiyor."
        )

    if not hasattr(
        model,
        "classes_",
    ):
        raise TypeError(
            f"{name} trained classifier değil."
        )

    classes = tuple(
        int(value)
        for value in model.classes_
    )

    if classes != (0, 1):
        raise ValueError(
            f"{name} beklenmeyen classes_: "
            f"{classes}"
        )

    # Minimal inference smoke test.
    sample = pd.DataFrame(
        np.zeros(
            (
                1,
                len(INFERENCE_FEATURES),
            ),
            dtype=np.float64,
        ),
        columns=INFERENCE_FEATURES,
    )

    probabilities = model.predict_proba(
        sample
    )

    if probabilities.shape != (1, 2):
        raise ValueError(
            f"{name} probability shape invalid: "
            f"{probabilities.shape}"
        )

    if not np.isfinite(
        probabilities
    ).all():
        raise ValueError(
            f"{name} non-finite probability üretti."
        )

    probability_sum = float(
        probabilities[0].sum()
    )

    if not np.isclose(
        probability_sum,
        1.0,
    ):
        raise ValueError(
            f"{name} probability toplamı 1 değil: "
            f"{probability_sum}"
        )

    print(
        f"Artifact:       {path}"
    )

    print(
        f"Model name:     "
        f"{artifact['model_name']}"
    )

    print(
        f"Feature count:  "
        f"{len(artifact_features)}"
    )

    print(
        f"Classes:        {classes}"
    )

    print(
        "predict_proba:  OK"
    )

    print(
        "Feature order:  OK"
    )

    print(
        "Smoke inference: OK"
    )


def main() -> None:
    validate_inference_contract()

    print("=" * 78)
    print("CYBERLAB IDS ARTIFACT VALIDATION")
    print("=" * 78)

    validate_artifact(
        "PRIMARY MODEL",
        PRIMARY_MODEL_PATH,
    )

    validate_artifact(
        "SPECIALIST MODEL",
        SPECIALIST_MODEL_PATH,
    )

    print()
    print("=" * 78)
    print("IDS ARTIFACT VALIDATION: OK")
    print("=" * 78)


if __name__ == "__main__":
    main()