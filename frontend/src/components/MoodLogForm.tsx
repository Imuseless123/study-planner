import { useState } from 'react';
import {
  Form, InputNumber, DatePicker, Button, message, Space, Typography,
} from 'antd';
import { SmileOutlined } from '@ant-design/icons';
import dayjs, { Dayjs } from 'dayjs';
import { logsApi } from '../api/logs';
import { getErrorMessage } from '../api/client';

const { Text } = Typography;

interface Props {
  onSuccess: () => void;
}

export default function MoodLogForm({ onSuccess }: Props) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: any) => {
    const date: Dayjs = values.log_date;
    setLoading(true);
    try {
      await logsApi.createMood({
        log_date: date.format('YYYY-MM-DD'),
        energy_level: values.energy_level,
        stress_level: values.stress_level,
      });
      message.success('Đã ghi nhật ký tâm trạng');
      form.resetFields();
      onSuccess();
    } catch (err) {
      message.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={onFinish}
      initialValues={{
        log_date: dayjs(),
        energy_level: 3,
        stress_level: 3,
      }}
    >
      <Form.Item
        name="log_date"
        label="Ngày"
        rules={[{ required: true }]}
      >
        <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
      </Form.Item>

      <Form.Item
        name="energy_level"
        label="Mức năng lượng (1-5) — 1 = kiệt sức, 5 = tràn đầy"
        rules={[{ required: true }]}
      >
        <InputNumber min={1} max={5} style={{ width: '100%' }} />
      </Form.Item>

      <Form.Item
        name="stress_level"
        label="Mức căng thẳng (1-5) — 1 = thư giãn, 5 = rất căng"
        rules={[{ required: true }]}
      >
        <InputNumber min={1} max={5} style={{ width: '100%' }} />
      </Form.Item>

      <Text type="secondary" style={{ display: 'block', marginBottom: 16, fontSize: 12 }}>
        Lưu ý: Nếu đã có nhật ký cho ngày này, giá trị cũ sẽ bị ghi đè.
      </Text>

      <Form.Item style={{ marginBottom: 0 }}>
        <Button
          type="primary"
          htmlType="submit"
          loading={loading}
          icon={<SmileOutlined />}
          block
        >
          Ghi nhật ký tâm trạng
        </Button>
      </Form.Item>
    </Form>
  );
}
