import { Card, Col, Row, Statistic, Tag, Space, Progress } from 'antd';
import {
  ClockCircleOutlined, MoonOutlined, FileTextOutlined,
  FireOutlined, RiseOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { DashboardSummary } from '../api/dashboard';

interface Props {
  data: DashboardSummary;
}

export default function StatisticsCards({ data }: Props) {
  // 1. Tổng giờ học 7 ngày
  const totalStudyHours = Object.values(data.study_hours_by_date).reduce(
    (sum, h) => sum + h,
    0,
  );

  // 2. TB giấc ngủ
  const avgSleep =
    data.sleep_hours_recent.length > 0
      ? data.sleep_hours_recent.reduce((s, h) => s + h, 0) /
        data.sleep_hours_recent.length
      : 0;

  // 3. Bài tập sắp tới hạn (≤3 ngày)
  const now = dayjs();
  const dueSoonCount = data.upcoming_assignments.filter((a) => {
    const days = dayjs(a.deadline).diff(now, 'day');
    return days <= 3 && days >= 0;
  }).length;

  // 4. Streak — số ngày liên tiếp có ghi log
  const streak = calculateStreak(data.study_hours_by_date);

  return (
    <Row gutter={[16, 16]}>
      <Col xs={12} sm={12} md={6}>
        <Card size="small" hoverable>
          <Statistic
            title="Giờ học (7 ngày)"
            value={totalStudyHours}
            precision={1}
            suffix="h"
            prefix={<ClockCircleOutlined />}
            valueStyle={{ color: '#667eea' }}
          />
        </Card>
      </Col>

      <Col xs={12} sm={12} md={6}>
        <Card size="small" hoverable>
          <Statistic
            title="TB giấc ngủ"
            value={avgSleep}
            precision={1}
            suffix="h"
            prefix={<MoonOutlined />}
            valueStyle={{
              color: avgSleep >= 7 ? '#52c41a' : avgSleep >= 6 ? '#faad14' : '#ff4d4f',
            }}
          />
        </Card>
      </Col>

      <Col xs={12} sm={12} md={6}>
        <Card size="small" hoverable>
          <Statistic
            title="Bài tập sắp tới hạn"
            value={dueSoonCount}
            prefix={<FileTextOutlined />}
            valueStyle={{ color: dueSoonCount > 0 ? '#fa8c16' : '#52c41a' }}
            suffix={<span style={{ fontSize: 12, color: '#999' }}>≤3 ngày</span>}
          />
        </Card>
      </Col>

      <Col xs={12} sm={12} md={6}>
        <Card size="small" hoverable>
          <Statistic
            title="Chuỗi ngày học"
            value={streak}
            suffix="ngày"
            prefix={<FireOutlined />}
            valueStyle={{ color: streak >= 3 ? '#fa541c' : '#999' }}
          />
        </Card>
      </Col>
    </Row>
  );
}

function calculateStreak(studyHours: Record<string, number>): number {
  const days = Object.keys(studyHours)
    .filter((d) => studyHours[d] > 0)
    .sort()
    .reverse();

  if (days.length === 0) return 0;

  const today = dayjs().startOf('day');
  const mostRecent = dayjs(days[0]).startOf('day');

  // Nếu ngày gần nhất không phải hôm nay hoặc hôm qua → streak = 0
  const dayDiff = today.diff(mostRecent, 'day');
  if (dayDiff > 1) return 0;

  let streak = 1;
  for (let i = 1; i < days.length; i++) {
    const curr = dayjs(days[i - 1]).startOf('day');
    const prev = dayjs(days[i]).startOf('day');
    if (curr.diff(prev, 'day') === 1) {
      streak++;
    } else {
      break;
    }
  }
  return streak;
}
