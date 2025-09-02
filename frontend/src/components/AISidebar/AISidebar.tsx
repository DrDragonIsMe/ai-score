import React, { useState, useRef, useEffect } from 'react';
import {
  Card,
  Avatar,
  Typography,
  Input,
  Button,
  Space,
  Divider,
  Badge,
  Tooltip,
  Progress,
  Tag,
  List,
  Spin,
  Upload,
  message,
  Modal,
  Select,
  Form,
} from 'antd';
import {
  RobotOutlined,
  SendOutlined,
  CameraOutlined,
  FileTextOutlined,
  BulbOutlined,
  ThunderboltOutlined,
  HeartOutlined,
  StarOutlined,
  MessageOutlined,
  SettingOutlined,
  MinusOutlined,
  PlusOutlined,
  ExpandOutlined,
  FullscreenOutlined,
  CloseOutlined,
  MenuOutlined,
  PaperClipOutlined,
  UserOutlined,
  FileAddOutlined,
  DownloadOutlined,
  UploadOutlined,
  CloudUploadOutlined,
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import rehypeRaw from 'rehype-raw';
import { useAuthStore } from '../../stores/authStore';
import './AISidebar.css';

const { Text, Title } = Typography;
const { TextArea } = Input;

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface PPTTemplate {
  id: number;
  name: string;
  category: string;
  preview?: string;
  description: string;
}

interface AISidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  displayMode?: 'hidden' | 'sidebar' | 'drawer' | 'fullscreen';
  onModeChange?: (mode: 'hidden' | 'sidebar' | 'drawer' | 'fullscreen') => void;
}

