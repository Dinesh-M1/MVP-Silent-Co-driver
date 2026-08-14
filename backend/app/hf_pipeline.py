"""
Silent Co-Driver
Hugging Face Hosted AI Pipeline

Pipeline:

    Driver Radio / Text
            |
            v
    Speech-to-Text
       Whisper
            |
            v
    Voice Emotion
       Wav2Vec2
            |
            v
    Transcript Understanding
          Qwen
            |
            v
    Motorsport Rule Engine
            |
            +----> FINAL ENGINEERING DECISION
            |
            v
    Driver State
            |
            v
    Strategy / Co-Driver Response

    Qwen = context/explanation only
    Wav2Vec2 = voice emotion only
    Explicit rule-engine signals always win

Important:
- Models are NOT downloaded into the Hugging Face Space.
- Inference is performed through Hugging Face Inference Providers.
- HF failure falls back to the local motorsport rule engine.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from huggingface_hub import InferenceClient


# ============================================================
# ENVIRONMENT
# ============================================================

HF_TOKEN = os.getenv("HF_TOKEN", "").strip()

# Hugging Face hosted models
HF_SENTIMENT_MODEL = os.getenv(
    "HF_SENTIMENT_MODEL",
    "distilbert/distilbert-base-uncased-finetuned-sst-2-english",
)

HF_ASR_MODEL = os.getenv(
    "HF_ASR_MODEL",
    "openai/whisper-large-v3",
)

HF_EMOTION_MODEL = os.getenv(
    "HF_EMOTION_MODEL",
    "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition",
)

HF_REASONING_MODEL = os.getenv(
    "HF_REASONING_MODEL",
    "Qwen/Qwen2.5-1.5B-Instruct",
)


# ============================================================
# HUGGING FACE CLIENT
# ============================================================

_client: Optional[InferenceClient] = None


def get_hf_client() -> Optional[InferenceClient]:
    """
    Create one shared Hugging Face client.

    If HF_TOKEN is missing, return None and allow the
    local rule engine to operate.
    """

    global _client

    if not HF_TOKEN:
        return None

    if _client is None:
        _client = InferenceClient(
            provider="auto",
            api_key=HF_TOKEN,
        )

    return _client


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text: str) -> str:
    """
    Normalize transcript/radio text.
    """

    text = str(text or "").strip()

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text


# ============================================================
# MOTORSPORT SIGNAL PATTERNS
# ============================================================

SIGNAL_PATTERNS = {

    "grip_loss": [
        r"\blost grip\b",
        r"\blosing grip\b",
        r"\bno grip\b",
        r"\bgrip is gone\b",
        r"\bsliding\b",
        r"\bslip(ping)?\b",
        r"\bstepping out\b",
        r"\brear is moving\b",
        r"\brear is gone\b",
        r"\bundersteer\b",
        r"\boversteer\b",
        r"\bno traction\b",
        r"\blosing traction\b",
        r"\bcan't put the power down\b",
        r"\bcan'?t get the power down\b",
    ],

    "rear_instability": [
        r"\brear is stepping out\b",
        r"\brear stepping out\b",
        r"\brear is loose\b",
        r"\brear feels loose\b",
        r"\brear end is loose\b",
        r"\brear is unstable\b",
        r"\brear instability\b",
        r"\brear keeps sliding\b",
        r"\brear keeps moving\b",
        r"\bback of the car is sliding\b",
        r"\bback end is sliding\b",
    ],

    "front_instability": [
        r"\bundersteer\b",
        r"\bfront is washing out\b",
        r"\bfront end is washing\b",
        r"\bfront doesn't turn\b",
        r"\bfront won't turn\b",
        r"\bcan't turn in\b",
        r"\bcan'?t turn in\b",
        r"\bpoor turn in\b",
    ],

    "tire_overheating": [
        r"\boverheating\b",
        r"\boverheated\b",
        r"\btyres? (are )?too hot\b",
        r"\btires? (are )?too hot\b",
        r"\btyres? are hot\b",
        r"\btires? are hot\b",
        r"\btyre temperature\b",
        r"\btire temperature\b",
        r"\btemperatures? (are )?high\b",
        r"\btemps? (are )?high\b",
        r"\btemps? are climbing\b",
        r"\btyres? are cooking\b",
        r"\btires? are cooking\b",
    ],

    "tire_wear": [
        r"\btyre wear\b",
        r"\btire wear\b",
        r"\btyres? are worn\b",
        r"\btires? are worn\b",
        r"\btyres? are gone\b",
        r"\btires? are gone\b",
        r"\btyre degradation\b",
        r"\btire degradation\b",
        r"\bdegrad(ing|ation)\b",
        r"\bfalling off\b",
        r"\bno life left\b",
    ],

    "puncture": [
        r"\bpuncture\b",
        r"\bpunctured\b",
        r"\bflat tyre\b",
        r"\bflat tire\b",
        r"\btyre is flat\b",
        r"\btire is flat\b",
    ],

    "brake_problem": [
        r"\bbrake problem\b",
        r"\bbrakes? are gone\b",
        r"\bbrakes? feel bad\b",
        r"\bbrakes? feel weak\b",
        r"\bbrakes? are weak\b",
        r"\bno brakes\b",
        r"\blong brake pedal\b",
        r"\bbraking problem\b",
        r"\bcan't brake\b",
        r"\bcan'?t brake\b",
        r"\bbrake failure\b",
    ],

    "steering_problem": [
        r"\bsteering problem\b",
        r"\bsteering is heavy\b",
        r"\bsteering feels heavy\b",
        r"\bsteering feels wrong\b",
        r"\bsteering issue\b",
        r"\bsteering failure\b",
    ],

    "engine_problem": [
        r"\bengine problem\b",
        r"\bengine issue\b",
        r"\bengine failure\b",
        r"\bengine is overheating\b",
        r"\bpower loss\b",
        r"\blost power\b",
        r"\bno power\b",
        r"\bengine feels weak\b",
    ],

    "car_failure": [
        r"\bbroken\b",
        r"\bfailure\b",
        r"\bfailed\b",
        r"\bnot working\b",
        r"\bmalfunction\b",
        r"\bsomething broke\b",
        r"\bsomething is broken\b",
    ],

    "pit_request": [
        r"\bbox box\b",
        r"\bbox this lap\b",
        r"\bbox now\b",
        r"\bbox\b",
        r"\bi need to pit\b",
        r"\bneed to pit\b",
        r"\bpit this lap\b",
        r"\bpit now\b",
        r"\bcome in\b",
        r"\bbring me in\b",
        r"\bbring it in\b",
        r"\bcall me in\b",
    ],

    "traffic": [
        r"\btraffic\b",
        r"\bblue flags?\b",
        r"\bcar ahead\b",
        r"\bcars ahead\b",
        r"\bstuck behind\b",
        r"\bgetting held up\b",
        r"\bcan't get past\b",
        r"\bcan'?t get past\b",
    ],

    "vibration": [
        r"\bvibration\b",
        r"\bvibrating\b",
        r"\bshaking\b",
        r"\bwheel is shaking\b",
        r"\bcar is shaking\b",
    ],

    "driver_stress": [
        r"\bstruggling\b",
        r"\bfrustrated\b",
        r"\bfrustrating\b",
        r"\bangry\b",
        r"\bfurious\b",
        r"\bstressed\b",
        r"\bstress(ed)?\b",
        r"\banxious\b",
        r"\bworried\b",
        r"\bnervous\b",
        r"\bscared\b",
        r"\bcan't do this\b",
        r"\bcan'?t do this\b",
        r"\bthis is bad\b",
        r"\bthis feels bad\b",
        r"\bdamn\b",
        r"\bshit\b",
        r"\bfuck\b",
    ],

    "positive_state": [
        r"\bcar feels good\b",
        r"\bcar feels great\b",
        r"\bcar feels fantastic\b",
        r"\bbalance is good\b",
        r"\bbalance is perfect\b",
        r"\bfeels perfect\b",
        r"\bfeels great\b",
        r"\bfeels good\b",
        r"\bno issues\b",
        r"\bno problem\b",
        r"\bcomfortable\b",
        r"\bconfident\b",
        r"\bpace is good\b",
        r"\bpace is strong\b",
        r"\ball good\b",
        r"\beverything is good\b",
    ],
}


# ============================================================
# SIGNAL SEVERITY
# ============================================================

SIGNAL_SEVERITY = {
    "puncture": 1.00,
    "car_failure": 0.95,
    "engine_problem": 0.95,
    "brake_problem": 0.95,
    "steering_problem": 0.90,
    "grip_loss": 0.75,
    "rear_instability": 0.80,
    "front_instability": 0.70,
    "tire_overheating": 0.75,
    "tire_wear": 0.65,
    "driver_stress": 0.65,
    "pit_request": 0.55,
    "vibration": 0.55,
    "traffic": 0.35,
    "positive_state": 0.00,
}


# ============================================================
# SIGNAL DETECTION
# ============================================================

def detect_signals(text: str) -> List[str]:
    """
    Rule-based safety net.

    This is deliberately retained even after adding AI.
    The LLM should not be the only source of truth for
    motorsport alerts.
    """

    lower = text.lower()

    detected: List[str] = []

    for signal, patterns in SIGNAL_PATTERNS.items():

        if any(
            re.search(
                pattern,
                lower,
            )
            for pattern in patterns
        ):
            detected.append(signal)

    return detected


# ============================================================
# SIGNAL SEVERITY
# ============================================================

def calculate_signal_severity(
    signals: List[str],
) -> float:

    if not signals:
        return 0.0

    strongest = max(
        SIGNAL_SEVERITY.get(
            signal,
            0.0,
        )
        for signal in signals
    )

    additional = max(
        0,
        len(signals) - 1,
    ) * 0.05

    return min(
        1.0,
        strongest + additional,
    )


# ============================================================
# HUGGING FACE SENTIMENT
# ============================================================

def run_huggingface_sentiment(
    text: str,
) -> Tuple[str, float, str]:

    client = get_hf_client()

    if client is None:
        return (
            "UNKNOWN",
            0.50,
            "Motorsport Rule Engine",
        )

    try:

        result = client.text_classification(
            text,
            model=HF_SENTIMENT_MODEL,
        )

        if not result:
            return (
                "UNKNOWN",
                0.50,
                "Motorsport Rule Engine",
            )

        best = max(
            result,
            key=lambda item: float(item.score),
        )

        label = str(
            best.label
        ).upper()

        score = float(
            best.score
        )

        return (
            label,
            score,
            f"Hugging Face: {HF_SENTIMENT_MODEL}",
        )

    except Exception as exc:

        print(
            "Hugging Face sentiment unavailable:",
            exc,
        )

        return (
            "UNKNOWN",
            0.50,
            "Motorsport Rule Engine",
        )


# ============================================================
# QWEN RACE MESSAGE ANALYSIS
# ============================================================

def run_qwen_race_analysis(
    text: str,
) -> Dict[str, Any]:
    """
    Ask Qwen to interpret ANY driver message.

    The rule engine remains the fallback.
    """

    client = get_hf_client()

    if client is None:
        return {}

    system_prompt = """
