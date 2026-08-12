from typing import List, Optional

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    text_input: str = Field(
        default="",
        description="Raw driver radio or voice transcript",
    )

    driver_id: str = Field(
        default="DRIVER_01",
        description="Driver identifier",
    )

    lap_number: int = Field(
        default=18,
        ge=1,
        description="Current racing lap",
    )


class Strategy(BaseModel):
    action: str
    target_compound: str
    recommended_pit_lap: int


class Telemetry(BaseModel):
    """
    Driver and racing simulator telemetry.

    Speed is optional because a simulator is not connected yet.
    """

    speed_kmh: Optional[float] = None

    speed_available: bool = False

    rpm: Optional[int] = None

    gear: Optional[int] = None

    throttle: Optional[float] = None

    brake: Optional[float] = None

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


class AnalysisResponse(BaseModel):
    transcript: str

    stress_index: float = Field(
        ge=0.0,
        le=1.0,
    )

    alert_level: str

    emotion_label: str

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    inference_source: Optional[str] = None

    # Your pipeline returns a LIST such as:
    # ["grip_loss", "tire_overheating"]
    detected_signals: List[str] = Field(
        default_factory=list
    )

    driver_message: str

    telemetry: Telemetry

    strategy: Strategy


class SimulatorTelemetryRequest(BaseModel):
    """
    Data that will eventually come from the
    racing simulator.
    """

    speed_kmh: Optional[float] = Field(
        default=None,
        ge=0.0,
    )

    rpm: Optional[int] = Field(
        default=None,
        ge=0,
    )

    gear: Optional[int] = Field(
        default=None,
    )

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
