import { ReactNode, useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Spin, message } from 'antd';
import { useAuthStore } from '../store/authStore';
import { authApi } from '../api/auth';

interface ProtectedRouteProps {
  children: ReactNode;
  requireConsent?: boolean;
}

export default function ProtectedRoute({
  children,
  requireConsent = true,
}: ProtectedRouteProps) {
  const location = useLocation();
  const { token, consentSigned, setConsent, setAuth, clearAuth } = useAuthStore();
  const [checking, setChecking] = useState(false);

  // Nếu có token nhưng chưa load user → load lại
  useEffect(() => {
    if (token && !useAuthStore.getState().user) {
      setChecking(true);
      authApi
        .me()
        .then((user) => {
          setAuth(token, user);
        })
        .catch(() => {
          clearAuth();
        })
        .finally(() => setChecking(false));
    }
  }, [token, setAuth, clearAuth]);

  // Nếu có token + requireConsent, verify consent từ backend
  useEffect(() => {
    if (token && requireConsent) {
      authApi
        .getConsent()
        .then((consent) => {
          setConsent(!!consent && !consent.withdrawn_at);
        })
        .catch(() => {
          // ignore
        });
    }
  }, [token, requireConsent, setConsent]);

  // Chưa đăng nhập → về login
  if (!token) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  // Đang verify user
  if (checking) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Spin size="large" />
      </div>
    );
  }

  // Đã đăng nhập nhưng chưa ký consent
  if (requireConsent && !consentSigned) {
    return <Navigate to="/consent" replace />;
  }

  return <>{children}</>;
}
