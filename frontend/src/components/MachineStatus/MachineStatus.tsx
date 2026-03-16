/**
 * MachineStatus — header card showing machine name, type, location, and overall status.
 *
 * Props contract (per ARCHITECTURE.md):
 *   - machine: MachineInfo — full machine data object
 *
 * Behavior:
 *   - Large status badge, color-coded by MachineStatus value
 *   - Displays last_updated as localized date/time string
 *   - Shows machine_id, name, type, location
 */
import React from 'react'
import type { MachineInfo } from '../../types'

interface MachineStatusProps {
  machine: MachineInfo
}

const STATUS_STYLES: Record<string, { bg: string; color: string }> = {
  normal:   { bg: '#e8f5e9', color: '#2e7d32' },
  warning:  { bg: '#fff3e0', color: '#e65100' },
  critical: { bg: '#ffebee', color: '#c62828' },
  offline:  { bg: '#f5f5f5', color: '#757575' },
}

const MachineStatus: React.FC<MachineStatusProps> = ({ machine }) => {
  const sc = STATUS_STYLES[machine.status] ?? STATUS_STYLES.offline

  return (
    <div style={{
      padding: 20,
      borderRadius: 8,
      border: '1px solid #e0e0e0',
      marginBottom: 20,
      background: '#fff',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
    }}>
      <div>
        <h2 style={{ margin: 0, fontSize: 20 }}>{machine.name}</h2>
        <p style={{ margin: '4px 0 2px', color: '#666', fontSize: 14 }}>
          {machine.type} &middot; {machine.location}
        </p>
        <p style={{ margin: 0, color: '#aaa', fontSize: 12 }}>
          ID: {machine.machine_id} &nbsp;&middot;&nbsp; Updated: {new Date(machine.last_updated).toLocaleString()}
        </p>
      </div>
      <span style={{
        padding: '6px 18px',
        borderRadius: 20,
        background: sc.bg,
        color: sc.color,
        fontWeight: 700,
        fontSize: 14,
        textTransform: 'uppercase',
        letterSpacing: 1,
        whiteSpace: 'nowrap',
      }}>
        {machine.status}
      </span>
    </div>
  )
}

export default MachineStatus
