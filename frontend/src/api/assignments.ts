import { api } from './client';

export interface Assignment {
  assignment_id: string;
  subject_id: string;
  subject_name: string;
  title: string;
  deadline: string;
  required_hours: number;
  priority: number;
  days_until_deadline: number;
  is_overdue: boolean;
}

export interface AssignmentStats {
  total: number;
  overdue: number;
  due_soon: number;
  high_priority: number;
  total_required_hours: number;
}

export interface AssignmentCreatePayload {
  subject_id: string;
  title: string;
  deadline: string;
  required_hours: number;
  priority: number;
}

export interface AssignmentUpdatePayload {
  subject_id?: string;
  title?: string;
  deadline?: string;
  required_hours?: number;
  priority?: number;
}

export const assignmentsApi = {
  list: () =>
    api
      .get<{ assignments: Assignment[] }>('/api/assignments')
      .then((r) => r.data.assignments),

  stats: () =>
    api.get<AssignmentStats>('/api/assignments/stats').then((r) => r.data),

  get: (id: string) =>
    api.get<Assignment>(`/api/assignments/${id}`).then((r) => r.data),

  create: (payload: AssignmentCreatePayload) =>
    api.post<Assignment>('/api/assignments', payload).then((r) => r.data),

  update: (id: string, payload: AssignmentUpdatePayload) =>
    api.put<Assignment>(`/api/assignments/${id}`, payload).then((r) => r.data),

  delete: (id: string) =>
    api.delete(`/api/assignments/${id}`).then((r) => r.data),
};
