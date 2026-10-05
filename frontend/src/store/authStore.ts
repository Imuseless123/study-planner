import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserMe } from '../api/auth';

interface AuthState {
  token: string | null;
  user: UserMe | null;
  consentSigned: boolean;
  hydrated: boolean;

  setAuth: (token: string, user: UserMe) => void;
  setConsent: (signed: boolean) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      consentSigned: false,
      hydrated: false,

      setAuth: (token, user) => set({ token, user }),
      setConsent: (signed) => set({ consentSigned: signed }),
      clearAuth: () => set({ token: null, user: null, consentSigned: false }),
    }),
    {
      name: 'study-planner-auth',
      // Chỉ persist user + consent, KHÔNG persist token (giữ trong memory)
      partialize: (state) => ({
        user: state.user,
        consentSigned: state.consentSigned,
      }),
      onRehydrateStorage: () => (state) => {
        if (state) state.hydrated = true;
      },
    }
  )
);
