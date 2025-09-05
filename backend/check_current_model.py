#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask
from config import Config
from utils.database import db
from models.ai_model import AIModelConfig

# 创建应用实例
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    # 查询默认模型
    default_models = AIModelConfig.query.filter_by(is_default=True).all()
    
    print("=== 当前默认AI模型配置 ===")
    for model in default_models:
        print(f"模型名称: {model.model_name}")
        print(f"模型ID: {model.model_id}")
        print(f"模型类型: {model.model_type}")
        print(f"API URL: {model.api_base_url}")
        print(f"是否激活: {model.is_active}")
        print("-" * 40)
    
    # 查询所有可用模型
    all_models = AIModelConfig.query.filter_by(is_active=True).all()
    print("\n=== 所有可用AI模型 ===")
    for model in all_models:
        print(f"{model.model_name} ({model.model_type}) - {model.model_id}")