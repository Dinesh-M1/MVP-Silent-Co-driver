import asyncio
from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware

from app.racing_events import normalize_events
from app.f1_udp import start_f1_udp, stop_f1_udp
from app.hf_pipeline import (
    analyze_driver_audio,
    analyze_driver_state,
)
from app.schemas import SimulatorTelemetryRequest
from app.telemetry import simulator_telemetry


# ============================================================
# APPLICATION LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[SYSTEM] Silent Co-Driver backend starting")
    print("[SYSTEM] F1 UDP receiver starting...")

    try:
        start_f1_udp(simulator_telemetry)
    except Exception as exc:
        print("[SYSTEM] F1 UDP startup error:", repr(exc))

    yield

    print("[SYSTEM] F1 UDP receiver stopping...")

    try:
        stop_f1_udp()
    except Exception as exc:
        print("[SYSTEM] F1 UDP shutdown error:", repr(exc))


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Silent Co-Driver AI Engine",
    description=(
        "AI driver analysis and F1 racing telemetry engine."
    ),
    version="5.0.0",
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
        "OPTIONS",
        "DELETE",
    ],
    allow_headers=["*"],
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():
    telemetry = simulator_telemetry.get()

    return {
        "status": "online",
        "system": "Silent Co-Driver AI Engine",
        "version": "5.0.0",
        "f1_udp_connected": telemetry.get(
            "udp_connected",
            False,
        ),
        "telemetry_source": telemetry.get(
            "telemetry_source"
        ),
        "endpoints": {
            "health": "/health",
            "telemetry": "/api/v1/telemetry",
            "text_analysis": "/api/v1/analyze",
            "audio_analysis": "/api/v1/analyze-audio",
            "docs": "/docs",
        },
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():
    telemetry = simulator_telemetry.get()

    return {
        "status": "healthy",
        "service": "silent-co-driver-backend",
        "f1_udp_connected": telemetry.get(
            "udp_connected",
            False,
        ),
        "telemetry_source": telemetry.get(
            "telemetry_source"
        ),
        "speed_kmh": telemetry.get(
            "speed_kmh"
        ),
        "rpm": telemetry.get(
            "rpm"
        ),
        "gear": telemetry.get(
            "gear"
        ),
        "lap_number": telemetry.get(
            "lap_number"
        ),
    }


# ============================================================
# TELEMETRY
# ============================================================

@app.post("/api/v1/telemetry")
async def receive_simulator_telemetry(
    payload: SimulatorTelemetryRequest,
):
    """
    Compatibility endpoint for external simulators.

    F1 UDP remains the preferred live source when connected.
    """

    try:
        simulator_telemetry.update(
            speed_kmh=payload.speed_kmh,
            rpm=payload.rpm,
            gear=payload.gear,
            throttle=payload.throttle,
            brake=payload.brake,
            lap_number=payload.lap_number,
            lap_time=payload.lap_time,
        )

        return {
            "status": "received",
            "telemetry": simulator_telemetry.get(),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Telemetry error: {exc}",
        ) from exc


@app.get("/api/v1/telemetry")
async def get_simulator_telemetry():
    return simulator_telemetry.get()


@app.get("/api/v1/telemetry/history")
async def get_telemetry_history(
    limit: int = 50,
):
    limit = max(
        1,
        min(int(limit), 200),
    )

    return {
        "laps": simulator_telemetry.get_lap_history(
            limit=limit
        )
    }


@app.delete("/api/v1/telemetry/history")
async def clear_telemetry_history():
    simulator_telemetry.clear_history()

    return {
        "status": "cleared",
        "laps": [],
    }


# ============================================================
# F1 UDP STATUS
# ============================================================

@app.get("/api/v1/f1-udp/status")
async def f1_udp_status():
    """
    Exposes receiver diagnostics so the frontend/engineer can
    distinguish "UDP is not running" from "UDP is running but
    the game is not sending packets".
    """

    from app.f1_udp import f1_udp_receiver

    telemetry = simulator_telemetry.get()

    receiver_status = (
        f1_udp_receiver.status()
        if f1_udp_receiver is not None
        else {
            "running": False,
            "packets_received": 0,
            "telemetry_packets": 0,
            "lap_packets": 0,
            "invalid_packets": 0,
            "host": "0.0.0.0",
            "port": 20777,
        }
    )

    return {
        "udp_connected": telemetry.get(
            "udp_connected",
            False,
        ),
        "telemetry": telemetry,
        "receiver": receiver_status,
    }


# ============================================================
# AUTHORITATIVE LAP
# ============================================================

def get_current_lap() -> int | None:
    """
    F1 UDP is the only authoritative lap source.

    No 18.
    No 0.
    No frontend fallback.
    """

    telemetry = simulator_telemetry.get()

    if not telemetry.get(
        "udp_connected",
        False,
    ):
        return None

    raw_lap = telemetry.get(
        "lap_number"
    )

    if raw_lap is None:
        return None

    try:
        lap = int(raw_lap)
    except (
        TypeError,
        ValueError,
    ):
        return None

    if lap <= 0:
        return None

    return lap


# ============================================================
# ATTACH LIVE TELEMETRY
# ============================================================

def attach_simulator_telemetry(
    result: dict,
) -> dict:
    live = simulator_telemetry.get()

    telemetry = result.setdefault(
        "telemetry",
        {},
    )

    # Vehicle values are copied directly from the telemetry store.
    for key in (
        "speed_kmh",
        "speed_available",
        "rpm",
        "gear",
        "throttle",
        "brake",
        "lap_number",
        "lap_time",
        "previous_lap",
        "last_completed_lap",
        "current_lap_time",
        "last_lap_time",
        "lap_change_count",
        "udp_connected",
        "udp_packet_format",
        "udp_game_year",
        "udp_game_major",
        "udp_game_minor",
    ):
        telemetry[key] = live.get(key)

    driver_state = (
        result.get("driver_state")
        or {}
    )

    telemetry.setdefault(
        "fatigue_score",
        driver_state.get(
            "fatigue_score",
            result.get(
                "stress_index",
                0.0,
            ),
        ),
    )

    telemetry.setdefault(
        "fatigue",
        driver_state.get(
            "fatigue",
            "LOW",
        ),
    )

    telemetry.setdefault(
        "workload",
        driver_state.get(
            "workload",
            "NORMAL",
        ),
    )

    if live.get(
        "udp_connected",
        False,
    ):
        telemetry[
            "telemetry_source"
        ] = "F1 UDP Telemetry"
    else:
        telemetry[
            "telemetry_source"
        ] = "No live simulator connected"

    return result


# ============================================================
# EVENT NORMALIZATION
# ============================================================

def normalize_analysis_events(
    result: dict,
    lap: int | None,
) -> dict:
    transcript = str(
        result.get(
            "transcript",
            "",
        )
        or ""
    )

    events = result.get(
        "important_events",
        [],
    ) or []

    try:
        confidence = float(
            result.get(
                "confidence",
                0.0,
            )
            or 0.0
        )
    except (
        TypeError,
        ValueError,
    ):
        confidence = 0.0

    # Racing event code historically expects an int.
    # If UDP is unavailable, use 0 ONLY for the event schema.
    # The authoritative result lap remains None.
    event_lap = (
        lap
        if lap is not None
        else 0
    )

    result[
        "important_events"
    ] = normalize_events(
        events=events,
        transcript=transcript,
        lap_number=event_lap,
        confidence=confidence,
    )

    return result


# ============================================================
# LAP HISTORY
# ============================================================

def store_analysis_in_lap_history(
    result: dict,
    lap: int | None,
) -> None:
    if lap is None:
        return

    driver_state = (
        result.get("driver_state")
        or {}
    )

    telemetry = (
        result.get("telemetry")
        or {}
    )

    events = (
        result.get("important_events")
        or []
    )

    latest_event = (
        events[-1]
        if events
        else {}
    )

    try:
        simulator_telemetry.update_driver_state(
            lap_number=lap,
            stress=result.get(
                "stress_index",
                driver_state.get(
                    "stress",
                    0.0,
                ),
            ),
            fatigue=telemetry.get(
                "fatigue_score",
                driver_state.get(
                    "fatigue_score",
                    0.0,
                ),
            ),
            driver_state=driver_state.get(
                "state",
                "NORMAL",
            ),
            event=latest_event.get(
                "title"
            ),
            event_type=latest_event.get(
                "event_type"
            ),
            confidence=latest_event.get(
                "confidence",
                result.get(
                    "confidence",
                    0.0,
                ),
            ),
        )

    except Exception as exc:
        # Analysis must not fail just because lap-history
        # visualization storage has a problem.
        print(
            "[LAP HISTORY ERROR]",
            repr(exc),
        )


# ============================================================
# TEXT EXTRACTION
# ============================================================

def extract_text_from_payload(
    payload: object,
) -> str:
    """
    Accept every text field used by the different versions
    of this project.

    This removes the previous frontend/backend schema mismatch.
    """

    if not isinstance(
        payload,
        dict,
    ):
        return ""

    for key in (
        "text_input",
        "driver_radio_text",
        "transcript",
        "text",
        "message",
        "driver_message",
    ):
        value = payload.get(key)

        if value is None:
            continue

        text = str(value).strip()

        if text:
            return text

    return ""


# ============================================================
# CORE TEXT ANALYSIS
# ============================================================

async def _analyze_text(
    input_text: str,
    driver_id: str,
):
    if not input_text:
        raise HTTPException(
            status_code=400,
            detail="Driver radio text is required.",
        )

    # F1 UDP owns the actual lap.
    lap = get_current_lap()

    print(
        "[TEXT ANALYSIS]",
        f"driver={driver_id}",
        f"lap={lap}",
        f"text={input_text!r}",
    )

    # The HF pipeline accepts a lap argument.
    # When no live lap exists, 0 is used internally only.
    # The returned public lap is always None in that case.
    inference_lap = (
        lap
        if lap is not None
        else 0
    )

    try:
        result = await asyncio.to_thread(
            analyze_driver_state,
            input_text,
            inference_lap,
        )

        if not isinstance(
            result,
            dict,
        ):
            result = dict(result)

        result = attach_simulator_telemetry(
            result
        )

        actual_lap = get_current_lap()

        result[
            "lap_number"
        ] = actual_lap

        result[
            "driver_id"
        ] = driver_id

        result = normalize_analysis_events(
            result=result,
            lap=actual_lap,
        )

        store_analysis_in_lap_history(
            result=result,
            lap=actual_lap,
        )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        print(
            "[TEXT ANALYSIS ERROR]",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Text analysis error: {exc}"
            ),
        ) from exc


