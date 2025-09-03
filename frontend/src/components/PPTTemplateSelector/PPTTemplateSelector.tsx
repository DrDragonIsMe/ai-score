import React, { useState, useEffect } from 'react';
import {
  Modal,
  Card,
  Row,
  Col,
  Button,
  Upload,
  Form,
  Input,
  Select,
  message,
  Space,
  Tag,
  Typography,
  Divider,
  Spin,
} from 'antd';
import {
  PlusOutlined,
  UploadOutlined,
  FileTextOutlined,
  CheckOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../../stores/authStore';
import { useAIAssistantStore, type PPTTemplate } from '../../stores/aiAssistantStore';
import './PPTTemplateSelector.css';

const { Title, Text } = Typography;
const { Option } = Select;

interface PPTTemplateSelectorProps {
  visible: boolean;
  onClose: () => void;
  onSelect: (templateId: number, templateName: string) => void;
  selectedTemplateId?: number | null;
}

const PPTTemplateSelector: React.FC<PPTTemplateSelectorProps> = ({
  visible,
  onClose,
  onSelect,
  selectedTemplateId,
}) => {
  const { token } = useAuthStore();
  const { pptTemplates, loadPptTemplates, addPptTemplate } = useAIAssistantStore();
  const [loading, setLoading] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [form] = Form.useForm();

  // 加载PPT模板列表
  const loadTemplates = async () => {
    setLoading(true);
    try {
      await loadPptTemplates();
    } catch (error) {
      console.error('加载模板失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (visible) {
      loadTemplates();
    }
  }, [visible]);

  // 处理模板选择
  const handleTemplateSelect = (template: PPTTemplate) => {
    onSelect(template.id, template.name);
    message.success(`已选择模板：${template.name}`);
    onClose();
  };

  // 处理模板上传
  const handleUpload = async (values: any) => {
    const { name, category, description, file } = values;
    
    if (!file || file.length === 0) {
      message.error('请选择要上传的文件');
      return;
    }

    setUploadLoading(true);
    try {
      const formData = new FormData();
      formData.append('name', name);
      formData.append('category', category);
      formData.append('description', description || '');
      formData.append('file', file[0].originFileObj);

      const response = await fetch('http://localhost:5001/api/ppt-templates/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      const result = await response.json();
      if (result.success) {
        message.success('模板上传成功');
        // 将新模板添加到store中
        const newTemplate: PPTTemplate = {
          id: result.data.id,
          name: result.data.name,
          category: result.data.category,
          description: result.data.description
        };
        addPptTemplate(newTemplate);
        setShowUploadModal(false);
        form.resetFields();
      } else {
        message.error(result.message || '上传失败');
      }
    } catch (error) {
      console.error('上传失败:', error);
      message.error('上传失败，请重试');
    } finally {
      setUploadLoading(false);
    }
  };

  // 文件上传前的验证
  const beforeUpload = (file: File) => {
    const isValidType = file.type === 'application/vnd.openxmlformats-officedocument.presentationml.presentation' || 
                       file.type === 'application/vnd.ms-powerpoint';
    if (!isValidType) {
      message.error('只支持 .ppt 和 .pptx 格式的文件');
      return false;
    }
    
    const isLt10M = file.size / 1024 / 1024 < 10;
    if (!isLt10M) {
      message.error('文件大小不能超过 10MB');
      return false;
    }
    
    return false; // 阻止自动上传
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case '学术类': return 'blue';
      case '商务类': return 'green';
      case '教育类': return 'orange';
      default: return 'default';
    }
  };

  return (
    <>
      <Modal
        title="选择PPT模板"
        open={visible}
        onCancel={onClose}
        footer={null}
        width={800}
        className="ppt-template-selector"
        style={{ top: 20 }}
        zIndex={2000} // 确保在全屏模式下也能正确显示
      >
        <div className="template-selector-content">
          <div className="template-header">
            <Space>
              <Title level={4} style={{ margin: 0 }}>选择模板</Title>
              <Button 
                type="primary" 
                icon={<PlusOutlined />} 
                onClick={() => setShowUploadModal(true)}
              >
                上传新模板
              </Button>
            </Space>
            <Text type="secondary">选择一个PPT模板来生成您的演示文稿</Text>
          </div>

          <Divider />

          <Spin spinning={loading}>
            <Row gutter={[16, 16]}>
              {pptTemplates.map((template: PPTTemplate) => (
                <Col xs={24} sm={12} md={8} key={template.id}>
                  <Card
                    hoverable
                    className={`template-card ${
                      selectedTemplateId === template.id ? 'selected' : ''
                    }`}
                    onClick={() => handleTemplateSelect(template)}
                    cover={
                      <div className="template-preview">
                        <FileTextOutlined style={{ fontSize: 48, color: '#1890ff' }} />
                        {selectedTemplateId === template.id && (
                          <div className="selected-overlay">
                            <CheckOutlined style={{ fontSize: 24, color: 'white' }} />
                          </div>
                        )}
                      </div>
                    }
                  >
                    <Card.Meta
                      title={
                        <Space>
                          <span>{template.name}</span>
                          <Tag color={getCategoryColor(template.category)}>
                            {template.category}
                          </Tag>
                        </Space>
                      }
                      description={template.description}
                    />
                  </Card>
                </Col>
              ))}
            </Row>
          </Spin>
        </div>
      </Modal>

      {/* 上传模板模态框 */}
      <Modal
        title="上传PPT模板"
        open={showUploadModal}
        onCancel={() => {
          setShowUploadModal(false);
          form.resetFields();
        }}
        footer={null}
        width={600}
        zIndex={2100} // 确保在模板选择器之上
      >
        <Form
          form={form}
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
            <Select placeholder="请选择模板分类">
              <Option value="学术类">学术类</Option>
              <Option value="商务类">商务类</Option>
              <Option value="教育类">教育类</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="模板描述"
          >
            <Input.TextArea 
              rows={3} 
              placeholder="请输入模板描述（可选）" 
            />
          </Form.Item>

          <Form.Item
            name="file"
            label="模板文件"
            rules={[{ required: true, message: '请选择模板文件' }]}
            valuePropName="fileList"
            getValueFromEvent={(e) => {
              if (Array.isArray(e)) {
                return e;
              }
              return e && e.fileList;
            }}
          >
            <Upload
              beforeUpload={beforeUpload}
              maxCount={1}
              accept=".ppt,.pptx"
              listType="text"
            >
              <Button icon={<UploadOutlined />}>选择PPT文件</Button>
            </Upload>
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setShowUploadModal(false)}>
                取消
              </Button>
              <Button 
                type="primary" 
                htmlType="submit" 
                loading={uploadLoading}
              >
                上传模板
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default PPTTemplateSelector;