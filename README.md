# AI Field Technician Copilot

An AI-powered web application for industrial machine diagnostics. Field technicians select a machine, view live sensor telemetry, and get an AI-generated diagnosis with recommended corrective actions.

## Why this project

Formant’s platform focuses on enabling AI agents to observe machines,
analyze system behavior, and assist operators in real-world operations.

This project was built over a weekend while exploring ideas around how
Formant-style physical AI systems could assist field technicians during
machine failures.

This prototype explores one small extension of that idea:

An AI assistant that analyzes machine telemetry and logs to produce
a structured diagnosis and recommended corrective actions for field technicians.

The goal of the project is to simulate how an intelligent agent could
triage machine alerts before escalation and assist technicians with
faster root-cause analysis.

## Demo Flow

1. Technician selects a machine
2. System loads current sensor telemetry and recent machine errors
3. A deterministic rules engine evaluates known fault patterns
4. If no high-confidence rule fires, an LLM analyzes telemetry + logs
5. The system returns:
   - probable root cause
   - recommended corrective action
   - severity level
   - confidence score

## Quick Start

### Backend (FastAPI + Python)

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — set GEMINI_API_KEY, or set USE_MOCK_LLM=true for demo mode
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### Frontend (React + TypeScript + Vite)

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

### Run backend tests

```bash
cd backend
pytest tests/ -v
```

### Run frontend tests

```bash
cd frontend
npm test
```

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the complete system specification including:
- 3-layer architecture (Data → Rules Engine → LLM)
- All API endpoint contracts
- Diagnosis pipeline flow
- Fallback behavior specification
- Frontend component tree

## Project Structure

```
ai-field-technician-copilot/
├── ARCHITECTURE.md        
├── backend/
│   ├── app/
│   │   ├── main.py        — FastAPI app entry point
│   │   ├── config.py      — settings via pydantic-settings
│   │   ├── routes/        — HTTP endpoint handlers
│   │   ├── services/      — business logic + cache
│   │   ├── diagnosis/     — rules engine, pipeline, prompt builder, parser
│   │   ├── llm/           — LLM client abstraction (Gemini + mock)
│   │   └── schemas/       — Pydantic models (shared API contract)
│   ├── data/
│   │   └── machines/      — JSON data files for 5 pre-loaded machines
│   ├── tests/             — pytest test suite
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── components/    — React UI components
    │   ├── hooks/         — custom data-fetching hooks
    │   ├── api/           — HTTP client (fetch wrapper)
    │   └── types/         — TypeScript types mirroring Pydantic schemas
    ├── package.json
    └── vite.config.ts
```

## Pre-loaded Machines

| ID | Name | Status | Scenario |
|---|---|---|---|
| `conveyor_1` | Conveyor Belt Alpha | Normal | Healthy baseline — all sensors nominal |
| `conveyor_2` | Conveyor Belt Beta | Warning | Temperature + vibration trending up (bearing wear) |
| `robotic_arm_1` | Robotic Arm Delta | Critical | Joint 1 critical overheat — emergency stop triggered |
| `pump_4` | Hydraulic Pump Gamma | Critical | Seal failure — critical pressure loss + cavitation |
| `compressor_2` | Air Compressor Epsilon | Warning | Rotor imbalance — vibration above threshold |
