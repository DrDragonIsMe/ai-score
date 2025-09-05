#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 文件模板生成器

Description:
    从模板创建新文件，自动填入当天日期和其他动态信息

Author: Chang Xinglong
Date: 2025-01-21
Version: 1.0.0
License: Apache License 2.0
"""

import os
import sys
from datetime import datetime

def create_file_from_template(template_path, output_path, module_name, description, version="1.0.0"):
    """
    从模板创建新文件
    
    Args:
        template_path (str): 模板文件路径
        output_path (str): 输出文件路径
        module_name (str): 模块名称
        description (str): 模块描述
        version (str): 版本号，默认为1.0.0
    """
    try:
        # 读取模板文件
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # 获取当天日期
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # 替换模板变量
        content = template_content.replace('{MODULE_NAME}', module_name)
        content = content.replace('{DESCRIPTION}', description)
        content = content.replace('{DATE}', current_date)
        content = content.replace('{VERSION}', version)
        
        # 创建输出目录（如果不存在）
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 写入新文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"文件已创建: {output_path}")
        print(f"模块名称: {module_name}")
        print(f"创建日期: {current_date}")
        
    except Exception as e:
        print(f"创建文件时出错: {e}")
        sys.exit(1)

def main():
    """
    主函数 - 命令行接口
    """
    if len(sys.argv) < 5 or len(sys.argv) > 6:
        print("使用方法: python create_file_from_template.py <模板路径> <输出路径> <模块名称> <描述> [版本号]")
        print("示例: python create_file_from_template.py templates/python_template.py backend/api/new_module.py 'New Module' 'This is a new module' '1.2.0'")
        print("注意: 版本号参数可选，默认为1.0.0")
        sys.exit(1)
    
    template_path = sys.argv[1]
    output_path = sys.argv[2]
    module_name = sys.argv[3]
    description = sys.argv[4]
    version = sys.argv[5] if len(sys.argv) == 6 else "1.0.0"
    
    create_file_from_template(template_path, output_path, module_name, description, version)

if __name__ == "__main__":
    main()