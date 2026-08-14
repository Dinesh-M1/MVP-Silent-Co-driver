Silent Co-Driver

AI-assisted racing co-driver MVP for an F1 simulator.

The project combines driver radio analysis, Hugging Face inference, deterministic
motorsport rules, driver-state estimation, strategy/co-driver responses, and
live F1 game telemetry.

Scope: The current telemetry integration is for an F1 game/simulator using
its UDP telemetry interface. It does not connect directly to a real-world
Haas/F1 car or private FIA/team telemetry.

Architecture

                         ┌─────────────────────┐
                         │    F1 GAME / SIM    │
                         │     UDP :20777      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      f1_udp.py      │
                         │  Live vehicle data  │
                         └──────────┬──────────┘
                                    │
                                    ▼
Driver ── Voice / Radio ──► Silent Co-Driver AI
                                    │
                    ┌───────────────┼────────────────┐
                    ▼               ▼                ▼
                 Whisper          Qwen          Wav2Vec2
                speech-to-text   context       voice emotion
                    │               │                │
                    └───────────────┼────────────────┘
                                    ▼
                         Motorsport Rule Engine
                                    │
                                    ▼
                         FINAL ENGINEER DECISION
                                    │
                    ┌───────────────┼────────────────┐
                    ▼               ▼                ▼
              Driver State      Strategy       Co-Driver
              Stress/Fatigue     Pit/Tires       Response
                                    │
                                    ▼
                              Next.js Dashboard

Decision authority

The project intentionally separates AI context from the final motorsport
decision:

Whisper: speech-to-text for uploaded driver radio audio.

Wav2Vec2: voice-emotion analysis.

Qwen: contextual interpretation/explanation.

Motorsport rule engine: authoritative for explicit racing signals.

Therefore, an explicit command such as Box, box. is treated as a
deterministic PIT REQUEST rather than allowing an LLM to change it.

The Hugging Face pipeline is hosted through Hugging Face Inference Providers;
the project does not require downloading the large models locally. If
HF_TOKEN is unavailable, the local deterministic motorsport rules can still
handle supported text/radio signals.

Project structure

Silent Co-Driver/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── f1_udp.py
│   │   ├── telemetry.py
│   │   ├── hf_pipeline.py
│   │   ├── racing_events.py
│   │   └── schemas.py
│   └── requirements.txt
│
└── frontend/
    ├── app/
    │   └── page.tsx
    ├── components/
    ├── package.json
    └── .env.local

Backend requirements

Python 3.10+

FastAPI

Uvicorn

python-multipart for audio uploads

huggingface-hub for Hugging Face Inference Providers

The backend does not need torch, transformers, librosa, or Whisper to be
installed locally for the current hosted-inference architecture.

Run the backend

From the project root:

cd backend
python -m venv .venv

Windows

.venv\Scriptsctivate

macOS/Linux

source .venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Start FastAPI:

python -m uvicorn app.main:app --reload --port 8000

Backend:

http://127.0.0.1:8000

Swagger:

http://127.0.0.1:8000/docs

Health check:

http://127.0.0.1:8000/health

Hugging Face configuration

Set your Hugging Face token if you want hosted Hugging Face inference:

Windows PowerShell

$env:HF_TOKEN="hf_your_token_here"

macOS/Linux

export HF_TOKEN="hf_your_token_here"

The current default models are:

ASR:
openai/whisper-large-v3

Voice emotion:
ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition

Sentiment:
distilbert/distilbert-base-uncased-finetuned-sst-2-english

Reasoning/context:
Qwen/Qwen2.5-1.5B-Instruct

These can be overridden with:

HF_ASR_MODEL
HF_EMOTION_MODEL
HF_SENTIMENT_MODEL
HF_REASONING_MODEL

Do not commit HF_TOKEN to Git.

Run the frontend

Open another terminal:

cd frontend
npm install
npm run dev

The frontend uses:

http://127.0.0.1:8000

by default.

If you need to override it, create:

frontend/.env.local

with:

NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000

Then open:

http://localhost:3000

Note: NEXT_PUBLIC_BACKEND_URL is the frontend variable used by the current
Next.js dashboard. The older BACKEND_URL=.../api/v1/analyze setting is not
the correct configuration for the current frontend.

Text analysis

The current API endpoint is:

POST /api/v1/analyze

Example request:

{
  "text_input": "I lost rear grip and tires are overheating",
  "driver_id": "DRIVER_01"
}

If F1 UDP is connected, the backend obtains the current lap from the simulator.
Do not provide a fake fallback lap such as 18 or 0.

Example: deterministic pit request

Input:

Box, box.

Expected core decision:

Detected signal: pit_request

Priority: HIGH

Pit request confirmed.
Box this lap.
Prepare Fresh Medium tires.

Identical radio text should produce the same explicit PIT REQUEST decision.

Audio analysis

The current API endpoint is:

POST /api/v1/analyze-audio

The multipart upload field must be:

audio

The frontend sends:

audio = selected audio file
driver_id = DRIVER_01

The backend then runs:

Audio
  ↓
Whisper
  ↓
Transcript
  ↓
Voice emotion
  ↓
Qwen/context
  ↓
Motorsport rule engine
  ↓
Driver state + strategy + engineer decision

For hosted Whisper/audio inference, set HF_TOKEN.

F1 simulator UDP telemetry

The backend includes an F1 UDP receiver.

Default listener:

Host: 0.0.0.0
Port: 20777

For a game running on the same Windows PC, configure the game to send UDP
telemetry to:

IP:   127.0.0.1
Port: 20777

Enable UDP telemetry in the game's telemetry settings and enter an actual
driving session.

The receiver reads live vehicle/lap information such as:

Speed
RPM
Gear
Throttle
Brake
Current lap
Lap time

The dashboard must display these values from the UDP telemetry store. They are
not generated by the AI.

Check UDP status

GET /api/v1/f1-udp/status

Example:

Invoke-RestMethod "http://127.0.0.1:8000/api/v1/f1-udp/status" |
    ConvertTo-Json -Depth 10

Before the game sends telemetry, this is expected:

udp_connected: false
packets_received: 0

After entering a session and driving, it should become:

udp_connected: true
packets_received: > 0

with live telemetry values.

Check current telemetry

GET /api/v1/telemetry

PowerShell:

Invoke-RestMethod "http://127.0.0.1:8000/api/v1/telemetry"

When the simulator is disconnected, vehicle values remain null/--.
The application does not fabricate speed, RPM, gear, throttle, brake, or lap
values.

Telemetry endpoints

Current telemetry

GET /api/v1/telemetry

Simulator telemetry input

POST /api/v1/telemetry

This endpoint can be used for testing with a simulator adapter or manual
telemetry source.

Example:

{
  "speed_kmh": 247.5,
  "rpm": 8420,
  "gear": 6,
  "throttle": 0.92,
  "brake": 0.0,
  "lap_number": 24
}

Lap history

GET /api/v1/telemetry/history

Clear lap history

DELETE /api/v1/telemetry/history

Autonomous lap handling

The current system is designed so the simulator owns the lap number.

F1 UDP LapData
      ↓
current lap
      ↓
telemetry store
      ↓
analysis / lap performance / dashboard

There is no intentional hard-coded race lap such as:

18

and 0 is not treated as a real racing lap.

If the simulator is disconnected:

lap_number = null

Once the simulator sends lap data:

lap_number = actual F1 game lap

Live vehicle telemetry

The live telemetry dashboard uses simulator data rather than AI estimates:

Speed       ← F1 UDP
RPM         ← F1 UDP
Gear        ← F1 UDP
Throttle    ← F1 UDP
Brake       ← F1 UDP
Lap         ← F1 UDP
Lap time    ← F1 UDP

If UDP packets stop arriving, the system should stop presenting stale vehicle
values as live data.

Driver-state analysis

The current MVP derives driver-state indicators from driver radio analysis.

The main concepts are:

Stress
Fatigue
Workload
Alert level
Confidence
Tone / emotion

These are analysis outputs, not medical measurements.

Lap performance

Lap performance combines available simulator lap data with analysis outputs,
including:

Lap number
Lap time
Stress
Fatigue
Driver state
Events
Confidence

The dashboard visualizes this history for the engineer.

Real F1 race scope

This project currently supports an F1 game/simulator telemetry interface.

It does not directly connect to:

Real Haas F1 car
Real FIA telemetry
Private team telemetry

A real-world F1 data source would require an authorized telemetry feed and a
separate adapter. The AI/rule/driver-state layers can remain conceptually
separate from that future telemetry adapter.

Troubleshooting

Backend is offline

Run:

python -m uvicorn app.main:app --reload --port 8000

Check:

http://127.0.0.1:8000/health

Text analysis returns 400

Use JSON:

{
  "text_input": "Box, box.",
  "driver_id": "DRIVER_01"
}

PowerShell:

$body = @{
    text_input = "Box, box."
    driver_id = "DRIVER_01"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/api/v1/analyze" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

UDP shows zero packets

Check:

Get-NetUDPEndpoint -LocalPort 20777

The backend should be listening on:

0.0.0.0:20777

Then verify the F1 game's UDP telemetry is enabled, the destination IP is
127.0.0.1 for a same-PC setup, and the port is 20777.

Finally, enter an actual driving session. Merely running the game without
telemetry packets does not populate the dashboard.

Audio inference fails

Check:

HF_TOKEN

and confirm that the backend can reach Hugging Face Inference Providers.

Text-based deterministic motorsport rules can still operate without the
Hugging Face token, but hosted ASR/voice inference requires the configured
Hugging Face service.

Development notes

Speed is never fabricated.

RPM, gear, throttle, brake and lap are simulator telemetry values.

F1 UDP is the authoritative source for the live lap.

Identical explicit radio commands should produce identical deterministic
engineering decisions.

Qwen is context/explanation support, not the final authority for explicit
motorsport commands.

EAR/camera processing is not part of the current MVP.

The co-driver response is intentionally short and actionable.

Keep secrets such as HF_TOKEN out of source control.
