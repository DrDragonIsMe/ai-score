import React, { useState } from 'react';
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
import AIAssistant from '../components/AIAssistant/AIAssistant';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const MainLayout: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [switchAccountModalVisible, setSwitchAccountModalVisible] = useState(false);
  const [aiAssistantVisible, setAiAssistantVisible] = useState(false);
  const [switchAccountForm] = Form.useForm();
  const { user, logout, login } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  // 菜单项配置
  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: '/subjects',
      icon: <BookOutlined />,
      label: '学科管理',
    },
    {
      key: '/exam-papers',
      icon: <FilePdfOutlined />,
      label: '试卷管理',
    },
    {
      key: '/diagnosis',
      icon: <BulbOutlined />,
      label: '学习诊断',
    },
    {
      key: '/learning-path',
      icon: <FileTextOutlined />,
      label: '学习路径',
    },
    {
      key: '/memory-cards',
      icon: <ClockCircleOutlined />,
      label: '记忆强化',
    },
    {
      key: '/mistake-book',
      icon: <ExclamationCircleOutlined />,
      label: '错题本',
    },
    {
      key: '/exam',
      icon: <TrophyOutlined />,
      label: '考试测评',
    },
    {
      key: '/analytics',
      icon: <BarChartOutlined />,
      label: '学习分析',
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
      label: '个人资料',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'switch-account',
      icon: <SwapOutlined />,
      label: '切换账号',
      onClick: handleSwitchAccount,
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
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
    <Layout style={{ minHeight: '100vh' }}>
      <Sider trigger={null} collapsible collapsed={collapsed}>
        <div
          style={{
            height: 32,
            margin: 16,
            background: 'rgba(255, 255, 255, 0.2)',
            borderRadius: 6,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 'bold',
          }}
        >
          {collapsed ? 'AI' : 'AI学习系统'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            padding: '0 16px',
            background: colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
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
            }}
          />
          <Space>
            <Button
              type="primary"
              icon={<RobotOutlined />}
              onClick={() => setAiAssistantVisible(true)}
              style={{
                borderRadius: '20px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                border: 'none',
                boxShadow: '0 4px 15px 0 rgba(116, 75, 162, 0.3)',
              }}
            >
              高小分
            </Button>
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
                style={{ cursor: 'pointer' }}
              />
            </Dropdown>
          </Space>
        </Header>
        <Content
          style={{
            margin: '24px 16px',
            padding: 24,
            minHeight: 280,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
          }}
        >
          {children}
        </Content>
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

      {/* AI助理组件 */}
      <AIAssistant
        visible={aiAssistantVisible}
        onClose={() => setAiAssistantVisible(false)}
      />
    </Layout>
  );
};

export default MainLayout;