from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DiagnosisRequest(BaseModel):
    machine_id: str
    include_logs: bool = True
    force_refresh: bool = False


class EvidenceItem(BaseModel):
    description: str
    source: str  # "sensor", "log", "error_code", "pattern"


class DiagnosisResult(BaseModel):
    machine_id: str
    timestamp: str
    diagnosis: str
    recommended_action: str
    severity: SeverityLevel
    confidence_score: float  # 0.0 to 1.0
    supporting_evidence: List[EvidenceItem]
    source: str  # "llm", "rules_fallback", "cache"
    raw_sensor_snapshot: Optional[dict] = None


class DiagnosisResponse(BaseModel):
    success: bool
    result: Optional[DiagnosisResult] = None
    error: Optional[str] = None
