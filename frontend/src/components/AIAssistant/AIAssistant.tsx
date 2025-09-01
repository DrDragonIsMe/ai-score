import React, { useState, useRef, useEffect } from 'react';
import {
  Modal,
  Input,
  Button,
  Avatar,
  List,
  Upload,
  message,
  Spin,
  Card,
  Tabs,
  Space,
  Typography,
  Divider,
  Tag,
  Tooltip
} from 'antd';
import {
  SendOutlined,
  CameraOutlined,
  RobotOutlined,
  UserOutlined,
  PictureOutlined,
  BulbOutlined,
  BookOutlined,
  HeartOutlined,
  CloseOutlined
} from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';
import './AIAssistant.css';

const { TextArea } = Input;
const { Text, Title } = Typography;

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isImage?: boolean;
  imageUrl?: string;
  questionAnalysis?: {
    solution: string;
    explanation: string;
    keyPoints: string[];
    difficulty: string;
  };
}

interface AIAssistantProps {
  visible: boolean;
  onClose: () => void;
}

const AIAssistant: React.FC<AIAssistantProps> = ({ visible, onClose }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: '你好！我是高小分，你的AI学习助手。我可以帮你：\n\n📸 拍照识别试题并提供详细解析\n💡 回答学习问题和疑惑\n📚 制定个性化学习计划\n🎯 分析薄弱知识点\n\n有什么可以帮助你的吗？',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('chat');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 滚动到底部
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
      const response = await fetch('/api/ai-assistant/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputValue,
          context: messages.slice(-5) // 发送最近5条消息作为上下文
        })
      });

      const result = await response.json();

      if (result.success) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: result.data.response,
          timestamp: new Date()
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
        content: '抱歉，我现在遇到了一些问题，请稍后再试。如果问题持续存在，请联系技术支持。',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  // 处理图片上传
  const handleImageUpload = async (file: File) => {
    setLoading(true);

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
      const response = await fetch('/api/ai-assistant/recognize-image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_data: base64
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
          
          console.log('识别到题目:', questionText);
          
          const analysisMessage: Message = {
            id: (Date.now() + 1).toString(),
            type: 'assistant',
            content: `我识别到了以下题目：\n\n${questionText}\n\n让我为你分析这道题...`,
            timestamp: new Date()
          };
          setMessages(prev => [...prev, analysisMessage]);

          // 自动分析题目
          setTimeout(() => {
            analyzeQuestion(questionText);
          }, 1000);
        } else {
          // 不是题目，显示图片内容描述
          const description = result.description || '这张图片不包含题目内容。';
          
          console.log('图片内容描述:', description);
          
          const descriptionMessage: Message = {
            id: (Date.now() + 1).toString(),
            type: 'assistant',
            content: description,
            timestamp: new Date()
          };
          setMessages(prev => [...prev, descriptionMessage]);
        }
      } else {
        throw new Error(result.message || '图片识别失败');
      }
    } catch (error) {
      console.error('图片上传失败:', error);
      message.error('图片识别失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 分析题目
  const analyzeQuestion = async (questionText: string, userAnswer?: string) => {
    setLoading(true);

    // 参数验证
    if (!questionText || !questionText.trim()) {
      console.error('题目文本为空:', questionText);
      message.error('题目文本不能为空');
      setLoading(false);
      return;
    }

    console.log('开始分析题目:', questionText);

    try {
      const response = await fetch('/api/ai-assistant/analyze-question', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question_text: questionText,
          user_answer: userAnswer
        })
      });

      const result = await response.json();

      if (result.success) {
        const analysis = result.data.analysis;
        const analysisMessage: Message = {
          id: (Date.now() + 2).toString(),
          type: 'assistant',
          content: analysis.detailed_solution,
          timestamp: new Date(),
          questionAnalysis: {
            solution: analysis.detailed_solution,
            explanation: analysis.explanation,
            keyPoints: analysis.key_points || [],
            difficulty: analysis.difficulty || '中等'
          }
        };
        setMessages(prev => [...prev, analysisMessage]);
      } else {
        throw new Error(result.message || '题目分析失败');
      }
    } catch (error) {
      console.error('题目分析失败:', error);
      message.error('题目分析失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 快速帮助功能
  const handleQuickHelp = async (helpType: string) => {
    setLoading(true);

    const helpMessages = {
      study_plan: '请为我制定一个学习计划',
      weak_points: '帮我分析一下薄弱知识点',
      motivation: '给我一些学习动力和鼓励'
    };

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: helpMessages[helpType as keyof typeof helpMessages],
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      console.log('发送快速帮助请求:', helpType);
      const response = await fetch('/api/ai-assistant/quick-help', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          help_type: helpType
        })
      });

      console.log('响应状态:', response.status, response.statusText);
      console.log('响应头:', Object.fromEntries(response.headers.entries()));
      
      if (!response.ok) {
        console.error('响应不正常:', response.status, response.statusText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const text = await response.text();
      if (!text) {
        throw new Error('Empty response from server');
      }

      let result;
      try {
        result = JSON.parse(text);
      } catch (parseError) {
        console.error('JSON parse error:', parseError, 'Response text:', text);
        throw new Error('Invalid JSON response from server');
      }

      if (result.success) {
        let helpContent = result.data.help_content;
        
        // 如果返回的是对象，格式化为字符串
        if (typeof helpContent === 'object' && helpContent !== null) {
          if (result.data.type === 'study_plan') {
            helpContent = `📚 个性化学习计划\n\n🌅 上午：${helpContent.morning}\n\n🌞 下午：${helpContent.afternoon}\n\n🌙 晚上：${helpContent.evening}\n\n⏰ 建议时长：${helpContent.duration}`;
          } else {
            helpContent = JSON.stringify(helpContent, null, 2);
          }
        }
        
        const helpMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: helpContent,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, helpMessage]);
      } else {
        throw new Error(result.message || '获取帮助失败');
      }
    } catch (error) {
      console.error('快速帮助失败:', error);
      message.error('获取帮助失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 渲染消息
  const renderMessage = (msg: Message) => {
    const isUser = msg.type === 'user';
    
    return (
      <div key={msg.id} className={`message ${isUser ? 'user-message' : 'assistant-message'}`}>
        <div className="message-avatar">
          <Avatar 
            icon={isUser ? <UserOutlined /> : <RobotOutlined />} 
            style={{ backgroundColor: isUser ? '#1890ff' : '#52c41a' }}
          />
        </div>
        <div className="message-content">
          <div className="message-header">
            <Text strong>{isUser ? '你' : '高小分'}</Text>
            <Text type="secondary" style={{ fontSize: '12px', marginLeft: '8px' }}>
              {msg.timestamp.toLocaleTimeString()}
            </Text>
          </div>
          <div className="message-body">
            {msg.isImage && msg.imageUrl ? (
              <div className="image-message">
                <img src={msg.imageUrl} alt="上传的图片" style={{ maxWidth: '200px', borderRadius: '8px' }} />
                <Text>{msg.content}</Text>
              </div>
            ) : (
              <div className="text-message">
                <Text style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</Text>
                {msg.questionAnalysis && (
                  <Card size="small" style={{ marginTop: '8px' }}>
                    <Space direction="vertical" size="small" style={{ width: '100%' }}>
                      <div>
                        <Text strong>难度等级：</Text>
                        <Tag color={msg.questionAnalysis.difficulty === '简单' ? 'green' : 
                                   msg.questionAnalysis.difficulty === '困难' ? 'red' : 'orange'}>
                          {msg.questionAnalysis.difficulty}
                        </Tag>
                      </div>
                      {msg.questionAnalysis.keyPoints.length > 0 && (
                        <div>
                          <Text strong>关键知识点：</Text>
                          <div style={{ marginTop: '4px' }}>
                            {msg.questionAnalysis.keyPoints.map((point, index) => (
                              <Tag key={index} color="blue" style={{ marginBottom: '4px' }}>
                                {point}
                              </Tag>
                            ))}
                          </div>
                        </div>
                      )}
                    </Space>
                  </Card>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#52c41a', marginRight: '8px' }} />
          <span>高小分 - AI学习助手</span>
        </div>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={800}
      height={600}
      className="ai-assistant-modal"
      closeIcon={<CloseOutlined />}
    >
      <div className="ai-assistant-container">
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          items={[
            {
              key: 'chat',
              label: '智能对话',
              children: (
                <div className="chat-container">
                  <div className="messages-container">
                    {messages.map(renderMessage)}
                    {loading && (
                      <div className="loading-message">
                        <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#52c41a' }} />
                        <div className="loading-content">
                          <Spin size="small" />
                          <Text style={{ marginLeft: '8px' }}>高小分正在思考...</Text>
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>
                  
                  <div className="input-container">
                    <div className="quick-actions">
                      <Space>
                        <Tooltip title="制定学习计划">
                          <Button 
                            size="small" 
                            icon={<BookOutlined />}
                            onClick={() => handleQuickHelp('study_plan')}
                          >
                            学习计划
                          </Button>
                        </Tooltip>
                        <Tooltip title="分析薄弱点">
                          <Button 
                            size="small" 
                            icon={<BulbOutlined />}
                            onClick={() => handleQuickHelp('weak_points')}
                          >
                            薄弱分析
                          </Button>
                        </Tooltip>
                        <Tooltip title="学习鼓励">
                          <Button 
                            size="small" 
                            icon={<HeartOutlined />}
                            onClick={() => handleQuickHelp('motivation')}
                          >
                            加油鼓励
                          </Button>
                        </Tooltip>
                      </Space>
                    </div>
                    
                    <div className="message-input">
                      <TextArea
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="输入你的问题，或点击相机图标拍照识别题目..."
                        autoSize={{ minRows: 1, maxRows: 4 }}
                        onPressEnter={(e) => {
                          if (!e.shiftKey) {
                            e.preventDefault();
                            handleSendMessage();
                          }
                        }}
                      />
                      <div className="input-actions">
                        <input
                          ref={fileInputRef}
                          type="file"
                          accept="image/*"
                          style={{ display: 'none' }}
                          onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) {
                              handleImageUpload(file);
                            }
                          }}
                        />
                        <Button
                          type="text"
                          icon={<CameraOutlined />}
                          onClick={() => fileInputRef.current?.click()}
                          disabled={loading}
                        />
                        <Button
                          type="primary"
                          icon={<SendOutlined />}
                          onClick={handleSendMessage}
                          disabled={loading || !inputValue.trim()}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )
            },
            {
              key: 'recommendations',
              label: '学习建议',
              children: (
                <div className="recommendations-container">
                  <Card>
                    <Title level={4}>个性化学习建议</Title>
                    <Text type="secondary">
                      基于你的学习情况，高小分为你准备了专属的学习建议。
                    </Text>
                    <Divider />
                    <Button 
                      type="primary" 
                      block 
                      onClick={() => handleQuickHelp('study_plan')}
                      loading={loading}
                    >
                      获取学习建议
                    </Button>
                  </Card>
                </div>
              )
            }
          ]}
        />
      </div>
    </Modal>
  );
};

export default AIAssistant;