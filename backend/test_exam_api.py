#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试考试API接口
"""

import requests
import json

# API基础URL
BASE_URL = 'http://127.0.0.1:5001'

# 全局变量存储token
auth_token = None

def get_auth_token():
    """获取认证token"""
    global auth_token
    
    # 先尝试注册用户
    register_url = f'{BASE_URL}/api/auth/register'
    register_data = {
        'email': 'test@example.com',
        'password': 'Test123456!',
        'username': 'testuser',
        'tenant_name': 'test_tenant'
    }
    
    try:
        response = requests.post(register_url, json=register_data)
        print(f"注册用户 - 状态码: {response.status_code}")
        if response.status_code not in [200, 409]:  # 409表示用户已存在
            print(f"注册失败: {response.text}")
    except Exception as e:
        print(f"注册请求失败: {str(e)}")
    
    # 登录获取token
    login_url = f'{BASE_URL}/api/auth/login'
    login_data = {
        'email': 'test@example.com',
        'password': 'Test123456!'
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        print(f"用户登录 - 状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            auth_token = result.get('data', {}).get('access_token')
            print(f"获取到token: {auth_token[:20]}..." if auth_token else "未获取到token")
            return auth_token
        else:
            print(f"登录失败: {response.text}")
    except Exception as e:
        print(f"登录请求失败: {str(e)}")
    
    return None

def get_auth_headers():
    """获取认证头"""
    if auth_token:
        return {'Authorization': f'Bearer {auth_token}'}
    return {}

def test_create_exam_session():
    """测试创建考试会话"""
    # 确保有认证token
    if not auth_token:
        get_auth_token()
    
    url = f'{BASE_URL}/api/exam/sessions'
    data = {
        'exam_name': '数学练习测试',
        'exam_type': 'practice',
        'subject_id': 1,
        'total_questions': 10,
        'total_time_minutes': 30,
        'difficulty_level': 'medium'
    }
    
    try:
        headers = {'Content-Type': 'application/json'}
        headers.update(get_auth_headers())
        response = requests.post(url, json=data, headers=headers)
        print(f"创建考试会话 - 状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            return result.get('data', {}).get('session_id')
        return None
    except Exception as e:
        print(f"请求失败: {str(e)}")
        return None

def test_start_exam():
    """测试开始考试"""
    # 确保有认证token
    if not auth_token:
        get_auth_token()
    
    # 首先创建一个考试会话
    session_id = test_create_exam_session()
    if not session_id:
        print("没有有效的会话ID，跳过开始考试测试")
        return
        
    url = f'{BASE_URL}/api/exam/sessions/{session_id}/start'
    data = {
        'session_id': session_id
    }
    
    try:
        headers = {'Content-Type': 'application/json'}
        headers.update(get_auth_headers())
        response = requests.post(url, json=data, headers=headers)
        print(f"开始考试 - 状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"请求失败: {str(e)}")

def test_api_validation():
    """测试API参数验证"""
    # 确保有认证token
    if not auth_token:
        get_auth_token()
    
    print("=== 测试API参数验证 ===")
    
    # 测试缺少必填参数
    url = f'{BASE_URL}/api/exam/sessions'
    data = {
        'exam_name': '测试考试'
        # 缺少其他必填参数
    }
    
    try:
        headers = {'Content-Type': 'application/json'}
        headers.update(get_auth_headers())
        response = requests.post(url, json=data, headers=headers)
        print(f"缺少参数测试 - 状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"请求失败: {str(e)}")

def main():
    """主测试函数"""
    print("=== 开始测试考试API接口 ===")
    
    # 获取认证token
    print("\n=== 获取认证token ===")
    token = get_auth_token()
    if not token:
        print("无法获取认证token，测试终止")
        return
    
    # 测试参数验证
    print("\n=== 测试API参数验证 ===")
    test_api_validation()
    
    print("\n=== 测试正常流程 ===")
    
    # 测试创建考试会话
    session_id = test_create_exam_session()
    
    # 测试开始考试
    test_start_exam()
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    main()