import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Input,
  Button,
  Avatar,
  Space,
  Typography,
  List,
  Tag,
  Spin,
  message,
  Upload,
  Dropdown,
  Tooltip,
  Modal,
  Form,
  Select,
  InputNumber,
  Drawer,
  Divider,
  Switch,
  Slider,
} from 'antd';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeHighlight from 'rehype-highlight';
import rehypeRaw from 'rehype-raw';
import 'katex/dist/katex.min.css';
import 'highlight.js/styles/github.css';
import {
  RobotOutlined,
  SendOutlined,
  CameraOutlined,
  FileImageOutlined,
  FilePdfOutlined,
  SearchOutlined,
  MessageOutlined,
  BulbOutlined,
  UserOutlined,
  CopyOutlined,
  PlusOutlined,
  ShareAltOutlined,
  DeleteOutlined,
  ReloadOutlined,
  SettingOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined,
  MenuOutlined,
  CloseOutlined,
  EditOutlined,
  SaveOutlined,
  HistoryOutlined,
  StarOutlined,
  MoreOutlined,
  ThunderboltOutlined,
  BookOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons';
import { useAIAssistantStore, type Message, type ConversationItem } from '../stores/aiAssistantStore';
import { useAuthStore } from '../stores/authStore';
import KnowledgeGraphEditor from '../components/KnowledgeGraphEditor/KnowledgeGraphEditor';
import './AIAssistant.css';

const { TextArea } = Input;
const { Text, Title } = Typography;

// ConversationItem 接口已在 store 中定义

const AIAssistant: React.FC = () => {
  const {
    messages,
    inputValue,
    loading,
    aiStats,
    conversations,
    currentConversationId,
    conversationsLoading,
    addMessage,
    setInputValue,
    setLoading,
    incrementTodayInteractions,
    resetConversation,
    loadConversations,
    createConversation,
    updateConversation,
    deleteConversation,
    toggleConversationStar,
    setCurrentConversationId,
  } = useAIAssistantStore();
  
  const { user } = useAuthStore();
  
  // UI状态
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [editingMessage, setEditingMessage] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
  const [renameModalVisible, setRenameModalVisible] = useState(false);
  const [renamingConversationId, setRenamingConversationId] = useState<string | null>(null);
  const [newConversationTitle, setNewConversationTitle] = useState('');
  const [searchKeyword, setSearchKeyword] = useState('');
  const [knowledgeGraphEditorVisible, setKnowledgeGraphEditorVisible] = useState(false);
  // 会话相关状态现在由 store 管理
  
  // 设置状态
  const [aiSettings, setAiSettings] = useState({
    temperature: 0.7,
    maxTokens: 2000,
    enableContext: true,
    autoSave: true,
    theme: 'auto'
  });
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pdfInputRef = useRef<HTMLInputElement>(null);

  // 滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 页面加载时自动加载会话列表
  useEffect(() => {
    if (user) {
      loadConversations();
    }
  }, [user, loadConversations]);

  // 当没有当前会话时，自动创建一个新会话
   useEffect(() => {
     if (user && conversations.length === 0 && !conversationsLoading && !currentConversationId) {
       handleCreateNewConversation();
     }
   }, [user, conversations.length, conversationsLoading, currentConversationId]);

  // 发送消息
  const handleSendMessage = async () => {
    if (!inputValue.trim() || loading) return;

    // 确保有当前会话
     let conversationId = currentConversationId;
     if (!conversationId) {
       conversationId = await handleCreateNewConversation();
       if (!conversationId) {
         message.error('创建会话失败，请重试');
         return;
       }
     }

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setInputValue('');
    setLoading(true);
    incrementTodayInteractions();

    try {
      // 先保存用户消息到会话
      await saveMessageToConversation(conversationId, userMessage);

      const response = await fetch('http://localhost:5001/api/ai-assistant/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          message: userMessage.content,
          context: messages.slice(-5).map(msg => ({
            type: msg.type,
            content: msg.content,
            timestamp: msg.timestamp.toISOString()
          })),
          settings: aiSettings,
          conversationId: conversationId
        })
      });

      const result = await response.json();

      if (result.success) {
        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: result.data?.response || result.response || '抱歉，我现在无法回答这个问题。',
          timestamp: new Date(),
        };
        addMessage(aiResponse);
        
        // 保存AI回复到会话
        await saveMessageToConversation(conversationId, aiResponse);
        
        // 更新会话的最后消息
        await updateConversation(conversationId, {
          lastMessage: userMessage.content,
          timestamp: new Date()
        });
      } else {
        throw new Error(result.message || '请求失败');
      }
    } catch (error) {
      console.error('AI对话失败:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: '抱歉，我遇到了一些技术问题，请稍后再试。',
        timestamp: new Date(),
      };
      addMessage(errorMessage);
      message.error('发送失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 保存消息到会话
  const saveMessageToConversation = async (conversationId: string, msg: Message) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      await fetch(`/api/ai-assistant/conversations/${conversationId}/messages`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          role: msg.type,
          content: msg.content,
          message_type: 'text',
          metadata: {
            timestamp: msg.timestamp.toISOString(),
            messageId: msg.id
          }
        })
      });
    } catch (error) {
      console.error('保存消息失败:', error);
    }
  };

  // 新建对话
  const handleCreateNewConversation = async () => {
    const conversationId = await createConversation('新对话');
    if (conversationId) {
      resetConversation();
      return conversationId;
    }
    return null;
  };

  // 处理会话操作
  const handleConversationAction = async (action: string, conversationId: string) => {
    switch (action) {
      case 'star':
        await toggleConversationStar(conversationId);
        break;
      case 'rename':
        // 显示重命名对话框
        setRenamingConversationId(conversationId);
        const currentConv = conversations.find(c => c.id === conversationId);
        setNewConversationTitle(currentConv?.title || '');
        setRenameModalVisible(true);
        break;
      case 'export':
        await handleExportConversation(conversationId);
        break;
      case 'delete':
        Modal.confirm({
          title: '确认删除',
          content: '确定要删除这个对话吗？删除后无法恢复。',
          onOk: async () => {
            const success = await deleteConversation(conversationId);
            if (success) {
              message.success('删除成功');
              // 如果删除的是当前会话，重置对话
              if (conversationId === currentConversationId) {
                resetConversation();
              }
            } else {
              message.error('删除失败');
            }
          }
        });
        break;
    }
  };

  // 快捷操作
  const quickActions = [
    { key: 'explain', label: '解释概念', icon: <QuestionCircleOutlined /> },
    { key: 'solve', label: '解题步骤', icon: <ThunderboltOutlined /> },
    { key: 'summarize', label: '总结要点', icon: <BookOutlined /> },
    { key: 'translate', label: '翻译文本', icon: <MessageOutlined /> },
  ];

  const handleQuickAction = (actionKey: string) => {
    const actionPrompts = {
      explain: '请解释一个概念或知识点',
      solve: '请提供解题步骤和思路',
      summarize: '请总结重要知识点',
      translate: '请翻译以下内容'
    };
    setInputValue(actionPrompts[actionKey as keyof typeof actionPrompts] || '');
  };

  // 消息操作
  const handleCopyMessage = (content: string) => {
    navigator.clipboard.writeText(content);
    message.success('已复制到剪贴板');
  };

  const handleEditMessage = (messageId: string, content: string) => {
    setEditingMessage(messageId);
    setEditContent(content);
  };

  const handleSaveEdit = () => {
    // 这里应该更新消息内容
    setEditingMessage(null);
    setEditContent('');
    message.success('消息已更新');
  };

  // 智能推荐学科
  const analyzeContentForSubject = (content: string): string | undefined => {
    const subjectKeywords = {
      'math': ['数学', '计算', '公式', '方程', '函数', '几何', '代数', '微积分', '统计', '概率'],
      'physics': ['物理', '力学', '电学', '光学', '热学', '量子', '相对论', '能量', '动量'],
      'chemistry': ['化学', '分子', '原子', '反应', '化合物', '元素', '有机', '无机', '催化'],
      'biology': ['生物', '细胞', '基因', '蛋白质', 'DNA', '进化', '生态', '植物', '动物'],
      'history': ['历史', '朝代', '战争', '文化', '政治', '社会', '经济', '人物', '事件'],
      'literature': ['文学', '诗歌', '小说', '散文', '作家', '文本', '修辞', '语言', '文化'],
      'english': ['英语', 'English', '语法', '词汇', '阅读', '写作', '听力', '口语'],
      'computer': ['计算机', '编程', '算法', '数据结构', '软件', '硬件', '网络', '数据库']
    };

    const contentLower = content.toLowerCase();
    let maxScore = 0;
    let recommendedSubject = undefined;

    Object.entries(subjectKeywords).forEach(([subject, keywords]) => {
      const score = keywords.reduce((acc, keyword) => {
        return acc + (contentLower.includes(keyword.toLowerCase()) ? 1 : 0);
      }, 0);
      if (score > maxScore) {
        maxScore = score;
        recommendedSubject = subject;
      }
    });

    return maxScore > 0 ? recommendedSubject : undefined;
  };

  // 保存到知识图谱
  const handleSaveToKnowledgeGraph = () => {
    if (!editContent.trim()) {
      message.warning('请输入要保存的内容');
      return;
    }
    setKnowledgeGraphEditorVisible(true);
  };



  const handleDeleteMessage = (messageId: string) => {
    // 这里应该删除消息
    message.success('消息已删除');
  };

  // 新建对话（UI处理）
  const handleNewConversation = () => {
    handleCreateNewConversation();
  };

  // 处理图片上传
  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // TODO: 实现图片上传功能
      message.info('图片上传功能待实现');
    }
  };

  // 处理PDF上传
  const handlePdfUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // TODO: 实现PDF上传功能
      message.info('PDF上传功能待实现');
    }
  };

  // 导出会话功能
  const handleExportConversation = async (conversationId: string) => {
    try {
      const conversation = conversations.find(c => c.id === conversationId);
      if (!conversation) {
        message.error('会话不存在');
        return;
      }

      // 获取会话的完整消息历史
      const response = await fetch(`/api/conversations/${conversationId}/messages`);
      if (!response.ok) {
        throw new Error('获取会话消息失败');
      }
      
      const messages = await response.json();
      
      // 生成导出内容
      const exportContent = [
        `会话标题: ${conversation.title}`,
        `导出时间: ${new Date().toLocaleString()}`,
        `消息数量: ${messages.length}`,
        '\n' + '='.repeat(50) + '\n',
        ...messages.map((msg: Message, index: number) => 
          `${index + 1}. [${msg.type === 'user' ? '用户' : 'AI助手'}] ${new Date(msg.timestamp).toLocaleString()}\n${msg.content}\n`
        )
      ].join('\n');

      // 创建并下载文件
      const blob = new Blob([exportContent], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${conversation.title}_${new Date().toISOString().split('T')[0]}.txt`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      message.success('导出成功');
    } catch (error) {
      console.error('导出失败:', error);
      message.error('导出失败，请重试');
    }
  };

  // 预处理LaTeX公式格式
  const preprocessLatex = (content: string) => {
    let processed = content;
    
    // 如果内容已经包含标准LaTeX格式，直接返回
    if (processed.includes('\\[') || processed.includes('\\(')) {
      return processed;
    }
    
    // 1. 将独立行的 [ formula ] 转换为 \[ formula \]
    processed = processed.replace(/^\s*\[\s*([^\[\]]+?)\s*\]\s*$/gm, '\\[$1\\]');
    
    // 2. 将行内的 [ formula ] 转换为 \[ formula \]
    processed = processed.replace(/\s\[\s*([^\[\]]+?)\s*\]\s/g, ' \\[$1\\] ');
    
    // 3. 将包含数学符号的 (formula) 转换为 \(formula\)（更严格的匹配）
    processed = processed.replace(/\(([^()]*(?:\\[a-zA-Z]+|\\frac|\\sqrt|\\sum|\\int|\\Delta|[a-zA-Z]\s*[=<>+\-*/^_{}])[^()]*)\)/g, '\\($1\\)');
    
    return processed;
  };

  // 渲染消息
  const renderMessage = (msg: Message) => {
    const isUser = msg.type === 'user';
    const isEditing = editingMessage === msg.id;

    return (
      <div key={msg.id} className={`message-item ${isUser ? 'user' : 'assistant'}`}>
        <div className="message-avatar">
          <Avatar 
            icon={isUser ? <UserOutlined /> : <RobotOutlined />}
            style={{ 
              backgroundColor: isUser ? 'var(--primary-color)' : 'var(--secondary-color)'
            }}
          />
        </div>
        <div className="message-content">
          <div className="message-header">
            <Text strong style={{ color: 'var(--text-primary)' }}>
              {isUser ? (user?.full_name || '我') : 'AI助手'}
            </Text>
            <Text type="secondary" style={{ fontSize: '12px', marginLeft: '8px' }}>
              {msg.timestamp.toLocaleTimeString()}
            </Text>
          </div>
          <div className="message-body">
            {isEditing ? (
              <div className="edit-container">
                <TextArea
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  autoSize={{ minRows: 2, maxRows: 8 }}
                />
                <div className="edit-actions">
                  <Button size="small" onClick={handleSaveToKnowledgeGraph} icon={<SaveOutlined />} type="primary">
                    保存到图谱
                  </Button>
                  <Button size="small" onClick={() => setEditingMessage(null)}>
                    取消
                  </Button>
                </div>
              </div>
            ) : (
              <div className="message-text">
                {isUser ? (
                  <Text>{msg.content}</Text>
                ) : (
                  <div className="markdown-content">
                     <ReactMarkdown
                       remarkPlugins={[remarkGfm, remarkMath]}
                       rehypePlugins={[rehypeKatex, rehypeHighlight, rehypeRaw]}
                       components={{
                         // 自定义代码块渲染
                         code: ({ className, children, ...props }: any) => {
                           const match = /language-(\w+)/.exec(className || '');
                           const isInline = !match;
                           return isInline ? (
                             <code className={className} {...props}>
                               {children}
                             </code>
                           ) : (
                             <pre className={className}>
                               <code>{children}</code>
                             </pre>
                           );
                         },
                         // 自定义表格渲染
                         table: ({ children }) => (
                           <table style={{ 
                             border: '1px solid #d9d9d9', 
                             borderCollapse: 'collapse',
                             width: '100%',
                             marginBottom: '16px'
                           }}>
                             {children}
                           </table>
                         ),
                         th: ({ children }) => (
                           <th style={{ 
                             border: '1px solid #d9d9d9', 
                             padding: '8px 12px',
                             backgroundColor: '#fafafa',
                             fontWeight: 'bold'
                           }}>
                             {children}
                           </th>
                         ),
                         td: ({ children }) => (
                           <td style={{ 
                             border: '1px solid #d9d9d9', 
                             padding: '8px 12px'
                           }}>
                             {children}
                           </td>
                         ),
                       }}
                     >
                       {preprocessLatex(msg.content)}
                     </ReactMarkdown>
                   </div>
                )}
              </div>
            )}
          </div>
          {!isEditing && (
            <div className="message-actions">
              <Tooltip title="复制">
                <Button 
                  type="text" 
                  size="small" 
                  icon={<CopyOutlined />}
                  onClick={() => handleCopyMessage(msg.content)}
                />
              </Tooltip>
              <Tooltip title="编辑">
                <Button 
                  type="text" 
                  size="small" 
                  icon={<EditOutlined />}
                  onClick={() => handleEditMessage(msg.id, msg.content)}
                />
              </Tooltip>
              <Tooltip title="删除">
                <Button 
                  type="text" 
                  size="small" 
                  icon={<DeleteOutlined />}
                  onClick={() => handleDeleteMessage(msg.id)}
                  danger
                />
              </Tooltip>
            </div>
          )}
        </div>
      </div>
    );
  };

  // 侧边栏内容
  // 过滤会话列表
  const filteredConversations = conversations.filter(conv => {
    if (!searchKeyword.trim()) return true;
    const keyword = searchKeyword.toLowerCase();
    return conv.title.toLowerCase().includes(keyword) || 
           conv.lastMessage?.toLowerCase().includes(keyword);
  });

  const renderSidebar = () => (
    <div className="ai-sidebar">
      <div className="sidebar-header">
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={handleNewConversation}
          block
          style={{ marginBottom: '12px' }}
        >
          新建对话
        </Button>
        
        <Input
          placeholder="搜索对话..."
          prefix={<SearchOutlined />}
          value={searchKeyword}
          onChange={(e) => setSearchKeyword(e.target.value)}
          allowClear
        />
      </div>
      
      <div className="conversation-list">
        <Text strong style={{ color: 'var(--text-primary)', marginBottom: '12px', display: 'block' }}>
          对话历史 ({filteredConversations.length})
        </Text>
        {filteredConversations.length === 0 && searchKeyword ? (
          <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text-secondary)' }}>
            <SearchOutlined style={{ fontSize: '24px', marginBottom: '8px' }} />
            <div>未找到匹配的对话</div>
          </div>
        ) : (
          filteredConversations.map(conv => (
            <div 
            key={conv.id}
            className={`conversation-item ${currentConversationId === conv.id ? 'active' : ''}`}
            onClick={() => setCurrentConversationId(conv.id)}
          >
            <div className="conversation-content">
              <div className="conversation-title">
                {conv.starred && <StarOutlined style={{ color: '#faad14', marginRight: '4px' }} />}
                <Text ellipsis>{conv.title}</Text>
              </div>
              <Text type="secondary" ellipsis style={{ fontSize: '12px' }}>
                {conv.lastMessage}
              </Text>
            </div>
            <Dropdown
              menu={{
                items: [
                  { key: 'star', label: conv.starred ? '取消收藏' : '收藏', icon: <StarOutlined /> },
                  { key: 'rename', label: '重命名', icon: <EditOutlined /> },
                  { key: 'export', label: '导出', icon: <ShareAltOutlined /> },
                  { key: 'delete', label: '删除', icon: <DeleteOutlined />, danger: true },
                ],
                onClick: ({ key }) => handleConversationAction(key, conv.id)
              }}
              trigger={['click']}
            >
              <Button type="text" size="small" icon={<MoreOutlined />} />
            </Dropdown>
          </div>
        ))
        )}
      </div>
    </div>
  );

  // 设置面板
  const renderSettings = () => (
    <div className="settings-panel">
      <Title level={4}>AI设置</Title>
      <Divider />
      
      <div className="setting-item">
        <Text>创造性</Text>
        <Slider
          min={0}
          max={1}
          step={0.1}
          value={aiSettings.temperature}
          onChange={(value) => setAiSettings({...aiSettings, temperature: value})}
        />
      </div>
      
      <div className="setting-item">
        <Text>最大回复长度</Text>
        <InputNumber
          min={100}
          max={4000}
          value={aiSettings.maxTokens}
          onChange={(value) => setAiSettings({...aiSettings, maxTokens: value || 2000})}
        />
      </div>
      
      <div className="setting-item">
        <Text>启用上下文记忆</Text>
        <Switch
          checked={aiSettings.enableContext}
          onChange={(checked) => setAiSettings({...aiSettings, enableContext: checked})}
        />
      </div>
      
      <div className="setting-item">
        <Text>自动保存对话</Text>
        <Switch
          checked={aiSettings.autoSave}
          onChange={(checked) => setAiSettings({...aiSettings, autoSave: checked})}
        />
      </div>
    </div>
  );

  // 主界面
  const renderMainContent = () => (
    <div className="ai-main-content">
      {/* 顶部工具栏 */}
      <div className="ai-toolbar">
        <div className="toolbar-left">
          <Button 
            type="text" 
            icon={<MenuOutlined />}
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          />
          <Title level={4} style={{ margin: 0, color: 'var(--text-primary)' }}>
            AI智能助手
          </Title>
        </div>
        <div className="toolbar-right">
          <Tooltip title="设置">
            <Button 
              type="text" 
              icon={<SettingOutlined />}
              onClick={() => setShowSettings(true)}
            />
          </Tooltip>
          <Tooltip title={isFullscreen ? '退出全屏' : '全屏'}>
             <Button 
               type="text" 
               icon={isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
               onClick={() => setIsFullscreen(!isFullscreen)}
             />
           </Tooltip>
        </div>
      </div>

      {/* 消息区域 */}
      <div className="messages-area">
        {messages.length === 0 ? (
          <div className="welcome-screen">
            <div className="welcome-content">
              <RobotOutlined style={{ fontSize: '64px', color: 'var(--primary-color)', marginBottom: '16px' }} />
              <Title level={3} style={{ color: 'var(--text-primary)' }}>你好！我是AI学习助手</Title>
              <Text type="secondary">我可以帮助你学习、解答问题、制定计划等。有什么我可以帮助你的吗？</Text>
              
              <div className="quick-start">
                <Text strong style={{ display: 'block', marginBottom: '12px', color: 'var(--text-primary)' }}>快速开始：</Text>
                <Space wrap>
                  {quickActions.map(action => (
                    <Button 
                      key={action.key}
                      icon={action.icon}
                      onClick={() => handleQuickAction(action.key)}
                    >
                      {action.label}
                    </Button>
                  ))}
                </Space>
              </div>
            </div>
          </div>
        ) : (
          <div className="messages-list">
            {messages.map(renderMessage)}
            {loading && (
              <div className="message-item assistant">
                <div className="message-avatar">
                  <Avatar icon={<RobotOutlined />} style={{ backgroundColor: 'var(--secondary-color)' }} />
                </div>
                <div className="message-content">
                  <div className="message-body loading">
                    <Spin size="small" />
                    <Text style={{ marginLeft: '8px', color: 'var(--text-secondary)' }}>正在思考...</Text>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* 输入区域 */}
      <div className="input-area">
        {messages.length > 0 && (
          <div className="quick-actions">
            <Space>
              {quickActions.map(action => (
                <Button 
                  key={action.key}
                  size="small"
                  icon={action.icon}
                  onClick={() => handleQuickAction(action.key)}
                >
                  {action.label}
                </Button>
              ))}
            </Space>
          </div>
        )}
        
        <div className="input-container">
          <div className="input-wrapper">
            <TextArea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="输入消息...（按 Enter 发送，Shift + Enter 换行）"
              autoSize={{ minRows: 1, maxRows: 6 }}
              onPressEnter={(e) => {
                if (!e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
            />
            <div className="input-actions">
              <Tooltip title="上传图片">
                <Button
                  type="text"
                  icon={<FileImageOutlined />}
                  onClick={() => fileInputRef.current?.click()}
                />
              </Tooltip>
              <Tooltip title="上传PDF">
                <Button
                  type="text"
                  icon={<FilePdfOutlined />}
                  onClick={() => pdfInputRef.current?.click()}
                />
              </Tooltip>
              <Tooltip title="拍照识题">
                <Button
                  type="text"
                  icon={<CameraOutlined />}
                />
              </Tooltip>
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSendMessage}
                loading={loading}
                disabled={!inputValue.trim()}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className={`ai-assistant-container ${isFullscreen ? 'fullscreen' : ''}`}>
      {/* 侧边栏 */}
      {!sidebarCollapsed && (
        <div className="ai-sidebar-container">
          {renderSidebar()}
        </div>
      )}
      
      {/* 主内容区 */}
      <div className="ai-content-container">
        {renderMainContent()}
      </div>

      {/* 隐藏的文件输入 */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleImageUpload}
        style={{ display: 'none' }}
      />
      <input
        ref={pdfInputRef}
        type="file"
        accept=".pdf"
        onChange={handlePdfUpload}
        style={{ display: 'none' }}
      />

      {/* 设置抽屉 */}
      <Drawer
        title="AI设置"
        placement="right"
        onClose={() => setShowSettings(false)}
        open={showSettings}
        width={320}
      >
        {renderSettings()}
      </Drawer>

      {/* 重命名对话框 */}
      <Modal
        title="重命名对话"
        open={renameModalVisible}
        onOk={async () => {
          if (newConversationTitle.trim() && renamingConversationId) {
            await updateConversation(renamingConversationId, { title: newConversationTitle.trim() });
            setRenameModalVisible(false);
            setRenamingConversationId(null);
            setNewConversationTitle('');
            message.success('重命名成功');
          } else {
            message.error('请输入有效的标题');
          }
        }}
        onCancel={() => {
          setRenameModalVisible(false);
          setRenamingConversationId(null);
          setNewConversationTitle('');
        }}
        okText="确定"
        cancelText="取消"
      >
        <Input
          value={newConversationTitle}
          onChange={(e) => setNewConversationTitle(e.target.value)}
          placeholder="请输入对话标题"
          maxLength={50}
          showCount
          onPressEnter={() => {
            if (newConversationTitle.trim() && renamingConversationId) {
              updateConversation(renamingConversationId, { title: newConversationTitle.trim() });
              setRenameModalVisible(false);
              setRenamingConversationId(null);
              setNewConversationTitle('');
              message.success('重命名成功');
            }
          }}
        />
      </Modal>

      {/* 知识图谱编辑器 */}
      <KnowledgeGraphEditor
        visible={knowledgeGraphEditorVisible}
        onClose={() => setKnowledgeGraphEditorVisible(false)}
        onSuccess={(data) => {
          setKnowledgeGraphEditorVisible(false);
          setEditingMessage(null);
          setEditContent('');
        }}
        initialContent={editContent}
        suggestedSubjectId={analyzeContentForSubject(editContent)}
      />
    </div>
  );
};

export default AIAssistant;