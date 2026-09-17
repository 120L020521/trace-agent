import type { TripFormData, TripPlan } from '@/types'

export interface PlanVersion {
  id: string
  revision: number
  createdAt: string
  reason: string
  traceId?: string
  plan: TripPlan
}

export interface WorkspaceRun {
  id: string
  title: string
  createdAt: string
  updatedAt: string
  status: 'completed' | 'needs_review' | 'running' | 'failed'
  request: TripFormData
  plan: TripPlan
  versions: PlanVersion[]
  feedback?: { accepted: boolean; rating?: number; comment?: string }
}

const STORAGE_KEY = 'tripPilot.workspace.runs.v1'
const ACTIVE_KEY = 'tripPilot.workspace.activeRun'

const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value))

export function listWorkspaceRuns(): WorkspaceRun[] {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') as WorkspaceRun[]
    return value.sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
  } catch {
    return []
  }
}

function writeRuns(runs: WorkspaceRun[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(runs.slice(0, 50)))
  window.dispatchEvent(new CustomEvent('trip-workspace-updated'))
}

export function createWorkspaceRun(request: TripFormData, plan: TripPlan): WorkspaceRun {
  const now = new Date().toISOString()
  const id = plan.planning_trace_id || `run-${Date.now()}`
  const run: WorkspaceRun = {
    id,
    title: `${plan.city} · ${request.travel_days}天行程`,
    createdAt: now,
    updatedAt: now,
    status: plan.validation_report?.passed === false ? 'needs_review' : 'completed',
    request: clone(request),
    plan: clone(plan),
    versions: [{
      id: `${id}-v${plan.revision || 0}`,
      revision: plan.revision || 0,
      createdAt: now,
      reason: '首次规划',
      traceId: plan.planning_trace_id,
      plan: clone(plan)
    }]
  }
  const runs = listWorkspaceRuns().filter(item => item.id !== id)
  writeRuns([run, ...runs])
  setActiveRun(id)
  return run
}

export function updateWorkspaceRun(plan: TripPlan, reason: string): WorkspaceRun | null {
  const id = getActiveRunId()
  const runs = listWorkspaceRuns()
  const run = runs.find(item => item.id === id)
  if (!run) return null
  const now = new Date().toISOString()
  run.plan = clone(plan)
  run.updatedAt = now
  run.status = plan.validation_report?.passed === false ? 'needs_review' : 'completed'
  const traceId = plan.planning_trace_id
  const latest = run.versions[run.versions.length - 1]
  if (!latest || latest.traceId !== traceId || latest.reason !== reason) {
    run.versions.push({
      id: `${run.id}-${Date.now()}`,
      revision: plan.revision || run.versions.length,
      createdAt: now,
      reason,
      traceId,
      plan: clone(plan)
    })
  } else {
    latest.plan = clone(plan)
  }
  writeRuns(runs)
  return run
}

export function updateWorkspaceFeedback(accepted: boolean, rating?: number, comment?: string) {
  const id = getActiveRunId()
  const runs = listWorkspaceRuns()
  const run = runs.find(item => item.id === id)
  if (!run) return
  run.feedback = { accepted, rating, comment }
  run.updatedAt = new Date().toISOString()
  if (!accepted) run.status = 'needs_review'
  writeRuns(runs)
}

export function openWorkspaceRun(run: WorkspaceRun, version?: PlanVersion) {
  const selected = version?.plan || run.plan
  sessionStorage.setItem('tripPlan', JSON.stringify(selected))
  sessionStorage.setItem('tripRequest', JSON.stringify(run.request))
  setActiveRun(run.id)
}

export function getActiveRunId() {
  return sessionStorage.getItem(ACTIVE_KEY)
}

export function setActiveRun(id: string) {
  sessionStorage.setItem(ACTIVE_KEY, id)
}

