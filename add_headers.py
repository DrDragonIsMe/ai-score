#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 批量添加文件头注释脚本

Description:
    为所有Python文件添加标准的文件头注释，包含作者信息、
    描述、版本等信息。

Author: Chang Xinglong
Date: 2025-08-30
Version: 1.0.0
License: Apache License 2.0
"""

import os
import re
from pathlib import Path

# 文件描述映射
FILE_DESCRIPTIONS = {
    'app.py': 'Flask应用的主入口文件，负责应用初始化、配置加载、蓝图注册和中间件设置等核心功能。',
    'config.py': '系统配置管理，包括数据库、缓存、AI模型、多租户、国际化等各种配置参数的定义和管理。',
    'extensions.py': 'Flask扩展初始化文件，统一管理各种第三方扩展的初始化和配置。',
    
    # API模块
    'auth.py': '用户认证API接口，提供登录、注册、令牌刷新等认证相关功能。',
    'users.py': '用户管理API接口，提供用户信息查询、更新、权限管理等功能。',
    'subjects.py': '学科管理API接口，提供学科信息、知识点管理等功能。',
    'diagnosis.py': '学习诊断API接口，提供智能诊断、能力评估等功能。',
    'learning.py': '学习路径API接口，提供个性化学习路径生成和管理功能。',
    'memory.py': '记忆强化API接口，提供艾宾浩斯记忆曲线相关功能。',
    'exam.py': '考试管理API接口，提供模拟考试、成绩分析等功能。',
    'mistakes.py': '错题管理API接口，提供错题收集、分析、复习等功能。',
    'tracking.py': '学习跟踪API接口，提供学习行为记录和分析功能。',
    
    # 数据模型
    'base.py': '数据模型基类，定义通用字段和方法。',
    'user.py': '用户数据模型，定义用户信息、权限等数据结构。',
    'tenant.py': '租户数据模型，支持多租户架构的数据隔离。',
    'knowledge.py': '知识点数据模型，定义学科知识体系结构。',
    'question.py': '题目数据模型，定义题目信息、难度、标签等。',
    'diagnosis.py': '诊断数据模型，定义学习诊断结果和分析数据。',
    'learning.py': '学习路径数据模型，定义个性化学习计划和进度。',
    'memory.py': '记忆数据模型，定义记忆强化相关数据结构。',
    'exam.py': '考试数据模型，定义考试信息、成绩等数据结构。',
    'mistake.py': '错题数据模型，定义错题信息和分析数据。',
    'tracking.py': '跟踪数据模型，定义学习行为和统计数据。',
    'ai_model.py': 'AI模型数据模型，定义AI模型配置和使用记录。',
    
    # 服务层
    'llm_service.py': 'LLM服务，提供大语言模型调用、内容生成等AI功能。',
    'diagnosis_service.py': '诊断服务，提供智能学习诊断和能力评估功能。',
    'learning_path_service.py': '学习路径服务，提供个性化学习路径生成和优化。',
    'memory_service.py': '记忆服务，实现艾宾浩斯记忆曲线算法。',
    'exam_service.py': '考试服务，提供智能组卷、成绩分析等功能。',
    'mistake_service.py': '错题服务，提供错题分析和推荐功能。',
    'content_generation_service.py': '内容生成服务，提供AI驱动的教学内容生成。',
    'tutoring_service.py': '辅导服务，提供智能答疑和学习指导。',
    'strategy_service.py': '策略服务，提供学习策略推荐和优化。',
    'adaptive_service.py': '自适应服务，提供个性化学习适配功能。',
    'tracking_service.py': '跟踪服务，提供学习行为分析和统计。',
    'learning_profile_service.py': '学习档案服务，提供学习者画像分析。',
    
    # 工具模块
    'validators.py': '数据验证工具，提供各种数据格式和业务规则验证。',
    'database.py': '数据库工具，提供数据库连接、事务管理等功能。',
    'response.py': '响应工具，提供统一的API响应格式处理。',
    'logger.py': '日志工具，提供结构化日志记录和管理功能。',
    'decorators.py': '装饰器工具，提供权限验证、缓存、限流等装饰器。',
    
    # 配置模块
    'database.py': '数据库配置，定义数据库连接和ORM配置。',
    'i18n.py': '国际化配置，定义多语言支持配置。',
    'multi_tenant.py': '多租户配置，定义租户隔离和管理配置。',
}

def get_file_description(file_path):
    """根据文件路径获取文件描述"""
    filename = os.path.basename(file_path)
    
    # 特殊处理__init__.py文件
    if filename == '__init__.py':
        parent_dir = os.path.basename(os.path.dirname(file_path))
        return f'{parent_dir}模块初始化文件，定义模块导出接口和初始化逻辑。'
    
    return FILE_DESCRIPTIONS.get(filename, '系统功能模块，提供相关业务逻辑实现。')

def create_header_comment(file_path):
    """创建标准的文件头注释"""
    filename = os.path.basename(file_path)
    description = get_file_description(file_path)
    
    # 根据文件路径确定模块名称
    if 'api/' in file_path:
        module_name = f'API接口 - {filename}'
    elif 'models/' in file_path:
        module_name = f'数据模型 - {filename}'
    elif 'services/' in file_path:
        module_name = f'业务服务 - {filename}'
    elif 'utils/' in file_path:
        module_name = f'工具模块 - {filename}'
    elif 'config/' in file_path:
        module_name = f'配置模块 - {filename}'
    else:
        module_name = filename
    
    header = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - {module_name}

Description:
    {description}

Author: Chang Xinglong
Date: 2025-08-30
Version: 1.0.0
License: Apache License 2.0
"""
'''
    return header

def has_header_comment(content):
    """检查文件是否已有头注释"""
    # 检查是否包含作者信息
    return 'Author: Chang Xinglong' in content

def add_header_to_file(file_path):
    """为单个文件添加头注释"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 如果已有头注释，跳过
        if has_header_comment(content):
            print(f"跳过 {file_path} (已有头注释)")
            return
        
        # 创建新的头注释
        header = create_header_comment(file_path)
        
        # 处理现有的编码声明和简单注释
        lines = content.split('\n')
        new_lines = []
        skip_lines = 0
        
        # 跳过现有的shebang和编码声明
        for i, line in enumerate(lines):
            if line.startswith('#!') or line.startswith('# -*- coding:') or line.startswith('# coding:'):
                skip_lines = i + 1
            elif line.strip() == '' and i < 5:  # 跳过开头的空行
                skip_lines = i + 1
            elif line.startswith('"""') and i < 10:  # 跳过简单的文档字符串
                # 找到结束的"""
                for j in range(i + 1, min(i + 10, len(lines))):
                    if lines[j].strip().endswith('"""'):
                        skip_lines = j + 1
                        break
                break
            else:
                break
        
        # 构建新内容
        new_content = header
        if skip_lines < len(lines):
            remaining_content = '\n'.join(lines[skip_lines:])
            if remaining_content.strip():
                new_content += '\n' + remaining_content
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"已更新 {file_path}")
        
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")

def main():
    """主函数"""
    # 获取项目根目录
    project_root = Path(__file__).parent
    
    # 查找所有Python文件
    python_files = []
    for root, dirs, files in os.walk(project_root / 'backend'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"找到 {len(python_files)} 个Python文件")
    
    # 为每个文件添加头注释
    for file_path in python_files:
        add_header_to_file(file_path)
    
    print("\n批量添加头注释完成！")

if __name__ == '__main__':
    main()