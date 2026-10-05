import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Form, Input, Button, Typography, message } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { authApi } from '../api/auth';
import { getErrorMessage } from '../api/client';

const { Text } = Typography;

interface RegisterForm {
  username: string;
  email: string;
  password: string;
  confirm: string;
}

export default function RegisterPage() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values: RegisterForm) => {
    setLoading(true);
    try {
      await authApi.register({
        username: values.username,
        password: values.password,
        email: values.email,
      });
      message.success('Đăng ký thành công! Vui lòng đăng nhập.');
      navigate('/login', { replace: true });
    } catch (err) {
      message.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Form<RegisterForm> name="register" onFinish={onFinish} layout="vertical" size="large">
      <Form.Item
        name="username"
        rules={[
          { required: true, message: 'Vui lòng nhập username' },
          { min: 3, max: 50, message: 'Username từ 3-50 ký tự' },
        ]}
      >
        <Input prefix={<UserOutlined />} placeholder="Username" autoComplete="username" />
      </Form.Item>

      <Form.Item
        name="email"
        rules={[
          { required: true, message: 'Vui lòng nhập email' },
          { type: 'email', message: 'Email không hợp lệ' },
        ]}
      >
        <Input prefix={<MailOutlined />} placeholder="Email" autoComplete="email" />
      </Form.Item>

      <Form.Item
        name="password"
        rules={[
          { required: true, message: 'Vui lòng nhập mật khẩu' },
          { min: 8, message: 'Mật khẩu tối thiểu 8 ký tự' },
        ]}
      >
        <Input.Password
          prefix={<LockOutlined />}
          placeholder="Mật khẩu (≥ 8 ký tự)"
          autoComplete="new-password"
        />
      </Form.Item>

      <Form.Item
        name="confirm"
        dependencies={['password']}
        rules={[
          { required: true, message: 'Vui lòng xác nhận mật khẩu' },
          ({ getFieldValue }) => ({
            validator(_, value) {
              if (!value || getFieldValue('password') === value) return Promise.resolve();
              return Promise.reject(new Error('Mật khẩu không khớp'));
            },
          }),
        ]}
      >
        <Input.Password
          prefix={<LockOutlined />}
          placeholder="Xác nhận mật khẩu"
          autoComplete="new-password"
        />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit" loading={loading} block>
          Đăng ký
        </Button>
      </Form.Item>

      <div style={{ textAlign: 'center' }}>
        <Text type="secondary">
          Đã có tài khoản? <Link to="/login">Đăng nhập</Link>
        </Text>
      </div>
    </Form>
  );
}
