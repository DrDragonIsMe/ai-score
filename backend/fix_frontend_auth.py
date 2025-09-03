#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前端认证问题修复脚本
自动登录并测试学习分析页面访问
"""

import requests
import json
import time

def test_api_login():
    """测试API登录"""
    print("=== 测试API登录 ===")
    
    login_url = "http://localhost:5001/api/auth/login"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        print(f"登录响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print(f"获取到token: {token[:50]}...")
            return token
        else:
            print(f"登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"API登录错误: {e}")
        return None

def test_dashboard_api(token):
    """测试仪表板API"""
    print("\n=== 测试仪表板API ===")
    
    dashboard_url = "http://localhost:5001/api/learning-analytics/dashboard-summary"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(dashboard_url, headers=headers)
        print(f"仪表板API响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"仪表板数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"仪表板API失败: {response.text}")
            return False
    except Exception as e:
        print(f"仪表板API错误: {e}")
        return False

def print_manual_steps():
    """打印手动修复步骤"""
    print("=== 手动修复前端认证问题 ===")
    print("请按照以下步骤操作:")
    print("1. 打开浏览器访问: http://localhost:5173/login")
    print("2. 使用以下凭据登录:")
    print("   用户名: admin")
    print("   密码: admin123")
    print("3. 登录成功后，访问: http://localhost:5173/analytics")
    print("4. 检查学习分析页面是否正常显示数据")
    print("\n如果仍然出现错误，请检查:")
    print("- 浏览器控制台是否有错误信息")
    print("- 网络标签页中API请求的状态")
    print("- localStorage中是否有有效的token")
    print("\n按Ctrl+Shift+I打开开发者工具进行检查")
    
def clear_browser_data():
    """提供清除浏览器数据的指导"""
    print("\n=== 清除浏览器数据 ===")
    print("如果问题持续存在，请尝试清除浏览器数据:")
    print("1. 在Chrome中按F12打开开发者工具")
    print("2. 右键点击刷新按钮，选择'清空缓存并硬性重新加载'")
    print("3. 或者在Application标签页中清除localStorage和sessionStorage")
    print("4. 重新登录系统")

def main():
    """主函数"""
    print("开始前端认证问题诊断和修复...\n")
    
    # 1. 测试API登录
    token = test_api_login()
    
    if token:
        # 2. 测试仪表板API
        api_success = test_dashboard_api(token)
        
        if api_success:
            print("\n后端API工作正常，问题在前端认证")
            
            # 3. 提供手动修复步骤
            print_manual_steps()
            clear_browser_data()
        else:
            print("\n后端API有问题，需要先修复后端")
    else:
        print("\n无法获取token，后端登录有问题")
    
    print("\n=== 修复完成 ===")
    print("请检查浏览器中的学习分析页面是否正常显示数据")

if __name__ == "__main__":
    main()