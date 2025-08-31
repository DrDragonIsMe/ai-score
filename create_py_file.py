#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - Python文件创建工具

Description:
    基于模板创建新的Python文件，自动添加标准头注释。
    使用方法: python create_py_file.py <文件路径> [模块描述]

Author: Chang Xinglong
Date: 2025-08-30
Version: 1.0.0
License: Apache License 2.0
"""

import os
import sys
from datetime import datetime
from pathlib import Path

def get_module_name_from_path(file_path):
    """根据文件路径生成模块名称"""
    filename = os.path.basename(file_path)
    
    # 根据文件路径确定模块类型
    if 'api/' in file_path:
        return f'API接口 - {filename}'
    elif 'models/' in file_path:
        return f'数据模型 - {filename}'
    elif 'services/' in file_path:
        return f'业务服务 - {filename}'
    elif 'utils/' in file_path:
        return f'工具模块 - {filename}'
    elif 'config/' in file_path:
        return f'配置模块 - {filename}'
    elif 'tests/' in file_path:
        return f'测试模块 - {filename}'
    else:
        return filename

def get_default_description(file_path):
    """根据文件路径生成默认描述"""
    if 'api/' in file_path:
        return '提供REST API接口，处理HTTP请求和响应。'
    elif 'models/' in file_path:
        return '定义数据模型和数据库表结构。'
    elif 'services/' in file_path:
        return '提供业务逻辑服务和核心功能实现。'
    elif 'utils/' in file_path:
        return '提供通用工具函数和辅助功能。'
    elif 'config/' in file_path:
        return '定义配置参数和系统设置。'
    elif 'tests/' in file_path:
        return '提供单元测试和集成测试功能。'
    else:
        return '提供相关功能实现。'

def create_python_file(file_path, description=None):
    """创建Python文件"""
    # 检查文件是否已存在
    if os.path.exists(file_path):
        print(f"错误: 文件 {file_path} 已存在")
        return False
    
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # 读取模板
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'python_template.py')
    if not os.path.exists(template_path):
        print(f"错误: 模板文件 {template_path} 不存在")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # 替换模板变量
    module_name = get_module_name_from_path(file_path)
    if description is None:
        description = get_default_description(file_path)
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    content = template_content.replace('{MODULE_NAME}', module_name)
    content = content.replace('{DESCRIPTION}', description)
    content = content.replace('{DATE}', current_date)
    
    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"成功创建文件: {file_path}")
    return True

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python create_py_file.py <文件路径> [模块描述]")
        print("")
        print("示例:")
        print("  python create_py_file.py backend/api/new_api.py")
        print("  python create_py_file.py backend/services/new_service.py '新服务模块，提供XXX功能'")
        print("  python create_py_file.py backend/models/new_model.py")
        return
    
    file_path = sys.argv[1]
    description = sys.argv[2] if len(sys.argv) > 2 else None
    
    # 确保文件路径以.py结尾
    if not file_path.endswith('.py'):
        file_path += '.py'
    
    # 转换为绝对路径
    if not os.path.isabs(file_path):
        file_path = os.path.join(os.getcwd(), file_path)
    
    create_python_file(file_path, description)

if __name__ == '__main__':
    main()