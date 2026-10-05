import { useState } from 'react';
import { Outlet, useNavigate, useLocation, Link } from 'react-router-dom';
import { Layout, Menu, Avatar, Dropdown, Typography, message } from 'antd';
import {
  DashboardOutlined,
  EditOutlined,
  BookOutlined,
  CalendarOutlined,
  SettingOutlined,
  LogoutOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../store/authStore';
import { authApi } from '../api/auth';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const MENU_ITEMS = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: <Link to="/dashboard">Dashboard</Link> },
  { key: '/logging', icon: <EditOutlined />, label: <Link to="/logging">Ghi nhật ký</Link> },
  { key: '/subjects', icon: <BookOutlined />, label: <Link to="/subjects">Môn học</Link> },
  { key: '/schedule', icon: <CalendarOutlined />, label: <Link to="/schedule">Lịch học</Link> },
  { key: '/settings', icon: <SettingOutlined />, label: <Link to="/settings">Cài đặt</Link> },
];

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const user = useAuthStore((s) => s.user);
  const clearAuth = useAuthStore((s) => s.clearAuth);

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch {
      // ignore
    }
    clearAuth();
    message.success('Đã đăng xuất');
    navigate('/login');
  };

  const userMenu = {
    items: [
      {
        key: 'profile',
        icon: <UserOutlined />,
        label: user?.username || 'User',
        disabled: true,
      },
      { type: 'divider' as const },
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: 'Đăng xuất',
        onClick: handleLogout,
      },
    ],
  };

  // Chọn menu key dựa trên path
  const selectedKey = MENU_ITEMS.find((m) => location.pathname.startsWith(m.key))?.key || '/dashboard';

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="light"
        style={{
          borderRight: '1px solid #f0f0f0',
          position: 'sticky',
          top: 0,
          height: '100vh',
        }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderBottom: '1px solid #f0f0f0',
            fontWeight: 600,
            fontSize: collapsed ? 16 : 18,
            color: '#667eea',
          }}
        >
          {collapsed ? 'SP' : 'Study Planner'}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={MENU_ITEMS}
          style={{ borderInlineEnd: 'none' }}
        />
      </Sider>

      <Layout>
        <Header
          style={{
            background: '#fff',
            borderBottom: '1px solid #f0f0f0',
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <Text strong style={{ fontSize: 16 }}>
            {MENU_ITEMS.find((m) => m.key === selectedKey)?.label?.props?.children || 'Dashboard'}
          </Text>
          <Dropdown menu={userMenu} placement="bottomRight">
            <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Avatar style={{ background: '#667eea' }}>
                {user?.username?.[0]?.toUpperCase() || 'U'}
              </Avatar>
              <Text>{user?.username}</Text>
            </div>
          </Dropdown>
        </Header>

        <Content
          style={{
            padding: 24,
            background: '#f5f5f5',
            overflow: 'auto',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
