import { api } from './client';

export interface Subject {
  subject_id: string;
  subject_name: string;
  difficulty: number;
  priority: number;
}

export interface SubjectCreatePayload {
  subject_name: string;
  difficulty: number;
  priority: number;
}

export const subjectsApi = {
  list: () =>
    api
      .get<{ subjects: Subject[] }>('/api/subjects')
      .then((r) => r.data.subjects),

  create: (payload: SubjectCreatePayload) =>
    api.post<Subject>('/api/subjects', payload).then((r) => r.data),

  delete: (id: string) =>
    api.delete(`/api/subjects/${id}`).then((r) => r.data),
};
