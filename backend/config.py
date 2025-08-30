#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 配置文件

Description:
    系统配置管理，包括数据库、缓存、AI模型、多租户、
    国际化等各种配置参数的定义和管理。

Author: Chang Xinglong
Date: 2025-01-20
Version: 1.0.0
License: Apache License 2.0
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """基础配置"""
    
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ai-score-secret-key-2024'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///ai_score.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 120,
        'pool_pre_ping': True
    }
    
    # Redis配置
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # 国际化配置
    LANGUAGES = {
        'zh': '中文',
        'en': 'English', 
        'ja': '日本語',
        'ko': '한국어'
    }
    BABEL_DEFAULT_LOCALE = 'zh'
    BABEL_DEFAULT_TIMEZONE = 'UTC'
    
    # AI模型配置
    DEFAULT_AI_MODEL = 'doubao'  # 豆包模型
    AI_MODELS = {
        'doubao': {
            'name': '豆包',
            'api_key': os.environ.get('DOUBAO_API_KEY'),
            'base_url': 'https://ark.cn-beijing.volces.com/api/v3',
            'model_id': 'ep-20241201-xxxxx'
        },
        'openai': {
            'name': 'OpenAI GPT',
            'api_key': os.environ.get('OPENAI_API_KEY'),
            'base_url': 'https://api.openai.com/v1',
            'model_id': 'gpt-4'
        },
        'claude': {
            'name': 'Claude',
            'api_key': os.environ.get('CLAUDE_API_KEY'),
            'base_url': 'https://api.anthropic.com',
            'model_id': 'claude-3-sonnet-20240229'
        }
    }
    
    # 多租户配置
    MULTI_TENANT_MODE = True
    DEFAULT_TENANT = 'default'
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    
    # 学习配置
    SUBJECTS = {
        'chinese': '语文',
        'math': '数学', 
        'english': '英语',
        'physics': '物理',
        'chemistry': '化学',
        'biology': '生物',
        'history': '历史',
        'geography': '地理',
        'politics': '政治'
    }
    
    # 难度等级
    DIFFICULTY_LEVELS = {
        1: '基础',
        2: '简单',
        3: '中等',
        4: '困难',
        5: '极难'
    }
    
    # 记忆强化配置（艾宾浩斯遗忘曲线）
    MEMORY_INTERVALS = [1, 2, 4, 7, 15, 30, 60]  # 天数
    
    # 诊断层级
    DIAGNOSIS_LEVELS = {
        'basic': '基础(记忆)',
        'advanced': '进阶(应用)', 
        'comprehensive': '综合(迁移)'
    }

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'postgresql://aiscore:password@localhost/aiscore_dev'

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    
class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
