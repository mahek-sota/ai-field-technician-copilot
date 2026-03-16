import { useState, useEffect, useCallback } from 'react'
import type { MachineInfo } from './types'
import { useMachines } from './hooks/useMachines'
import { useDiagnosis } from './hooks/useDiagnosis'
import { fetchMachine } from './api'
import MachineSelector from './components/MachineSelector/MachineSelector'
import MachineStatus from './components/MachineStatus/MachineStatus'
import SensorDisplay from './components/SensorDisplay/SensorDisplay'
import LogsPanel from './components/LogsPanel/LogsPanel'
import DiagnosisCard from './components/DiagnosisCard/DiagnosisCard'

function App() {
  const { data: machines, loading: machinesLoading, error: machinesError } = useMachines()
  const [selectedMachineId, setSelectedMachineId] = useState<string | null>(null)
  const [machineInfo, setMachineInfo] = useState<MachineInfo | null>(null)
  const [machineLoading, setMachineLoading] = useState(false)
  const [machineError, setMachineError] = useState<string | null>(null)
  const { data: diagnosisResult, loading: diagnosisLoading, error: diagnosisError, diagnose } = useDiagnosis()

  const loadMachine = useCallback(async (machineId: string) => {
    setMachineLoading(true)
    setMachineError(null)
    setMachineInfo(null)
    try {
      const info = await fetchMachine(machineId)
      setMachineInfo(info)
    } catch (err) {
      setMachineError(err instanceof Error ? err.message : 'Failed to load machine')
    } finally {
      setMachineLoading(false)
    }
  }, [])

  const handleSelectMachine = useCallback((machineId: string) => {
    setSelectedMachineId(machineId)
    loadMachine(machineId)
  }, [loadMachine])

  const handleRunDiagnosis = useCallback((forceRefresh: boolean) => {
    if (!selectedMachineId) return
    diagnose({ machine_id: selectedMachineId, include_logs: true, force_refresh: forceRefresh })
  }, [selectedMachineId, diagnose])

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: "'Segoe UI', system-ui, sans-serif", background: '#f5f6fa' }}>

      {/* Sidebar */}
      <aside style={{
        width: 270,
        background: '#1a1a2e',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
      }}>
        {/* Sidebar Header */}
        <div style={{ padding: '20px 16px 16px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
            <span style={{ fontSize: 20 }}>⚙</span>
            <span style={{ color: '#fff', fontWeight: 700, fontSize: 15 }}>Field Technician Copilot</span>
          </div>
          <div style={{ color: 'rgba(255,255,255,0.45)', fontSize: 12 }}>AI-powered machine diagnostics</div>
        </div>

        {/* Machine List */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px 8px' }}>
          <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: 11, fontWeight: 600, letterSpacing: 1, padding: '0 8px 8px', textTransform: 'uppercase' }}>
            Machines
          </div>
          <MachineSelector
            selectedMachineId={selectedMachineId}
            onSelect={handleSelectMachine}
            machines={machines}
            loading={machinesLoading}
            error={machinesError}
          />
        </div>

        {/* Sidebar Footer */}
        <div style={{ padding: '12px 16px', borderTop: '1px solid rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.3)', fontSize: 11 }}>
          {machines.length > 0 ? `${machines.length} machines monitored` : 'Connecting...'}
        </div>
      </aside>

      {/* Main Content */}
      <main style={{ flex: 1, overflowY: 'auto', padding: 24 }}>

        {/* Page Header */}
        <div style={{ marginBottom: 24 }}>
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#1a1a2e' }}>
            {machineInfo ? machineInfo.name : 'AI Field Technician Copilot'}
          </h1>
          <p style={{ margin: '4px 0 0', color: '#888', fontSize: 13 }}>
            {machineInfo
              ? `${machineInfo.type} · ${machineInfo.location}`
              : 'Select a machine from the sidebar to begin diagnostics'}
          </p>
        </div>

        {/* No machine selected */}
        {!selectedMachineId && (
          <div style={{
            textAlign: 'center',
            padding: '80px 40px',
            background: '#fff',
            borderRadius: 12,
            border: '1px solid #e0e0e0',
          }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>🔧</div>
            <h2 style={{ color: '#1a1a2e', margin: '0 0 8px' }}>Select a Machine</h2>
            <p style={{ color: '#888', margin: 0, maxWidth: 380, display: 'inline-block' }}>
              Choose a machine from the sidebar to view its sensor data, logs, and run an AI-powered diagnosis.
            </p>
          </div>
        )}

        {/* Machine loading state */}
        {selectedMachineId && machineLoading && (
          <div style={{ textAlign: 'center', padding: 60, color: '#666' }}>
            Loading machine data...
          </div>
        )}

        {/* Machine error */}
        {selectedMachineId && machineError && (
          <div style={{
            background: '#ffebee',
            color: '#c62828',
            padding: '16px 20px',
            borderRadius: 8,
            marginBottom: 20,
            fontSize: 14,
          }}>
            {machineError}
          </div>
        )}

        {/* Machine content */}
        {machineInfo && !machineLoading && (
          <div style={{ display: 'grid', gap: 20 }}>

            {/* Status + Sensors row */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 20 }}>
              <MachineStatus machine={machineInfo} />
              <SensorDisplay sensors={machineInfo.sensors} />
            </div>

            {/* Logs */}
            <LogsPanel errors={machineInfo.recent_errors} />

            {/* Diagnosis */}
            <DiagnosisCard
              machineId={machineInfo.machine_id}
              result={diagnosisResult}
              loading={diagnosisLoading}
              error={diagnosisError}
              onRunDiagnosis={handleRunDiagnosis}
            />
          </div>
        )}
      </main>
    </div>
  )
}

export default App
