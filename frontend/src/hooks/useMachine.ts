import { useState, useEffect, useCallback } from 'react'
import { fetchMachine } from '../api'
import type { MachineInfo } from '../types'

interface UseMachineResult {
  data: MachineInfo | null
  loading: boolean
  error: string | null
  refetch: () => void
}

export function useMachine(machineId: string | null): UseMachineResult {
  const [data, setData] = useState<MachineInfo | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!machineId) return
    setLoading(true)
    setError(null)
    try {
      const machine = await fetchMachine(machineId)
      setData(machine)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch machine')
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [machineId])

  useEffect(() => { load() }, [load])

  return { data, loading, error, refetch: load }
}
