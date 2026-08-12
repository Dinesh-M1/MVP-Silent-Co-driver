from pydantic import BaseModel

class FrameBase64(BaseModel):
    image_base64: str

class TelemetryPayload(BaseModel):
    frame: FrameBase64
    driver_id: str | None = None