const AISidebar: React.FC<AISidebarProps> = ({ 
  collapsed, 
  onToggleCollapse, 
  displayMode = 'sidebar',
  onModeChange 
}) => {
  const { token } = useAuthStore();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: '你好！我是**高小分**，你的AI学习助手。\n\n我可以帮助你：\n- 📚 **学习诊断**：分析你的学习情况\n- 🎯 **个性化推荐**：制定专属学习计划\n- 📝 **作业辅导**：解答学习中的疑问\n- 📊 **进度跟踪**：实时监控学习效果\n\n有什么可以帮助你的吗？',
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [aiStatus, setAiStatus] = useState<'online' | 'thinking' | 'offline'>('online');
  const [uploading, setUploading] = useState(false);
  const [showMoreActions, setShowMoreActions] = useState(false);
  const [actionUsageStats, setActionUsageStats] = useState<Record<string, number>>({});
  const [showPPTTemplateModal, setShowPPTTemplateModal] = useState(false);
  const [pptTemplates, setPptTemplates] = useState<PPTTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<PPTTemplate | null>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadForm, setUploadForm] = useState({ name: '', category: '', file: null as File | null });
  const [uploadLoading, setUploadLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 初始化使用统计数据
  useEffect(() => {
    const savedStats = localStorage.getItem('ai_action_usage_stats');
    if (savedStats) {
      try {
        setActionUsageStats(JSON.parse(savedStats));
      } catch (error) {
        console.error('Failed to load usage stats:', error);
      }
    }
  }, []);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputValue;
    setInputValue('');
    setLoading(true);
    setAiStatus('thinking');

    try {
      // 调用AI助理API
      const response = await fetch('http://localhost:5001/api/ai-assistant/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: currentInput,
          conversation_id: 'ai-sidebar',
          context: messages.slice(-3).map(msg => ({
            type: msg.type,
            content: msg.content,
            timestamp: msg.timestamp.toISOString()
          }))
        })
      });

      const result = await response.json();

      if (result.success) {
        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: result.data.response || result.response,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, aiResponse]);
      } else {
        throw new Error(result.message || '发送失败');
      }
    } catch (error) {
      console.error('发送消息失败:', error);
      
      // 添加错误提示消息
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: '抱歉，我现在遇到了一些问题，请稍后再试。如果问题持续存在，请联系技术支持。',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      setAiStatus('online');
    }
  };

  // 处理图片上传
  const handleImageUpload = async (file: File) => {
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('image', file);

      const response = await fetch('http://localhost:5001/api/ai-assistant/recognize-image', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();

      if (result.success) {
        // 添加用户消息（显示上传的图片）
        const userMessage: Message = {
          id: Date.now().toString(),
          type: 'user',
          content: `[已上传图片: ${file.name}]`,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, userMessage]);

        // 添加AI响应
        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: result.data.analysis || result.analysis,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, aiResponse]);
      } else {
        message.error(result.message || '图片识别失败');
      }
    } catch (error) {
      console.error('图片上传失败:', error);
      message.error('图片上传失败，请重试');
    } finally {
      setUploading(false);
    }
  };

  // 处理PDF文档上传
  const handleDocumentUpload = async (file: File) => {
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', file.name);

      const response = await fetch('http://localhost:5001/api/document/upload', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();

      if (result.success) {
        // 添加用户消息
        const userMessage: Message = {
          id: Date.now().toString(),
          type: 'user',
          content: `[已上传文档: ${file.name}]`,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, userMessage]);

        // 添加AI响应
        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: `文档"${file.name}"已成功上传！我已经分析了文档内容，现在你可以向我提问关于这个文档的任何问题。`,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, aiResponse]);
        message.success('文档上传成功！');
      } else {
        message.error(result.message || '文档上传失败');
      }
    } catch (error) {
      console.error('文档上传失败:', error);
      message.error('文档上传失败，请重试');
    } finally {
      setUploading(false);
    }
  };

  // 处理文件选择
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const isImage = file.type.startsWith('image/');
    const isPDF = file.type === 'application/pdf';

    if (isImage) {
      handleImageUpload(file);
    } else if (isPDF) {
      handleDocumentUpload(file);
    } else {
      message.error('只支持图片文件和PDF文档');
    }

    // 清空input值，允许重复选择同一文件
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // 处理PPT模板选择
  const handlePPTTemplateSelection = () => {
    setShowPPTTemplateModal(true);
    // 这里可以加载PPT模板数据
    const templates = [
      { id: 1, name: '学术报告模板', category: '学术类', preview: '/templates/academic.png', description: '适用于学术演讲和研究报告' },
      { id: 2, name: '课程展示模板', category: '教育类', preview: '/templates/course.png', description: '适用于课程内容展示' },
      { id: 3, name: '项目汇报模板', category: '商务类', preview: '/templates/project.png', description: '适用于项目进展汇报' }
    ];
    setPptTemplates(templates);
  };

  // 处理模板上传
  const handleUploadTemplate = async () => {
    if (!uploadForm.name || !uploadForm.category || !uploadForm.file) {
      message.error('请填写完整的模板信息');
      return;
    }

    setUploadLoading(true);
    try {
      const formData = new FormData();
      formData.append('name', uploadForm.name);
      formData.append('category', uploadForm.category);
      formData.append('file', uploadForm.file);

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
        setShowUploadModal(false);
        setUploadForm({ name: '', category: '', file: null });
        // 重新加载模板列表
        handlePPTTemplateSelection();
      } else {
        message.error(result.message || '上传失败');
      }
    } catch (error) {
      console.error('Upload error:', error);
      message.error('上传失败，请重试');
    } finally {
      setUploadLoading(false);
    }
  };

  // 处理文件选择
  const handleFileChange = (file: File) => {
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
    
    setUploadForm(prev => ({ ...prev, file }));
    return false; // 阻止自动上传
  };

  // 处理快捷操作点击
  const handleQuickAction = async (actionKey: string) => {
    if (loading) return;

    let prompt = '';
    let actionName = '';
    let userDisplayMessage = '';

    switch (actionKey) {
      case 'explain':
        prompt = `作为一名专业的AI学习助手，请为学生解释一个重要的学习概念。请选择一个适合当前学习阶段的核心概念，用以下方式进行详细解释：

1. **概念定义**：用简洁明了的语言定义这个概念
2. **核心要点**：列出3-5个关键要点
3. **实际例子**：提供2-3个生动的实例说明
4. **应用场景**：说明这个概念在实际学习或生活中的应用
5. **学习建议**：给出掌握这个概念的学习方法和技巧

请确保解释通俗易懂，适合学生理解。`;
        actionName = '解释概念';
        userDisplayMessage = '💡 请为我解释一个重要的学习概念';
        break;
      case 'practice':
        prompt = `作为AI学习助手，请为学生生成个性化的练习题目。请按以下要求生成：

1. **题目类型**：包含选择题、填空题、简答题等多种形式
2. **难度层次**：从基础到进阶，循序渐进
3. **知识覆盖**：涵盖重要知识点
4. **详细解答**：每道题都要提供完整的解题过程和思路分析
5. **学习提示**：针对易错点给出特别提醒

请生成3-5道高质量的练习题，确保题目有针对性和实用性。`;
        actionName = '练习题目';
        userDisplayMessage = '📝 请为我生成一些练习题目';
        break;
      case 'summary':
        prompt = `作为AI学习助手，请帮助学生总结一个重要的知识点。请按以下结构进行总结：

1. **知识点概述**：简要介绍这个知识点的重要性
2. **核心内容**：详细列出主要知识要点
3. **重难点分析**：标出学习中的重点和难点
4. **知识关联**：说明与其他知识点的联系
5. **记忆技巧**：提供有效的记忆方法
6. **复习建议**：给出针对性的复习策略

请选择一个具有代表性的知识点进行全面总结。`;
        actionName = '知识总结';
        userDisplayMessage = '📚 请帮我总结一个重要的知识点';
        break;
      case 'plan':
        prompt = `作为专业的AI学习规划师，请为学生制定一个科学合理的学习计划。请包含以下要素：

1. **学习目标设定**：短期目标（1周）、中期目标（1月）、长期目标（1学期）
2. **时间安排**：每日学习时间分配和学习节奏
3. **学习内容规划**：按优先级安排学习内容
4. **复习策略**：制定系统的复习计划
5. **进度监控**：设置学习里程碑和检查点
6. **调整机制**：根据学习效果调整计划的方法
7. **激励措施**：保持学习动力的方法

请制定一个个性化、可执行的学习计划。`;
        actionName = '学习计划';
        userDisplayMessage = '📅 请帮我制定一个学习计划';
        break;
      case 'analyze':
        prompt = `作为AI学习诊断专家，请深入分析学生在学习过程中的常见错误和问题。请按以下框架进行分析：

1. **错误类型分类**：概念理解错误、方法应用错误、计算错误等
2. **错误原因分析**：深层次分析产生错误的根本原因
3. **典型错误示例**：提供具体的错误案例和正确做法对比
4. **改进策略**：针对每种错误类型提供具体的改进方法
5. **预防措施**：如何在学习中避免类似错误
6. **自我检查方法**：教会学生自主发现和纠正错误

请提供专业、实用的错误分析和改进建议。`;
        actionName = '错题分析';
        userDisplayMessage = '🔍 请帮我分析学习中的常见错误';
        break;
      case 'recommend':
        prompt = `作为AI智能推荐系统，请为学生提供个性化的学习资源和方法推荐。请包含：

1. **学习资源推荐**：
   - 优质教材和参考书
   - 在线学习平台和课程
   - 学习工具和应用

2. **学习方法推荐**：
   - 高效的学习技巧
   - 记忆方法和策略
   - 时间管理技巧

3. **个性化建议**：
   - 根据不同学习风格的建议
   - 针对不同基础水平的推荐
   - 考虑学习目标的定制化方案

4. **实践指导**：如何有效使用推荐的资源和方法

请提供实用、可操作的推荐方案。`;
        actionName = '智能推荐';
        userDisplayMessage = '🎯 请为我推荐学习资源和方法';
        break;
      case 'ppt_template':
        // PPT模板选择功能
        handlePPTTemplateSelection();
        return;
      default:
        return;
    }

    // 添加用户消息
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: userDisplayMessage,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);

    // 发送到AI助理
    setLoading(true);
    setAiStatus('thinking');

    try {
      const response = await fetch('http://localhost:5001/api/ai-assistant/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: prompt,
          context: messages.slice(-3).map(msg => ({
            type: msg.type,
            content: msg.content,
            timestamp: msg.timestamp.toISOString()
          })),
          action_type: actionKey,
          user_preferences: {
            learning_style: 'adaptive',
            difficulty_level: 'intermediate',
            preferred_format: 'structured'
          }
        })
      });

      const result = await response.json();

      if (result.success) {
        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: result.data.response || result.response,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, aiResponse]);
        
        // 显示成功提示
        message.success(`${actionName}已完成！`);
        
        // 更新使用统计
        setActionUsageStats(prev => ({
          ...prev,
          [actionKey]: (prev[actionKey] || 0) + 1
        }));
        
        // 保存到本地存储
        const updatedStats = {
          ...actionUsageStats,
          [actionKey]: (actionUsageStats[actionKey] || 0) + 1
        };
        localStorage.setItem('ai_action_usage_stats', JSON.stringify(updatedStats));
      } else {
        throw new Error(result.message || '请求失败');
      }
    } catch (error) {
      console.error('快捷操作失败:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `抱歉，${actionName}功能暂时不可用。请检查网络连接或稍后重试。如果问题持续存在，您可以尝试手动输入相关问题。`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
      
      // 显示错误提示
      message.error(`${actionName}执行失败，请重试`);
    } finally {
      setLoading(false);
      setAiStatus('online');
    }
  };

  const quickActions = [
    { icon: <BulbOutlined />, text: '学习诊断', color: '#52c41a' },
    { icon: <FileTextOutlined />, text: '作业辅导', color: '#1890ff' },
    { icon: <ThunderboltOutlined />, text: '快速答疑', color: '#faad14' },
    { icon: <StarOutlined />, text: '学习计划', color: '#722ed1' },
  ];

  // 快捷操作
  const quickActionsExtended = [
    { key: 'explain', label: '解释概念', icon: '💡', description: '让AI解释复杂概念' },
    { key: 'practice', label: '练习题目', icon: '📝', description: '生成个性化练习题' },
    { key: 'summary', label: '知识总结', icon: '📚', description: '总结学习要点' },
    { key: 'ppt_template', label: 'PPT模板', icon: '📊', description: '选择PPT模板生成演示文稿' },
    { key: 'plan', label: '学习计划', icon: '📅', description: '制定学习计划' },
    { key: 'analyze', label: '错题分析', icon: '🔍', description: '分析错题原因' },
    { key: 'recommend', label: '智能推荐', icon: '🎯', description: '推荐学习内容' },
  ];

  const aiStats = [
    { label: '今日互动', value: 23, icon: <MessageOutlined /> },
    { label: '解答问题', value: 156, icon: <BulbOutlined /> },
    { label: '学习建议', value: 89, icon: <StarOutlined /> },
  ];

  // AI统计数据（模拟）
  const aiStatsData = {
    totalQuestions: 156,
    correctAnswers: 128,
    accuracy: 82,
    studyTime: 45,
    aiStatus: 'online', // online, busy, offline
    lastActive: '刚刚',
    todayInteractions: 23,
  };

  if (collapsed) {
    return (
      <div className="ai-sidebar ai-sidebar-collapsed">
        <div className="ai-sidebar-header">
          <Button
            type="text"
            icon={<PlusOutlined />}
            onClick={onToggleCollapse}
            className="expand-button"
          />
          <div className="ai-avatar-mini">
            <Badge status={aiStatus === 'online' ? 'success' : aiStatus === 'thinking' ? 'processing' : 'default'}>
              <Avatar icon={<RobotOutlined />} className="ai-avatar" />
            </Badge>
          </div>
        </div>
        <div className="quick-actions-mini">
          {quickActions.map((action, index) => {
            // 映射旧的快捷操作到新的key
            const actionKeyMap: { [key: string]: string } = {
              '学习诊断': 'analyze',
              '作业辅导': 'explain',
              '快速答疑': 'practice',
              '学习计划': 'plan'
            };
            const actionKey = actionKeyMap[action.text] || 'explain';
            
            return (
              <Tooltip key={index} title={action.text} placement="right">
                <Button
                  type="text"
                  icon={action.icon}
                  className="quick-action-mini"
                  style={{ color: action.color }}
                  onClick={() => handleQuickAction(actionKey)}
                  disabled={loading}
                />
              </Tooltip>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="ai-sidebar">
      {/* AI助手头部 */}
      <div className="ai-sidebar-header">
        <div className="ai-header-content">
          <div className="ai-avatar">
            <RobotOutlined />
            <div className={`ai-status-indicator ${aiStatsData.aiStatus}`}></div>
          </div>
          <div className="ai-info">
            <Title level={4} style={{ margin: 0, color: 'var(--ai-text-primary)' }}>高小分 AI</Title>
            <Text style={{ color: 'var(--ai-text-secondary)', fontSize: '12px' }}>
              {aiStatsData.aiStatus === 'online' && '🟢 在线助学'}
              {aiStatsData.aiStatus === 'busy' && '🟡 忙碌中'}
              {aiStatsData.aiStatus === 'offline' && '🔴 离线'}
            </Text>
            <Text className="ai-last-active">
              最后活跃: {aiStatsData.lastActive}
            </Text>
          </div>
        </div>
        <Space>
          {/* 模式切换按钮组 */}
          {onModeChange && (
            <Space size={4}>
              <Tooltip title="抽屉模式">
                <Button
                  type={displayMode === 'drawer' ? 'primary' : 'text'}
                  icon={<ExpandOutlined />}
                  onClick={() => onModeChange('drawer')}
                  size="small"
                  className="mode-switch-btn"
                />
              </Tooltip>
              <Tooltip title="全屏模式">
                <Button
                  type={displayMode === 'fullscreen' ? 'primary' : 'text'}
                  icon={<FullscreenOutlined />}
                  onClick={() => onModeChange('fullscreen')}
                  size="small"
                  className="mode-switch-btn"
                />
              </Tooltip>
              <Tooltip title="隐藏AI">
                <Button
                  type="text"
                  icon={<CloseOutlined />}
                  onClick={() => onModeChange('hidden')}
                  size="small"
                  className="mode-switch-btn"
                />
              </Tooltip>
            </Space>
          )}
          <Button
            type="text"
            icon={<MinusOutlined />}
            onClick={onToggleCollapse}
            className="collapse-button"
          />
        </Space>
      </div>

      {/* AI统计信息 */}
      <div className="ai-stats">
        <div className="stats-grid">
          {aiStats.map((stat, index) => (
            <div key={index} className="stat-item">
              <div className="stat-icon">{stat.icon}</div>
              <div className="stat-content">
                <div className="stat-value">{stat.value}</div>
                <div className="stat-label">{stat.label}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 快捷操作 - 紧凑设计 */}
      <div className="quick-actions-compact">
        <div className="actions-horizontal">
          {quickActionsExtended.slice(0, 3).map((action, index) => (
            <Tooltip key={action.key} title={action.description} placement="top">
              <Button
                type="text"
                className="quick-action-compact"
                title={action.description}
                onClick={() => handleQuickAction(action.key)}
                disabled={loading}
              >
                <span className="action-icon">{action.icon}</span>
              </Button>
            </Tooltip>
          ))}
          <Tooltip title="更多功能" placement="top">
            <Button
              type="text"
              className="quick-action-compact more-actions"
              onClick={() => setShowMoreActions(!showMoreActions)}
            >
              <MenuOutlined />
            </Button>
          </Tooltip>
        </div>
        {showMoreActions && (
          <div className="more-actions-panel">
            {quickActionsExtended.slice(3).map((action, index) => (
              <Button
                key={action.key}
                type="text"
                className="quick-action-item"
                title={action.description}
                onClick={() => handleQuickAction(action.key)}
                disabled={loading}
              >
                <span className="action-icon">{action.icon}</span>
                <span className="action-label">
                  {action.label}
                  {actionUsageStats[action.key] && (
                    <Badge 
                      count={actionUsageStats[action.key]} 
                      size="small" 
                      style={{ 
                        backgroundColor: '#52c41a',
                        fontSize: '10px',
                        marginLeft: '8px'
                      }}
                    />
                  )}
                </span>
              </Button>
            ))}
          </div>
        )}
      </div>

      {/* 对话区域 */}
      <div className="chat-section">
        <div className="messages-container">
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.type}-message`}>
              <div className={`message-avatar ${message.type}-message`}>
                {message.type === 'user' ? <UserOutlined /> : <RobotOutlined />}
              </div>
              <div className="message-content">
                <div className="message-body">
                  {message.type === 'assistant' ? (
                    <div className="markdown-content">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        rehypePlugins={[rehypeHighlight, rehypeRaw]}
                        components={{
                          code: ({ children, ...props }: any) => (
                            <code {...props}>{children}</code>
                          ),
                          pre: ({ children, ...props }: any) => (
                            <pre {...props}>{children}</pre>
                          ),
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    message.content
                  )}
                </div>
                <div className="message-time">
                  {message.timestamp.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="loading-message">
              <div className="message-avatar assistant-message">
                <RobotOutlined />
              </div>
              <div className="loading-content">
                AI正在思考中
                <div className="loading-dots">
                  <div className="loading-dot"></div>
                  <div className="loading-dot"></div>
                  <div className="loading-dot"></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* 输入区域 */}
        <div className="input-section">
          <div className="input-container">
            <TextArea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="向高小分提问..."
              autoSize={{ minRows: 1, maxRows: 3 }}
              onPressEnter={(e) => {
                if (!e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              className="message-input"
              disabled={uploading}
            />
            <div className="input-actions">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*,.pdf"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
              />
              <Tooltip title="上传图片或PDF文档">
                <Button
                  type="text"
                  icon={<PaperClipOutlined />}
                  size="small"
                  className="action-button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  loading={uploading}
                />
              </Tooltip>
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || loading || uploading}
                size="small"
                className="send-button"
                loading={loading}
              />
            </div>
          </div>
        </div>
      </div>

      {/* PPT模板选择Modal */}
      <Modal
        title={
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center'
          }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '14px' }}>
              <FileTextOutlined style={{ fontSize: '12px' }} />
              选择PPT模板
            </span>
            <Button 
              type="primary" 
              icon={<UploadOutlined />} 
              onClick={() => setShowUploadModal(true)}
            >
              上传模板
            </Button>
          </div>
        }
        open={showPPTTemplateModal}
        onCancel={() => setShowPPTTemplateModal(false)}
        okText={selectedTemplate ? '应用模板' : '请选择模板'}
        cancelText="取消"
        onOk={() => {
          if (selectedTemplate) {
            const templateMessage = `请使用"${selectedTemplate.name}"模板帮我生成PPT，模板描述：${selectedTemplate.description}`;
            setInputValue(templateMessage);
            handleSendMessage();
            setShowPPTTemplateModal(false);
            setSelectedTemplate(null);
          }
        }}
        okButtonProps={{
          disabled: !selectedTemplate
        }}
        width={800}
      >
        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
        {/* 按分类显示模板 */}
        {Object.entries(
          pptTemplates.reduce((groups, template) => {
            const category = template.category || '其他';
            if (!groups[category]) groups[category] = [];
            groups[category].push(template);
            return groups;
          }, {} as Record<string, any[]>)
        ).map(([category, templates]) => {
          const categoryIcons: Record<string, string> = {
            '学术类': '📚',
            '教育类': '🎓', 
            '商务类': '💼',
            '创意类': '🎨',
            '其他': '📋'
          };
          const categoryColors: Record<string, string> = {
            '学术类': '#1890ff',
            '教育类': '#52c41a',
            '商务类': '#fa8c16', 
            '创意类': '#eb2f96',
            '其他': '#722ed1'
          };
          
          return (
            <div key={category} style={{ marginBottom: '24px' }}>
              <Title level={5} style={{ 
                marginBottom: '8px', 
                color: categoryColors[category],
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '12px'
              }}>
                <span>{categoryIcons[category]}</span>
                {category}
              </Title>
              
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', 
                gap: '12px'
              }}>
                {templates.map(template => {
                  const isSelected = selectedTemplate?.id === template.id;
                  return (
                    <Card
                      key={template.id}
                      hoverable
                      style={{
                        border: isSelected ? `2px solid ${categoryColors[category]}` : '1px solid #f0f0f0',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        transition: 'all 0.3s ease',
                        boxShadow: isSelected 
                          ? `0 4px 12px ${categoryColors[category]}30` 
                          : '0 1px 4px rgba(0,0,0,0.06)'
                      }}
                      onClick={() => setSelectedTemplate(template)}
                      cover={
                        <div style={{ 
                          height: '100px', 
                          background: `linear-gradient(135deg, ${categoryColors[category]}20 0%, ${categoryColors[category]}10 100%)`,
                          display: 'flex', 
                          alignItems: 'center', 
                          justifyContent: 'center'
                        }}>
                          <FileAddOutlined style={{ 
                            fontSize: '32px', 
                            color: categoryColors[category]
                          }} />
                          {isSelected && (
                            <div style={{
                              position: 'absolute',
                              top: '12px',
                              right: '12px',
                              width: '24px',
                              height: '24px',
                              background: categoryColors[category],
                              borderRadius: '50%',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              zIndex: 2
                            }}>
                              <span style={{ color: 'white', fontSize: '14px' }}>✓</span>
                            </div>
                          )}
                        </div>
                      }
                    >
                      <Card.Meta
                        title={template.name}
                        description={template.description}
                      />
                      <div style={{
                        marginTop: '12px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}>
                        <Tag 
                          color={categoryColors[category]}
                          style={{
                            borderRadius: '12px',
                            fontSize: '11px',
                            fontWeight: 500
                          }}
                        >
                          {categoryIcons[category]} {category}
                        </Tag>
                        {isSelected && (
                          <div style={{
                            color: categoryColors[category],
                            fontSize: '12px',
                            fontWeight: 600
                          }}>
                            已选择
                          </div>
                        )}
                      </div>
                    </Card>
                  );
                })}
              </div>
            </div>
          );
        })}
        </div>
      </Modal>

      {/* 上传模板Modal */}
      <Modal
        title={
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            fontSize: '18px',
            fontWeight: 600,
            color: '#1890ff'
          }}>
            <UploadOutlined style={{ fontSize: '20px' }} />
            <span>上传PPT模板</span>
          </div>
        }
        open={showUploadModal}
        onCancel={() => {
          setShowUploadModal(false);
          setUploadForm({ name: '', category: '', file: null });
        }}
        footer={[
          <Button 
            key="cancel" 
            size="large"
            onClick={() => {
              setShowUploadModal(false);
              setUploadForm({ name: '', category: '', file: null });
            }}
            style={{
              borderRadius: '8px',
              height: '40px',
              fontWeight: 500
            }}
          >
            取消
          </Button>,
          <Button 
            key="upload" 
            type="primary" 
            size="large"
            loading={uploadLoading}
            onClick={handleUploadTemplate}
            icon={<UploadOutlined />}
            style={{
              borderRadius: '8px',
              height: '40px',
              fontWeight: 600,
              background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
              border: 'none',
              boxShadow: '0 4px 12px rgba(24, 144, 255, 0.3)'
            }}
          >
            {uploadLoading ? '上传中...' : '立即上传'}
          </Button>
        ]}
        width={600}
        centered
        maskClosable={false}
        style={{
          borderRadius: '12px'
        }}
      >
        <div style={{
          padding: '20px 0',
          background: 'linear-gradient(135deg, #f6f9ff 0%, #e6f7ff 100%)',
          borderRadius: '8px',
          margin: '0 -24px 20px -24px',
          paddingLeft: '24px',
          paddingRight: '24px'
        }}>
          <div style={{
            textAlign: 'center',
            marginBottom: '16px'
          }}>
            <div style={{
              width: '60px',
              height: '60px',
              background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 12px',
              boxShadow: '0 4px 16px rgba(24, 144, 255, 0.3)'
            }}>
              <FileAddOutlined style={{ fontSize: '28px', color: 'white' }} />
            </div>
            <Text style={{ 
              fontSize: '16px', 
              color: '#1890ff',
              fontWeight: 500
            }}>
              上传您的PPT模板，让AI助手更好地为您服务
            </Text>
          </div>
        </div>

        <Form layout="vertical" style={{ marginTop: '8px' }}>
          <Form.Item 
            label={
              <span style={{ 
                fontSize: '14px', 
                fontWeight: 600, 
                color: '#262626',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}>
                <FileTextOutlined style={{ color: '#1890ff' }} />
                模板名称
              </span>
            } 
            required
            style={{ marginBottom: '20px' }}
          >
            <Input
              placeholder="请输入一个有意义的模板名称"
              value={uploadForm.name}
              onChange={(e) => setUploadForm(prev => ({ ...prev, name: e.target.value }))}
              size="large"
              style={{
                borderRadius: '8px',
                border: '2px solid #f0f0f0',
                transition: 'all 0.3s ease'
              }}
              onFocus={(e) => {
                e.target.style.borderColor = '#1890ff';
                e.target.style.boxShadow = '0 0 0 2px rgba(24, 144, 255, 0.1)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = '#f0f0f0';
                e.target.style.boxShadow = 'none';
              }}
            />
          </Form.Item>
          <Form.Item 
            label={
              <span style={{ 
                fontSize: '14px', 
                fontWeight: 600, 
                color: '#262626',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}>
                <StarOutlined style={{ color: '#1890ff' }} />
                模板分类
              </span>
            } 
            required
            style={{ marginBottom: '20px' }}
          >
            <Select
              placeholder="请选择适合的模板分类"
              value={uploadForm.category}
              onChange={(value) => setUploadForm(prev => ({ ...prev, category: value }))}
              size="large"
              style={{ 
                width: '100%',
                borderRadius: '8px'
              }}
              options={[
                { 
                  label: (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: '#1890ff' }}>📚</span>
                      学术类
                    </div>
                  ), 
                  value: '学术类' 
                },
                { 
                  label: (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: '#52c41a' }}>🎓</span>
                      教育类
                    </div>
                  ), 
                  value: '教育类' 
                },
                { 
                  label: (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: '#fa8c16' }}>💼</span>
                      商务类
                    </div>
                  ), 
                  value: '商务类' 
                },
                { 
                  label: (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: '#eb2f96' }}>🎨</span>
                      创意类
                    </div>
                  ), 
                  value: '创意类' 
                },
                { 
                  label: (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: '#722ed1' }}>📋</span>
                      其他
                    </div>
                  ), 
                  value: '其他' 
                }
              ]}
            />
          </Form.Item>
          <Form.Item 
            label={
              <span style={{ 
                fontSize: '14px', 
                fontWeight: 600, 
                color: '#262626',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}>
                <UploadOutlined style={{ color: '#1890ff' }} />
                PPT文件
              </span>
            } 
            required
          >
            <Upload
              beforeUpload={handleFileChange}
              showUploadList={false}
              accept=".ppt,.pptx"
            >
              <div style={{
                border: uploadForm.file ? '2px dashed #52c41a' : '2px dashed #d9d9d9',
                borderRadius: '8px',
                padding: '24px',
                textAlign: 'center',
                background: uploadForm.file ? '#f6ffed' : '#fafafa',
                cursor: 'pointer',
                transition: 'all 0.3s ease'
              }}>
                {uploadForm.file ? (
                  <div>
                    <div style={{
                      fontSize: '48px',
                      color: '#52c41a',
                      marginBottom: '12px'
                    }}>
                      ✅
                    </div>
                    <div style={{
                      fontSize: '16px',
                      fontWeight: 600,
                      color: '#52c41a',
                      marginBottom: '4px'
                    }}>
                      {uploadForm.file.name}
                    </div>
                    <div style={{
                      fontSize: '12px',
                      color: '#8c8c8c'
                    }}>
                      文件大小: {(uploadForm.file.size / 1024 / 1024).toFixed(2)} MB
                    </div>
                  </div>
                ) : (
                  <div>
                    <div style={{
                      fontSize: '48px',
                      color: '#d9d9d9',
                      marginBottom: '12px'
                    }}>
                      📎
                    </div>
                    <div style={{
                      fontSize: '16px',
                      fontWeight: 600,
                      color: '#1890ff',
                      marginBottom: '8px'
                    }}>
                      点击选择PPT文件
                    </div>
                    <div style={{
                      fontSize: '12px',
                      color: '#8c8c8c',
                      lineHeight: '1.5'
                    }}>
                      支持 .ppt 和 .pptx 格式<br/>
                      文件大小不超过 10MB
                    </div>
                  </div>
                )}
              </div>
            </Upload>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AISidebar;