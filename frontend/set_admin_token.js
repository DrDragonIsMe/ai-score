// 在浏览器控制台中运行此脚本来设置管理员token
// 这是一个临时解决方案，用于快速测试管理员功能

// 管理员token（从后端获取）
const adminToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc1Njc0NDE0NCwianRpIjoiZjY0YTQ5YTMtNDYyNS00Y2EwLTk1ZDctMzA4MGRiMDFjNTg2IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6eyJ1c2VyX2lkIjoiYzBhNzUwZTMtNzk5Zi00ZTNlLWI5MDctMjA4NGUwMjNiZDI4IiwidGVuYW50X2lkIjoiN2YyNmVlZWEtNjFkMC00MDQ5LTgxYjktNGM4NmViMTc3OGVlIiwicm9sZSI6ImFkbWluIn0sIm5iZiI6MTc1Njc0NDE0NCwiZXhwIjoxNzU2ODMwNTQ0fQ.bVcqfxw9dblnX39svAvZMhLIKZx3p-tmonKcQx546zM';

// 管理员用户信息
const adminUser = {
  id: 'c0a750e3-799f-4e3e-b907-2084e023bd28',
  username: 'admin',
  email: 'admin@example.com',
  role: 'admin',
  tenant_id: '7f26eeea-61d0-4049-81b9-4c86eb1778ee'
};

// 设置localStorage中的token
localStorage.setItem('token', adminToken);

// 设置zustand存储的认证状态
const authStorage = {
  state: {
    user: adminUser,
    token: adminToken,
    isAuthenticated: true
  },
  version: 0
};

localStorage.setItem('auth-storage', JSON.stringify(authStorage));

console.log('管理员token已设置！');
console.log('请刷新页面以应用更改。');
console.log('管理员信息:', adminUser);

// 提示用户刷新页面
alert('管理员token已设置！请刷新页面以应用更改。');