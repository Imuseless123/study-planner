import { api } from './client';

// ====== Types ======

export interface StudyLogItem {
  session_id: string;
  subject_id: string;
  subject_name: string;
  start_time: string;
  duration: number;
  focus_level: number;
}

export interface SleepLogItem {
  sleep_id: string;
  sleep_time: string;
  wake_time: string;
  quality: number;
  hours: number;
}

export interface MoodLogItem {
  mood_id: string;
  log_date: string;
  energy_level: number;
  stress_level: number;
}

export interface StudyLogPayload {
  subject_id: string;
  start_time: string; // ISO
  duration: number;
  focus_level: number;
}

export interface SleepLogPayload {
  sleep_time: string;
  wake_time: string;
  quality: number;
}

export interface MoodLogPayload {
  log_date: string; // YYYY-MM-DD
  energy_level: number;
  stress_level: number;
}

// ====== API ======

export const logsApi = {
  // Study
  createStudy: (payload: StudyLogPayload) =>
    api.post('/api/log/study', payload).then((r) => r.data),

  listStudy: (limit = 50) =>
    api
      .get<{ items: StudyLogItem[]; total: number }>('/api/log/study', {
        params: { limit },
      })
      .then((r) => r.data),

  deleteStudy: (sessionId: string) =>
    api.delete(`/api/log/study/${sessionId}`).then((r) => r.data),

  // Sleep
  createSleep: (payload: SleepLogPayload) =>
    api.post('/api/log/sleep', payload).then((r) => r.data),

  listSleep: (limit = 50) =>
    api
      .get<{ items: SleepLogItem[]; total: number }>('/api/log/sleep', {
        params: { limit },
      })
      .then((r) => r.data),

  deleteSleep: (sleepId: string) =>
    api.delete(`/api/log/sleep/${sleepId}`).then((r) => r.data),

  // Mood
  createMood: (payload: MoodLogPayload) =>
    api.post('/api/log/mood', payload).then((r) => r.data),

  listMood: (limit = 50) =>
    api
      .get<{ items: MoodLogItem[]; total: number }>('/api/log/mood', {
        params: { limit },
      })
      .then((r) => r.data),

  deleteMood: (moodId: string) =>
    api.delete(`/api/log/mood/${moodId}`).then((r) => r.data),
};
