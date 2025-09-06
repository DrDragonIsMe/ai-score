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

import { getSubjects } from '../../api/subjects';
import knowledgeGraphApi, { generateKnowledgeGraph, updateKnowledgeGraph } from '../../api/knowledgeGraph';
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
  suggestedSubjectId?: string; // 建议的学科ID
  editMode?: boolean; // 是否为编辑模式
  editData?: {
    id: string;
    title: string;
    subject_id: string;
    subject_name?: string;
    content: string;
    description?: string;
    tags: string[];
  }; // 编辑时的初始数据
}

const KnowledgeGraphEditor: React.FC<KnowledgeGraphEditorProps> = ({
  visible,
  onClose,
  onSuccess,
  initialContent = '',
  suggestedSubjectId,
  editMode = false,
  editData
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

  // 学科数据加载完成后处理编辑模式预填和智能推荐
  useEffect(() => {
    if (visible && subjects.length > 0) {
      // 编辑模式：预填所有数据
      if (editMode && editData) {
        // 使用setTimeout确保状态更新的顺序
        setTimeout(() => {
          setSelectedSubject(editData.subject_id);
          // 确保标签包含当前学科
          const currentSubject = subjects.find(s => s.id === editData.subject_id);
          let initialTags = editData.tags || [];
          if (currentSubject && !initialTags.includes(currentSubject.name)) {
            initialTags = [...initialTags, currentSubject.name];
          }
          setTags(initialTags);
          form.setFieldsValue({
            title: editData.title,
            subject_id: editData.subject_id,
            content: editData.content || editData.description,
            description: editData.description
          });
        }, 50);
      }
      // 创建模式：智能推荐学科和预填写内容
      else {
        if (initialContent) {
          // 预填写内容
          form.setFieldsValue({ content: initialContent });
          // 根据内容智能推荐学科和生成标题
          analyzeContentForSubject(initialContent);
        } else if (suggestedSubjectId) {
          setSelectedSubject(suggestedSubjectId);
          form.setFieldsValue({ subject_id: suggestedSubjectId });
        }
      }
    }
  }, [visible, subjects, suggestedSubjectId, initialContent, editMode, editData]);

  // 当模态框关闭时重置状态
  useEffect(() => {
    if (!visible) {
      // 延迟重置状态，确保模态框完全关闭后再重置
      const timer = setTimeout(() => {
        form.resetFields();
        setTags([]);
        setSelectedSubject('');
      }, 200);
      
      return () => clearTimeout(timer);
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

  // 分析内容并推荐学科和标题
  const analyzeContentForSubject = (content: string) => {
    if (!content || subjects.length === 0) return;
    
    const keywords = {
      '数学': ['数学', '函数', '方程', '几何', '代数', '微积分', '统计', '概率', '三角', '向量'],
      '语文': ['语文', '文学', '诗歌', '散文', '小说', '古诗', '作文', '阅读', '语法', '修辞'],
      '英语': ['英语', 'English', '语法', '词汇', '阅读', '写作', '听力', '口语', '翻译'],
      '物理': ['物理', '力学', '电学', '光学', '热学', '声学', '磁场', '电场', '波动', '量子'],
      '化学': ['化学', '元素', '分子', '原子', '反应', '有机', '无机', '酸碱', '氧化', '还原'],
      '生物': ['生物', '细胞', '基因', '蛋白质', '遗传', '进化', '生态', '植物', '动物', 'DNA'],
      '历史': ['历史', '朝代', '战争', '文明', '古代', '近代', '现代', '革命', '政治', '文化'],
      '地理': ['地理', '地球', '气候', '地形', '河流', '山脉', '国家', '城市', '经纬度', '板块']
    };
    
    let maxScore = 0;
    let suggestedSubject = '';
    
    Object.entries(keywords).forEach(([subjectName, subjectKeywords]) => {
      const score = subjectKeywords.reduce((acc, keyword) => {
        return acc + (content.toLowerCase().includes(keyword.toLowerCase()) ? 1 : 0);
      }, 0);
      
      if (score > maxScore) {
        maxScore = score;
        suggestedSubject = subjectName;
      }
    });
    
    // 推荐学科
    if (maxScore > 0) {
       const subject = subjects.find(s => s.name.includes(suggestedSubject));
       if (subject) {
         setSelectedSubject(subject.id);
         form.setFieldsValue({ subject_id: subject.id });
         message.success(`已为您推荐学科：${subject.name}`);
       }
     }
     
     // 自动生成标题
     generateTitleFromContent(content, suggestedSubject);
   };
   
   // 根据内容自动生成标题
   const generateTitleFromContent = (content: string, subject: string) => {
     if (!content) return;
     
     // 提取内容的前50个字符作为基础
     let title = content.substring(0, 50).trim();
     
     // 移除换行符和多余空格
     title = title.replace(/\n/g, ' ').replace(/\s+/g, ' ');
     
     // 如果内容以问题开头，保留问题格式
     if (title.includes('？') || title.includes('?')) {
       const questionEnd = Math.max(title.indexOf('？'), title.indexOf('?'));
       if (questionEnd > 0) {
         title = title.substring(0, questionEnd + 1);
       }
     }
     // 如果内容包含关键概念，提取概念
     else {
       const concepts = ['定义', '概念', '原理', '定理', '公式', '方法', '技巧', '知识点'];
       for (const concept of concepts) {
         if (title.includes(concept)) {
           // 尝试提取概念前后的关键词
           const index = title.indexOf(concept);
           const before = title.substring(Math.max(0, index - 10), index).trim();
           const after = title.substring(index, Math.min(title.length, index + 15)).trim();
           title = (before + after).trim();
           break;
         }
       }
     }
     
     // 添加学科前缀
     if (subject && !title.includes(subject)) {
       title = `${subject} - ${title}`;
     }
     
     // 确保标题不超过30个字符
     if (title.length > 30) {
       title = title.substring(0, 27) + '...';
     }
     
     // 设置到表单中
     form.setFieldsValue({ title });
   };

  const handleSubmit = async (forceOverwrite: boolean = false) => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      const requestData = {
        subject_id: selectedSubject,
        content: values.content,
        tags: tags,
        title: values.title || (editMode ? editData?.title : '知识图谱内容'),
        force_overwrite: forceOverwrite
      };

      let response;
      if (editMode && editData) {
        try {
          // 编辑模式：调用更新API
          response = await updateKnowledgeGraph(editData.id, requestData);
        } catch (updateError) {
          console.error('更新知识图谱失败，尝试使用节点更新API:', updateError);
          // 尝试使用节点更新API
          response = await knowledgeGraphApi.updateKnowledgeGraph(editData.id, requestData);
        }
      } else {
        // 创建模式：调用生成API
        response = await generateKnowledgeGraph(requestData);
      }

      // 显示成功提示
      if (editMode) {
        message.success('知识图谱更新成功！');
      } else {
        message.success('知识图谱创建成功！');
      }
      
      onSuccess?.({
        ...response,
        tags: tags,
        content: values.content
      });
      handleClose();
    } catch (error: any) {
      console.error('提交失败:', error);
      
      // 检查是否是重复标题错误
      if (error.response?.status === 409 && error.response?.data?.duplicate_found) {
        const duplicateData = error.response.data;
        
        Modal.confirm({
          title: '发现同名知识图谱',
          content: (
            <div>
              <p>已存在名为 "{duplicateData.existing_graph.name}" 的知识图谱</p>
              <p>创建时间: {new Date(duplicateData.existing_graph.created_at).toLocaleString()}</p>
              <p>请选择操作:</p>
            </div>
          ),
          okText: '覆盖现有图谱',
          cancelText: '使用新名称',
          onOk: () => {
            // 覆盖现有图谱
            handleSubmit(true);
          },
          onCancel: () => {
            // 使用建议的新名称
            form.setFieldsValue({
              title: duplicateData.suggested_name
            });
            message.info('已为您生成新的标题，请确认后重新提交');
          }
        });
      } else {
        message.error('提交失败，请重试');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitClick = () => {
    handleSubmit(false);
  };

  const handleClose = () => {
    onClose();
  };

  const handleSubjectChange = (value: string) => {
    const oldSubject = subjects.find(s => s.id === selectedSubject);
    const newSubject = subjects.find(s => s.id === value);
    
    setSelectedSubject(value);
    
    if (newSubject) {
      let updatedTags = [...tags];
      
      // 如果之前有选择学科，移除旧的学科标签
      if (oldSubject && oldSubject.name !== newSubject.name) {
        updatedTags = updatedTags.filter(tag => tag !== oldSubject.name);
      }
      
      // 添加新的学科标签
      if (!updatedTags.includes(newSubject.name)) {
        updatedTags.push(newSubject.name);
      }
      
      setTags(updatedTags);
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
          <span>{editMode ? '编辑知识图谱' : '添加到知识图谱'}</span>
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
          onClick={handleSubmitClick}
          disabled={!selectedSubject}
        >
          <SaveOutlined /> {editMode ? '保存修改' : '生成知识图谱'}
        </Button>
      ]}
      className="knowledge-graph-editor"
    >
      <div className="editor-content">
        <Alert
          message="💡 智能提示"
          description="系统已为您智能推荐学科，您可以添加标签来更好地分类和检索内容。"
          type="info"
          showIcon
          style={{ 
            marginBottom: 20, 
            borderRadius: 8,
            border: '1px solid #e1f5fe',
            backgroundColor: '#f0f9ff'
          }}
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
              size="large"
              style={{ borderRadius: 8 }}
              disabled={false}
            >
              {subjects.map(subject => (
                <Option key={subject.id} value={subject.id}>
                  <Space>
                    <BookOutlined style={{ color: '#64748b' }} />
                    <span>{subject.name}</span>
                    {subject.description && (
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {subject.description}
                      </Text>
                    )}
                  </Space>
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label="标题"
            name="title"
          >
            <Input 
              placeholder="请输入标题（可选）" 
              size="large"
              style={{ borderRadius: 8 }}
            />
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
              style={{ borderRadius: 8, resize: 'none' }}
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
              style={{ borderRadius: 8, resize: 'none' }}
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
            <Select
              mode="tags"
              value={tags}
              onChange={handleTagsChange}
              placeholder="输入标签"
              size="large"
              style={{ width: '100%', borderRadius: 8 }}
            />
            <Text type="secondary" style={{ fontSize: '12px', marginTop: 4, display: 'block' }}>
              标签用于分类和检索，建议添加相关的知识点、章节或主题标签
            </Text>
          </Form.Item>
        </Form>

        {selectedSubject && (
          <Card 
            size="small" 
            style={{ 
              marginTop: 20, 
              borderRadius: 12,
              border: '1px solid #e2e8f0',
              backgroundColor: '#f8fafc'
            }}
          >
            <Title level={5} style={{ margin: 0, marginBottom: 12, color: '#475569' }}>
              📋 预览信息
            </Title>
            <Space direction="vertical" size={8} style={{ width: '100%' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <BookOutlined style={{ color: '#3b82f6' }} />
                <Text style={{ color: '#64748b' }}>学科：</Text>
                <Text strong style={{ color: '#1e293b' }}>
                  {subjects.find(s => s.id === selectedSubject)?.name}
                </Text>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <TagsOutlined style={{ color: '#10b981' }} />
                <Text style={{ color: '#64748b' }}>标签：</Text>
                <Text strong style={{ color: '#1e293b' }}>
                  {tags.length} 个
                </Text>
              </div>
              {tags.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <Space size={6} wrap>
                    {tags.map(tag => (
                      <span 
                        key={tag} 
                        style={{
                          padding: '2px 8px',
                          backgroundColor: '#e0f2fe',
                          color: '#0369a1',
                          borderRadius: 12,
                          fontSize: '12px',
                          border: '1px solid #bae6fd'
                        }}
                      >
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