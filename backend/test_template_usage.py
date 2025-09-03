#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试PPT模板使用功能
"""

import sys
import os
import requests
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.ppt_template import PPTTemplate
from services.ppt_generation_service import ppt_generation_service
from services.ai_assistant_service import ai_assistant_service

def test_template_api():
    """测试模板API接口"""
    print("=== 测试PPT模板API接口 ===")
    
    # 测试获取模板列表
    try:
        response = requests.get('http://localhost:5001/api/ppt-templates/list')
        print(f"API响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"API响应成功: {result.get('success', False)}")
            
            if result.get('success'):
                templates = result.get('data', {}).get('templates', [])
                print(f"获取到 {len(templates)} 个模板:")
                
                for template in templates:
                    print(f"  - ID: {template.get('id')}, 名称: {template.get('name')}, 分类: {template.get('category')}")
                
                return templates
            else:
                print(f"API返回错误: {result.get('message', '未知错误')}")
        else:
            print(f"HTTP错误: {response.text}")
    
    except Exception as e:
        print(f"API请求失败: {str(e)}")
    
    return []

def test_ppt_generation_with_template(template_id):
    """测试使用模板生成PPT"""
    print(f"\n=== 测试使用模板 {template_id} 生成PPT ===")
    
    app = create_app()
    with app.app_context():
        try:
            # 直接调用PPT生成服务
            result = ppt_generation_service.generate_ppt_from_text(
                user_id="test_user",
                tenant_id="default",
                content="生成一个关于Python编程的PPT，包含基础语法、数据类型、控制结构三个部分",
                title="Python编程入门",
                template_id=str(template_id)
            )
            
            print(f"PPT生成结果: {result.get('success', False)}")
            
            if result.get('success'):
                data = result.get('data', {})
                print(f"生成的文件: {data.get('title', '未知')}.pptx")
                print(f"文件路径: {data.get('file_path', '未知')}")
                print(f"幻灯片数量: {data.get('slides_count', 0)}")
                print(f"下载链接: {data.get('download_url', '无')}")
                
                # 检查文件是否存在
                file_path = data.get('file_path')
                if file_path and os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    print(f"文件大小: {file_size} 字节")
                    print("✓ PPT文件生成成功")
                else:
                    print("✗ PPT文件不存在")
            else:
                print(f"生成失败: {result.get('error', '未知错误')}")
                
        except Exception as e:
            print(f"PPT生成测试失败: {str(e)}")

def test_ai_assistant_with_template(template_id):
    """测试AI助手使用模板生成PPT"""
    print(f"\n=== 测试AI助手使用模板 {template_id} 生成PPT ===")
    
    app = create_app()
    with app.app_context():
        try:
            # 通过AI助手接口生成PPT
            result = ai_assistant_service.chat_with_user(
                user_id="test_user",
                message="生成一个关于数据结构的PPT，包含数组、链表、栈、队列四个部分",
                template_id=str(template_id)
            )
            
            print(f"AI助手响应成功: {result.get('success', False)}")
            
            if result.get('success'):
                print(f"响应内容: {result.get('response', '')[:200]}...")
                
                ppt_info = result.get('ppt_info')
                if ppt_info:
                    print(f"PPT信息:")
                    print(f"  文件名: {ppt_info.get('filename', '未知')}")
                    print(f"  下载链接: {ppt_info.get('download_url', '无')}")
                    print(f"  幻灯片数量: {ppt_info.get('slides_count', 0)}")
                    print("✓ AI助手PPT生成成功")
                else:
                    print("✗ 未获取到PPT信息")
            else:
                print(f"AI助手响应失败: {result.get('error', '未知错误')}")
                
        except Exception as e:
            print(f"AI助手测试失败: {str(e)}")

def main():
    """主测试函数"""
    print("开始测试PPT模板使用功能...\n")
    
    # 1. 测试API接口
    templates = test_template_api()
    
    if not templates:
        print("\n❌ 没有可用的模板，无法继续测试")
        return
    
    # 2. 选择第一个模板进行测试
    test_template = templates[0]
    template_id = test_template.get('id')
    
    print(f"\n使用模板进行测试: {test_template.get('name')} (ID: {template_id})")
    
    # 3. 测试PPT生成服务
    test_ppt_generation_with_template(template_id)
    
    # 4. 测试AI助手服务
    test_ai_assistant_with_template(template_id)
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    main()