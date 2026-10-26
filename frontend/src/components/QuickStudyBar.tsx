import { useEffect, useState } from 'react';
import { Card, Space, Typography, Button, message, Tag, Divider } from 'antd';
import dayjs from 'dayjs';
import { logsApi } from '../api/logs';
import { subjectsApi, Subject } from '../api/subjects';
import { assignmentsApi, Assignment } from '../api/assignments';
import { getErrorMessage } from '../api/client';

const { Text } = Typography;

const DURATIONS = [
  { label: '30m', hours: 0.5 },
  { label: '1h', hours: 1.0 },
  { label: '1.5h', hours: 1.5 },
  { label: '2h', hours: 2.0 },
];

interface Props {
  onLogged?: () => void;
}

export default function QuickStudyBar({ onLogged }: Props) {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<string | null>(null);
  const [selectedAssignment, setSelectedAssignment] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<number | null>(null);
  const [lastLogged, setLastLogged] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [subjList, assignList] = await Promise.all([
          subjectsApi.list(),
          assignmentsApi.list()
        ]);
        setSubjects(subjList);
        setAssignments(assignList.filter(a => !a.is_completed));
        if (subjList.length > 0) setSelectedSubject(subjList[0].subject_id);
      } catch { /* ignore */ }
    })();
  }, []);

  // Reset assignment when subject changes
  useEffect(() => {
    setSelectedAssignment(null);
  }, [selectedSubject]);

  const filteredAssignments = assignments.filter(a => a.subject_id === selectedSubject);

  const handleLog = async (hours: number, index: number) => {
    if (!selectedSubject) return;
    setSubmitting(index);
    try {
      await logsApi.createStudy({
        subject_id: selectedSubject,
        assignment_id: selectedAssignment || undefined,
        start_time: dayjs().subtract(hours, 'hour').toISOString(),
        duration: hours,
        focus_level: 3,
      });
      const subjName = subjects.find((s) => s.subject_id === selectedSubject)?.subject_name || '';
      const assignName = selectedAssignment ? filteredAssignments.find(a => a.assignment_id === selectedAssignment)?.title : null;
      
      setLastLogged(assignName ? `${assignName} (${hours}h)` : `${subjName} (${hours}h)`);
      message.success('Đã ghi nhận phiên học');
      onLogged?.();
    } catch (err) {
      message.error(getErrorMessage(err));
    } finally {
      setSubmitting(null);
    }
  };

  if (subjects.length === 0) {
    return (
      <Card size="small" style={{ background: '#fafafa', height: '100%' }}>
        <Text type="secondary" style={{ fontSize: 12 }}>Tạo môn học trước để ghi phiên học.</Text>
      </Card>
    );
  }

  return (
    <Card
      size="small"
      style={{
        background: 'linear-gradient(135deg, #e6f4ff 0%, #f0f5ff 100%)',
        border: '1px solid #91caff',
        height: '100%',
        display: 'flex',
        flexDirection: 'column'
      }}
      styles={{ body: { flex: 1, display: 'flex', flexDirection: 'column' } }}
    >
      <Space direction="vertical" size={10} style={{ width: '100%', flex: 1 }}>
        <div>
          <Text strong style={{ fontSize: 13 }}>📚 Vừa học xong?</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 11 }}>Chọn môn → chọn thời lượng (2 taps)</Text>
        </div>

        {/* Subject chips */}
        <Space size={6} wrap>
          {subjects.slice(0, 4).map((s) => (
            <Button
              key={s.subject_id}
              size="small"
              type={selectedSubject === s.subject_id ? 'primary' : 'default'}
              onClick={() => setSelectedSubject(s.subject_id)}
              style={{ borderRadius: 16, fontSize: 12 }}
            >
              {s.subject_name}
            </Button>
          ))}
        </Space>

        {/* Assignment context (Optional) */}
        {filteredAssignments.length > 0 && (
          <div style={{ background: 'rgba(255,255,255,0.6)', padding: '8px', borderRadius: 8, border: '1px dashed #91caff' }}>
            <Text type="secondary" style={{ fontSize: 10, display: 'block', marginBottom: 4 }}>
              Bạn đang làm bài nào? (Tùy chọn)
            </Text>
            <Space size={4} wrap>
              {filteredAssignments.map(a => (
                <Tag
                  key={a.assignment_id}
                  color={selectedAssignment === a.assignment_id ? 'blue' : 'default'}
                  style={{ cursor: 'pointer', fontSize: 11, margin: 0 }}
                  onClick={() => setSelectedAssignment(a.assignment_id === selectedAssignment ? null : a.assignment_id)}
                >
                  {a.title}
                </Tag>
              ))}
            </Space>
          </div>
        )}

        <div style={{ marginTop: 'auto' }}>
          <Divider style={{ margin: '8px 0' }} />
          {/* Duration buttons */}
          <Space size={6} style={{ width: '100%' }}>
            {DURATIONS.map((d, i) => (
              <Button
                key={d.label}
                type={submitting === i ? 'primary' : 'default'}
                size="middle"
                onClick={() => handleLog(d.hours, i)}
                loading={submitting === i}
                disabled={submitting !== null || !selectedSubject}
                style={{ flex: 1, height: 44, fontSize: 13 }}
              >
                {d.label}
              </Button>
            ))}
          </Space>
        </div>

        {lastLogged && (
          <div style={{ textAlign: 'right', marginTop: 4 }}>
            <Tag color="green" style={{ fontSize: 11 }}>✅ Đã ghi: {lastLogged}</Tag>
          </div>
        )}
      </Space>
    </Card>
  );
}
