import { useState } from 'react';
import {
  Form, InputNumber, DatePicker, TimePicker, Button, message, Space,
} from 'antd';
import { MoonOutlined } from '@ant-design/icons';
import dayjs, { Dayjs } from 'dayjs';
import { logsApi } from '../api/logs';
import { getErrorMessage } from '../api/client';

interface Props {
  onSuccess: () => void;
}

export default function SleepLogForm({ onSuccess }: Props) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: any) => {
    const sleepDate: Dayjs = values.sleep_date;
    const sleepTime: Dayjs = values.sleep_time;
    const wakeTime: Dayjs = values.wake_time;

    // Sleep time = sleep_date + sleep_time
    const sleepAt = sleepDate
      .hour(sleepTime.hour())
      .minute(sleepTime.minute())
      .second(0)
      .millisecond(0);

    // Wake time: nếu giờ thức <= giờ ngủ → cộng thêm 1 ngày
    let wakeAt = sleepDate
      .hour(wakeTime.hour())
      .minute(wakeTime.minute())
      .second(0)
      .millisecond(0);
    if (wakeAt.isBefore(sleepAt) || wakeAt.isSame(sleepAt)) {
      wakeAt = wakeAt.add(1, 'day');
    }

    setLoading(true);
    try {
      await logsApi.createSleep({
        sleep_time: sleepAt.toISOString(),
        wake_time: wakeAt.toISOString(),
        quality: values.quality,
      });
      message.success('Đã ghi nhật ký giấc ngủ');
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
        sleep_date: dayjs(),
        sleep_time: dayjs().hour(23).minute(0),
        wake_time: dayjs().hour(7).minute(0),
        quality: 4,
      }}
    >
      <Form.Item name="sleep_date" label="Ngày đi ngủ" rules={[{ required: true }]}>
        <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
      </Form.Item>

      <Space style={{ display: 'flex' }} size="middle">
        <Form.Item
          name="sleep_time"
          label="Giờ đi ngủ"
          rules={[{ required: true }]}
          style={{ flex: 1, marginBottom: 0 }}
        >
          <TimePicker style={{ width: '100%' }} format="HH:mm" minuteStep={5} />
        </Form.Item>

        <Form.Item
          name="wake_time"
          label="Giờ thức dậy"
          rules={[{ required: true }]}
          style={{ flex: 1, marginBottom: 0 }}
        >
          <TimePicker style={{ width: '100%' }} format="HH:mm" minuteStep={5} />
        </Form.Item>
      </Space>

      <Form.Item
        name="quality"
        label="Chất lượng giấc ngủ (1-5)"
        rules={[{ required: true }]}
        style={{ marginTop: 16 }}
      >
        <InputNumber min={1} max={5} style={{ width: '100%' }} />
      </Form.Item>

      <Form.Item style={{ marginBottom: 0 }}>
        <Button
          type="primary"
          htmlType="submit"
          loading={loading}
          icon={<MoonOutlined />}
          block
        >
          Ghi nhật ký giấc ngủ
        </Button>
      </Form.Item>
    </Form>
  );
}
