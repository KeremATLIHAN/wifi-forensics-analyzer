from __future__ import annotations


# ---------------------------------------------------------
# TARGETS
# Model girdisi değildir.
# ---------------------------------------------------------

TARGET_FEATURES = {
    "Attack Name",
    "Label",
}


# ---------------------------------------------------------
# IDENTITY / LEAKAGE
# Trafik davranışından ziyade capture ortamını tanımlayabilir.
# ML modeline verilmez.
# ---------------------------------------------------------

IDENTITY_FEATURES = {
    "Flow ID",
    "Src IP",
    "Dst IP",
    "Timestamp",
}


# ---------------------------------------------------------
# CONSTANT FEATURES
# Mevcut 11,010,062 satırlık corpus üzerinde
# ayırt edici bilgi taşımadığı doğrulandı.
# ---------------------------------------------------------

CONSTANT_FEATURES = {
    "Bwd PSH Flags",
    "Bwd URG Flags",
    "Fwd Bulk Rate Avg",
    "Fwd Bytes/Bulk Avg",
    "Fwd Packet/Bulk Avg",
    "Protocol",
}


# ---------------------------------------------------------
# DIRECT
# Paketlerden doğrudan elde edilebilecek temel bilgiler.
# ---------------------------------------------------------

DIRECT_FEATURES = {
    "Src Port",
    "Dst Port",
}


# ---------------------------------------------------------
# DERIVED
# Flow içindeki paketlerden matematiksel olarak üretilebilir.
# ---------------------------------------------------------

DERIVED_FEATURES = {
    "Flow Duration",

    "Total Fwd Packet",
    "Total Bwd packets",

    "Total Length of Fwd Packet",
    "Total Length of Bwd Packet",

    "Fwd Packet Length Max",
    "Fwd Packet Length Min",
    "Fwd Packet Length Mean",
    "Fwd Packet Length Std",

    "Bwd Packet Length Max",
    "Bwd Packet Length Min",
    "Bwd Packet Length Mean",
    "Bwd Packet Length Std",

    "Flow Bytes/s",
    "Flow Packets/s",

    "Fwd Packets/s",
    "Bwd Packets/s",

    "Packet Length Min",
    "Packet Length Max",
    "Packet Length Mean",
    "Packet Length Std",
    "Packet Length Variance",

    "FIN Flag Count",
    "SYN Flag Count",
    "RST Flag Count",
    "PSH Flag Count",
    "ACK Flag Count",
    "URG Flag Count",
    "CWR Flag Count",
    "ECE Flag Count",

    "Down/Up Ratio",
    "Average Packet Size",

    "Fwd Segment Size Avg",
    "Bwd Segment Size Avg",

    "Fwd Header Length",
    "Bwd Header Length",

    "Fwd PSH Flags",
    "Fwd URG Flags",

    "FWD Init Win Bytes",
    "Bwd Init Win Bytes",

    "Fwd Act Data Pkts",
    "Fwd Seg Size Min",
}


# ---------------------------------------------------------
# STATEFUL
# Flow boyunca zaman/paket geçmişi tutulmasını gerektirir.
# ---------------------------------------------------------

STATEFUL_FEATURES = {
    "Flow IAT Mean",
    "Flow IAT Std",
    "Flow IAT Max",
    "Flow IAT Min",

    "Fwd IAT Total",
    "Fwd IAT Mean",
    "Fwd IAT Std",
    "Fwd IAT Max",
    "Fwd IAT Min",

    "Bwd IAT Total",
    "Bwd IAT Mean",
    "Bwd IAT Std",
    "Bwd IAT Max",
    "Bwd IAT Min",

    "Bwd Bytes/Bulk Avg",
    "Bwd Packet/Bulk Avg",
    "Bwd Bulk Rate Avg",

    "Subflow Fwd Packets",
    "Subflow Fwd Bytes",
    "Subflow Bwd Packets",
    "Subflow Bwd Bytes",

    "Active Mean",
    "Active Std",
    "Active Max",
    "Active Min",

    "Idle Mean",
    "Idle Std",
    "Idle Max",
    "Idle Min",
}


EXCLUDED_FEATURES = (
    TARGET_FEATURES
    | IDENTITY_FEATURES
    | CONSTANT_FEATURES
)


MODEL_FEATURES = (
    DIRECT_FEATURES
    | DERIVED_FEATURES
    | STATEFUL_FEATURES
)


def validate_schema(dataset_columns: list[str]) -> None:
    """
    Dataset kolonlarının Canonical Feature Schema ile
    eksiksiz eşleşip eşleşmediğini doğrular.
    """

    dataset_set = {
        str(column).strip()
        for column in dataset_columns
    }

    classified = (
        TARGET_FEATURES
        | IDENTITY_FEATURES
        | CONSTANT_FEATURES
        | MODEL_FEATURES
    )

    missing_classification = dataset_set - classified
    unknown_features = classified - dataset_set

    if missing_classification:
        raise ValueError(
            "Siniflandirilmamis dataset kolonlari: "
            + ", ".join(
                sorted(missing_classification)
            )
        )

    if unknown_features:
        raise ValueError(
            "Dataset'te bulunmayan schema kolonlari: "
            + ", ".join(
                sorted(unknown_features)
            )
        )


def schema_summary() -> None:
    print("=" * 70)
    print("CYBERLAB CANONICAL FEATURE SCHEMA v1")
    print("=" * 70)

    print(f"Target:       {len(TARGET_FEATURES)}")
    print(f"Identity:     {len(IDENTITY_FEATURES)}")
    print(f"Constant:     {len(CONSTANT_FEATURES)}")
    print(f"Direct:       {len(DIRECT_FEATURES)}")
    print(f"Derived:      {len(DERIVED_FEATURES)}")
    print(f"Stateful:     {len(STATEFUL_FEATURES)}")
    print("-" * 70)
    print(f"Model input:  {len(MODEL_FEATURES)}")