import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FloatButton, Drawer, Button, Space, Typography } from 'antd';
import {
  PlusOutlined, BookOutlined, MoonOutlined, SmileOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

interface Props {
  onQuickStudy?: () => void;
  onQuickSleep?: () => void;
  onQuickMood?: () => void;
}

/**
 * Floating Action Button (bottom-center) for 1-tap quick logging.
 * Opens a bottom sheet with 3 shortcuts.
 */
export default function QuickActionFab({ onQuickStudy, onQuickSleep, onQuickMood }: Props) {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  const close = () => setOpen(false);

  return (
    <>
      <FloatButton
        icon={<PlusOutlined style={{ fontSize: 22 }} />}
        type="primary"
        style={{
          right: 'calc(50% - 28px)',
          bottom: 74,
          width: 56,
          height: 56,
          zIndex: 101,
        }}
        onClick={() => setOpen(true)}
      />
      <Drawer
        title="Ghi nhật ký nhanh"
        placement="bottom"
        height="auto"
        open={open}
        onClose={close}
        styles={{ body: { paddingBottom: 24 } }}
      >
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            1 tap → 3 taps để hoàn tất. Dành cho mobile.
          </Text>

          <Button
            size="large"
            block
            icon={<BookOutlined />}
            onClick={() => {
              close();
              if (onQuickStudy) onQuickStudy();
              else navigate('/logging?tab=study&quick=1');
            }}
            style={{
              height: 56,
              justifyContent: 'flex-start',
              textAlign: 'left',
              paddingLeft: 20,
            }}
          >
            📚 Vừa học xong — Ghi phiên học
          </Button>

          <Button
            size="large"
            block
            icon={<MoonOutlined />}
            onClick={() => {
              close();
              if (onQuickSleep) onQuickSleep();
              else navigate('/logging?tab=sleep&quick=1');
            }}
            style={{
              height: 56,
              justifyContent: 'flex-start',
              textAlign: 'left',
              paddingLeft: 20,
            }}
          >
            🌙 Vừa thức dậy — Ghi giấc ngủ
          </Button>

          <Button
            size="large"
            block
            icon={<SmileOutlined />}
            onClick={() => {
              close();
              if (onQuickMood) onQuickMood();
              else navigate('/logging?tab=mood&quick=1');
            }}
            style={{
              height: 56,
              justifyContent: 'flex-start',
              textAlign: 'left',
              paddingLeft: 20,
            }}
          >
            😊 Cảm thấy thế nào? — Ghi tâm trạng
          </Button>
        </Space>
      </Drawer>
    </>
  );
}
