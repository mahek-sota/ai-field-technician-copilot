/**
 * LoadingSpinner — simple CSS-animated loading indicator.
 *
 * Props contract (per ARCHITECTURE.md):
 *   - size?: number — diameter in px (default: 32)
 *   - message?: string — optional label rendered below the spinner
 */
import React from 'react'

interface LoadingSpinnerProps {
  size?: number
  message?: string
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ size = 32, message }) => {
  const thickness = Math.max(2, Math.round(size / 10))
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: 16 }}>
      <div
        role="status"
        aria-label={message ?? 'Loading'}
        style={{
          width: size,
          height: size,
          borderRadius: '50%',
          border: `${thickness}px solid #e0e0e0`,
          borderTopColor: '#1976d2',
          animation: 'spin 0.75s linear infinite',
        }}
      />
      {message && (
        <p style={{ margin: '10px 0 0', fontSize: 13, color: '#666' }}>{message}</p>
      )}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

export default LoadingSpinner
