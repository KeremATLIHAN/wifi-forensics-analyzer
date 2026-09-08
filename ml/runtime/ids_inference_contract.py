from __future__ import annotations

from pathlib import Path

from ml.preprocessing.training_dataset import FEATURE_COLUMNS


# ------------------------------------------------------------------
# CyberLab Hierarchical IDS - Inference Contract v1
# ------------------------------------------------------------------

CONTRACT_VERSION = "1.0"

# Flows with fewer than two packets are outside the training population.
MINIMUM_TOTAL_PACKET_COUNT = 2

MODEL_DIR = Path("ml/models")

PRIMARY_MODEL_PATH = (
    MODEL_DIR
    / "cyberlab_binary_rf_v1.joblib"
)

SPECIALIST_MODEL_PATH = (
    MODEL_DIR
    / "cyberlab_hard_case_specialist_v1.joblib"
)


# ------------------------------------------------------------------
# Decision thresholds
# ------------------------------------------------------------------

PRIMARY_THRESHOLD = 0.50

ROUTING_FLOOR = 0.10

SPECIALIST_THRESHOLD = 0.60


# ------------------------------------------------------------------
# Feature contract
# ------------------------------------------------------------------

EXPECTED_FEATURE_COUNT = 57

INFERENCE_FEATURES = tuple(
    FEATURE_COLUMNS
)


def validate_inference_contract() -> None:
    """
    Validate the static CyberLab IDS inference contract.

    This does not load model artifacts. Artifact-level validation
    belongs to the inference engine / artifact validation layer.
    """

    if len(INFERENCE_FEATURES) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            "Inference feature count mismatch: "
            f"expected={EXPECTED_FEATURE_COUNT}, "
            f"actual={len(INFERENCE_FEATURES)}"
        )

    if len(set(INFERENCE_FEATURES)) != len(
        INFERENCE_FEATURES
    ):
        raise ValueError(
            "Duplicate features detected in inference contract."
        )

    if not (
        0.0
        <= ROUTING_FLOOR
        < PRIMARY_THRESHOLD
        <= 1.0
    ):
        raise ValueError(
            "Invalid primary routing thresholds."
        )

    if not (
        0.0
        <= SPECIALIST_THRESHOLD
        <= 1.0
    ):
        raise ValueError(
            "Invalid specialist threshold."
        )


def contract_summary() -> None:
    print("=" * 78)
    print("CYBERLAB HIERARCHICAL IDS INFERENCE CONTRACT")
    print("=" * 78)

    print(f"Contract version:      {CONTRACT_VERSION}")
    print(f"Feature count:         {len(INFERENCE_FEATURES)}")
    print(
        "Minimum total packets: "
        f"{MINIMUM_TOTAL_PACKET_COUNT} "
        "(lower counts are skipped)"
    )

    print()
    print("Primary model:")
    print(f"  Artifact:            {PRIMARY_MODEL_PATH}")
    print(f"  Threshold:           {PRIMARY_THRESHOLD:.2f}")

    print()
    print("Routing:")
    print(f"  Floor:               {ROUTING_FLOOR:.2f}")
    print(
        "  Specialist region:   "
        f"{ROUTING_FLOOR:.2f} <= p < "
        f"{PRIMARY_THRESHOLD:.2f}"
    )

    print()
    print("Specialist model:")
    print(f"  Artifact:            {SPECIALIST_MODEL_PATH}")
    print(
        f"  Threshold:           "
        f"{SPECIALIST_THRESHOLD:.2f}"
    )

    print()
    print("Decision policy:")
    print(
        f"  p < {ROUTING_FLOOR:.2f}"
        "                  -> BENIGN"
    )
    print(
        f"  {ROUTING_FLOOR:.2f} <= p < "
        f"{PRIMARY_THRESHOLD:.2f}"
        "       -> SPECIALIST"
    )
    print(
        f"  p >= {PRIMARY_THRESHOLD:.2f}"
        "                 -> ATTACK"
    )


if __name__ == "__main__":
    validate_inference_contract()
    contract_summary()

    print()
    print("Inference contract validation: OK")