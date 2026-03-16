import { useState, useEffect, useCallback } from 'react'
import { fetchMachines } from '../api'
import type { MachineListItem } from '../types'

interface UseMachinesResult {
  data: MachineListItem[]
  loading: boolean
  error: string | null
  refetch: () => void
}

export function useMachines(): UseMachinesResult {
  const [data, setData] = useState<MachineListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const machines = await fetchMachines()
      setData(machines)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch machines')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  return { data, loading, error, refetch: load }
}
