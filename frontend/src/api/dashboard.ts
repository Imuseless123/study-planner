import { api } from './client';

export interface UpcomingAssignment {
  assignment_id: string;
  title: string;
  subject_id: string;
  deadline: string;
  required_hours: number;
  priority: number;
}

export interface DashboardSummary {
  study_hours_by_date: Record<string, number>;
  study_hours_matrix: Record<string, Record<string, number>>;
  sleep_hours_recent: number[];
  upcoming_assignments: UpcomingAssignment[];
  subjects: Array<{
    subject_id: string;
    subject_name: string;
    difficulty: number;
    priority: number;
  }>;
}

export const dashboardApi = {
  summary: () =>
    api.get<DashboardSummary>('/api/dashboard/summary').then((r) => r.data),
};
