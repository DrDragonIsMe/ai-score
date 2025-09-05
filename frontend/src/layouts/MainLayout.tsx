import React, { useState, useEffect } from 'react';
import {
  Layout,
  Menu,
  Button,
  Avatar,
  Dropdown,
  Space,
  Typography,
  theme,
  Modal,
  Form,
  Input,
  message,
  ConfigProvider,
} from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DashboardOutlined,
  BookOutlined,
  BulbOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FolderOutlined,
  BarChartOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  ExclamationCircleOutlined,
  TrophyOutlined,
  SwapOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useThemeStore, getThemeColors } from '../stores/themeStore';
import { useTranslation } from '../stores/i18nStore';

import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';
import './MainLayout.css';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const MainLayout: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [switchAccountModalVisible, setSwitchAccountModalVisible] = useState(false);
  const [switchAccountForm] = Form.useForm();
  const { user, logout, login } = useAuthStore();
  const { config, actualMode, applyTheme } = useThemeStore();
  const { t, language } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const {
    token: { colorBgContainer },
  } = theme.useToken();

  // 应用主题
  useEffect(() => {
    applyTheme();
  }, [config, actualMode, applyTheme]);

  // 获取Ant Design语言包
  const getAntdLocale = () => {
    return language === "en-US" ? enUS : zhCN;
  };

  // 菜单项配置
  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: t('menu.dashboard'),
    },
    {
      key: '/ai-assistant',
      icon: <RobotOutlined />,
      label: t('menu.scorePlus'),
      className: 'score-plus-menu-item',
    },
    {
      key: '/subjects',
      icon: <BookOutlined />,
      label: t('menu.subjects'),
    },
    {
      key: '/exam-papers',
      icon: <FilePdfOutlined />,
      label: t('menu.examPapers'),
    },
    {
      key: '/documents',
      icon: <FolderOutlined />,
      label: t('menu.documents'),
    },
    {
      key: '/diagnosis',
      icon: <BulbOutlined />,
      label: t('menu.diagnosis'),
    },
    {
      key: '/learning-path',
      icon: <FileTextOutlined />,
      label: t('menu.learningPath'),
    },
    {
      key: '/memory-cards',
      icon: <ClockCircleOutlined />,
      label: t('menu.memoryCards'),
    },
    {
      key: '/mistake-book',
      icon: <ExclamationCircleOutlined />,
      label: t('menu.mistakeBook'),
    },
    {
      key: '/exam',
      icon: <TrophyOutlined />,
      label: t('menu.exam'),
    },
    {
      key: '/analytics',
      icon: <BarChartOutlined />,
      label: t('menu.analytics'),
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: t('common.settings'),
    },
  ];

  // 切换账号功能
  const handleSwitchAccount = () => {
    setSwitchAccountModalVisible(true);
    switchAccountForm.resetFields();
  };

  // 执行账号切换
  const handleSwitchAccountSubmit = async (values: { username: string; password: string }) => {
    try {
      await login({
        email: values.username, // 后端使用username字段
        password: values.password
      });
      message.success('账号切换成功！');
      setSwitchAccountModalVisible(false);
      switchAccountForm.resetFields();
      // 刷新页面以更新UI
      window.location.reload();
    } catch (error) {
      console.error('切换账号失败:', error);
      message.error('切换账号失败，请检查用户名和密码');
    }
  };

  // 取消切换账号
  const handleSwitchAccountCancel = () => {
    setSwitchAccountModalVisible(false);
    switchAccountForm.resetFields();
  };

  // 用户菜单
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: t('common.profile'),
      onClick: () => navigate('/profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: t('common.settings'),
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'switch-account',
      icon: <SwapOutlined />,
      label: '切换账号', // 保持中文，因为这是特定功能
      onClick: handleSwitchAccount,
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: t('common.logout'),
      onClick: () => {
        logout();
        navigate('/login');
      },
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  return (
    <ConfigProvider
      locale={getAntdLocale()}
      theme={{
        token: {
          colorPrimary: getThemeColors(config.style, config.customColors).primary,
        },
      }}
    >
      <Layout style={{ minHeight: '100vh' }}>
        <Sider 
          trigger={null} 
          collapsible 
          collapsed={collapsed}
          width={260}
          collapsedWidth={80}
          style={{
            background: 'linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%)',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            boxShadow: '2px 0 8px rgba(0, 0, 0, 0.06)',
            borderRight: '1px solid #e1e5e9',
            position: 'relative',
            zIndex: 10,
          }}
        >
          <div
            style={{
              height: 32,
              margin: 16,
              background: 'linear-gradient(135deg, #6c7b95 0%, #a8b5c8 100%)',
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontWeight: 'bold',
              boxShadow: '0 2px 8px rgba(108, 123, 149, 0.2)',
            }}
          >
            {collapsed ? 'AI' : 'AI学习系统'}
          </div>
          <Menu
            theme="light"
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={handleMenuClick}
            style={{
              background: 'transparent',
              border: 'none',
            }}
          />
        </Sider>
        <Layout>
          <Header
            style={{
              padding: '0 24px',
              background: 'var(--background-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              boxShadow: 'var(--shadow-soft)',
              borderBottom: '1px solid var(--border-color)',
              backdropFilter: 'blur(10px)',
              position: 'sticky',
              top: 0,
              zIndex: 100,
            }}
          >
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              style={{
                fontSize: '16px',
                width: 64,
                height: 64,
                transition: 'all 0.2s ease-in-out',
                borderRadius: 'var(--border-radius)',
              }}
            />
            <Space>
              <Text>欢迎回来，{user?.full_name || user?.username}</Text>
              <Dropdown
                menu={{ items: userMenuItems }}
                placement="bottomRight"
                arrow
              >
                <Avatar
                  size="large"
                  icon={<UserOutlined />}
                  src={user?.avatar_url}
                  style={{ 
                    cursor: 'pointer',
                    transition: 'all 0.2s ease-in-out',
                    boxShadow: 'var(--shadow-light)'
                  }}
                  className="user-avatar"
                />
              </Dropdown>
            </Space>
          </Header>
          <Content
            style={{
              margin: '16px',
              padding: '32px',
              minHeight: 'calc(100vh - 120px)',
              background: 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)',
              borderRadius: '12px',
              transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
              position: 'relative',
              overflow: 'hidden',
              animation: 'fadeInContent 0.6s ease-out',
            }}
          >
            <div style={{
              opacity: 1,
              transform: 'translateY(0)',
              transition: 'opacity 0.4s ease-out, transform 0.4s ease-out',
              animation: 'slideInUp 0.5s ease-out',
            }}>
              {children}
            </div>
          </Content>
        </Layout>
        </Layout>

        {/* 切换账号模态框 */}
      <Modal
        title="切换账号"
        open={switchAccountModalVisible}
        onCancel={handleSwitchAccountCancel}
        footer={null}
        width={400}
      >
        <Form
          form={switchAccountForm}
          layout="vertical"
          onFinish={handleSwitchAccountSubmit}
        >
          <Form.Item
            label="用户名"
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
            ]}
          >
            <Input placeholder="请输入用户名" />
          </Form.Item>
          
          <Form.Item
            label="密码"
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
            ]}
          >
            <Input.Password placeholder="请输入密码" />
          </Form.Item>
          
          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={handleSwitchAccountCancel}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                切换
              </Button>
            </Space>
          </Form.Item>
        </Form>
        
        <div style={{ marginTop: 16, padding: 12, backgroundColor: '#f6f8fa', borderRadius: 6 }}>
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            提示：可以切换到其他管理员或学生账号。<br/>
            管理员账号：admin / admin123<br/>
            学生账号：student / student123
          </Typography.Text>
        </div>
        </Modal>
    </ConfigProvider>
  );
};

export default MainLayout;