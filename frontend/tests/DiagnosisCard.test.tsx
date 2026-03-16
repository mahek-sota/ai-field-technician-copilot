import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import DiagnosisCard from '../src/components/DiagnosisCard/DiagnosisCard'
import { mockDiagnosisResult, mockCriticalDiagnosis } from './fixtures'

describe('DiagnosisCard', () => {
  it('renders the Run Diagnosis button', () => {
    render(
      <DiagnosisCard machineId="conveyor_2" result={null} />
    )
    expect(screen.getByText('Run Diagnosis')).toBeInTheDocument()
  })

  it('shows empty state message when no result', () => {
    render(
      <DiagnosisCard machineId="conveyor_2" result={null} />
    )
    expect(screen.getByText(/click "run diagnosis"/i)).toBeInTheDocument()
  })

  it('renders diagnosis text when result is present', () => {
    render(
      <DiagnosisCard machineId="conveyor_2" result={mockDiagnosisResult} />
    )
    expect(screen.getByText(/bearing wear detected/i)).toBeInTheDocument()
  })

  it('renders recommended action', () => {
    render(
      <DiagnosisCard machineId="conveyor_2" result={mockDiagnosisResult} />
    )
    expect(screen.getByText(/schedule immediate inspection/i)).toBeInTheDocument()
  })

  it('renders severity badge', () => {
    render(
      <DiagnosisCard machineId="conveyor_2" result={mockDiagnosisResult} />
    )
    expect(screen.getByText('HIGH')).toBeInTheDocument()
  })

  it('renders confidence score as percentage', () => {
    render(
      <DiagnosisCard machineId="conveyor_2" result={mockDiagnosisResult} />
    )
    expect(screen.getByText(/83%/)).toBeInTheDocument()
  })

  it('renders all supporting evidence descriptions', () => {
    render(
      <DiagnosisCard machineId="conveyor_2" result={mockDiagnosisResult} />
    )
    expect(screen.getByText(/temperature at 78\.5°C/i)).toBeInTheDocument()
    expect(screen.getByText(/vibration level trending/i)).toBeInTheDocument()
    expect(screen.getByText(/W_TEMP_HIGH error/i)).toBeInTheDocument()
  })

  it('renders evidence source badges', () => {
    render(
      <DiagnosisCard machineId="conveyor_2" result={mockDiagnosisResult} />
    )
    const sensorBadges = screen.getAllByText('sensor')
    expect(sensorBadges.length).toBeGreaterThanOrEqual(2)
    expect(screen.getByText('error_code')).toBeInTheDocument()
  })

  it('renders source indicator (llm/rules_fallback)', () => {
    render(
      <DiagnosisCard machineId="conveyor_2" result={mockDiagnosisResult} />
    )
    expect(screen.getByText(/llm/i)).toBeInTheDocument()
  })

  it('renders CRITICAL badge for critical result', () => {
    render(
      <DiagnosisCard machineId="robotic_arm_1" result={mockCriticalDiagnosis} />
    )
    expect(screen.getByText('CRITICAL')).toBeInTheDocument()
  })

  it('shows 95% confidence for critical result', () => {
    render(
      <DiagnosisCard machineId="robotic_arm_1" result={mockCriticalDiagnosis} />
    )
    expect(screen.getByText(/95%/)).toBeInTheDocument()
  })

  it('shows loading state when loading=true', () => {
    render(
      <DiagnosisCard machineId="conveyor_2" result={null} loading={true} />
    )
    expect(screen.getByText(/diagnosing/i)).toBeInTheDocument()
  })

  it('disables button when loading', () => {
    render(
      <DiagnosisCard machineId="conveyor_2" result={null} loading={true} />
    )
    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
  })

  it('shows error message when error is set', () => {
    render(
      <DiagnosisCard machineId="conveyor_2" result={null} error="Connection refused" />
    )
    expect(screen.getByText(/connection refused/i)).toBeInTheDocument()
  })

  it('calls onRunDiagnosis when button is clicked', () => {
    const onRun = vi.fn()
    render(
      <DiagnosisCard machineId="conveyor_2" result={null} onRunDiagnosis={onRun} />
    )
    fireEvent.click(screen.getByText('Run Diagnosis'))
    expect(onRun).toHaveBeenCalledTimes(1)
  })
})
