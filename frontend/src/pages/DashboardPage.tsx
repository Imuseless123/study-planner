import { useCallback, useEffect, useState } from 'react';
import {
  Typography, Row, Col, Spin, Empty, Alert, Button, Space, message,
} from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

import { dashboardApi, DashboardSummary } from '../api/dashboard';
import { useAuthStore } from '../store/authStore';
import { getErrorMessage } from '../api/client';

import StatisticsCards from '../components/StatisticsCards';
import WeeklyStudyChart from '../components/WeeklyStudyChart';
import WorkloadHeatmap from '../components/WorkloadHeatmap';
import DeadlineTimeline from '../components/DeadlineTimeline';
import SleepQualityCard from '../components/SleepQualityCard';
import RiskScoreWidget from '../components/RiskScoreWidget';

const { Title, Text } = Typography;

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await dashboardApi.summary();
      setData(res);
    } catch (err) {
      message.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading && !data) {
    return (
      <div style={{ textAlign: 'center', padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!data) {
    return <Empty description="Không tải được dữ liệu" />;
  }

  const hasNoData =
    Object.keys(data.study_hours_by_date).length === 0 &&
    data.sleep_hours_recent.length === 0 &&
    data.upcoming_assignments.length === 0 &&
    data.subjects.length === 0;

  return (
    <div>
      {/* Header */}
      <div
        style={{
          marginBottom: 24,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <div>
          <Title level={2} style={{ marginBottom: 4 }}>
            Xin chào, {user?.username} 👋
          </Title>
          <Text type="secondary">
            Hôm nay là {dayjs().format('dddd, DD/MM/YYYY')}. Đây là tổng quan
            hoạt động học tập của bạn.
          </Text>
        </div>
        <Button
          icon={<ReloadOutlined />}
          onClick={fetchData}
          loading={loading}
        >
          Làm mới
        </Button>
      </div>

      {/* Onboarding alert */}
      {hasNoData && (
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
          message="Bắt đầu sử dụng Study Planner"
          description={
            <Space direction="vertical" size={4}>
              <Text>
                1. Tạo môn học ở trang <strong>Môn học</strong>
              </Text>
              <Text>
                2. Thêm bài tập với deadline ở trang <strong>Bài tập</strong>
              </Text>
              <Text>
                3. Ghi nhật ký học tập hàng ngày ở trang <strong>Ghi nhật ký</strong>
              </Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                Sau khi có dữ liệu, dashboard sẽ hiển thị heatmap, biểu đồ và
                timeline tự động.
              </Text>
            </Space>
          }
        />
      )}

      {/* Statistics Cards */}
      <div style={{ marginBottom: 24 }}>
        <StatisticsCards data={data} />
      </div>

      {/* Chart + Sleep */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={16}>
          <WeeklyStudyChart data={data} />
        </Col>
        <Col xs={24} lg={8}>
          <SleepQualityCard data={data} />
        </Col>
      </Row>

      {/* Heatmap + Risk */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={16}>
          <WorkloadHeatmap data={data} />
        </Col>
        <Col xs={24} lg={8}>
          <RiskScoreWidget />
        </Col>
      </Row>

      {/* Timeline */}
      <Row gutter={[16, 16]}>
        <Col xs={24}>
          <DeadlineTimeline data={data} />
        </Col>
      </Row>
    </div>
  );
}
