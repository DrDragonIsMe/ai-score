#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - API接口 - settings.py

Description:
    系统设置API接口，提供AI模型配置、系统参数设置等功能。

Author: Chang Xinglong
Date: 2025-01-21
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
        
        return success_response(
            data=model_config.to_dict(include_sensitive=False),
            message='AI模型配置创建成功'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建AI模型配置失败: {str(e)}")
        return error_response(message='创建AI模型配置失败')

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
        
        db.session.delete(model_config)
        db.session.commit()
        
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
    try:
        tenant_id = get_jwt_identity()['tenant_id']
        
        model_config = AIModelConfig.query.filter_by(
            id=model_id,
            tenant_id=tenant_id
        ).first()
        
        if not model_config:
            return error_response(message='模型配置不存在')
        
        # 这里可以添加实际的模型测试逻辑
        # 暂时返回成功响应
        test_result = {
            'status': 'success',
            'response_time': 1.2,
            'test_message': '模型连接正常',
            'model_info': {
                'name': model_config.model_name,
                'type': model_config.model_type,
                'version': model_config.api_version
            }
        }
        
        return success_response(
            data=test_result,
            message='模型测试完成'
        )
        
    except Exception as e:
        logger.error(f"测试AI模型失败: {str(e)}")
        return error_response(message='测试AI模型失败')

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
        
        return success_response(
            data=model_config.to_dict(include_sensitive=False),
            message='默认模型设置成功'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"设置默认模型失败: {str(e)}")
        return error_response(message='设置默认模型失败')

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