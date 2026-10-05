import { api } from './client';

export interface RegisterPayload {
  username: string;
  password: string;
  email: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface AuthResponse {
  status: string;
  token: string;
  refresh_token?: string;
}

export interface UserMe {
  user_id: string;
  username: string;
  email: string;
  created_at: string;
}

export interface ConsentResponse {
  consent_id: string;
  version: string;
  signed_at: string;
  expires_at: string;
  withdrawn_at: string | null;
}

export const authApi = {
  register: (payload: RegisterPayload) =>
    api.post('/api/auth/register', payload).then((r) => r.data),

  login: (payload: LoginPayload) =>
    api.post<AuthResponse>('/api/auth/login', payload).then((r) => r.data),

  logout: () =>
    api.post('/api/auth/logout').then((r) => r.data),

  // tokenOverride: dùng khi cần gọi /me ngay sau login
  // (trước khi token được lưu vào store)
  me: (tokenOverride?: string) =>
    api
      .get<UserMe>('/api/auth/me', {
        headers: tokenOverride
          ? { Authorization: `Bearer ${tokenOverride}` }
          : undefined,
      })
      .then((r) => r.data),

  getConsent: (tokenOverride?: string) =>
    api
      .get<ConsentResponse | null>('/api/consent', {
        headers: tokenOverride
          ? { Authorization: `Bearer ${tokenOverride}` }
          : undefined,
      })
      .then((r) => r.data),

  signConsent: (version: string) =>
    api.post<ConsentResponse>('/api/consent', { version }).then((r) => r.data),

  withdrawConsent: () =>
    api.post('/api/consent/withdraw').then((r) => r.data),
};
