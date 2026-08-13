from threading import Lock
from typing import Any, Dict, Optional


class SimulatorTelemetryStore:

    def __init__(self) -> None:
        self._lock = Lock()

        self._data: Dict[str, Any] = {
            "speed_kmh": None,
            "speed_available": False,
            "rpm": None,
            "gear": None,
            "throttle": None,
            "brake": None,
            "lap_number": None,
            "telemetry_source": "No live simulator connected",
        }

    def update(
        self,
        speed_kmh: Optional[float] = None,
        rpm: Optional[int] = None,
        gear: Optional[int] = None,
        throttle: Optional[float] = None,
        brake: Optional[float] = None,
        lap_number: Optional[int] = None,
    ) -> None:

        with self._lock:

            if speed_kmh is not None:
                self._data["speed_kmh"] = speed_kmh
                self._data["speed_available"] = True

            if rpm is not None:
                self._data["rpm"] = rpm

            if gear is not None:
                self._data["gear"] = gear

            if throttle is not None:
                self._data["throttle"] = throttle

            if brake is not None:
                self._data["brake"] = brake

            if lap_number is not None:
                self._data["lap_number"] = lap_number

            if self._data["speed_available"]:
                self._data["telemetry_source"] = (
                    "Racing Simulator"
                )

    def get(self) -> Dict[str, Any]:

        with self._lock:
            return dict(self._data)


simulator_telemetry = SimulatorTelemetryStore()
