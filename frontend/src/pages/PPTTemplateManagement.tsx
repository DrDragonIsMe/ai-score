import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Upload,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Tag,
  Space,
  Typography,
  Row,
  Col,
  Divider
} from 'antd';
import {
  UploadOutlined,
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  PlusOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { UploadFile } from 'antd/es/upload/interface';

const { Title, Text } = Typography;
const { Option } = Select;

interface PPTTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  file_path: string;
  preview_image?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

const PPTTemplateManagement: React.FC = () => {
  const [templates, setTemplates] = useState<PPTTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [currentTemplate, setCurrentTemplate] = useState<PPTTemplate | null>(null);
  const [categories, setCategories] = useState<string[]>([]);
  const [form] = Form.useForm();
  const [uploadForm] = Form.useForm();

  // 获取模板列表
  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:5001/api/ppt-template/list', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      const result = await response.json();
      if (result.success) {
        setTemplates(result.data || []);
      } else {
        message.error('获取模板列表失败');
      }
    } catch (error) {
      console.error('获取模板列表失败:', error);
      message.error('获取模板列表失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 获取模板分类
  const fetchCategories = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/ppt-template/categories', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      const result = await response.json();
      if (result.success) {
        setCategories(result.data || []);
      }
    } catch (error) {
      console.error('获取分类列表失败:', error);
    }
  };

  useEffect(() => {
    fetchTemplates();
    fetchCategories();
  }, []);

  // 上传模板
  const handleUpload = async (values: any) => {
    try {
      const formData = new FormData();
      formData.append('file', values.file.file);
      formData.append('name', values.name);
      formData.append('description', values.description || '');
      formData.append('category', values.category);

      const response = await fetch('http://localhost:5001/api/ppt-template/upload', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();
      if (result.success) {
        message.success('模板上传成功');
        setUploadModalVisible(false);
        uploadForm.resetFields();
        fetchTemplates();
      } else {
        message.error(result.message || '模板上传失败');
      }
    } catch (error) {
      console.error('模板上传失败:', error);
      message.error('模板上传失败，请重试');
    }
  };

  // 更新模板信息
  const handleUpdate = async (values: any) => {
    if (!currentTemplate) return;

    try {
      const response = await fetch(`http://localhost:5001/api/ppt-template/${currentTemplate.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(values)
      });

      const result = await response.json();
      if (result.success) {
        message.success('模板更新成功');
        setEditModalVisible(false);
        setCurrentTemplate(null);
        form.resetFields();
        fetchTemplates();
      } else {
        message.error(result.message || '模板更新失败');
      }
    } catch (error) {
      console.error('模板更新失败:', error);
      message.error('模板更新失败，请重试');
    }
  };

  // 删除模板
  const handleDelete = async (templateId: string) => {
    try {
      const response = await fetch(`http://localhost:5001/api/ppt-template/${templateId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      const result = await response.json();
      if (result.success) {
        message.success('模板删除成功');
        fetchTemplates();
      } else {
        message.error(result.message || '模板删除失败');
      }
    } catch (error) {
      console.error('模板删除失败:', error);
      message.error('模板删除失败，请重试');
    }
  };

  // 下载模板
  const handleDownload = async (templateId: string, filename: string) => {
    try {
      const response = await fetch(`http://localhost:5001/api/ppt-template/${templateId}/download`, {
        method: 'GET'
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        message.success('模板下载成功');
      } else {
        message.error('模板下载失败');
      }
    } catch (error) {
      console.error('模板下载失败:', error);
      message.error('模板下载失败，请重试');
    }
  };

  // 编辑模板
  const handleEdit = (template: PPTTemplate) => {
    setCurrentTemplate(template);
    form.setFieldsValue({
      name: template.name,
      description: template.description,
      category: template.category,
      is_active: template.is_active
    });
    setEditModalVisible(true);
  };

  const columns: ColumnsType<PPTTemplate> = [
    {
      title: '模板名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: PPTTemplate) => (
        <Space>
          <FileTextOutlined />
          <span>{text}</span>
          {record.is_active && <Tag color="green">活跃</Tag>}
        </Space>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => <Tag color="blue">{category}</Tag>,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record: PPTTemplate) => (
        <Space size="middle">
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => handleDownload(record.id, record.name)}
            title="下载模板"
          />
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            title="编辑模板"
          />
          <Popconfirm
            title="确定要删除这个模板吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="text"
              icon={<DeleteOutlined />}
              danger
              title="删除模板"
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <Title level={3} style={{ margin: 0 }}>PPT模板管理</Title>
                <Text type="secondary">管理和维护PPT生成模板</Text>
              </div>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setUploadModalVisible(true)}
              >
                上传模板
              </Button>
            </div>
            
            <Divider />
            
            <Table
              columns={columns}
              dataSource={templates}
              rowKey="id"
              loading={loading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 个模板`,
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* 上传模板弹窗 */}
      <Modal
        title="上传PPT模板"
        open={uploadModalVisible}
        onCancel={() => {
          setUploadModalVisible(false);
          uploadForm.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={uploadForm}
          layout="vertical"
          onFinish={handleUpload}
        >
          <Form.Item
            name="name"
            label="模板名称"
            rules={[{ required: true, message: '请输入模板名称' }]}
          >
            <Input placeholder="请输入模板名称" />
          </Form.Item>
          
          <Form.Item
            name="category"
            label="模板分类"
            rules={[{ required: true, message: '请选择模板分类' }]}
          >
            <Select placeholder="请选择模板分类" allowClear>
              {categories.map(category => (
                <Option key={category} value={category}>{category}</Option>
              ))}
              <Option value="其他">其他</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="description"
            label="模板描述"
          >
            <Input.TextArea rows={3} placeholder="请输入模板描述" />
          </Form.Item>
          
          <Form.Item
            name="file"
            label="模板文件"
            rules={[{ required: true, message: '请选择模板文件' }]}
          >
            <Upload
              accept=".pptx,.ppt"
              maxCount={1}
              beforeUpload={() => false}
            >
              <Button icon={<UploadOutlined />}>选择PPT文件</Button>
            </Upload>
          </Form.Item>
          
          <Form.Item style={{ textAlign: 'right', marginBottom: 0 }}>
            <Space>
              <Button onClick={() => {
                setUploadModalVisible(false);
                uploadForm.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                上传
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑模板弹窗 */}
      <Modal
        title="编辑模板信息"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setCurrentTemplate(null);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleUpdate}
        >
          <Form.Item
            name="name"
            label="模板名称"
            rules={[{ required: true, message: '请输入模板名称' }]}
          >
            <Input placeholder="请输入模板名称" />
          </Form.Item>
          
          <Form.Item
            name="category"
            label="模板分类"
            rules={[{ required: true, message: '请选择模板分类' }]}
          >
            <Select placeholder="请选择模板分类" allowClear>
              {categories.map(category => (
                <Option key={category} value={category}>{category}</Option>
              ))}
              <Option value="其他">其他</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="description"
            label="模板描述"
          >
            <Input.TextArea rows={3} placeholder="请输入模板描述" />
          </Form.Item>
          
          <Form.Item
            name="is_active"
            label="状态"
            valuePropName="checked"
          >
            <Select>
              <Option value={true}>活跃</Option>
              <Option value={false}>非活跃</Option>
            </Select>
          </Form.Item>
          
          <Form.Item style={{ textAlign: 'right', marginBottom: 0 }}>
            <Space>
              <Button onClick={() => {
                setEditModalVisible(false);
                setCurrentTemplate(null);
                form.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                更新
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default PPTTemplateManagement;