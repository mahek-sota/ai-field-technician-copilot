from fastapi import APIRouter, HTTPException
from app.schemas.diagnosis import DiagnosisRequest, DiagnosisResponse
from app.services.diagnosis_service import DiagnosisService

router = APIRouter()
_service = DiagnosisService()


@router.post("/diagnose", response_model=DiagnosisResponse)
async def diagnose(request: DiagnosisRequest):
    """
    Run the full diagnosis pipeline for a machine.

    Request body: DiagnosisRequest
      - machine_id: str          — which machine to diagnose
      - include_logs: bool       — whether to pull recent log lines (default True)
      - force_refresh: bool      — bypass cache and re-run pipeline (default False)

    Response: DiagnosisResponse
      - success: bool
      - result: DiagnosisResult | null
          - machine_id, timestamp, diagnosis, recommended_action
          - severity: SeverityLevel  ("low" | "medium" | "high" | "critical")
          - confidence_score: float  (0.0–1.0)
          - supporting_evidence: List[EvidenceItem]
          - source: str              ("llm" | "rules_fallback" | "cache")
          - raw_sensor_snapshot: dict | null
      - error: str | null

    Pipeline order:
      1. Check cache (unless force_refresh=True)
      2. Load machine data from disk
      3. Run rules engine — if a high-confidence rule fires, short-circuit and return
      4. Build LLM prompt and call Gemini
      5. Parse LLM response into DiagnosisResult
      6. Store result in cache
      7. Return result

    On any unhandled exception, returns DiagnosisResponse(success=False, error=<message>).
    """
    try:
        result = await _service.diagnose(request)
        return DiagnosisResponse(success=True, result=result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        return DiagnosisResponse(success=False, error=str(exc))
