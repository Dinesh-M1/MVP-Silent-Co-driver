from typing import Any, Dict


def process_frame(frame: Any) -> Dict[str, Any]:
    """Create a lightweight structured summary from a frame-like object."""
    shape = getattr(frame, "shape", None)
    if isinstance(shape, tuple):
        height, width = shape[:2]
    else:
        height, width = None, None

    if height is not None and width is not None:
        occupancy = min(1.0, round((height * width) / 100000, 2))
    else:
        occupancy = 0.0

    return {
        "status": "processed",
        "frame_shape": shape,
        "frame_size": {"height": height, "width": width},
        "occupancy_score": occupancy,
        "quality_hint": "clear" if occupancy > 0.2 else "unknown"
    }
