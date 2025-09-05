#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - API接口 - settings.py

Description:
    系统设置API接口，提供AI模型配置、系统参数设置等功能。

Author: Chang Xinglong
Date: 2025-08-31
Version: 1.0.0
License: Apache License 2.0
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from utils.response import success_response, error_response
from utils.decorators import admin_required, tenant_required
from models.ai_model import AIModelConfig
from models.tenant import Tenant
from utils.database import db
from utils.logger import get_logger
from services.llm_service import llm_service
import uuid

logger = get_logger(__name__)

# 创建蓝图
settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/ai-models', methods=['GET'])
@jwt_required()
@tenant_required
def get_ai_models():
    """
    获取AI模型配置列表
    """
    try:
        tenant_id = get_jwt_identity()['tenant_id']
        
        models = AIModelConfig.query.filter_by(
            tenant_id=tenant_id,
            is_active=True
        ).order_by(AIModelConfig.is_default.desc(), AIModelConfig.model_name).all()
        
        models_data = [model.to_dict(include_sensitive=False) for model in models]
        
        return success_response(
            data={
                'models': models_data,
                'total': len(models_data)
            },
            message='获取AI模型配置成功'
        )
        
    except Exception as e:
        logger.error(f"获取AI模型配置失败: {str(e)}")
        return error_response(message='获取AI模型配置失败')

@settings_bp.route('/ai-models/<model_id>', methods=['GET'])
@jwt_required()
@tenant_required
def get_ai_model(model_id):
    """
    获取单个AI模型配置详情（包含敏感信息）
    """
    try:
        tenant_id = get_jwt_identity()['tenant_id']
        
        model_config = AIModelConfig.query.filter_by(
            id=model_id,
            tenant_id=tenant_id
        ).first()
        
        if not model_config:
            return error_response(message='模型配置不存在')
        
        return success_response(
            data=model_config.to_dict(include_sensitive=True),
            message='获取AI模型配置成功'
        )
        
    except Exception as e:
        logger.error(f"获取AI模型配置失败: {str(e)}")
        return error_response(message='获取AI模型配置失败')