You are the intelligence/explanation module of an AI
motorsport race engineer called Silent Co-Driver.

Analyze the driver's radio message in a professional
motorsport race-engineering context.

Return ONLY valid JSON.

IMPORTANT DECISION AUTHORITY:

The deterministic motorsport rule engine is the source
of truth for explicit racing commands and engineering
alerts.

You MUST NOT override, reinterpret, or contradict an
explicit motorsport command detected by the rule engine.

Examples:
- "Box, box" = pit_request
- "Box this lap" = pit_request
- "Pit this lap" = pit_request
- "Pit now" = pit_request
- "I need to pit" = pit_request

Do not reinterpret the racing word "box" as another
meaning when it appears in a driver radio context.

Qwen provides context and explanation only. It does not
make the final engineering decision.

Required fields:

{
  "category": "vehicle_handling | tyres | brakes | engine | steering | driver_condition | strategy | traffic | other",
  "component": "string",
  "issue": "short snake_case description",
  "severity": "low | medium | high | critical",
  "urgency": "low | medium | high | critical",
  "driver_state": "NORMAL | FOCUSED | ELEVATED | HIGH | CRITICAL",
  "description": "short explanation",
  "confidence": 0.0
}

Do not invent telemetry.
Do not invent a mechanical failure if the driver only
describes a feeling.
"""

    user_prompt = f"""
