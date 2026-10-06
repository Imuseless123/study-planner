import { useCallback, useEffect, useState } from 'react';
import {
  Card, Table, Button, Modal, Form, Input, InputNumber,
  Typography, Space, Popconfirm, Tag, message, Empty,
  Row, Col, Statistic, Alert, Select, DatePicker, Progress, Tooltip,
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined,
  FileTextOutlined, WarningOutlined, ClockCircleOutlined,
  StarOutlined, HourglassOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs, { Dayjs } from 'dayjs';

import {
  assignmentsApi, Assignment, AssignmentCreatePayload,
} from '../api/assignments';
import { subjectsApi, Subject } from '../api/subjects';
import { getErrorMessage } from '../api/client';

const { Title, Text } = Typography;

interface FormValues {
  subject_id: string;
  title: string;
  deadline: Dayjs;
  required_hours: number;
  priority: number;
}

export default function AssignmentsPage() {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [editingAssignment, setEditingAssignment] = useState<Assignment | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm<FormValues>();

  // ====== Load data ======
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [a, s] = await Promise.all([
        assignmentsApi.list(),
        subjectsApi.list(),
      ]);
      setAssignments(a);
      setSubjects(s);
    } catch (err) {
      message.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // ====== Modal handlers ======
  const handleOpenCreate = () => {
    if (subjects.length === 0) {
      message.warning('Bạn cần tạo ít nhất 1 môn học trước');
      return;
    }
    setEditingAssignment(null);
    form.resetFields();
    form.setFieldsValue({
      priority: 3,
      required_hours: 2,
      deadline: dayjs().add(7, 'day').hour(23).minute(59),
      subject_id: subjects[0]?.subject_id,
    });
    setModalOpen(true);
  };

  const handleOpenEdit = (a: Assignment) => {
    setEditingAssignment(a);
    form.setFieldsValue({
      subject_id: a.subject_id,
      title: a.title,
      deadline: dayjs(a.deadline),
      required_hours: a.required_hours,
      priority: a.priority,
    });
    setModalOpen(true);
  };

  const handleCancel = () => {
    setModalOpen(false);
    form.resetFields();
    setEditingAssignment(null);
  };

  const handleSubmit = async (values: FormValues) => {
    setSubmitting(true);
    try {
      const payload = {
        subject_id: values.subject_id,
        title: values.title,
        deadline: values.deadline.toISOString(),
        required_hours: values.required_hours,
        priority: values.priority,
      };

      if (editingAssignment) {
        await assignmentsApi.update(editingAssignment.assignment_id, payload);
        message.success('Đã cập nhật bài tập');
      } else {
        await assignmentsApi.create(payload as AssignmentCreatePayload);
        message.success('Đã tạo bài tập');
      }
      setModalOpen(false);
      form.resetFields();
      setEditingAssignment(null);
      fetchData();
    } catch (err) {
      message.error(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (a: Assignment) => {
    try {
      await assignmentsApi.delete(a.assignment_id);
      message.success(`Đã xóa "${a.title}"`);
      fetchData();
    } catch (err) {
      message.error(getErrorMessage(err));
    }
  };

  // ====== Statistics ======
  const now = dayjs();
  const total = assignments.length;
  const overdue = assignments.filter((a) => a.is_overdue).length;
  const dueSoon = assignments.filter(
    (a) => !a.is_overdue && a.days_until_deadline <= 3
  ).length;
  const highPriority = assignments.filter((a) => a.priority >= 4).length;
  const totalHours = assignments
    .reduce((sum, a) => sum + a.required_hours, 0)
    .toFixed(1);

  // ====== Deadline render ======
  const renderDeadline = (a: Assignment) => {
    const deadline = dayjs(a.deadline);
    const days = a.days_until_deadline;

    let color = 'green';
    let label = '';
    if (a.is_overdue) {
      color = 'red';
      label = `Quá hạn ${Math.abs(days)} ngày`;
    } else if (days === 0) {
      color = 'red';
      label = 'Hôm nay';
    } else if (days === 1) {
      color = 'orange';
      label = 'Ngày mai';
    } else if (days <= 3) {
      color = 'orange';
      label = `Còn ${days} ngày`;
    } else if (days <= 7) {
      color = 'blue';
      label = `Còn ${days} ngày`;
    } else {
      color = 'default';
      label = `Còn ${days} ngày`;
    }

    return (
      <Space direction="vertical" size={2}>
        <Text>{deadline.format('DD/MM/YYYY HH:mm')}</Text>
        <Tag color={color}>{label}</Tag>
      </Space>
    );
  };

  // ====== Urgency progress ======
  const renderUrgency = (a: Assignment) => {
    // Tính urgency: nếu deadline 7 ngày thì 100% thời gian còn
    //                       nếu < 0 thì 0%
    const totalWindowDays = 30;
    const days = a.days_until_deadline;
    const percent = Math.max(0, Math.min(100, (days / totalWindowDays) * 100));

    let strokeColor = '#52c41a';
    if (a.is_overdue || days <= 1) strokeColor = '#ff4d4f';
    else if (days <= 3) strokeColor = '#faad14';
    else if (days <= 7) strokeColor = '#1890ff';

    return (
      <Tooltip title={a.is_overdue ? 'Quá hạn' : `Còn ${days} ngày`}>
        <Progress
          type="circle"
          size={40}
          percent={Math.round(percent)}
          strokeColor={strokeColor}
          format={() => (a.is_overdue ? '!' : days)}
        />
      </Tooltip>
    );
  };

  // ====== Table columns ======
  const columns: ColumnsType<Assignment> = [
    {
      title: 'Trạng thái',
      key: 'urgency',
      width: 80,
      render: (_, record) => renderUrgency(record),
      sorter: (a, b) => a.days_until_deadline - b.days_until_deadline,
      defaultSortOrder: 'ascend',
    },
    {
      title: 'Bài tập',
      key: 'title',
      render: (_, record) => (
        <Space direction="vertical" size={2} style={{ width: '100%' }}>
          <Text strong>{record.title}</Text>
          <Tag color="blue">{record.subject_name}</Tag>
        </Space>
      ),
    },
    {
      title: 'Deadline',
      key: 'deadline',
      width: 200,
      render: (_, record) => renderDeadline(record),
      sorter: (a, b) => dayjs(a.deadline).unix() - dayjs(b.deadline).unix(),
    },
    {
      title: 'Giờ chuẩn bị',
      dataIndex: 'required_hours',
      key: 'required_hours',
      width: 130,
      render: (v: number) => <Text>{v}h</Text>,
      sorter: (a, b) => a.required_hours - b.required_hours,
    },
    {
      title: 'Ưu tiên',
      dataIndex: 'priority',
      key: 'priority',
      width: 130,
      filters: [
        { text: 'Cao (4-5)', value: 'high' },
        { text: 'Trung bình (3)', value: 'medium' },
        { text: 'Thấp (1-2)', value: 'low' },
      ],
      onFilter: (value, record) => {
        if (value === 'high') return record.priority >= 4;
        if (value === 'medium') return record.priority === 3;
        if (value === 'low') return record.priority <= 2;
        return true;
      },
      render: (v: number) => {
        const color = v >= 4 ? 'purple' : v === 3 ? 'blue' : 'default';
        const label = v >= 4 ? 'Cao' : v === 3 ? 'TB' : 'Thấp';
        return <Tag color={color}>{label} ({v}/5)</Tag>;
      },
      sorter: (a, b) => a.priority - b.priority,
    },
    {
      title: 'Hành động',
      key: 'action',
      width: 130,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleOpenEdit(record)}
          >
            Sửa
          </Button>
          <Popconfirm
            title="Xóa bài tập?"
            description={<span>Xóa <strong>{record.title}</strong>?</span>}
            okText="Xóa"
            cancelText="Hủy"
            okButtonProps={{ danger: true }}
            onConfirm={() => handleDelete(record)}
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* Header */}
      <div
        style={{
          marginBottom: 24,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <div>
          <Title level={2} style={{ marginBottom: 4 }}>
            Bài tập
          </Title>
          <Text type="secondary">
            Quản lý deadline và khối lượng chuẩn bị cho từng bài tập.
          </Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleOpenCreate}>
          Tạo bài tập
        </Button>
      </div>

      {/* Statistics */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={6} lg={4}>
          <Card size="small">
            <Statistic
              title="Tổng bài tập"
              value={total}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#667eea' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={5}>
          <Card size="small">
            <Statistic
              title="Quá hạn"
              value={overdue}
              prefix={<WarningOutlined />}
              valueStyle={{ color: overdue > 0 ? '#cf1322' : '#999' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={5}>
          <Card size="small">
            <Statistic
              title="Sắp tới hạn (≤3 ngày)"
              value={dueSoon}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: dueSoon > 0 ? '#fa8c16' : '#999' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={5}>
          <Card size="small">
            <Statistic
              title="Ưu tiên cao (≥4)"
              value={highPriority}
              prefix={<StarOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6} lg={5}>
          <Card size="small">
            <Statistic
              title="Tổng giờ chuẩn bị"
              value={totalHours}
              suffix="h"
              prefix={<HourglassOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Alerts */}
      {overdue > 0 && (
        <Alert
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
          message={`Bạn có ${overdue} bài tập đã quá hạn!`}
          description="Hãy kiểm tra và điều chỉnh kế hoạch học tập."
        />
      )}
      {!loading && subjects.length === 0 && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          message="Chưa có môn học nào"
          description="Hãy tạo ít nhất 1 môn học ở trang Môn học trước khi tạo bài tập."
        />
      )}

      {/* Table */}
      <Card
        title="Danh sách bài tập"
        extra={
          <Button
            type="text"
            icon={<ReloadOutlined />}
            onClick={fetchData}
            loading={loading}
            size="small"
          />
        }
      >
        {total === 0 && !loading ? (
          <Empty description="Chưa có bài tập nào" />
        ) : (
          <Table
            dataSource={assignments}
            columns={columns}
            rowKey="assignment_id"
            loading={loading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => `Tổng ${total} bài tập`,
            }}
            scroll={{ x: 900 }}
            rowClassName={(record) =>
              record.is_overdue ? 'assignment-overdue-row' : ''
            }
          />
        )}
      </Card>

      {/* Modal Create/Edit */}
      <Modal
        open={modalOpen}
        title={editingAssignment ? 'Sửa bài tập' : 'Tạo bài tập mới'}
        onCancel={handleCancel}
        onOk={() => form.submit()}
        okText={editingAssignment ? 'Cập nhật' : 'Tạo'}
        cancelText="Hủy"
        confirmLoading={submitting}
        destroyOnClose
        width={560}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            name="subject_id"
            label="Môn học"
            rules={[{ required: true, message: 'Chọn môn học' }]}
          >
            <Select
              placeholder="Chọn môn học"
              options={subjects.map((s) => ({
                value: s.subject_id,
                label: `${s.subject_name} (khó ${s.difficulty}, ưu tiên ${s.priority})`,
              }))}
            />
          </Form.Item>

          <Form.Item
            name="title"
            label="Tiêu đề bài tập"
            rules={[
              { required: true, message: 'Nhập tiêu đề' },
              { max: 200, message: 'Tối đa 200 ký tự' },
            ]}
          >
            <Input placeholder="VD: Bài tập chương 3, Báo cáo thí nghiệm..." />
          </Form.Item>

          <Form.Item
            name="deadline"
            label="Deadline"
            rules={[{ required: true, message: 'Chọn deadline' }]}
          >
            <DatePicker
              showTime={{ format: 'HH:mm' }}
              format="DD/MM/YYYY HH:mm"
              style={{ width: '100%' }}
              placeholder="Chọn ngày giờ nộp"
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="required_hours"
                label="Giờ chuẩn bị"
                rules={[
                  { required: true, message: 'Nhập số giờ' },
                  { type: 'number', min: 0.25, max: 100, message: '0.25 - 100h' },
                ]}
              >
                <InputNumber
                  min={0.25}
                  max={100}
                  step={0.5}
                  style={{ width: '100%' }}
                  addonAfter="giờ"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="priority"
                label="Ưu tiên (1-5)"
                rules={[{ required: true }]}
              >
                <InputNumber min={1} max={5} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Text type="secondary" style={{ fontSize: 12 }}>
            💡 Số giờ chuẩn bị và ưu tiên sẽ dùng để tính hệ số hiệu quả trong thuật toán tối ưu lịch học (Tầng 3).
          </Text>
        </Form>
      </Modal>
    </div>
  );
}
