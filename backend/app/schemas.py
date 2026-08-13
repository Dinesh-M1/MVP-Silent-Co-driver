from pydantic import BaseModel, Field
from typing import Optional


class Strategy(BaseModel):
    action: str
    target_compound: str
    recommended_pit_lap: int


class Telemetry(BaseModel):
    fatigue: str = "LOW"
    fatigue_score: float = 0.15
    workload: str = "NORMAL"

    # Simulator telemetry is optional until a simulator is connected.
    speed_kmh: Optional[float] = None
    ear: Optional[float] = None
    rpm: Optional[float] = None
    gear: Optional[int] = None


class DetectedSignals(BaseModel):
    grip_loss: bool = False
    tire_problem: bool = False
    overheating: bool = False
    puncture: bool = False
    braking_problem: bool = False
    steering_problem: bool = False
    engine_problem: bool = False
    traffic: bool = False
    fatigue: bool = False
    high_workload: bool = False
    sliding: bool = False
    vibration: bool = False


class AnalysisRequest(BaseModel):
    text_input: str = Field(..., min_length=1)
    driver_id: str = "DRIVER_01"
    lap_number: int = 1


class SimulatorTelemetryRequest(BaseModel):
    speed_kmh: Optional[float] = None
    rpm: Optional[float] = None
    gear: Optional[int] = None
    throttle: Optional[float] = None
    brake: Optional[float] = None


class AnalysisResponse(BaseModel):
    transcript: str

    stress_index: float
    alert_level: str
    emotion_label: str
    confidence: float

    inference_source: Optional[str] = None

    telemetry: Telemetry

    strategy: Strategy

    driver_message: str

    detected_signals: DetectedSignals
