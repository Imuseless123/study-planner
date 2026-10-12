import { api } from './client';

export interface DataExport {
  exported_at: string;
  schema_version: string;
  user: Record<string, unknown>;
  subjects: Array<Record<string, unknown>>;
  assignments: Array<Record<string, unknown>>;
  study_sessions: Array<Record<string, unknown>>;
  sleep_logs: Array<Record<string, unknown>>;
  mood_logs: Array<Record<string, unknown>>;
  schedules: Array<Record<string, unknown>>;
  feedback: Array<Record<string, unknown>>;
  consents: Array<Record<string, unknown>>;
  stats: Record<string, number>;
}

export interface DeleteAccountPayload {
  confirm: boolean;
  username_confirmation: string;
}

export const userDataApi = {
  export: () => api.get<DataExport>('/api/user/data').then((r) => r.data),

  deleteAccount: (payload: DeleteAccountPayload) =>
    api.delete('/api/user/data', { data: payload }).then((r) => r.data),
};
