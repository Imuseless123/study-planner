import { Card, Empty } from 'antd';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import dayjs from 'dayjs';
import type { DashboardSummary } from '../api/dashboard';

interface Props {
  data: DashboardSummary;
}

export default function WeeklyStudyChart({ data }: Props) {
  // Tạo 7 ngày gần nhất (bao gồm hôm nay)
  const today = dayjs();
  const chartData = [];

  for (let i = 6; i >= 0; i--) {
    const date = today.subtract(i, 'day');
    const key = date.format('YYYY-MM-DD');
    const hours = data.study_hours_by_date[key] || 0;
    chartData.push({
      day: date.format('ddd'),
      date: date.format('DD/MM'),
      hours,
      fullDate: key,
    });
  }

  const hasData = chartData.some((d) => d.hours > 0);

  return (
    <Card title="Giờ học 7 ngày gần đây" size="small" style={{ height: '100%' }}>
      {!hasData ? (
        <Empty description="Chưa có dữ liệu" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="day"
              tick={{ fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              label={{
                value: 'Giờ',
                angle: -90,
                position: 'insideLeft',
                style: { fontSize: 11, fill: '#999' },
              }}
            />
            <Tooltip
              contentStyle={{
                borderRadius: 8,
                border: 'none',
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
              }}
              formatter={(value: number) => [`${value}h`, 'Giờ học']}
              labelFormatter={(label, payload) => {
                const item = payload?.[0]?.payload;
                return item ? `${label} (${item.date})` : label;
              }}
            />
            <ReferenceLine
              y={3}
              stroke="#faad14"
              strokeDasharray="3 3"
              label={{
                value: 'Mục tiêu 3h',
                position: 'right',
                style: { fontSize: 10, fill: '#faad14' },
              }}
            />
            <Bar
              dataKey="hours"
              fill="#667eea"
              radius={[6, 6, 0, 0]}
              maxBarSize={40}
            />
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}
