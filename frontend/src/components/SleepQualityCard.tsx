import { Card, Empty, Statistic, Progress, Space, Typography } from 'antd';
import { MoonOutlined } from '@ant-design/icons';
import type { DashboardSummary } from '../api/dashboard';

const { Text } = Typography;

interface Props {
  data: DashboardSummary;
}

export default function SleepQualityCard({ data }: Props) {
  const sleepHours = data.sleep_hours_recent;

  if (sleepHours.length === 0) {
    return (
      <Card title="Chất lượng giấc ngủ" size="small" style={{ height: '100%' }}>
        <Empty
          description="Chưa có dữ liệu giấc ngủ"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    );
  }

  const avg = sleepHours.reduce((s, h) => s + h, 0) / sleepHours.length;
  const deficit = Math.max(0, 7 - avg);
  const percent = Math.min(100, Math.round((avg / 8) * 100));

  let status = 'Tốt';
  let statusColor = '#52c41a';
  if (avg < 6) {
    status = 'Thiếu ngủ';
    statusColor = '#ff4d4f';
  } else if (avg < 7) {
    status = 'Chưa đủ';
    statusColor = '#faad14';
  }

  return (
    <Card
      title={
        <Space>
          <MoonOutlined />
          <span>Chất lượng giấc ngủ</span>
        </Space>
      }
      size="small"
      style={{ height: '100%' }}
    >
      <Space direction="vertical" size={12} style={{ width: '100%', alignItems: 'center' }}>
        <Progress
          type="dashboard"
          percent={percent}
          strokeColor={statusColor}
          format={() => (
            <div>
              <div style={{ fontSize: 22, fontWeight: 700, color: statusColor }}>
                {avg.toFixed(1)}h
              </div>
              <div style={{ fontSize: 11, color: '#999' }}>TB/ngày</div>
            </div>
          )}
          size={140}
        />
        <Space direction="vertical" size={4} style={{ width: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <Text type="secondary">Trạng thái:</Text>
            <Text strong style={{ color: statusColor }}>
              {status}
            </Text>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <Text type="secondary">Khuyến nghị:</Text>
            <Text>7-8 giờ/ngày</Text>
          </div>
          {deficit > 0 && (
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Text type="secondary">Thiếu hụt:</Text>
              <Text strong style={{ color: '#ff4d4f' }}>
                -{deficit.toFixed(1)}h/ngày
              </Text>
            </div>
          )}
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <Text type="secondary">Số ngày ghi log:</Text>
            <Text>{sleepHours.length} ngày</Text>
          </div>
        </Space>
      </Space>
    </Card>
  );
}
