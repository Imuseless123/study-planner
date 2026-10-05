import { Outlet } from 'react-router-dom';
import { Layout, Typography } from 'antd';
import { BookOutlined } from '@ant-design/icons';

const { Content } = Layout;
const { Title, Text } = Typography;

export default function AuthLayout() {
  return (
    <Layout
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 20,
      }}
    >
      <Content
        style={{
          width: '100%',
          maxWidth: 420,
          background: 'white',
          borderRadius: 12,
          padding: 40,
          boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <BookOutlined style={{ fontSize: 48, color: '#667eea' }} />
          <Title level={3} style={{ marginTop: 16, marginBottom: 4 }}>
            Study Planner
          </Title>
          <Text type="secondary">Lập kế hoạch học tập cá nhân</Text>
        </div>
        <Outlet />
      </Content>
    </Layout>
  );
}
