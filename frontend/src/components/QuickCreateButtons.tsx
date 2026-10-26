import { useState } from 'react';
import {
  Card, Button, Space, Typography, Modal, Form, Input, InputNumber,
  Select, DatePicker, message, AutoComplete,
} from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import dayjs, { Dayjs } from 'dayjs';
import { subjectsApi, Subject } from '../api/subjects';
import { assignmentsApi } from '../api/assignments';
import { getErrorMessage } from '../api/client';
import { useNavigate } from 'react-router-dom';

const { Text } = Typography;

const COMMON_SUBJECTS = [
  'Toán cao cấp', 'Giải tích', 'Đại số tuyến tính',
  'Vật lý đại cương', 'Hóa đại cương', 'Xác suất thống kê',
  'Lập trình', 'Cấu trúc dữ liệu', 'Cơ sở dữ liệu',
  'Tiếng Anh', 'Kinh tế vi mô', 'Triết học',
];

interface Props {
  subjects: Subject[];
  onRefresh?: () => void;
}

/**
 * Quick create buttons for Subject + Assignment.
 * Opens modal với minimal fields (smart defaults cho phần còn lại).
 */
export default function QuickCreateButtons({ subjects, onRefresh }: Props) {
  const navigate = useNavigate();

  // ===== SUBJECT MODAL =====
  const [subjectOpen, setSubjectOpen] = useState(false);
  const [subjectForm] = Form.useForm();
  const [subjectSubmitting, setSubjectSubmitting] = useState(false);

  const handleSubjectSubmit = async () => {
    try {
      const values = await subjectForm.validateFields();
      setSubjectSubmitting(true);
      await subjectsApi.create({
        subject_name: values.subject_name,
        difficulty: 3,    // default
        priority: 3,      // default
      });
      message.success(`Đã tạo môn: ${values.subject_name}`);
      setSubjectOpen(false);
      subjectForm.resetFields();
      onRefresh?.();
    } catch (err) {
      if (err && typeof err === 'object' && 'errorFields' in err) {
        // Form validation error — do nothing
        return;
      }
      message.error(getErrorMessage(err));
    } finally {
      setSubjectSubmitting(false);
    }
  };

  // ===== ASSIGNMENT MODAL =====
  const [assignmentOpen, setAssignmentOpen] = useState(false);
  const [assignmentForm] = Form.useForm();
  const [assignmentSubmitting, setAssignmentSubmitting] = useState(false);

  const openAssignmentModal = () => {
    if (subjects.length === 0) {
      message.warning('Tạo môn học trước khi tạo bài tập');
      return;
    }
    assignmentForm.resetFields();
    assignmentForm.setFieldsValue({
      subject_id: subjects[0].subject_id,
      deadline: dayjs().add(7, 'day').hour(23).minute(59),
    });
    setAssignmentOpen(true);
  };

  const handleAssignmentSubmit = async () => {
    try {
      const values = await assignmentForm.validateFields();
      setAssignmentSubmitting(true);
      await assignmentsApi.create({
        subject_id: values.subject_id,
        title: values.title,
        deadline: values.deadline.toISOString(),
        required_hours: values.required_hours ?? 2,   // default
        priority: values.priority ?? 3,                // default
      });
      message.success(`Đã tạo bài tập: ${values.title}`);
      setAssignmentOpen(false);
      assignmentForm.resetFields();
      onRefresh?.();
    } catch (err) {
      if (err && typeof err === 'object' && 'errorFields' in err) {
        return;
      }
      message.error(getErrorMessage(err));
    } finally {
      setAssignmentSubmitting(false);
    }
  };

  return (
    <>
      <Card
        size="small"
        style={{
          background: '#fff',
          border: '1px dashed #d9d9d9',
        }}
      >
        <Space style={{ width: '100%', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            ➕ Tạo nhanh (chỉ cần 1-2 trường)
          </Text>
          <Space size={8}>
            <Button
              icon={<PlusOutlined />}
              size="small"
              onClick={() => setSubjectOpen(true)}
              style={{ borderRadius: 16 }}
            >
              Môn học
            </Button>
            <Button
              icon={<PlusOutlined />}
              size="small"
              type="primary"
              onClick={openAssignmentModal}
              style={{ borderRadius: 16 }}
            >
              Bài tập
            </Button>
            <Button
              type="link"
              size="small"
              onClick={() => navigate('/subjects')}
              style={{ fontSize: 11, padding: 0 }}
            >
              Xem tất cả
            </Button>
          </Space>
        </Space>
      </Card>

      {/* ===== SUBJECT MODAL ===== */}
      <Modal
        title="➕ Tạo môn học nhanh"
        open={subjectOpen}
        onCancel={() => setSubjectOpen(false)}
        onOk={handleSubjectSubmit}
        okText="Tạo"
        cancelText="Hủy"
        confirmLoading={subjectSubmitting}
        destroyOnClose
        width={400}
      >
        <Form form={subjectForm} layout="vertical">
          <Form.Item
            name="subject_name"
            label="Tên môn học"
            rules={[{ required: true, message: 'Nhập tên môn' }]}
            extra="Độ khó & ưu tiên mặc định = 3 — có thể sửa sau ở trang Môn học."
          >
            <AutoComplete
              options={COMMON_SUBJECTS.map((s) => ({ value: s }))}
              placeholder="VD: Lập trình, Toán cao cấp..."
              filterOption={(input, option) =>
                (option?.value as string).toLowerCase().includes(input.toLowerCase())
              }
            >
              <Input autoFocus />
            </AutoComplete>
          </Form.Item>
        </Form>
      </Modal>

      {/* ===== ASSIGNMENT MODAL ===== */}
      <Modal
        title="➕ Tạo bài tập nhanh"
        open={assignmentOpen}
        onCancel={() => setAssignmentOpen(false)}
        onOk={handleAssignmentSubmit}
        okText="Tạo"
        cancelText="Hủy"
        confirmLoading={assignmentSubmitting}
        destroyOnClose
        width={480}
      >
        <Form form={assignmentForm} layout="vertical">
          <Form.Item
            name="subject_id"
            label="Môn học"
            rules={[{ required: true }]}
          >
            <Select
              options={subjects.map((s) => ({
                value: s.subject_id,
                label: s.subject_name,
              }))}
              placeholder="Chọn môn"
            />
          </Form.Item>

          <Form.Item
            name="title"
            label="Tên bài tập"
            rules={[{ required: true, message: 'Nhập tên bài tập' }]}
          >
            <Input placeholder="VD: Bài tập chương 3" autoFocus />
          </Form.Item>

          <Form.Item
            name="deadline"
            label="Deadline"
            rules={[{ required: true }]}
          >
            <DatePicker
              showTime={{ format: 'HH:mm' }}
              format="DD/MM/YYYY HH:mm"
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Text type="secondary" style={{ fontSize: 11 }}>
            💡 Các trường khác mặc định: 2h chuẩn bị, ưu tiên 3/5 — có thể sửa sau ở trang Bài tập.
          </Text>
        </Form>
      </Modal>
    </>
  );
}
