# AI Field Technician Copilot — Architecture Specification

---

## 1. System Overview

The AI Field Technician Copilot is a web application that helps industrial field technicians diagnose machine faults. Given a machine ID, the system reads live sensor data and logs from disk, runs a deterministic rules engine, then (if needed) calls Google Gemini to produce a natural-language diagnosis and recommended action.

### Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI (Python 3.11+) |
| LLM | Google Gemini 1.5 Flash via `google-generativeai` SDK |
| Data store | JSON files on disk (no database) |
| Frontend | React 18 + TypeScript + Vite |
| Styling | Inline styles (no CSS framework) |
| Testing (backend) | pytest + pytest-asyncio |
| Testing (frontend) | Vitest + @testing-library/react |

---

## 2. Three-Layer Architecture

```
┌─────────────────────────────────────────────┐
│              HTTP Clients / Browser         │
└─────────────────────────┬───────────────────┘
                          │ HTTP
┌─────────────────────────▼───────────────────┐
│               FastAPI Routes                │
│         /machines/*   /diagnose             │
└──────────┬─────────────────────┬────────────┘
           │                     │
┌──────────▼──────────┐ ┌────────▼────────────┐
│   MachineService    │ │  DiagnosisService   │
│  (disk reads only)  │ │  (orchestrator)     │
└──────────┬──────────┘ └────────┬────────────┘
           │                     │
           │            ┌────────▼────────────┐
           │            │  DiagnosisPipeline  │
           │            │                     │
           │            │  1. RulesEngine     │ ← Layer 1: Deterministic
           │            │  2. PromptBuilder   │ ← Layer 2: Context builder
           │            │  3. LLM Client      │ ← Layer 3: AI
           │            │  4. ResponseParser  │ ← Layer 3: Parse
           │            └────────┬────────────┘
           │                     │
┌──────────▼──────────┐ ┌────────▼────────────┐
│  data/machines/     │ │    CacheService     │
│  (JSON files)       │ │  (in-memory TTL)    │
└─────────────────────┘ └─────────────────────┘
```

### Layer 1 — Data Layer
- **Location:** `backend/data/machines/<machine_id>/`
- Reads `info.json`, `sensors.json`, `errors.json`, `logs.txt`
- Implemented in: `app/services/machine_service.py`
- Purely synchronous disk I/O

### Layer 2 — Rules Engine
- **Location:** `app/diagnosis/rules_engine.py`
- Deterministic rules evaluated before any LLM call
- If a rule fires with `confidence >= 0.85`, the pipeline short-circuits — no LLM call
- Rules are prioritized: offline > critical temp > critical vibration > motor overload > pressure > warning temp

### Layer 3 — LLM Layer
- **Location:** `app/llm/`, `app/diagnosis/prompt_builder.py`, `app/diagnosis/response_parser.py`
- Only called when no high-confidence rule fires
- LLM client is swappable via `BaseLLMClient` abstract base class
- `USE_MOCK_LLM=true` in `.env` substitutes `MockLLMClient` for all tests

---

## 3. API Endpoint Contracts

All endpoints return JSON. Errors follow FastAPI's default `{"detail": "..."}` shape for 4xx, and `DiagnosisResponse(success=False, error=...)` for diagnosis failures.

### 3.1 GET /

**Response:**
```json
{ "status": "ok", "app": "AI Field Technician Copilot" }
```

### 3.2 GET /health

**Response:**
```json
{ "status": "healthy" }
```

### 3.3 GET /machines/

Returns summary list of all machines. Discovers machines by scanning `data/machines/` subdirectories.

**Response:** `200 OK`
```json
[
  {
    "machine_id": "conveyor_1",
    "name": "Conveyor Belt 1",
    "type": "conveyor",
    "status": "normal",
    "location": "Factory Floor A - Line 1"
  }
]
```

