export interface RouteStop {
  sequence: number
  exhibit_id: string
  exhibit_title: string
  gallery_id: string
  gallery_name: string
  visit_duration_minutes: number
  walking_distance_from_previous_m: number
  walking_time_from_previous_minutes: number
  planned_arrival_offset_minutes: number
  accessibility_status: string
  opening_status: string
  is_completed: boolean
}

export interface SkippedItem {
  exhibit_id: string
  title: string
  reason_code: string
  human_readable_reason: string
}

export interface ExhibitCommentary {
  exhibit_id: string
  commentary: string
  interest_match_reason: string
  source_references: string[]
  confidence: string
  did_you_know: string
}

export interface WorkflowTraceEntry {
  agent_name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  started_at: string | null
  completed_at: string | null
  duration_ms: number | null
  input_summary: string
  output_summary: string
  error_message: string | null
}

export interface RetrievedEvidence {
  exhibit_id: string
  source_id: string
  source_title: string
  chunk_text: string
  relevance_score: number
}

export interface VisitGuide {
  visit_id: string
  visitor_id: string
  generated_at: string
  route: RouteStop[]
  commentaries: Record<string, ExhibitCommentary>
  skipped_items: SkippedItem[]
  total_visit_minutes: number
  total_walking_minutes: number
  total_walking_distance_m: number
  time_budget_minutes: number
  time_budget_fit: boolean
  interest_coverage: Record<string, boolean>
  sources: RetrievedEvidence[]
  workflow_trace: WorkflowTraceEntry[]
  crowd_replan_version: number
  replan_explanation: string
}

export interface Gallery {
  gallery_id: string
  name: string
  floor: number
  crowd_state: string
}

export interface CrowdStatus {
  gallery_id: string
  crowd_state: string
  penalty_minutes: number
  is_visitable: boolean
  description: string
}

export interface ProfileEvalResult {
  visitor_id: string
  display_name: string
  time_budget_minutes: number
  total_route_minutes: number
  time_budget_fit: boolean
  stated_interests: string[]
  covered_interests: string[]
  interest_coverage_pct: number
  num_exhibits_in_route: number
  total_walking_minutes: number
  accessibility_compliant: boolean
  opening_hours_compliant: boolean
}

export interface EvaluationReport {
  run_at: string
  profiles: ProfileEvalResult[]
  time_budget_fit_rate_pct: number
  average_interest_coverage_pct: number
  average_exhibits_per_route: number
  average_walking_minutes: number
  accessibility_compliance_rate_pct: number
  opening_hours_compliance_rate_pct: number
  notes: string
}

export interface VisitorMemory {
  visitor_id: string
  display_name: string
  interests: string[]
  preferred_language: string
  preferred_commentary_length: string
  accessibility_needs: string[]
  previously_visited_exhibits: string[]
  updated_at: string
}
