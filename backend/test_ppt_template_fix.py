#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试PPT模板功能修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ai_assistant_service import ai_assistant_service
from services.ppt_generation_service import ppt_generation_service
from models.ppt_template import PPTTemplate
from utils.database import db
from app import create_app

def test_ppt_template_functionality():
    """
    测试PPT模板功能
    """
    print("=== PPT模板功能测试 ===")
    
    # 创建应用上下文
    app = create_app()
    with app.app_context():
        # 1. 检查数据库中的模板
        print("\n1. 检查数据库中的PPT模板:")
        templates = PPTTemplate.query.filter_by(is_active=True).all()
        print(f"找到 {len(templates)} 个活跃模板:")
        
        for template in templates:
            print(f"  - ID: {template.id}, 名称: {template.name}, 文件路径: {template.template_file_path}")
            if template.template_file_path and os.path.exists(template.template_file_path):
                print(f"    ✓ 文件存在")
            else:
                print(f"    ✗ 文件不存在")
        
        if not templates:
            print("  没有找到活跃的PPT模板")
            return
        
        # 2. 测试通过聊天接口生成PPT（使用模板）
        print("\n2. 测试通过聊天接口生成PPT（使用模板）:")
        test_template = templates[0]  # 使用第一个模板
        print(f"使用模板: {test_template.name} (ID: {test_template.id})")
        
        try:
            result = ai_assistant_service.chat_with_user(
                user_id="test_user",
                message="生成一个关于人工智能的PPT",
                template_id=str(test_template.id)
            )
            
            print(f"聊天接口结果: {result.get('success', False)}")
            if result.get('success'):
                print(f"响应: {result.get('response', '')[:100]}...")
                if 'ppt_info' in result:
                    print(f"PPT信息: {result['ppt_info']}")
            else:
                print(f"错误: {result.get('error', '未知错误')}")
                
        except Exception as e:
            print(f"聊天接口测试失败: {str(e)}")
        
        # 3. 测试直接PPT生成服务（使用模板）
        print("\n3. 测试直接PPT生成服务（使用模板）:")
        try:
            result = ppt_generation_service.generate_ppt_from_text(
                user_id="test_user",
                tenant_id="default",
                content="生成一个关于机器学习的PPT，包含介绍、基本概念、应用场景三个部分",
                title="机器学习入门",
                template_id=str(test_template.id)
            )
            
            print(f"PPT生成服务结果: {result.get('success', False)}")
            if result.get('success'):
                print(f"生成的文件: {result.get('data', {}).get('filename', '未知')}")
                print(f"文件路径: {result.get('data', {}).get('file_path', '未知')}")
            else:
                print(f"错误: {result.get('error', '未知错误')}")
                
        except Exception as e:
            print(f"PPT生成服务测试失败: {str(e)}")
        
        # 4. 测试不使用模板的情况
        print("\n4. 测试不使用模板的PPT生成:")
        try:
            result = ppt_generation_service.generate_ppt_from_text(
                user_id="test_user",
                tenant_id="default",
                content="生成一个关于数据科学的PPT",
                title="数据科学概述",
                template_id=None
            )
            
            print(f"无模板PPT生成结果: {result.get('success', False)}")
            if result.get('success'):
                print(f"生成的文件: {result.get('data', {}).get('filename', '未知')}")
            else:
                print(f"错误: {result.get('error', '未知错误')}")
                
        except Exception as e:
            print(f"无模板PPT生成测试失败: {str(e)}")

if __name__ == "__main__":
    test_ppt_template_functionality()