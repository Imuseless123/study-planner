import { Card, Space, Typography, Tag, Progress, Alert, Button } from 'antd';
import { AlertOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Text, Paragraph } = Typography;

export default function RiskScoreWidget() {
  const navigate = useNavigate();

  // Placeholder — sẽ tích hợp Tầng 2 sau
  const riskScore = 0;
  const level = 'low';

  const config = {
    low: { color: '#52c41a', label: 'Thấp', bg: '#f6ffed' },
    moderate: { color: '#faad14', label: 'Trung bình', bg: '#fffbe6' },
    high: { color: '#ff4d4f', label: 'Cao', bg: '#fff1f0' },
  }[level];

  return (
    <Card
      title={
        <Space>
          <AlertOutlined />
          <span>Rủi ro khối lượng</span>
          <Tag color="default">Sắp ra mắt</Tag>
        </Space>
      }
      size="small"
      style={{ height: '100%', background: config.bg }}
    >
      <Space direction="vertical" size={12} style={{ width: '100%', alignItems: 'center' }}>
        <Progress
          type="circle"
          percent={riskScore}
          strokeColor={config.color}
          format={() => (
            <div>
              <div style={{ fontSize: 22, fontWeight: 700, color: config.color }}>
                {riskScore}
              </div>
              <div style={{ fontSize: 11, color: '#999' }}>/ 100</div>
            </div>
          )}
          size={140}
        />

        <Tag
          color={
            level === 'low' ? 'green' : level === 'moderate' ? 'orange' : 'red'
          }
          style={{ fontSize: 13, padding: '4px 12px' }}
        >
          Mức: {config.label}
        </Tag>

        <Paragraph
          type="secondary"
          style={{ fontSize: 11, textAlign: 'center', marginBottom: 0 }}
        >
          <InfoCircleOutlined /> Chỉ báo này phản ánh mức độ căng thẳng do khối
          lượng công việc dựa trên dữ liệu hành vi tự báo cáo. Đây KHÔNG phải là
          chẩn đoán y tế hoặc tâm lý.
        </Paragraph>

        <Alert
          type="info"
          showIcon
          style={{ fontSize: 11 }}
          message="Đang phát triển"
          description={
            <span style={{ fontSize: 11 }}>
              Chỉ báo rủi ro khối lượng sẽ có sẵn khi Tầng 2 (Risk Indicator)
              hoàn thành.
            </span>
          }
        />

        <Button
          type="link"
          size="small"
          onClick={() => navigate('/logging')}
        >
          Ghi thêm nhật ký →
        </Button>
      </Space>
    </Card>
  );
}
