/**
 * Custom React hooks for data fetching.
 *
 * Each hook follows the pattern:
 *   { data, loading, error, refetch }
 *
 * Hooks defined here (implementations to be written by Frontend Agent):
 *   - useMachines()         : fetch all machines list
 *   - useMachine(id)        : fetch single machine detail
 *   - useDiagnosis(request) : run diagnosis pipeline
 */

export { useMachines } from './useMachines'
export { useMachine } from './useMachine'
export { useDiagnosis } from './useDiagnosis'
