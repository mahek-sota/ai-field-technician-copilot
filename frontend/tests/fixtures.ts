import type { MachineListItem, MachineInfo, DiagnosisResult, DiagnosisResponse } from '../src/types'

export const mockMachineList: MachineListItem[] = [
  { machine_id: 'conveyor_1', name: 'Conveyor Belt Alpha', type: 'Conveyor Belt', status: 'normal', location: 'Warehouse Section A' },
  { machine_id: 'conveyor_2', name: 'Conveyor Belt Beta', type: 'Conveyor Belt', status: 'warning', location: 'Production Floor B' },
  { machine_id: 'robotic_arm_1', name: 'Robotic Arm Delta', type: 'Robotic Arm', status: 'critical', location: 'Assembly Station C' },
  { machine_id: 'pump_4', name: 'Hydraulic Pump Gamma', type: 'Hydraulic Pump', status: 'critical', location: 'Hydraulic Room D' },
  { machine_id: 'compressor_2', name: 'Air Compressor Epsilon', type: 'Air Compressor', status: 'warning', location: 'Utility Room E' },
]

export const mockMachineInfo: MachineInfo = {
  machine_id: 'conveyor_2',
  name: 'Conveyor Belt Beta',
  type: 'Conveyor Belt',
  location: 'Production Floor B',
  status: 'warning',
  last_updated: '2026-03-14T08:30:00Z',
  sensors: [
    { name: 'temperature', value: 78.5, unit: '°C', threshold_warning: 70.0, threshold_critical: 85.0, status: 'warning' },
    { name: 'vibration', value: 2.1, unit: 'mm/s', threshold_warning: 3.0, threshold_critical: 5.0, status: 'normal' },
    { name: 'motor_current', value: 16.8, unit: 'A', threshold_warning: 18.0, threshold_critical: 22.0, status: 'normal' },
  ],
  recent_errors: ['W_TEMP_HIGH: Belt temperature above warning threshold', 'W_MOTOR_STRESS: Motor load elevated'],
}

export const mockDiagnosisResult: DiagnosisResult = {
  machine_id: 'conveyor_2',
  timestamp: '2026-03-14T09:00:00Z',
  diagnosis: 'Bearing wear detected due to elevated temperature and rising vibration trend.',
  recommended_action: 'Schedule immediate inspection of motor assembly. Replace bearing if wear confirmed.',
  severity: 'high',
  confidence_score: 0.83,
  supporting_evidence: [
    { description: 'Temperature at 78.5°C, above warning threshold of 70°C', source: 'sensor' },
    { description: 'Vibration level trending upward at 2.1 mm/s', source: 'sensor' },
    { description: 'W_TEMP_HIGH error occurred 3 times in past 48 hours', source: 'error_code' },
  ],
  source: 'llm',
  raw_sensor_snapshot: null,
}

export const mockCriticalDiagnosis: DiagnosisResult = {
  machine_id: 'robotic_arm_1',
  timestamp: '2026-03-14T09:05:00Z',
  diagnosis: 'Critical joint bearing failure. Immediate shutdown required.',
  recommended_action: 'Shut down immediately. Do not operate until bearing replaced.',
  severity: 'critical',
  confidence_score: 0.95,
  supporting_evidence: [
    { description: 'Joint temperature at 104.7°C, exceeds critical threshold', source: 'sensor' },
    { description: 'E_JOINT_TEMP_CRITICAL error occurred 5 times', source: 'error_code' },
  ],
  source: 'rules_fallback',
  raw_sensor_snapshot: null,
}

export const mockDiagnosisResponse: DiagnosisResponse = {
  success: true,
  result: mockDiagnosisResult,
  error: null,
}
