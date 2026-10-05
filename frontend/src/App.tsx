import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, App as AntdApp } from 'antd';
import viVN from 'antd/locale/vi_VN';

import AuthLayout from './layouts/AuthLayout';
import AppLayout from './layouts/AppLayout';
import ProtectedRoute from './components/ProtectedRoute';

import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ConsentPage from './pages/ConsentPage';
import DashboardPage from './pages/DashboardPage';

export default function App() {
  return (
    <ConfigProvider
      locale={viVN}
      theme={{
        token: {
          colorPrimary: '#667eea',
          borderRadius: 8,
        },
      }}
    >
      <AntdApp>
        <BrowserRouter>
          <Routes>
            {/* Auth routes (không cần đăng nhập) */}
            <Route element={<AuthLayout />}>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
            </Route>

            {/* Consent page (cần đăng nhập, không cần consent) */}
            <Route
              path="/consent"
              element={
                <ProtectedRoute requireConsent={false}>
                  <ConsentPage />
                </ProtectedRoute>
              }
            />

            {/* App routes (cần đăng nhập + consent) */}
            <Route
              element={
                <ProtectedRoute requireConsent>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              {/* Các routes khác sẽ bổ sung sau */}
              <Route path="/logging" element={<PlaceholderPage title="Ghi nhật ký" />} />
              <Route path="/subjects" element={<PlaceholderPage title="Môn học" />} />
              <Route path="/schedule" element={<PlaceholderPage title="Lịch học" />} />
              <Route path="/settings" element={<PlaceholderPage title="Cài đặt" />} />
            </Route>

            {/* 404 */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AntdApp>
    </ConfigProvider>
  );
}

// Placeholder tạm cho các trang chưa làm
function PlaceholderPage({ title }: { title: string }) {
  return (
    <div style={{ padding: 40, textAlign: 'center', color: '#999' }}>
      <h2>{title}</h2>
      <p>Tính năng này sẽ được bổ sung ở bước tiếp theo.</p>
    </div>
  );
}
