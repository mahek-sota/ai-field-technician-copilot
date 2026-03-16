/**
 * MachineSelector — displays a scrollable list of machines in the sidebar.
 *
 * Props contract (per ARCHITECTURE.md):
 *   - selectedMachineId: string | null — currently selected machine
 *   - onSelect: (machineId: string) => void — called when user clicks a machine
 *   - machines: MachineListItem[] — list from useMachines() hook
 *   - loading: boolean
 *   - error: string | null
 *
 * Behavior:
 *   - Status badge colors: normal=green, warning=orange, critical=red, offline=gray
 *   - Highlights the currently selected machine with blue left-border accent
 */
import React from 'react'
import type { MachineListItem } from '../../types'

interface MachineSelectorProps {
  selectedMachineId: string | null
  onSelect: (machineId: string) => void
  machines?: MachineListItem[]
  loading?: boolean
  error?: string | null
}

const MachineSelectorItem: React.FC<{
  machine: MachineListItem
  selected: boolean
  onSelect: (id: string) => void
}> = ({ machine, selected, onSelect }) => {
  const statusColors: Record<string, { bg: string; color: string }> = {
    normal: { bg: '#e8f5e9', color: '#2e7d32' },
    warning: { bg: '#fff3e0', color: '#e65100' },
    critical: { bg: '#ffebee', color: '#c62828' },
    offline: { bg: '#f5f5f5', color: '#757575' },
  }
  const sc = statusColors[machine.status] ?? statusColors.offline

  return (
    <li
      onClick={() => onSelect(machine.machine_id)}
      style={{
        padding: '10px 8px',
        cursor: 'pointer',
        borderRadius: 6,
        marginBottom: 4,
        background: selected ? '#e3f2fd' : 'transparent',
        borderLeft: selected ? '3px solid #1976d2' : '3px solid transparent',
      }}
    >
      <div style={{ fontWeight: 600, fontSize: 14 }}>{machine.name}</div>
      <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>
        {machine.type} · {machine.location}
      </div>
      <span style={{
        fontSize: 11,
        padding: '2px 6px',
        borderRadius: 10,
        background: sc.bg,
        color: sc.color,
      }}>
        {machine.status}
      </span>
    </li>
  )
}

const MachineSelector: React.FC<MachineSelectorProps> = ({
  selectedMachineId,
  onSelect,
  machines = [],
  loading = false,
  error = null,
}) => {
  if (loading) return <div style={{ padding: 8, color: '#666', fontSize: 13 }}>Loading machines...</div>
  if (error) return <div style={{ padding: 8, color: '#c62828', fontSize: 13 }}>Error: {error}</div>
  if (machines.length === 0) return <div style={{ padding: 8, color: '#999', fontSize: 13 }}>No machines found.</div>

  return (
    <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
      {machines.map((m) => (
        <MachineSelectorItem
          key={m.machine_id}
          machine={m}
          selected={selectedMachineId === m.machine_id}
          onSelect={onSelect}
        />
      ))}
    </ul>
  )
}

export default MachineSelector
