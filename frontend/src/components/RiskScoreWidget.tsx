import { useCallback, useEffect, useState } from 'react';
import { Card, Space, Typography, Tag, Progress, Alert, Button, Spin, Tooltip, Divider, Statistic, Row, Col } from 'antd';
import { AlertOutlined, InfoCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

import { riskApi, RiskScore } from '../api/risk';
import { getErrorMessage } from '../api/client';

const { Text, Paragraph } = Typography;

const LEVEL_CONFIG = {
  low: { color: '#52c41a', label: 'Thấp', bg: '#f6ffed', tagColor: 'green' },
  moderate: { color: '#faad14', label: 'Trung bình', bg: '#fffbe6', tagColor: 'orange' },
  high: { color: '#ff4d4f', label: 'Cao', bg: '#fff1f0', tagColor: 'red' },
} as const;

export default function RiskScoreWidget() {
  const navigate = useNavigate();
  const [data, setData] = useState<RiskScore | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchRisk = useCallback(async () => {
    setLoading(true);
    try {
      const result = await riskApi.getScore();
      setData(result);
    } catch {
      // Silent — widget shows error state
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRisk();
  }, [fetchRisk]);

  if (loading && !data) {
    return (
      <Card title={<Space><AlertOutlined /><span>Rủi ro khối lượng</span></Space>} size="small">
        <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card title={<Space><AlertOutlined /><span>Rủi ro khối lượng</span></Space>} size="small">
        <Alert
          type="warning"
          showIcon
          message="Không tải được dữ liệu rủi ro"
          action={<Button size="small" icon={<ReloadOutlined />} onClick={fetchRisk}>Thử lại</Button>}
        />
      </Card>
    );
  }

  const cfg = LEVEL_CONFIG[data.level] || LEVEL_CONFIG.low;
  const c = data.components;
  const w = data.weights;

  return (
    <Card
      title={
        <Space>
          <AlertOutlined />
          <span>Rủi ro khối lượng</span>
          <Tooltip title="Tính lại">
            <Button type="text" size="small" icon={<ReloadOutlined />} onClick={fetchRisk} />
          </Tooltip>
        </Space>
      }
      size="small"
      style={{ height: '100%', background: cfg.bg }}
    >
      <Space direction="vertical" size={12} style={{ width: '100%', alignItems: 'center' }}>
        <Progress
          type="circle"
          percent={data.risk_score}
          strokeColor={cfg.color}
          format={() => (
            <div>
              <div style={{ fontSize: 22, fontWeight: 700, color: cfg.color }}>
                {data.risk_score.toFixed(0)}
              </div>
              <div style={{ fontSize: 11, color: '#999' }}>/ 100</div>
            </div>
          )}
          size={140}
        />

        <Tag color={cfg.tagColor} style={{ fontSize: 13, padding: '4px 12px' }}>
          Mức: {cfg.label}
        </Tag>

        <Divider style={{ margin: '4px 0' }} />

        {/* Component breakdown */}
        <div style={{ width: '100%' }}>
          <Text strong style={{ fontSize: 12 }}>Thành phần (đã chuẩn hóa):</Text>
          <Row gutter={8} style={{ marginTop: 8 }}>
            <Col span={12}>
              <Statistic
                title="Thiếu ngủ"
                value={c.sleep_deficit}
                precision={2}
                valueStyle={{ fontSize: 14 }}
                suffix={<Text type="secondary" style={{ fontSize: 10 }}>× {w.sleep_deficit}</Text>}
              />
            </Col>
            <Col span={12}>
              <Statistic
                title="Mật độ công việc"
                value={c.workload_density}
                precision={2}
                valueStyle={{ fontSize: 14 }}
                suffix={<Text type="secondary" style={{ fontSize: 10 }}>× {w.workload_density}</Text>}
              />
            </Col>
            <Col span={12}>
              <Statistic
                title="Gần deadline"
                value={c.deadline_proximity}
                precision={2}
                valueStyle={{ fontSize: 14 }}
                suffix={<Text type="secondary" style={{ fontSize: 10 }}>× {w.deadline_proximity}</Text>}
              />
            </Col>
            <Col span={12}>
              <Statistic
                title="Thiếu nhất quán"
                value={c.study_inconsistency}
                precision={2}
                valueStyle={{ fontSize: 14 }}
                suffix={<Text type="secondary" style={{ fontSize: 10 }}>× {w.study_inconsistency}</Text>}
              />
            </Col>
          </Row>
        </div>

        <Divider style={{ margin: '4px 0' }} />

        {/* Disclaimer */}
        <Paragraph
          type="secondary"
          style={{ fontSize: 11, textAlign: 'center', marginBottom: 0 }}
        >
          <InfoCircleOutlined /> {data.disclaimer}
        </Paragraph>

        <Button type="link" size="small" onClick={() => navigate('/logging')}>
          Ghi thêm nhật ký →
        </Button>
      </Space>
    </Card>
  );
}
