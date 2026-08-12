import os
import re
import requests
from typing import Any, Dict, List, Optional


# ============================================================
# Hugging Face sentiment model
# ============================================================

HF_API_URL = (
    "https://api-inference.huggingface.co/models/"
    "distilbert/distilbert-base-uncased-finetuned-sst-2-english"
)


# ============================================================
# Motorsport language patterns
# ============================================================

SIGNAL_PATTERNS = {
    "grip_loss": [
        r"\blost grip\b",
        r"\blosing grip\b",
        r"\bno grip\b",
        r"\bgrip is gone\b",
        r"\bgrip has gone\b",
        r"\bsliding\b",
        r"\bslide\b",
        r"\bslip(ping)?\b",
        r"\bstepping out\b",
        r"\bthe rear is moving\b",
        r"\brear is gone\b",
        r"\bfront is gone\b",
        r"\bfront end is gone\b",
        r"\bundersteer\b",
        r"\boversteer\b",
        r"\bcar is rotating\b",
        r"\bcar keeps moving\b",
        r"\bcan't put the power down\b",
        r"\bno traction\b",
        r"\blosing traction\b",
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
    ],

    "front_instability": [
        r"\bundersteer\b",
        r"\bfront is washing out\b",
        r"\bfront end is washing\b",
        r"\bfront doesn't turn\b",
        r"\bfront won't turn\b",
        r"\bcan't turn in\b",
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
        r"\bfalling away\b",
    ],

    "puncture": [
        r"\bpuncture\b",
        r"\bpunctured\b",
        r"\bflat tyre\b",
        r"\bflat tire\b",
        r"\bflat\b.*\btyre\b",
        r"\bflat\b.*\btire\b",
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
        r"\bbrake pedal\b.*\bsoft\b",
        r"\bbraking problem\b",
        r"\bcan't brake\b",
    ],

    "steering_problem": [
        r"\bsteering problem\b",
        r"\bsteering is heavy\b",
        r"\bsteering feels heavy\b",
        r"\bsteering feels wrong\b",
        r"\bsteering issue\b",
        r"\bsteering failure\b",
        r"\bwheel feels wrong\b",
        r"\bwheel is heavy\b",
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
        r"\bengine is weak\b",
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
        r"\bthis is bad\b",
        r"\bthis feels bad\b",
        r"\bwhat is happening\b",
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
# Severity weights
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
# Utility functions
# ============================================================

def clean_text(text: str) -> str:
    """
    Normalize arbitrary driver input.
    """
    if not text:
        return ""

    text = str(text).strip()

    # Collapse repeated whitespace
    text = re.sub(r"\s+", " ", text)

    return text


def detect_signals(text: str) -> List[str]:
    """
    Detect motorsport signals from natural driver language.
    """

    text_lower = text.lower()

    detected = []

    for signal, patterns in SIGNAL_PATTERNS.items():

        for pattern in patterns:

            if re.search(pattern, text_lower):
                detected.append(signal)
                break

    return detected


def has_signal(signals: List[str], name: str) -> bool:
    return name in signals


def calculate_signal_severity(signals: List[str]) -> float:
    """
    Calculates the strongest detected condition.
    """

    if not signals:
        return 0.0

    severity_values = [
        SIGNAL_SEVERITY.get(signal, 0.0)
        for signal in signals
    ]

    strongest = max(severity_values)

    # Multiple simultaneous issues increase urgency.
    additional = max(0, len(signals) - 1) * 0.05

    return min(1.0, strongest + additional)


# ============================================================
# Hugging Face sentiment
# ============================================================

def run_huggingface_sentiment(
    text: str,
) -> tuple[str, float, str]:

    """
    Attempts Hugging Face sentiment inference.

    If unavailable, the local motorsport rule engine
    continues working.
    """

    hf_token = os.getenv("HF_TOKEN")

    headers: Dict[str, str] = {}

    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"

    payload = {
        "inputs": text
    }

    try:

        response = requests.post(
            HF_API_URL,
            json=payload,
            headers=headers,
            timeout=4,
        )

        if response.status_code != 200:
            return (
                "UNKNOWN",
                0.50,
                "Motorsport Rule Engine",
            )

        data = response.json()

        if not isinstance(data, list) or not data:
            return (
                "UNKNOWN",
                0.50,
                "Motorsport Rule Engine",
            )

        result = data[0]

        if isinstance(result, list):
            result = result[0]

        label = str(
            result.get("label", "UNKNOWN")
        ).upper()

        score = float(
            result.get("score", 0.50)
        )

        return (
            label,
            score,
            "Hugging Face DistilBERT + Motorsport Rules",
        )

    except Exception as exc:

        print(
            f"Hugging Face inference unavailable: {exc}"
        )

        return (
            "UNKNOWN",
            0.50,
            "Motorsport Rule Engine",
        )


# ============================================================
# Driver state
# ============================================================

def calculate_driver_state(
    text: str,
    signals: List[str],
    sentiment_label: str,
    sentiment_score: float,
) -> Dict[str, Any]:

    signal_severity = calculate_signal_severity(signals)

    negative_sentiment = (
        sentiment_label == "NEGATIVE"
    )

    positive_sentiment = (
        sentiment_label == "POSITIVE"
    )

    # --------------------------------------------------------
    # Base stress
    # --------------------------------------------------------

    stress = 0.15

    # Motorsport signals
    stress += signal_severity * 0.60

    # Sentiment
    if negative_sentiment:
        stress += sentiment_score * 0.20

    elif positive_sentiment:
        stress -= sentiment_score * 0.08

    # Explicit positive phrases
    if has_signal(signals, "positive_state"):
        stress -= 0.15

    stress_index = round(
        max(0.0, min(1.0, stress)),
        2,
    )

    # --------------------------------------------------------
    # Alert
    # --------------------------------------------------------

    critical_signals = {
        "puncture",
        "car_failure",
        "engine_problem",
        "brake_problem",
        "steering_problem",
    }

    if any(
        signal in critical_signals
        for signal in signals
    ):
        alert_level = "CRITICAL"

    elif (
        stress_index >= 0.75
        or has_signal(signals, "grip_loss")
        or has_signal(signals, "rear_instability")
        or has_signal(signals, "tire_overheating")
    ):
        alert_level = "CRITICAL"

    elif (
        stress_index >= 0.45
        or signals
    ):
        alert_level = "ELEVATED"

    else:
        alert_level = "NORMAL"

    # --------------------------------------------------------
    # Emotion
    # --------------------------------------------------------

    if alert_level == "CRITICAL":

        if has_signal(signals, "driver_stress"):
            emotion = "HIGH STRESS / ANXIETY"

        else:
            emotion = "HIGH ALERT"

    elif alert_level == "ELEVATED":

        if has_signal(signals, "driver_stress"):
            emotion = "MODERATE STRESS"

        else:
            emotion = "DRIVER UNDER LOAD"

    else:

        if has_signal(signals, "positive_state"):
            emotion = "CALM / FOCUSED"

        else:
            emotion = "NEUTRAL / FOCUSED"

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    confidence = 0.70

    if signals:
        confidence += 0.05

    if len(signals) >= 2:
        confidence += 0.05

    if sentiment_label != "UNKNOWN":
        confidence += 0.05

    confidence = min(
        0.98,
        confidence,
    )

    return {
        "stress_index": stress_index,
        "alert_level": alert_level,
        "emotion_label": emotion,
        "confidence": round(confidence, 4),
    }


# ============================================================
# Pit strategy
# ============================================================

def generate_pit_strategy(
    lap: int,
    alert_level: str,
    signals: List[str],
) -> Dict[str, Any]:

    # --------------------------------------------------------
    # Puncture / immediate mechanical issue
    # --------------------------------------------------------

    if has_signal(signals, "puncture"):

        return {
            "action": (
                "Box immediately. Avoid aggressive "
                "cornering and protect the damaged tire."
            ),
            "target_compound": "Fresh Medium",
            "recommended_pit_lap": lap,
        }

    # --------------------------------------------------------
    # Brake / steering / engine failure
    # --------------------------------------------------------

    if (
        has_signal(signals, "brake_problem")
        or has_signal(signals, "steering_problem")
        or has_signal(signals, "engine_problem")
    ):

        return {
            "action": (
                "Box immediately for inspection. "
                "Prioritize vehicle safety."
            ),
            "target_compound": "Fresh Medium",
            "recommended_pit_lap": lap,
        }

    # --------------------------------------------------------
    # Explicit pit request
    # --------------------------------------------------------

    if has_signal(signals, "pit_request"):

        if (
            has_signal(signals, "tire_overheating")
            or has_signal(signals, "tire_wear")
            or has_signal(signals, "grip_loss")
        ):

            return {
                "action": (
                    "Box this lap. Prepare fresh tires "
                    "and manage the entry safely."
                ),
                "target_compound": "Fresh Medium",
                "recommended_pit_lap": lap,
            }

        return {
            "action": (
                "Pit request confirmed. Prepare pit entry "
                "and evaluate tire selection."
            ),
            "target_compound": "Fresh Medium",
            "recommended_pit_lap": lap,
        }

    # --------------------------------------------------------
    # Tire overheating + grip
    # --------------------------------------------------------

    if (
        has_signal(signals, "tire_overheating")
        and has_signal(signals, "grip_loss")
    ):

        return {
            "action": (
                "Manage tire load immediately and prepare "
                "to box at the next suitable opportunity."
            ),
            "target_compound": "Medium",
            "recommended_pit_lap": lap + 1,
        }

    # --------------------------------------------------------
    # Rear instability
    # --------------------------------------------------------

    if has_signal(signals, "rear_instability"):

        return {
            "action": (
                "Reduce rear tire load and stabilize the car. "
                "Monitor rear temperatures."
            ),
            "target_compound": "Medium",
            "recommended_pit_lap": lap + 3,
        }

    # --------------------------------------------------------
    # General grip loss
    # --------------------------------------------------------

    if has_signal(signals, "grip_loss"):

        return {
            "action": (
                "Reduce tire stress and monitor grip through "
                "the next sector."
            ),
            "target_compound": "Medium",
            "recommended_pit_lap": lap + 3,
        }

    # --------------------------------------------------------
    # Tire wear
    # --------------------------------------------------------

    if has_signal(signals, "tire_wear"):

        return {
            "action": (
                "Manage tire degradation and prepare for "
                "a controlled pit stop."
            ),
            "target_compound": "Medium",
            "recommended_pit_lap": lap + 4,
        }

    # --------------------------------------------------------
    # Traffic
    # --------------------------------------------------------

    if has_signal(signals, "traffic"):

        return {
            "action": (
                "Manage the gap and avoid unnecessary tire "
                "and brake temperature spikes."
            ),
            "target_compound": "Optimal Delta",
            "recommended_pit_lap": lap + 5,
        }

    # --------------------------------------------------------
    # Elevated driver state
    # --------------------------------------------------------

    if alert_level == "ELEVATED":

        return {
            "action": (
                "Maintain a controlled pace and monitor "
                "driver and tire state."
            ),
            "target_compound": "Optimal Delta",
            "recommended_pit_lap": lap + 5,
        }

    # --------------------------------------------------------
    # Normal
    # --------------------------------------------------------

    return {
        "action": (
            "Maintain current pace and stint strategy."
        ),
        "target_compound": "Optimal Delta",
        "recommended_pit_lap": lap + 6,
    }


# ============================================================
# Co-Driver radio response
# ============================================================

def generate_driver_message(
    alert_level: str,
    signals: List[str],
    strategy: Dict[str, Any],
) -> str:

    """
    Produces a short actionable radio response.

    This is deliberately different from the detailed
    dashboard output.
    """

    # --------------------------------------------------------
    # Immediate danger
    # --------------------------------------------------------

    if has_signal(signals, "puncture"):

        return (
            "Puncture detected. Box immediately. "
            "Protect the damaged tire on the way in."
        )

    if has_signal(signals, "brake_problem"):

        return (
            "Brake issue detected. Box immediately "
            "for inspection. Prioritize safety."
        )

    if has_signal(signals, "steering_problem"):

        return (
            "Steering issue detected. Box immediately "
            "for inspection."
        )

    if has_signal(signals, "engine_problem"):

        return (
            "Engine issue detected. Reduce load and "
            "box for inspection."
        )

    # --------------------------------------------------------
    # Pit request
    # --------------------------------------------------------

    if has_signal(signals, "pit_request"):

        return (
            "Pit request confirmed. "
            f"{strategy['action']} "
            f"{strategy['target_compound']} tires."
        )

    # --------------------------------------------------------
    # Grip + overheating
    # --------------------------------------------------------

    if (
        has_signal(signals, "grip_loss")
        and has_signal(signals, "tire_overheating")
    ):

        return (
            "Grip loss and tire overheating detected. "
            "Manage the tires and prepare to box."
        )

    # --------------------------------------------------------
    # Grip
    # --------------------------------------------------------

    if has_signal(signals, "grip_loss"):

        return (
            "Grip loss detected. Reduce tire load "
            "and stabilize the car."
        )

    # --------------------------------------------------------
    # Rear instability
    # --------------------------------------------------------

    if has_signal(signals, "rear_instability"):

        return (
            "Rear instability detected. Reduce aggression "
            "and manage the rear tires."
        )

    # --------------------------------------------------------
    # Front instability
    # --------------------------------------------------------

    if has_signal(signals, "front_instability"):

        return (
            "Understeer detected. Protect the front tires "
            "and avoid overloading turn-in."
        )

    # --------------------------------------------------------
    # Tire temperature
    # --------------------------------------------------------

    if has_signal(signals, "tire_overheating"):

        return (
            "Tire temperatures are high. Reduce tire load "
            "and manage the next sector."
        )

    # --------------------------------------------------------
    # Tire wear
    # --------------------------------------------------------

    if has_signal(signals, "tire_wear"):

        return (
            "Tire degradation detected. Manage the tires "
            "and protect the remaining stint."
        )

    # --------------------------------------------------------
    # Driver stress
    # --------------------------------------------------------

    if has_signal(signals, "driver_stress"):

        return (
            "Driver stress elevated. Stay composed, "
            "stabilize the car and focus on the next sector."
        )

    # --------------------------------------------------------
    # Traffic
    # --------------------------------------------------------

    if has_signal(signals, "traffic"):

        return (
            "Traffic detected. Manage the gap and "
            "avoid unnecessary tire and brake load."
        )

    # --------------------------------------------------------
    # Positive
    # --------------------------------------------------------

    if has_signal(signals, "positive_state"):

        return (
            "Car balance is stable. Maintain current "
            "pace and strategy."
        )

    # --------------------------------------------------------
    # Default
    # --------------------------------------------------------

    if alert_level == "NORMAL":

        return (
            "Driver state stable. Maintain current pace "
            "and strategy."
        )

    return (
        "Driver state elevated. Stay composed and "
        "monitor the next sector."
    )


# ============================================================
# Gauge / driver telemetry
# ============================================================

def generate_driver_telemetry(
    stress_index: float,
    alert_level: str,
    signals: List[str],
) -> Dict[str, Any]:

    """
    Generates telemetry values that are actually supported
    by the current input.

    Speed and EAR are NOT fabricated.

    Fatigue is an estimate derived from driver-state signals.
    """

    # --------------------------------------------------------
    # Fatigue estimate
    # --------------------------------------------------------

    fatigue_score = stress_index

    if has_signal(signals, "driver_stress"):
        fatigue_score += 0.10

    if has_signal(signals, "tire_overheating"):
        fatigue_score += 0.05

    if has_signal(signals, "grip_loss"):
        fatigue_score += 0.05

    fatigue_score = min(
        1.0,
        round(fatigue_score, 2),
    )

    if fatigue_score >= 0.75:
        fatigue = "HIGH"

    elif fatigue_score >= 0.45:
        fatigue = "MEDIUM"

    else:
        fatigue = "LOW"

    # --------------------------------------------------------
    # Driver workload
    # --------------------------------------------------------

    if alert_level == "CRITICAL":
        workload = "VERY HIGH"

    elif alert_level == "ELEVATED":
        workload = "HIGH"

    else:
        workload = "NORMAL"

    # --------------------------------------------------------
    # Actual vehicle telemetry is unavailable
    # --------------------------------------------------------

    return {
        "speed_kmh": None,
        "speed_available": False,

        "ear": None,
        "ear_available": False,

        "fatigue": fatigue,
        "fatigue_score": fatigue_score,

        "workload": workload,

        "telemetry_source": (
            "Voice-derived driver state. "
            "Vehicle speed and camera EAR unavailable."
        ),
    }


# ============================================================
# Main engine
# ============================================================

class SilentCoDriverEngine:

    def __init__(self):

        print(
            "⚡ Silent Co-Driver Dynamic Inference Engine Initialized"
        )

    def analyze_vocal_telemetry(
        self,
        text: str,
        lap: int = 18,
    ) -> Dict[str, Any]:

        # ----------------------------------------------------
        # Normalize input
        # ----------------------------------------------------

        text = clean_text(text)

        if not text:
            text = "Telemetry signal standard"

        try:
            lap = int(lap)
        except (TypeError, ValueError):
            lap = 18

        lap = max(1, lap)

        # ----------------------------------------------------
        # Detect racing language
        # ----------------------------------------------------

        signals = detect_signals(text)

        # ----------------------------------------------------
        # Sentiment
        # ----------------------------------------------------

        sentiment_label, sentiment_score, inference_source = (
            run_huggingface_sentiment(text)
        )

        # ----------------------------------------------------
        # Driver state
        # ----------------------------------------------------

        state = calculate_driver_state(
            text=text,
            signals=signals,
            sentiment_label=sentiment_label,
            sentiment_score=sentiment_score,
        )

        stress_index = state["stress_index"]
        alert_level = state["alert_level"]
        emotion = state["emotion_label"]
        confidence = state["confidence"]

        # ----------------------------------------------------
        # Pit strategy
        # ----------------------------------------------------

        strategy = generate_pit_strategy(
            lap=lap,
            alert_level=alert_level,
            signals=signals,
        )

        # ----------------------------------------------------
        # Driver radio response
        # ----------------------------------------------------

        driver_message = generate_driver_message(
            alert_level=alert_level,
            signals=signals,
            strategy=strategy,
        )

        # ----------------------------------------------------
        # Dashboard gauges
        # ----------------------------------------------------

        telemetry = generate_driver_telemetry(
            stress_index=stress_index,
            alert_level=alert_level,
            signals=signals,
        )

        # ----------------------------------------------------
        # Return complete analysis
        # ----------------------------------------------------

        return {
            "transcript": text,

            "stress_index": stress_index,

            "alert_level": alert_level,

            "emotion_label": emotion,

            "confidence": confidence,

            "inference_source": inference_source,

            "detected_signals": signals,

            "driver_message": driver_message,

            "telemetry": telemetry,

            "strategy": strategy,
        }


# ============================================================
# Global engine
# ============================================================

engine = SilentCoDriverEngine()


def analyze_driver_state(
    text: str,
    lap: int = 18,
) -> Dict[str, Any]:

    return engine.analyze_vocal_telemetry(
        text=text,
        lap=lap,
    )