Driver radio:

"{text}"

Analyze the message for a professional motorsport
race-engineering context.
"""

    try:

        completion = client.chat_completion(
            model=HF_REASONING_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=0.0,
            max_tokens=350,
        )

        content = (
            completion.choices[0]
            .message.content
        )

        if not content:
            return {}

        parsed = extract_json_object(
            content
        )

        if not isinstance(
            parsed,
            dict,
        ):
            return {}

        return parsed

    except Exception as exc:

        print(
            "Qwen race analysis unavailable:",
            exc,
        )

        return {}


# ============================================================
# JSON EXTRACTION
# ============================================================

def extract_json_object(
    text: str,
) -> Optional[Dict[str, Any]]:
    """
    Qwen can occasionally surround JSON with markdown.
    Extract the first JSON object safely.
    """

    text = str(text or "").strip()

    try:
        direct = json.loads(text)

        if isinstance(
            direct,
            dict,
        ):
            return direct

    except Exception:
        pass

    match = re.search(
        r"\{.*\}",
        text,
        flags=re.DOTALL,
    )

    if not match:
        return None

    try:

        parsed = json.loads(
            match.group(0)
        )

        if isinstance(
            parsed,
            dict,
        ):
            return parsed

    except Exception:
        return None

    return None


# ============================================================
# DRIVER STATE
# ============================================================

def calculate_driver_state(
    signals: List[str],
    sentiment_label: str,
    sentiment_score: float,
    ai_analysis: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Calculate driver state from deterministic signals and
    sentiment only.

    Qwen's driver_state is intentionally NOT allowed to
    override the deterministic driver-state calculation.
    """

    # Explicit pit commands have a deterministic driver-state
    # profile. AI availability or Qwen output must not change
    # the result for identical race-radio text.
    if "pit_request" in signals:
        return {
            "stress_index": 0.47,
            "alert_level": "ELEVATED",
            "emotion_label": "DRIVER UNDER LOAD",
            "confidence": 0.95,
        }

    severity = calculate_signal_severity(
        signals
    )

    stress = (
        0.15
        + severity * 0.60
    )

    if sentiment_label == "NEGATIVE":
        stress += (
            sentiment_score * 0.20
        )
    elif sentiment_label == "POSITIVE":
        stress -= (
            sentiment_score * 0.08
        )

    if "positive_state" in signals:
        stress -= 0.15

    stress_index = round(
        max(
            0.0,
            min(
                1.0,
                stress,
            ),
        ),
        2,
    )

    critical = {
        "puncture",
        "car_failure",
        "engine_problem",
        "brake_problem",
        "steering_problem",
    }

    if any(
        signal in critical
        for signal in signals
    ):
        alert = "CRITICAL"

    elif (
        stress_index >= 0.75
        or any(
            signal in signals
            for signal in (
                "grip_loss",
                "rear_instability",
                "tire_overheating",
            )
        )
    ):
        alert = "CRITICAL"

    elif (
        stress_index >= 0.45
        or signals
    ):
        alert = "ELEVATED"

    else:
        alert = "NORMAL"

    if alert == "CRITICAL":
        emotion = (
            "HIGH STRESS / ANXIETY"
            if "driver_stress" in signals
            else "HIGH ALERT"
        )

    elif alert == "ELEVATED":
        emotion = (
            "MODERATE STRESS"
            if "driver_stress" in signals
            else "DRIVER UNDER LOAD"
        )

    else:
        emotion = (
            "CALM / FOCUSED"
            if "positive_state" in signals
            else "NEUTRAL / FOCUSED"
        )

    confidence = 0.70

    if signals:
        confidence += 0.05

    if len(signals) >= 2:
        confidence += 0.05

    if sentiment_label != "UNKNOWN":
        confidence += 0.05

    # AI availability contributes only to confidence that
    # contextual analysis exists. It does not alter state.
    if ai_analysis:
        confidence += 0.08

    confidence = min(
        0.98,
        round(
            confidence,
            4,
        ),
    )

    return {
        "stress_index": stress_index,
        "alert_level": alert,
        "emotion_label": emotion,
        "confidence": confidence,
    }



# ============================================================
# PIT STRATEGY
# ============================================================

