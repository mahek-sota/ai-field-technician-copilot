/**
 * DiagnosisCard — shows the AI diagnosis result and triggers diagnosis run.
 *
 * Props contract (per ARCHITECTURE.md):
 *   - machineId: string
 *   - result: DiagnosisResult | null
 *   - loading: boolean
 *   - error: string | null
 *   - onRunDiagnosis: (forceRefresh: boolean) => void
 *
 * Behavior:
 *   - "Run Diagnosis" button calls onRunDiagnosis(forceRefresh)
 *   - "Force refresh" checkbox bypasses server-side cache
 *   - Shows severity badge, confidence score, diagnosis text, recommended action,
 *     supporting evidence list, source tag, and timestamp
 *   - Loading state disables button and shows spinner text
 *   - Error state shows red error box
 */
import React, { useState } from 'react'
import type { DiagnosisResult } from '../../types'

interface DiagnosisCardProps {
  machineId: string
  result: DiagnosisResult | null
  loading?: boolean
  error?: string | null
  onRunDiagnosis?: (forceRefresh: boolean) => void
}

const SEVERITY_STYLES: Record<string, { bg: string; color: string }> = {
  low:      { bg: '#e8f5e9', color: '#2e7d32' },
  medium:   { bg: '#fff3e0', color: '#e65100' },
  high:     { bg: '#fff8e1', color: '#f57f17' },
  critical: { bg: '#ffebee', color: '#c62828' },
}

const DiagnosisCard: React.FC<DiagnosisCardProps> = ({
  machineId,
  result,
  loading = false,
  error = null,
  onRunDiagnosis,
}) => {
  const [forceRefresh, setForceRefresh] = useState(false)

  return (
    <div style={{
      borderRadius: 8,
      border: '1px solid #e0e0e0',
      background: '#fff',
      padding: 20,
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h3 style={{ margin: 0 }}>AI Diagnosis</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <label style={{ fontSize: 13, color: '#666', cursor: 'pointer', userSelect: 'none' }}>
            <input
              type="checkbox"
              checked={forceRefresh}
              onChange={(e) => setForceRefresh(e.target.checked)}
              style={{ marginRight: 5 }}
            />
            Force refresh
          </label>
          <button
            onClick={() => onRunDiagnosis?.(forceRefresh)}
            disabled={loading}
            style={{
              padding: '8px 20px',
              background: loading ? '#90caf9' : '#1976d2',
              color: '#fff',
              border: 'none',
              borderRadius: 6,
              cursor: loading ? 'not-allowed' : 'pointer',
              fontWeight: 600,
              fontSize: 14,
            }}
          >
            {loading ? 'Diagnosing...' : 'Run Diagnosis'}
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div style={{
          background: '#ffebee',
          color: '#c62828',
          padding: '10px 14px',
          borderRadius: 6,
          fontSize: 13,
          marginBottom: 12,
        }}>
          {error}
        </div>
      )}

      {/* Empty state */}
      {!result && !loading && !error && (
        <p style={{ color: '#aaa', textAlign: 'center', margin: '24px 0', fontSize: 14 }}>
          Click "Run Diagnosis" to analyze this machine with AI.
        </p>
      )}

      {/* Result */}
      {result && (() => {
        const sc = SEVERITY_STYLES[result.severity] ?? SEVERITY_STYLES.medium
        return (
          <div>
            {/* Severity + meta */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <span style={{
                padding: '5px 14px',
                borderRadius: 14,
                fontSize: 12,
                fontWeight: 700,
                letterSpacing: 1,
                background: sc.bg,
                color: sc.color,
              }}>
                {result.severity.toUpperCase()}
              </span>
              <span style={{ fontSize: 12, color: '#aaa' }}>
                {result.source} &middot; {Math.round(result.confidence_score * 100)}% confidence
              </span>
            </div>

            {/* Diagnosis */}
            <h4 style={{ margin: '0 0 6px', fontSize: 13, color: '#555', textTransform: 'uppercase', letterSpacing: 0.5 }}>Diagnosis</h4>
            <p style={{ margin: '0 0 16px', fontSize: 15 }}>{result.diagnosis}</p>

            {/* Recommended action */}
            <h4 style={{ margin: '0 0 6px', fontSize: 13, color: '#555', textTransform: 'uppercase', letterSpacing: 0.5 }}>Recommended Action</h4>
            <p style={{ margin: '0 0 16px', fontSize: 14, background: '#f9f9f9', padding: '10px 14px', borderRadius: 6, borderLeft: '3px solid #1976d2' }}>
              {result.recommended_action}
            </p>

            {/* Evidence */}
            {result.supporting_evidence.length > 0 && (
              <>
                <h4 style={{ margin: '0 0 6px', fontSize: 13, color: '#555', textTransform: 'uppercase', letterSpacing: 0.5 }}>Supporting Evidence</h4>
                <ul style={{ margin: '0 0 16px', paddingLeft: 18 }}>
                  {result.supporting_evidence.map((ev, i) => (
                    <li key={i} style={{ fontSize: 13, marginBottom: 4 }}>
                      <span style={{
                        fontSize: 10,
                        padding: '1px 6px',
                        borderRadius: 8,
                        background: '#f0f0f0',
                        color: '#666',
                        marginRight: 6,
                      }}>
                        {ev.source}
                      </span>
                      {ev.description}
                    </li>
                  ))}
                </ul>
              </>
            )}

            {/* Footer */}
            <p style={{ margin: 0, fontSize: 11, color: '#ccc' }}>
              {new Date(result.timestamp).toLocaleString()} &middot; {machineId}
            </p>
          </div>
        )
      })()}
    </div>
  )
}

export default DiagnosisCard
