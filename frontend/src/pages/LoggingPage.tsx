import { useEffect, useState, useCallback } from 'react';
import {
  Card, Tabs, Row, Col, Table, Tag, Button, Popconfirm,
  Typography, message, Empty, Space, Spin,
} from 'antd';
import { DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

import StudyLogForm from '../components/StudyLogForm';
import SleepLogForm from '../components/SleepLogForm';
import MoodLogForm from '../components/MoodLogForm';

import { logsApi, StudyLogItem, SleepLogItem, MoodLogItem } from '../api/logs';
import { subjectsApi, Subject } from '../api/subjects';
import { getErrorMessage } from '../api/client';

const { Title, Text } = Typography;

export default function LoggingPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [studyLogs, setStudyLogs] = useState<StudyLogItem[]>([]);
  const [sleepLogs, setSleepLogs] = useState<SleepLogItem[]>([]);
  const [moodLogs, setMoodLogs] = useState<MoodLogItem[]>([]);
  const [loading, setLoading] = useState(true);

  const refreshAll = useCallback(async () => {
    setLoading(true);
    try {
      const [subs, study, sleep, mood] = await Promise.all([
        subjectsApi.list(),
        logsApi.listStudy(30),
        logsApi.listSleep(30),
        logsApi.listMood(30),
      ]);
      setSubjects(subs);
      setStudyLogs(study.items);
      setSleepLogs(sleep.items);
      setMoodLogs(mood.items);
    } catch (err) {
      message.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  const handleDelete = async (
    type: 'study' | 'sleep' | 'mood',
    id: string,
  ) => {
    try {
      if (type === 'study') await logsApi.deleteStudy(id);
      if (type === 'sleep') await logsApi.deleteSleep(id);
      if (type === 'mood') await logsApi.deleteMood(id);
      message.success('Đã xóa');
      refreshAll();
    } catch (err) {
      message.error(getErrorMessage(err));
    }
  };

  // ====== Study columns ======
  const studyColumns = [
    {
      title: 'Môn',
      dataIndex: 'subject_name',
      key: 'subject',
      render: (v: string) => <Tag color="blue">{v}</Tag>,
    },
    {
      title: 'Bắt đầu',
      dataIndex: 'start_time',
      key: 'start_time',
      render: (v: string) => dayjs(v).format('DD/MM/YYYY HH:mm'),
      sorter: (a: StudyLogItem, b: StudyLogItem) =>
        dayjs(a.start_time).unix() - dayjs(b.start_time).unix(),
    },
    {
      title: 'Thời lượng',
      dataIndex: 'duration',
      key: 'duration',
      render: (v: number) => `${v}h`,
    },
    {
      title: 'Tập trung',
      dataIndex: 'focus_level',
      key: 'focus',
      render: (v: number) => {
        const color = v >= 4 ? 'green' : v === 3 ? 'orange' : 'red';
        return <Tag color={color}>{v}/5</Tag>;
      },
    },
    {
      title: '',
      key: 'action',
      width: 60,
      render: (_: any, record: StudyLogItem) => (
        <Popconfirm
          title="Xóa phiên học này?"
          onConfirm={() => handleDelete('study', record.session_id)}
          okText="Xóa"
          cancelText="Hủy"
        >
          <Button type="text" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  // ====== Sleep columns ======
  const sleepColumns = [
    {
      title: 'Đi ngủ',
      dataIndex: 'sleep_time',
      key: 'sleep_time',
      render: (v: string) => dayjs(v).format('DD/MM HH:mm'),
    },
    {
      title: 'Thức dậy',
      dataIndex: 'wake_time',
      key: 'wake_time',
      render: (v: string) => dayjs(v).format('DD/MM HH:mm'),
    },
    {
      title: 'Số giờ',
      dataIndex: 'hours',
      key: 'hours',
      render: (v: number) => {
        const color = v >= 7 ? 'green' : v >= 6 ? 'orange' : 'red';
        return <Tag color={color}>{v}h</Tag>;
      },
    },
    {
      title: 'Chất lượng',
      dataIndex: 'quality',
      key: 'quality',
      render: (v: number) => `${v}/5`,
    },
    {
      title: '',
      key: 'action',
      width: 60,
      render: (_: any, record: SleepLogItem) => (
        <Popconfirm
          title="Xóa nhật ký này?"
          onConfirm={() => handleDelete('sleep', record.sleep_id)}
          okText="Xóa"
          cancelText="Hủy"
        >
          <Button type="text" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  // ====== Mood columns ======
  const moodColumns = [
    {
      title: 'Ngày',
      dataIndex: 'log_date',
      key: 'log_date',
      render: (v: string) => dayjs(v).format('DD/MM/YYYY'),
    },
    {
      title: 'Năng lượng',
      dataIndex: 'energy_level',
      key: 'energy',
      render: (v: number) => {
        const color = v >= 4 ? 'green' : v === 3 ? 'orange' : 'red';
        return <Tag color={color}>{v}/5</Tag>;
      },
    },
    {
      title: 'Căng thẳng',
      dataIndex: 'stress_level',
      key: 'stress',
      render: (v: number) => {
        const color = v <= 2 ? 'green' : v === 3 ? 'orange' : 'red';
        return <Tag color={color}>{v}/5</Tag>;
      },
    },
    {
      title: '',
      key: 'action',
      width: 60,
      render: (_: any, record: MoodLogItem) => (
        <Popconfirm
          title="Xóa nhật ký này?"
          onConfirm={() => handleDelete('mood', record.mood_id)}
          okText="Xóa"
          cancelText="Hủy"
        >
          <Button type="text" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 60 }}>
        <Spin size="large" />
      </div>
    );
  }

  const tabs = [
    {
      key: 'study',
      label: `📚 Phiên học (${studyLogs.length})`,
      children: (
        <Row gutter={24}>
          <Col xs={24} lg={10}>
            <Card title="Ghi phiên học mới" size="small">
              <StudyLogForm subjects={subjects} onSuccess={refreshAll} />
            </Card>
          </Col>
          <Col xs={24} lg={14}>
            <Card
              title="Lịch sử gần đây"
              size="small"
              extra={
                <Button
                  type="text"
                  icon={<ReloadOutlined />}
                  onClick={refreshAll}
                  size="small"
                />
              }
            >
              {studyLogs.length === 0 ? (
                <Empty description="Chưa có phiên học nào" />
              ) : (
                <Table
                  dataSource={studyLogs}
                  columns={studyColumns}
                  rowKey="session_id"
                  pagination={{ pageSize: 10, size: 'small' }}
                  size="small"
                />
              )}
            </Card>
          </Col>
        </Row>
      ),
    },
    {
      key: 'sleep',
      label: `🌙 Giấc ngủ (${sleepLogs.length})`,
      children: (
        <Row gutter={24}>
          <Col xs={24} lg={10}>
            <Card title="Ghi nhật ký giấc ngủ" size="small">
              <SleepLogForm onSuccess={refreshAll} />
            </Card>
          </Col>
          <Col xs={24} lg={14}>
            <Card
              title="Lịch sử gần đây"
              size="small"
              extra={
                <Button
                  type="text"
                  icon={<ReloadOutlined />}
                  onClick={refreshAll}
                  size="small"
                />
              }
            >
              {sleepLogs.length === 0 ? (
                <Empty description="Chưa có nhật ký giấc ngủ" />
              ) : (
                <Table
                  dataSource={sleepLogs}
                  columns={sleepColumns}
                  rowKey="sleep_id"
                  pagination={{ pageSize: 10, size: 'small' }}
                  size="small"
                />
              )}
            </Card>
          </Col>
        </Row>
      ),
    },
    {
      key: 'mood',
      label: `😊 Tâm trạng (${moodLogs.length})`,
      children: (
        <Row gutter={24}>
          <Col xs={24} lg={10}>
            <Card title="Ghi nhật ký tâm trạng" size="small">
              <MoodLogForm onSuccess={refreshAll} />
            </Card>
          </Col>
          <Col xs={24} lg={14}>
            <Card
              title="Lịch sử gần đây"
              size="small"
              extra={
                <Button
                  type="text"
                  icon={<ReloadOutlined />}
                  onClick={refreshAll}
                  size="small"
                />
              }
            >
              {moodLogs.length === 0 ? (
                <Empty description="Chưa có nhật ký tâm trạng" />
              ) : (
                <Table
                  dataSource={moodLogs}
                  columns={moodColumns}
                  rowKey="mood_id"
                  pagination={{ pageSize: 10, size: 'small' }}
                  size="small"
                />
              )}
            </Card>
          </Col>
        </Row>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ marginBottom: 4 }}>
          Ghi nhật ký
        </Title>
        <Text type="secondary">
          Ghi lại các hoạt động học tập hàng ngày để hệ thống phân tích và tối ưu lịch trình.
        </Text>
      </div>

      <Card>
        <Tabs items={tabs} />
      </Card>
    </div>
  );
}
