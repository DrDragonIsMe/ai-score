#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from services.ppt_generation_service import ppt_generation_service
from models.ppt_template import PPTTemplate
from utils.database import db

def test_ppt_generation():
    """测试PPT生成功能"""
    app = create_app()
    with app.app_context():
        print("=== PPT模板功能最终测试 ===")
        
        # 1. 获取可用模板
        templates = PPTTemplate.query.filter_by(is_active=True).all()
        print(f"\n1. 可用模板数量: {len(templates)}")
        for template in templates:
            print(f"   - {template.name} (ID: {template.id})")
        
        if templates:
            # 2. 使用第一个模板生成PPT
            template = templates[0]
            print(f"\n2. 使用模板 '{template.name}' 生成PPT...")
            
            result = ppt_generation_service.generate_ppt_from_text(
                user_id="test_user",
                tenant_id="default",
                content="人工智能是计算机科学的一个分支，它试图理解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。",
                title="人工智能概述",
                template_id=template.id
            )
            
            if result['success']:
                print(f"   ✅ PPT生成成功")
                file_path = result.get('data', {}).get('file_path', '未知')
                print(f"   📁 文件路径: {file_path}")
                
                # 检查文件是否存在
                if file_path != '未知' and os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    print(f"   📊 文件大小: {file_size} 字节")
                    print(f"   📄 幻灯片数量: {result.get('data', {}).get('slides_count', '未知')}")
                else:
                    print(f"   ❌ 文件不存在: {file_path}")
            else:
                print(f"   ❌ PPT生成失败: {result.get('error', '未知错误')}")
        
        # 3. 测试不使用模板
        print(f"\n3. 不使用模板生成PPT...")
        result = ppt_generation_service.generate_ppt_from_text(
            user_id="test_user",
            tenant_id="default",
            content="云计算是一种通过互联网提供计算服务的模式，包括服务器、存储、数据库、网络、软件等。",
            title="云计算概述"
        )
        
        if result['success']:
            print(f"   ✅ PPT生成成功")
            file_path = result.get('data', {}).get('file_path', '未知')
            print(f"   📁 文件路径: {file_path}")
            
            # 检查文件是否存在
            if file_path != '未知' and os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"   📊 文件大小: {file_size} 字节")
                print(f"   📄 幻灯片数量: {result.get('data', {}).get('slides_count', '未知')}")
            else:
                print(f"   ❌ 文件不存在: {file_path}")
        else:
            print(f"   ❌ PPT生成失败: {result.get('error', '未知错误')}")
        
        print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_ppt_generation()