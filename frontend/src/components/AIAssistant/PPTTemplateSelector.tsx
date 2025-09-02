import React, { useState, useEffect } from 'react';
import {
  Modal,
  Card,
  Row,
  Col,
  Button,
  message,
  Spin,
  Typography,
  Tag,
  Empty
} from 'antd';
import {
  FileTextOutlined,
  EyeOutlined,
  DownloadOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;

interface PPTTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  file_path: string;
  preview_image?: string;
  created_at: string;
  is_active: boolean;
}

interface PPTTemplateSelectorProps {
  visible: boolean;
  onClose: () => void;
  onSelect: (templateId: string, templateName: string) => void;
}

const PPTTemplateSelector: React.FC<PPTTemplateSelectorProps> = ({
  visible,
  onClose,
  onSelect
}) => {
  const [templates, setTemplates] = useState<PPTTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);

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

  useEffect(() => {
    if (visible) {
      fetchTemplates();
    }
  }, [visible]);

  // 处理模板选择
  const handleSelectTemplate = () => {
    if (!selectedTemplate) {
      message.warning('请选择一个模板');
      return;
    }

    const template = templates.find(t => t.id === selectedTemplate);
    if (template) {
      onSelect(selectedTemplate, template.name);
      onClose();
    }
  };

  // 预览模板
  const handlePreviewTemplate = (templateId: string) => {
    // 这里可以实现模板预览功能
    message.info('模板预览功能开发中...');
  };

  // 按类别分组模板
  const groupedTemplates = templates.reduce((groups, template) => {
    const category = template.category || '其他';
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push(template);
    return groups;
  }, {} as Record<string, PPTTemplate[]>);

  return (
    <Modal
      title="选择PPT模板"
      open={visible}
      onCancel={onClose}
      width={800}
      footer={[
        <Button key="cancel" onClick={onClose}>
          取消
        </Button>,
        <Button
          key="select"
          type="primary"
          onClick={handleSelectTemplate}
          disabled={!selectedTemplate}
        >
          选择模板
        </Button>
      ]}
    >
      <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <Spin size="large" />
            <div style={{ marginTop: '16px' }}>加载模板中...</div>
          </div>
        ) : templates.length === 0 ? (
          <Empty
            description="暂无可用模板"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <div>
            {Object.entries(groupedTemplates).map(([category, categoryTemplates]) => (
              <div key={category} style={{ marginBottom: '24px' }}>
                <Title level={4} style={{ marginBottom: '16px' }}>
                  {category}
                </Title>
                <Row gutter={[16, 16]}>
                  {categoryTemplates.map((template) => (
                    <Col key={template.id} xs={24} sm={12} md={8}>
                      <Card
                        hoverable
                        className={`template-card ${
                          selectedTemplate === template.id ? 'selected' : ''
                        }`}
                        onClick={() => setSelectedTemplate(template.id)}
                        actions={[
                          <Button
                            key="preview"
                            type="text"
                            icon={<EyeOutlined />}
                            onClick={(e) => {
                              e.stopPropagation();
                              handlePreviewTemplate(template.id);
                            }}
                          >
                            预览
                          </Button>
                        ]}
                        style={{
                          border: selectedTemplate === template.id ? '2px solid #1890ff' : '1px solid #d9d9d9'
                        }}
                      >
                        <div style={{ textAlign: 'center', marginBottom: '12px' }}>
                          {template.preview_image ? (
                            <img
                              src={template.preview_image}
                              alt={template.name}
                              style={{
                                width: '100%',
                                height: '120px',
                                objectFit: 'cover',
                                borderRadius: '4px'
                              }}
                            />
                          ) : (
                            <div
                              style={{
                                width: '100%',
                                height: '120px',
                                backgroundColor: '#f5f5f5',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                borderRadius: '4px'
                              }}
                            >
                              <FileTextOutlined style={{ fontSize: '48px', color: '#d9d9d9' }} />
                            </div>
                          )}
                        </div>
                        <Card.Meta
                          title={
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              <span>{template.name}</span>
                              {template.is_active && (
                                <Tag color="green">活跃</Tag>
                              )}
                            </div>
                          }
                          description={
                            <div>
                              <Text type="secondary" style={{ fontSize: '12px' }}>
                                {template.description || '暂无描述'}
                              </Text>
                            </div>
                          }
                        />
                      </Card>
                    </Col>
                  ))}
                </Row>
              </div>
            ))}
          </div>
        )}
      </div>
      
      <style>{`
        .template-card.selected {
          box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
        }
      `}</style>
    </Modal>
  );
};

export default PPTTemplateSelector;