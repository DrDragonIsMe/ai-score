import React, { useState, useRef, useEffect } from 'react';
import {
  Input,
  Button,
  Avatar,
  Typography,
  Space,
  Spin,
  message,
  Tooltip,
  Dropdown,
  Upload,
  Card,
  Tag,
  Divider,
} from 'antd';
import type { MenuProps } from 'antd';
import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  PaperClipOutlined,
  CameraOutlined,
  FileTextOutlined,
  SettingOutlined,
  FullscreenExitOutlined,
  MenuOutlined,
  BulbOutlined,
  ThunderboltOutlined,
  StarOutlined,
  HeartOutlined,
  PictureOutlined,
  FileOutlined,
  CloseOutlined,
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import rehypeRaw from 'rehype-raw';
import { useAuthStore } from '../../stores/authStore';
import './AIFullscreen.css';

const { Text, Title } = Typography;
const { TextArea } = Input;

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  referencedDocuments?: any[];
  isImage?: boolean;
  imageUrl?: string;
  isPdf?: boolean;
  pdfName?: string;
  documentId?: string;
}

interface AIFullscreenProps {
  onClose?: () => void;
}

const AIFullscreen: React.FC<AIFullscreenProps> = ({ onClose }) => {
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
  const [uploading, setUploading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textAreaRef = useRef<any>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 发送消息
  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);

    try {
      // 调用AI助理API
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
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error(result.message || '发送失败');
      }
    } catch (error) {
      console.error('发送消息失败:', error);
      message.error('发送失败，请重试');
      
      // 添加错误提示消息
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: '抱歉，我现在有点忙，请稍后再试。如果问题持续存在，请检查网络连接。',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
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

  // 快捷操作
  const quickActions = [
    { icon: <BulbOutlined />, text: '学习建议', action: () => setInputValue('给我一些学习建议') },
    { icon: <ThunderboltOutlined />, text: '知识点总结', action: () => setInputValue('帮我总结重要知识点') },
    { icon: <StarOutlined />, text: '制定计划', action: () => setInputValue('帮我制定学习计划') },
    { icon: <HeartOutlined />, text: '学习鼓励', action: () => setInputValue('给我一些学习鼓励') },
  ];

  // 处理图片上传
  const handleImageUpload = async (file: File) => {
    setUploading(true);

    try {
      // 转换为Base64
      const base64 = await new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.readAsDataURL(file);
      });

      // 添加用户上传的图片消息
      const imageMessage: Message = {
        id: Date.now().toString(),
        type: 'user',
        content: '上传了一张图片',
        timestamp: new Date(),
        isImage: true,
        imageUrl: base64
      };
      setMessages(prev => [...prev, imageMessage]);

      // 调用图片识别API
      const response = await fetch('http://localhost:5001/api/ai-assistant/recognize-image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_data: base64.split(',')[1] // 移除data:image前缀
        })
      });

      const result = await response.json();

      if (result.success) {
        console.log('图片识别结果:', result);
        
        // 检查是否为题目
        if (result.is_question && result.question_analysis) {
          // 这是一道题目，进行解题
          const questionAnalysis = result.question_analysis;
          const questionText = questionAnalysis.cleaned_question || result.extracted_text;
          
          const assistantMessage: Message = {
            id: (Date.now() + 1).toString(),
            type: 'assistant',
            content: `我识别出这是一道${questionAnalysis.subject || ''}题目：\n\n**题目内容：**\n${questionText}\n\n**解题分析：**\n${questionAnalysis.solution || '正在分析中...'}\n\n**知识点：** ${questionAnalysis.knowledge_points ? questionAnalysis.knowledge_points.join('、') : '暂无'}`,
            timestamp: new Date()
          };
          setMessages(prev => [...prev, assistantMessage]);
        } else {
          // 普通图片识别
          const assistantMessage: Message = {
            id: (Date.now() + 1).toString(),
            type: 'assistant',
            content: result.analysis || result.extracted_text || '我已经识别了这张图片，有什么问题想要了解的吗？',
            timestamp: new Date()
          };
          setMessages(prev => [...prev, assistantMessage]);
        }
        
        message.success('图片上传并识别成功！');
      } else {
        throw new Error(result.message || '图片识别失败');
      }
    } catch (error) {
      console.error('图片上传失败:', error);
      message.error('图片上传失败，请重试');
    } finally {
      setUploading(false);
    }
  };

  // 处理PDF上传
  const handlePdfUpload = async (file: File) => {
    setUploading(true);

    try {
      // 创建FormData
      const formData = new FormData();
      formData.append('file', file);
      formData.append('user_id', '1'); // 暂时使用固定用户ID
      formData.append('tenant_id', '1'); // 暂时使用固定租户ID
      formData.append('title', file.name);

      // 添加用户上传的PDF消息
      const pdfMessage: Message = {
        id: Date.now().toString(),
        type: 'user',
        content: `上传了PDF文件：${file.name}`,
        timestamp: new Date(),
        isPdf: true,
        pdfName: file.name
      };
      setMessages(prev => [...prev, pdfMessage]);

      // 调用PDF上传API
      const response = await fetch('http://localhost:5001/api/document/upload', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log('API响应:', result);

      if (result.success) {
        console.log('PDF上传成功:', result);
        
        // 更新消息，添加文档ID
        setMessages(prev => prev.map(msg => 
          msg.id === pdfMessage.id 
            ? { ...msg, documentId: result.data.document_id }
            : msg
        ));
        
        // 自动分析PDF内容
        const analysisResponse = await fetch('http://localhost:5001/api/ai-assistant/analyze-document', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            document_id: result.data.document_id
          })
        });

        const analysisResult = await analysisResponse.json();

        if (analysisResult.success) {
          const assistantMessage: Message = {
            id: (Date.now() + 1).toString(),
            type: 'assistant',
            content: analysisResult.data.analysis || '我已经成功分析了你上传的PDF文档。有什么具体问题想要了解的吗？',
            timestamp: new Date()
          };
          setMessages(prev => [...prev, assistantMessage]);
        } else {
          throw new Error(analysisResult.message || 'PDF分析失败');
        }
        
        message.success('PDF上传并分析成功！');
      } else {
        throw new Error(result.message || 'PDF上传失败');
      }
    } catch (error) {
      console.error('PDF上传失败:', error);
      message.error('PDF上传失败，请重试');
    } finally {
      setUploading(false);
    }
  };

  // 文件上传处理
  const handleFileUpload = async (file: File) => {
    const fileType = file.type;
    
    if (fileType.startsWith('image/')) {
      await handleImageUpload(file);
    } else if (fileType === 'application/pdf') {
      await handlePdfUpload(file);
    } else {
      message.error('仅支持图片和PDF文件格式');
    }
    
    return false; // 阻止默认上传行为
  };

  // 渲染消息
  const renderMessage = (msg: Message) => {
    const isUser = msg.type === 'user';
    return (
      <div key={msg.id} className={`message ${isUser ? 'user-message' : 'assistant-message'}`}>
        <div className="message-avatar">
          <Avatar 
            icon={isUser ? <UserOutlined /> : <RobotOutlined />} 
            style={{ 
              backgroundColor: isUser ? '#1890ff' : '#52c41a',
              flexShrink: 0
            }} 
          />
        </div>
        <div className="message-content">
          <div className="message-body">
            {msg.isImage && msg.imageUrl && (
              <div className="image-message">
                <img 
                  src={msg.imageUrl} 
                  alt="上传的图片" 
                  style={{ maxWidth: '300px', maxHeight: '300px', borderRadius: '8px', marginBottom: '8px' }}
                />
              </div>
            )}
            {msg.isPdf && msg.pdfName && (
              <div className="pdf-message">
                <div style={{ 
                  padding: '12px', 
                  backgroundColor: '#f5f5f5', 
                  borderRadius: '8px', 
                  marginBottom: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <FileTextOutlined style={{ fontSize: '16px', color: '#1890ff' }} />
                  <span>{msg.pdfName}</span>
                </div>
              </div>
            )}
            {isUser ? (
              <Text>{msg.content}</Text>
            ) : (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight, rehypeRaw]}
                components={{
                  p: ({ children }) => <Text>{children}</Text>,
                  strong: ({ children }) => <Text strong>{children}</Text>,
                  em: ({ children }) => <Text italic>{children}</Text>,
                  code: ({ children }) => <Text code>{children}</Text>,
                  ul: ({ children }) => <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>{children}</ul>,
                  li: ({ children }) => <li style={{ margin: '4px 0' }}>{children}</li>,
                }}
              >
                {msg.content}
              </ReactMarkdown>
            )}
            {msg.referencedDocuments && msg.referencedDocuments.length > 0 && (
              <div className="referenced-documents">
                <h4>参考文档：</h4>
                {msg.referencedDocuments.map((doc, index) => (
                  <div key={index} className="document-reference">
                    <a href={doc.url} target="_blank" rel="noopener noreferrer">
                      {doc.title}
                    </a>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="message-time">
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {msg.timestamp.toLocaleTimeString()}
            </Text>
          </div>
        </div>
      </div>
    );
  };

  // 设置菜单
  const settingsMenuItems: MenuProps['items'] = [
    {
      key: 'model',
      label: '模型设置',
      icon: <SettingOutlined />,
    },
    {
      key: 'history',
      label: '聊天记录',
      icon: <FileTextOutlined />,
    },
    {
      key: 'clear',
      label: '清空对话',
      icon: <MenuOutlined />,
    },
  ];

  return (
    <div className="ai-fullscreen">
      {/* 顶部工具栏 */}
      <div className="ai-fullscreen-header">
        <div className="header-left">
          <Avatar 
            icon={<RobotOutlined />} 
            style={{ backgroundColor: '#52c41a', marginRight: '12px' }} 
          />
          <div>
            <Title level={4} style={{ margin: 0, color: '#fff' }}>高小分</Title>
            <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: '12px' }}>AI学习助手</Text>
          </div>
        </div>
        <div className="header-right">
          <Space>
            <Dropdown menu={{ items: settingsMenuItems }} placement="bottomRight">
              <Button type="text" icon={<SettingOutlined />} style={{ color: '#fff' }} />
            </Dropdown>
            {onClose && (
              <Button 
                type="text" 
                icon={<FullscreenExitOutlined />} 
                onClick={onClose}
                style={{ color: '#fff' }}
              />
            )}
          </Space>
        </div>
      </div>

      {/* 主要内容区域 */}
      <div className="ai-fullscreen-content">
        {/* 消息区域 */}
        <div className="messages-area">
          <div className="messages-container">
            {messages.map(renderMessage)}
            {loading && (
              <div className="message assistant-message">
                <div className="message-avatar">
                  <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#52c41a' }} />
                </div>
                <div className="message-content">
                  <div className="message-body loading">
                    <Spin size="small" />
                    <Text style={{ marginLeft: '8px', color: '#666' }}>高小分正在思考...</Text>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* 输入区域 */}
        <div className="input-area">
          {/* 快捷操作 */}
          <div className="quick-actions">
            <Space wrap>
              {quickActions.map((action, index) => (
                <Button
                  key={index}
                  type="text"
                  icon={action.icon}
                  onClick={action.action}
                  className="quick-action-btn"
                >
                  {action.text}
                </Button>
              ))}
            </Space>
          </div>

          {/* 输入框区域 */}
          <div className="input-container">
            <div className="input-wrapper">
              <TextArea
                ref={textAreaRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="输入你的问题，按 Enter 发送，Shift + Enter 换行"
                autoSize={{ minRows: 3, maxRows: 10 }}
                className="message-input"
              />
              <div className="input-actions">
                <Space>
                  <Upload
                    beforeUpload={handleFileUpload}
                    showUploadList={false}
                    multiple={false}
                    accept="image/*"
                  >
                    <Button 
                      type="text" 
                      icon={<PictureOutlined />} 
                      className="action-btn"
                      loading={uploading}
                      title="上传图片"
                    />
                  </Upload>
                  <Upload
                    beforeUpload={handleFileUpload}
                    showUploadList={false}
                    multiple={false}
                    accept=".pdf"
                  >
                    <Button 
                      type="text" 
                      icon={<FileOutlined />} 
                      className="action-btn"
                      loading={uploading}
                      title="上传PDF文档"
                    />
                  </Upload>
                  <Button
                    type="primary"
                    icon={<SendOutlined />}
                    onClick={handleSendMessage}
                    loading={loading}
                    disabled={!inputValue.trim()}
                    className="send-btn"
                  >
                    发送
                  </Button>
                </Space>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIFullscreen;