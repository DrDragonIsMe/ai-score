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
import requests
import json

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
db.init_app(app)

def test_model_connection(model):
    """测试模型连接"""
    try:
        # 构建测试请求
        test_data = {
            "model": model.model_id,
            "messages": [
                {"role": "user", "content": "Hello, this is a connection test."}
            ],
            "max_tokens": 50,
            "temperature": 0.7
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # 根据模型类型设置不同的请求参数
        if model.model_type == 'azure' or 'azure.com' in (model.api_base_url or ''):
            # Azure OpenAI
            api_url = f"{model.api_base_url}/openai/deployments/{model.model_id}/chat/completions?api-version=2024-02-15-preview"
            headers["api-key"] = model.api_key
        elif model.model_type == 'openai':
            # OpenAI
            api_url = f"{model.api_base_url}/chat/completions"
            headers["Authorization"] = f"Bearer {model.api_key}"
        else:
            return False, f"不支持的模型类型: {model.model_type}"
        
        # 检查必要参数
        if not model.api_key:
            return False, "API密钥未设置"
        
        if not model.api_base_url:
            return False, "API基础URL未设置"
        
        # 发送测试请求
        response = requests.post(
            api_url,
            headers=headers,
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return True, "连接成功"
            else:
                return False, "响应格式异常"
        else:
            return False, f"API请求失败: {response.status_code} - {response.text[:200]}"
            
    except requests.exceptions.Timeout:
        return False, "连接超时"
    except requests.exceptions.ConnectionError:
        return False, "连接错误"
    except Exception as e:
        return False, f"测试异常: {str(e)}"

with app.app_context():
    print("=== 修复AI模型配置 ===")
    
    # 1. 修复默认模型设置（确保只有一个默认模型）
    print("\n🔧 修复默认模型设置...")
    default_models = AIModelConfig.query.filter_by(is_default=True).all()
    
    if len(default_models) > 1:
        print(f"   发现 {len(default_models)} 个默认模型，修复中...")
        # 保留第一个有效的默认模型，取消其他的默认状态
        valid_default = None
        for model in default_models:
            if model.is_active and model.api_key and model.api_base_url:
                if valid_default is None:
                    valid_default = model
                    print(f"   ✅ 保留默认模型: {model.model_name}")
                else:
                    model.is_default = False
                    print(f"   🔄 取消默认状态: {model.model_name}")
            else:
                model.is_default = False
                print(f"   ❌ 取消无效默认模型: {model.model_name} (配置不完整)")
        
        # 如果没有有效的默认模型，设置第一个激活的模型为默认
        if valid_default is None:
            active_model = AIModelConfig.query.filter_by(is_active=True).first()
            if active_model:
                active_model.is_default = True
                print(f"   🎯 设置新默认模型: {active_model.model_name}")
        
        db.session.commit()
        print("   ✅ 默认模型设置已修复")
    elif len(default_models) == 0:
        print("   ❌ 未找到默认模型，设置第一个激活模型为默认")
        active_model = AIModelConfig.query.filter_by(is_active=True).first()
        if active_model:
            active_model.is_default = True
            db.session.commit()
            print(f"   ✅ 设置默认模型: {active_model.model_name}")
    else:
        print("   ✅ 默认模型设置正常")
    
    # 2. 测试所有激活模型的连接
    print("\n🧪 测试模型连接...")
    active_models = AIModelConfig.query.filter_by(is_active=True).all()
    
    for model in active_models:
        print(f"\n   测试模型: {model.model_name} ({model.model_type})")
        success, message = test_model_connection(model)
        
        if success:
            print(f"   ✅ {message}")
        else:
            print(f"   ❌ {message}")
            
            # 如果是默认模型连接失败，尝试找到其他可用模型
            if model.is_default:
                print(f"   ⚠️ 默认模型连接失败，寻找备用模型...")
                for backup_model in active_models:
                    if backup_model.id != model.id:
                        backup_success, backup_message = test_model_connection(backup_model)
                        if backup_success:
                            model.is_default = False
                            backup_model.is_default = True
                            db.session.commit()
                            print(f"   🔄 切换默认模型到: {backup_model.model_name}")
                            break
    
    # 3. 检查并修复模型配置完整性
    print("\n🔍 检查模型配置完整性...")
    all_models = AIModelConfig.query.all()
    
    for model in all_models:
        issues = []
        
        if not model.api_key:
            issues.append("API密钥未设置")
        
        if not model.api_base_url:
            issues.append("API基础URL未设置")
        
        if not model.model_id:
            issues.append("模型ID未设置")
        
        if model.model_type not in ['openai', 'azure', 'azure_openai', 'doubao', 'claude']:
            issues.append(f"不支持的模型类型: {model.model_type}")
        
        if issues:
            print(f"\n   ⚠️ 模型 {model.model_name} 存在问题:")
            for issue in issues:
                print(f"      - {issue}")
            
            if model.is_active:
                print(f"      🔄 由于配置不完整，将停用此模型")
                model.is_active = False
        else:
            print(f"   ✅ 模型 {model.model_name} 配置完整")
    
    db.session.commit()
    
    # 4. 最终状态检查
    print("\n📊 最终状态检查:")
    final_models = AIModelConfig.query.all()
    active_count = len([m for m in final_models if m.is_active])
    default_count = len([m for m in final_models if m.is_default])
    
    print(f"   总模型数: {len(final_models)}")
    print(f"   激活模型数: {active_count}")
    print(f"   默认模型数: {default_count}")
    
    if default_count == 1:
        default_model = next(m for m in final_models if m.is_default)
        print(f"   ✅ 默认模型: {default_model.model_name}")
    elif default_count == 0:
        print(f"   ❌ 警告: 没有默认模型")
    else:
        print(f"   ❌ 错误: 有多个默认模型")
    
    print("\n=== 修复完成 ===")