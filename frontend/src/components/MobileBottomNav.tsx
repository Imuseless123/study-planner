import { Link, useLocation } from 'react-router-dom';
import {
  HomeOutlined, BookOutlined, CalendarOutlined, SettingOutlined,
} from '@ant-design/icons';

const ITEMS = [
  { key: '/dashboard', icon: <HomeOutlined />, label: 'Home' },
  { key: '/logging', icon: <BookOutlined />, label: 'Nhật ký' },
  { key: '/schedule', icon: <CalendarOutlined />, label: 'Lịch' },
  { key: '/settings', icon: <SettingOutlined />, label: 'Cài đặt' },
];

/**
 * Bottom navigation bar — mobile only.
 * Left slot: Home / Logging. Right slot: Schedule / Settings.
 * The middle slot (FAB) is provided separately by QuickActionFab.
 */
export default function MobileBottomNav() {
  const location = useLocation();

  const renderItem = (item: typeof ITEMS[0], index: number) => {
    const active = location.pathname.startsWith(item.key);
    // Add empty placeholder for the center FAB slot
    const isRightSide = index >= 2;

    return (
      <>
        {!isRightSide && index === 1 && <div style={{ width: 56 }} />}
        <Link
          key={item.key}
          to={item.key}
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '6px 0',
            fontSize: 11,
            color: active ? '#667eea' : '#8c8c8c',
            textDecoration: 'none',
            fontWeight: active ? 600 : 400,
            transition: 'color 0.2s',
          }}
        >
          <div style={{ fontSize: 20, marginBottom: 2 }}>{item.icon}</div>
          <span>{item.label}</span>
        </Link>
        {isRightSide && index === 2 && <div style={{ width: 56 }} />}
      </>
    );
  };

  return (
    <nav
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        height: 60,
        background: '#fff',
        borderTop: '1px solid #f0f0f0',
        display: 'flex',
        alignItems: 'stretch',
        zIndex: 100,
        paddingBottom: 'env(safe-area-inset-bottom)',
        boxShadow: '0 -2px 8px rgba(0,0,0,0.04)',
      }}
    >
      {ITEMS.map((item, i) => (
        <div key={item.key} style={{ flex: 1, display: 'flex' }}>
          {renderItem(item, i)}
        </div>
      ))}
    </nav>
  );
}
