from typing import List, Optional

from pydantic import BaseModel, Field


# ============================================================
# ANALYSIS REQUEST
# ============================================================

class AnalysisRequest(BaseModel):

    text_input: str = Field(
        default=""
    )

    driver_id: str = Field(
        default="DRIVER_01"
    )

    lap_number: int = Field(
        default=18,
        ge=1,
    )


# ============================================================
# STRATEGY
# ============================================================

class Strategy(BaseModel):

    action: str = Field(
        default=(
            "Monitor driver and "
            "vehicle state."
        )
    )

    target_compound: str = Field(
        default="UNKNOWN"
    )

    recommended_pit_lap: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# TELEMETRY
# ============================================================

class Telemetry(BaseModel):

    speed_kmh: Optional[float] = None

    speed_available: bool = False

    rpm: Optional[int] = None

    gear: Optional[int] = None

    throttle: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    brake: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    fatigue: str = "LOW"

    fatigue_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    workload: str = "NORMAL"

    telemetry_source: str = (
        "No live simulator connected"
    )


# ============================================================
# VOICE ANALYSIS
# ============================================================

class VoiceAnalysis(BaseModel):

    emotion: str = "NEUTRAL"

    tone: str = "CALM"

    energy: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    speech_rate: str = "NORMAL"

    voice_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )


# ============================================================
# DRIVER STATE
# ============================================================

class DriverState(BaseModel):

    state: str = "NORMAL"

    stress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    fatigue: str = "LOW"

    fatigue_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    workload: str = "NORMAL"

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )


# ============================================================
# RACE EVENT
# ============================================================

class RaceEvent(BaseModel):

    lap: int = Field(
        default=0,
        ge=0,
    )

    event_type: str = "normal"

    title: str = (
        "No significant event"
    )

    description: str = ""

    severity: str = "LOW"

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )


# ============================================================
# LAP PERFORMANCE
# ============================================================

class LapPerformancePoint(BaseModel):

    lap: int = Field(
        ge=1
    )

    lap_time: Optional[float] = Field(
        default=None,
        ge=0.0,
    )

    stress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    fatigue: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    driver_state: str = "NORMAL"

    event: Optional[str] = None

    event_type: Optional[str] = None

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )


# ============================================================
# DECISION
# ============================================================

class Decision(BaseModel):

    priority: str = "NORMAL"

    action: str = (
        "Continue monitoring "
        "driver and vehicle state."
    )

    reason: str = ""

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )


# ============================================================
# ANALYSIS RESPONSE
# ============================================================

class AnalysisResponse(BaseModel):

    transcript: str = ""

    stress_index: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    alert_level: str = "NORMAL"

    emotion_label: str = "NEUTRAL"

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    inference_source: Optional[str] = None

    detected_signals: List[str] = Field(
        default_factory=list
    )

    driver_message: str = ""

    telemetry: Telemetry = Field(
        default_factory=Telemetry
    )

    strategy: Strategy = Field(
        default_factory=Strategy
    )

    voice_analysis: VoiceAnalysis = Field(
        default_factory=VoiceAnalysis
    )

    driver_state: DriverState = Field(
        default_factory=DriverState
    )

    important_events: List[
        RaceEvent
    ] = Field(
        default_factory=list
    )

    lap_performance: List[
        LapPerformancePoint
    ] = Field(
        default_factory=list
    )

    decision: Decision = Field(
        default_factory=Decision
    )

    co_driver_response: str = ""


# ============================================================
# SIMULATOR TELEMETRY
# ============================================================

class SimulatorTelemetryRequest(BaseModel):

    speed_kmh: Optional[float] = Field(
        default=None,
        ge=0.0,
    )

    rpm: Optional[int] = Field(
        default=None,
        ge=0,
    )

    gear: Optional[int] = None

    throttle: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    brake: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    lap_number: Optional[int] = Field(
        default=None,
        ge=1,
    )

    lap_time: Optional[float] = Field(
        default=None,
        ge=0.0,
    )
