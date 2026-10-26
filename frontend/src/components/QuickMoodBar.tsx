import { useEffect, useState } from 'react';
import { Card, Space, Typography, message, Button } from 'antd';
import dayjs from 'dayjs';
import { logsApi } from '../api/logs';
import { getErrorMessage } from '../api/client';

const { Text } = Typography;

const ENERGY_LEVELS = [
  { emoji: '😴', label: 'Kiệt sức' },
  { emoji: '😐', label: 'Uể oải' },
  { emoji: '🙂', label: 'Bình thường' },
  { emoji: '😃', label: 'Tốt' },
  { emoji: '🚀', label: 'Tràn đầy' },
];

const STRESS_LEVELS = [
  { emoji: '😌', label: 'Thư giãn' },
  { emoji: '🙂', label: 'Nhẹ nhàng' },
  { emoji: '😐', label: 'Bình thường' },
  { emoji: '😟', label: 'Lo lắng' },
  { emoji: '😫', label: 'Rất căng' },
];

interface Props {
  onLogged?: () => void;
}

/**
 * 1-tap mood logger — 2 rows: Energy (1-5) + Stress (1-5).
 * Auto-submits when both selected. Date = today.
 * Uses upsert (updates if same-day exists).
 */
export default function QuickMoodBar({ onLogged }: Props) {
  const [energy, setEnergy] = useState<number | null>(null);
  const [stress, setStress] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [saved, setSaved] = useState(false);

  // Auto-submit when both selected
  useEffect(() => {
    if (energy === null || stress === null) return;
    if (submitting) return;

    (async () => {
      setSubmitting(true);
      try {
        await logsApi.createMood({
          log_date: dayjs().format('YYYY-MM-DD'),
          energy_level: energy + 1,   // index 0-4 → level 1-5
          stress_level: stress + 1,
        });
        setSaved(true);
        message.success('Đã ghi: ' + ENERGY_LEVELS[energy].emoji + ' + ' + STRESS_LEVELS[stress].emoji);
        onLogged?.();
      } catch (err) {
        message.error(getErrorMessage(err));
      } finally {
        setSubmitting(false);
      }
    })();
  }, [energy, stress, submitting, onLogged]);

  const reset = () => {
    setEnergy(null);
    setStress(null);
    setSaved(false);
  };

  return (
    <Card
      size="small"
      style={{
        background: 'linear-gradient(135deg, #f6ffed 0%, #e6f7ff 100%)',
        border: '1px solid #b7eb8f',
        height: '100%',
      }}
    >
      <Space direction="vertical" size={10} style={{ width: '100%' }}>
        <div>
          <Text strong style={{ fontSize: 13 }}>Hôm nay bạn cảm thấy thế nào?</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 11 }}>
            Chọn 1 emoji mỗi hàng — tự động ghi nhật ký
          </Text>
        </div>

        {/* Energy row */}
        <div>
          <Text style={{ fontSize: 11, color: '#8c8c8c', marginBottom: 4, display: 'block' }}>
            ⚡ Năng lượng
          </Text>
          <Space size={6} style={{ width: '100%', justifyContent: 'space-between' }}>
            {ENERGY_LEVELS.map((m, i) => (
              <button
                key={i}
                onClick={() => { setEnergy(i); setSaved(false); }}
                disabled={submitting}
                title={m.label}
                style={{
                  flex: 1,
                  height: 44,
                  fontSize: 22,
                  background: energy === i ? 'rgba(82, 196, 26, 0.15)' : 'white',
                  border: energy === i ? '2px solid #52c41a' : '1px solid #e8e8e8',
                  borderRadius: 10,
                  cursor: submitting ? 'wait' : 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                {m.emoji}
              </button>
            ))}
          </Space>
        </div>

        {/* Stress row */}
        <div>
          <Text style={{ fontSize: 11, color: '#8c8c8c', marginBottom: 4, display: 'block' }}>
            💭 Căng thẳng
          </Text>
          <Space size={6} style={{ width: '100%', justifyContent: 'space-between' }}>
            {STRESS_LEVELS.map((m, i) => (
              <button
                key={i}
                onClick={() => { setStress(i); setSaved(false); }}
                disabled={submitting}
                title={m.label}
                style={{
                  flex: 1,
                  height: 44,
                  fontSize: 22,
                  background: stress === i ? 'rgba(250, 140, 22, 0.15)' : 'white',
                  border: stress === i ? '2px solid #fa8c16' : '1px solid #e8e8e8',
                  borderRadius: 10,
                  cursor: submitting ? 'wait' : 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                {m.emoji}
              </button>
            ))}
          </Space>
        </div>

        {saved && (
          <div style={{ textAlign: 'right' }}>
            <Button type="link" size="small" onClick={reset}>
              Ghi lại
            </Button>
          </div>
        )}
      </Space>
    </Card>
  );
}
