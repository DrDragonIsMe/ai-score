import React, { useRef, useEffect } from 'react';
import {
  Input,
  Button,
  Avatar,
  Typography,
  Space,
  Spin,
  message,
  Tooltip,
  Card,
  Row,
  Col,
  Statistic,
  Divider,
} from 'antd';
import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  FullscreenExitOutlined,
  BulbOutlined,
  ThunderboltOutlined,
  StarOutlined,
  FileTextOutlined,
  HeartOutlined,
  PictureOutlined,
  FileOutlined,
  CameraOutlined,
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import rehypeRaw from 'rehype-raw';
import { useAuthStore } from '../../stores/authStore';
import { useAIAssistantStore } from '../../stores/aiAssistantStore';
import type { Message } from '../../stores/aiAssistantStore';
import PPTTemplateSelector from '../PPTTemplateSelector/PPTTemplateSelector';
import './AIFullscreen.css';

const { Text, Title } = Typography;
const { TextArea } = Input;

interface AIFullscreenProps {
  onClose?: () => void;
}

const AIFullscreen: React.FC<AIFullscreenProps> = ({ onClose }) => {
  const { token } = useAuthStore();
  const {
    messages,
    inputValue,
    loading,
    showPPTTemplateSelector,
    selectedTemplateId,
    selectedTemplateName,
    aiStats,
    addMessage,
    setInputValue,
    setLoading,
    setShowPPTTemplateSelector,
    setSelectedTemplate,
    incrementTodayInteractions,
    loadPptTemplates,
  } = useAIAssistantStore();
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textAreaRef = useRef<any>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // 组件挂载时加载PPT模板
    loadPptTemplates();
  }, [loadPptTemplates]);

  // 发送消息
  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    addMessage(userMessage);
    setInputValue('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:5001/api/ai-assistant/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: inputValue,
          context: messages.slice(-5).map(msg => ({
            type: msg.type,
            content: msg.content,
            timestamp: msg.timestamp.toISOString()
          }))
        })
      });

      const result = await response.json();

      if (result.success) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: result.data.response || result.response,
          timestamp: new Date(),
          referencedDocuments: result.data.referenced_documents || []
        };
        addMessage(assistantMessage);
        incrementTodayInteractions();
      } else {
        throw new Error(result.message || '发送失败');
      }
    } catch (error) {
      console.error('发送消息失败:', error);
      message.error('发送失败，请重试');
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: '抱歉，我现在有点忙，请稍后再试。如果问题持续存在，请检查网络连接。',
        timestamp: new Date()
      };
      addMessage(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // 处理键盘事件
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // 处理PPT模板选择
  const handlePPTTemplateSelection = () => {
    setShowPPTTemplateSelector(true);
  };

  // 处理模板选择
  const handleTemplateSelect = (templateId: number, templateName: string) => {
    setSelectedTemplate(templateId, templateName);
  };

  // 快捷操作
  const quickActions = [
    { icon: <BulbOutlined />, text: '学习建议', action: () => setInputValue('给我一些学习建议') },
    { icon: <ThunderboltOutlined />, text: '知识点总结', action: () => setInputValue('帮我总结重要知识点') },
    { icon: <StarOutlined />, text: '制定计划', action: () => setInputValue('帮我制定学习计划') },
    { icon: <FileTextOutlined />, text: 'PPT模板', action: () => handlePPTTemplateSelection() },
    { icon: <HeartOutlined />, text: '学习鼓励', action: () => setInputValue('给我一些学习鼓励') },
  ];

  // 渲染消息
  const renderMessage = (msg: Message) => {
    const isUser = msg.type === 'user';
    return (
      <div key={msg.id} className={`message ${isUser ? 'user' : 'assistant'}`}>
        <div className="message-avatar">
          <Avatar 
            icon={isUser ? <UserOutlined /> : <RobotOutlined />} 
            style={{ backgroundColor: isUser ? '#1890ff' : '#52c41a' }}
          />
        </div>
        <div className="message-content">
          <div className="message-bubble">
            {isUser ? (
              <Text>{msg.content}</Text>
            ) : (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight, rehypeRaw]}
                components={{
                  table: ({ children }) => (
                    <div style={{ overflowX: 'auto', margin: '16px 0' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        {children}
                      </table>
                    </div>
                  ),
                  th: ({ children }) => (
                    <th style={{ 
                      border: '1px solid #d9d9d9', 
                      padding: '8px 12px', 
                      backgroundColor: '#fafafa',
                      textAlign: 'left'
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
                {msg.content}
              </ReactMarkdown>
            )}
          </div>
          
          {/* 显示引用文档 */}
          {msg.referencedDocuments && msg.referencedDocuments.length > 0 && (
            <div className="referenced-documents">
              <Text type="secondary" style={{ fontSize: '12px' }}>参考文档：</Text>
              {msg.referencedDocuments.map((doc: any, index: number) => (
                <div key={index} className="referenced-doc">
                  <Text style={{ fontSize: '12px' }}>
                    📄 {doc.title} (相关度: {(doc.relevance_score * 100).toFixed(1)}%)
                  </Text>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="ai-fullscreen">
      {/* 头部 */}
      <div className="fullscreen-header">
        <div className="header-left">
          <Title level={3} style={{ margin: 0, color: 'white' }}>
            🤖 高小分AI助手
          </Title>
          {selectedTemplateName && (
            <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: '14px' }}>
              已选择模板：{selectedTemplateName}
            </Text>
          )}
        </div>
        <div className="header-right">
          <Button 
            type="text" 
            icon={<FullscreenExitOutlined />} 
            onClick={onClose}
            style={{ color: 'white' }}
          >
            退出全屏
          </Button>
        </div>
      </div>

      {/* AI统计信息 */}
      <div className="ai-stats-section">
        <Row gutter={16}>
          <Col span={4}>
            <Card size="small">
              <Statistic 
                title="今日互动" 
                value={aiStats.todayInteractions} 
                suffix="次"
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic 
                title="总互动" 
                value={aiStats.totalInteractions} 
                suffix="次"
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic 
                title="问题解答" 
                value={aiStats.questionsAnswered} 
                suffix="个"
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic 
                title="AI准确率" 
                value={aiStats.aiAccuracy} 
                suffix="%"
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic 
                title="学习时长" 
                value={aiStats.aiStudyTime} 
                suffix="分钟"
                valueStyle={{ color: '#13c2c2' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic 
                title="智能分析" 
                value={aiStats.intelligentAnalysis} 
                suffix="次"
                valueStyle={{ color: '#eb2f96' }}
              />
            </Card>
          </Col>
        </Row>
      </div>

      <Divider style={{ margin: '16px 0' }} />

      {/* 主要内容区域 */}
      <div className="fullscreen-content">
        {/* 消息区域 */}
        <div className="messages-container">
          {messages.map(renderMessage)}
          {loading && (
            <div className="message assistant">
              <div className="message-avatar">
                <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#52c41a' }} />
              </div>
              <div className="message-content">
                <div className="message-bubble">
                  <Spin size="small" /> <Text>正在思考中...</Text>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* 快捷操作 */}
        <div className="quick-actions">
          <Space wrap>
            {quickActions.map((action, index) => (
              <Button
                key={index}
                type="default"
                icon={action.icon}
                onClick={action.action}
                size="small"
              >
                {action.text}
              </Button>
            ))}
          </Space>
        </div>

        {/* 输入区域 */}
        <div className="input-container">
          <div className="input-wrapper">
            <TextArea
              ref={textAreaRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="输入您的问题...（按 Enter 发送，Shift+Enter 换行）"
              autoSize={{ minRows: 1, maxRows: 4 }}
              disabled={loading}
            />
            <div className="input-actions">
              <Space>
                <Tooltip title="上传图片">
                  <Button 
                    type="text" 
                    icon={<PictureOutlined />} 
                    size="small"
                    disabled={loading}
                  />
                </Tooltip>
                <Tooltip title="上传文档">
                  <Button 
                    type="text" 
                    icon={<FileOutlined />} 
                    size="small"
                    disabled={loading}
                  />
                </Tooltip>
                <Tooltip title="拍照">
                  <Button 
                    type="text" 
                    icon={<CameraOutlined />} 
                    size="small"
                    disabled={loading}
                  />
                </Tooltip>
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  onClick={handleSendMessage}
                  disabled={loading || !inputValue.trim()}
                  size="small"
                >
                  发送
                </Button>
              </Space>
            </div>
          </div>
        </div>
      </div>

      {/* PPT模板选择器 */}
      <PPTTemplateSelector
        visible={showPPTTemplateSelector}
        onClose={() => setShowPPTTemplateSelector(false)}
        onSelect={handleTemplateSelect}
        selectedTemplateId={selectedTemplateId}
      />
    </div>
  );
};

export default AIFullscreen;