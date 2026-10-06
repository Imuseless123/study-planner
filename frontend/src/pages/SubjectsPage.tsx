import { useCallback, useEffect, useState } from 'react';
import {
  Card, Table, Button, Modal, Form, Input, InputNumber,
  Typography, Space, Popconfirm, Tag, message, Empty,
  Row, Col, Statistic, Alert,
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined,
  BookOutlined, FireOutlined, StarOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

import { subjectsApi, Subject, SubjectCreatePayload } from '../api/subjects';
import { getErrorMessage } from '../api/client';

const { Title, Text } = Typography;

interface FormValues {
  subject_name: string;
  difficulty: number;
  priority: number;
}

export default function SubjectsPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [editingSubject, setEditingSubject] = useState<Subject | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm<FormValues>();

  // ====== Load data ======
  const fetchSubjects = useCallback(async () => {
    setLoading(true);
    try {
      const data = await subjectsApi.list();
      setSubjects(data);
    } catch (err) {
      message.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSubjects();
  }, [fetchSubjects]);

  // ====== Modal handlers ======
  const handleOpenCreate = () => {
    setEditingSubject(null);
    form.resetFields();
    form.setFieldsValue({ difficulty: 3, priority: 3 });
    setModalOpen(true);
  };

  const handleOpenEdit = (subject: Subject) => {
    setEditingSubject(subject);
    form.setFieldsValue({
      subject_name: subject.subject_name,
      difficulty: subject.difficulty,
      priority: subject.priority,
    });
    setModalOpen(true);
  };

  const handleCancel = () => {
    setModalOpen(false);
    form.resetFields();
    setEditingSubject(null);
  };

  const handleSubmit = async (values: FormValues) => {
    setSubmitting(true);
    try {
      if (editingSubject) {
        // Update
        await subjectsApi.update(editingSubject.subject_id, {
          subject_name: values.subject_name,
          difficulty: values.difficulty,
          priority: values.priority,
        });
        message.success('Đã cập nhật môn học');
      } else {
        // Create
        await subjectsApi.create(values as SubjectCreatePayload);
        message.success('Đã tạo môn học');
      }
      setModalOpen(false);
      form.resetFields();
      setEditingSubject(null);
      fetchSubjects();
    } catch (err) {
      message.error(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (subject: Subject) => {
    try {
      await subjectsApi.delete(subject.subject_id);
      message.success(`Đã xóa môn "${subject.subject_name}"`);
      fetchSubjects();
    } catch (err) {
      message.error(getErrorMessage(err));
    }
  };

  // ====== Statistics ======
  const total = subjects.length;
  const highDifficulty = subjects.filter((s) => s.difficulty >= 4).length;
  const highPriority = subjects.filter((s) => s.priority >= 4).length;
  const avgDifficulty =
    total === 0
      ? 0
      : (subjects.reduce((sum, s) => sum + s.difficulty, 0) / total).toFixed(1);

  // ====== Table columns ======
  const columns: ColumnsType<Subject> = [
    {
      title: 'Tên môn học',
      dataIndex: 'subject_name',
      key: 'subject_name',
      render: (v: string) => (
        <Space>
          <BookOutlined style={{ color: '#667eea' }} />
          <Text strong>{v}</Text>
        </Space>
      ),
      sorter: (a, b) => a.subject_name.localeCompare(b.subject_name),
    },
    {
      title: 'Độ khó',
      dataIndex: 'difficulty',
      key: 'difficulty',
      width: 140,
      filters: [
        { text: 'Dễ (1-2)', value: 'easy' },
        { text: 'Trung bình (3)', value: 'medium' },
        { text: 'Khó (4-5)', value: 'hard' },
      ],
      onFilter: (value, record) => {
        if (value === 'easy') return record.difficulty <= 2;
        if (value === 'medium') return record.difficulty === 3;
        if (value === 'hard') return record.difficulty >= 4;
        return true;
      },
      render: (v: number) => {
        const color = v >= 4 ? 'red' : v === 3 ? 'orange' : 'green';
        const label = v >= 4 ? 'Khó' : v === 3 ? 'TB' : 'Dễ';
        return <Tag color={color}>{label} ({v}/5)</Tag>;
      },
      sorter: (a, b) => a.difficulty - b.difficulty,
    },
    {
      title: 'Độ ưu tiên',
      dataIndex: 'priority',
      key: 'priority',
      width: 140,
      filters: [
        { text: 'Thấp (1-2)', value: 'low' },
        { text: 'Trung bình (3)', value: 'medium' },
        { text: 'Cao (4-5)', value: 'high' },
      ],
      onFilter: (value, record) => {
        if (value === 'low') return record.priority <= 2;
        if (value === 'medium') return record.priority === 3;
        if (value === 'high') return record.priority >= 4;
        return true;
      },
      render: (v: number) => {
        const color = v >= 4 ? 'purple' : v === 3 ? 'blue' : 'default';
        const label = v >= 4 ? 'Cao' : v === 3 ? 'TB' : 'Thấp';
        return <Tag color={color}>{label} ({v}/5)</Tag>;
      },
      sorter: (a, b) => a.priority - b.priority,
      defaultSortOrder: 'descend',
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
            title="Xóa môn học?"
            description={
              <div style={{ maxWidth: 280 }}>
                Xóa môn <strong>{record.subject_name}</strong> sẽ xóa tất cả
                phiên học và bài tập liên quan. Bạn chắc chắn?
              </div>
            }
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
            Môn học
          </Title>
          <Text type="secondary">
            Quản lý danh sách môn học để ghi nhật ký và lập kế hoạch.
          </Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleOpenCreate}>
          Tạo môn học
        </Button>
      </div>

      {/* Statistics */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Tổng số môn"
              value={total}
              prefix={<BookOutlined />}
              valueStyle={{ color: '#667eea' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Môn khó (≥4)"
              value={highDifficulty}
              prefix={<FireOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Ưu tiên cao (≥4)"
              value={highPriority}
              prefix={<StarOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Độ khó TB"
              value={avgDifficulty}
              suffix="/ 5"
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Alert nếu chưa có subject */}
      {!loading && total === 0 && (
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
          message="Chưa có môn học nào"
          description="Hãy tạo ít nhất 1 môn học để bắt đầu ghi nhật ký học tập."
        />
      )}

      {/* Table */}
      <Card
        title="Danh sách môn học"
        extra={
          <Button
            type="text"
            icon={<ReloadOutlined />}
            onClick={fetchSubjects}
            loading={loading}
            size="small"
          />
        }
      >
        {total === 0 && !loading ? (
          <Empty description="Chưa có môn học nào" />
        ) : (
          <Table
            dataSource={subjects}
            columns={columns}
            rowKey="subject_id"
            loading={loading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              pageSizeOptions: ['10', '20', '50'],
              showTotal: (total) => `Tổng ${total} môn`,
            }}
            scroll={{ x: 700 }}
          />
        )}
      </Card>

      {/* Modal Create/Edit */}
      <Modal
        open={modalOpen}
        title={editingSubject ? 'Sửa môn học' : 'Tạo môn học mới'}
        onCancel={handleCancel}
        onOk={() => form.submit()}
        okText={editingSubject ? 'Cập nhật' : 'Tạo'}
        cancelText="Hủy"
        confirmLoading={submitting}
        destroyOnClose
        width={500}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{ difficulty: 3, priority: 3 }}
        >
          <Form.Item
            name="subject_name"
            label="Tên môn học"
            rules={[
              { required: true, message: 'Vui lòng nhập tên môn' },
              { max: 100, message: 'Tối đa 100 ký tự' },
            ]}
          >
            <Input placeholder="VD: Toán cao cấp, Lập trình Web..." autoFocus />
          </Form.Item>

          <Form.Item
            name="difficulty"
            label="Độ khó (1 = rất dễ, 5 = rất khó)"
            rules={[{ required: true, message: 'Chọn độ khó' }]}
          >
            <InputNumber min={1} max={5} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="priority"
            label="Độ ưu tiên (1 = thấp, 5 = cao)"
            rules={[{ required: true, message: 'Chọn độ ưu tiên' }]}
          >
            <InputNumber min={1} max={5} style={{ width: '100%' }} />
          </Form.Item>

          <Text type="secondary" style={{ fontSize: 12 }}>
            💡 Độ khó và độ ưu tiên sẽ được dùng để tính hệ số hiệu quả trong
            thuật toán tối ưu lịch học (Tầng 3).
          </Text>
        </Form>
      </Modal>
    </div>
  );
}
