import { Card, Typography, Empty, Space, Tag } from 'antd';
import { useAuthStore } from '../store/authStore';

const { Title, Paragraph, Text } = Typography;

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);

  return (
    <Space direction="vertical" size={24} style={{ display: 'flex' }}>
      <div>
        <Title level={2} style={{ marginBottom: 4 }}>
          Xin chào, {user?.username} 👋
        </Title>
        <Paragraph type="secondary">
          Đây là bảng điều khiển của bạn. Các widget sẽ được bổ sung ở bước tiếp theo.
        </Paragraph>
      </div>

      <Card title="Trạng thái hiện tại">
        <Space direction="vertical">
          <div>
            <Text strong>User ID: </Text>
            <Text code>{user?.user_id}</Text>
          </div>
          <div>
            <Text strong>Email: </Text>
            <Text>{user?.email}</Text>
          </div>
          <div>
            <Text strong>Tầng 1 — Auth: </Text>
            <Tag color="green">Hoàn thành</Tag>
          </div>
          <div>
            <Text strong>Tầng 1 — Logging: </Text>
            <Tag color="green">Backend xong</Tag>
          </div>
          <div>
            <Text strong>Tầng 1 — Dashboard widgets: </Text>
            <Tag color="orange">Đang phát triển</Tag>
          </div>
          <div>
            <Text strong>Tầng 2 — Risk Indicator: </Text>
            <Tag color="default">Chưa làm</Tag>
          </div>
          <div>
            <Text strong>Tầng 3 — LP Solver: </Text>
            <Tag color="default">Chưa làm</Tag>
          </div>
        </Space>
      </Card>

      <Card title="Tiếp theo">
        <Empty
          description="Các widget dashboard (heatmap, deadline timeline, risk widget) sẽ được bổ sung sau khi hoàn thiện Authentication."
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    </Space>
  );
}