Status is derived from sensor readings:
- Any sensor with `status="critical"` → machine status `"critical"`
- Any sensor with `status="warning"` → machine status `"warning"`
- No sensors at all → machine status `"offline"` is NOT returned here; offline is returned when `status` would be `"normal"` but sensors array is empty (handled by `_derive_status`)
- All normal → `"normal"`

### 3.4 GET /machines/{machine_id}

**Path param:** `machine_id` — must match a subdirectory name under `data/machines/`

**Response:** `200 OK`
```json
{
  "machine_id": "robotic_arm_1",
  "name": "Robotic Arm 1",
  "type": "robotic_arm",
  "location": "Assembly Station B",
  "status": "critical",
  "last_updated": "2026-03-14T10:30:00+00:00",
  "sensors": [
    {
      "name": "joint_1_temperature",
      "value": 104.7,
      "unit": "°C",
      "threshold_warning": 85.0,
      "threshold_critical": 100.0,
      "status": "critical"
    }
  ],
  "recent_errors": [
    "E_JOINT_TEMP_CRITICAL: Joint 1 temperature exceeded critical threshold"
  ]
}
```

**Error:** `404 Not Found` if machine_id not found.

### 3.5 POST /diagnose

**Request body:**
```json
{
  "machine_id": "pump_4",
  "include_logs": true,
  "force_refresh": false
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `machine_id` | string | required | Machine to diagnose |
| `include_logs` | bool | `true` | Include `logs.txt` content in prompt |
| `force_refresh` | bool | `false` | Bypass cache; re-run pipeline |

**Response:** `200 OK` (always 200; check `success` field)
```json
{
  "success": true,
  "result": {
    "machine_id": "pump_4",
    "timestamp": "2026-03-14T10:30:00+00:00",
    "diagnosis": "Critical low outlet pressure indicating pump seal failure or blockage.",
    "recommended_action": "Shut down pump. Inspect seals, check for leaks in hydraulic circuit. Replace worn seal kit.",
    "severity": "critical",
    "confidence_score": 0.91,
    "supporting_evidence": [
      {
        "description": "outlet_pressure = 1.8 bar (critical threshold exceeded)",
        "source": "sensor"
      },
      {
        "description": "E_PRESSURE_LOW error code present",
        "source": "error_code"
      }
    ],
    "source": "rules_fallback",
    "raw_sensor_snapshot": {
      "outlet_pressure": 1.8,
      "flow_rate": 12.4
    }
  },
  "error": null
}
```

**On failure (machine not found):** `404 Not Found`
**On pipeline error:**
```json
{ "success": false, "result": null, "error": "Gemini API call timed out after 30s" }
```

#### DiagnosisResult field reference

| Field | Type | Values |
|---|---|---|
| `machine_id` | string | — |
| `timestamp` | string | ISO 8601 UTC |
| `diagnosis` | string | One sentence root cause |
| `recommended_action` | string | Step-by-step technician action |
| `severity` | string | `"low"` `"medium"` `"high"` `"critical"` |
| `confidence_score` | float | 0.0–1.0 |
| `supporting_evidence` | array | List of EvidenceItem |
| `source` | string | `"llm"` `"rules_fallback"` `"cache"` |
| `raw_sensor_snapshot` | object\|null | `{sensor_name: value, ...}` |

#### EvidenceItem field reference

| Field | Type | Values |
|---|---|---|
| `description` | string | Human-readable observation |
| `source` | string | `"sensor"` `"log"` `"error_code"` `"pattern"` |

---

## 4. Diagnosis Pipeline Flow

```
POST /diagnose  →  DiagnosisService.diagnose()
  │
  ├─ [1] Cache check (if force_refresh=False)
  │       Hit → return DiagnosisResult with source="cache"
  │       Miss → continue
  │
  ├─ [2] MachineService.get_raw_data(machine_id)
  │       None → raise ValueError → 404
  │
  ├─ [3] RulesEngine.evaluate(raw_data)
  │       High-confidence match (≥0.85) → return DiagnosisResult, source="rules_fallback"
  │       No match → collect soft hints via evaluate_all()
  │
  ├─ [4] PromptBuilder.build(machine_id, raw_data, include_logs, rule_hints)
  │       Constructs full prompt with sensor data, errors, logs, hints, JSON schema instruction
  │
  ├─ [5] LLMClient.generate(prompt)
  │       Success → raw text response
  │       Failure/timeout → fall back to best rule match, else generic fallback
  │
  ├─ [6] ResponseParser.parse(raw_text, machine_id, sensor_snapshot)
  │       Extracts JSON → DiagnosisResult with source="llm"
  │       Parse failure → DiagnosisResult with source="rules_fallback"
  │
  └─ [7] CacheService.set(machine_id, result) → return result