@settings_bp.route('/ai-models', methods=['POST'])
@jwt_required()
@admin_required
@tenant_required
def create_ai_model():
    """
    创建AI模型配置
    """
    try:
        tenant_id = get_jwt_identity()['tenant_id']
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['name', 'model_type', 'model_id']
        for field in required_fields:
            if not data.get(field):
                return error_response(message=f'缺少必填字段: {field}')
        
        # 验证模型类型
        valid_model_types = ['openai', 'azure', 'azure_openai', 'doubao', 'claude']
        if data['model_type'] not in valid_model_types:
            return error_response(message=f'不支持的模型类型: {data["model_type"]}，支持的类型: {", ".join(valid_model_types)}')
        
        # 验证关键配置参数
        if data['model_type'] in ['openai', 'azure', 'azure_openai']:
            if not data.get('api_key'):
                return error_response(message='API密钥是必填字段')
            if not data.get('api_base_url'):
                return error_response(message='API基础URL是必填字段')
        
        # 验证数值参数
        numeric_fields = {
            'max_tokens': (1, 32000),
            'temperature': (0.0, 2.0),
            'top_p': (0.0, 1.0),
            'frequency_penalty': (-2.0, 2.0),
            'presence_penalty': (-2.0, 2.0)
        }
        
        for field, (min_val, max_val) in numeric_fields.items():
            if field in data and data[field] is not None:
                try:
                    value = float(data[field])
                    if not (min_val <= value <= max_val):
                        return error_response(message=f'{field}参数值应在{min_val}-{max_val}之间')
                except (ValueError, TypeError):
                    return error_response(message=f'{field}参数必须是数字')
        
        # 检查模型名称是否已存在
        existing_model = AIModelConfig.query.filter_by(
            tenant_id=tenant_id,
            model_name=data['name']
        ).first()
        
        if existing_model:
            return error_response(message='模型名称已存在')
        
        # 创建新模型配置
        model_config = AIModelConfig(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            model_name=data['name'],
            model_type=data['model_type'],
            model_id=data['model_id'],
            api_key=data.get('api_key'),
            api_base_url=data.get('api_base_url'),
            api_version=data.get('api_version'),
            max_tokens=data.get('max_tokens', 2000),
            temperature=data.get('temperature', 0.7),
            top_p=data.get('top_p', 0.9),
            frequency_penalty=data.get('frequency_penalty', 0.0),
            presence_penalty=data.get('presence_penalty', 0.0),
            supported_features=data.get('supported_features', []),
            use_cases=data.get('use_cases', []),
            rate_limit=data.get('rate_limit'),
            timeout=data.get('timeout', 30),
            retry_count=data.get('retry_count', 3),
            cost_per_1k_tokens=data.get('cost_per_1k_tokens'),
            monthly_quota=data.get('monthly_quota'),
            is_default=data.get('is_default', False)
        )
        
        # 如果设置为默认模型，取消其他模型的默认状态
        if model_config.is_default:
            AIModelConfig.query.filter_by(
                tenant_id=tenant_id,
                is_default=True
            ).update({'is_default': False})
        
        db.session.add(model_config)
        db.session.commit()
        
        # 刷新LLM服务配置
        try:
            llm_service.refresh_default_model()
            logger.info(f"LLM服务配置已刷新，新创建模型: {model_config.model_name}")
        except Exception as refresh_error:
            logger.warning(f"刷新LLM服务配置失败: {str(refresh_error)}")
        
        return success_response(
            data=model_config.to_dict(include_sensitive=False),
            message='AI模型配置创建成功'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建AI模型配置失败: {str(e)}")
        logger.error(f"请求数据: {data}")
        return error_response(message=f'创建AI模型配置失败: {str(e)}')

@settings_bp.route('/ai-models/<model_id>', methods=['PUT'])
@jwt_required()
@admin_required
@tenant_required
def update_ai_model(model_id):
    """
    更新AI模型配置
    """
    try:
        tenant_id = get_jwt_identity()['tenant_id']
        data = request.get_json()
        
        model_config = AIModelConfig.query.filter_by(
            id=model_id,
            tenant_id=tenant_id
        ).first()
        
        if not model_config:
            return error_response(message='模型配置不存在')
        
        # 更新字段
        updatable_fields = [
            'model_name', 'model_type', 'model_id', 'api_key', 'api_base_url',
            'api_version', 'max_tokens', 'temperature', 'top_p', 'frequency_penalty',
            'presence_penalty', 'supported_features', 'use_cases', 'rate_limit',
            'timeout', 'retry_count', 'cost_per_1k_tokens', 'monthly_quota', 'is_default'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(model_config, field, data[field])
        
        # 如果设置为默认模型，取消其他模型的默认状态
        if data.get('is_default'):
            AIModelConfig.query.filter(
                AIModelConfig.tenant_id == tenant_id,
                AIModelConfig.id != model_id,
                AIModelConfig.is_default == True
            ).update({'is_default': False})
        
        model_config.updated_at = datetime.utcnow()
        db.session.commit()
        
        # 刷新LLM服务配置
        try:
            llm_service.refresh_default_model()
            logger.info(f"LLM服务配置已刷新，模型ID: {model_id}")
        except Exception as refresh_error:
            logger.warning(f"刷新LLM服务配置失败: {str(refresh_error)}")
        
        return success_response(
            data=model_config.to_dict(include_sensitive=False),
            message='AI模型配置更新成功'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新AI模型配置失败: {str(e)}")
        return error_response(message='更新AI模型配置失败')

@settings_bp.route('/ai-models/<model_id>', methods=['DELETE'])
@jwt_required()
@admin_required
@tenant_required
def delete_ai_model(model_id):
    """
    删除AI模型配置
    """
    try:
        tenant_id = get_jwt_identity()['tenant_id']
        
        model_config = AIModelConfig.query.filter_by(
            id=model_id,
            tenant_id=tenant_id
        ).first()
        
        if not model_config:
            return error_response(message='模型配置不存在')
        
        # 检查是否为默认模型
        if model_config.is_default:
            return error_response(message='不能删除默认模型，请先设置其他模型为默认')
        
        model_name = model_config.model_name
        db.session.delete(model_config)
        db.session.commit()
        
        # 刷新LLM服务配置
        try:
            llm_service.refresh_default_model()
            logger.info(f"LLM服务配置已刷新，已删除模型: {model_name}")
        except Exception as refresh_error:
            logger.warning(f"刷新LLM服务配置失败: {str(refresh_error)}")
        
        return success_response(message='AI模型配置删除成功')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除AI模型配置失败: {str(e)}")
        return error_response(message='删除AI模型配置失败')

@settings_bp.route('/ai-models/<model_id>/test', methods=['POST'])
@jwt_required()
@tenant_required
def test_ai_model(model_id):
    """
    测试AI模型连接
    """
    import requests
    import time
    
    try:
        tenant_id = get_jwt_identity()['tenant_id']
        
        model_config = AIModelConfig.query.filter_by(
            id=model_id,
            tenant_id=tenant_id
        ).first()
        
        if not model_config:
            return error_response(message='模型配置不存在')
        
        # 检查必要参数
        validation_errors = []
        if not model_config.api_key:
            validation_errors.append('API密钥未设置')
        if not model_config.api_base_url:
            validation_errors.append('API基础URL未设置')
        if not model_config.model_id:
            validation_errors.append('模型ID未设置')
        
        if validation_errors:
            return error_response(
                message=f'模型配置不完整: {", ".join(validation_errors)}'
            )
        
        # 实际测试模型连接
        start_time = time.time()
        
        test_data = {
            "model": model_config.model_id,
            "messages": [
                {"role": "user", "content": "Hello, this is a connection test. Please respond with 'Test successful'."}
            ],
            "max_tokens": 50,
            "temperature": 0.3
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # 根据模型类型设置不同的请求参数
        if model_config.model_type == 'azure' or 'azure.com' in (model_config.api_base_url or ''):
            # Azure OpenAI
            api_url = f"{model_config.api_base_url}/openai/deployments/{model_config.model_id}/chat/completions?api-version=2024-02-15-preview"
            headers["api-key"] = model_config.api_key
        elif model_config.model_type == 'openai':
            # OpenAI
            api_url = f"{model_config.api_base_url}/chat/completions"
            headers["Authorization"] = f"Bearer {model_config.api_key}"
        else:
            return error_response(message=f'不支持的模型类型: {model_config.model_type}')
        
        try:
            response = requests.post(
                api_url,
                headers=headers,
                json=test_data,
                timeout=15
            )
            
            response_time = round(time.time() - start_time, 2)
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    test_response = result['choices'][0]['message']['content']
                    
                    test_result = {
                        'status': 'success',
                        'response_time': response_time,
                        'test_message': '模型连接正常',
                        'test_response': test_response,
                        'model_info': {
                            'name': model_config.model_name,
                            'type': model_config.model_type,
                            'model_id': model_config.model_id,
                            'version': model_config.api_version
                        },
                        'usage': result.get('usage', {})
                    }
                    
                    return success_response(
                        data=test_result,
                        message='模型测试成功'
                    )
                else:
                    return error_response(
                        message=f'模型响应格式异常 (响应时间: {response_time}s)'
                    )
            else:
                error_detail = response.text[:200] if response.text else 'No error details'
                return error_response(
                    message=f'API请求失败 (HTTP {response.status_code}): {error_detail}'
                )
                
        except requests.exceptions.Timeout:
            response_time = round(time.time() - start_time, 2)
            return error_response(
                message=f'连接超时 (响应时间: {response_time}s)'
            )
        except requests.exceptions.ConnectionError:
            return error_response(
                message=f'连接错误，请检查API URL是否正确: {api_url}'
            )
        except Exception as req_error:
            response_time = round(time.time() - start_time, 2)
            return error_response(
                message=f'请求异常: {str(req_error)} (响应时间: {response_time}s)'
            )
        
    except Exception as e:
        logger.error(f"测试AI模型失败: {str(e)}")
        return error_response(message=f'测试AI模型失败: {str(e)}')

@settings_bp.route('/ai-models/<model_id>/set-default', methods=['POST'])
@jwt_required()
@admin_required
@tenant_required
def set_default_model(model_id):
    """
    设置默认AI模型
    """
    try:
        tenant_id = get_jwt_identity()['tenant_id']
        
        model_config = AIModelConfig.query.filter_by(
            id=model_id,
            tenant_id=tenant_id
        ).first()
        
        if not model_config:
            return error_response(message='模型配置不存在')
        
        # 取消其他模型的默认状态
        AIModelConfig.query.filter_by(
            tenant_id=tenant_id,
            is_default=True
        ).update({'is_default': False})
        
        # 设置当前模型为默认
        model_config.is_default = True
        model_config.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # 刷新LLM服务配置
        try:
            llm_service.refresh_default_model()
            logger.info(f"LLM服务配置已刷新，新默认模型ID: {model_id}")
        except Exception as refresh_error:
            logger.warning(f"刷新LLM服务配置失败: {str(refresh_error)}")
        
        return success_response(
            data=model_config.to_dict(include_sensitive=False),
            message='默认模型设置成功'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"设置默认模型失败: {str(e)}")
        return error_response(message='设置默认模型失败')

@settings_bp.route('/ai-models/<model_id>/toggle-active', methods=['POST'])
@jwt_required()
@admin_required
@tenant_required
def toggle_model_active(model_id):
    """
    切换AI模型的启用/禁用状态
    """
    try:
        tenant_id = get_jwt_identity()['tenant_id']
        
        model_config = AIModelConfig.query.filter_by(
            id=model_id,
            tenant_id=tenant_id
        ).first()
        
        if not model_config:
            return error_response(message='模型配置不存在')
        
        # 如果是默认模型且要禁用，需要先检查是否有其他可用模型
        if model_config.is_default and model_config.is_active:
            other_active_models = AIModelConfig.query.filter(
                AIModelConfig.tenant_id == tenant_id,
                AIModelConfig.id != model_id,
                AIModelConfig.is_active == True
            ).count()
            
            if other_active_models == 0:
                return error_response(message='不能禁用默认模型，请先启用其他模型或设置其他模型为默认')
        
        # 切换激活状态
        model_config.is_active = not model_config.is_active
        model_config.updated_at = datetime.utcnow()
        
        # 如果禁用了默认模型，自动设置第一个可用模型为默认
        if model_config.is_default and not model_config.is_active:
            model_config.is_default = False
            
            # 找到第一个可用模型设为默认
            new_default = AIModelConfig.query.filter_by(
                tenant_id=tenant_id,
                is_active=True
            ).filter(AIModelConfig.id != model_id).first()
            
            if new_default:
                new_default.is_default = True
                new_default.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # 刷新LLM服务配置
        try:
            llm_service.refresh_default_model()
            logger.info(f"LLM服务配置已刷新，模型ID: {model_id}，状态: {'启用' if model_config.is_active else '禁用'}")
        except Exception as refresh_error:
            logger.warning(f"刷新LLM服务配置失败: {str(refresh_error)}")
        
        status_text = '启用' if model_config.is_active else '禁用'
        return success_response(
            data=model_config.to_dict(include_sensitive=False),
            message=f'模型{status_text}成功'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"切换模型状态失败: {str(e)}")
        return error_response(message='切换模型状态失败')

@settings_bp.route('/system-info', methods=['GET'])
@jwt_required()
def get_system_info():
    """
    获取系统信息
    """
    try:
        # 获取AI模型统计信息
        total_models = AIModelConfig.query.count()
        active_models = AIModelConfig.query.filter_by(is_active=True).count()
        default_model_obj = AIModelConfig.query.filter_by(is_default=True).first()
        default_model = default_model_obj.model_name if default_model_obj else '未设置'
        
        system_info = {
            'version': '1.1.0',
            'environment': 'development',
            'database_status': 'connected',
            'ai_service_status': 'running',
            'total_models': total_models,
            'active_models': active_models,
            'default_model': default_model
        }
        
        return success_response(
            data=system_info,
            message='获取系统信息成功'
        )
        
    except Exception as e:
        logger.error(f"获取系统信息失败: {str(e)}")
        return error_response(message='获取系统信息失败')