# ============================================================
# TEXT ANALYSIS
# ============================================================

@app.post("/api/v1/analyze")
async def analyze_v1(
    request: Request,
):
    """
    Raw JSON endpoint.

    Accepted:
        {"text_input": "Box, box."}
        {"driver_radio_text": "Box, box."}

    Both are supported.
    """

    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON body: {exc}",
        ) from exc

    input_text = extract_text_from_payload(
        payload
    )

    driver_id = (
        str(
            payload.get(
                "driver_id",
                "DRIVER_01",
            )
        ).strip()
        if isinstance(
            payload,
            dict,
        )
        else "DRIVER_01"
    )

    if not driver_id:
        driver_id = "DRIVER_01"

    return await _analyze_text(
        input_text=input_text,
        driver_id=driver_id,
    )


# ============================================================
# LEGACY TEXT ENDPOINT
# ============================================================

@app.post("/api/analyze")
async def analyze_legacy(
    request: Request,
):
    return await analyze_v1(
        request
    )


# ============================================================
# AUDIO ANALYSIS
# ============================================================

@app.post("/api/v1/analyze-audio")
async def analyze_audio(
    audio: UploadFile = File(...),
    driver_id: str = Form(
        "DRIVER_01"
    ),
    lap_number: int | None = Form(
        None
    ),
):
    """
    Multipart audio endpoint.

    Required field:
        audio

    Optional:
        driver_id
        lap_number

    The supplied lap_number is intentionally ignored as an
    authority. F1 UDP owns the public lap.
    """

    if audio is None:
        raise HTTPException(
            status_code=400,
            detail="Audio file is required.",
        )

    filename = (
        audio.filename
        or "driver_radio.wav"
    )

    content_type = (
        audio.content_type
        or ""
    ).lower()

    if (
        content_type
        and not content_type.startswith(
            "audio/"
        )
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported audio content type: "
                f"{content_type}"
            ),
        )

    try:
        audio_bytes = await audio.read()
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not read audio file: "
                f"{exc}"
            ),
        ) from exc

    if not audio_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded audio file is empty.",
        )

    lap = get_current_lap()

    print(
        "[AUDIO ANALYSIS]",
        f"driver={driver_id}",
        f"lap={lap}",
        f"file={filename}",
        f"bytes={len(audio_bytes)}",
    )

    inference_lap = (
        lap
        if lap is not None
        else 0
    )

    try:
        result = await asyncio.to_thread(
            analyze_driver_audio,
            audio_bytes,
            inference_lap,
        )

        if not isinstance(
            result,
            dict,
        ):
            result = dict(result)

        result = attach_simulator_telemetry(
            result
        )

        actual_lap = get_current_lap()

        result[
            "lap_number"
        ] = actual_lap

        result[
            "driver_id"
        ] = driver_id

        result[
            "audio_filename"
        ] = filename

        result[
            "audio_content_type"
        ] = content_type

        result = normalize_analysis_events(
            result=result,
            lap=actual_lap,
        )

        store_analysis_in_lap_history(
            result=result,
            lap=actual_lap,
        )

        # Keep a guaranteed decision object.
        if not result.get(
            "decision"
        ):
            strategy = (
                result.get(
                    "strategy"
                )
                or {}
            )

            result[
                "decision"
            ] = {
                "priority": result.get(
                    "alert_level",
                    "NORMAL",
                ),
                "action": strategy.get(
                    "action",
                    (
                        "Continue monitoring "
                        "driver and vehicle state."
                    ),
                ),
                "reason": (
                    "Generated from "
                    "driver analysis."
                ),
                "confidence": result.get(
                    "confidence",
                    0.0,
                ),
            }

        return result

    except HTTPException:
        raise

    except Exception as exc:
        print(
            "[AUDIO ANALYSIS ERROR]",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Audio analysis error: {exc}"
            ),
        ) from exc