```

---

## 5. Data Directory Structure

```
backend/data/
├── error_codes.json          — global error code reference dictionary
└── machines/
    └── <machine_id>/         — directory name IS the machine_id
        ├── info.json         — REQUIRED: static metadata
        ├── sensors.json      — REQUIRED: current sensor readings array
        ├── errors.json       — OPTIONAL: recent error code strings (array of strings)
        └── logs.txt          — OPTIONAL: recent log lines (last 50 lines used)
```

### info.json schema
```json
{
  "name": "string",
  "type": "string",
  "location": "string"
}
```

### sensors.json schema
```json
[
  {
    "name": "string",
    "value": 0.0,
    "unit": "string",
    "threshold_warning": 0.0,
    "threshold_critical": 0.0,
    "status": "normal | warning | critical"
  }
]
```

### errors.json schema
```json
["ERROR_CODE: Description string", "..."]
```

### Pre-loaded machines

| machine_id | Name | Type | Scenario |
|---|---|---|---|
| `conveyor_1` | Conveyor Belt 1 | conveyor | All normal — healthy baseline |
| `conveyor_2` | Conveyor Belt 2 | conveyor | Temperature warning |
| `robotic_arm_1` | Robotic Arm 1 | robotic_arm | Critical joint temperature + multiple warnings |
| `pump_4` | Hydraulic Pump 4 | pump | Critical pressure + reduced flow |
| `compressor_2` | Air Compressor 2 | compressor | Elevated vibration + motor current warning |

---

## 6. LLM Abstraction Contract

All LLM backends must extend `app/llm/base.py::BaseLLMClient`:

```python
class BaseLLMClient(ABC):
    async def generate(self, prompt: str) -> str:
        """
        Generate a response. Returns raw text.
        Raises RuntimeError on failure or timeout.
        """
        ...

    def is_available(self) -> bool:
        """Return True if configured and ready. Synchronous."""
        ...
```

**Available implementations:**

| Class | File | Used when |
|---|---|---|
| `GeminiClient` | `app/llm/gemini_client.py` | `USE_MOCK_LLM=false` and `GEMINI_API_KEY` set |
| `MockLLMClient` | `app/llm/mock_client.py` | `USE_MOCK_LLM=true` (all tests) |

**Selection logic** (in `app/diagnosis/pipeline.py::_get_llm_client()`):
```python
if settings.USE_MOCK_LLM:
    return MockLLMClient()
