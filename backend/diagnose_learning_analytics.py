#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习分析页面问题诊断脚本
检查API调用、数据返回和前端加载问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from datetime import datetime
from app import create_app
from utils.database import db
from models.user import User

def test_api_endpoints_with_auth():
    """
    测试学习分析API端点（带认证）
    """
    print("=== 学习分析API诊断 ===")
    
    # 1. 获取JWT token
    login_url = 'http://localhost:5001/api/auth/login'
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        print("🔐 尝试登录获取token...")
        login_response = requests.post(login_url, json=login_data, timeout=10)
        print(f"登录响应状态: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.text}")
            return False
        
        login_result = login_response.json()
        if not login_result.get('success'):
            print(f"❌ 登录失败: {login_result.get('message', 'Unknown error')}")
            return False
        
        token = login_result.get('access_token')
        if not token:
            print("❌ 未获取到访问令牌")
            return False
        
        print("✅ 登录成功，获取到访问令牌")
        
        # 2. 设置请求头
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # 3. 测试学习分析API端点
        api_endpoints = [
            {
                'name': '仪表板摘要',
                'url': '/api/learning-analytics/dashboard-summary',
                'critical': True
            },
            {
                'name': '学习进度',
                'url': '/api/learning-analytics/progress',
                'critical': True
            },
            {
                'name': '知识点掌握',
                'url': '/api/learning-analytics/knowledge-mastery',
                'critical': True
            },
            {
                'name': '学习统计',
                'url': '/api/learning-analytics/study-statistics',
                'critical': False
            },
            {
                'name': '学习建议',
                'url': '/api/learning-analytics/learning-recommendations',
                'critical': False
            },
            {
                'name': '性能趋势',
                'url': '/api/learning-analytics/performance-trends',
                'critical': False
            }
        ]
        
        success_count = 0
        critical_failures = []
        
        for endpoint in api_endpoints:
            try:
                print(f"\n📊 测试 {endpoint['name']} API...")
                full_url = f"http://localhost:5001{endpoint['url']}"
                
                response = requests.get(full_url, headers=headers, timeout=15)
                print(f"  状态码: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get('success'):
                            print(f"  ✅ {endpoint['name']} - 成功")
                            
                            # 检查数据结构
                            response_data = data.get('data', {})
                            if response_data:
                                data_keys = list(response_data.keys())[:3]
                                print(f"  📋 数据字段: {data_keys}")
                                
                                # 检查数据是否为空
                                non_empty_fields = sum(1 for k, v in response_data.items() 
                                                      if v is not None and v != [] and v != {})
                                print(f"  📊 非空字段数: {non_empty_fields}/{len(response_data)}")
                            else:
                                print(f"  ⚠️ 数据为空")
                            
                            success_count += 1
                        else:
                            error_msg = data.get('message', 'Unknown error')
                            print(f"  ❌ {endpoint['name']} - 业务失败: {error_msg}")
                            if endpoint['critical']:
                                critical_failures.append(f"{endpoint['name']}: {error_msg}")
                    except json.JSONDecodeError:
                        print(f"  ❌ {endpoint['name']} - JSON解析失败")
                        if endpoint['critical']:
                            critical_failures.append(f"{endpoint['name']}: JSON解析失败")
                else:
                    print(f"  ❌ {endpoint['name']} - HTTP错误: {response.status_code}")
                    if response.text:
                        print(f"  错误详情: {response.text[:200]}")
                    if endpoint['critical']:
                        critical_failures.append(f"{endpoint['name']}: HTTP {response.status_code}")
                        
            except requests.exceptions.Timeout:
                print(f"  ❌ {endpoint['name']} - 请求超时")
                if endpoint['critical']:
                    critical_failures.append(f"{endpoint['name']}: 请求超时")
            except requests.exceptions.ConnectionError:
                print(f"  ❌ {endpoint['name']} - 连接错误")
                if endpoint['critical']:
                    critical_failures.append(f"{endpoint['name']}: 连接错误")
            except Exception as e:
                print(f"  ❌ {endpoint['name']} - 异常: {str(e)}")
                if endpoint['critical']:
                    critical_failures.append(f"{endpoint['name']}: {str(e)}")
        
        # 4. 生成诊断报告
        print("\n" + "=" * 50)
        print("📋 诊断报告")
        print(f"成功API数量: {success_count}/{len(api_endpoints)}")
        
        if critical_failures:
            print("\n🚨 关键问题:")
            for failure in critical_failures:
                print(f"  - {failure}")
            
            print("\n🔧 可能的解决方案:")
            print("  1. 检查后端服务是否正常运行")
            print("  2. 验证数据库中是否有学习记录数据")
            print("  3. 检查API路由注册是否正确")
            print("  4. 验证JWT认证配置")
            print("  5. 查看后端日志获取详细错误信息")
        else:
            print("\n✅ 所有关键API正常工作")
            if success_count < len(api_endpoints):
                print("⚠️ 部分非关键API存在问题，但不影响基本功能")
        
        return len(critical_failures) == 0
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务 (http://localhost:5001)")
        print("🔧 请确保后端服务正在运行")
        return False
    except Exception as e:
        print(f"❌ 诊断过程出错: {str(e)}")
        return False

def check_database_data():
    """
    检查数据库中的学习数据
    """
    print("\n=== 数据库数据检查 ===")
    
    app = create_app()
    
    with app.app_context():
        try:
            # 检查用户数据
            user_count = db.session.query(User).count()
            print(f"👥 用户总数: {user_count}")
            
            if user_count == 0:
                print("❌ 没有用户数据")
                return False
            
            # 检查学习记录
            from models.learning import StudyRecord
            study_count = db.session.query(StudyRecord).count()
            print(f"📚 学习记录总数: {study_count}")
            
            if study_count == 0:
                print("⚠️ 没有学习记录数据，这可能是前端显示空白的原因")
                print("💡 建议运行测试数据生成脚本")
                return False
            
            # 检查最近的学习记录
            from datetime import timedelta
            recent_date = datetime.now() - timedelta(days=30)
            recent_count = db.session.query(StudyRecord).filter(
                StudyRecord.created_at >= recent_date
            ).count()
            print(f"📅 最近30天学习记录: {recent_count}")
            
            if recent_count == 0:
                print("⚠️ 最近30天没有学习记录，分析结果可能为空")
            
            # 检查知识点数据
            from models.knowledge import KnowledgePoint
            kp_count = db.session.query(KnowledgePoint).count()
            print(f"🧠 知识点总数: {kp_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ 数据库检查失败: {str(e)}")
            return False

def check_frontend_console_errors():
    """
    提供前端调试建议
    """
    print("\n=== 前端调试建议 ===")
    print("🔍 请在浏览器中检查以下内容:")
    print("")
    print("1. 打开浏览器开发者工具 (F12)")
    print("2. 查看 Console 标签页是否有错误信息")
    print("3. 查看 Network 标签页中的API请求:")
    print("   - 是否有失败的请求 (红色)")
    print("   - 请求响应时间是否过长")
    print("   - 响应数据是否正确")
    print("4. 检查 Application 标签页中的 Local Storage:")
    print("   - 是否有有效的 JWT token")
    print("   - token 是否已过期")
    print("")
    print("🚨 常见问题:")
    print("   - 401 错误: 认证失败，需要重新登录")
    print("   - 500 错误: 后端服务错误")
    print("   - 超时错误: 网络或服务响应慢")
    print("   - CORS 错误: 跨域配置问题")

def main():
    """
    主诊断流程
    """
    print("学习分析页面问题诊断")
    print("=" * 50)
    print(f"诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 检查数据库数据
    db_ok = check_database_data()
    
    # 2. 测试API端点
    api_ok = test_api_endpoints_with_auth()
    
    # 3. 提供前端调试建议
    check_frontend_console_errors()
    
    # 4. 总结诊断结果
    print("\n" + "=" * 50)
    print("🎯 诊断总结")
    
    if db_ok and api_ok:
        print("✅ 后端服务和数据都正常")
        print("🔍 问题可能在前端，请检查浏览器控制台")
        print("💡 建议刷新页面或清除浏览器缓存")
    elif not db_ok:
        print("❌ 数据库数据不足")
        print("🔧 建议运行: python test_learning_analytics_integration.py")
    elif not api_ok:
        print("❌ API服务存在问题")
        print("🔧 建议检查后端服务日志")
    else:
        print("❌ 存在多个问题，需要逐一解决")
    
    print("\n📞 如需进一步帮助，请提供:")
    print("   - 浏览器控制台错误信息")
    print("   - 网络请求详情")
    print("   - 后端服务日志")

if __name__ == '__main__':
    main()