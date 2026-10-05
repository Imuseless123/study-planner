import { useEffect, useState } from 'react';
import {
  Form, InputNumber, Select, DatePicker, TimePicker,
  Button, message, Space, Empty, Typography,
} from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import dayjs, { Dayjs } from 'dayjs';
import { logsApi } from '../api/logs';
import { subjectsApi, Subject } from '../api/subjects';
import { getErrorMessage } from '../api/client';

const { Text } = Typography;

interface Props {
  subjects: Subject[];
  onSuccess: () => void;
}

export default function StudyLogForm({ subjects, onSuccess }: Props) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: any) => {
    if (!values.start_date || !values.start_time) {
      message.error('Vui lòng chọn ngày và giờ');
      return;
    }

    // Combine date + time thành ISO
    const date: Dayjs = values.start_date;
    const time: Dayjs = values.start_time;
    const startTime = date
      .hour(time.hour())
      .minute(time.minute())
      .second(0)
      .millisecond(0)
      .toISOString();

    setLoading(true);
    try {
      await logsApi.createStudy({
        subject_id: values.subject_id,
        start_time: startTime,
        duration: values.duration,
        focus_level: values.focus_level,
      });
      message.success('Đã ghi phiên học');
      form.resetFields();
      onSuccess();
    } catch (err) {
      message.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (subjects.length === 0) {
    return (
      <Empty description="Bạn cần tạo ít nhất 1 môn học trước khi ghi phiên học." />
    );
  }

  return (
    <Form form={form} layout="vertical" onFinish={onFinish} initialValues={{ focus_level: 3 }}>
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

      <Space style={{ display: 'flex' }} size="middle">
        <Form.Item
          name="start_date"
          label="Ngày"
          rules={[{ required: true }]}
          style={{ flex: 1, marginBottom: 0 }}
          initialValue={dayjs()}
        >
          <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
        </Form.Item>

        <Form.Item
          name="start_time"
          label="Giờ bắt đầu"
          rules={[{ required: true }]}
          style={{ flex: 1, marginBottom: 0 }}
          initialValue={dayjs()}
        >
          <TimePicker style={{ width: '100%' }} format="HH:mm" minuteStep={5} />
        </Form.Item>
      </Space>

      <Form.Item
        name="duration"
        label="Thời lượng (giờ)"
        rules={[
          { required: true, message: 'Nhập thời lượng' },
          { type: 'number', min: 0.25, max: 12, message: 'Trong khoảng 0.25 - 12h' },
        ]}
        style={{ marginTop: 16 }}
      >
        <InputNumber
          min={0.25}
          max={12}
          step={0.25}
          placeholder="VD: 1.5"
          style={{ width: '100%' }}
          addonAfter="giờ"
        />
      </Form.Item>

      <Form.Item
        name="focus_level"
        label="Mức tập trung (1-5)"
        rules={[{ required: true }]}
      >
        <InputNumber min={1} max={5} style={{ width: '100%' }} />
      </Form.Item>

      <Form.Item style={{ marginBottom: 0 }}>
        <Button
          type="primary"
          htmlType="submit"
          loading={loading}
          icon={<PlusOutlined />}
          block
        >
          Ghi phiên học
        </Button>
      </Form.Item>
    </Form>
  );
}
