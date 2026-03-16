import { useState, useCallback } from 'react'
import { runDiagnosis } from '../api'
import type { DiagnosisRequest, DiagnosisResult } from '../types'

interface UseDiagnosisResult {
  data: DiagnosisResult | null
  loading: boolean
  error: string | null
  diagnose: (request: DiagnosisRequest) => Promise<void>
}

export function useDiagnosis(): UseDiagnosisResult {
  const [data, setData] = useState<DiagnosisResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const diagnose = useCallback(async (request: DiagnosisRequest) => {
    setLoading(true)
    setError(null)
    try {
      const response = await runDiagnosis(request)
      if (response.success && response.result) {
        setData(response.result)
      } else {
        setError(response.error ?? 'Diagnosis failed')
        setData(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Diagnosis request failed')
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [])

  return { data, loading, error, diagnose }
}
