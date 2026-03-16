/**
 * LogsPanel — collapsible panel showing recent error codes.
 *
 * Props contract (per ARCHITECTURE.md):
 *   - errors: string[] — MachineInfo.recent_errors
 *
 * Behavior:
 *   - Expanded by default; click header to collapse/expand
 *   - Empty state shows green "No recent errors" message
 *   - Error strings rendered in monospace, red text
 */
import React, { useState } from 'react'

interface LogsPanelProps {
  errors: string[]
}

const LogsPanel: React.FC<LogsPanelProps> = ({ errors }) => {
  const [expanded, setExpanded] = useState(true)

  return (
    <div style={{
      marginBottom: 20,
      borderRadius: 8,
      border: '1px solid #e0e0e0',
      background: '#fff',
      overflow: 'hidden',
    }}>
      <div
        onClick={() => setExpanded((v) => !v)}
        style={{
          padding: '12px 16px',
          cursor: 'pointer',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontWeight: 600,
          fontSize: 14,
          background: '#fafafa',
          borderBottom: expanded ? '1px solid #e0e0e0' : 'none',
        }}
      >
        <span>Recent Error Codes <span style={{ fontWeight: 400, color: '#999' }}>({errors.length})</span></span>
        <span style={{ fontSize: 12, color: '#999' }}>{expanded ? '▲' : '▼'}</span>
      </div>
      {expanded && (
        <div style={{ padding: 16 }}>
          {errors.length === 0 ? (
            <p style={{ margin: 0, color: '#2e7d32', fontSize: 13 }}>No recent errors.</p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {errors.map((err, i) => (
                <li
                  key={i}
                  style={{
                    fontFamily: 'monospace',
                    fontSize: 12,
                    padding: '5px 0',
                    borderBottom: i < errors.length - 1 ? '1px solid #f5f5f5' : 'none',
                    color: '#b71c1c',
                  }}
                >
                  {err}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}

export default LogsPanel
