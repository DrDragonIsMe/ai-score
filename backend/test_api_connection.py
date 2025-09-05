#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API连接和模型功能
"""

import requests
import json

def test_api_connection():
    """测试API连接和模型功能"""
    base_url = 'http://localhost:5001'
    
    print("=== API连接测试 ===")
    
    # 1. 测试登录
    print("\n1. 测试登录...")
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    try:
        response = requests.post(f'{base_url}/api/auth/login', json=login_data, timeout=10)
        print(f"登录状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                token = result['data']['access_token']
                print("✅ 登录成功")
                
                # 2. 测试获取模型列表
                print("\n2. 测试获取模型列表...")
                headers = {'Authorization': f'Bearer {token}'}
                models_response = requests.get(f'{base_url}/api/settings/ai-models', headers=headers)
                print(f"模型列表状态码: {models_response.status_code}")
                
                if models_response.status_code == 200:
                    models_data = models_response.json()
                    print("✅ 获取模型列表成功")
                    print(f"模型数量: {len(models_data.get('data', []))}")
                    
                    # 显示模型信息
                    for model in models_data.get('data', []):
                        print(f"  - {model['name']} ({model['model_type']}) - 激活: {model['is_active']} - 默认: {model['is_default']}")
                    
                    # 3. 测试模型连接
                    print("\n3. 测试模型连接...")
                    active_models = [m for m in models_data.get('data', []) if m['is_active']]
                    
                    if active_models:
                        for model in active_models:
                            print(f"\n测试模型: {model['name']}")
                            test_response = requests.post(
                                f"{base_url}/api/settings/ai-models/{model['id']}/test",
                                headers=headers
                            )
                            print(f"测试状态码: {test_response.status_code}")
                            
                            if test_response.status_code == 200:
                                test_result = test_response.json()
                                if test_result.get('success'):
                                    print("✅ 模型连接测试成功")
                                    print(f"响应时间: {test_result['data'].get('response_time', 'N/A')}s")
                                else:
                                    print(f"❌ 模型连接测试失败: {test_result.get('message')}")
                            else:
                                print(f"❌ 模型连接测试失败: HTTP {test_response.status_code}")
                                print(f"错误信息: {test_response.text[:200]}")
                    else:
                        print("❌ 没有激活的模型")
                        
                else:
                    print(f"❌ 获取模型列表失败: HTTP {models_response.status_code}")
                    print(f"错误信息: {models_response.text[:200]}")
                    
            else:
                print(f"❌ 登录失败: {result.get('message')}")
        else:
            print(f"❌ 登录失败: HTTP {response.status_code}")
            print(f"错误信息: {response.text[:200]}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务")
    except Exception as e:
        print(f"❌ 测试过程出错: {str(e)}")

if __name__ == '__main__':
    test_api_connection()