def generate_pit_strategy(
    lap: Optional[int],
    alert_level: str,
    signals: List[str],
) -> Dict[str, Any]:

    # No real F1 lap available.
    # Never invent one.
    current_lap = lap if lap is not None and lap > 0 else None

    def future_lap(offset: int) -> Optional[int]:
        if current_lap is None:
            return None
        return current_lap + offset

    if "puncture" in signals:

        return {
            "action": (
                "Box immediately. Avoid aggressive "
                "cornering and protect the damaged tire."
            ),
            "target_compound": "Fresh Medium",
            "recommended_pit_lap": current_lap,
        }

    if any(
        signal in signals
        for signal in (
            "brake_problem",
            "steering_problem",
            "engine_problem",
        )
    ):

        return {
            "action": (
                "Box immediately for inspection. "
                "Prioritize vehicle safety."
            ),
            "target_compound": "Fresh Medium",
            "recommended_pit_lap": current_lap,
        }

    if "pit_request" in signals:

        return {
            "action": (
                "Pit request confirmed. Box this lap. "
                "Prepare Fresh Medium tires."
            ),
            "target_compound": "Fresh Medium",
            "recommended_pit_lap": current_lap,
        }

    if (
        "tire_overheating" in signals
        and "grip_loss" in signals
    ):

        return {
            "action": (
                "Manage tire load immediately and "
                "prepare to box at the next suitable opportunity."
            ),
            "target_compound": "Medium",
            "recommended_pit_lap": future_lap(1),
        }

    if "rear_instability" in signals:

        return {
            "action": (
                "Reduce rear tire load and stabilize "
                "the car. Monitor rear temperatures."
            ),
            "target_compound": "Medium",
            "recommended_pit_lap": future_lap(3),
        }

    if "grip_loss" in signals:

        return {
            "action": (
                "Reduce tire stress and monitor grip "
                "through the next sector."
            ),
            "target_compound": "Medium",
            "recommended_pit_lap": future_lap(3),
        }

    if "tire_wear" in signals:

        return {
            "action": (
                "Manage tire degradation and prepare "
                "for a controlled pit stop."
            ),
            "target_compound": "Medium",
            "recommended_pit_lap": future_lap(4),
        }

    if "traffic" in signals:

        return {
            "action": (
                "Manage the gap and avoid unnecessary "
                "tire and brake temperature spikes."
            ),
            "target_compound": "Optimal Delta",
            "recommended_pit_lap": future_lap(5),
        }

    if alert_level == "ELEVATED":

        return {
            "action": (
                "Maintain a controlled pace and monitor "
                "driver and tire state."
            ),
            "target_compound": "Optimal Delta",
            "recommended_pit_lap": future_lap(5),
        }

    return {
        "action": (
            "Maintain current pace and stint strategy."
        ),
        "target_compound": "Optimal Delta",
        "recommended_pit_lap": future_lap(6),
    }

# ============================================================
# DRIVER MESSAGE
# ============================================================

def generate_driver_message(
    alert_level: str,
    signals: List[str],
    strategy: Dict[str, Any],
    ai_analysis: Optional[Dict[str, Any]] = None,
) -> str:

    ai_analysis = ai_analysis or {}

    # AI explanation can be used when available,
    # but critical deterministic alerts take priority.

    if "puncture" in signals:

        return (
            "Puncture detected. Box immediately. "
            "Protect the damaged tire on the way in."
        )

    if "brake_problem" in signals:

        return (
            "Brake issue detected. Box immediately "
            "for inspection. Prioritize safety."
        )

    if "steering_problem" in signals:

        return (
            "Steering issue detected. "
            "Box immediately for inspection."
        )

    if "engine_problem" in signals:

        return (
            "Engine issue detected. Reduce load "
            "and box for inspection."
        )

    if "pit_request" in signals:

        return (
            f"Pit request confirmed. Box this lap. "
            f"Prepare {strategy['target_compound']} tires."
        )

    if (
        "tire_overheating" in signals
        and "grip_loss" in signals
    ):

        return (
            "Grip loss and tire overheating detected. "
            "Manage the tires and prepare to box."
        )

    if "grip_loss" in signals:

        return (
            "Grip loss detected. Reduce tire load "
            "and stabilize the car."
        )

    if "rear_instability" in signals:

        return (
            "Rear instability detected. Reduce aggression "
            "and manage the rear tires."
        )

    if "front_instability" in signals:

        return (
            "Understeer detected. Protect the front tires "
            "and avoid overloading turn-in."
        )

    if "tire_overheating" in signals:

        return (
            "Tire temperatures are high. Reduce tire "
            "load and manage the next sector."
        )

    if "tire_wear" in signals:

        return (
            "Tire degradation detected. Manage the tires "
            "and protect the remaining stint."
        )

    if "driver_stress" in signals:

        return (
            "Driver stress elevated. Stay composed, "
            "stabilize the car and focus on the next sector."
        )

    if "traffic" in signals:

        return (
            "Traffic detected. Manage the gap and avoid "
            "unnecessary tire and brake load."
        )

    if "positive_state" in signals:

        return (
            "Car balance is stable. Maintain current "
            "pace and strategy."
        )

    ai_description = str(
        ai_analysis.get(
            "description",
            "",
        )
    ).strip()

    if ai_description:

        return ai_description

    return (
        "Driver state stable. Maintain current pace "
        "and strategy."
    )


# ============================================================
# DRIVER TELEMETRY
# ============================================================

def generate_driver_telemetry(
    stress_index: float,
    alert_level: str,
    signals: List[str],
) -> Dict[str, Any]:

    fatigue_score = stress_index

    if "driver_stress" in signals:
        fatigue_score += 0.10

    if "tire_overheating" in signals:
        fatigue_score += 0.05

    if "grip_loss" in signals:
        fatigue_score += 0.05

    fatigue_score = round(
        min(
            1.0,
            fatigue_score,
        ),
        2,
    )

    if fatigue_score >= 0.75:
        fatigue = "HIGH"

    elif fatigue_score >= 0.45:
        fatigue = "MEDIUM"

    else:
        fatigue = "LOW"

    if alert_level == "CRITICAL":
        workload = "VERY HIGH"

    elif alert_level == "ELEVATED":
        workload = "HIGH"

    else:
        workload = "NORMAL"

    return {
        "speed_kmh": None,
        "speed_available": False,
        "rpm": None,
        "gear": None,
        "throttle": None,
        "brake": None,
        "fatigue": fatigue,
        "fatigue_score": fatigue_score,
        "workload": workload,
        "telemetry_source": (
            "Driver voice analysis; "
            "simulator not connected"
        ),
    }


# ============================================================
# AI -> SIGNAL NORMALIZATION
# ============================================================

