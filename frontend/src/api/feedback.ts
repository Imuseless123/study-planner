import { api } from './client';

export interface FeedbackCreate {
  schedule_id: string;
  rating: number;
  comment?: string;
}

export interface Feedback {
  feedback_id: string;
  schedule_id: string;
  rating: number;
  comment: string | null;
  created_at: string;
}

export const feedbackApi = {
  create: (payload: FeedbackCreate) =>
    api.post<Feedback>('/api/feedback', payload).then((r) => r.data),
  list: (scheduleId: string) =>
    api.get<Feedback[]>(`/api/feedback/${scheduleId}`).then((r) => r.data),
};
