import os
from typing import Dict, Any


def get_hf_client() -> Dict[str, Any]:
    """Return a lightweight client configuration object for the co-driver."""
    return {
        "token": bool(os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_TOKEN")),
        "provider": "huggingface",
        "status": "configured" if os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_TOKEN") else "fallback"
    }


def build_recommendation(text: str, alert_level: str) -> Dict[str, Any]:
    """Create a compact co-driver recommendation from telemetry text."""
    lowered = text.lower()
    if alert_level == "CRITICAL" or any(word in lowered for word in ["lost", "grip", "slip", "crash", "box"]):
        return {
            "message": "Reduce pace, prioritize car stability, and prepare a defensive box call.",
            "tone": "urgent",
            "confidence": 0.91,
        }
    if alert_level == "ELEVATED" or any(word in lowered for word in ["warm", "traffic", "delta", "struggling"]):
        return {
            "message": "Keep the rhythm consistent and monitor tire load before the next stint.",
            "tone": "steady",
            "confidence": 0.78,
        }
    return {
        "message": "Maintain current pace and preserve tire life through the next phase.",
        "tone": "calm",
        "confidence": 0.74,
        }
