// 自动登录脚本
// 在浏览器控制台中运行此脚本来自动登录

(async function autoLogin() {
    console.log('开始自动登录...');
    
    try {
        // 1. 发送登录请求
        const loginResponse = await fetch('http://localhost:5001/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: 'admin',
                password: 'admin123'
            })
        });
        
        if (!loginResponse.ok) {
            throw new Error(`登录请求失败: ${loginResponse.status}`);
        }
        
        const loginData = await loginResponse.json();
        
        if (loginData.success && loginData.data.access_token) {
            // 2. 保存token到localStorage
            localStorage.setItem('token', loginData.data.access_token);
            localStorage.setItem('user', JSON.stringify(loginData.data.user));
            
            console.log('登录成功！Token已保存到localStorage');
            console.log('用户信息:', loginData.data.user);
            
            // 3. 跳转到学习分析页面
            window.location.href = '/analytics';
            
        } else {
            console.error('登录失败:', loginData.message);
        }
        
    } catch (error) {
        console.error('自动登录出错:', error);
    }
})();

// 使用说明:
// 1. 打开浏览器访问 http://localhost:5173/login
// 2. 按F12打开开发者工具
// 3. 在控制台中粘贴并运行此脚本
// 4. 脚本会自动登录并跳转到学习分析页面