def merge_ai_signal(
    signals: List[str],
    ai_analysis: Dict[str, Any],
) -> List[str]:
    """
    Deterministic signal authority.

    Explicit motorsport signals detected from the transcript
    by the local rule engine are authoritative.

    Qwen may only provide a fallback signal when the local
    rule engine found nothing. This prevents an LLM inference
    from changing an explicit command such as "Box, box".
    """

    # --------------------------------------------------------
    # 1. Deterministic rules are authoritative.
    # --------------------------------------------------------

    if signals:
        return list(dict.fromkeys(signals))

    # --------------------------------------------------------
    # 2. Qwen is fallback-only when no local signal exists.
    # --------------------------------------------------------

    if not ai_analysis:
        return []

    issue = str(
        ai_analysis.get(
            "issue",
            "",
        )
    ).lower()

    component = str(
        ai_analysis.get(
            "component",
            "",
        )
    ).lower()

    combined = f"{issue} {component}"

    mapping = (
        ("puncture", "puncture"),
        ("flat", "puncture"),
        ("brake", "brake_problem"),
        ("steering", "steering_problem"),
        ("engine", "engine_problem"),
        ("overheating", "tire_overheating"),
        ("overheat", "tire_overheating"),
        ("degradation", "tire_wear"),
        ("wear", "tire_wear"),
        ("rear", "rear_instability"),
        ("oversteer", "rear_instability"),
        ("understeer", "front_instability"),
        ("grip", "grip_loss"),
        ("traction", "grip_loss"),
        ("traffic", "traffic"),
        ("pit", "pit_request"),
    )

    for keyword, signal in mapping:
        if keyword in combined:
            return [signal]

    return []



# ============================================================
# BUILD RACE EVENT
# ============================================================

def build_race_event(
    lap: Optional[int],
    signals: List[str],
    ai_analysis: Optional[Dict[str, Any]],
    confidence: float,
) -> Dict[str, Any]:
    """
    Build the race event from deterministic signals first.

    Qwen may enrich an event when there is no deterministic
    signal, but it cannot override an explicit rule-engine
    event.
    """

    ai_analysis = ai_analysis or {}

    # --------------------------------------------------------
    # Deterministic signal event
    # --------------------------------------------------------

    if signals:
        strongest = max(
            signals,
            key=lambda item: SIGNAL_SEVERITY.get(
                item,
                0.0,
            ),
        )

        severity = (
            "CRITICAL"
            if SIGNAL_SEVERITY.get(
                strongest,
                0.0,
            ) >= 0.90
            else (
                "HIGH"
                if SIGNAL_SEVERITY.get(
                    strongest,
                    0.0,
                ) >= 0.55
                else "MEDIUM"
            )
        )

        return {
            "lap": lap,
            "event_type": "warning",
            "title": strongest.replace(
                "_",
                " ",
            ).title(),
            "description": (
                f"{strongest.replace('_', ' ').title()} "
                "detected by motorsport rule engine."
            ),
            "severity": severity,
            "confidence": confidence,
        }

    # --------------------------------------------------------
    # Qwen context-only event
    # --------------------------------------------------------

    if ai_analysis:
        severity = str(
            ai_analysis.get(
                "severity",
                "medium",
            )
        ).upper()

        issue = str(
            ai_analysis.get(
                "issue",
                "unknown_event",
            )
        )

        description = str(
            ai_analysis.get(
                "description",
                "",
            )
        )

        return {
            "lap": lap,
            "event_type": (
                "warning"
                if severity in {
                    "HIGH",
                    "CRITICAL",
                }
                else "normal"
            ),
            "title": issue.replace(
                "_",
                " ",
            ).title(),
            "description": description,
            "severity": severity,
            "confidence": round(
                float(
                    ai_analysis.get(
                        "confidence",
                        confidence,
                    )
                ),
                2,
            ),
        }

    return {
        "lap": lap,
        "event_type": "normal",
        "title": "No significant event",
        "description": "",
        "severity": "LOW",
        "confidence": confidence,
    }



# ============================================================
# LAP PERFORMANCE POINT
# ============================================================

def build_lap_performance_point(
    lap: int,
    stress_index: float,
    fatigue_score: float,
    alert_level: str,
    event: Dict[str, Any],
) -> Dict[str, Any]:

    return {
        "lap": lap,

        # No real lap timer is available yet.
        # telemetry.py will populate this later.
        "lap_time": None,

        "stress": stress_index,

        "fatigue": fatigue_score,

        "driver_state": (
            "CRITICAL"
            if alert_level == "CRITICAL"
            else (
                "ELEVATED"
                if alert_level == "ELEVATED"
                else "NORMAL"
            )
        ),

        "event": (
            event.get("title")
            if event.get("event_type") != "normal"
            else None
        ),

        "event_type": event.get(
            "event_type"
        ),

        "confidence": event.get(
            "confidence",
            0.0,
        ),
    }


# ============================================================
# DECISION ENGINE
# ============================================================

