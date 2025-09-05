import React, { useState, useEffect } from 'react';
import {
  Button,
  Space,
  Tooltip,
  ConfigProvider,
} from 'antd';
import {
  RobotOutlined,
  CloseOutlined,
} from '@ant-design/icons';
import AIAssistant from '../AIAssistant/AIAssistant';
import './AIDisplayManager.css';

export type AIDisplayMode = 'hidden' | 'modal';

interface AIDisplayManagerProps {
  children: React.ReactNode;
  defaultMode?: AIDisplayMode;
}

const AIDisplayManager: React.FC<AIDisplayManagerProps> = ({ 
  children, 
  defaultMode = 'hidden' 
}) => {
  const [displayMode, setDisplayMode] = useState<AIDisplayMode>(defaultMode);
  const [modalVisible, setModalVisible] = useState(false);
  const [hoverTriggerVisible, setHoverTriggerVisible] = useState(false);
  const [hoverTimeout, setHoverTimeout] = useState<NodeJS.Timeout | null>(null);

  // 处理显示模式切换
  const handleModeChange = (mode: AIDisplayMode) => {
    // 先关闭当前模式
    setModalVisible(false);
    
    // 设置新模式
    setDisplayMode(mode);
    
    // 根据新模式打开相应界面
    if (mode === 'modal') {
      setTimeout(() => setModalVisible(true), 100);
    }
  };

  // 处理鼠标悬停触发
  const handleHoverEnter = () => {
    if (displayMode === 'hidden') {
      if (hoverTimeout) {
        clearTimeout(hoverTimeout);
      }
      const timeout = setTimeout(() => {
        setHoverTriggerVisible(true);
        handleModeChange('modal');
      }, 300); // 300ms延迟，避免误触发
      setHoverTimeout(timeout);
    }
  };

  const handleHoverLeave = () => {
    if (hoverTimeout) {
      clearTimeout(hoverTimeout);
      setHoverTimeout(null);
    }
    setHoverTriggerVisible(false);
  };

  // 清理定时器
  useEffect(() => {
    return () => {
      if (hoverTimeout) {
        clearTimeout(hoverTimeout);
      }
    };
  }, [hoverTimeout]);

  // 键盘快捷键支持
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.altKey) {
        switch (e.key) {
          case '1':
            handleModeChange('hidden');
            break;
          case '2':
            handleModeChange('modal');
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  // 渲染AI组件
  const renderAIComponent = () => (
    <AIAssistant 
      visible={modalVisible}
      onClose={() => {
        setModalVisible(false);
        setDisplayMode('hidden');
      }}
    />
  );

  // 渲染模式切换按钮
  const renderModeButtons = () => (
    <Space className="ai-mode-buttons">
      <Tooltip title="隐藏AI助手 (Alt+1)">
        <Button 
          type={displayMode === 'hidden' ? 'primary' : 'default'}
          icon={<CloseOutlined />}
          onClick={() => handleModeChange('hidden')}
          size="small"
        />
      </Tooltip>
      <Tooltip title="AI助手 (Alt+2)">
        <Button 
          type={displayMode === 'modal' ? 'primary' : 'default'}
          icon={<RobotOutlined />}
          onClick={() => handleModeChange('modal')}
          size="small"
        />
      </Tooltip>
    </Space>
  );

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#52c41a',
          colorBgContainer: '#fafafa',
          borderRadius: 8,
        },
      }}
    >
      <div className="ai-display-manager">
        {/* 主内容区域 */}
        <div className="main-content full-width">
          {/* 主要内容 */}
          <div className="content-area">
            {children}
          </div>
        </div>

        {/* AI助手模态框 */}
        {renderAIComponent()}

        {/* 隐藏模式时的侧边触发区域和浮动按钮 */}
        {displayMode === 'hidden' && (
          <>
            {/* 侧边触发区域 */}
            <div 
              className="hover-trigger-area"
              onMouseEnter={handleHoverEnter}
              onMouseLeave={handleHoverLeave}
              style={{
                position: 'fixed',
                right: 0,
                top: '50%',
                transform: 'translateY(-50%)',
                width: '20px',
                height: '200px',
                zIndex: 1000,
                backgroundColor: 'transparent',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
              }}
            >
              <div 
                style={{
                  position: 'absolute',
                  right: 0,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  width: '4px',
                  height: '60px',
                  backgroundColor: hoverTriggerVisible ? 'var(--primary-color)' : 'rgba(74, 144, 226, 0.3)',
                  borderRadius: '4px 0 0 4px',
                  transition: 'all 0.3s ease',
                  opacity: hoverTriggerVisible ? 1 : 0.6,
                }}
              />
            </div>
            
            {/* 智能AI助手快速访问 */}
            <div className="ai-quick-access">
              <Tooltip title="点击唤醒AI助手" placement="left">
                <div 
                  className="ai-quick-btn"
                  onClick={() => handleModeChange('modal')}
                >
                  <RobotOutlined className="ai-icon" />
                  <div className="ai-pulse"></div>
                </div>
              </Tooltip>
            </div>
          </>
        )}
      </div>
    </ConfigProvider>
  );
};

export default AIDisplayManager;