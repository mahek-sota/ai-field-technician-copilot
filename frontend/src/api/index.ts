/**
 * API client — all backend calls go through this module.
 *
 * Base URL is proxied via Vite dev server to http://localhost:8000
 * In production, set VITE_API_BASE_URL env var.
 */
import type { MachineListItem, MachineInfo, DiagnosisRequest, DiagnosisResponse } from '../types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`HTTP ${response.status}: ${text}`)
  }
  return response.json() as Promise<T>
}

/**
 * GET /machines/
 * Returns summary list of all machines.
 */
export async function fetchMachines(): Promise<MachineListItem[]> {
  return request<MachineListItem[]>('/machines/')
}

/**
 * GET /machines/:machine_id
 * Returns full machine detail including sensors and recent errors.
 */
export async function fetchMachine(machineId: string): Promise<MachineInfo> {
  return request<MachineInfo>(`/machines/${machineId}`)
}

/**
 * POST /diagnose
 * Runs the diagnosis pipeline for a machine.
 */
export async function runDiagnosis(payload: DiagnosisRequest): Promise<DiagnosisResponse> {
  return request<DiagnosisResponse>('/diagnose', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

/**
 * GET /machines/:machine_id/history
 * Returns past diagnosis results for a machine.
 */
export async function fetchHistory(machineId: string): Promise<import('../types').DiagnosisResult[]> {
  return request(`/machines/${machineId}/history`)
}