return GeminiClient()
```

**To add a new LLM provider:** Subclass `BaseLLMClient`, implement both methods, update `_get_llm_client()`.

---

## 7. Caching Strategy

**Implementation:** `app/services/cache_service.py::CacheService`
**Type:** In-process Python dict with TTL expiry
**Key:** `machine_id` (string)
**TTL:** `settings.CACHE_TTL_SECONDS` (default: 300 seconds / 5 minutes)

### Cache lifecycle

```
set(machine_id, result)  →  stores (result, time.time() + TTL)
get(machine_id)          →  returns result if not expired, else None and evicts entry
invalidate(machine_id)   →  removes entry
clear()                  →  flushes all entries (used in tests)
```

### Cache bypass

Client sends `force_refresh: true` in `POST /diagnose` request body. This skips the cache read but DOES write the new result back to cache afterward.

### Limitations (by design for demo scope)

- Single-process only (no Redis, no shared state across workers)
- No persistence across restarts
- One cache instance per `DiagnosisService` instance

---

## 8. Fallback Behavior Specification

The system must NEVER return an unhandled 500 error from `/diagnose`. All failures degrade gracefully:

| Failure scenario | Fallback behavior |
|---|---|
| Machine not found | `404 Not Found` (raises `ValueError`) |
| High-confidence rule fires | Return `rules_fallback` result immediately; skip LLM |
| LLM timeout | Use best rule match if available; else return generic `MEDIUM` severity result |
| LLM API error | Same as timeout |
| LLM returns unparseable JSON | `ResponseParser` returns `rules_fallback` result with `confidence=0.3` |
| No rules match + LLM fails | Return generic fallback: "Unable to complete automated diagnosis" |
| `GEMINI_API_KEY` missing | `GeminiClient.__init__` raises `RuntimeError` → pipeline catches → fallback |

### Fallback result properties

- `source`: always `"rules_fallback"` (never `"llm"` or `"cache"`)
- `severity`: matches rule severity, or `"medium"` for generic fallback
- `confidence_score`: from rule match, or `0.2` for generic fallback, or `0.3` for parse failure

---

## 9. Frontend Component Tree

```
App
├── Sidebar
│   └── MachineSelector
│       props: { selectedMachineId, onSelect, machines, loading, error }
│       data:  useMachines() → GET /machines/
│
└── Main
    ├── MachineStatus
    │   props: { machine: MachineInfo }
    │   data:  useMachine(selectedMachineId) → GET /machines/:id
    │
    ├── SensorDisplay
    │   props: { sensors: SensorReading[] }
    │   data:  from MachineInfo.sensors
    │
    ├── LogsPanel
    │   props: { errors: string[] }
    │   data:  from MachineInfo.recent_errors
    │
    └── DiagnosisCard
        props: { machineId, result, loading, error, onRunDiagnosis }
        data:  useDiagnosis() → POST /diagnose
```

### Component prop contracts

#### MachineSelector
```typescript
interface MachineSelectorProps {
  selectedMachineId: string | null
  onSelect: (machineId: string) => void
  machines: MachineListItem[]
  loading: boolean
  error: string | null
}
```

#### MachineStatus
```typescript
interface MachineStatusProps {
  machine: MachineInfo
}
```

#### SensorDisplay
```typescript
interface SensorDisplayProps {
  sensors: SensorReading[]
}
```

#### LogsPanel
```typescript
interface LogsPanelProps {
  errors: string[]
}
```

#### DiagnosisCard
```typescript
interface DiagnosisCardProps {
  machineId: string
  result: DiagnosisResult | null
  loading: boolean
  error: string | null
  onRunDiagnosis: (forceRefresh: boolean) => void
}
```

#### LoadingSpinner
```typescript
interface LoadingSpinnerProps {
  size?: number      // px, default 32
  message?: string   // optional label below spinner
}
```

### Custom hooks

All in `frontend/src/hooks/`:

| Hook | Return type | Purpose |
|---|---|---|
| `useMachines()` | `{ data, loading, error, refetch }` | Fetch all machines |
| `useMachine(id)` | `{ data, loading, error, refetch }` | Fetch single machine detail |
| `useDiagnosis()` | `{ data, loading, error, diagnose }` | Trigger + track diagnosis |

### API client

All HTTP calls go through `frontend/src/api/index.ts`:

| Function | Method + Path | Description |
|---|---|---|
| `fetchMachines()` | `GET /machines/` | Returns `MachineListItem[]` |
| `fetchMachine(id)` | `GET /machines/:id` | Returns `MachineInfo` |
| `runDiagnosis(req)` | `POST /diagnose` | Returns `DiagnosisResponse` |

Vite dev-server proxy forwards `/machines` and `/diagnose` to `http://localhost:8000`.

