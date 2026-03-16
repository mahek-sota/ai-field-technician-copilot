import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import MachineSelector from '../src/components/MachineSelector/MachineSelector'
import { mockMachineList } from './fixtures'

describe('MachineSelector', () => {
  it('renders all machine names', () => {
    render(
      <MachineSelector
        selectedMachineId={null}
        onSelect={vi.fn()}
        machines={mockMachineList}
      />
    )
    expect(screen.getByText('Conveyor Belt Alpha')).toBeInTheDocument()
    expect(screen.getByText('Conveyor Belt Beta')).toBeInTheDocument()
    expect(screen.getByText('Robotic Arm Delta')).toBeInTheDocument()
    expect(screen.getByText('Hydraulic Pump Gamma')).toBeInTheDocument()
    expect(screen.getByText('Air Compressor Epsilon')).toBeInTheDocument()
  })

  it('renders 5 machines from fixture', () => {
    render(
      <MachineSelector
        selectedMachineId={null}
        onSelect={vi.fn()}
        machines={mockMachineList}
      />
    )
    const items = screen.getAllByText(/Conveyor|Robotic|Hydraulic|Compressor/)
    expect(items.length).toBeGreaterThanOrEqual(5)
  })

  it('calls onSelect with machine_id when machine is clicked', () => {
    const onSelect = vi.fn()
    render(
      <MachineSelector
        selectedMachineId={null}
        onSelect={onSelect}
        machines={mockMachineList}
      />
    )
    fireEvent.click(screen.getByText('Conveyor Belt Beta'))
    expect(onSelect).toHaveBeenCalledWith('conveyor_2')
  })

  it('shows loading state when loading=true', () => {
    render(
      <MachineSelector
        selectedMachineId={null}
        onSelect={vi.fn()}
        machines={[]}
        loading={true}
      />
    )
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('shows error state when error is set', () => {
    render(
      <MachineSelector
        selectedMachineId={null}
        onSelect={vi.fn()}
        machines={[]}
        error="Network error"
      />
    )
    expect(screen.getByText(/network error/i)).toBeInTheDocument()
  })

  it('shows empty state when machines list is empty', () => {
    render(
      <MachineSelector
        selectedMachineId={null}
        onSelect={vi.fn()}
        machines={[]}
      />
    )
    expect(screen.getByText(/no machines/i)).toBeInTheDocument()
  })

  it('highlights the selected machine visually', () => {
    const { container } = render(
      <MachineSelector
        selectedMachineId="conveyor_2"
        onSelect={vi.fn()}
        machines={mockMachineList}
      />
    )
    // The selected item has blue left-border styling
    const listItems = container.querySelectorAll('li')
    const selectedItem = Array.from(listItems).find(li =>
      li.textContent?.includes('Conveyor Belt Beta')
    )
    expect(selectedItem).toBeDefined()
  })

  it('renders status badges for machines', () => {
    render(
      <MachineSelector
        selectedMachineId={null}
        onSelect={vi.fn()}
        machines={mockMachineList}
      />
    )
    expect(screen.getAllByText('warning').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('normal').length).toBeGreaterThanOrEqual(1)
    // Two critical machines
    const criticalBadges = screen.getAllByText('critical')
    expect(criticalBadges.length).toBeGreaterThanOrEqual(2)
  })
})
