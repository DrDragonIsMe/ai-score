import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Drawer,
  Form,
  Input,
  Select,
  Upload,
  message,
  Tabs,
  Progress,
  Tooltip,
  Badge,
  Statistic,
  Row,
  Col
} from 'antd';
import {
  PlusOutlined,
  UploadOutlined,
  EyeOutlined,
  DownloadOutlined,
  DeleteOutlined,
  FileTextOutlined,
  FolderAddOutlined,
  SearchOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { UploadProps } from 'antd';

const { Option } = Select;
const { TextArea } = Input;

interface Document {
  id: string;
  filename: string;
  title: string;
  description?: string;
  file_size: number;
  file_type: string;
  parse_status: 'pending' | 'processing' | 'completed' | 'failed';
  parse_progress: number;
  created_at: string;
  updated_at: string;
  category?: {
    id: string;
    name: string;
  };
  tags: string[];
  page_count?: number;
  word_count?: number;
}

interface Category {
  id: string;
  name: string;
  description?: string;
  document_count?: number;
}

interface DocumentStats {
  total_documents: number;
  status_stats: {
    pending: number;
    processing: number;
    completed: number;
    failed: number;
  };
  type_stats: Record<string, number>;
}

const DocumentManagement: React.FC = () => {
  const [activeTab, setActiveTab] = useState('list');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [stats, setStats] = useState<DocumentStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [categoryModalVisible, setCategoryModalVisible] = useState(false);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [form] = Form.useForm();
  const [categoryForm] = Form.useForm();

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'processing':
        return 'processing';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  // 获取状态文本
  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return '解析完成';
      case 'processing':
        return '解析中';
      case 'failed':
        return '解析失败';
      default:
        return '等待解析';
    }
  };

  // 获取文档列表
  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/document/list');
      const result = await response.json();
      
      if (result.success) {
        setDocuments(result.data.documents || []);
      } else {
        message.error('获取文档列表失败: ' + result.message);
      }
    } catch (error) {
      console.error('获取文档列表失败:', error);
      message.error('获取文档列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取分类列表
  const fetchCategories = async () => {
    try {
      const response = await fetch('/api/document/categories');
      const result = await response.json();
      
      if (result.success) {
        setCategories(result.data || []);
      }
    } catch (error) {
      console.error('获取分类列表失败:', error);
    }
  };

  // 获取统计信息
  const fetchStats = async () => {
    try {
      const response = await fetch('/api/document/stats');
      const result = await response.json();
      
      if (result.success) {
        setStats(result.data);
      }
    } catch (error) {
      console.error('获取统计信息失败:', error);
    }
  };

  // 上传文档
  const handleUpload = async (values: any) => {
    try {
      const formData = new FormData();
      if (values.file && values.file.length > 0) {
        formData.append('file', values.file[0].originFileObj);
      }
      
      if (values.title) formData.append('title', values.title);
      if (values.description) formData.append('description', values.description);
      if (values.category_id) formData.append('category_id', values.category_id);
      if (values.tags) formData.append('tags', values.tags.join(','));

      const response = await fetch('/api/document/upload', {
        method: 'POST',
        body: formData
      });
      
      const result = await response.json();
      
      if (result.success) {
        message.success('文档上传成功');
        setUploadModalVisible(false);
        form.resetFields();
        fetchDocuments();
        fetchStats();
      } else {
        message.error('上传失败: ' + result.message);
      }
    } catch (error) {
      console.error('上传失败:', error);
      message.error('上传失败');
    }
  };

  // 删除文档
  const handleDelete = async (documentId: string) => {
    Modal.confirm({
      title: '确定要删除这个文档吗？',
      content: '删除后无法恢复',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await fetch(`/api/document/${documentId}`, {
            method: 'DELETE'
          });
          
          const result = await response.json();
          
          if (result.success) {
            message.success('删除成功');
            fetchDocuments();
            fetchStats();
          } else {
            message.error('删除失败: ' + result.message);
          }
        } catch (error) {
          console.error('删除失败:', error);
          message.error('删除失败');
        }
      }
    });
  };

  // 下载文档
  const handleDownload = async (documentId: string, filename: string) => {
    try {
      const response = await fetch(`/api/document/${documentId}/download`);
      
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
      } else {
        message.error('下载失败');
      }
    } catch (error) {
      console.error('下载失败:', error);
      message.error('下载失败');
    }
  };

  // 查看文档详情
  const handleViewDocument = async (documentId: string) => {
    try {
      const response = await fetch(`/api/document/${documentId}`);
      const result = await response.json();
      
      if (result.success) {
        setSelectedDocument(result.data);
        setDrawerVisible(true);
      } else {
        message.error('获取文档详情失败: ' + result.message);
      }
    } catch (error) {
      console.error('获取文档详情失败:', error);
      message.error('获取文档详情失败');
    }
  };

  // 创建分类
  const handleCreateCategory = async (values: any) => {
    try {
      const response = await fetch('/api/document/categories', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(values)
      });
      
      const result = await response.json();
      
      if (result.success) {
        message.success('分类创建成功');
        setCategoryModalVisible(false);
        categoryForm.resetFields();
        fetchCategories();
      } else {
        message.error('创建分类失败: ' + result.message);
      }
    } catch (error) {
      console.error('创建分类失败:', error);
      message.error('创建分类失败');
    }
  };

  // 表格列定义
  const columns: ColumnsType<Document> = [
    {
      title: '文档信息',
      key: 'document',
      render: (_, record) => (
        <div>
          <div style={{ fontWeight: 500, marginBottom: 4 }}>
            {record.title}
          </div>
          <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>
            {record.filename}
          </div>
          {record.category && (
            <Tag color="blue">
              {record.category.name}
            </Tag>
          )}
        </div>
      )
    },
    {
      title: '状态',
      dataIndex: 'parse_status',
      key: 'status',
      render: (status, record) => (
        <div>
          <Badge
            status={getStatusColor(status) as any}
            text={getStatusText(status)}
          />
          {status === 'processing' && (
            <div style={{ marginTop: 8, width: 120 }}>
              <Progress
                percent={record.parse_progress}
                size="small"
                showInfo={false}
              />
            </div>
          )}
        </div>
      )
    },
    {
      title: '文件信息',
      key: 'fileInfo',
      render: (_, record) => (
        <div>
          <div style={{ fontSize: 12, color: '#666' }}>
            {formatFileSize(record.file_size)}
          </div>
          <div style={{ fontSize: 12, color: '#999', marginTop: 2 }}>
            {new Date(record.created_at).toLocaleDateString('zh-CN')}
          </div>
        </div>
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title="查看">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleViewDocument(record.id)}
            />
          </Tooltip>
          <Tooltip title="下载">
            <Button
              type="text"
              icon={<DownloadOutlined />}
              onClick={() => handleDownload(record.id, record.filename)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record.id)}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  // 渲染统计信息
  const renderStatistics = () => {
    if (!stats) return <div>暂无统计数据</div>;

    return (
      <div>
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总文档数"
                value={stats.total_documents}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="已完成"
                value={stats.status_stats.completed}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="处理中"
                value={stats.status_stats.processing}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="失败"
                value={stats.status_stats.failed}
                valueStyle={{ color: '#cf1322' }}
              />
            </Card>
          </Col>
        </Row>

        <Card title="文件类型分布">
          <Row gutter={16}>
            {Object.entries(stats.type_stats).map(([type, count]) => (
              <Col span={8} key={type}>
                <Statistic
                  title={type.toUpperCase()}
                  value={count}
                />
              </Col>
            ))}
          </Row>
        </Card>
      </div>
    );
  };

  useEffect(() => {
    fetchDocuments();
    fetchCategories();
    fetchStats();
  }, []);

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: 'list',
              label: '文档管理',
              children: (
                <>
                  <div style={{ marginBottom: 16 }}>
                    <Space>
                      <Button
                        type="primary"
                        icon={<UploadOutlined />}
                        onClick={() => setUploadModalVisible(true)}
                      >
                        上传文档
                      </Button>
                      <Button
                        icon={<FolderAddOutlined />}
                        onClick={() => setCategoryModalVisible(true)}
                      >
                        创建分类
                      </Button>
                    </Space>
                  </div>

                  <Table
                    columns={columns}
                    dataSource={documents}
                    rowKey="id"
                    loading={loading}
                    pagination={{
                      pageSize: 10,
                      showSizeChanger: true,
                      showQuickJumper: true,
                      showTotal: (total) => `共 ${total} 个文档`
                    }}
                  />
                </>
              )
            },
            {
              key: 'statistics',
              label: '统计分析',
              children: renderStatistics()
            }
          ]}
        />
      </Card>

      {/* 上传文档模态框 */}
      <Modal
        title="上传文档"
        open={uploadModalVisible}
        onCancel={() => {
          setUploadModalVisible(false);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleUpload}
        >
          <Form.Item
            name="file"
            label="选择文件"
            rules={[{ required: true, message: '请选择要上传的文件' }]}
          >
            <Upload.Dragger
              name="file"
              multiple={false}
              beforeUpload={() => false}
              accept=".pdf,.doc,.docx,.txt"
            >
              <p className="ant-upload-drag-icon">
                <UploadOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">
                支持 PDF、Word、文本文件
              </p>
            </Upload.Dragger>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="title"
                label="文档标题"
                rules={[{ required: true, message: '请输入文档标题' }]}
              >
                <Input placeholder="请输入文档标题" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="category_id"
                label="分类"
              >
                <Select placeholder="请选择分类">
                  {categories.map((category) => (
                    <Option key={category.id} value={category.id}>
                      {category.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea
              rows={3}
              placeholder="请输入文档描述"
            />
          </Form.Item>

          <Form.Item
            name="tags"
            label="标签"
          >
            <Select
              mode="tags"
              placeholder="请输入标签"
              tokenSeparators={[',']}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setUploadModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                上传
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 创建分类模态框 */}
      <Modal
        title="创建分类"
        open={categoryModalVisible}
        onCancel={() => {
          setCategoryModalVisible(false);
          categoryForm.resetFields();
        }}
        footer={null}
      >
        <Form
          form={categoryForm}
          layout="vertical"
          onFinish={handleCreateCategory}
        >
          <Form.Item
            name="name"
            label="分类名称"
            rules={[{ required: true, message: '请输入分类名称' }]}
          >
            <Input placeholder="请输入分类名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea
              rows={3}
              placeholder="请输入分类描述"
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setCategoryModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                创建
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 文档详情抽屉 */}
      <Drawer
        title="文档详情"
        placement="right"
        width={600}
        open={drawerVisible}
        onClose={() => {
          setDrawerVisible(false);
          setSelectedDocument(null);
        }}
        extra={
          <Space>
            {selectedDocument && (
              <>
                <Button
                  icon={<DownloadOutlined />}
                  onClick={() => handleDownload(selectedDocument.id, selectedDocument.filename)}
                >
                  下载
                </Button>
                <Button
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => {
                    handleDelete(selectedDocument.id);
                    setDrawerVisible(false);
                  }}
                >
                  删除
                </Button>
              </>
            )}
          </Space>
        }
      >
        {selectedDocument && (
          <div>
            <Tabs
              defaultActiveKey="info"
              items={[
                {
                  key: 'info',
                  label: '基本信息',
                  children: (
                    <div style={{ padding: '16px 0' }}>
                      <Row gutter={[16, 16]}>
                        <Col span={24}>
                          <div style={{ marginBottom: 16 }}>
                            <h3 style={{ margin: 0, marginBottom: 8 }}>{selectedDocument.title}</h3>
                            <p style={{ color: '#666', margin: 0 }}>{selectedDocument.filename}</p>
                          </div>
                        </Col>
                        
                        <Col span={12}>
                          <Statistic title="文件大小" value={formatFileSize(selectedDocument.file_size)} />
                        </Col>
                        <Col span={12}>
                          <Statistic title="文件类型" value={selectedDocument.file_type.toUpperCase()} />
                        </Col>
                        
                        <Col span={12}>
                          <div>
                            <p style={{ margin: '0 0 8px 0', color: '#666' }}>状态</p>
                            <Tag color={getStatusColor(selectedDocument.parse_status)}>
                              {getStatusText(selectedDocument.parse_status)}
                            </Tag>
                          </div>
                        </Col>
                        <Col span={12}>
                          <div>
                            <p style={{ margin: '0 0 8px 0', color: '#666' }}>上传时间</p>
                            <p style={{ margin: 0 }}>{new Date(selectedDocument.created_at).toLocaleString('zh-CN')}</p>
                          </div>
                        </Col>
                        
                        {selectedDocument.parse_status === 'processing' && (
                          <Col span={24}>
                            <div>
                              <p style={{ margin: '0 0 8px 0', color: '#666' }}>解析进度</p>
                              <Progress percent={selectedDocument.parse_progress} />
                            </div>
                          </Col>
                        )}
                        
                        {selectedDocument.category && (
                          <Col span={24}>
                            <div>
                              <p style={{ margin: '0 0 8px 0', color: '#666' }}>分类</p>
                              <Tag>{selectedDocument.category.name}</Tag>
                            </div>
                          </Col>
                        )}
                        
                        {selectedDocument.description && (
                          <Col span={24}>
                            <div>
                              <p style={{ margin: '0 0 8px 0', color: '#666' }}>描述</p>
                              <p style={{ margin: 0 }}>{selectedDocument.description}</p>
                            </div>
                          </Col>
                        )}
                        
                        {selectedDocument.tags && selectedDocument.tags.length > 0 && (
                          <Col span={24}>
                            <div>
                              <p style={{ margin: '0 0 8px 0', color: '#666' }}>标签</p>
                              <Space wrap>
                                {selectedDocument.tags.map((tag, index) => (
                                  <Tag key={index}>{tag}</Tag>
                                ))}
                              </Space>
                            </div>
                          </Col>
                        )}
                      </Row>
                    </div>
                  )
                },
                {
                  key: 'content',
                  label: '文档内容',
                  children: (
                    <div style={{ padding: '16px 0' }}>
                      <p style={{ color: '#666' }}>文档内容预览功能开发中...</p>
                    </div>
                  )
                }
              ]}
            />
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default DocumentManagement;