---

## 10. Environment Variables

All in `backend/.env` (copy from `.env.example`):

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | Yes (for live LLM) | — | Google AI Studio key |
| `GEMINI_MODEL` | No | `gemini-1.5-flash` | Gemini model ID |
| `USE_MOCK_LLM` | No | `false` | `true` → use MockLLMClient |
| `CACHE_TTL_SECONDS` | No | `300` | Cache expiry in seconds |
| `DEBUG` | No | `false` | FastAPI debug mode |

---

## 11. Running the Project

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # edit GEMINI_API_KEY or set USE_MOCK_LLM=true
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev               # starts on http://localhost:5173
```

### Tests
```bash
cd backend
pytest tests/ -v
```

---

## 12. Module Responsibilities (for agent handoff)

| Module | Owner agent | Responsibility |
|---|---|---|
| `app/schemas/` | Architect | Pydantic schemas — DO NOT modify without updating frontend types |
| `app/config.py` | Architect | Settings — add new env vars here |
| `app/main.py` | Architect | App bootstrap and CORS |
| `app/routes/machines.py` | Backend Agent | List and detail endpoints |
| `app/routes/diagnosis.py` | Backend Agent | Diagnosis endpoint |
| `app/services/machine_service.py` | Backend Agent | Disk reads, data loading |
| `app/services/diagnosis_service.py` | Backend Agent | Pipeline orchestration |
| `app/services/cache_service.py` | Backend Agent | TTL cache |
| `app/diagnosis/rules_engine.py` | Backend Agent | Deterministic rules |
| `app/diagnosis/pipeline.py` | Backend Agent | Pipeline flow |
| `app/diagnosis/prompt_builder.py` | Backend Agent | LLM prompt construction |
| `app/diagnosis/response_parser.py` | Backend Agent | LLM response extraction |
| `app/llm/base.py` | Backend Agent | LLM interface contract |
| `app/llm/gemini_client.py` | Backend Agent | Gemini SDK wrapper |
| `app/llm/mock_client.py` | Backend Agent | Test mock |
| `backend/data/machines/` | Data Agent | Machine JSON data files |
| `frontend/src/types/` | Frontend Agent | TS types — must mirror Pydantic schemas |
| `frontend/src/api/` | Frontend Agent | HTTP client |
| `frontend/src/hooks/` | Frontend Agent | React data hooks |
| `frontend/src/components/` | Frontend Agent | UI components |
| `backend/tests/` | Test Agent | pytest test suite |
| `frontend/tests/` | Test Agent | Vitest test suite |

---

## 13. Key Invariants (rules all agents must preserve)

1. **Schema is the contract.** The Pydantic models in `app/schemas/` and TypeScript types in `frontend/src/types/index.ts` must stay in sync. Never add a field to one without adding it to the other.

2. **Pipeline always returns a result.** `DiagnosisPipeline.run()` must never raise — it must always return a `DiagnosisResult`, falling back as described in Section 8.

3. **No direct LLM calls outside the pipeline.** All LLM interactions go through `BaseLLMClient`. No agent should import `google.generativeai` outside of `app/llm/gemini_client.py`.

4. **Tests use MockLLMClient.** `conftest.py` sets `USE_MOCK_LLM=true`. No test should require a real Gemini API key.

5. **Data directory is read-only at runtime.** The application only reads from `data/machines/`. It never writes there. No agent should add write logic to `MachineService`.

6. **machine_id is the filesystem directory name.** The ID used in URLs, cache keys, and schema fields must exactly match the directory name under `data/machines/`.

7. **Cache TTL is configurable.** Always use `settings.CACHE_TTL_SECONDS` — never hardcode a TTL value.
