import { useCallback, useEffect, useState } from 'react';
import {
  Typography, Card, Space, Button, Alert, Row, Col, Statistic,
  Divider, Modal, Input, message, Tag, Descriptions, Popconfirm,
} from 'antd';
import {
  DownloadOutlined, DeleteOutlined, WarningOutlined,
  UserOutlined, SafetyCertificateOutlined, LogoutOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';

import { userDataApi, DataExport } from '../api/userData';
import { consentApi, ConsentInfo } from '../api/consent';
import { useAuthStore } from '../store/authStore';
import { getErrorMessage } from '../api/client';

const { Title, Text, Paragraph } = Typography;

export default function SettingsPage() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const clearAuth = useAuthStore((s) => s.clearAuth);

  const [exportData, setExportData] = useState<DataExport | null>(null);
  const [consent, setConsent] = useState<ConsentInfo | null>(null);
  const [loading, setLoading] = useState(true);

  // Delete modal state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [usernameInput, setUsernameInput] = useState('');
  const [confirmChecked, setConfirmChecked] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // ====== Load data ======
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [data, c] = await Promise.all([
        userDataApi.export(),
        consentApi.get(),
      ]);
      setExportData(data);
      setConsent(c);
    } catch (err) {
      message.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // ====== Export handlers ======
  const handleExport = async () => {
    try {
      const data = await userDataApi.export();
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `study-planner-export-${user?.username}-${dayjs().format(
        'YYYY-MM-DD-HHmmss',
      )}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      message.success('Đã tải file dữ liệu');
    } catch (err) {
      message.error(getErrorMessage(err));
    }
  };

  // ====== Delete handlers ======
  const handleDeleteAccount = async () => {
    setDeleting(true);
    try {
      await userDataApi.deleteAccount({
        confirm: true,
        username_confirmation: usernameInput,
      });
      message.success(
        'Tài khoản đã được xóa. Bạn sẽ được chuyển về trang đăng nhập.',
      );
      setTimeout(() => {
        clearAuth();
        navigate('/login', { replace: true });
      }, 1500);
    } catch (err) {
      message.error(getErrorMessage(err));
    } finally {
      setDeleting(false);
    }
  };

  // ====== Withdraw consent ======
  const handleWithdrawConsent = async () => {
    try {
      await consentApi.withdraw();
      message.success('Đã rút lui khỏi nghiên cứu');
      fetchData();
    } catch (err) {
      message.error(getErrorMessage(err));
    }
  };

  const canDelete =
    confirmChecked && usernameInput === user?.username && !deleting;

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ marginBottom: 4 }}>
          Cài đặt
        </Title>
        <Text type="secondary">
          Quản lý tài khoản, dữ liệu cá nhân và quyền riêng tư.
        </Text>
      </div>

      {/* ====== Account Info ====== */}
      <Card
        title={
          <Space>
            <UserOutlined />
            <span>Thông tin tài khoản</span>
          </Space>
        }
        size="small"
        style={{ marginBottom: 24 }}
      >
        <Descriptions column={{ xs: 1, sm: 2 }} size="small">
          <Descriptions.Item label="Username">
            <Text strong>{user?.username}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="Email">{user?.email}</Descriptions.Item>
          <Descriptions.Item label="User ID">
            <Text code style={{ fontSize: 11 }}>
              {user?.user_id}
            </Text>
          </Descriptions.Item>
          <Descriptions.Item label="Ngày tạo">
            {user?.created_at ? dayjs(user.created_at).format('DD/MM/YYYY HH:mm') : '—'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* ====== Consent Status ====== */}
      <Card
        title={
          <Space>
            <SafetyCertificateOutlined />
            <span>Đồng thuận nghiên cứu</span>
          </Space>
        }
        size="small"
        style={{ marginBottom: 24 }}
      >
        {consent ? (
          <>
            <Space direction="vertical" style={{ width: '100%' }} size="small">
              <div>
                <Text strong>Phiên bản:</Text> {consent.version}{' '}
                {consent.withdrawn_at ? (
                  <Tag color="red">Đã rút lui</Tag>
                ) : (
                  <Tag color="green">Đang hiệu lực</Tag>
                )}
              </div>
              <div>
                <Text strong>Ngày ký:</Text>{' '}
                {dayjs(consent.signed_at).format('DD/MM/YYYY HH:mm')}
              </div>
              <div>
                <Text strong>Hết hiệu lực:</Text>{' '}
                {dayjs(consent.expires_at).format('DD/MM/YYYY')}
              </div>
              {consent.withdrawn_at && (
                <div>
                  <Text strong>Ngày rút lui:</Text>{' '}
                  {dayjs(consent.withdrawn_at).format('DD/MM/YYYY HH:mm')}
                </div>
              )}
            </Space>

            {!consent.withdrawn_at && (
              <>
                <Divider style={{ margin: '16px 0 12px' }} />
                <Alert
                  type="info"
                  showIcon
                  style={{ marginBottom: 12 }}
                  message="Rút lui khỏi nghiên cứu"
                  description="Bạn có thể rút lui bất kỳ lúc nào. Dữ liệu đã thu thập vẫn được giữ nhưng sẽ không được sử dụng cho phân tích mới. Để xóa hoàn toàn, hãy dùng chức năng Xóa tài khoản bên dưới."
                />
                <Popconfirm
                  title="Rút lui khỏi nghiên cứu?"
                  description="Bạn sẽ không thể ký lại consent mà phải liên hệ tác giả."
                  okText="Rút lui"
                  cancelText="Hủy"
                  okButtonProps={{ danger: true }}
                  onConfirm={handleWithdrawConsent}
                >
                  <Button danger icon={<LogoutOutlined />}>
                    Rút lui khỏi nghiên cứu
                  </Button>
                </Popconfirm>
              </>
            )}
          </>
        ) : (
          <Alert
            type="warning"
            showIcon
            message="Bạn chưa ký đồng thuận"
            description="Vui lòng ký đồng thuận để sử dụng đầy đủ tính năng."
          />
        )}
      </Card>

      {/* ====== Data Overview ====== */}
      {exportData && (
        <Card
          title={
            <Space>
              <DownloadOutlined />
              <span>Dữ liệu của bạn</span>
            </Space>
          }
          size="small"
          style={{ marginBottom: 24 }}
        >
          <Row gutter={[16, 16]}>
            <Col xs={12} sm={8} md={6}>
              <Statistic
                title="Phiên học"
                value={exportData.stats.total_study_sessions}
                valueStyle={{ color: '#667eea' }}
              />
            </Col>
            <Col xs={12} sm={8} md={6}>
              <Statistic
                title="Tổng giờ học"
                value={exportData.stats.total_study_hours}
                suffix="h"
                precision={1}
              />
            </Col>
            <Col xs={12} sm={8} md={6}>
              <Statistic
                title="Nhật ký giấc ngủ"
                value={exportData.stats.total_sleep_logs}
              />
            </Col>
            <Col xs={12} sm={8} md={6}>
              <Statistic
                title="TB giấc ngủ"
                value={exportData.stats.average_sleep_hours}
                suffix="h"
                precision={1}
              />
            </Col>
            <Col xs={12} sm={8} md={6}>
              <Statistic
                title="Nhật ký tâm trạng"
                value={exportData.stats.total_mood_logs}
              />
            </Col>
            <Col xs={12} sm={8} md={6}>
              <Statistic
                title="Môn học"
                value={exportData.stats.total_subjects}
              />
            </Col>
            <Col xs={12} sm={8} md={6}>
              <Statistic
                title="Bài tập"
                value={exportData.stats.total_assignments}
              />
            </Col>
            <Col xs={12} sm={8} md={6}>
              <Statistic
                title="TB mức tập trung"
                value={exportData.stats.average_focus_level}
                suffix="/ 5"
                precision={1}
              />
            </Col>
          </Row>

          <Divider style={{ margin: '20px 0 16px' }} />

          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <Alert
              type="info"
              showIcon
              message="Xuất dữ liệu cá nhân"
              description="Tải xuống toàn bộ dữ liệu của bạn dưới dạng JSON. File bao gồm tất cả phiên học, nhật ký, môn học, bài tập và đồng thuận."
            />
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              onClick={handleExport}
              size="large"
            >
              Tải xuống dữ liệu (JSON)
            </Button>
          </Space>
        </Card>
      )}

      {/* ====== Danger Zone ====== */}
      <Card
        title={
          <Space>
            <WarningOutlined style={{ color: '#ff4d4f' }} />
            <span style={{ color: '#ff4d4f' }}>Vùng nguy hiểm</span>
          </Space>
        }
        size="small"
        style={{
          borderColor: '#ffccc7',
          background: '#fff2f0',
        }}
      >
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Alert
            type="error"
            showIcon
            message="Xóa tài khoản vĩnh viễn"
            description={
              <div>
                <Paragraph style={{ marginBottom: 8 }}>
                  Hành động này sẽ <strong>xóa vĩnh viễn</strong>:
                </Paragraph>
                <ul style={{ marginBottom: 8, paddingLeft: 20 }}>
                  <li>Tài khoản và thông tin đăng nhập</li>
                  <li>Tất cả môn học và bài tập</li>
                  <li>Tất cả phiên học, nhật ký giấc ngủ, nhật ký tâm trạng</li>
                  <li>Tất cả lịch đã tạo và đánh giá</li>
                  <li>Đồng thuận nghiên cứu</li>
                </ul>
                <Paragraph style={{ marginBottom: 0, color: '#ff4d4f', fontWeight: 600 }}>
                  ⚠️ KHÔNG THỂ HOÀN TÁC. Dữ liệu sẽ không thể khôi phục.
                </Paragraph>
              </div>
            }
          />

          <Button
            danger
            type="primary"
            icon={<DeleteOutlined />}
            onClick={() => setDeleteModalOpen(true)}
            size="large"
          >
            Xóa tài khoản và dữ liệu
          </Button>
        </Space>
      </Card>

      {/* ====== Delete Confirmation Modal ====== */}
      <Modal
        open={deleteModalOpen}
        title={
          <Space>
            <WarningOutlined style={{ color: '#ff4d4f' }} />
            <span style={{ color: '#ff4d4f' }}>
              Xác nhận xóa tài khoản vĩnh viễn
            </span>
          </Space>
        }
        onCancel={() => {
          setDeleteModalOpen(false);
          setUsernameInput('');
          setConfirmChecked(false);
        }}
        footer={null}
        width={520}
        destroyOnClose
      >
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Alert
            type="error"
            showIcon
            message="Bạn sắp xóa tài khoản"
            description={
              <Text>
                Hành động này sẽ xóa toàn bộ dữ liệu của{' '}
                <strong>{user?.username}</strong> và không thể hoàn tác.
              </Text>
            }
          />

          <div>
            <Text strong>Để xác nhận, vui lòng gõ username của bạn:</Text>
            <Text code style={{ display: 'block', marginTop: 4, marginBottom: 8 }}>
              {user?.username}
            </Text>
            <Input
              placeholder="Nhập username để xác nhận"
              value={usernameInput}
              onChange={(e) => setUsernameInput(e.target.value)}
              size="large"
            />
          </div>

          <div>
            <label style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
              <input
                type="checkbox"
                checked={confirmChecked}
                onChange={(e) => setConfirmChecked(e.target.checked)}
                style={{ marginTop: 4 }}
              />
              <Text>
                Tôi hiểu rằng hành động này là <strong>vĩnh viễn</strong> và
                không thể hoàn tác. Tôi đồng ý xóa tài khoản và toàn bộ dữ liệu
                của mình.
              </Text>
            </label>
          </div>

          <Divider style={{ margin: '4px 0' }} />

          <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
            <Button
              onClick={() => {
                setDeleteModalOpen(false);
                setUsernameInput('');
                setConfirmChecked(false);
              }}
            >
              Hủy
            </Button>
            <Button
              danger
              type="primary"
              icon={<DeleteOutlined />}
              disabled={!canDelete}
              loading={deleting}
              onClick={handleDeleteAccount}
            >
              Xóa vĩnh viễn
            </Button>
          </Space>
        </Space>
      </Modal>
    </div>
  );
}
