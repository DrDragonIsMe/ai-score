import React, { useState, useEffect } from 'react';
import {
  Button,
  Drawer,
  Modal,
  Space,
  Tooltip,
  ConfigProvider,
} from 'antd';
import {
  RobotOutlined,
  ExpandOutlined,
  CompressOutlined,
  MenuOutlined,
  CloseOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined,
} from '@ant-design/icons';
import AISidebar from '../AISidebar/AISidebar';
import './AIDisplayManager.css';

export type AIDisplayMode = 'hidden' | 'sidebar' | 'drawer' | 'fullscreen';

interface AIDisplayManagerProps {
  children: React.ReactNode;
  defaultMode?: AIDisplayMode;
}

const AIDisplayManager: React.FC<AIDisplayManagerProps> = ({ 
  children, 
  defaultMode = 'hidden' 
}) => {
  const [displayMode, setDisplayMode] = useState<AIDisplayMode>(defaultMode);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [fullscreenVisible, setFullscreenVisible] = useState(false);
  const [aiSidebarCollapsed, setAiSidebarCollapsed] = useState(false);
  const [hoverTriggerVisible, setHoverTriggerVisible] = useState(false);
  const [hoverTimeout, setHoverTimeout] = useState<NodeJS.Timeout | null>(null);

  // 处理显示模式切换
  const handleModeChange = (mode: AIDisplayMode) => {
    // 先关闭当前模式
    setDrawerVisible(false);
    setFullscreenVisible(false);
    
    // 设置新模式
    setDisplayMode(mode);
    
    // 根据新模式打开相应界面
    if (mode === 'drawer') {
      setTimeout(() => setDrawerVisible(true), 100);
    } else if (mode === 'fullscreen') {
      setTimeout(() => setFullscreenVisible(true), 100);
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
        handleModeChange('drawer');
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
            handleModeChange('sidebar');
            break;
          case '3':
            handleModeChange('drawer');
            break;
          case '4':
            handleModeChange('fullscreen');
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  // 渲染AI组件
  const renderAIComponent = (className?: string) => (
    <div className={className}>
      <AISidebar 
        collapsed={aiSidebarCollapsed} 
        onToggleCollapse={() => setAiSidebarCollapsed(!aiSidebarCollapsed)}
        displayMode={displayMode}
        onModeChange={handleModeChange}
      />
    </div>
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
      <Tooltip title="侧边栏模式 (Alt+2)">
        <Button 
          type={displayMode === 'sidebar' ? 'primary' : 'default'}
          icon={<MenuOutlined />}
          onClick={() => handleModeChange('sidebar')}
          size="small"
        />
      </Tooltip>
      <Tooltip title="抽屉模式 (Alt+3)">
        <Button 
          type={displayMode === 'drawer' ? 'primary' : 'default'}
          icon={<ExpandOutlined />}
          onClick={() => handleModeChange('drawer')}
          size="small"
        />
      </Tooltip>
      <Tooltip title="全屏模式 (Alt+4)">
        <Button 
          type={displayMode === 'fullscreen' ? 'primary' : 'default'}
          icon={<FullscreenOutlined />}
          onClick={() => handleModeChange('fullscreen')}
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
        <div className={`main-content ${displayMode === 'sidebar' ? 'with-sidebar' : 'full-width'}`}>
          {/* 侧边栏模式 */}
          {displayMode === 'sidebar' && (
            <div className="ai-sidebar-container">
              {renderAIComponent('ai-sidebar-mode')}
            </div>
          )}
          
          {/* 主要内容 */}
          <div className="content-area">
            {children}
          </div>
        </div>

        {/* 抽屉模式 */}
        <Drawer
          title="AI智能助手"
          placement="right"
          width={400}
          open={drawerVisible}
          onClose={() => {
            setDrawerVisible(false);
            setDisplayMode('hidden');
          }}
          className="ai-drawer"
          extra={
            <Space>
              <Tooltip title="切换到全屏模式">
                <Button 
                  type="text" 
                  icon={<FullscreenOutlined />} 
                  onClick={() => handleModeChange('fullscreen')}
                />
              </Tooltip>
            </Space>
          }
        >
          {renderAIComponent('ai-drawer-mode')}
        </Drawer>

        {/* 全屏模式 */}
        <Modal
          title="AI智能助手 - 全屏模式"
          open={fullscreenVisible}
          onCancel={() => {
            setFullscreenVisible(false);
            setDisplayMode('hidden');
          }}
          footer={null}
          width="100vw"
          style={{ top: 0, paddingBottom: 0 }}
          styles={{ body: { height: 'calc(100vh - 55px)', padding: 0 } }}
          className="ai-fullscreen-modal"
        >
          {renderAIComponent('ai-fullscreen-mode')}
        </Modal>

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
                  onClick={() => handleModeChange('drawer')}
                >
                  <RobotOutlined className="ai-icon" />
                  <div className="ai-pulse"></div>
                </div>
              </Tooltip>
              
              {/* 模式选择菜单 */}
              <div className="ai-mode-menu">
                <Tooltip title="侧边栏模式" placement="left">
                  <Button 
                    type="text" 
                    icon={<MenuOutlined />}
                    onClick={() => handleModeChange('sidebar')}
                    className="mode-menu-btn"
                  />
                </Tooltip>
                <Tooltip title="抽屉模式" placement="left">
                  <Button 
                    type="text" 
                    icon={<ExpandOutlined />}
                    onClick={() => handleModeChange('drawer')}
                    className="mode-menu-btn"
                  />
                </Tooltip>
                <Tooltip title="全屏模式" placement="left">
                  <Button 
                    type="text" 
                    icon={<FullscreenOutlined />}
                    onClick={() => handleModeChange('fullscreen')}
                    className="mode-menu-btn"
                  />
                </Tooltip>
              </div>
            </div>
          </>
        )}
      </div>
    </ConfigProvider>
  );
};

export default AIDisplayManager;