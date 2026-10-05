import { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { Form, Input, Button, Typography, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { authApi } from '../api/auth';
import { getErrorMessage } from '../api/client';
import { useAuthStore } from '../store/authStore';

const { Text } = Typography;

interface LoginForm {
  username: string;
  password: string;
}

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const setAuth = useAuthStore((s) => s.setAuth);
  const setConsent = useAuthStore((s) => s.setConsent);

  const onFinish = async (values: LoginForm) => {
    setLoading(true);
    try {
      // 1. Login để lấy token
      const res = await authApi.login(values);

      // 2. Lưu token vào store NGAY, để interceptor có thể dùng
      //    cho các request tiếp theo. Tạm thời user = null.
      useAuthStore.setState({ token: res.token });

      // 3. Gọi /me và /consent song song, truyền token trực tiếp
      //    (vì interceptor có thể chưa kịp update)
      const [user, consent] = await Promise.all([
        authApi.me(res.token),
        authApi.getConsent(res.token),
      ]);

      // 4. Update store với user đầy đủ + trạng thái consent
      setAuth(res.token, user);
      const hasConsent = !!consent && !consent.withdrawn_at;
      setConsent(hasConsent);

      message.success(`Chào mừng ${user.username}!`);

      // 5. Điều hướng
      const from = (location.state as any)?.from?.pathname;
      if (hasConsent) {
        navigate(from || '/dashboard', { replace: true });
      } else {
        navigate('/consent', { replace: true });
      }
    } catch (err) {
      // Nếu có lỗi, clear token đã set tạm
      useAuthStore.getState().clearAuth();
      message.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Form<LoginForm> name="login" onFinish={onFinish} layout="vertical" size="large">
      <Form.Item
        name="username"
        rules={[{ required: true, message: 'Vui lòng nhập username' }]}
      >
        <Input prefix={<UserOutlined />} placeholder="Username" autoComplete="username" />
      </Form.Item>

      <Form.Item
        name="password"
        rules={[{ required: true, message: 'Vui lòng nhập mật khẩu' }]}
      >
        <Input.Password
          prefix={<LockOutlined />}
          placeholder="Mật khẩu"
          autoComplete="current-password"
        />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit" loading={loading} block>
          Đăng nhập
        </Button>
      </Form.Item>

      <div style={{ textAlign: 'center' }}>
        <Text type="secondary">
          Chưa có tài khoản? <Link to="/register">Đăng ký ngay</Link>
        </Text>
      </div>
    </Form>
  );
}
