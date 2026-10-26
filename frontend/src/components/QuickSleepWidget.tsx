import { useEffect, useState } from 'react';
import { Card, Space, Typography, message, Button, Tag } from 'antd';
import dayjs from 'dayjs';
import { logsApi } from '../api/logs';
import { getErrorMessage } from '../api/client';
import { useAuthStore } from '../store/authStore';

const { Text } = Typography;

const QUALITY_LEVELS = [
  { emoji: '😫', label: 'Rất kém' },
  { emoji: '😟', label: 'Kém' },
  { emoji: '😐', label: 'Tạm được' },
  { emoji: '🙂', label: 'Tốt' },
  { emoji: '😄', label: 'Rất tốt' },
];

interface Props {
  onLogged?: () => void;
}

/**
 * Quick sleep logger — user only picks quality.
 * Auto-computes:
 *   - wake_time = now (user just woke up)
 *   - sleep_time = yesterday at usual_bedtime (if bedtime is evening)
 *                 or today at usual_bedtime (if bedtime is early morning)
 *   - hours = wake - sleep
 */
export default function QuickSleepWidget({ onLogged }: Props) {
  const user = useAuthStore((s) => s.user);
  const [submitting, setSubmitting] = useState<number | null>(null);
  const [lastChoice, setLastChoice] = useState<number | null>(null);
  const [preview, setPreview] = useState<{ sleep: string; wake: string; hours: number } | null>(null);

  const bedtime = user?.usual_bedtime || '23:00:00';

  // Compute preview on mount
  useEffect(() => {
    const now = dayjs();
    const [h, m] = bedtime.split(':').map(Number);
    const bedtimeToday = now.hour(h).minute(m).second(0).millisecond(0);

    let sleepTime = bedtimeToday;
    if (bedtimeToday.isAfter(now)) {
      sleepTime = bedtimeToday.subtract(1, 'day');
    }

    const wakeTime = now.second(0).millisecond(0);
    const hours = Math.max(0, wakeTime.diff(sleepTime, 'minute') / 60);

    setPreview({
      sleep: sleepTime.format('DD/MM HH:mm'),
      wake: wakeTime.format('DD/MM HH:mm'),
      hours: Math.round(hours * 10) / 10,
    });
  }, [bedtime]);

  const handleTap = async (qualityIndex: number) => {
    setSubmitting(qualityIndex);
    try {
      const now = dayjs();
      const [h, m] = bedtime.split(':').map(Number);
      const bedtimeToday = now.hour(h).minute(m).second(0).millisecond(0);

      let sleepTime = bedtimeToday;
      if (bedtimeToday.isAfter(now)) {
        sleepTime = bedtimeToday.subtract(1, 'day');
      }
      const wakeTime = now.second(0).millisecond(0);

      const hours = Math.max(0, wakeTime.diff(sleepTime, 'minute') / 60);
      if (hours < 0.5) {
        message.warning('Thời gian ngủ quá ngắn. Kiểm tra lại giờ đi ngủ trong Cài đặt.');
        setSubmitting(null);
        return;
      }
      if (hours > 16) {
        message.warning('Thời gian ngủ > 16h. Kiểm tra lại giờ đi ngủ trong Cài đặt.');
        setSubmitting(null);
        return;
      }

      await logsApi.createSleep({
        sleep_time: sleepTime.toISOString(),
        wake_time: wakeTime.toISOString(),
        quality: qualityIndex + 1,
      });

      setLastChoice(qualityIndex);
      message.success(`Đã ghi: ${hours.toFixed(1)}h ngủ`);
      onLogged?.();
    } catch (err) {
      message.error(getErrorMessage(err));
    } finally {
      setSubmitting(null);
    }
  };

  return (
    <Card
      size="small"
      style={{
        background: 'linear-gradient(135deg, #f0f5ff 0%, #f9f0ff 100%)',
        border: '1px solid #adc6ff',
        height: '100%',
      }}
    >
      <Space direction="vertical" size={10} style={{ width: '100%' }}>
        <div>
          <Text strong style={{ fontSize: 13 }}>🌙 Vừa thức dậy?</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 11 }}>
            Chọn chất lượng giấc ngủ — hệ thống tự tính giờ
          </Text>
        </div>

        {preview && (
          <div style={{
            background: 'rgba(255,255,255,0.7)',
            padding: '6px 10px',
            borderRadius: 6,
            fontSize: 11,
          }}>
            <Space size={4} wrap>
              <Tag color="blue" style={{ fontSize: 10 }}>
                Ngủ: {preview.sleep}
              </Tag>
              <Tag color="green" style={{ fontSize: 10 }}>
                Thức: {preview.wake}
              </Tag>
              <Tag color="purple" style={{ fontSize: 10 }}>
                ≈ {preview.hours}h
              </Tag>
            </Space>
            <div style={{ marginTop: 4, color: '#999', fontSize: 10 }}>
              Giờ ngủ thông thường: {bedtime.slice(0, 5)} (đổi trong Cài đặt)
            </div>
          </div>
        )}

        <Space size={6} style={{ width: '100%', justifyContent: 'space-between' }}>
          {QUALITY_LEVELS.map((m, i) => (
            <button
              key={i}
              onClick={() => handleTap(i)}
              disabled={submitting !== null}
              title={m.label}
              style={{
                flex: 1,
                height: 48,
                fontSize: 24,
                background: lastChoice === i ? 'rgba(102, 126, 234, 0.15)' : 'white',
                border: lastChoice === i ? '2px solid #667eea' : '1px solid #e8e8e8',
                borderRadius: 10,
                cursor: submitting !== null ? 'wait' : 'pointer',
                transition: 'all 0.15s',
                opacity: submitting === i ? 0.5 : 1,
              }}
            >
              {m.emoji}
            </button>
          ))}
        </Space>

        {lastChoice !== null && (
          <div style={{ textAlign: 'right' }}>
            <Button type="link" size="small" onClick={() => setLastChoice(null)}>
              Ghi lại
            </Button>
          </div>
        )}
      </Space>
    </Card>
  );
}
