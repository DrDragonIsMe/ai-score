import React, { useState, useEffect } from 'react';
import {
  Modal,
  Form,
  Select,
  Input,
  Button,
  Space,
  Typography,
  Card,
  Divider,
  message,
  Spin,
  Alert
} from 'antd';
import {
  NodeIndexOutlined,
  BookOutlined,
  TagsOutlined,
  SaveOutlined,
  CloseOutlined
} from '@ant-design/icons';
import TagInput from '../TagInput/TagInput';
import { getSubjects } from '../../api/subjects';
import { generateKnowledgeGraph } from '../../api/knowledgeGraph';
import './KnowledgeGraphEditor.css';

const { TextArea } = Input;
const { Title, Text } = Typography;
const { Option } = Select;

interface Subject {
  id: string;
  name: string;
  description?: string;
}

interface KnowledgeGraphEditorProps {
  visible: boolean;
  onClose: () => void;
  onSuccess?: (data: any) => void;
  initialContent?: string;
}

const KnowledgeGraphEditor: React.FC<KnowledgeGraphEditorProps> = ({
  visible,
  onClose,
  onSuccess,
  initialContent = ''
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [subjectsLoading, setSubjectsLoading] = useState(false);
  const [tags, setTags] = useState<string[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<string>('');

  // 获取学科列表
  useEffect(() => {
    if (visible) {
      fetchSubjects();
    }
  }, [visible]);

  const fetchSubjects = async () => {
    setSubjectsLoading(true);
    try {
      const subjects = await getSubjects();
      setSubjects(subjects);
    } catch (error) {
      console.error('获取学科列表失败:', error);
      message.error('获取学科列表失败');
    } finally {
      setSubjectsLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      const requestData = {
        subject_id: selectedSubject,
        content: values.content,
        tags: tags,
        title: values.title || '知识图谱内容',
        description: values.description || ''
      };

      // 调用知识图谱生成API
      const response = await generateKnowledgeGraph({
        subject_id: selectedSubject,
        content: values.content,
        tags
      });

      message.success('知识图谱生成成功！');
      onSuccess?.({
        ...response,
        tags: tags,
        content: values.content
      });
      handleClose();
    } catch (error) {
      console.error('提交失败:', error);
      message.error('提交失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    form.resetFields();
    setTags([]);
    setSelectedSubject('');
    onClose();
  };

  const handleSubjectChange = (value: string) => {
    setSelectedSubject(value);
    const subject = subjects.find(s => s.id === value);
    if (subject) {
      // 自动添加学科名称作为标签
      if (!tags.includes(subject.name)) {
        setTags([...tags, subject.name]);
      }
    }
  };

  const handleTagsChange = (newTags: string[]) => {
    setTags(newTags);
  };

  return (
    <Modal
      title={
        <Space>
          <NodeIndexOutlined style={{ color: 'var(--primary-color)' }} />
          <span>添加到知识图谱</span>
        </Space>
      }
      open={visible}
      onCancel={handleClose}
      width={600}
      footer={[
        <Button key="cancel" onClick={handleClose}>
          <CloseOutlined /> 取消
        </Button>,
        <Button
          key="submit"
          type="primary"
          loading={loading}
          onClick={handleSubmit}
          disabled={!selectedSubject}
        >
          <SaveOutlined /> 生成知识图谱
        </Button>
      ]}
      className="knowledge-graph-editor"
    >
      <div className="editor-content">
        <Alert
          message="知识图谱功能说明"
          description="选择学科后，系统将基于您的内容生成相应的知识图谱，并支持通过标签进行分类和检索。"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Form
          form={form}
          layout="vertical"
          initialValues={{
            content: initialContent
          }}
        >
          <Form.Item
            label={
              <Space>
                <BookOutlined />
                <span>选择学科</span>
              </Space>
            }
            name="subject_id"
            rules={[{ required: true, message: '请选择学科' }]}
          >
            <Select
              placeholder="请选择学科"
              loading={subjectsLoading}
              onChange={handleSubjectChange}
              value={selectedSubject}
            >
              {subjects.map(subject => (
                <Option key={subject.id} value={subject.id}>
                  {subject.name}
                  {subject.description && (
                    <Text type="secondary" style={{ marginLeft: 8, fontSize: '12px' }}>
                      {subject.description}
                    </Text>
                  )}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label="标题"
            name="title"
          >
            <Input placeholder="请输入标题（可选）" />
          </Form.Item>

          <Form.Item
            label="内容"
            name="content"
            rules={[{ required: true, message: '请输入内容' }]}
          >
            <TextArea
              rows={6}
              placeholder="请输入要添加到知识图谱的内容..."
              showCount
              maxLength={2000}
            />
          </Form.Item>

          <Form.Item
            label="描述"
            name="description"
          >
            <TextArea
              rows={2}
              placeholder="请输入描述信息（可选）"
              showCount
              maxLength={500}
            />
          </Form.Item>

          <Form.Item
            label={
              <Space>
                <TagsOutlined />
                <span>标签</span>
              </Space>
            }
          >
            <TagInput
              value={tags}
              onChange={handleTagsChange}
              placeholder="输入标签，用分号(;)分隔"
              maxTags={10}
            />
            <Text type="secondary" style={{ fontSize: '12px', marginTop: 4, display: 'block' }}>
              标签用于分类和检索，建议添加相关的知识点、章节或主题标签
            </Text>
          </Form.Item>
        </Form>

        {selectedSubject && (
          <Card size="small" style={{ marginTop: 16 }}>
            <Title level={5} style={{ margin: 0, marginBottom: 8 }}>
              预览信息
            </Title>
            <Space direction="vertical" size={4} style={{ width: '100%' }}>
              <Text>
                <strong>学科：</strong>
                {subjects.find(s => s.id === selectedSubject)?.name}
              </Text>
              <Text>
                <strong>标签数量：</strong>
                {tags.length} 个
              </Text>
              {tags.length > 0 && (
                <div>
                  <strong>标签：</strong>
                  <Space size={4} wrap style={{ marginTop: 4 }}>
                    {tags.map(tag => (
                      <span key={tag} className="preview-tag">
                        {tag}
                      </span>
                    ))}
                  </Space>
                </div>
              )}
            </Space>
          </Card>
        )}
      </div>
    </Modal>
  );
};

export default KnowledgeGraphEditor;