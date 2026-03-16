import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import SensorDisplay from '../src/components/SensorDisplay/SensorDisplay'
import { mockMachineInfo } from './fixtures'

describe('SensorDisplay', () => {
  const sensors = mockMachineInfo.sensors

  it('renders all sensor names', () => {
    render(<SensorDisplay sensors={sensors} />)
    expect(screen.getByText('temperature')).toBeInTheDocument()
    expect(screen.getByText('vibration')).toBeInTheDocument()
    expect(screen.getByText('motor_current')).toBeInTheDocument()
  })

  it('renders sensor values', () => {
    render(<SensorDisplay sensors={sensors} />)
    expect(screen.getByText('78.5')).toBeInTheDocument()
    expect(screen.getByText('2.1')).toBeInTheDocument()
  })

  it('renders sensor units', () => {
    render(<SensorDisplay sensors={sensors} />)
    expect(screen.getByText('°C')).toBeInTheDocument()
    expect(screen.getByText('mm/s')).toBeInTheDocument()
    expect(screen.getByText('A')).toBeInTheDocument()
  })

  it('renders warning status badge for warning sensor', () => {
    render(<SensorDisplay sensors={sensors} />)
    expect(screen.getByText('warning')).toBeInTheDocument()
  })

  it('renders normal status badge for normal sensors', () => {
    render(<SensorDisplay sensors={sensors} />)
    const normalBadges = screen.getAllByText('normal')
    expect(normalBadges.length).toBeGreaterThanOrEqual(2)
  })

  it('renders threshold values when present', () => {
    render(<SensorDisplay sensors={sensors} />)
    expect(screen.getByText(/warn: 70/)).toBeInTheDocument()
    expect(screen.getByText(/crit: 85/)).toBeInTheDocument()
  })

  it('renders empty state when sensors array is empty', () => {
    render(<SensorDisplay sensors={[]} />)
    expect(screen.getByText(/no sensor data/i)).toBeInTheDocument()
  })

  it('renders critical sensor with critical badge', () => {
    const criticalSensors = [
      { name: 'joint_temp', value: 104.7, unit: '°C', threshold_warning: 80, threshold_critical: 95, status: 'critical' },
    ]
    render(<SensorDisplay sensors={criticalSensors} />)
    expect(screen.getByText('critical')).toBeInTheDocument()
  })
})
