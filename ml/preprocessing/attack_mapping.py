from __future__ import annotations


ATTACK_FAMILY_MAP = {
    # Normal traffic
    "Benign Traffic": "BENIGN",

    # DDoS
    "DDoS RSTFIN Flood": "DDOS",
    "DDoS PSHACK Flood": "DDOS",
    "DDoS ACK Fragmentation": "DDOS",
    "DDoS ICMP Fragmentation": "DDOS",
    "DDoS UDP Flood": "DDOS",
    "DDoS ICMP Flood": "DDOS",

    # DoS
    "DoS TCP Flood": "DOS",
    "DoS SYN Flood": "DOS",
    "DoS UDP Flood": "DOS",
    "DoS ICMP Flood": "DOS",
    "DoS DNS Flood": "DOS",

    # Reconnaissance
    "Recon Port Scan": "RECON",
    "Recon OS Scan": "RECON",
    "Recon Vulnerability Scan": "RECON",
    "Recon Ping Sweep": "RECON",
    "Recon Host Discovery": "RECON",

    # MQTT
    "MQTT DDoS Publish Flood": "MQTT",
    "MQTT DoS Connect Flood": "MQTT",
    "MQTT DoS Publish Flood": "MQTT",
    "MQTT Malformed": "MQTT",

    # Credential attack
    "Dictionary Brute Force": "BRUTE_FORCE",

    # MITM
    "MITM ARP Spoofing": "MITM",

    # Malware / botnet
    "Mirai UDP Plain": "MIRAI",
}


ATTACK_FAMILIES = frozenset(
    ATTACK_FAMILY_MAP.values()
)


def get_attack_family(
    attack_name: str,
) -> str:
    try:
        return ATTACK_FAMILY_MAP[attack_name]
    except KeyError as exc:
        raise ValueError(
            f"Unknown Attack Name: {attack_name!r}"
        ) from exc

def validate_attack_mapping() -> None:
    import pandas as pd

    from ml.preprocessing.dataset_loader import (
        DATASET_ROOT,
    )

    csv_files = sorted(
        DATASET_ROOT.rglob("*.csv")
    )

    if not csv_files:
        raise FileNotFoundError(
            f"CSV bulunamadı: {DATASET_ROOT}"
        )

    dataset_attacks: set[str] = set()

    for index, path in enumerate(
        csv_files,
        start=1,
    ):
        print(
            f"[{index:02}/{len(csv_files)}] "
            f"{path.name}"
        )

        for chunk in pd.read_csv(
            path,
            usecols=["Attack Name"],
            chunksize=100_000,
            low_memory=False,
        ):
            names = (
                chunk["Attack Name"]
                .dropna()
                .astype(str)
                .str.strip()
                .unique()
            )

            dataset_attacks.update(names)

    mapped_attacks = set(ATTACK_FAMILY_MAP)

    unmapped = (
        dataset_attacks - mapped_attacks
    )

    unused = (
        mapped_attacks - dataset_attacks
    )

    print("=" * 70)
    print("CYBERLAB ATTACK FAMILY MAPPING")
    print("=" * 70)

    print(
        f"Dataset attack names: "
        f"{len(dataset_attacks)}"
    )

    print(
        f"Mapped attack names:  "
        f"{len(mapped_attacks)}"
    )

    print(
        f"Attack families:      "
        f"{len(ATTACK_FAMILIES)}"
    )

    print("\nFamilies:")

    for family in sorted(
        ATTACK_FAMILIES
    ):
        print(f"  - {family}")

    if unmapped:
        print("\nUNMAPPED ATTACK NAMES:")

        for attack in sorted(unmapped):
            print(f"  - {attack}")

        raise ValueError(
            "Dataset contains unmapped "
            "attack names."
        )

    if unused:
        print("\nWARNING - UNUSED MAPPINGS:")

        for attack in sorted(unused):
            print(f"  - {attack}")

    print(
        "\nAttack mapping contract: OK"
    )

if __name__ == "__main__":
    validate_attack_mapping()
