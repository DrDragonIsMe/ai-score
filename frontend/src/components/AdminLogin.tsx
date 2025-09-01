import React from 'react';
import { Button, message } from 'antd';
import { useAuthStore } from '../stores/authStore';

/**
 * 临时管理员登录组件
 * 用于快速获取管理员权限以测试学科管理功能
 */
const AdminLogin: React.FC = () => {
  const { login } = useAuthStore();

  const handleAdminLogin = async () => {
    try {
      // 使用预设的管理员凭据登录
      await login({
        email: 'admin', // 后端使用username字段
        password: 'admin123'
      });
      message.success('管理员登录成功！');
    } catch (error) {
      console.error('管理员登录失败:', error);
      message.error('管理员登录失败，请检查后端服务是否正常运行');
    }
  };

  return (
    <div style={{ 
      position: 'fixed', 
      top: 20, 
      right: 20, 
      zIndex: 1000,
      background: '#fff',
      padding: '10px',
      border: '1px solid #d9d9d9',
      borderRadius: '6px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
    }}>
      <Button 
        type="primary" 
        size="small"
        onClick={handleAdminLogin}
        style={{ backgroundColor: '#ff4d4f', borderColor: '#ff4d4f' }}
      >
        管理员登录
      </Button>
      <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
        临时功能：快速获取管理员权限
      </div>
    </div>
  );
};

export default AdminLogin;