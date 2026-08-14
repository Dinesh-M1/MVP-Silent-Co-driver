import re
from typing import Any, Dict, List, Optional


# ============================================================
# DETERMINISTIC PIT REQUEST RULES
# ============================================================
#
# Explicit race-radio commands are handled by this rule engine.
#
# IMPORTANT:
# Qwen, sentiment, and other AI output must NOT override
# an explicit motorsport command.
#
# Therefore:
#
#     "Box, box."
#     "Box box"
#
# will ALWAYS produce:
#
#     pit_request
#
# with the same decision every time.
# ============================================================

PIT_PATTERNS = [
    r"\bbox\s*,?\s*box\b",
    r"\bbox\s+box\b",
    r"\bbox\s+this\s+lap\b",
    r"\bbox\s+now\b",

    r"\bpit\s*,?\s*pit\b",
    r"\bpit\s+this\s+lap\b",
    r"\bpit\s+now\b",

    r"\bi\s+need\s+to\s+pit\b",
    r"\bneed\s+to\s+pit\b",

    r"\bpits?\s+this\s+lap\b",

    r"\bcome\s+in\b",
    r"\bcome\s+in\s+this\s+lap\b",

    r"\bbring\s+(?:me\s+)?in\b",
    r"\bbring\s+it\s+in\b",
    r"\bcall\s+me\s+in\b",

    r"\bbox\s+lap\b",
]


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_transcript(
    text: str,
) -> str:
    """
    Normalize whitespace and case.

    We intentionally do NOT aggressively rewrite words because
    Whisper output should remain semantically unchanged.
    """

    return re.sub(
        r"\s+",
        " ",
        str(text or "").strip().lower(),
    )


# ============================================================
# PIT REQUEST DETECTION
# ============================================================

def is_pit_request(
    text: str,
) -> bool:
    """
    Deterministic pit-request detector.

    IMPORTANT:

    "box" by itself is NOT considered a pit request.

    This avoids false positives from Whisper producing an
    isolated word.

    Examples:

        Box, box.          -> True
        Box box            -> True
        Box this lap       -> True
        Pit this lap       -> True
        I need to pit      -> True
        Come in            -> True
        box                -> False
        box on the lap     -> False
    """

    normalized = normalize_transcript(
        text
    )

    if not normalized:
        return False

    for pattern in PIT_PATTERNS:

        if re.search(
            pattern,
            normalized,
        ):
            return True

    return False


# ============================================================
# BUILD PIT EVENT
# ============================================================

def build_pit_event(
    transcript: str,
    lap_number: Optional[int],
    confidence: float,
) -> Dict[str, Any]:
    """
    Build the canonical PIT REQUEST event.

    lap_number may be None when the F1 simulator is not
    connected. We never invent a lap.
    """

    safe_confidence = max(
        0.0,
        min(
            1.0,
            float(
                confidence
            ),
        ),
    )

    return {
        "lap": lap_number,

        "event_type":
            "pit_request",

        "title":
            "PIT REQUEST",

        "description":
            (
                "Driver requested a pit stop using "
                "standard race radio terminology."
            ),

        "severity":
            "HIGH",

        "confidence":
            round(
                safe_confidence,
                2,
            ),
    }


# ============================================================
# NORMALIZE SINGLE EVENT
# ============================================================

def normalize_event(
    event: Dict[str, Any],
    transcript: str,
    lap_number: Optional[int],
    confidence: float,
) -> Dict[str, Any]:
    """
    Normalize a single event.

    Explicit PIT REQUEST always wins over a generic AI event.
    """

    if is_pit_request(
        transcript
    ):

        return build_pit_event(
            transcript=transcript,
            lap_number=lap_number,
            confidence=confidence,
        )

    return event


# ============================================================
# NORMALIZE EVENT LIST
# ============================================================

def normalize_events(
    events: List[
        Dict[str, Any]
    ],
    transcript: str,
    lap_number: Optional[int],
    confidence: float,
) -> List[
    Dict[str, Any]
]:
    """
    Normalize the complete event list.

    If the driver explicitly requests a pit stop:

        1. Remove generic "Other" events.
        2. Remove generic "normal" classifications.
        3. Remove duplicate PIT REQUEST events.
        4. Add exactly one canonical PIT REQUEST event.

    No fake lap number is generated.
    """

    safe_events: List[
        Dict[str, Any]
    ] = []

    if isinstance(
        events,
        list,
    ):

        for event in events:

            if isinstance(
                event,
                dict,
            ):

                safe_events.append(
                    event
                )

    # --------------------------------------------------------
    # No pit request
    # --------------------------------------------------------

    if not is_pit_request(
        transcript
    ):

        return safe_events

    # --------------------------------------------------------
    # Remove incorrect classifications
    # --------------------------------------------------------

    filtered: List[
        Dict[str, Any]
    ] = []

    for event in safe_events:

        title = str(
            event.get(
                "title",
                "",
            )
        ).strip().lower()

        event_type = str(
            event.get(
                "event_type",
                "",
            )
        ).strip().lower()

        # Generic AI classifications
        if title in {
            "other",
            "driver's communication",
            "driver's communication",
        }:

            continue

        if event_type == "normal":

            continue

        # Remove an existing PIT REQUEST so that we
        # always return exactly one canonical event.

        if (
            event_type
            == "pit_request"
        ):

            continue

        if (
            title
            == "pit request"
        ):

            continue

        filtered.append(
            event
        )

    # --------------------------------------------------------
    # Add canonical PIT REQUEST
    # --------------------------------------------------------

    filtered.append(
        build_pit_event(
            transcript=transcript,
            lap_number=lap_number,
            confidence=confidence,
        )
    )

    return filtered
