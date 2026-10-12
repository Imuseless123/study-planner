import { api } from './client';

export interface ConsentInfo {
  consent_id: string;
  version: string;
  signed_at: string;
  expires_at: string;
  withdrawn_at: string | null;
}

export const consentApi = {
  get: () => api.get<ConsentInfo | null>('/api/consent').then((r) => r.data),
  withdraw: () => api.post('/api/consent/withdraw').then((r) => r.data),
};
