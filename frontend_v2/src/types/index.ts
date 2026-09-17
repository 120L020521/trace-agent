export interface Location {
  longitude: number
  latitude: number
}

export interface Attraction {
  name: string
  address: string
  location?: Location
  visit_duration: number
  description: string
  category?: string
  rating?: number
  image_url?: string
  ticket_price?: number
  opening_time?: string
  closing_time?: string
  priority_score?: number
  evidence_confidence?: number
  scheduled_start?: string
  scheduled_end?: string
}

export interface Meal {
  type: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  name: string
  address?: string
  location?: Location
  description?: string
  estimated_cost?: number
}

export interface Hotel {
  name: string
  address: string
  location?: Location
  price_range: string
  rating: string
  distance: string
  type: string
  estimated_cost?: number
}

export interface Budget {
  total_attractions: number
  total_hotels: number
  total_meals: number
  total_transportation: number
  total: number
}

export interface DayPlan {
  date: string
  day_index: number
  description: string
  transportation: string
  accommodation: string
  hotel?: Hotel
  attractions: Attraction[]
  meals: Meal[]
}

export interface WeatherInfo {
  date: string
  day_weather: string
  night_weather: string
  day_temp: number
  night_temp: number
  wind_direction: string
  wind_power: string
}

export interface TripPlan {
  city: string
  start_date: string
  end_date: string
  days: DayPlan[]
  weather_info: WeatherInfo[]
  overall_suggestions: string
  budget?: Budget
  citations: SourceCitation[]
  validation_report?: ValidationReport
  optimization_report?: OptimizationReport
  evidence_report?: EvidenceReport
  planning_trace_id?: string
  revision: number
}

export interface OptimizationReport {
  status: string
  objective_value?: number
  selected_attractions: number
  dropped_attractions: string[]
  estimated_travel_minutes: number
  solver_time_ms: number
  fallback_used: boolean
}

export interface EvidenceReport {
  strategy: 'tool_first' | 'long_context' | 'hybrid_multi_query' | string
  rationale: string
  queries: string[]
  retrieval_rounds: number
  source_count: number
  candidate_chunks: number
  selected_chunks: number
  context_chars: number
  coverage: number
  sufficient: boolean
  missing_aspects: string[]
  fallback_used: boolean
}

export interface Disruption {
  type: 'attraction_closed' | 'weather' | 'delay' | 'budget_changed' | 'user_change'
  date?: string
  target?: string
  delay_minutes?: number
  new_budget?: number
  description?: string
}

export interface SourceCitation {
  source_id: string
  source_name: string
  chunk_id: string
  excerpt: string
  score: number
  retrieval_strategy?: string
}

export interface ValidationIssue {
  code: string
  severity: 'error' | 'warning'
  path: string
  message: string
  expected?: string
  actual?: string
}

export interface ValidationReport {
  passed: boolean
  score: number
  issues: ValidationIssue[]
  checks: Record<string, boolean>
  repair_attempted: boolean
}

export interface TripFormData {
  city: string
  start_date: string
  end_date: string
  travel_days: number
  transportation: string
  accommodation: string
  preferences: string[]
  free_text_input: string
  max_budget?: number
  max_daily_attractions: number
  accessibility_needs: string[]
  knowledge_source_ids: string[]
  enable_experience_learning: boolean
}

export interface TripPlanResponse {
  success: boolean
  message: string
  data?: TripPlan
}