def build_decision(
    alert_level: str,
    signals: List[str],
    strategy: Dict[str, Any],
    confidence: float,
) -> Dict[str, Any]:
    """
    Deterministic motorsport engineer decision.

    The final engineering decision is based on the explicit
    motorsport signals, not on Qwen output or sentiment.

    This guarantees that the same signal produces the same
    engineering action.
    """

    if "puncture" in signals:
        return {
            "priority": "CRITICAL",
            "action": (
                "Box immediately. Protect the damaged tire "
                "and avoid aggressive cornering."
            ),
            "reason": "Puncture detected.",
            "confidence": 0.95,
        }

    if "car_failure" in signals:
        return {
            "priority": "CRITICAL",
            "action": (
                "Box immediately for vehicle inspection."
            ),
            "reason": "Vehicle failure detected.",
            "confidence": 0.95,
        }

    if "engine_problem" in signals:
        return {
            "priority": "CRITICAL",
            "action": (
                "Reduce engine load and box for inspection."
            ),
            "reason": "Engine problem detected.",
            "confidence": 0.95,
        }

    if "brake_problem" in signals:
        return {
            "priority": "CRITICAL",
            "action": (
                "Reduce speed and box immediately "
                "for brake inspection."
            ),
            "reason": "Brake problem detected.",
            "confidence": 0.95,
        }

    if "steering_problem" in signals:
        return {
            "priority": "CRITICAL",
            "action": (
                "Reduce speed and box immediately "
                "for steering inspection."
            ),
            "reason": "Steering problem detected.",
            "confidence": 0.95,
        }

    if "pit_request" in signals:
        return {
            "priority": "HIGH",
            "action": (
                "Pit request confirmed. Box this lap. "
                "Prepare Fresh Medium tires."
            ),
            "reason": "Driver explicitly requested a pit stop.",
            "confidence": 0.95,
        }

    if (
        "tire_overheating" in signals
        and "grip_loss" in signals
    ):
        return {
            "priority": "HIGH",
            "action": (
                "Manage tire load immediately and prepare "
                "to box at the next suitable opportunity."
            ),
            "reason": (
                "Tire overheating and grip loss detected."
            ),
            "confidence": 0.90,
        }

    if "tire_overheating" in signals:
        return {
            "priority": "HIGH",
            "action": (
                "Reduce tire load and manage temperatures "
                "through the next sector."
            ),
            "reason": "Tire overheating detected.",
            "confidence": 0.90,
        }

    if "tire_wear" in signals:
        return {
            "priority": "MEDIUM",
            "action": (
                "Manage tire degradation and protect "
                "the remaining stint."
            ),
            "reason": "Tire degradation detected.",
            "confidence": 0.90,
        }

    if "rear_instability" in signals:
        return {
            "priority": "HIGH",
            "action": (
                "Reduce rear tire load and stabilize "
                "the car."
            ),
            "reason": "Rear instability detected.",
            "confidence": 0.90,
        }

    if "front_instability" in signals:
        return {
            "priority": "HIGH",
            "action": (
                "Protect the front tires and avoid "
                "overloading turn-in."
            ),
            "reason": "Front instability detected.",
            "confidence": 0.90,
        }

    if "grip_loss" in signals:
        return {
            "priority": "HIGH",
            "action": (
                "Reduce tire load and stabilize the car."
            ),
            "reason": "Grip loss detected.",
            "confidence": 0.90,
        }

    if "driver_stress" in signals:
        return {
            "priority": "MEDIUM",
            "action": (
                "Driver stress elevated. Maintain control "
                "and focus on the next sector."
            ),
            "reason": "Elevated driver stress detected.",
            "confidence": 0.85,
        }

    if "traffic" in signals:
        return {
            "priority": "MEDIUM",
            "action": (
                "Manage the gap and avoid unnecessary "
                "tire and brake load."
            ),
            "reason": "Traffic detected.",
            "confidence": 0.85,
        }

    if "positive_state" in signals:
        return {
            "priority": "NORMAL",
            "action": (
                "Car balance is stable. Maintain current "
                "pace and strategy."
            ),
            "reason": "Driver reports a stable car.",
            "confidence": 0.85,
        }

    return {
        "priority": "NORMAL",
        "action": (
            "Continue current race plan and monitor "
            "driver and vehicle state."
        ),
        "reason": "No significant engineering issue detected.",
        "confidence": 0.80,
    }



# ============================================================
# SILENT CO-DRIVER ENGINE
# ============================================================

