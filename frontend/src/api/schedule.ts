import { api } from './client';

export interface ScheduleEntry {
  subject_id: string;
  day: number;
  slot: number;
  hours: number;
}

export interface SubjectExplanation {
  subject_id: string;
  required_hours: number;
  scheduled_hours: number;
  buffer_used: number;
  deadline_shortfall: number;
}

export interface DayExplanation {
  day: number;
  total_hours: number;
  overload: number;
}

export interface Warning {
  type: string;
  message: string;
  subject_id?: string;
  day?: number;
  shortfall_hours?: number;
  overload_hours?: number;
}

export interface ScheduleResponse {
  status: string;
  feasible: boolean;
  schedule: ScheduleEntry[];
  explanation?: {
    per_subject: SubjectExplanation[];
    per_day: DayExplanation[];
  };
  warnings?: Warning[];
  objective_value?: number;
  schedule_id?: string;
  generated_date?: string;
  risk_score_at_generation?: number;
  risk_level?: string;
  w_max_effective?: number;
  w_max?: number;
  horizon_days?: number;
}

export const scheduleApi = {
  generate: () =>
    api.post<ScheduleResponse>('/api/schedule/generate').then((r) => r.data),
  latest: () =>
    api.get<ScheduleResponse>('/api/schedule/latest').then((r) => r.data),
};
