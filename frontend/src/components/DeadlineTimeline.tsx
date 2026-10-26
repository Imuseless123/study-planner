import { useState } from 'react';
import { Card, Empty, Timeline, Tag, Space, Typography, Button, Dropdown, message, Tooltip } from 'antd';
import {
  ClockCircleOutlined, FileTextOutlined, WarningOutlined,
  CheckCircleOutlined, DownOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import { logsApi } from '../api/logs';
import { assignmentsApi } from '../api/assignments';
import { getErrorMessage } from '../api/client';
import type { DashboardSummary } from '../api/dashboard';

const { Text } = Typography;

interface Props {
  data: DashboardSummary;
  onRefresh?: () => void;
}

export default function DeadlineTimeline({ data, onRefresh }: Props) {
  const navigate = useNavigate();
  const now = dayjs();
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const upcoming = [...data.upcoming_assignments]
    .sort((a, b) => dayjs(a.deadline).unix() - dayjs(b.deadline).unix())
    .slice(0, 10);

  const handleLogStudy = async (assignment: any, hours: number) => {
    setLoadingId(assignment.assignment_id);
    try {
      await logsApi.createStudy({
        subject_id: assignment.subject_id,
        assignment_id: assignment.assignment_id,
        start_time: dayjs().subtract(hours, 'hour').toISOString(),
        duration: hours,
        focus_level: 3,
      });
      message.success(`Đã ghi ${hours}h cho: ${assignment.title}`);
      onRefresh?.();
    } catch (err) {
      message.error(getErrorMessage(err));
    } finally {
      setLoadingId(null);
    }
  };

  const handleMarkDone = async (assignment: any) => {
    setLoadingId(assignment.assignment_id);
    try {
      await assignmentsApi.update(assignment.assignment_id, { is_completed: true });
      message.success(`Đã xong: ${assignment.title}`);
      onRefresh?.();
    } catch (err) {
      message.error(getErrorMessage(err));
    } finally {
      setLoadingId(null);
    }
  };

  if (upcoming.length === 0) {
    return (
      <Card title="Deadline sắp tới" size="small" style={{ height: '100%' }}>
        <Empty description="Không có deadline nào trong 30 ngày tới" image={Empty.PRESENTED_IMAGE_SIMPLE} />
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

    if (days < 0) { color = '#ff4d4f'; label = `Quá hạn`; icon = <WarningOutlined />; }
    else if (hours < 24) { color = '#ff4d4f'; label = `Còn ${hours} giờ`; }
    else if (days === 1) { color = '#fa8c16'; label = 'Ngày mai'; }
    else if (days <= 3) { color = '#fa8c16'; label = `Còn ${days} ngày`; }
    else if (days <= 7) { color = '#1890ff'; label = `Còn ${days} ngày`; }
    else { label = `Còn ${days} ngày`; }

    return {
      color,
      dot: icon,
      children: (
        <div style={{ marginBottom: 8, opacity: loadingId === a.assignment_id ? 0.5 : 1 }}>
          <Space direction="vertical" size={4} style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <Text strong style={{ fontSize: 13 }}>{a.title}</Text>
              
              {/* Action buttons */}
              <Space size={4}>
                <Dropdown
                  menu={{
                    items: [
                      { key: '15', label: '15 phút' },
                      { key: '30', label: '30 phút' },
                      { key: '60', label: '1 giờ' },
                    ],
                    onClick: ({ key }) => handleLogStudy(a, parseInt(key) / 60),
                  }}
                  disabled={loadingId !== null}
                >
                  <Button size="small" type="text" icon={<ClockCircleOutlined />} style={{ fontSize: 12, color: '#1677ff' }}>
                    Đã học <DownOutlined style={{ fontSize: 8 }} />
                  </Button>
                </Dropdown>
                <Tooltip title="Đánh dấu hoàn thành">
                  <Button 
                    size="small" 
                    type="text" 
                    icon={<CheckCircleOutlined />} 
                    onClick={() => handleMarkDone(a)}
                    disabled={loadingId !== null}
                    style={{ color: '#52c41a' }}
                  />
                </Tooltip>
              </Space>
            </div>
            
            <Space size={6} wrap>
              <Tag color="blue" style={{ fontSize: 11 }}>
                {data.subjects.find((s) => s.subject_id === a.subject_id)?.subject_name || 'N/A'}
              </Tag>
              <Tag color={color} style={{ fontSize: 11 }}>{label}</Tag>
            </Space>
            
            <Text type="secondary" style={{ fontSize: 11 }}>
              📅 {deadline.format('DD/MM/YYYY HH:mm')} • {a.required_hours}h chuẩn bị • Ưu tiên {a.priority}/5
            </Text>
          </Space>
        </div>
      ),
    };
  });

  return (
    <Card
      title={<Space><FileTextOutlined /><span>Deadline sắp tới</span><Tag color="blue">{upcoming.length}</Tag></Space>}
      size="small"
      style={{ height: '100%' }}
      extra={<Button type="link" size="small" onClick={() => navigate('/assignments')}>Xem tất cả</Button>}
    >
      <div style={{ maxHeight: 400, overflowY: 'auto', paddingRight: 8 }}>
        <Timeline items={items} />
      </div>
    </Card>
  );
}
