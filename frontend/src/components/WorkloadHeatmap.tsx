import { Card, Empty, Tooltip, Space, Tag, Typography, Row, Col } from 'antd';
import dayjs from 'dayjs';
import type { DashboardSummary } from '../api/dashboard';

const { Text } = Typography;

interface Props {
  data: DashboardSummary;
}

// Palette màu theo cường độ
const getColorForHours = (hours: number): string => {
  if (hours === 0) return '#f5f5f5';
  if (hours < 1) return '#e6f4ff';
  if (hours < 2) return '#91caff';
  if (hours < 3) return '#4096ff';
  if (hours < 4) return '#1677ff';
  if (hours < 6) return '#0958d9';
  return '#003eb3';
};

const getTextColorForHours = (hours: number): string => {
  if (hours === 0) return '#bbb';
  if (hours < 2) return '#333';
  return '#fff';
};

export default function WorkloadHeatmap({ data }: Props) {
  // Lấy danh sách subjects
  const subjects = data.subjects.map((s) => s.subject_name);

  // Tạo 7 ngày gần nhất
  const today = dayjs();
  const days = [];
  for (let i = 6; i >= 0; i--) {
    const d = today.subtract(i, 'day');
    days.push({
      key: d.format('YYYY-MM-DD'),
      dayLabel: d.format('ddd'),
      dateLabel: d.format('DD/MM'),
      isToday: i === 0,
    });
  }

  // Nếu chưa có subject nào → empty
  if (subjects.length === 0) {
    return (
      <Card title="Bản đồ nhiệt khối lượng" size="small" style={{ height: '100%' }}>
        <Empty
          description="Chưa có môn học nào"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    );
  }

  return (
    <Card title="Bản đồ nhiệt khối lượng" size="small" style={{ height: '100%' }}>
      <div style={{ overflowX: 'auto', paddingBottom: 8 }}>
        <table
          style={{
            borderCollapse: 'separate',
            borderSpacing: 3,
            fontSize: 12,
            minWidth: 500,
            width: '100%',
          }}
        >
          <thead>
            <tr>
              <th style={{ width: 110, textAlign: 'left', padding: 4 }}></th>
              {days.map((d) => (
                <th
                  key={d.key}
                  style={{
                    padding: 4,
                    textAlign: 'center',
                    fontWeight: d.isToday ? 700 : 400,
                    color: d.isToday ? '#667eea' : '#666',
                  }}
                >
                  <div>{d.dayLabel}</div>
                  <div style={{ fontSize: 10, color: '#999' }}>{d.dateLabel}</div>
                </th>
              ))}
              <th
                style={{
                  padding: 4,
                  textAlign: 'center',
                  fontWeight: 700,
                  color: '#667eea',
                }}
              >
                Tổng
              </th>
            </tr>
          </thead>
          <tbody>
            {subjects.map((subj) => {
              let rowTotal = 0;
              return (
                <tr key={subj}>
                  <td
                    style={{
                      padding: 4,
                      fontWeight: 500,
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      maxWidth: 110,
                    }}
                  >
                    <Tooltip title={subj}>
                      <span>{subj}</span>
                    </Tooltip>
                  </td>
                  {days.map((d) => {
                    const hours =
                      data.study_hours_matrix[d.key]?.[subj] || 0;
                    rowTotal += hours;
                    const bg = getColorForHours(hours);
                    const fg = getTextColorForHours(hours);
                    return (
                      <td key={d.key} style={{ padding: 0 }}>
                        <Tooltip
                          title={
                            hours > 0
                              ? `${subj} • ${d.dateLabel}: ${hours.toFixed(2)}h`
                              : `${subj} • ${d.dateLabel}: chưa học`
                          }
                        >
                          <div
                            style={{
                              width: '100%',
                              height: 36,
                              background: bg,
                              borderRadius: 4,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              color: fg,
                              fontWeight: hours >= 2 ? 600 : 400,
                              cursor: 'pointer',
                              transition: 'all 0.2s',
                              fontSize: 11,
                            }}
                          >
                            {hours > 0 ? hours.toFixed(1) : ''}
                          </div>
                        </Tooltip>
                      </td>
                    );
                  })}
                  <td
                    style={{
                      padding: 4,
                      textAlign: 'center',
                      fontWeight: 600,
                      color: '#667eea',
                    }}
                  >
                    {rowTotal.toFixed(1)}h
                  </td>
                </tr>
              );
            })}

            {/* Row "Tổng ngày" */}
            <tr>
              <td
                style={{
                  padding: 4,
                  fontWeight: 700,
                  color: '#667eea',
                  borderTop: '2px solid #f0f0f0',
                }}
              >
                Tổng ngày
              </td>
              {days.map((d) => {
                const total = Object.values(
                  data.study_hours_matrix[d.key] || {},
                ).reduce((s, h) => s + h, 0);
                return (
                  <td
                    key={d.key}
                    style={{
                      padding: 4,
                      textAlign: 'center',
                      fontWeight: 600,
                      color: total > 0 ? '#667eea' : '#bbb',
                      borderTop: '2px solid #f0f0f0',
                    }}
                  >
                    {total > 0 ? `${total.toFixed(1)}h` : '—'}
                  </td>
                );
              })}
              <td
                style={{
                  padding: 4,
                  textAlign: 'center',
                  fontWeight: 700,
                  color: '#667eea',
                  borderTop: '2px solid #f0f0f0',
                }}
              >
                {Object.values(data.study_hours_matrix)
                  .flatMap((day) => Object.values(day))
                  .reduce((s, h) => s + h, 0)
                  .toFixed(1)}
                h
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div style={{ marginTop: 12 }}>
        <Space size={4} wrap>
          <Text type="secondary" style={{ fontSize: 11 }}>
            Cường độ:
          </Text>
          {[
            { h: 0, label: '0' },
            { h: 0.5, label: '<1h' },
            { h: 1.5, label: '1-2h' },
            { h: 2.5, label: '2-3h' },
            { h: 3.5, label: '3-4h' },
            { h: 5, label: '4-6h' },
            { h: 8, label: '>6h' },
          ].map((item) => (
            <Space key={item.label} size={4}>
              <div
                style={{
                  width: 16,
                  height: 16,
                  background: getColorForHours(item.h),
                  borderRadius: 3,
                }}
              />
              <Text style={{ fontSize: 11 }}>{item.label}</Text>
            </Space>
          ))}
        </Space>
      </div>
    </Card>
  );
}
