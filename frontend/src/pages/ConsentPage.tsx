import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Button, Typography, Checkbox, message, Divider, Alert } from 'antd';
import { useAuthStore } from '../store/authStore';
import { authApi } from '../api/auth';
import { getErrorMessage } from '../api/client';

const { Title, Paragraph, Text } = Typography;

const CONSENT_VERSION = '1.0';

export default function ConsentPage() {
  const [agreed, setAgreed] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const setConsent = useAuthStore((s) => s.setConsent);
  const clearAuth = useAuthStore((s) => s.clearAuth);

  const handleAccept = async () => {
    setLoading(true);
    try {
      await authApi.signConsent(CONSENT_VERSION);
      setConsent(true);
      message.success('Đã ký đồng thuận tham gia nghiên cứu');
      navigate('/dashboard', { replace: true });
    } catch (err) {
      message.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleDecline = () => {
    clearAuth();
    message.info('Bạn đã từ chối tham gia nghiên cứu');
    navigate('/login', { replace: true });
  };

  return (
    <Card
      style={{
        maxWidth: 720,
        margin: '40px auto',
        boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
      }}
    >
      <Title level={3}>Đồng thuận tham gia nghiên cứu</Title>
      <Text type="secondary">Phiên bản: {CONSENT_VERSION}</Text>

      <Divider />

      <Paragraph>
        <strong>Mục đích nghiên cứu:</strong> Phát triển và đánh giá nguyên mẫu Hệ thống Lập kế
        hoạch Học tập Cá nhân, bao gồm thu thập dữ liệu hành vi học tập, đánh giá rủi ro khối
        lượng công việc, và tối ưu hóa lịch học.
      </Paragraph>

      <Paragraph>
        <strong>Dữ liệu thu thập:</strong> Phiên học (môn, thời lượng, mức tập trung), nhật ký
        giấc ngủ (giờ ngủ, giờ thức, chất lượng), nhật ký tâm trạng (năng lượng, căng thẳng),
        thông tin bài tập và deadline.
      </Paragraph>

      <Paragraph>
        <strong>Thời hạn lưu trữ:</strong> Dữ liệu được lưu trữ 12 tháng kể từ khi kết thúc
        giai đoạn thu thập, sau đó sẽ được ẩn danh hóa.
      </Paragraph>

      <Paragraph>
        <strong>Người truy cập dữ liệu:</strong> Tác giả luận văn và giảng viên hướng dẫn.
      </Paragraph>

      <Paragraph>
        <strong>Quyền của bạn:</strong> Bạn có quyền xem, xuất, xóa dữ liệu cá nhân của mình,
        và rút lui khỏi nghiên cứu bất kỳ lúc nào mà không cần giải thích.
      </Paragraph>

      <Alert
        type="warning"
        showIcon
        style={{ marginBottom: 16 }}
        message="Giới hạn của hệ thống"
        description="Hệ thống không đưa ra chẩn đoán y tế hoặc tâm lý. Kết quả chỉ mang tính tham khảo để hỗ trợ quản lý thời gian và không thay thế tư vấn chuyên nghiệp."
      />

      <Divider />

      <Checkbox
        checked={agreed}
        onChange={(e) => setAgreed(e.target.checked)}
        style={{ marginBottom: 20 }}
      >
        Tôi đã đọc và đồng ý tham gia nghiên cứu này.
      </Checkbox>

      <div style={{ display: 'flex', gap: 12 }}>
        <Button onClick={handleDecline} danger>
          Từ chối
        </Button>
        <Button type="primary" onClick={handleAccept} disabled={!agreed} loading={loading}>
          Đồng ý và tiếp tục
        </Button>
      </div>
    </Card>
  );
}
