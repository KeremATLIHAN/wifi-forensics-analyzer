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
        flow_timeout: float = 120.0,
    ) -> None:
        if inactivity_timeout <= 0:
            raise ValueError(
                "inactivity_timeout sıfırdan büyük olmalıdır."
            )

        if flow_timeout <= 0:
            raise ValueError(
                "flow_timeout sıfırdan büyük olmalıdır."
            )

        self.inactivity_timeout = inactivity_timeout
        self.flow_timeout = flow_timeout

        self._flows: dict[
            FlowKey,
            FlowState,
        ] = {}

        self._finished_flows: list[CompletedFlow] = []

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
            return flow

        # ----------------------------------------------------------
        # CICFlowMeter maximum flow lifetime
        #
        # Reference:
        # flowTimeout = 120 seconds
        #
        # Timeout kontrolü tetikleyici paket mevcut flow'a
        # eklenmeden önce yapılır.
        # ----------------------------------------------------------
        flow_age = packet.timestamp - flow.first_timestamp

        if flow_age > self.flow_timeout:
            self._finished_flows.append(
                CompletedFlow(
                    key=key,
                    features=flow.to_feature_dict(),
                    reason="FLOW_TIMEOUT",
                )
            )

            del self._flows[key]

            flow = FlowState(packet)
            self._flows[key] = flow

            return flow

        # ----------------------------------------------------------
        # TCP RST lifecycle
        #
        # CICFlowMeter davranışı:
        # RST paketi flow'a eklenir ve flow
        # hemen tamamlanır.
        # ----------------------------------------------------------
        if packet.is_tcp and packet.tcp_rst:
            flow.add_packet(packet)

            self._finished_flows.append(
                CompletedFlow(
                    key=key,
                    features=flow.to_feature_dict(),
                    reason="TCP_RST",
                )
            )

            del self._flows[key]

            return flow

        if packet.is_tcp and packet.tcp_fin:
            is_forward = (
                packet.src_ip
                == flow.forward_source_ip
                and packet.src_port
                == flow.forward_source_port
            )

            if is_forward:
                # Reference:
                # setFwdFINFlags()
                #
                # 1. FIN -> add
                # 2. FIN -> add
                # 3+ FIN -> discard

                if flow.fwd.fin_count < 2:
                    flow.add_packet(packet)

                return flow

            else:
                # Reference:
                # setBwdFINFlags()
                #
                # İlk BWD FIN sonrasında:
                # bwdFIN + bwdFIN == 2
                # -> flow tamamlanır.

                if flow.bwd.fin_count == 0:
                    flow.add_packet(packet)

                    if (
                        flow.bwd.fin_count
                        + flow.bwd.fin_count
                    ) == 2:
                        self._finished_flows.append(
                            CompletedFlow(
                                key=key,
                                features=flow.to_feature_dict(),
                                reason="TCP_FIN",
                            )
                        )
                        del self._flows[key]

                return flow

        flow.add_packet(packet)

        return flow

    def expire_flows(
        self,
        current_timestamp: float,
    ) -> list[CompletedFlow]:

        completed: list[CompletedFlow] = []

        # ----------------------------------------------------------
        # TCP FIN ile tamamlanan flow'lar
        # ----------------------------------------------------------
        if self._finished_flows:
            completed.extend(
                self._finished_flows
            )
            self._finished_flows.clear()

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

        completed = list(
            self._finished_flows
        )

        self._finished_flows.clear()

        completed.extend(
            CompletedFlow(
                key=key,
                features=flow.to_feature_dict(),
                reason=reason,
            )
            for key, flow in self._flows.items()
        )

        self._flows.clear()

        return completed