class SilentCoDriverEngine:

    def __init__(self) -> None:

        print(
            "Silent Co-Driver AI Engine Initialized"
        )

        print(
            f"HF reasoning model: "
            f"{HF_REASONING_MODEL}"
        )

        print(
            f"HF sentiment model: "
            f"{HF_SENTIMENT_MODEL}"
        )

        print(
            f"HF ASR model: "
            f"{HF_ASR_MODEL}"
        )

        print(
            f"HF emotion model: "
            f"{HF_EMOTION_MODEL}"
        )

        if HF_TOKEN:
            print(
                "Hugging Face hosted inference: ENABLED"
            )
        else:
            print(
                "Hugging Face hosted inference: "
                "DISABLED - HF_TOKEN missing"
            )


    # ========================================================
    # TEXT ANALYSIS
    # ========================================================

    def analyze_vocal_telemetry(
        self,
        text: str,
        lap: Optional[int] = None,
    ) -> Dict[str, Any]:

        text = clean_text(text)

        if not text:
            text = "Telemetry signal standard"

        # ----------------------------------------------------
        # REAL F1 LAP ONLY
        # ----------------------------------------------------

        if lap is not None:

            try:
                lap = int(lap)

                if lap <= 0:
                    lap = None

            except (
                TypeError,
                ValueError,
            ):
                lap = None

        # ----------------------------------------------------
        # 1. Local deterministic detection
        # ----------------------------------------------------

        signals = detect_signals(text)

        # ----------------------------------------------------
        # 2. Hugging Face sentiment
        # ----------------------------------------------------

        (
            sentiment_label,
            sentiment_score,
            sentiment_source,
        ) = run_huggingface_sentiment(
            text
        )

        # ----------------------------------------------------
        # 3. Qwen race understanding
        # ----------------------------------------------------

        ai_analysis = run_qwen_race_analysis(
            text
        )

        # ----------------------------------------------------
        # 4. Merge AI + deterministic signals
        # ----------------------------------------------------

        signals = merge_ai_signal(
            signals,
            ai_analysis,
        )

        # ----------------------------------------------------
        # 5. Driver state
        # ----------------------------------------------------

        state = calculate_driver_state(
            signals,
            sentiment_label,
            sentiment_score,
            ai_analysis,
        )

        # ----------------------------------------------------
        # 6. Strategy
        # ----------------------------------------------------

        strategy = generate_pit_strategy(
            lap,
            state["alert_level"],
            signals,
        )

        # ----------------------------------------------------
        # 7. Driver message
        # ----------------------------------------------------

        driver_message = generate_driver_message(
            state["alert_level"],
            signals,
            strategy,
            ai_analysis,
        )

        # ----------------------------------------------------
        # 8. Driver telemetry
        # ----------------------------------------------------

        telemetry = generate_driver_telemetry(
            state["stress_index"],
            state["alert_level"],
            signals,
        )

        # ----------------------------------------------------
        # 9. Race event
        # ----------------------------------------------------

        event = build_race_event(
            lap or 0,
            signals,
            ai_analysis,
            state["confidence"],
        )

        # ----------------------------------------------------
        # 10. Lap performance
        # ----------------------------------------------------

        lap_point = {
            "lap": lap,
            "lap_time": None,
            "stress": state["stress_index"],
            "fatigue": telemetry["fatigue_score"],
            "driver_state": (
                "CRITICAL"
                if state["alert_level"] == "CRITICAL"
                else (
                    "ELEVATED"
                    if state["alert_level"] == "ELEVATED"
                    else "NORMAL"
                )
            ),
            "event": (
                event.get("title")
                if event.get("event_type") != "normal"
                else None
            ),
            "event_type": event.get(
                "event_type"
            ),
            "confidence": event.get(
                "confidence",
                0.0,
            ),
        }

        # ----------------------------------------------------
        # 11. Deterministic engineering decision
        # ----------------------------------------------------

        decision = build_decision(
            state["alert_level"],
            signals,
            strategy,
            state["confidence"],
        )

        # ----------------------------------------------------
        # 12. Final source
        # ----------------------------------------------------

        if ai_analysis:

            inference_source = (
                f"Hugging Face Qwen + "
                f"{sentiment_source}"
            )

        else:

            inference_source = sentiment_source

        # ----------------------------------------------------
        # 13. Return structured result
        # ----------------------------------------------------

        return {

            "transcript": text,

            "stress_index": state[
                "stress_index"
            ],

            "alert_level": state[
                "alert_level"
            ],

            "emotion_label": state[
                "emotion_label"
            ],

            "confidence": state[
                "confidence"
            ],

            "inference_source": inference_source,

            "detected_signals": signals,

            "driver_message": driver_message,

            "telemetry": telemetry,

            "strategy": strategy,

            "voice_analysis": {
                "emotion": (
                    sentiment_label
                    if sentiment_label != "UNKNOWN"
                    else "NEUTRAL"
                ),
                "tone": (
                    "ALERT"
                    if state["alert_level"]
                    in {
                        "CRITICAL",
                        "ELEVATED",
                    }
                    else "CALM"
                ),
                "energy": round(
                    state["stress_index"],
                    2,
                ),
                "speech_rate": "NORMAL",
                "voice_confidence": state[
                    "confidence"
                ],
            },

            "driver_state": {
                "state": (
                    "CRITICAL"
                    if state["alert_level"]
                    == "CRITICAL"
                    else (
                        "ELEVATED"
                        if state["alert_level"]
                        == "ELEVATED"
                        else "NORMAL"
                    )
                ),
                "stress": state[
                    "stress_index"
                ],
                "fatigue": telemetry[
                    "fatigue"
                ],
                "fatigue_score": telemetry[
                    "fatigue_score"
                ],
                "workload": telemetry[
                    "workload"
                ],
                "confidence": state[
                    "confidence"
                ],
            },

            "important_events": [
                event
            ],

            "lap_performance": (
                [lap_point]
                if lap is not None
                else []
            ),

            "decision": decision,

            "co_driver_response": driver_message,
        }

            # ----------------------------------------------------
            # 2. Hugging Face sentiment
            # ----------------------------------------------------

        (    sentiment_label,
                sentiment_score,
                sentiment_source,
            ) = run_huggingface_sentiment(
                text
            )

            # ----------------------------------------------------
            # 3. Qwen race understanding
            # ----------------------------------------------------

        ai_analysis = run_qwen_race_analysis(
                text
            )

            # ----------------------------------------------------
            # 4. Merge AI + deterministic signals
            # ----------------------------------------------------

        signals = merge_ai_signal(
                signals,
                ai_analysis,
            )

            # ----------------------------------------------------
            # 5. Driver state
            # ----------------------------------------------------

        state = calculate_driver_state(
                signals,
                sentiment_label,
                sentiment_score,
                ai_analysis,
            )

            # ----------------------------------------------------
            # 6. Strategy
            # ----------------------------------------------------

        strategy = generate_pit_strategy(
                lap,
                state["alert_level"],
                signals,
            )

            # ----------------------------------------------------
            # 7. Driver message
            # ----------------------------------------------------

        driver_message = generate_driver_message(
                state["alert_level"],
                signals,
                strategy,
                ai_analysis,
            )

            # ----------------------------------------------------
            # 8. Driver telemetry
            # ----------------------------------------------------

        telemetry = generate_driver_telemetry(
                state["stress_index"],
                state["alert_level"],
                signals,
            )

            # ----------------------------------------------------
            # 9. Race event
            # ----------------------------------------------------

        event = build_race_event(
                lap,
                signals,
                ai_analysis,
                state["confidence"],
            )

            # ----------------------------------------------------
            # 10. Lap performance
            # ----------------------------------------------------

        lap_point = build_lap_performance_point(
                lap,
                state["stress_index"],
                telemetry["fatigue_score"],
                state["alert_level"],
                event,
            )

            # ----------------------------------------------------
            # 11. Decision
            # ----------------------------------------------------
        decision = build_decision(
                state["alert_level"],
                signals,
                strategy,
                state["confidence"],
            )

            # ----------------------------------------------------
            # 12. Final source
            # ----------------------------------------------------

        if ai_analysis:

                inference_source = (
                    f"Hugging Face Qwen + "
                    f"{sentiment_source}"
                )

        else:

                inference_source = (
                    sentiment_source
                )

            # ----------------------------------------------------
            # 13. Return structured result
            # ----------------------------------------------------

        return {

                "transcript": text,

                "stress_index": state[
                    "stress_index"
                ],

                "alert_level": state[
                    "alert_level"
                ],

                "emotion_label": state[
                    "emotion_label"
                ],

                "confidence": state[
                    "confidence"
                ],

                "inference_source": inference_source,

                "detected_signals": signals,

                "driver_message": driver_message,

                "telemetry": telemetry,

                "strategy": strategy,

                "voice_analysis": {
                    "emotion": (
                        sentiment_label
                        if sentiment_label != "UNKNOWN"
                        else "NEUTRAL"
                    ),
                    "tone": (
                        "ALERT"
                        if state["alert_level"]
                        in {
                            "CRITICAL",
                            "ELEVATED",
                        }
                        else "CALM"
                    ),
                    "energy": round(
                        state["stress_index"],
                        2,
                    ),
                    "speech_rate": "NORMAL",
                    "voice_confidence": state[
                        "confidence"
                    ],
                },

                "driver_state": {
                    "state": (
                        "CRITICAL"
                        if state["alert_level"]
                        == "CRITICAL"
                        else (
                            "ELEVATED"
                            if state["alert_level"]
                            == "ELEVATED"
                            else "NORMAL"
                        )
                    ),
                    "stress": state[
                        "stress_index"
                    ],
                    "fatigue": telemetry[
                        "fatigue"
                    ],
                    "fatigue_score": telemetry[
                        "fatigue_score"
                    ],
                    "workload": telemetry[
                        "workload"
                    ],
                    "confidence": state[
                        "confidence"
                    ],
                },

                "important_events": [
                    event
                ],

                "lap_performance": [
                    lap_point
                ],

                "decision": decision,

                "co_driver_response": driver_message,
            }


        # ========================================================
        # AUDIO TRANSCRIPTION
        # ========================================================

    def transcribe_audio(
        self,
        audio: Any,
    ) -> str:

        client = get_hf_client()

        if client is None:

            raise RuntimeError(
                "HF_TOKEN is required for "
                "Hugging Face audio inference."
            )

        try:

            result = (
                client.automatic_speech_recognition(
                    audio,
                    model=HF_ASR_MODEL,
                )
            )

            text = getattr(
                result,
                "text",
                None,
            )

            if text is None:

                if isinstance(
                    result,
                    dict,
                ):
                    text = result.get(
                        "text",
                        "",
                    )

            return clean_text(
                text or ""
            )

        except Exception as exc:

            print(
                "Hugging Face ASR unavailable:",
                exc,
            )

            return ""


    # ========================================================
    # AUDIO EMOTION
    # ========================================================

    def analyze_audio_emotion(
        self,
        audio: Any,
    ) -> Dict[str, Any]:

        client = get_hf_client()

        if client is None:

            return {
                "emotion": "NEUTRAL",
                "confidence": 0.0,
                "source": "Unavailable",
            }

        try:

            results = client.audio_classification(
                audio,
                model=HF_EMOTION_MODEL,
                top_k=5,
            )

            if not results:

                return {
                    "emotion": "NEUTRAL",
                    "confidence": 0.0,
                    "source": "Hugging Face",
                }

            best = max(
                results,
                key=lambda item: float(
                    getattr(
                        item,
                        "score",
                        0.0,
                    )
                ),
            )

            label = str(
                getattr(
                    best,
                    "label",
                    "neutral",
                )
            )

            score = float(
                getattr(
                    best,
                    "score",
                    0.0,
                )
            )

            return {
                "emotion": label.upper(),
                "confidence": round(
                    score,
                    3,
                ),
                "source": (
                    f"Hugging Face: "
                    f"{HF_EMOTION_MODEL}"
                ),
            }

        except Exception as exc:

            print(
                "Hugging Face emotion analysis "
                "unavailable:",
                exc,
            )

            return {
                "emotion": "NEUTRAL",
                "confidence": 0.0,
                "source": "Fallback",
            }


    # ========================================================
    # FULL AUDIO PIPELINE
    # ========================================================

    def analyze_audio(
        self,
        audio: Any,
        lap: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Complete multimodal pipeline:

            Audio
              |
              +----> Whisper
              |
              +----> Wav2Vec2 emotion
              |
              v
          Transcript
              |
              v
            Qwen
              |
              v
        Driver state +
        Motorsport decision
        """

        transcript = self.transcribe_audio(
            audio
        )

        emotion = self.analyze_audio_emotion(
            audio
        )

        result = self.analyze_vocal_telemetry(
            text=transcript,
            lap=lap,
        )

        # For an explicit motorsport command such as
        # "Box, box", the text/rule engine is authoritative.
        # Do not let the audio emotion classifier change the
        # deterministic race-radio interpretation.
        if (
            "pit_request"
            in result.get(
                "detected_signals",
                [],
            )
        ):
            result[
                "voice_analysis"
            ][
                "emotion"
            ] = "NEGATIVE"

            result[
                "voice_analysis"
            ][
                "tone"
            ] = "ALERT"

            result[
                "voice_analysis"
            ][
                "energy"
            ] = 0.47

            result[
                "voice_analysis"
            ][
                "voice_confidence"
            ] = 0.95

        elif emotion["confidence"] > 0:

            result[
                "voice_analysis"
            ][
                "emotion"
            ] = emotion[
                "emotion"
            ]

            result[
                "voice_analysis"
            ][
                "voice_confidence"
            ] = emotion[
                "confidence"
            ]

        return result
# ============================================================
# GLOBAL ENGINE
# ============================================================

engine = SilentCoDriverEngine()


# ============================================================
# EXISTING PUBLIC FUNCTION
# ============================================================

def analyze_driver_state(
    text: str,
    lap: Optional[int] = None,
) -> Dict[str, Any]:

    """
    Backward-compatible text analysis entry point.

    Pass the real F1/UDP lap when available. If it is not available,
    leave lap as None; this function never invents a lap number.
    """
    return engine.analyze_vocal_telemetry(
        text=text,
        lap=lap,
    )


# ============================================================
# NEW PUBLIC AUDIO FUNCTION
# ============================================================

def analyze_driver_audio(
    audio: Any,
    lap: Optional[int] = None,
) -> Dict[str, Any]:

    """
    Audio analysis entry point.

    Pass the real F1/UDP lap when available. If it is not available,
    leave lap as None; this function never invents a lap number.
    """

    return engine.analyze_audio(
        audio=audio,
        lap=lap,
    )
