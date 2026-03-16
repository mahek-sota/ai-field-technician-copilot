import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import App from '../src/App'
import { mockMachineList, mockMachineInfo, mockDiagnosisResponse } from './fixtures'

// Mock the entire api module
vi.mock('../src/api', () => ({
  fetchMachines: vi.fn(),
  fetchMachine: vi.fn(),
  runDiagnosis: vi.fn(),
  fetchHistory: vi.fn(),
}))

import * as api from '../src/api'

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.fetchMachines).mockResolvedValue(mockMachineList)
    vi.mocked(api.fetchMachine).mockResolvedValue(mockMachineInfo)
    vi.mocked(api.runDiagnosis).mockResolvedValue(mockDiagnosisResponse)
    vi.mocked(api.fetchHistory).mockResolvedValue([])
  })

  it('renders the app title in the sidebar', async () => {
    render(<App />)
    expect(screen.getAllByText(/Field Technician Copilot/i).length).toBeGreaterThanOrEqual(1)
  })

  it('shows welcome message before machine selection', () => {
    vi.mocked(api.fetchMachines).mockResolvedValue([])
    render(<App />)
    expect(screen.getAllByText(/select a machine/i).length).toBeGreaterThanOrEqual(1)
  })

  it('loads and displays machine list after fetch', async () => {
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText('Conveyor Belt Alpha')).toBeInTheDocument()
    })
    expect(screen.getByText('Robotic Arm Delta')).toBeInTheDocument()
  })

  it('shows loading state initially for machine list', () => {
    vi.mocked(api.fetchMachines).mockReturnValue(new Promise(() => {})) // never resolves
    render(<App />)
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('shows machine details after selecting a machine', async () => {
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText('Conveyor Belt Alpha')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText('Conveyor Belt Beta'))
    await waitFor(() => {
      expect(api.fetchMachine).toHaveBeenCalledWith('conveyor_2')
    })
  })

  it('shows Run Diagnosis button after machine is selected and loaded', async () => {
    render(<App />)
    await waitFor(() => screen.getByText('Conveyor Belt Beta'))
    fireEvent.click(screen.getByText('Conveyor Belt Beta'))
    await waitFor(() => {
      expect(screen.getByText('Run Diagnosis')).toBeInTheDocument()
    })
  })

  it('calls runDiagnosis when diagnosis button is clicked', async () => {
    render(<App />)
    await waitFor(() => screen.getByText('Conveyor Belt Beta'))
    fireEvent.click(screen.getByText('Conveyor Belt Beta'))
    await waitFor(() => screen.getByText('Run Diagnosis'))
    fireEvent.click(screen.getByText('Run Diagnosis'))
    await waitFor(() => {
      expect(api.runDiagnosis).toHaveBeenCalledWith(
        expect.objectContaining({ machine_id: 'conveyor_2' })
      )
    })
  })

  it('shows diagnosis result after successful diagnosis', async () => {
    render(<App />)
    await waitFor(() => screen.getByText('Conveyor Belt Beta'))
    fireEvent.click(screen.getByText('Conveyor Belt Beta'))
    await waitFor(() => screen.getByText('Run Diagnosis'))
    fireEvent.click(screen.getByText('Run Diagnosis'))
    await waitFor(() => {
      expect(screen.getByText(/bearing wear detected/i)).toBeInTheDocument()
    })
  })

  it('shows error state when machine fetch fails', async () => {
    vi.mocked(api.fetchMachine).mockRejectedValue(new Error('Server error'))
    render(<App />)
    await waitFor(() => screen.getByText('Conveyor Belt Beta'))
    fireEvent.click(screen.getByText('Conveyor Belt Beta'))
    await waitFor(() => {
      expect(screen.getByText(/server error/i)).toBeInTheDocument()
    })
  })

  it('does not render diagnosis card before machine is selected', async () => {
    vi.mocked(api.fetchMachines).mockResolvedValue([])
    render(<App />)
    expect(screen.queryByText('Run Diagnosis')).not.toBeInTheDocument()
  })
})
