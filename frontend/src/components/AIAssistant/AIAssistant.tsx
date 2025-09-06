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
  Tooltip,
  Row,
  Col,
  Statistic
} from 'antd';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeHighlight from 'rehype-highlight';
import rehypeRaw from 'rehype-raw';
import 'katex/dist/katex.min.css';
import {
  SendOutlined,
  CameraOutlined,
  RobotOutlined,
  UserOutlined,
  PictureOutlined,
  BulbOutlined,
  BookOutlined,
  HeartOutlined,
  CloseOutlined,
  SearchOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  PaperClipOutlined,
  FileAddOutlined,
  PartitionOutlined
} from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';
import { useAIAssistantStore } from '../../stores/aiAssistantStore';
import type { Message } from '../../stores/aiAssistantStore';
import CameraCapture from './CameraCapture';
import PPTTemplateSelector from '../PPTTemplateSelector/PPTTemplateSelector';
import KnowledgeGraphEditor from '../KnowledgeGraphEditor/KnowledgeGraphEditor';
import './AIAssistant.css';

const { TextArea } = Input;
const { Text, Title } = Typography;

interface AIAssistantProps {
  visible: boolean;
  onClose: () => void;
}

const AIAssistant: React.FC<AIAssistantProps> = ({ visible, onClose }) => {
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
  
  const [activeTab, setActiveTab] = useState('chat');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const [showKnowledgeGraphEditor, setShowKnowledgeGraphEditor] = useState(false);
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
        },
        body: JSON.stringify({
          message: inputValue,
          context: messages.slice(-5).map(msg => ({
            type: msg.type,
            content: msg.content,
            timestamp: msg.timestamp.toISOString()
          })),
          template_id: selectedTemplateId
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
        content: '抱歉，我现在遇到了一些问题，请稍后再试。如果问题持续存在，请联系技术支持。',
        timestamp: new Date()
      };
      addMessage(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // 处理PPT模板选择
  const handleTemplateSelect = (templateId: number, templateName: string) => {
    setSelectedTemplate(templateId, templateName);
    message.success(`已选择模板：${templateName}`);
  };

  // 生成PPT
  const handleGeneratePPT = async () => {
    if (!inputValue.trim()) {
      message.warning('请输入PPT内容描述');
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: `生成PPT：${inputValue}${selectedTemplateName ? ` (使用模板：${selectedTemplateName})` : ''}`,
      timestamp: new Date()
    };

    addMessage(userMessage);
    setInputValue('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:5001/api/ai-assistant/generate-ppt', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: inputValue,
          template_id: selectedTemplateId
        })
      });

      const result = await response.json();

      if (result.success) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: result.data.message || 'PPT生成成功！',
          timestamp: new Date()
        };
        addMessage(assistantMessage);
      } else {
        throw new Error(result.message || 'PPT生成失败');
      }
    } catch (error) {
      console.error('PPT生成失败:', error);
      message.error('PPT生成失败，请重试');
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
          <div className="message-body">
            {isUser ? (
              <Text>{msg.content}</Text>
            ) : (
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

  // AI统计卡片
  const renderAIStatsCard = () => (
    <Card 
      title="AI互动统计" 
      size="small" 
      style={{ marginBottom: 16 }}
      extra={<RobotOutlined style={{ color: '#1890ff' }} />}
    >
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Statistic 
            title="今日互动" 
            value={aiStats.todayInteractions} 
            suffix="次"
            valueStyle={{ color: '#1890ff', fontSize: '16px' }}
          />
        </Col>
        <Col span={12}>
          <Statistic 
            title="总互动" 
            value={aiStats.totalInteractions} 
            suffix="次"
            valueStyle={{ color: '#52c41a', fontSize: '16px' }}
          />
        </Col>
        <Col span={12}>
          <Statistic 
            title="问题解答" 
            value={aiStats.questionsAnswered} 
            suffix="个"
            valueStyle={{ color: '#722ed1', fontSize: '16px' }}
          />
        </Col>
        <Col span={12}>
          <Statistic 
            title="AI准确率" 
            value={aiStats.aiAccuracy} 
            suffix="%"
            valueStyle={{ color: '#fa8c16', fontSize: '16px' }}
          />
        </Col>
      </Row>
    </Card>
  );

  const tabItems = [
    {
      key: 'chat',
      label: (
        <span>
          <RobotOutlined />
          AI对话
        </span>
      ),
      children: (
        <div className="chat-container">
          {/* AI统计卡片 */}
          {renderAIStatsCard()}
          
          {/* 消息列表 */}
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

          {/* 快捷操作 */}
          <div className="quick-actions">
            <Space wrap>
              <Button 
                type="text" 
                icon={<PictureOutlined />} 
                size="small"
                onClick={() => fileInputRef.current?.click()}
              >
                图片上传
              </Button>
              <Button 
                type="text" 
                icon={<FilePdfOutlined />} 
                size="small"
                onClick={() => pdfInputRef.current?.click()}
              >
                PDF上传
              </Button>
              <Button 
                type="text" 
                icon={<CameraOutlined />} 
                size="small"
                onClick={() => setShowCamera(true)}
              >
                拍照
              </Button>
              <Button 
                type="text" 
                icon={<FileTextOutlined />} 
                size="small"
                onClick={() => setShowPPTTemplateSelector(true)}
              >
                PPT模板
              </Button>
              <Button 
                type="text" 
                icon={<PartitionOutlined />} 
                size="small"
                onClick={() => setShowKnowledgeGraphEditor(true)}
              >
                知识图谱
              </Button>
              <Button 
                type="primary" 
                icon={<FileAddOutlined />} 
                size="small"
                onClick={handleGeneratePPT}
                disabled={!inputValue.trim()}
              >
                生成PPT
              </Button>
            </Space>
          </div>

          {/* 输入区域 */}
          <div className="input-container">
            <TextArea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="输入您的问题...（按 Enter 发送，Shift+Enter 换行）"
              autoSize={{ minRows: 2, maxRows: 6 }}
              disabled={loading}
            />
            <div className="send-button">
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSendMessage}
                disabled={loading || !inputValue.trim()}
                loading={loading}
              >
                发送
              </Button>
            </div>
          </div>
        </div>
      ),
    },
    {
      key: 'search',
      label: (
        <span>
          <SearchOutlined />
          文档搜索
        </span>
      ),
      children: (
        <div className="search-container">
          <div className="search-input">
            <Input.Search
              placeholder="搜索文档内容..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              loading={searchLoading}
              enterButton="搜索"
            />
          </div>
          <div className="search-results">
            {searchResults.length > 0 ? (
              <List
                dataSource={searchResults}
                renderItem={(item: any) => (
                  <List.Item>
                    <List.Item.Meta
                      title={item.title}
                      description={item.content}
                    />
                  </List.Item>
                )}
              />
            ) : (
              <div className="no-results">
                <Text type="secondary">暂无搜索结果</Text>
              </div>
            )}
          </div>
        </div>
      ),
    },
  ];

  return (
    <>
      <Modal
        title={
          <div className="modal-header">
            <div className="header-left">
              <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#52c41a', marginRight: 8 }} />
              <div>
                <Title level={4} style={{ margin: 0 }}>高小分AI助手</Title>
                {selectedTemplateName && (
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    已选择模板：{selectedTemplateName}
                  </Text>
                )}
              </div>
            </div>
            <Button 
              type="text" 
              icon={<CloseOutlined />} 
              onClick={onClose}
            />
          </div>
        }
        open={visible}
        onCancel={onClose}
        footer={null}
        width={800}
        height={600}
        className="ai-assistant-modal"
        destroyOnClose
      >
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab} 
          items={tabItems}
          className="ai-assistant-tabs"
        />
      </Modal>

      {/* 隐藏的文件输入 */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        style={{ display: 'none' }}
      />
      <input
        ref={pdfInputRef}
        type="file"
        accept=".pdf"
        style={{ display: 'none' }}
      />

      {/* 相机组件 */}
      <CameraCapture
        visible={showCamera}
        onClose={() => setShowCamera(false)}
        onCapture={(imageData) => {
          console.log('Captured image:', imageData);
          setShowCamera(false);
        }}
      />

      {/* PPT模板选择器 */}
      <PPTTemplateSelector
        visible={showPPTTemplateSelector}
        onClose={() => setShowPPTTemplateSelector(false)}
        onSelect={handleTemplateSelect}
        selectedTemplateId={selectedTemplateId}
      />

      {/* 知识图谱编辑器 */}
      <KnowledgeGraphEditor
        visible={showKnowledgeGraphEditor}
        onClose={() => setShowKnowledgeGraphEditor(false)}
        onSuccess={(knowledgeGraph) => {
          // 从节点中提取标签
          const nodeTags: string[] = [];
          if (knowledgeGraph.knowledge_graph?.nodes) {
            knowledgeGraph.knowledge_graph.nodes.forEach((node: any) => {
              if (node.tags && Array.isArray(node.tags)) {
                nodeTags.push(...node.tags);
              }
            });
          }
          // 去重
          const uniqueTags = [...new Set(nodeTags)];
          
          // 将知识图谱结果添加到聊天中
          const assistantMessage: Message = {
            id: Date.now().toString(),
            type: 'assistant',
            content: `已成功生成知识图谱！\n\n**学科**: ${knowledgeGraph.subject_id}\n**内容**: ${knowledgeGraph.content}\n**标签**: ${uniqueTags.join(', ') || '无'}\n\n知识图谱包含 ${knowledgeGraph.knowledge_graph?.nodes?.length || 0} 个节点和 ${knowledgeGraph.knowledge_graph?.edges?.length || 0} 个连接。`,
            timestamp: new Date()
          };
          addMessage(assistantMessage);
          setShowKnowledgeGraphEditor(false);
        }}
      />
    </>
  );
};

export default AIAssistant;