from __future__ import annotations

from ml.preprocessing.feature_schema import MODEL_FEATURES


DEFERRED_RUNTIME_FEATURES = {
    # Bulk semantics require CICFlowMeter parity validation.
    "Bwd Bytes/Bulk Avg",
    "Bwd Packet/Bulk Avg",
    "Bwd Bulk Rate Avg",

    # Subflow semantics require CICFlowMeter parity validation.
    "Subflow Fwd Packets",
    "Subflow Fwd Bytes",
    "Subflow Bwd Packets",
    "Subflow Bwd Bytes",

    # Active / Idle segmentation requires exact parity validation.
    "Active Mean",
    "Active Std",
    "Active Max",
    "Active Min",

    "Idle Mean",
    "Idle Std",
    "Idle Max",
    "Idle Min",
}


RUNTIME_MODEL_FEATURES = (
    MODEL_FEATURES
    - DEFERRED_RUNTIME_FEATURES
)


def validate_runtime_schema() -> None:
    unknown = (
        DEFERRED_RUNTIME_FEATURES
        - MODEL_FEATURES
    )

    if unknown:
        raise ValueError(
            "Deferred runtime feature "
            "MODEL_FEATURES içinde bulunamadı: "
            + ", ".join(sorted(unknown))
        )

    if len(RUNTIME_MODEL_FEATURES) != 58:
        raise ValueError(
            "Runtime schema 58 feature bekliyor, "
            f"ancak {len(RUNTIME_MODEL_FEATURES)} bulundu."
        )


def runtime_schema_summary() -> None:
    print("=" * 70)
    print("CYBERLAB RUNTIME FEATURE SCHEMA v1")
    print("=" * 70)

    print(
        f"Canonical candidates: "
        f"{len(MODEL_FEATURES)}"
    )

    print(
        f"Deferred:             "
        f"{len(DEFERRED_RUNTIME_FEATURES)}"
    )

    print(
        f"Runtime candidates:   "
        f"{len(RUNTIME_MODEL_FEATURES)}"
    )

    print("-" * 70)

    print("\nDEFERRED FEATURES:")

    for feature in sorted(
        DEFERRED_RUNTIME_FEATURES
    ):
        print(f"  - {feature}")

if __name__ == "__main__":
    validate_runtime_schema()
    runtime_schema_summary()

    print("\nRuntime schema validation: OK")