import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Avatar,
  Upload,
  Space,
  Typography,
  Row,
  Col,
  Divider,
  Select,
  message,
  Spin,
  Tag,
  Descriptions,
  Modal,
} from 'antd';
import {
  UserOutlined,
  CameraOutlined,
  EditOutlined,
  SaveOutlined,
  MailOutlined,
  PhoneOutlined,
  HomeOutlined,
  BookOutlined,
  GlobalOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../stores/authStore';
import type { UploadFile } from 'antd/es/upload/interface';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

interface UserProfile {
  id: string;
  username: string;
  email: string;
  real_name?: string;
  avatar?: string;
  phone?: string;
  grade?: string;
  school?: string;
  language: string;
  timezone: string;
  nickname?: string; // 用户希望AI称呼的名字
  preferred_greeting?: string; // 用户偏好的问候方式
  bio?: string; // 个人简介
  created_at: string;
  last_login_at?: string;
}

const Profile: React.FC = () => {
  const { user, token, updateUser } = useAuthStore();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [editing, setEditing] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState<string>('');
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [passwordForm] = Form.useForm();
  const [currentUser, setCurrentUser] = useState<any>(null);

  // 获取当前用户信息
  const fetchCurrentUser = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/users/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      const result = await response.json();
      if (result.success) {
        setCurrentUser(result.data);
        return result.data;
      } else {
        console.error('Failed to fetch user:', result.message);
        return user; // 回退到store中的用户数据
      }
    } catch (error) {
      console.error('Error fetching user:', error);
      return user; // 回退到store中的用户数据
    }
  };

  useEffect(() => {
    const loadUserData = async () => {
      let userData = user;
      if (token) {
        userData = await fetchCurrentUser();
      }
      
      if (userData) {
        form.setFieldsValue({
          username: userData.username,
          email: userData.email,
          real_name: userData.real_name || '',
          phone: userData.phone || '',
          grade: userData.grade || '',
          school: userData.school || '',
          language: userData.language || 'zh',
          timezone: userData.timezone || 'Asia/Shanghai',
          nickname: userData.nickname || userData.real_name || userData.username,
          preferred_greeting: userData.preferred_greeting || 'casual',
          bio: userData.bio || '',
        });
        setAvatarUrl(userData.avatar_url || '');
      }
    };
    
    loadUserData();
  }, [user, token, form]);

  const handleSave = async (values: any) => {
    setLoading(true);
    try {
      // 这里应该调用API更新用户信息
      const response = await fetch(`http://localhost:5001/api/users/${user?.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          real_name: values.real_name,
          nickname: values.nickname,
          grade: values.grade,
          school: values.school,
          bio: values.bio,
          language: values.language,
          timezone: values.timezone,
          preferred_greeting: values.preferred_greeting,
          avatar: avatarUrl,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          updateUser(result.data);
          message.success('个人资料更新成功！');
          setEditing(false);
        } else {
          throw new Error(result.message || '更新失败');
        }
      } else {
        throw new Error('网络请求失败');
      }
    } catch (error) {
      console.error('更新个人资料失败:', error);
      message.error('更新失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarChange = (info: any) => {
    if (info.file.status === 'uploading') {
      setLoading(true);
      return;
    }
    if (info.file.status === 'done') {
      // 获取上传后的URL
      const url = info.file.response?.url || URL.createObjectURL(info.file.originFileObj);
      setAvatarUrl(url);
      setLoading(false);
    }
  };

  const beforeUpload = (file: File) => {
    const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png';
    if (!isJpgOrPng) {
      message.error('只能上传 JPG/PNG 格式的图片!');
      return false;
    }
    const isLt2M = file.size / 1024 / 1024 < 2;
    if (!isLt2M) {
      message.error('图片大小不能超过 2MB!');
      return false;
    }
    return true;
  };

  const handlePasswordChange = async (values: any) => {
    setLoading(true);
    try {
      const response = await fetch('/api/users/password', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify(values),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          message.success('密码修改成功！');
          setPasswordModalVisible(false);
          passwordForm.resetFields();
        } else {
          throw new Error(result.message || '密码修改失败');
        }
      } else {
        throw new Error('网络请求失败');
      }
    } catch (error) {
      console.error('密码修改失败:', error);
      message.error('密码修改失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const greetingOptions = [
    { value: 'formal', label: '正式称呼（您好，[称呼]）' },
    { value: 'casual', label: '亲切称呼（嗨，[称呼]）' },
    { value: 'friendly', label: '友好称呼（[称呼]，你好）' },
    { value: 'professional', label: '专业称呼（[称呼]同学）' },
  ];

  if (!user) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <Title level={2} style={{ marginBottom: '24px' }}>
        <UserOutlined style={{ marginRight: '8px' }} />
        个人资料
      </Title>

      <Row gutter={[24, 24]}>
        {/* 左侧：基本信息卡片 */}
        <Col xs={24} lg={8}>
          <Card>
            <div style={{ textAlign: 'center', marginBottom: '24px' }}>
              <Upload
                name="avatar"
                listType="picture-card"
                className="avatar-uploader"
                showUploadList={false}
                action="/api/upload/avatar"
                beforeUpload={beforeUpload}
                onChange={handleAvatarChange}
                disabled={!editing}
              >
                {avatarUrl ? (
                  <Avatar size={100} src={avatarUrl} />
                ) : (
                  <Avatar size={100} icon={<UserOutlined />} />
                )}
                {editing && (
                  <div className="upload-overlay">
                    <CameraOutlined style={{ fontSize: '24px', color: '#fff' }} />
                  </div>
                )}
              </Upload>
              <div style={{ marginTop: '16px' }}>
                <Title level={4} style={{ margin: 0 }}>
                  {(currentUser || user)?.real_name || (currentUser || user)?.username}
                </Title>
                <Text type="secondary">{(currentUser || user)?.email}</Text>
                <br />
                <Tag color="blue" style={{ marginTop: '8px' }}>
                  {(currentUser || user)?.role === 'student' ? '学生' : (currentUser || user)?.role === 'teacher' ? '教师' : '管理员'}
                </Tag>
              </div>
            </div>

            <Descriptions column={1} size="small">
              <Descriptions.Item label="注册时间">
                {new Date(user.created_at).toLocaleDateString()}
              </Descriptions.Item>
              {user.last_login_at && (
                <Descriptions.Item label="最后登录">
                  {new Date(user.last_login_at).toLocaleString()}
                </Descriptions.Item>
              )}
            </Descriptions>

            <Divider />

            <Space direction="vertical" style={{ width: '100%' }}>
              <Button
                type={editing ? 'default' : 'primary'}
                icon={editing ? <SaveOutlined /> : <EditOutlined />}
                onClick={() => {
                  if (editing) {
                    form.submit();
                  } else {
                    setEditing(true);
                  }
                }}
                loading={loading}
                block
              >
                {editing ? '保存更改' : '编辑资料'}
              </Button>
              
              {editing && (
                <Button
                  onClick={() => {
                    setEditing(false);
                    form.resetFields();
                  }}
                  block
                >
                  取消编辑
                </Button>
              )}

              <Button
                onClick={() => setPasswordModalVisible(true)}
                block
              >
                修改密码
              </Button>
            </Space>
          </Card>
        </Col>

        {/* 右侧：详细信息表单 */}
        <Col xs={24} lg={16}>
          <Card title="详细信息">
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSave}
              disabled={!editing}
            >
              <Row gutter={16}>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="用户名"
                    name="username"
                    rules={[{ required: true, message: '请输入用户名' }]}
                  >
                    <Input prefix={<UserOutlined />} placeholder="请输入用户名" />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="真实姓名"
                    name="real_name"
                  >
                    <Input prefix={<UserOutlined />} placeholder="请输入真实姓名" />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="邮箱"
                    name="email"
                    tooltip="登录邮箱不可修改"
                  >
                    <Input 
                      prefix={<MailOutlined />} 
                      placeholder="请输入邮箱" 
                      disabled={true}
                      style={{ color: '#666', backgroundColor: '#f5f5f5' }}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="手机号"
                    name="phone"
                  >
                    <Input prefix={<PhoneOutlined />} placeholder="请输入手机号" />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="年级"
                    name="grade"
                  >
                    <Select placeholder="请选择年级">
                      <Option value="小学一年级">小学一年级</Option>
                      <Option value="小学二年级">小学二年级</Option>
                      <Option value="小学三年级">小学三年级</Option>
                      <Option value="小学四年级">小学四年级</Option>
                      <Option value="小学五年级">小学五年级</Option>
                      <Option value="小学六年级">小学六年级</Option>
                      <Option value="初中一年级">初中一年级</Option>
                      <Option value="初中二年级">初中二年级</Option>
                      <Option value="初中三年级">初中三年级</Option>
                      <Option value="高中一年级">高中一年级</Option>
                      <Option value="高中二年级">高中二年级</Option>
                      <Option value="高中三年级">高中三年级</Option>
                      <Option value="大学">大学</Option>
                      <Option value="其他">其他</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="学校"
                    name="school"
                  >
                    <Input prefix={<HomeOutlined />} placeholder="请输入学校名称" />
                  </Form.Item>
                </Col>
              </Row>

              <Divider orientation="left">AI助理设置</Divider>

              <Row gutter={16}>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="AI称呼"
                    name="nickname"
                    tooltip="AI助理将使用这个称呼来称呼您"
                    rules={[{ required: true, message: '请输入您希望AI称呼您的名字' }]}
                  >
                    <Input placeholder="例如：小明、张同学、小王等" />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="问候方式"
                    name="preferred_greeting"
                    tooltip="选择AI助理与您交流时的问候风格"
                  >
                    <Select placeholder="请选择问候方式">
                      {greetingOptions.map(option => (
                        <Option key={option.value} value={option.value}>
                          {option.label}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                label="个人简介"
                name="bio"
                tooltip="简单介绍一下自己，AI助理可以更好地了解您"
              >
                <TextArea
                  rows={3}
                  placeholder="例如：我是一名高中生，喜欢数学和物理，希望通过AI助理提高学习效率..."
                  maxLength={200}
                  showCount
                />
              </Form.Item>

              <Divider orientation="left">系统设置</Divider>

              <Row gutter={16}>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="语言偏好"
                    name="language"
                  >
                    <Select>
                      <Option value="zh">中文</Option>
                      <Option value="en">English</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="时区"
                    name="timezone"
                  >
                    <Select>
                      <Option value="Asia/Shanghai">北京时间 (UTC+8)</Option>
                      <Option value="America/New_York">纽约时间 (UTC-5)</Option>
                      <Option value="Europe/London">伦敦时间 (UTC+0)</Option>
                      <Option value="Asia/Tokyo">东京时间 (UTC+9)</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          </Card>
        </Col>
      </Row>

      {/* 修改密码模态框 */}
      <Modal
        title="修改密码"
        open={passwordModalVisible}
        onCancel={() => {
          setPasswordModalVisible(false);
          passwordForm.resetFields();
        }}
        footer={null}
        width={400}
      >
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handlePasswordChange}
        >
          <Form.Item
            label="当前密码"
            name="old_password"
            rules={[{ required: true, message: '请输入当前密码' }]}
          >
            <Input.Password placeholder="请输入当前密码" />
          </Form.Item>
          
          <Form.Item
            label="新密码"
            name="new_password"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码至少6位字符' },
            ]}
          >
            <Input.Password placeholder="请输入新密码" />
          </Form.Item>
          
          <Form.Item
            label="确认新密码"
            name="confirm_password"
            dependencies={['new_password']}
            rules={[
              { required: true, message: '请确认新密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password placeholder="请再次输入新密码" />
          </Form.Item>
          
          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button
                onClick={() => {
                  setPasswordModalVisible(false);
                  passwordForm.resetFields();
                }}
              >
                取消
              </Button>
              <Button type="primary" htmlType="submit" loading={loading}>
                确认修改
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <style dangerouslySetInnerHTML={{
        __html: `
          .avatar-uploader {
            position: relative;
          }
          .avatar-uploader:hover .upload-overlay {
            opacity: 1;
          }
          .upload-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            opacity: 0;
            transition: opacity 0.3s;
            cursor: pointer;
          }
        `
      }} />
    </div>
  );
};

export default Profile;