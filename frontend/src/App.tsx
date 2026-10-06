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
import LoggingPage from './pages/LoggingPage';
import SubjectsPage from './pages/SubjectsPage';
import AssignmentsPage from './pages/AssignmentsPage';

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
            <Route element={<AuthLayout />}>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
            </Route>

            <Route
              path="/consent"
              element={
                <ProtectedRoute requireConsent={false}>
                  <ConsentPage />
                </ProtectedRoute>
              }
            />

            <Route
              element={
                <ProtectedRoute requireConsent>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/logging" element={<LoggingPage />} />
              <Route path="/subjects" element={<SubjectsPage />} />
              <Route path="/assignments" element={<AssignmentsPage />} />
              <Route path="/schedule" element={<PlaceholderPage title="Lịch học" />} />
              <Route path="/settings" element={<PlaceholderPage title="Cài đặt" />} />
            </Route>

            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AntdApp>
    </ConfigProvider>
  );
}

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div style={{ padding: 40, textAlign: 'center', color: '#999' }}>
      <h2>{title}</h2>
      <p>Tính năng này sẽ được bổ sung ở bước tiếp theo.</p>
    </div>
  );
}
