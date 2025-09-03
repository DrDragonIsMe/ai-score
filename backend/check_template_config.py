#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.ppt_template import PPTTemplate
from utils.database import db

def check_template_config():
    app = create_app()
    with app.app_context():
        # 查找所有模板
        templates = PPTTemplate.query.all()
        print(f"找到 {len(templates)} 个模板:")
        
        for template in templates:
            print(f"\n模板ID: {template.id}")
            print(f"模板名称: {template.name}")
            print(f"模板配置: {template.config}")
            if template.config:
                for key, value in template.config.items():
                    print(f"  {key}: {value} (类型: {type(value)})")
        
        if not templates:
            print("未找到任何模板")

if __name__ == "__main__":
    check_template_config()