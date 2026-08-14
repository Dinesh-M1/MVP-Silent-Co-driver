import socket
import struct
import threading
import time
from typing import Optional


# ============================================================
# F1 UDP CONFIGURATION
# ============================================================

UDP_HOST = "0.0.0.0"
UDP_PORT = 20777

# Official F1 UDP packet IDs used by the project.
PACKET_LAP_DATA = 2
PACKET_CAR_TELEMETRY = 6

F1_HEADER_SIZE = 29
MAX_CARS = 22

# These are minimum bytes required from each player record.
CAR_TELEMETRY_MIN_SIZE = 18
LAP_DATA_MIN_SIZE = 38

# If no valid UDP packet is received for this long, the
# dashboard is considered disconnected.
UDP_STALE_SECONDS = 2.5


class F1UDPReceiver:
    """
    Robust F1 UDP telemetry receiver.

    Supports the common F1 23/24/25 packet layouts and keeps
    the parser tolerant of newer packet record sizes.

    IMPORTANT:
    - Vehicle telemetry comes ONLY from F1 UDP.
    - Lap number comes ONLY from F1 UDP LapData.
    - No hard-coded lap number is generated.
    - A UDP timeout clears live vehicle values.
    """

    def __init__(
        self,
        telemetry_store,
        host: str = UDP_HOST,
        port: int = UDP_PORT,
    ) -> None:
        self.telemetry_store = telemetry_store
        self.host = host
        self.port = port

        self.running = False
        self.sock: Optional[socket.socket] = None
        self.thread: Optional[threading.Thread] = None

        self.packet_count = 0
        self.telemetry_packet_count = 0
        self.lap_packet_count = 0
        self.invalid_packet_count = 0

        self.last_packet_format: Optional[int] = None
        self.last_game_year: Optional[int] = None
        self.last_game_major: Optional[int] = None
        self.last_game_minor: Optional[int] = None

        self.last_valid_packet_time: Optional[float] = None

        self.current_lap: Optional[int] = None
        self.previous_lap: Optional[int] = None
        self.last_completed_lap: Optional[int] = None
        self.current_lap_time: Optional[float] = None
        self.last_lap_time: Optional[float] = None
        self.lap_change_count = 0

    # ========================================================
    # START
    # ========================================================

    def start(self) -> None:
        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._receive_loop,
            daemon=True,
            name="F1-UDP-Receiver",
        )
        self.thread.start()

        print(
            f"[F1 UDP] Listening on "
            f"{self.host}:{self.port}"
        )

    # ========================================================
    # STOP
    # ========================================================

    def stop(self) -> None:
        self.running = False

        sock = self.sock
        self.sock = None

        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass

        thread = self.thread
        self.thread = None

        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=1.5)

        self._mark_disconnected()

    # ========================================================
    # RECEIVE LOOP
    # ========================================================

    def _receive_loop(self) -> None:
        try:
            sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM,
            )

            sock.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1,
            )

            sock.bind(
                (
                    self.host,
                    self.port,
                )
            )

            sock.settimeout(0.5)

            self.sock = sock

            print(
                "[F1 UDP] Receiver started "
                f"on {self.host}:{self.port}"
            )

        except Exception as exc:
            self.running = False
            self.sock = None

            print(
                "[F1 UDP] Failed to bind "
                f"{self.host}:{self.port}: {exc}"
            )

            self._mark_disconnected()
            return

        while self.running:
            try:
                data, _address = sock.recvfrom(4096)

                if not data:
                    continue

                self.packet_count += 1

                self._parse_packet(data)

                self._check_stale()

            except socket.timeout:
                self._check_stale()
                continue

            except OSError as exc:
                if self.running:
                    print(
                        "[F1 UDP] Socket error:",
                        exc,
                    )
                break

            except Exception as exc:
                self.invalid_packet_count += 1
                print(
                    "[F1 UDP] Unexpected packet error:",
                    repr(exc),
                )

        try:
            sock.close()
        except OSError:
            pass

        self._mark_disconnected()

    # ========================================================
    # STALE CONNECTION
    # ========================================================

    def _check_stale(self) -> None:
        if self.last_valid_packet_time is None:
            return

        age = (
            time.monotonic()
            - self.last_valid_packet_time
        )

        if age > UDP_STALE_SECONDS:
            self._mark_disconnected()

    def _mark_connected(
        self,
        header: dict,
    ) -> None:
        self.last_valid_packet_time = (
            time.monotonic()
        )

        try:
            self.telemetry_store.set_udp_status(
                connected=True,
                packet_format=header.get(
                    "packet_format"
                ),
                game_year=header.get(
                    "game_year"
                ),
                game_major=header.get(
                    "game_major"
                ),
                game_minor=header.get(
                    "game_minor"
                ),
            )
        except Exception as exc:
            print(
                "[F1 UDP] Could not update "
                f"connected status: {exc}"
            )

    def _mark_disconnected(self) -> None:
        self.last_valid_packet_time = None

        try:
            clear_method = getattr(
                self.telemetry_store,
                "clear_vehicle_telemetry",
                None,
            )

            if callable(clear_method):
                clear_method()

            self.telemetry_store.set_udp_status(
                connected=False,
            )

        except Exception as exc:
            print(
                "[F1 UDP] Could not update "
                f"disconnected status: {exc}"
            )

    # ========================================================
    # HEADER
    # ========================================================

    def _parse_header(
        self,
        data: bytes,
    ) -> Optional[dict]:
        if len(data) < F1_HEADER_SIZE:
            return None

        try:
            packet_format = struct.unpack_from(
                "<H",
                data,
                0,
            )[0]

            game_year = data[2]
            game_major = data[3]
            game_minor = data[4]
            packet_version = data[5]
            packet_id = data[6]

            player_car_index = data[27]
            secondary_player_index = data[28]

            if player_car_index >= MAX_CARS:
                return None

            return {
                "packet_format": packet_format,
                "game_year": game_year,
                "game_major": game_major,
                "game_minor": game_minor,
                "packet_version": packet_version,
                "packet_id": packet_id,
                "player_car_index": player_car_index,
                "secondary_player_index": (
                    secondary_player_index
                ),
            }

        except (
            IndexError,
            struct.error,
        ):
            return None

    # ========================================================
    # PLAYER RECORD SIZE
    # ========================================================

    def _get_record_size(
        self,
        data: bytes,
    ) -> Optional[int]:
        payload_size = (
            len(data)
            - F1_HEADER_SIZE
        )

        if payload_size <= 0:
            return None

        if payload_size % MAX_CARS != 0:
            return None

        record_size = (
            payload_size
            // MAX_CARS
        )

        if record_size <= 0:
            return None

        return record_size

    # ========================================================
    # PACKET DISPATCH
    # ========================================================

    def _parse_packet(
        self,
        data: bytes,
    ) -> None:
        header = self._parse_header(data)

        if header is None:
            self.invalid_packet_count += 1
            return

        self.last_packet_format = header[
            "packet_format"
        ]
        self.last_game_year = header[
            "game_year"
        ]
        self.last_game_major = header[
            "game_major"
        ]
        self.last_game_minor = header[
            "game_minor"
        ]

        packet_id = header["packet_id"]

        if packet_id == PACKET_CAR_TELEMETRY:
            self.telemetry_packet_count += 1

            if self._parse_car_telemetry(
                data,
                header,
            ):
                self._mark_connected(header)

        elif packet_id == PACKET_LAP_DATA:
            self.lap_packet_count += 1

            if self._parse_lap_data(
                data,
                header,
            ):
                self._mark_connected(header)

    # ========================================================
    # CAR TELEMETRY
    # ========================================================

    def _parse_car_telemetry(
        self,
        data: bytes,
        header: dict,
    ) -> bool:
        player_index = header[
            "player_car_index"
        ]

        record_size = self._get_record_size(
            data
        )

        if record_size is None:
            return False

        if record_size < CAR_TELEMETRY_MIN_SIZE:
            return False

        offset = (
            F1_HEADER_SIZE
            + player_index * record_size
        )

        if (
            offset + record_size
            > len(data)
        ):
            return False

        try:
            # CarTelemetryData:
            # speed uint16 @ 0
            speed_kmh = struct.unpack_from(
                "<H",
                data,
                offset + 0,
            )[0]

            # throttle float @ 2
            throttle = struct.unpack_from(
                "<f",
                data,
                offset + 2,
            )[0]

            # brake float @ 10
            brake = struct.unpack_from(
                "<f",
                data,
                offset + 10,
            )[0]

            # gear int8 @ 15
            gear = struct.unpack_from(
                "<b",
                data,
                offset + 15,
            )[0]

            # engine RPM uint16 @ 16
            rpm = struct.unpack_from(
                "<H",
                data,
                offset + 16,
            )[0]

        except (
            struct.error,
            ValueError,
        ):
            return False

        # ----------------------------------------------------
        # Sanity validation
        # ----------------------------------------------------

        try:
            throttle = float(throttle)
            brake = float(brake)
        except (
            TypeError,
            ValueError,
        ):
            return False

        if (
            speed_kmh < 0
            or speed_kmh > 450
        ):
            return False

        if rpm < 0 or rpm > 20000:
            return False

        if gear < -1 or gear > 8:
            return False

        if (
            throttle != throttle
            or brake != brake
        ):
            return False

        throttle = max(
            0.0,
            min(1.0, throttle),
        )

        brake = max(
            0.0,
            min(1.0, brake),
        )

        try:
            self.telemetry_store.update(
                speed_kmh=int(speed_kmh),
                rpm=int(rpm),
                gear=int(gear),
                throttle=throttle,
                brake=brake,
            )
        except Exception as exc:
            print(
                "[F1 UDP] Telemetry store "
                f"update failed: {exc}"
            )
            return False

        return True

    # ========================================================
    # LAP DATA
    # ========================================================

    def _parse_lap_data(
        self,
        data: bytes,
        header: dict,
    ) -> bool:
        player_index = header[
            "player_car_index"
        ]

        record_size = self._get_record_size(
            data
        )

        if record_size is None:
            return False

        if record_size < LAP_DATA_MIN_SIZE:
            return False

        offset = (
            F1_HEADER_SIZE
            + player_index * record_size
        )

        if (
            offset + record_size
            > len(data)
        ):
            return False

        try:
            # LapData:
            # lastLapTimeInMS @ 0
            # currentLapTimeInMS @ 4
            # carPosition @ 36
            # currentLapNum @ 37

            last_lap_time_ms = struct.unpack_from(
                "<I",
                data,
                offset + 0,
            )[0]

            current_lap_time_ms = struct.unpack_from(
                "<I",
                data,
                offset + 4,
            )[0]

            car_position = data[
                offset + 36
            ]

            current_lap = data[
                offset + 37
            ]

        except (
            struct.error,
            IndexError,
        ):
            return False

        if current_lap > 200:
            return False

        if (
            current_lap == 0
            and car_position == 0
            and current_lap_time_ms == 0
        ):
            return False

        current_lap_time = (
            current_lap_time_ms / 1000.0
        )

        last_lap_time = (
            last_lap_time_ms / 1000.0
            if last_lap_time_ms > 0
            else None
        )

        # ----------------------------------------------------
        # Autonomous lap tracking
        # ----------------------------------------------------

        if self.current_lap is None:
            self.current_lap = current_lap

            print(
                "[F1 UDP] Initial lap:",
                current_lap,
            )

        elif (
            current_lap
            != self.current_lap
        ):
            self.previous_lap = (
                self.current_lap
            )

            self.current_lap = current_lap
            self.last_completed_lap = (
                self.previous_lap
            )

            self.lap_change_count += 1

            print(
                "[F1 UDP] Lap change:",
                f"{self.previous_lap} -> "
                f"{self.current_lap}",
            )

        self.current_lap_time = (
            current_lap_time
        )

        if last_lap_time is not None:
            self.last_lap_time = (
                last_lap_time
            )

        try:
            self.telemetry_store.update(
                lap_number=int(
                    self.current_lap
                ),
                lap_time=current_lap_time,
            )

            self.telemetry_store.set_lap_state(
                current_lap=self.current_lap,
                previous_lap=self.previous_lap,
                last_completed_lap=(
                    self.last_completed_lap
                ),
                current_lap_time=(
                    self.current_lap_time
                ),
                last_lap_time=(
                    self.last_lap_time
                ),
                lap_change_count=(
                    self.lap_change_count
                ),
            )
        except Exception as exc:
            print(
                "[F1 UDP] Lap store update "
                f"failed: {exc}"
            )
            return False

        return True

    # ========================================================
    # STATUS
    # ========================================================

    def status(self) -> dict:
        age = None

        if self.last_valid_packet_time is not None:
            age = (
                time.monotonic()
                - self.last_valid_packet_time
            )

        return {
            "running": self.running,
            "packets_received": self.packet_count,
            "telemetry_packets": (
                self.telemetry_packet_count
            ),
            "lap_packets": (
                self.lap_packet_count
            ),
            "invalid_packets": (
                self.invalid_packet_count
            ),
            "packet_format": (
                self.last_packet_format
            ),
            "game_year": (
                self.last_game_year
            ),
            "game_major": (
                self.last_game_major
            ),
            "game_minor": (
                self.last_game_minor
            ),
            "last_packet_age_seconds": age,
            "current_lap": self.current_lap,
            "previous_lap": self.previous_lap,
            "last_completed_lap": (
                self.last_completed_lap
            ),
            "lap_change_count": (
                self.lap_change_count
            ),
            "host": self.host,
            "port": self.port,
        }


# ============================================================
# GLOBAL RECEIVER
# ============================================================

f1_udp_receiver: Optional[
    F1UDPReceiver
] = None


def start_f1_udp(
    telemetry_store,
) -> F1UDPReceiver:
    global f1_udp_receiver

    if (
        f1_udp_receiver is None
        or not f1_udp_receiver.running
    ):
        f1_udp_receiver = F1UDPReceiver(
            telemetry_store
        )
        f1_udp_receiver.start()

    return f1_udp_receiver


def stop_f1_udp() -> None:
    global f1_udp_receiver

    if f1_udp_receiver is not None:
        f1_udp_receiver.stop()
        f1_udp_receiver = None
