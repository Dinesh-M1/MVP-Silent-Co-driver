import json
import os
import re
from typing import Any

import requests


HF_API_URL = "https://router.huggingface.co/v1/chat/completions"


class SilentCoDriverEngine:
    def __init__(self):
        print("⚡ Silent Co-Driver Motorsport LLM Engine Initialized")

        self.hf_token = os.getenv("HF_TOKEN")
        self.llm_model = os.getenv(
            "HF_LLM_MODEL",
            "Qwen/Qwen2.5-7B-Instruct",
        )

    # ============================================================
    # BASIC HELPERS
    # ============================================================

    def _contains(self, text: str, patterns: list[str]) -> bool:
        text_lower = text.lower()

        for pattern in patterns:
            if re.search(
                rf"\b{re.escape(pattern.lower())}\b",
                text_lower,
            ):
                return True

        return False

    # ============================================================
    # LOCAL MOTORSPORT SIGNAL DETECTION
    # FALLBACK / VALIDATION LAYER
    # ============================================================

    def _analyse_signals(self, text: str) -> dict:
        text_lower = text.lower().strip()

        signals = {
            "grip_loss": False,
            "tire_problem": False,
            "overheating": False,
            "puncture": False,
            "braking_problem": False,
            "steering_problem": False,
            "engine_problem": False,
            "traffic": False,
            "fatigue": False,
            "high_workload": False,
            "sliding": False,
            "vibration": False,

            # New F1-specific signals
            "front_wing_damage": False,
            "rear_wing_damage": False,
            "floor_damage": False,
            "sidepod_damage": False,
            "diffuser_damage": False,
            "downforce_loss": False,
            "understeer": False,
            "oversteer": False,
            "wheel_locking": False,
            "brake_fade": False,
            "power_loss": False,
            "gearbox_problem": False,
            "dirty_air": False,
            "tire_degradation": False,
        }

        # --------------------------------------------------------
        # GRIP
        # --------------------------------------------------------

        grip_patterns = [
            "lost grip",
            "lose grip",
            "losing grip",
            "rear grip",
            "front grip",
            "no grip",
            "low grip",
            "grip is gone",
            "grip is lost",
            "car has no grip",
            "traction is gone",
            "lost traction",
            "traction loss",
        ]

        if self._contains(text_lower, grip_patterns):
            signals["grip_loss"] = True

        # --------------------------------------------------------
        # UNDERSTEER
        # --------------------------------------------------------

        understeer_patterns = [
            "understeer",
            "understeering",
            "car won't turn",
            "car wont turn",
            "front won't turn",
            "front wont turn",
            "front end won't turn",
            "front end wont turn",
            "pushing wide",
            "running wide",
            "front is washing",
            "washing out",
        ]

        if self._contains(text_lower, understeer_patterns):
            signals["understeer"] = True
            signals["grip_loss"] = True

        # --------------------------------------------------------
        # OVERSTEER
        # --------------------------------------------------------

        oversteer_patterns = [
            "oversteer",
            "oversteering",
            "rear is loose",
            "rear end is loose",
            "rear is stepping out",
            "rear stepping out",
            "rear keeps stepping out",
            "car is rotating",
            "car rotates",
        ]

        if self._contains(text_lower, oversteer_patterns):
            signals["oversteer"] = True
            signals["grip_loss"] = True
            signals["sliding"] = True

        # --------------------------------------------------------
        # TIRES
        # --------------------------------------------------------

        tire_patterns = [
            "tire",
            "tires",
            "tyre",
            "tyres",
            "tire degradation",
            "tyre degradation",
            "tire wear",
            "tyre wear",
            "tire damage",
            "tyre damage",
            "tires are gone",
            "tyres are gone",
        ]

        if self._contains(text_lower, tire_patterns):
            signals["tire_problem"] = True

        # --------------------------------------------------------
        # TIRE DEGRADATION
        # --------------------------------------------------------

        degradation_patterns = [
            "tire degradation",
            "tyre degradation",
            "tire deg",
            "tyre deg",
            "tires are degrading",
            "tyres are degrading",
            "tires are going off",
            "tyres are going off",
            "tires are worn",
            "tyres are worn",
            "tire wear",
            "tyre wear",
        ]

        if self._contains(text_lower, degradation_patterns):
            signals["tire_degradation"] = True
            signals["tire_problem"] = True

        # --------------------------------------------------------
        # LOST / FAILED TIRE
        # --------------------------------------------------------

        lost_tire_patterns = [
            "lost tire",
            "lost tires",
            "lost a tire",
            "lost my tire",
            "lost rear tire",
            "lost rear tires",
            "lost front tire",
            "lost front tires",
            "rear tire lost",
            "front tire lost",
            "rear tire is gone",
            "rear tires are gone",
            "front tire is gone",
            "front tires are gone",
            "tire has gone",
            "tyre has gone",
        ]

        if self._contains(text_lower, lost_tire_patterns):
            signals["tire_problem"] = True
            signals["puncture"] = True

        # --------------------------------------------------------
        # OVERHEATING
        # --------------------------------------------------------

        overheating_patterns = [
            "overheating",
            "overheat",
            "too hot",
            "running hot",
            "temperature is high",
            "temps are high",
            "tire temperature",
            "tyre temperature",
            "tire temps",
            "tyre temps",
            "tires are hot",
            "tyres are hot",
            "engine temperature",
            "engine is hot",
        ]

        if self._contains(text_lower, overheating_patterns):
            signals["overheating"] = True

        # --------------------------------------------------------
        # PUNCTURE
        # --------------------------------------------------------

        puncture_patterns = [
            "puncture",
            "punctured",
            "flat tire",
            "flat tyre",
            "tire is flat",
            "tyre is flat",
            "tire failure",
            "tyre failure",
            "tire damaged",
            "tyre damaged",
            "wheel damage",
        ]

        if self._contains(text_lower, puncture_patterns):
            signals["puncture"] = True
            signals["tire_problem"] = True

        # --------------------------------------------------------
        # FRONT WING
        # --------------------------------------------------------

        front_wing_patterns = [
            "front wing",
            "front wing damage",
            "front wing damaged",
            "front wing broken",
            "lost front wing",
            "front wing is gone",
            "wing damage",
            "nose damage",
            "front end damage",
        ]

        if self._contains(text_lower, front_wing_patterns):
            signals["front_wing_damage"] = True
            signals["downforce_loss"] = True

        # --------------------------------------------------------
        # REAR WING
        # --------------------------------------------------------

        rear_wing_patterns = [
            "rear wing",
            "rear wing damage",
            "rear wing damaged",
            "rear wing broken",
            "lost rear wing",
            "rear wing is gone",
        ]

        if self._contains(text_lower, rear_wing_patterns):
            signals["rear_wing_damage"] = True
            signals["downforce_loss"] = True

        # --------------------------------------------------------
        # FLOOR
        # --------------------------------------------------------

        floor_patterns = [
            "floor damage",
            "floor is damaged",
            "damaged floor",
            "floor broken",
            "lost the floor",
        ]

        if self._contains(text_lower, floor_patterns):
            signals["floor_damage"] = True
            signals["downforce_loss"] = True

        # --------------------------------------------------------
        # SIDEPOD
        # --------------------------------------------------------

        sidepod_patterns = [
            "sidepod damage",
            "sidepod damaged",
            "sidepod broken",
            "side pod damage",
            "side pod damaged",
        ]

        if self._contains(text_lower, sidepod_patterns):
            signals["sidepod_damage"] = True

        # --------------------------------------------------------
        # DIFFUSER
        # --------------------------------------------------------

        diffuser_patterns = [
            "diffuser damage",
            "diffuser damaged",
            "diffuser broken",
        ]

        if self._contains(text_lower, diffuser_patterns):
            signals["diffuser_damage"] = True
            signals["downforce_loss"] = True

        # --------------------------------------------------------
        # DOWNFORCE
        # --------------------------------------------------------

        downforce_patterns = [
            "lost downforce",
            "downforce loss",
            "no downforce",
            "low downforce",
            "less downforce",
            "downforce is gone",
        ]

        if self._contains(text_lower, downforce_patterns):
            signals["downforce_loss"] = True

        # --------------------------------------------------------
        # BRAKES
        # --------------------------------------------------------

        braking_patterns = [
            "brakes are bad",
            "brakes feel bad",
            "brake problem",
            "braking problem",
            "brake failure",
            "brake pedal",
            "can't brake",
            "cant brake",
            "no brakes",
            "brakes overheating",
            "brake temperature",
        ]

        if self._contains(text_lower, braking_patterns):
            signals["braking_problem"] = True

        # --------------------------------------------------------
        # BRAKE FADE
        # --------------------------------------------------------

        brake_fade_patterns = [
            "brake fade",
            "brakes fading",
            "brakes are fading",
            "brakes feel weak",
            "brakes feel soft",
            "pedal is soft",
            "braking performance is dropping",
        ]

        if self._contains(text_lower, brake_fade_patterns):
            signals["brake_fade"] = True
            signals["braking_problem"] = True

        # --------------------------------------------------------
        # WHEEL LOCKING
        # --------------------------------------------------------

        locking_patterns = [
            "locking up",
            "locked the fronts",
            "locking the fronts",
            "fronts are locking",
            "rear is locking",
            "rear locking",
            "wheel lock",
            "wheel locking",
        ]

        if self._contains(text_lower, locking_patterns):
            signals["wheel_locking"] = True
            signals["braking_problem"] = True

        # --------------------------------------------------------
        # STEERING
        # --------------------------------------------------------

        steering_patterns = [
            "steering problem",
            "steering issue",
            "steering is heavy",
            "steering feels heavy",
            "steering broken",
            "can't steer",
            "cant steer",
            "steering failure",
        ]

        if self._contains(text_lower, steering_patterns):
            signals["steering_problem"] = True

        # --------------------------------------------------------
        # ENGINE / POWER
        # --------------------------------------------------------

        engine_patterns = [
            "engine failure",
            "engine problem",
            "engine issue",
            "engine overheating",
            "engine is overheating",
            "engine smoke",
            "smoke from engine",
            "engine is broken",
        ]

        if self._contains(text_lower, engine_patterns):
            signals["engine_problem"] = True

        power_patterns = [
            "lost power",
            "no power",
            "power loss",
            "losing power",
            "engine losing power",
        ]

        if self._contains(text_lower, power_patterns):
            signals["power_loss"] = True
            signals["engine_problem"] = True

        # --------------------------------------------------------
        # GEARBOX
        # --------------------------------------------------------

        gearbox_patterns = [
            "gearbox",
            "gearbox problem",
            "gearbox issue",
            "gear won't engage",
            "gear wont engage",
            "can't change gear",
            "cant change gear",
            "stuck in gear",
            "gear selection problem",
        ]

        if self._contains(text_lower, gearbox_patterns):
            signals["gearbox_problem"] = True

        # --------------------------------------------------------
        # TRAFFIC / DIRTY AIR
        # --------------------------------------------------------

        traffic_patterns = [
            "traffic",
            "cars ahead",
            "car ahead",
            "cars in front",
            "traffic ahead",
            "stuck behind",
            "blocked",
        ]

        if self._contains(text_lower, traffic_patterns):
            signals["traffic"] = True

        dirty_air_patterns = [
            "dirty air",
            "following closely",
            "can't follow",
            "cant follow",
            "losing front in traffic",
            "front washes in traffic",
        ]

        if self._contains(text_lower, dirty_air_patterns):
            signals["dirty_air"] = True
            signals["traffic"] = True
            signals["grip_loss"] = True

        # --------------------------------------------------------
        # FATIGUE
        # --------------------------------------------------------

        fatigue_patterns = [
            "tired",
            "very tired",
            "exhausted",
            "fatigued",
            "fatigue",
            "sleepy",
            "struggling to focus",
            "can't focus",
            "cant focus",
            "losing concentration",
            "hard to concentrate",
        ]

        if self._contains(text_lower, fatigue_patterns):
            signals["fatigue"] = True

        # --------------------------------------------------------
        # WORKLOAD
        # --------------------------------------------------------

        workload_patterns = [
            "too much going on",
            "too busy",
            "struggling",
            "difficult to manage",
            "hard to manage",
            "can't keep up",
            "cant keep up",
            "under pressure",
            "high workload",
        ]

        if self._contains(text_lower, workload_patterns):
            signals["high_workload"] = True

        # --------------------------------------------------------
        # VIBRATION
        # --------------------------------------------------------

        vibration_patterns = [
            "vibration",
            "vibrating",
            "shaking",
            "wheel vibration",
            "steering vibration",
        ]

        if self._contains(text_lower, vibration_patterns):
            signals["vibration"] = True

        # --------------------------------------------------------
        # SLIDING
        # --------------------------------------------------------

        sliding_patterns = [
            "sliding",
            "slide",
            "slip",
            "slipping",
            "rear sliding",
            "front sliding",
        ]

        if self._contains(text_lower, sliding_patterns):
            signals["sliding"] = True
            signals["grip_loss"] = True

        return signals

    # ============================================================
    # MOTORSPORT LLM
    # ============================================================

    def _ask_motorsport_llm(self, text: str) -> dict | None:
        if not self.hf_token:
            print(
                "HF_TOKEN not configured - "
                "using Motorsport Rule Engine fallback."
            )
            return None

        system_prompt = """
You are a Formula 1 race engineer and motorsport radio analyst.

Interpret natural driver radio language, including incomplete,
informal, emotional and technically imprecise statements.

Understand Formula 1 terminology such as:

- understeer
- oversteer
- lock-up
- front/rear grip
- tire degradation
- tire overheating
- brake fade
- front wing
- rear wing
- floor
- diffuser
- sidepod
- downforce
- dirty air
- traffic
- power loss
- gearbox
- engine temperature
- puncture
- vibration
- steering problems

Return ONLY valid JSON.

The JSON must contain:

{
  "signals": {
    "grip_loss": false,
    "tire_problem": false,
    "overheating": false,
    "puncture": false,
    "braking_problem": false,
    "steering_problem": false,
    "engine_problem": false,
    "traffic": false,
    "fatigue": false,
    "high_workload": false,
    "sliding": false,
    "vibration": false,
    "front_wing_damage": false,
    "rear_wing_damage": false,
    "floor_damage": false,
    "sidepod_damage": false,
    "diffuser_damage": false,
    "downforce_loss": false,
    "understeer": false,
    "oversteer": false,
    "wheel_locking": false,
    "brake_fade": false,
    "power_loss": false,
    "gearbox_problem": false,
    "dirty_air": false,
    "tire_degradation": false
  },
  "severity": "NORMAL",
  "emotion": "NEUTRAL / FOCUSED",
  "driver_message": "short actionable radio response"
}

Rules:

1. Only mark a signal true when the driver's statement supports it.
2. Understand synonyms and natural language.
3. "I lost the front wing" means front_wing_damage=true and
   downforce_loss=true.
4. "The rear is stepping out" means oversteer=true,
   sliding=true and grip_loss=true.
5. "I'm locking the fronts" means wheel_locking=true and
   braking_problem=true.
6. "The tires are gone" means tire_problem=true and potentially
   tire_degradation=true.
7. "I can't get the car turned in" means understeer=true and
   grip_loss=true.
8. Critical vehicle damage should produce CRITICAL severity.
9. Do not invent telemetry values.
10. Keep driver_message concise enough for race radio.
"""

        user_prompt = f"""
Driver radio:

"{text}"

Analyze this statement as an F1 race engineer.
"""

        payload = {
            "model": self.llm_model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "temperature": 0.1,
            "max_tokens": 700,
        }

        headers = {
            "Authorization": f"Bearer {self.hf_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                HF_API_URL,
                json=payload,
                headers=headers,
                timeout=15,
            )

            if response.status_code != 200:
                print(
                    f"Motorsport LLM unavailable: "
                    f"{response.status_code}"
                )
                return None

            data = response.json()

            choices = data.get("choices")

            if not choices:
                return None

            content = choices[0]["message"]["content"]

            return self._extract_json(content)

        except Exception as exc:
            print(
                f"Motorsport LLM unavailable: {exc}"
            )
            return None

    # ============================================================
    # JSON EXTRACTION
    # ============================================================

    def _extract_json(self, content: str) -> dict | None:
        if not content:
            return None

        content = content.strip()

        # Direct JSON
        try:
            parsed = json.loads(content)

            if isinstance(parsed, dict):
                return parsed

        except json.JSONDecodeError:
            pass

        # JSON inside markdown fences
        fenced = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```",
            content,
            flags=re.DOTALL,
        )

        if fenced:
            try:
                parsed = json.loads(fenced.group(1))

                if isinstance(parsed, dict):
                    return parsed

            except json.JSONDecodeError:
                pass

        # Find first JSON object
        start = content.find("{")
        end = content.rfind("}")

        if start >= 0 and end > start:
            try:
                parsed = json.loads(
                    content[start : end + 1]
                )

                if isinstance(parsed, dict):
                    return parsed

            except json.JSONDecodeError:
                pass

        return None

    # ============================================================
    # MERGE LLM + LOCAL SIGNALS
    # ============================================================

    def _merge_signals(
        self,
        local_signals: dict,
        llm_result: dict | None,
    ) -> dict:

        merged = dict(local_signals)

        if not llm_result:
            return merged

        llm_signals = llm_result.get(
            "signals",
            {},
        )

        if not isinstance(llm_signals, dict):
            return merged

        for key in merged:
            if llm_signals.get(key) is True:
                merged[key] = True

        return merged

    # ============================================================
    # DRIVER STATE
    # ============================================================

    def _calculate_driver_state(
        self,
        signals: dict,
        llm_result: dict | None,
    ):
        critical = (
            signals["puncture"]
            or signals["engine_problem"]
            or signals["gearbox_problem"]
            or signals["braking_problem"]
            or signals["front_wing_damage"]
            or signals["rear_wing_damage"]
            or signals["floor_damage"]
            or signals["diffuser_damage"]
            or (
                signals["grip_loss"]
                and signals["tire_problem"]
            )
            or (
                signals["overheating"]
                and signals["tire_problem"]
            )
        )

        if critical:
            return (
                0.91,
                "CRITICAL",
                "HIGH STRESS / ANXIETY",
            )

        elevated = (
            signals["grip_loss"]
            or signals["tire_problem"]
            or signals["overheating"]
            or signals["steering_problem"]
            or signals["sliding"]
            or signals["vibration"]
            or signals["high_workload"]
            or signals["fatigue"]
            or signals["traffic"]
            or signals["understeer"]
            or signals["oversteer"]
            or signals["wheel_locking"]
            or signals["dirty_air"]
            or signals["tire_degradation"]
        )

        if elevated:
            return (
                0.72,
                "ELEVATED",
                "MODERATE STRESS",
            )

        if llm_result:
            severity = str(
                llm_result.get(
                    "severity",
                    "NORMAL",
                )
            ).upper()

            emotion = str(
                llm_result.get(
                    "emotion",
                    "NEUTRAL / FOCUSED",
                )
            )

            if severity == "CRITICAL":
                return (
                    0.91,
                    "CRITICAL",
                    emotion,
                )

            if severity == "ELEVATED":
                return (
                    0.72,
                    "ELEVATED",
                    emotion,
                )

        return (
            0.15,
            "NORMAL",
            "NEUTRAL / FOCUSED",
        )

    # ============================================================
    # STRATEGY
    # ============================================================

    def _generate_strategy(
        self,
        signals: dict,
        alert_level: str,
        lap: int,
        llm_result: dict | None,
    ):

        # LLM can provide a strategic recommendation,
        # but only use it if it contains a usable action.

        llm_strategy = (
            llm_result.get("strategy")
            if isinstance(llm_result, dict)
            else None
        )

        if isinstance(llm_strategy, dict):
            action = llm_strategy.get("action")
            compound = llm_strategy.get(
                "target_compound",
                "Current",
            )

            if action:
                return {
                    "action": str(action),
                    "target_compound": str(compound),
                    "recommended_pit_lap": lap,
                }

        # --------------------------------------------------------
        # FRONT / REAR WING
        # --------------------------------------------------------

        if (
            signals["front_wing_damage"]
            or signals["rear_wing_damage"]
        ):
            return {
                "action": (
                    "Box immediately. Assess aerodynamic damage "
                    "and prepare replacement parts."
                ),
                "target_compound": "Current",
                "recommended_pit_lap": lap,
            }

        # --------------------------------------------------------
        # FLOOR / DIFFUSER
        # --------------------------------------------------------

        if (
            signals["floor_damage"]
            or signals["diffuser_damage"]
        ):
            return {
                "action": (
                    "Box and inspect the floor and aerodynamic "
                    "components immediately."
                ),
                "target_compound": "Current",
                "recommended_pit_lap": lap,
            }

        # --------------------------------------------------------
        # PUNCTURE
        # --------------------------------------------------------

        if signals["puncture"]:
            return {
                "action": (
                    "Box immediately. Check tire damage "
                    "and prepare fresh Medium tires."
                ),
                "target_compound": "Medium",
                "recommended_pit_lap": lap,
            }

        # --------------------------------------------------------
        # GRIP + TIRE + OVERHEATING
        # --------------------------------------------------------

        if (
            signals["grip_loss"]
            and signals["tire_problem"]
            and signals["overheating"]
        ):
            return {
                "action": (
                    "Box this lap. Prepare fresh Medium tires."
                ),
                "target_compound": "Medium",
                "recommended_pit_lap": lap,
            }

        # --------------------------------------------------------
        # GRIP + TIRE
        # --------------------------------------------------------

        if (
            signals["grip_loss"]
            and signals["tire_problem"]
        ):
            return {
                "action": (
                    "Box this lap. Prepare fresh Medium tires."
                ),
                "target_compound": "Medium",
                "recommended_pit_lap": lap,
            }

        # --------------------------------------------------------
        # BRAKES
        # --------------------------------------------------------

        if (
            signals["brake_fade"]
            or signals["wheel_locking"]
            or signals["braking_problem"]
        ):
            return {
                "action": (
                    "Manage braking load and monitor "
                    "brake temperatures."
                ),
                "target_compound": "Current",
                "recommended_pit_lap": lap + 2,
            }

        # --------------------------------------------------------
        # ENGINE / POWER
        # --------------------------------------------------------

        if (
            signals["engine_problem"]
            or signals["power_loss"]
        ):
            return {
                "action": (
                    "Protect the engine and prepare "
                    "for an immediate pit stop."
                ),
                "target_compound": "Current",
                "recommended_pit_lap": lap,
            }

        # --------------------------------------------------------
        # GEARBOX
        # --------------------------------------------------------

        if signals["gearbox_problem"]:
            return {
                "action": (
                    "Protect the gearbox and avoid unnecessary "
                    "shift load."
                ),
                "target_compound": "Current",
                "recommended_pit_lap": lap + 2,
            }

        # --------------------------------------------------------
        # OVERHEATING
        # --------------------------------------------------------

        if signals["overheating"]:
            return {
                "action": (
                    "Manage tire temperatures "
                    "and prepare a pit stop."
                ),
                "target_compound": "Medium",
                "recommended_pit_lap": lap + 1,
            }

        # --------------------------------------------------------
        # TRAFFIC
        # --------------------------------------------------------

        if (
            signals["traffic"]
            or signals["dirty_air"]
        ):
            return {
                "action": (
                    "Manage tire temperature and search "
                    "for clean air."
                ),
                "target_compound": "Current",
                "recommended_pit_lap": lap + 4,
            }

        # --------------------------------------------------------
        # FATIGUE
        # --------------------------------------------------------

        if (
            signals["fatigue"]
            or signals["high_workload"]
        ):
            return {
                "action": (
                    "Reduce workload and maintain "
                    "a controlled race pace."
                ),
                "target_compound": "Current",
                "recommended_pit_lap": lap + 4,
            }

        # --------------------------------------------------------
        # ELEVATED
        # --------------------------------------------------------

        if alert_level == "ELEVATED":
            return {
                "action": (
                    "Adjust brake balance +2% rear "
                    "and monitor tire temperatures."
                ),
                "target_compound": "Medium",
                "recommended_pit_lap": lap + 3,
            }

        # --------------------------------------------------------
        # NORMAL
        # --------------------------------------------------------

        return {
            "action": (
                "Maintain current pace and stint strategy."
            ),
            "target_compound": "Optimal Delta",
            "recommended_pit_lap": lap + 6,
        }

    # ============================================================
    # DRIVER RADIO RESPONSE
    # ============================================================

    def _generate_driver_message(
        self,
        signals: dict,
        alert_level: str,
        llm_result: dict | None,
    ):

        # Prefer LLM radio response when available.
        if llm_result:
            llm_message = llm_result.get(
                "driver_message"
            )

            if isinstance(
                llm_message,
                str,
            ) and llm_message.strip():

                return llm_message.strip()

        if signals["front_wing_damage"]:
            return (
                "Front wing damage detected. "
                "Box immediately and prepare a replacement."
            )

        if signals["rear_wing_damage"]:
            return (
                "Rear wing damage detected. "
                "Box immediately and assess the damage."
            )

        if (
            signals["floor_damage"]
            or signals["diffuser_damage"]
        ):
            return (
                "Aero damage detected. "
                "Box this lap for inspection."
            )

        if signals["puncture"]:
            return (
                "Tire failure detected. "
                "Box immediately."
            )

        if (
            signals["grip_loss"]
            and signals["tire_problem"]
            and signals["overheating"]
        ):
            return (
                "Grip loss and tire overheating detected. "
                "Box this lap."
            )

        if (
            signals["understeer"]
            and signals["oversteer"]
        ):
            return (
                "Vehicle balance instability detected. "
                "Manage the car and report if it worsens."
            )

        if signals["understeer"]:
            return (
                "Understeer detected. "
                "Manage front tire load and entry speed."
            )

        if signals["oversteer"]:
            return (
                "Oversteer detected. "
                "Manage rear traction and throttle."
            )

        if signals["wheel_locking"]:
            return (
                "Front lock-up detected. "
                "Reduce braking load."
            )

        if signals["brake_fade"]:
            return (
                "Brake fade detected. "
                "Reduce braking load and monitor temperatures."
            )

        if signals["engine_problem"]:
            return (
                "Engine issue detected. "
                "Protect the engine and prepare to box."
            )

        if signals["power_loss"]:
            return (
                "Power loss detected. "
                "Protect the engine and prepare to box."
            )

        if signals["gearbox_problem"]:
            return (
                "Gearbox issue detected. "
                "Reduce shift load and protect the car."
            )

        if signals["traffic"]:
            return (
                "Traffic ahead. "
                "Manage tire temperature and look for clean air."
            )

        if signals["fatigue"]:
            return (
                "Driver fatigue detected. "
                "Stay controlled and maintain focus."
            )

        if signals["high_workload"]:
            return (
                "High driver workload detected. "
                "Focus on the next sector."
            )

        if alert_level == "ELEVATED":
            return (
                "Driver state elevated. "
                "Manage pace and monitor vehicle condition."
            )

        return (
            "Driver state stable. "
            "Maintain current pace and strategy."
        )

    # ============================================================
    # MAIN ANALYSIS PIPELINE
    # ============================================================

    def analyze_vocal_telemetry(
        self,
        text: str,
        lap: int = 18,
    ) -> dict:

        text = (text or "").strip()

        if not text:
            text = "Telemetry signal standard"

        try:
            lap = int(lap)
        except (TypeError, ValueError):
            lap = 18

        # --------------------------------------------------------
        # 1. LOCAL SIGNALS
        # --------------------------------------------------------

        local_signals = self._analyse_signals(text)

        # --------------------------------------------------------
        # 2. MOTORSPORT LLM
        # --------------------------------------------------------

        llm_result = self._ask_motorsport_llm(text)

        # --------------------------------------------------------
        # 3. MERGE
        # --------------------------------------------------------

        signals = self._merge_signals(
            local_signals,
            llm_result,
        )

        # --------------------------------------------------------
        # 4. DRIVER STATE
        # --------------------------------------------------------

        (
            stress_index,
            alert_level,
            emotion,
        ) = self._calculate_driver_state(
            signals,
            llm_result,
        )

        # --------------------------------------------------------
        # 5. STRATEGY
        # --------------------------------------------------------

        strategy = self._generate_strategy(
            signals,
            alert_level,
            lap,
            llm_result,
        )

        # --------------------------------------------------------
        # 6. DRIVER MESSAGE
        # --------------------------------------------------------

        driver_message = self._generate_driver_message(
            signals,
            alert_level,
            llm_result,
        )

        # --------------------------------------------------------
        # 7. CONFIDENCE
        # --------------------------------------------------------

        if llm_result:
            confidence = 0.94
            inference_source = (
                "Hugging Face Motorsport LLM "
                "+ Motorsport Rule Engine"
            )
        else:
            confidence = (
                0.94
                if alert_level != "NORMAL"
                else 0.70
            )

            inference_source = (
                "Motorsport Rule Engine"
            )

        # --------------------------------------------------------
        # 8. FATIGUE
        # --------------------------------------------------------

        fatigue_score = round(
            min(
                1.0,
                stress_index
                + (
                    0.15
                    if signals["fatigue"]
                    else 0.0
                ),
            ),
            2,
        )

        if fatigue_score >= 0.75:
            fatigue = "HIGH"
        elif fatigue_score >= 0.45:
            fatigue = "MODERATE"
        else:
            fatigue = "LOW"

        # --------------------------------------------------------
        # 9. WORKLOAD
        # --------------------------------------------------------

        if alert_level == "CRITICAL":
            workload = "VERY HIGH"
        elif alert_level == "ELEVATED":
            workload = "HIGH"
        else:
            workload = "NORMAL"

        # --------------------------------------------------------
        # 10. TELEMETRY
        # --------------------------------------------------------

        telemetry = {
            "speed_kmh": None,
            "ear": None,
            "rpm": None,
            "gear": None,
            "fatigue": fatigue,
            "fatigue_score": fatigue_score,
            "workload": workload,
        }

        # --------------------------------------------------------
        # 11. FINAL RESPONSE
        # --------------------------------------------------------

        return {
            "transcript": text,
            "stress_index": stress_index,
            "alert_level": alert_level,
            "emotion_label": emotion,
            "confidence": confidence,
            "inference_source": inference_source,
            "telemetry": telemetry,
            "detected_signals": signals,
            "strategy": strategy,
            "driver_message": driver_message,
        }


# ================================================================
# SINGLE ENGINE INSTANCE
# ================================================================

engine = SilentCoDriverEngine()


def analyze_driver_state(
    text: str,
    lap: int = 18,
) -> dict:

    return engine.analyze_vocal_telemetry(
        text=text,
        lap=lap,
    )
