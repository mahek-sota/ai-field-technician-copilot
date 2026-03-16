/**
 * SensorDisplay — responsive grid of sensor reading cards.
 *
 * Props contract (per ARCHITECTURE.md):
 *   - sensors: SensorReading[] — from MachineInfo.sensors
 *
 * Behavior:
 *   - One card per sensor; cards color-coded by status (normal/warning/critical)
 *   - Shows: name, value, unit, status badge
 *   - If thresholds present, shows them in small text below value
 */
import React from 'react'
import type { SensorReading } from '../../types'

interface SensorDisplayProps {
  sensors: SensorReading[]
}

const BORDER_COLOR: Record<string, string> = {
  normal:   '#e0e0e0',
  warning:  '#ff9800',
  critical: '#f44336',
}

const BADGE_STYLE: Record<string, { bg: string; color: string }> = {
  normal:   { bg: '#e8f5e9', color: '#2e7d32' },
  warning:  { bg: '#fff3e0', color: '#e65100' },
  critical: { bg: '#ffebee', color: '#c62828' },
}

const SensorDisplay: React.FC<SensorDisplayProps> = ({ sensors }) => {
  if (sensors.length === 0) {
    return <p style={{ color: '#888', marginBottom: 20 }}>No sensor data available.</p>
  }

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
      gap: 12,
      marginBottom: 20,
    }}>
      {sensors.map((s) => {
        const border = BORDER_COLOR[s.status] ?? '#e0e0e0'
        const badge = BADGE_STYLE[s.status] ?? BADGE_STYLE.normal
        return (
          <div key={s.name} style={{
            padding: 14,
            borderRadius: 8,
            border: `2px solid ${border}`,
            background: '#fff',
          }}>
            <div style={{ fontSize: 11, color: '#888', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              {s.name}
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, lineHeight: 1.2 }}>
              {s.value}
              <span style={{ fontSize: 13, fontWeight: 400, marginLeft: 4, color: '#555' }}>{s.unit}</span>
            </div>
            <span style={{
              display: 'inline-block',
              marginTop: 6,
              fontSize: 11,
              padding: '2px 8px',
              borderRadius: 10,
              background: badge.bg,
              color: badge.color,
              fontWeight: 600,
            }}>
              {s.status}
            </span>
            {(s.threshold_warning != null || s.threshold_critical != null) && (
              <div style={{ fontSize: 10, color: '#bbb', marginTop: 6 }}>
                {s.threshold_warning != null && <span>warn: {s.threshold_warning} </span>}
                {s.threshold_critical != null && <span>crit: {s.threshold_critical}</span>}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

export default SensorDisplay
