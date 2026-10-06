import { Card, Empty, Timeline, Tag, Space, Typography, Button } from 'antd';
import {
  ClockCircleOutlined,
  FileTextOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import type { DashboardSummary } from '../api/dashboard';

const { Text } = Typography;

interface Props {
  data: DashboardSummary;
}

export default function DeadlineTimeline({ data }: Props) {
  const navigate = useNavigate();
  const now = dayjs();

  // Sort theo deadline, chỉ lấy 10 bài sắp tới
  const upcoming = [...data.upcoming_assignments]
    .sort((a, b) => dayjs(a.deadline).unix() - dayjs(b.deadline).unix())
    .slice(0, 10);

  if (upcoming.length === 0) {
    return (
      <Card title="Deadline sắp tới" size="small" style={{ height: '100%' }}>
        <Empty
          description="Không có deadline nào trong 30 ngày tới"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    );
  }

  const items = upcoming.map((a) => {
    const deadline = dayjs(a.deadline);
    const days = deadline.diff(now, 'day');
    const hours = deadline.diff(now, 'hour');

    let color = '#52c41a';
    let label = '';
    let icon = <ClockCircleOutlined />;

    if (days < 0) {
      color = '#ff4d4f';
      label = `Quá hạn ${Math.abs(days)} ngày`;
      icon = <WarningOutlined />;
    } else if (hours < 24) {
      color = '#ff4d4f';
      label = `Còn ${hours} giờ`;
    } else if (days === 0) {
      color = '#ff4d4f';
      label = 'Hôm nay';
    } else if (days === 1) {
      color = '#fa8c16';
      label = 'Ngày mai';
    } else if (days <= 3) {
      color = '#fa8c16';
      label = `Còn ${days} ngày`;
    } else if (days <= 7) {
      color = '#1890ff';
      label = `Còn ${days} ngày`;
    } else {
      label = `Còn ${days} ngày`;
    }

    return {
      color,
      dot: icon,
      children: (
        <div style={{ marginBottom: 4 }}>
          <Space direction="vertical" size={2} style={{ width: '100%' }}>
            <Text strong style={{ fontSize: 13 }}>
              {a.title}
            </Text>
            <Space size={6} wrap>
              <Tag color="blue" style={{ fontSize: 11 }}>
                {data.subjects.find((s) => s.subject_id === a.subject_id)
                  ?.subject_name || 'N/A'}
              </Tag>
              <Tag color={color} style={{ fontSize: 11 }}>
                {label}
              </Tag>
            </Space>
            <Text type="secondary" style={{ fontSize: 11 }}>
              📅 {deadline.format('DD/MM/YYYY HH:mm')} •{' '}
              {a.required_hours}h chuẩn bị • Ưu tiên {a.priority}/5
            </Text>
          </Space>
        </div>
      ),
    };
  });

  return (
    <Card
      title={
        <Space>
          <FileTextOutlined />
          <span>Deadline sắp tới</span>
          <Tag color="blue">{upcoming.length}</Tag>
        </Space>
      }
      size="small"
      style={{ height: '100%' }}
      extra={
        <Button type="link" size="small" onClick={() => navigate('/assignments')}>
          Xem tất cả
        </Button>
      }
    >
      <div style={{ maxHeight: 360, overflowY: 'auto', paddingRight: 8 }}>
        <Timeline items={items} />
      </div>
    </Card>
  );
}
