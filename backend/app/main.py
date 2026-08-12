from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    SimulatorTelemetryRequest,
)

from app.hf_pipeline import analyze_driver_state
from app.telemetry import simulator_telemetry


app = FastAPI(
    title="Silent Co-Driver AI Engine",
    description=(
        "AI driver analysis and racing simulator "
        "telemetry engine."
    ),
    version="2.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "status": "online",
        "system": "Silent Co-Driver AI Engine",
        "version": "2.0.0",
        "docs_url": "/docs",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "silent-co-driver-backend",
    }


# ============================================================
# SIMULATOR TELEMETRY
# ============================================================

@app.post("/api/v1/telemetry")
async def receive_simulator_telemetry(
    payload: SimulatorTelemetryRequest,
):
    try:
        simulator_telemetry.update(
            speed_kmh=payload.speed_kmh,
            rpm=payload.rpm,
            gear=payload.gear,
            throttle=payload.throttle,
            brake=payload.brake,
            lap_number=payload.lap_number,
        )

        return {
            "status": "received",
            "telemetry": simulator_telemetry.get(),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Telemetry error: {str(exc)}",
        ) from exc


@app.get("/api/v1/telemetry")
async def get_simulator_telemetry():
    return simulator_telemetry.get()


# ============================================================
# DRIVER ANALYSIS
# ============================================================

@app.post(
    "/api/v1/analyze",
    response_model=AnalysisResponse,
)
async def analyze_v1(
    payload: AnalysisRequest,
):
    input_text = (
        payload.text_input.strip()
        if payload.text_input
        else "Telemetry signal standard"
    )

    try:
        result = analyze_driver_state(
            text=input_text,
            lap=payload.lap_number or 18,
        )

        # Get latest simulator telemetry.
        simulator_data = simulator_telemetry.get()

        # The pipeline already creates fatigue,
        # fatigue_score and workload.
        #
        # Here we only attach actual simulator data.
        result["telemetry"]["speed_kmh"] = (
            simulator_data.get("speed_kmh")
        )

        result["telemetry"]["speed_available"] = (
            simulator_data.get(
                "speed_available",
                False,
            )
        )

        result["telemetry"]["rpm"] = (
            simulator_data.get("rpm")
        )

        result["telemetry"]["gear"] = (
            simulator_data.get("gear")
        )

        result["telemetry"]["throttle"] = (
            simulator_data.get("throttle")
        )

        result["telemetry"]["brake"] = (
            simulator_data.get("brake")
        )

        if simulator_data.get("speed_available"):
            result["telemetry"]["telemetry_source"] = (
                "Racing Simulator"
            )
        else:
            result["telemetry"]["telemetry_source"] = (
                "Driver voice analysis; "
                "simulator not connected"
            )

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Inference error: {str(exc)}",
        ) from exc


# Backward-compatible endpoint used by your frontend proxy.
@app.post(
    "/api/analyze",
    response_model=AnalysisResponse,
)
async def analyze(
    payload: AnalysisRequest,
):
    return await analyze_v1(payload)
