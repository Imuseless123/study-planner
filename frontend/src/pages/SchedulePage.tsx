import { useCallback, useEffect, useState } from 'react';
import {
  Typography, Button, Card, Space, Alert, Spin, Empty, Tag, Row, Col,
  Statistic, Divider, Modal, Rate, Input, message, Tooltip,
} from 'antd';
import {
  ThunderboltOutlined, ReloadOutlined, ClockCircleOutlined,
  WarningOutlined, StarOutlined, InfoCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';

import { scheduleApi, ScheduleResponse } from '../api/schedule';
import { subjectsApi, Subject } from '../api/subjects';
import { feedbackApi } from '../api/feedback';
import { getErrorMessage } from '../api/client';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const SLOT_LABELS = ['🌅 Sáng', '☀️ Chiều', '🌙 Tối'];
const SLOT_BG = ['#fff7e6', '#e6f4ff', '#f9f0ff'];

export default function SchedulePage() {
  const [data, setData] = useState<ScheduleResponse | null>(null);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);

  // Feedback modal
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');
  const [submittingFeedback, setSubmittingFeedback] = useState(false);

  const fetchSubjects = useCallback(async () => {
    try {
      const list = await subjectsApi.list();
      setSubjects(list);
    } catch {
      // ignore
    }
  }, []);

  const fetchLatest = useCallback(async () => {
    setInitialLoading(true);
    try {
      const res = await scheduleApi.latest();
      setData(res);
    } catch (err: any) {
      if (err?.response?.status !== 404) {
        message.error(getErrorMessage(err));
      }
    } finally {
      setInitialLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSubjects();
    fetchLatest();
  }, [fetchSubjects, fetchLatest]);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const res = await scheduleApi.generate();
      setData(res);
      if (!res.feasible) {
        message.warning('Không thể tạo lịch — xem chi tiết bên dưới.');
      } else {
        message.success('Đã tạo lịch tối ưu');
      }
    } catch (err) {
      message.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitFeedback = async () => {
    if (!data?.schedule_id) return;
    if (rating < 1) {
      message.warning('Vui lòng chọn số sao');
      return;
    }
    setSubmittingFeedback(true);
    try {
      await feedbackApi.create({
        schedule_id: data.schedule_id,
        rating,
        comment: comment.trim() || undefined,
      });
      message.success('Cảm ơn phản hồi của bạn!');
      setFeedbackOpen(false);
      setRating(0);
      setComment('');
    } catch (err) {
      message.error(getErrorMessage(err));
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const getSubjectName = (id: string) => {
    // assignment_id based — subject_id được dùng nhưng ta map qua danh sách
    return subjects.find((s) => s.subject_id === id)?.subject_name || `#${id.slice(0, 6)}`;
  };

  // Nhóm sessions theo (day, slot)
  const groupSessions = () => {
    if (!data?.schedule) return {};
    const grouped: Record<string, { subject_id: string; hours: number }[]> = {};
    for (const entry of data.schedule) {
      const key = `${entry.day}-${entry.slot}`;
      if (!grouped[key]) grouped[key] = [];
      grouped[key].push({ subject_id: entry.subject_id, hours: entry.hours });
    }
    return grouped;
  };

  if (initialLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  const grouped = groupSessions();
  const horizon = data?.horizon_days || 7;

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between',
        alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <Title level={2} style={{ marginBottom: 4 }}>
            Lịch học tối ưu
          </Title>
          <Text type="secondary">
            Tạo lịch học tự động dựa trên deadline, độ khó, ưu tiên và rủi ro hiện tại.
          </Text>
        </div>
        <Space>
          {data?.schedule_id && (
            <Button
              icon={<StarOutlined />}
              onClick={() => setFeedbackOpen(true)}
            >
              Đánh giá
            </Button>
          )}
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            onClick={handleGenerate}
            loading={loading}
          >
            {data ? 'Tạo lại' : 'Tạo lịch'}
          </Button>
        </Space>
      </div>

      {/* Meta info */}
      {data && data.feasible && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col xs={12} sm={6}>
              <Statistic
                title="Rủi ro"
                value={data.risk_score_at_generation ?? 0}
                precision={1}
                suffix="/ 100"
                valueStyle={{
                  color: (data.risk_score_at_generation ?? 0) <= 30 ? '#52c41a'
                    : (data.risk_score_at_generation ?? 0) <= 60 ? '#faad14' : '#ff4d4f',
                }}
              />
            </Col>
            <Col xs={12} sm={6}>
              <Statistic
                title="Mức"
                value={(data.risk_level || 'low').toUpperCase()}
                valueStyle={{ fontSize: 16 }}
              />
            </Col>
            <Col xs={12} sm={6}>
              <Statistic
                title="Giới hạn ngày"
                value={data.w_max_effective ?? 0}
                precision={1}
                suffix="h"
              />
            </Col>
            <Col xs={12} sm={6}>
              <Statistic
                title="Mục tiêu"
                value={data.objective_value ?? 0}
                precision={1}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* Warnings */}
      {data?.warnings && data.warnings.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          {data.warnings.map((w, i) => (
            <Alert
              key={i}
              type="warning"
              showIcon
              icon={<WarningOutlined />}
              message={w.type}
              description={w.message}
              style={{ marginBottom: 8 }}
            />
          ))}
        </div>
      )}

      {/* Infeasible */}
      {data && !data.feasible && (
        <Alert
          type="error"
          showIcon
          message="Không thể tạo lịch"
          description={
            <div>
              <Paragraph>
                Solver không tìm được lịch khả thi với ràng buộc hiện tại.
                {data.status === 'no_assignments' && ' Bạn chưa có bài tập nào sắp tới.'}
              </Paragraph>
              {data.explanation && (
                <Text type="secondary">
                  Xem chi tiết cảnh báo ở trên hoặc thử giảm số bài tập.
                </Text>
              )}
            </div>
          }
        />
      )}

      {/* Calendar grid */}
      {data && data.feasible && data.schedule.length > 0 && (
        <Card title="Lịch tuần" size="small" style={{ marginBottom: 16 }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{
              borderCollapse: 'collapse',
              minWidth: 700,
              width: '100%',
            }}>
              <thead>
                <tr>
                  <th style={{
                    padding: 8, textAlign: 'left', borderBottom: '2px solid #f0f0f0',
                    background: '#fafafa', minWidth: 100,
                  }}>
                    Khung giờ
                  </th>
                  {Array.from({ length: horizon }).map((_, d) => {
                    const date = dayjs().add(d, 'day');
                    const isToday = d === 0;
                    return (
                      <th key={d} style={{
                        padding: 8, textAlign: 'center',
                        borderBottom: '2px solid #f0f0f0',
                        background: isToday ? '#e6f4ff' : '#fafafa',
                        color: isToday ? '#667eea' : '#666',
                      }}>
                        <div style={{ fontWeight: 600 }}>{date.format('ddd')}</div>
                        <div style={{ fontSize: 11, color: '#999' }}>
                          {date.format('DD/MM')}
                        </div>
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody>
                {SLOT_LABELS.map((slotLabel, t) => (
                  <tr key={t}>
                    <td style={{
                      padding: 8, fontWeight: 500, fontSize: 12,
                      borderRight: '1px solid #f0f0f0',
                      background: SLOT_BG[t],
                      minWidth: 100,
                    }}>
                      {slotLabel}
                    </td>
                    {Array.from({ length: horizon }).map((_, d) => {
                      const key = `${d}-${t}`;
                      const sessions = grouped[key] || [];
                      return (
                        <td key={d} style={{
                          padding: 4,
                          borderRight: '1px solid #f5f5f5',
                          borderBottom: '1px solid #f5f5f5',
                          verticalAlign: 'top',
                          minHeight: 60,
                          background: d === 0 ? '#fafcff' : 'white',
                        }}>
                          {sessions.length === 0 ? (
                            <div style={{ minHeight: 40 }} />
                          ) : (
                            <Space direction="vertical" size={2} style={{ width: '100%' }}>
                              {sessions.map((s, i) => (
                                <Tooltip key={i} title={`${s.hours}h`}>
                                  <Tag
                                    color="blue"
                                    style={{
                                      width: '100%',
                                      textOverflow: 'ellipsis',
                                      overflow: 'hidden',
                                      fontSize: 11,
                                      margin: 0,
                                    }}
                                  >
                                    {getSubjectName(s.subject_id)} · {s.hours}h
                                  </Tag>
                                </Tooltip>
                              ))}
                            </Space>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Explanation */}
      {data && data.feasible && data.explanation && (
        <Row gutter={16}>
          <Col xs={24} md={12}>
            <Card title="Theo bài tập" size="small">
              <Space direction="vertical" size={8} style={{ width: '100%' }}>
                {data.explanation.per_subject.map((s) => (
                  <div key={s.subject_id} style={{
                    padding: '8px 12px',
                    background: '#fafafa',
                    borderRadius: 6,
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: 12,
                  }}>
                    <span style={{ fontWeight: 500 }}>
                      {getSubjectName(s.subject_id)}
                    </span>
                    <Space size={12}>
                      <Text type="secondary">
                        {s.scheduled_hours}h / {s.required_hours}h
                      </Text>
                      {s.deadline_shortfall > 0 && (
                        <Tag color="red" style={{ fontSize: 11 }}>
                          Thiếu {s.deadline_shortfall}h
                        </Tag>
                      )}
                    </Space>
                  </div>
                ))}
              </Space>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card title="Theo ngày" size="small">
              <Space direction="vertical" size={8} style={{ width: '100%' }}>
                {data.explanation.per_day
                  .filter((d) => d.total_hours > 0)
                  .map((d) => (
                    <div key={d.day} style={{
                      padding: '8px 12px',
                      background: d.overload > 0 ? '#fff1f0' : '#fafafa',
                      borderRadius: 6,
                      display: 'flex',
                      justifyContent: 'space-between',
                      fontSize: 12,
                    }}>
                      <span style={{ fontWeight: 500 }}>
                        Ngày {d.day} ({dayjs().add(d.day, 'day').format('DD/MM')})
                      </span>
                      <Space size={12}>
                        <span>{d.total_hours}h</span>
                        {d.overload > 0 && (
                          <Tag color="red" style={{ fontSize: 11 }}>
                            Vượt {d.overload}h
                          </Tag>
                        )}
                      </Space>
                    </div>
                  ))}
              </Space>
            </Card>
          </Col>
        </Row>
      )}

      {/* Empty state */}
      {!data && !loading && (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <Space direction="vertical">
              <Text>Bạn chưa tạo lịch học nào.</Text>
              <Button
                type="primary"
                icon={<ThunderboltOutlined />}
                onClick={handleGenerate}
              >
                Tạo lịch ngay
              </Button>
            </Space>
          }
        />
      )}

      {/* Feedback Modal */}
      <Modal
        title="Đánh giá lịch học"
        open={feedbackOpen}
        onCancel={() => setFeedbackOpen(false)}
        onOk={handleSubmitFeedback}
        okText="Gửi đánh giá"
        cancelText="Hủy"
        confirmLoading={submittingFeedback}
        destroyOnClose
      >
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div>
            <Text strong>Mức độ hài lòng:</Text>
            <div style={{ marginTop: 8 }}>
              <Rate value={rating} onChange={setRating} />
            </div>
          </div>
          <div>
            <Text strong>Nhận xét (không bắt buộc):</Text>
            <TextArea
              rows={3}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Lịch có hợp lý không? Có điều gì cần cải thiện?"
              maxLength={500}
              showCount
              style={{ marginTop: 8 }}
            />
          </div>
          <Alert
            type="info"
            showIcon
            icon={<InfoCircleOutlined />}
            message="Phản hồi giúp cải thiện chất lượng lịch trong tương lai"
            style={{ fontSize: 12 }}
          />
        </Space>
      </Modal>
    </div>
  );
}
