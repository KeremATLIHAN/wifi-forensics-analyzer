from __future__ import annotations

import numpy as np

from ml.preprocessing.dataset_persistence import load_splits
from ml.runtime.hierarchical_ids_engine import (
    HierarchicalIDSEngine,
)
from ml.runtime.ids_inference_contract import (
    INFERENCE_FEATURES,
    PRIMARY_THRESHOLD,
    ROUTING_FLOOR,
)


def row_to_features(row) -> dict[str, float]:
    return {
        feature: float(row[feature])
        for feature in INFERENCE_FEATURES
    }


def main() -> None:
    print("=" * 78)
    print("CYBERLAB HIERARCHICAL IDS ENGINE TEST")
    print("=" * 78)

    engine = HierarchicalIDSEngine()

    # Validation is intentionally used here.
    # The final test split remains untouched.
    validation = load_splits().validation

    X = validation.loc[
        :,
        list(INFERENCE_FEATURES),
    ]

    primary_probabilities = (
        engine.primary_model.predict_proba(X)[:, 1]
    )

    # --------------------------------------------------------------
    # Locate examples for each primary routing region.
    # --------------------------------------------------------------

    primary_benign_idx = np.flatnonzero(
        primary_probabilities < ROUTING_FLOOR
    )

    specialist_idx = np.flatnonzero(
        (primary_probabilities >= ROUTING_FLOOR)
        & (primary_probabilities < PRIMARY_THRESHOLD)
    )

    primary_attack_idx = np.flatnonzero(
        primary_probabilities >= PRIMARY_THRESHOLD
    )

    if len(primary_benign_idx) == 0:
        raise AssertionError(
            "No PRIMARY_BENIGN validation sample found."
        )

    if len(specialist_idx) == 0:
        raise AssertionError(
            "No SPECIALIST validation sample found."
        )

    if len(primary_attack_idx) == 0:
        raise AssertionError(
            "No PRIMARY_ATTACK validation sample found."
        )

    # --------------------------------------------------------------
    # PRIMARY_BENIGN
    # --------------------------------------------------------------

    row = validation.iloc[
        primary_benign_idx[0]
    ]

    decision = engine.predict(
        row_to_features(row)
    )

    assert (
        decision.decision_path
        == "PRIMARY_BENIGN"
    )

    assert decision.prediction == 0
    assert decision.specialist_used is False
    assert decision.specialist_probability is None

    print()
    print("PRIMARY_BENIGN route:     OK")

    # --------------------------------------------------------------
    # PRIMARY_ATTACK
    # --------------------------------------------------------------

    row = validation.iloc[
        primary_attack_idx[0]
    ]

    decision = engine.predict(
        row_to_features(row)
    )

    assert (
        decision.decision_path
        == "PRIMARY_ATTACK"
    )

    assert decision.prediction == 1
    assert decision.specialist_used is False
    assert decision.specialist_probability is None

    print("PRIMARY_ATTACK route:     OK")

    # --------------------------------------------------------------
    # SPECIALIST ROUTING
    # --------------------------------------------------------------

    specialist_paths = set()

    for index in specialist_idx:
        row = validation.iloc[index]

        decision = engine.predict(
            row_to_features(row)
        )

        assert decision.specialist_used is True

        assert (
            decision.specialist_probability
            is not None
        )

        specialist_paths.add(
            decision.decision_path
        )

        if specialist_paths == {
            "SPECIALIST_BENIGN",
            "SPECIALIST_ATTACK",
        }:
            break

    if "SPECIALIST_BENIGN" not in specialist_paths:
        raise AssertionError(
            "SPECIALIST_BENIGN route not observed."
        )

    if "SPECIALIST_ATTACK" not in specialist_paths:
        raise AssertionError(
            "SPECIALIST_ATTACK route not observed."
        )

    print("SPECIALIST_BENIGN route:  OK")
    print("SPECIALIST_ATTACK route:  OK")

    # --------------------------------------------------------------
    # INPUT CONTRACT TESTS
    # --------------------------------------------------------------

    valid = row_to_features(
        validation.iloc[0]
    )

    # Missing feature.
    missing = dict(valid)
    missing.pop(INFERENCE_FEATURES[0])

    try:
        engine.predict(missing)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Missing feature was not rejected."
        )

    print("Missing feature rejection: OK")

    # Unexpected feature.
    unexpected = dict(valid)
    unexpected[
        "__CYBERLAB_INVALID_FEATURE__"
    ] = 1.0

    try:
        engine.predict(unexpected)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Unexpected feature was not rejected."
        )

    print("Extra feature rejection:   OK")

    # NaN.
    invalid_nan = dict(valid)
    invalid_nan[
        INFERENCE_FEATURES[0]
    ] = np.nan

    try:
        engine.predict(invalid_nan)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "NaN feature was not rejected."
        )

    print("NaN rejection:             OK")

    # Infinity.
    invalid_inf = dict(valid)
    invalid_inf[
        INFERENCE_FEATURES[0]
    ] = np.inf

    try:
        engine.predict(invalid_inf)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Infinity feature was not rejected."
        )

    print("Infinity rejection:        OK")

    print()
    print("=" * 78)
    print("HIERARCHICAL IDS ENGINE TEST: OK")
    print("=" * 78)


if __name__ == "__main__":
    main()