#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
from utils.database import db
from models.ai_model import AIModelConfig
from services.vector_database_service import vector_db_service
from services.llm_service import llm_service

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
db.init_app(app)

with app.app_context():
    print("=== AI模型配置检查 ===")
    
    # 获取所有模型配置
    models = AIModelConfig.query.all()
    print(f"\n总计模型数量: {len(models)}")
    
    if not models:
        print("❌ 未找到任何AI模型配置")
    else:
        print("\n📋 模型配置列表:")
        for i, model in enumerate(models, 1):
            print(f"\n{i}. 模型名称: {model.model_name}")
            print(f"   模型ID: {model.id}")
            print(f"   模型类型: {model.model_type}")
            print(f"   模型标识: {model.model_id}")
            print(f"   激活状态: {'✅ 已激活' if model.is_active else '❌ 未激活'}")
            print(f"   默认模型: {'✅ 是' if model.is_default else '❌ 否'}")
            print(f"   API密钥: {'✅ 已设置' if model.api_key else '❌ 未设置'}")
            print(f"   API URL: {model.api_base_url or '❌ 未设置'}")
            print(f"   创建时间: {model.created_at}")
    
    # 检查默认模型
    default_model = AIModelConfig.query.filter_by(is_default=True, is_active=True).first()
    print(f"\n🎯 默认模型状态:")
    if default_model:
        print(f"   ✅ 已设置默认模型: {default_model.model_name}")
        print(f"   模型类型: {default_model.model_type}")
        print(f"   API配置: {'完整' if default_model.api_key and default_model.api_base_url else '不完整'}")
    else:
        print("   ❌ 未设置默认模型")
    
    # 检查激活的模型
    active_models = AIModelConfig.query.filter_by(is_active=True).all()
    print(f"\n🔥 激活模型数量: {len(active_models)}")
    
    # 检查LLM服务状态
    print(f"\n🤖 LLM服务状态:")
    try:
        llm_service._ensure_initialized()
        if llm_service.default_model:
            if hasattr(llm_service.default_model, 'model_name'):
                print(f"   ✅ LLM服务已加载模型: {llm_service.default_model.model_name}")
            else:
                print(f"   ⚠️ LLM服务使用备用模型配置")
        else:
            print(f"   ❌ LLM服务未加载任何模型")
    except Exception as e:
        print(f"   ❌ LLM服务初始化失败: {str(e)}")
    
    print("\n=== 检查完成 ===")