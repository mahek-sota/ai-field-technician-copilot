// ============================================================
// Shared TypeScript types — mirror the Pydantic schemas exactly
// ============================================================

export type MachineStatus = 'normal' | 'warning' | 'critical' | 'offline'

export type SeverityLevel = 'low' | 'medium' | 'high' | 'critical'

export interface SensorReading {
  name: string
  value: number
  unit: string
  threshold_warning: number | null
  threshold_critical: number | null
  status: string
}

export interface MachineListItem {
  machine_id: string
  name: string
  type: string
  status: MachineStatus
  location: string
}

export interface MachineInfo {
  machine_id: string
  name: string
  type: string
  location: string
  status: MachineStatus
  last_updated: string
  sensors: SensorReading[]
  recent_errors: string[]
}

export interface EvidenceItem {
  description: string
  source: 'sensor' | 'log' | 'error_code' | 'pattern'
}

export interface DiagnosisResult {
  machine_id: string
  timestamp: string
  diagnosis: string
  recommended_action: string
  severity: SeverityLevel
  confidence_score: number
  supporting_evidence: EvidenceItem[]
  source: 'llm' | 'rules_fallback' | 'cache'
  raw_sensor_snapshot: Record<string, number> | null
}

export interface DiagnosisResponse {
  success: boolean
  result: DiagnosisResult | null
  error: string | null
}

export interface DiagnosisRequest {
  machine_id: string
  include_logs?: boolean
  force_refresh?: boolean
}
