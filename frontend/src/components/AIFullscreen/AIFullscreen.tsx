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
  Modal,
  Select,
  Form,
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
  FileAddOutlined,
  UploadOutlined,
  CloudUploadOutlined,
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

interface PPTTemplate {
  id: number;
  name: string;
  category: string;
  preview?: string;
  description: string;
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
  const [showPPTTemplateModal, setShowPPTTemplateModal] = useState(false);
  const [pptTemplates, setPptTemplates] = useState<PPTTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<PPTTemplate | null>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadForm, setUploadForm] = useState({ name: '', category: '', file: null as File | null });
  const [uploadLoading, setUploadLoading] = useState(false);
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

  // 处理PPT模板选择
  const handlePPTTemplateSelection = () => {
    setShowPPTTemplateModal(true);
    // 这里可以加载PPT模板数据
    setPptTemplates([
      { id: 1, name: '学习总结模板', category: '学术类', description: '适用于知识点总结和学习回顾' },
      { id: 2, name: '课程展示模板', category: '教育类', description: '适用于课程内容展示' },
      { id: 3, name: '项目汇报模板', category: '商务类', description: '适用于项目成果展示' }
    ]);
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

  // 快捷操作
  const quickActions = [
    { icon: <BulbOutlined />, text: '学习建议', action: () => setInputValue('给我一些学习建议') },
    { icon: <ThunderboltOutlined />, text: '知识点总结', action: () => setInputValue('帮我总结重要知识点') },
    { icon: <StarOutlined />, text: '制定计划', action: () => setInputValue('帮我制定学习计划') },
    { icon: <FileTextOutlined />, text: 'PPT模板', action: () => handlePPTTemplateSelection() },
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

      {/* PPT模板选择弹窗 */}
      <Modal
        title={
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <div style={{
                width: '24px',
                height: '24px',
                background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <FileTextOutlined style={{ fontSize: '12px', color: 'white' }} />
              </div>
              <span style={{ 
                fontSize: '14px', 
                fontWeight: 500, 
                color: '#262626'
              }}>
                选择PPT模板
              </span>
            </div>
            <Button 
              type="primary" 
              icon={<UploadOutlined />} 
              size="small"
              onClick={() => setShowUploadModal(true)}
            >
              上传模板
            </Button>
          </div>
        }
        open={showPPTTemplateModal}
        onCancel={() => setShowPPTTemplateModal(false)}
        onOk={() => {
          if (selectedTemplate) {
            setInputValue(`请帮我使用"${selectedTemplate.name}"创建一个PPT`);
            setShowPPTTemplateModal(false);
            setSelectedTemplate(null);
          }
        }}
        okText={selectedTemplate ? '应用模板' : '请选择模板'}
        cancelText="取消"
        width={800}
        okButtonProps={{
          disabled: !selectedTemplate
        }}
      >
        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
          {/* 按分类显示模板 */}
          {Object.entries(
            pptTemplates.reduce((groups, template) => {
              const category = template.category || '其他';
              if (!groups[category]) groups[category] = [];
              groups[category].push(template);
              return groups;
            }, {} as Record<string, PPTTemplate[]>)
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
                  {templates.map((template: PPTTemplate) => {
                    const isSelected = selectedTemplate?.id === template.id;
                    return (
                      <Card
                        key={template.id}
                        size="small"
                        hoverable
                        style={{
                          border: isSelected ? `2px solid ${categoryColors[category]}` : '1px solid #f0f0f0',
                          borderRadius: '8px',
                          cursor: 'pointer',
                          transition: 'all 0.3s ease'
                        }}
                        onClick={() => setSelectedTemplate(template)}
                      >
                        <Card.Meta
                          title={template.name}
                          description={template.description}
                        />
                      </Card>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </Modal>

      {/* 上传模板弹窗 */}
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
             >
               <Select.Option value="学术类">
                 <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                   <span style={{ color: '#1890ff' }}>📚</span>
                   学术类
                 </div>
               </Select.Option>
               <Select.Option value="教育类">
                 <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                   <span style={{ color: '#52c41a' }}>🎓</span>
                   教育类
                 </div>
               </Select.Option>
               <Select.Option value="商务类">
                 <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                   <span style={{ color: '#fa8c16' }}>💼</span>
                   商务类
                 </div>
               </Select.Option>
               <Select.Option value="创意类">
                 <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                   <span style={{ color: '#eb2f96' }}>🎨</span>
                   创意类
                 </div>
               </Select.Option>
               <Select.Option value="其他">
                 <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                   <span style={{ color: '#722ed1' }}>📋</span>
                   其他
                 </div>
               </Select.Option>
             </Select>
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
                 <CloudUploadOutlined style={{ color: '#1890ff' }} />
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

export default AIFullscreen;