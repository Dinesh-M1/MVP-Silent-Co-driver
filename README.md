# Silent Co-Driver MVP

A lightweight AI-assisted driving support prototype that analyzes driver text or voice-like input and returns stress/fatigue insights plus a recommended pit strategy.

## What it does

- Accepts driver transcripts or telemetry-style notes
- Runs analysis through a FastAPI backend
- Returns a stress score, alert level, emotion label, and strategy action
- Offers a simple web interface for local demos
- Uses a Hugging Face inference path with a heuristic fallback for reliability

## Project structure

```text
backend/           # FastAPI app and analysis logic
frontend/frontend/ # Next.js UI for the demo
frontend/          # Vite-based frontend files (legacy/alternate entry)
```

## Architecture

```text
User input -> Frontend UI -> FastAPI backend -> Hugging Face inference / heuristic fallback -> Strategy output
```

## Run the backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

The API will be available at:
- http://127.0.0.1:8001/
- http://127.0.0.1:8001/api/v1/analyze

## Run the frontend

```powershell
cd frontend/frontend
npm install
npm run dev
```

Then open:
- http://localhost:3000

## Example API payload

```json
{
  "text_input": "I lost grip on turn 5",
  "driver_id": "DRIVER_01",
  "lap_number": 24
}
```

## Example Hugging Face models

- https://huggingface.co/distilbert-base-uncased-finetuned-sms-spam-detection
- https://huggingface.co/bert-base-uncased
