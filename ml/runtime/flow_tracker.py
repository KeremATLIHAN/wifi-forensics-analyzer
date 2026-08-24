from __future__ import annotations

from dataclasses import dataclass

from ml.runtime.flow_key import FlowKey
from ml.runtime.flow_state import FlowState
from ml.runtime.packet_record import PacketRecord


@dataclass(slots=True)
class CompletedFlow:
    key: FlowKey
    features: dict[str, float]
    reason: str


class FlowTracker:
    """
    CyberLab canlı flow yöneticisi.

    Paketleri bidirectional FlowState nesnelerine yönlendirir
    ve belirlenen inactivity timeout sonrasında flow'u kapatır.
    """

    def __init__(
        self,
        inactivity_timeout: float = 60.0,
    ) -> None:
        if inactivity_timeout <= 0:
            raise ValueError(
                "inactivity_timeout sıfırdan büyük olmalıdır."
            )

        self.inactivity_timeout = inactivity_timeout

        self._flows: dict[
            FlowKey,
            FlowState,
        ] = {}

    @property
    def active_flow_count(self) -> int:
        return len(self._flows)

    def process_packet(
        self,
        packet: PacketRecord,
    ) -> FlowState:
        packet.validate()

        key = FlowKey.from_packet(packet)

        flow = self._flows.get(key)

        if flow is None:
            flow = FlowState(packet)
            self._flows[key] = flow
        else:
            flow.add_packet(packet)

        return flow

    def expire_flows(
        self,
        current_timestamp: float,
    ) -> list[CompletedFlow]:

        completed: list[CompletedFlow] = []

        expired_keys: list[FlowKey] = []

        for key, flow in self._flows.items():
            idle_time = (
                current_timestamp
                - flow.last_timestamp
            )

            if idle_time >= self.inactivity_timeout:
                completed.append(
                    CompletedFlow(
                        key=key,
                        features=flow.to_feature_dict(),
                        reason="INACTIVITY_TIMEOUT",
                    )
                )

                expired_keys.append(key)

        for key in expired_keys:
            del self._flows[key]

        return completed

    def close_all(
        self,
        reason: str = "CAPTURE_STOPPED",
    ) -> list[CompletedFlow]:

        completed = [
            CompletedFlow(
                key=key,
                features=flow.to_feature_dict(),
                reason=reason,
            )
            for key, flow in self._flows.items()
        ]

        self._flows.clear()

        return completed