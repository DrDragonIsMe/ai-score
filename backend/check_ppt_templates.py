#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.ppt_template import PPTTemplate
from utils.database import db

def check_ppt_templates():
    """检查PPT模板状态"""
    app = create_app()
    
    with app.app_context():
        print("=== PPT模板状态检查 ===")
        
        # 检查数据库中的模板
        templates = PPTTemplate.query.all()
        print(f"\n数据库中的模板数量: {len(templates)}")
        
        if templates:
            for template in templates:
                print(f"\n模板ID: {template.id}")
                print(f"模板名称: {template.name}")
                print(f"分类: {template.category}")
                print(f"描述: {template.description}")
                print(f"文件路径: {template.template_file_path}")
                print(f"是否启用: {template.is_active}")
                print(f"是否默认: {template.is_default}")
                print(f"使用次数: {template.usage_count}")
                print(f"租户ID: {template.tenant_id}")
                
                # 检查文件是否存在
                if template.template_file_path:
                    file_exists = os.path.exists(template.template_file_path)
                    print(f"文件是否存在: {file_exists}")
                    if file_exists:
                        file_size = os.path.getsize(template.template_file_path)
                        print(f"实际文件大小: {file_size} 字节")
                    else:
                        print(f"⚠️  模板文件不存在: {template.template_file_path}")
                else:
                    print("⚠️  未设置模板文件路径")
                
                print("-" * 50)
        else:
            print("\n❌ 数据库中没有找到任何PPT模板")
        
        # 检查上传目录
        upload_dir = 'uploads/ppt_templates'
        print(f"\n=== 上传目录检查 ===")
        print(f"上传目录: {upload_dir}")
        
        if os.path.exists(upload_dir):
            print(f"上传目录存在: ✅")
            files = os.listdir(upload_dir)
            print(f"目录中的文件数量: {len(files)}")
            
            if files:
                print("\n目录中的文件:")
                for file in files:
                    file_path = os.path.join(upload_dir, file)
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        print(f"  - {file} ({file_size} 字节)")
            else:
                print("目录为空")
        else:
            print(f"上传目录不存在: ❌")
            print("正在创建上传目录...")
            os.makedirs(upload_dir, exist_ok=True)
            print("上传目录创建完成: ✅")

if __name__ == '__main__':
    check_ppt_templates()