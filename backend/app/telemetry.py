from threading import Lock

from typing import (
    Any,
    Dict,
    List,
    Optional,
)


# ============================================================
# SIMULATOR TELEMETRY STORE
# ============================================================

class SimulatorTelemetryStore:

    def __init__(self) -> None:

        self._lock = Lock()

        # ====================================================
        # LIVE VEHICLE TELEMETRY
        # ====================================================

        self._data: Dict[
            str,
            Any,
        ] = {

            "speed_kmh":
                None,

            "speed_available":
                False,

            "rpm":
                None,

            "gear":
                None,

            "throttle":
                None,

            "brake":
                None,

            # =================================================
            # AUTONOMOUS LAP
            # =================================================

            "lap_number":
                None,

            "lap_time":
                None,

            "previous_lap":
                None,

            "last_completed_lap":
                None,

            "current_lap_time":
                None,

            "last_lap_time":
                None,

            "lap_change_count":
                0,

            # =================================================
            # DRIVER STATE
            # =================================================

            "fatigue":
                "LOW",

            "fatigue_score":
                0.0,

            "workload":
                "NORMAL",

            "driver_state":
                "NORMAL",

            "stress":
                0.0,

            "confidence":
                0.0,

            # =================================================
            # TELEMETRY SOURCE
            # =================================================

            "telemetry_source":
                "No live simulator connected",

            "udp_connected":
                False,

            "udp_packet_format":
                None,

            "udp_game_year":
                None,

            "udp_game_major":
                None,

            "udp_game_minor":
                None,
        }

        # ====================================================
        # LAP PERFORMANCE HISTORY
        # ====================================================

        self._lap_history: List[
            Dict[str, Any]
        ] = []

        self._max_history = 100

    # ========================================================
    # UPDATE VEHICLE TELEMETRY
    # ========================================================

    def update(
        self,

        speed_kmh: Optional[
            float
        ] = None,

        rpm: Optional[
            int
        ] = None,

        gear: Optional[
            int
        ] = None,

        throttle: Optional[
            float
        ] = None,

        brake: Optional[
            float
        ] = None,

        lap_number: Optional[
            int
        ] = None,

        lap_time: Optional[
            float
        ] = None,
    ) -> None:

        with self._lock:

            # ------------------------------------------------
            # SPEED
            # ------------------------------------------------

            if speed_kmh is not None:

                self._data[
                    "speed_kmh"
                ] = speed_kmh

                self._data[
                    "speed_available"
                ] = True

            # ------------------------------------------------
            # RPM
            # ------------------------------------------------

            if rpm is not None:

                self._data[
                    "rpm"
                ] = rpm

            # ------------------------------------------------
            # GEAR
            # ------------------------------------------------

            if gear is not None:

                self._data[
                    "gear"
                ] = gear

            # ------------------------------------------------
            # THROTTLE
            # ------------------------------------------------

            if throttle is not None:

                self._data[
                    "throttle"
                ] = throttle

            # ------------------------------------------------
            # BRAKE
            # ------------------------------------------------

            if brake is not None:

                self._data[
                    "brake"
                ] = brake

            # ------------------------------------------------
            # AUTONOMOUS LAP
            # ------------------------------------------------

            if lap_number is not None:

                self._data[
                    "lap_number"
                ] = int(
                    lap_number
                )

            # ------------------------------------------------
            # CURRENT LAP TIME
            # ------------------------------------------------

            if lap_time is not None:

                lap_time_value = float(
                    lap_time
                )

                self._data[
                    "lap_time"
                ] = lap_time_value

                self._data[
                    "current_lap_time"
                ] = lap_time_value

            # ------------------------------------------------
            # TELEMETRY SOURCE
            # ------------------------------------------------

            if self._data[
                "udp_connected"
            ]:

                self._data[
                    "telemetry_source"
                ] = (
                    "F1 UDP Telemetry"
                )

    # ========================================================
    # AUTONOMOUS LAP STATE
    # ========================================================

    def set_lap_state(
        self,

        current_lap: Optional[
            int
        ],

        previous_lap: Optional[
            int
        ] = None,

        last_completed_lap: Optional[
            int
        ] = None,

        current_lap_time: Optional[
            float
        ] = None,

        last_lap_time: Optional[
            float
        ] = None,

        lap_change_count: Optional[
            int
        ] = None,
    ) -> None:

        with self._lock:

            # ------------------------------------------------
            # CURRENT LAP
            # ------------------------------------------------

            if current_lap is not None:

                self._data[
                    "lap_number"
                ] = int(
                    current_lap
                )

            # ------------------------------------------------
            # PREVIOUS LAP
            # ------------------------------------------------

            if previous_lap is not None:

                self._data[
                    "previous_lap"
                ] = int(
                    previous_lap
                )

            # ------------------------------------------------
            # LAST COMPLETED LAP
            # ------------------------------------------------

            if (
                last_completed_lap
                is not None
            ):

                self._data[
                    "last_completed_lap"
                ] = int(
                    last_completed_lap
                )

            # ------------------------------------------------
            # CURRENT LAP TIME
            # ------------------------------------------------

            if (
                current_lap_time
                is not None
            ):

                current_time = float(
                    current_lap_time
                )

                self._data[
                    "current_lap_time"
                ] = current_time

                self._data[
                    "lap_time"
                ] = current_time

            # ------------------------------------------------
            # LAST LAP TIME
            # ------------------------------------------------

            if (
                last_lap_time
                is not None
            ):

                self._data[
                    "last_lap_time"
                ] = float(
                    last_lap_time
                )

            # ------------------------------------------------
            # LAP CHANGE COUNT
            # ------------------------------------------------

            if (
                lap_change_count
                is not None
            ):

                self._data[
                    "lap_change_count"
                ] = int(
                    lap_change_count
                )

    # ========================================================
    # CLEAR LIVE VEHICLE TELEMETRY
    # ========================================================

    def clear_vehicle_telemetry(
        self,
    ) -> None:
        """
        Clear only live vehicle values when F1 UDP times out.

        Driver analysis/history is intentionally preserved.
        """

        with self._lock:
            self._data["speed_kmh"] = None
            self._data["speed_available"] = False
            self._data["rpm"] = None
            self._data["gear"] = None
            self._data["throttle"] = None
            self._data["brake"] = None
            self._data["telemetry_source"] = (
                "No live simulator connected"
            )

    # ========================================================
    # UDP STATUS
    # ========================================================

    def set_udp_status(
        self,

        connected: bool,

        packet_format: Optional[
            int
        ] = None,

        game_year: Optional[
            int
        ] = None,

        game_major: Optional[
            int
        ] = None,

        game_minor: Optional[
            int
        ] = None,
    ) -> None:

        with self._lock:

            self._data[
                "udp_connected"
            ] = bool(
                connected
            )

            # ------------------------------------------------
            # METADATA
            # ------------------------------------------------

            if packet_format is not None:

                self._data[
                    "udp_packet_format"
                ] = packet_format

            if game_year is not None:

                self._data[
                    "udp_game_year"
                ] = game_year

            if game_major is not None:

                self._data[
                    "udp_game_major"
                ] = game_major

            if game_minor is not None:

                self._data[
                    "udp_game_minor"
                ] = game_minor

            # ------------------------------------------------
            # CONNECTED
            # ------------------------------------------------

            if connected:

                self._data[
                    "telemetry_source"
                ] = (
                    "F1 UDP Telemetry"
                )

                self._data[
                    "speed_available"
                ] = (
                    self._data.get(
                        "speed_kmh"
                    )
                    is not None
                )

            # ------------------------------------------------
            # DISCONNECTED
            # ------------------------------------------------

            else:

                self._data[
                    "telemetry_source"
                ] = (
                    "No live simulator connected"
                )

                self._data[
                    "speed_available"
                ] = False

                self._data[
                    "speed_kmh"
                ] = None

                self._data[
                    "rpm"
                ] = None

                self._data[
                    "gear"
                ] = None

                self._data[
                    "throttle"
                ] = None

                self._data[
                    "brake"
                ] = None

                self._data[
                    "lap_number"
                ] = None

                self._data[
                    "lap_time"
                ] = None

                self._data[
                    "current_lap_time"
                ] = None

    # ========================================================
    # DRIVER STATE
    # ========================================================

    def update_driver_state(
        self,

        lap_number: Optional[
            int
        ] = None,

        stress: Optional[
            float
        ] = None,

        fatigue: Optional[
            float
        ] = None,

        driver_state: Optional[
            str
        ] = None,

        event: Optional[
            str
        ] = None,

        event_type: Optional[
            str
        ] = None,

        confidence: Optional[
            float
        ] = None,
    ) -> None:

        with self._lock:

            # ------------------------------------------------
            # STRESS
            # ------------------------------------------------

            if stress is not None:

                stress_value = max(
                    0.0,
                    min(
                        1.0,
                        float(
                            stress
                        ),
                    ),
                )

                self._data[
                    "stress"
                ] = stress_value

            # ------------------------------------------------
            # FATIGUE
            # ------------------------------------------------

            if fatigue is not None:

                fatigue_value = max(
                    0.0,
                    min(
                        1.0,
                        float(
                            fatigue
                        ),
                    ),
                )

                self._data[
                    "fatigue_score"
                ] = fatigue_value

                self._data[
                    "fatigue"
                ] = (
                    self._fatigue_label(
                        fatigue_value
                    )
                )

            # ------------------------------------------------
            # DRIVER STATE
            # ------------------------------------------------

            if driver_state:

                self._data[
                    "driver_state"
                ] = str(
                    driver_state
                ).upper()

            # ------------------------------------------------
            # CONFIDENCE
            # ------------------------------------------------

            if confidence is not None:

                self._data[
                    "confidence"
                ] = max(
                    0.0,
                    min(
                        1.0,
                        float(
                            confidence
                        ),
                    ),
                )

            # ------------------------------------------------
            # LAP
            #
            # This is only updated when a real lap is supplied.
            #
            # No automatic fake number.
            # ------------------------------------------------

            if lap_number is not None:

                self._data[
                    "lap_number"
                ] = int(
                    lap_number
                )

            # ------------------------------------------------
            # WORKLOAD
            # ------------------------------------------------

            self._data[
                "workload"
            ] = (
                self._workload_label(
                    self._data.get(
                        "stress",
                        0.0,
                    ),
                    self._data.get(
                        "fatigue_score",
                        0.0,
                    ),
                )
            )

            # ------------------------------------------------
            # UPDATE CURRENT LAP HISTORY
            # ------------------------------------------------

            if lap_number is not None:

                self._add_lap_unlocked(

                    lap=int(
                        lap_number
                    ),

                    lap_time=(
                        self._data.get(
                            "lap_time"
                        )
                    ),

                    stress=(
                        self._data.get(
                            "stress",
                            0.0,
                        )
                    ),

                    fatigue=(
                        self._data.get(
                            "fatigue_score",
                            0.0,
                        )
                    ),

                    driver_state=(
                        self._data.get(
                            "driver_state",
                            "NORMAL",
                        )
                    ),

                    event=event,

                    event_type=event_type,

                    confidence=(
                        self._data.get(
                            "confidence",
                            0.0,
                        )
                    ),
                )

    # ========================================================
    # ADD LAP
    # ========================================================

    def add_lap(
        self,

        lap: int,

        lap_time: Optional[
            float
        ] = None,

        stress: float = 0.0,

        fatigue: float = 0.0,

        driver_state: str = "NORMAL",

        event: Optional[
            str
        ] = None,

        event_type: Optional[
            str
        ] = None,

        confidence: float = 0.0,
    ) -> None:

        with self._lock:

            self._add_lap_unlocked(

                lap=int(
                    lap
                ),

                lap_time=lap_time,

                stress=stress,

                fatigue=fatigue,

                driver_state=driver_state,

                event=event,

                event_type=event_type,

                confidence=confidence,
            )

    # ========================================================
    # INTERNAL LAP STORAGE
    # ========================================================

    def _add_lap_unlocked(
        self,

        lap: int,

        lap_time: Optional[
            float
        ],

        stress: float,

        fatigue: float,

        driver_state: str,

        event: Optional[
            str
        ],

        event_type: Optional[
            str
        ],

        confidence: float,
    ) -> None:

        point = {

            "lap":
                int(
                    lap
                ),

            "lap_time": (
                float(
                    lap_time
                )
                if lap_time is not None
                else None
            ),

            "stress": max(
                0.0,
                min(
                    1.0,
                    float(
                        stress
                    ),
                ),
            ),

            "fatigue": max(
                0.0,
                min(
                    1.0,
                    float(
                        fatigue
                    ),
                ),
            ),

            "driver_state":
                str(
                    driver_state
                ).upper(),

            "event":
                event,

            "event_type":
                event_type,

            "confidence": max(
                0.0,
                min(
                    1.0,
                    float(
                        confidence
                    ),
                ),
            ),
        }

        # ====================================================
        # FIND EXISTING LAP
        # ====================================================

        existing_index = None

        for index in range(
            len(
                self._lap_history
            ) - 1,
            -1,
            -1,
        ):

            existing_lap = (
                self._lap_history[
                    index
                ].get(
                    "lap"
                )
            )

            if (
                existing_lap
                == int(
                    lap
                )
            ):

                existing_index = (
                    index
                )

                break

        # ====================================================
        # UPDATE EXISTING LAP
        # ====================================================

        if (
            existing_index
            is not None
        ):

            existing = (
                self._lap_history[
                    existing_index
                ]
            )

            # Don't erase an existing
            # event with None.

            if (
                point[
                    "event"
                ] is None
                and existing.get(
                    "event"
                )
            ):

                point[
                    "event"
                ] = existing.get(
                    "event"
                )

            if (
                point[
                    "event_type"
                ] is None
                and existing.get(
                    "event_type"
                )
            ):

                point[
                    "event_type"
                ] = existing.get(
                    "event_type"
                )

            self._lap_history[
                existing_index
            ].update(
                point
            )

        # ====================================================
        # CREATE NEW LAP
        # ====================================================

        else:

            self._lap_history.append(
                point
            )

        # ====================================================
        # LIMIT HISTORY
        # ====================================================

        if (
            len(
                self._lap_history
            )
            > self._max_history
        ):

            self._lap_history = (
                self._lap_history[
                    -self._max_history:
                ]
            )

    # ========================================================
    # GET CURRENT TELEMETRY
    # ========================================================

    def get(
        self,
    ) -> Dict[
        str,
        Any,
    ]:

        with self._lock:

            return dict(
                self._data
            )

    # ========================================================
    # GET HISTORY
    # ========================================================

    def get_history(
        self,

        limit: int = 50,
    ) -> List[
        Dict[str, Any]
    ]:

        try:

            limit = int(
                limit
            )

        except (
            TypeError,
            ValueError,
        ):

            limit = 50

        limit = max(
            1,
            min(
                limit,
                self._max_history,
            ),
        )

        with self._lock:

            return [
                dict(
                    item
                )
                for item in
                self._lap_history[
                    -limit:
                ]
            ]

    # ========================================================
    # COMPATIBILITY ALIAS
    # ========================================================

    def get_lap_history(
        self,

        limit: int = 50,
    ) -> List[
        Dict[str, Any]
    ]:

        return self.get_history(
            limit
        )

    # ========================================================
    # CLEAR HISTORY
    # ========================================================

    def clear_history(
        self,
    ) -> None:

        with self._lock:

            self._lap_history.clear()

    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
    ) -> None:

        with self._lock:

            self._data = {

                # Vehicle
                "speed_kmh":
                    None,

                "speed_available":
                    False,

                "rpm":
                    None,

                "gear":
                    None,

                "throttle":
                    None,

                "brake":
                    None,

                # Autonomous lap
                "lap_number":
                    None,

                "lap_time":
                    None,

                "previous_lap":
                    None,

                "last_completed_lap":
                    None,

                "current_lap_time":
                    None,

                "last_lap_time":
                    None,

                "lap_change_count":
                    0,

                # Driver
                "fatigue":
                    "LOW",

                "fatigue_score":
                    0.0,

                "workload":
                    "NORMAL",

                "driver_state":
                    "NORMAL",

                "stress":
                    0.0,

                "confidence":
                    0.0,

                # Source
                "telemetry_source":
                    "No live simulator connected",

                "udp_connected":
                    False,

                "udp_packet_format":
                    None,

                "udp_game_year":
                    None,

                "udp_game_major":
                    None,

                "udp_game_minor":
                    None,
            }

            self._lap_history.clear()

    # ========================================================
    # FATIGUE LABEL
    # ========================================================

    @staticmethod
    def _fatigue_label(
        score: float,
    ) -> str:

        if score >= 0.75:

            return "HIGH"

        if score >= 0.45:

            return "MEDIUM"

        return "LOW"

    # ========================================================
    # WORKLOAD LABEL
    # ========================================================

    @staticmethod
    def _workload_label(
        stress: float,
        fatigue: float,
    ) -> str:

        value = max(
            stress,
            fatigue,
        )

        if value >= 0.75:

            return "VERY HIGH"

        if value >= 0.55:

            return "HIGH"

        if value >= 0.35:

            return "ELEVATED"

        return "NORMAL"


# ============================================================
# GLOBAL TELEMETRY STORE
# ============================================================

simulator_telemetry = (
    SimulatorTelemetryStore()
)
