import {
    LockOutlined,
    MailOutlined
} from '@ant-design/icons';
import {
    Alert,
    Button,
    Card,
    Divider,
    Form,
    Input,
    Space,
    Typography,
} from 'antd';
import React, { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import type { LoginRequest } from '../types';

const { Title, Text } = Typography;

const Login: React.FC = () => {
    const [form] = Form.useForm();
    const { login, isLoading, error, isAuthenticated, clearError } = useAuthStore();
    const navigate = useNavigate();

    useEffect(() => {
        if (isAuthenticated) {
            navigate('/dashboard');
        }
    }, [isAuthenticated, navigate]);

    useEffect(() => {
        // 清除之前的错误
        return () => clearError();
    }, [clearError]);

    const handleSubmit = async (values: LoginRequest) => {
        try {
            await login(values);
            // 登录成功后会通过useEffect重定向
        } catch (error) {
            // 错误已经在store中处理
        }
    };

    return (
        <div
            style={{
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                padding: '20px',
            }}
        >
            <Card
                style={{
                    width: '100%',
                    maxWidth: 400,
                    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                }}
            >
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                    <div style={{ textAlign: 'center' }}>
                        <Title level={2} style={{ marginBottom: 8 }}>
                            AI智能学习系统
                        </Title>
                        <Text type="secondary">登录您的账户</Text>
                    </div>

                    {error && (
                        <Alert
                            message={error}
                            type="error"
                            showIcon
                            closable
                            onClose={clearError}
                        />
                    )}

                    <Form
                        form={form}
                        name="login"
                        onFinish={handleSubmit}
                        autoComplete="off"
                        size="large"
                    >
                        <Form.Item
                            name="email"
                            rules={[
                                { required: true, message: '请输入邮箱地址' },
                                { type: 'email', message: '请输入有效的邮箱地址' },
                            ]}
                        >
                            <Input
                                prefix={<MailOutlined />}
                                placeholder="邮箱地址"
                            />
                        </Form.Item>

                        <Form.Item
                            name="password"
                            rules={[
                                { required: true, message: '请输入密码' },
                                { min: 6, message: '密码至少6位字符' },
                            ]}
                        >
                            <Input.Password
                                prefix={<LockOutlined />}
                                placeholder="密码"
                            />
                        </Form.Item>

                        <Form.Item>
                            <Button
                                type="primary"
                                htmlType="submit"
                                loading={isLoading}
                                style={{ width: '100%' }}
                            >
                                登录
                            </Button>
                        </Form.Item>
                    </Form>

                    <Divider>或</Divider>

                    <div style={{ textAlign: 'center' }}>
                        <Text type="secondary">
                            还没有账户？{' '}
                            <Link to="/register">
                                立即注册
                            </Link>
                        </Text>
                    </div>
                </Space>
            </Card>
        </div>
    );
};

export default Login;
