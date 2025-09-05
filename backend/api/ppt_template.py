#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - API接口 - ppt_template.py

Description:
    PPT模板管理API接口，提供模板的上传、列表、删除等功能。

Author: Chang Xinglong
Date: 2025-08-31
Version: 1.0.0
License: Apache License 2.0
"""

import os
import uuid
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from typing import Dict, Any

from models.ppt_template import PPTTemplate
from utils.response import success_response, error_response
from utils.logger import get_logger
from utils.database import db

logger = get_logger(__name__)

# 创建蓝图
ppt_template_bp = Blueprint('ppt_template', __name__, url_prefix='/api/ppt-templates')

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'pptx', 'potx'}
UPLOAD_FOLDER = 'uploads/ppt_templates'

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'previews'), exist_ok=True)

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@ppt_template_bp.route('/upload', methods=['POST'])
def upload_template():
    """
    上传PPT模板
    """
    try:
        # 检查文件是否存在
        if 'file' not in request.files:
            return error_response("未找到文件", 400)
        
        file = request.files['file']
        if file.filename == '':
            return error_response("未选择文件", 400)
        
        if not allowed_file(file.filename):
            return error_response("不支持的文件格式，仅支持 .pptx 和 .potx 文件", 400)
        
        # 获取表单数据
        name = request.form.get('name', '')
        description = request.form.get('description', '')
        category = request.form.get('category', 'general')
        user_id = request.form.get('user_id', '1')  # 临时使用固定用户ID
        tenant_id = request.form.get('tenant_id', 'default')
        
        if not name:
            return error_response("模板名称不能为空", 400)
        
        # 检查模板名称是否已存在
        existing_template = PPTTemplate.query.filter_by(
            name=name, tenant_id=tenant_id
        ).first()
        if existing_template:
            return error_response("模板名称已存在", 400)
        
        # 生成安全的文件名
        filename = secure_filename(file.filename or '')
        file_id = str(uuid.uuid4())
        new_filename = f"{file_id}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, new_filename)
        
        # 保存文件
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        
        # 创建模板记录
        template = PPTTemplate(
            name=name,
            description=description,
            category=category,
            template_file_path=file_path,
            file_size=file_size,
            created_by=user_id,
            tenant_id=tenant_id,
            config={
                'title_font_size': 44,
                'content_font_size': 24,
                'title_color': '#1f497d',
                'content_color': '#444444',
                'background_color': '#ffffff'
            }
        )
        
        db.session.add(template)
        db.session.commit()
        
        return success_response({
            'template': template.to_dict(),
            'message': '模板上传成功'
        })
        
    except Exception as e:
        logger.error(f"模板上传失败: {str(e)}")
        db.session.rollback()
        return error_response("模板上传失败", 500)

@ppt_template_bp.route('/list', methods=['GET'])
def list_templates():
    """
    获取模板列表
    """
    try:
        # 获取查询参数
        category = request.args.get('category')
        tenant_id = request.args.get('tenant_id', 'default')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # 构建查询
        query = PPTTemplate.query.filter_by(is_active=True, tenant_id=tenant_id)
        
        if category:
            query = query.filter_by(category=category)
        
        # 分页查询
        pagination = query.order_by(
            PPTTemplate.is_default.desc(),  # type: ignore
            PPTTemplate.usage_count.desc(),  # type: ignore
            PPTTemplate.created_at.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        templates = [template.to_dict() for template in pagination.items]
        
        return success_response({
            'templates': templates,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        })
        
    except Exception as e:
        logger.error(f"获取模板列表失败: {str(e)}")
        return error_response("获取模板列表失败", 500)

@ppt_template_bp.route('/<template_id>', methods=['GET'])
def get_template(template_id: str):
    """
    获取单个模板详情
    """
    try:
        template = PPTTemplate.query.filter_by(id=template_id, is_active=True).first()
        if not template:
            return error_response("模板不存在", 404)
        
        return success_response({
            'template': template.to_dict()
        })
        
    except Exception as e:
        logger.error(f"获取模板详情失败: {str(e)}")
        return error_response("获取模板详情失败", 500)

@ppt_template_bp.route('/<template_id>/download', methods=['GET'])
def download_template(template_id: str):
    """
    下载模板文件
    """
    try:
        template = PPTTemplate.query.filter_by(id=template_id, is_active=True).first()
        if not template:
            return error_response("模板不存在", 404)
        
        if not os.path.exists(template.template_file_path):
            return error_response("模板文件不存在", 404)
        
        # 增加使用次数
        template.increment_usage()
        
        return send_file(
            template.template_file_path,
            as_attachment=True,
            download_name=f"{template.name}.pptx"
        )
        
    except Exception as e:
        logger.error(f"模板下载失败: {str(e)}")
        return error_response("模板下载失败", 500)

@ppt_template_bp.route('/<template_id>', methods=['PUT'])
def update_template(template_id: str):
    """
    更新模板信息
    """
    try:
        template = PPTTemplate.query.filter_by(id=template_id).first()
        if not template:
            return error_response("模板不存在", 404)
        
        data = request.get_json()
        
        # 更新允许的字段
        if 'name' in data:
            # 检查名称是否重复
            existing = PPTTemplate.query.filter(
                PPTTemplate.name == data['name'],
                PPTTemplate.id != template_id,
                PPTTemplate.tenant_id == template.tenant_id
            ).first()
            if existing:
                return error_response("模板名称已存在", 400)
            template.name = data['name']
        
        if 'description' in data:
            template.description = data['description']
        
        if 'category' in data:
            template.category = data['category']
        
        if 'config' in data:
            template.config = data['config']
        
        if 'is_active' in data:
            template.is_active = data['is_active']
        
        if 'is_default' in data:
            # 如果设置为默认模板，需要取消其他默认模板
            if data['is_default']:
                PPTTemplate.query.filter_by(
                    tenant_id=template.tenant_id,
                    is_default=True
                ).update({'is_default': False})
            template.is_default = data['is_default']
        
        db.session.commit()
        
        return success_response({
            'template': template.to_dict(),
            'message': '模板更新成功'
        })
        
    except Exception as e:
        logger.error(f"模板更新失败: {str(e)}")
        db.session.rollback()
        return error_response("模板更新失败", 500)

@ppt_template_bp.route('/<template_id>', methods=['DELETE'])
def delete_template(template_id: str):
    """
    删除模板
    """
    try:
        template = PPTTemplate.query.filter_by(id=template_id).first()
        if not template:
            return error_response("模板不存在", 404)
        
        # 检查是否为系统模板
        if template.is_system:
            return error_response("系统模板不能删除", 400)
        
        # 软删除：设置为不活跃
        template.is_active = False
        db.session.commit()
        
        return success_response({
            'message': '模板删除成功'
        })
        
    except Exception as e:
        logger.error(f"模板删除失败: {str(e)}")
        db.session.rollback()
        return error_response("模板删除失败", 500)

@ppt_template_bp.route('/categories', methods=['GET'])
def list_categories():
    """
    获取模板分类列表
    """
    try:
        tenant_id = request.args.get('tenant_id', 'default')
        
        # 从数据库中获取所有分类
        categories = db.session.query(PPTTemplate.category).filter_by(
            tenant_id=tenant_id,
            is_active=True
        ).distinct().all()
        
        category_list = [{
            'value': cat[0],
            'label': {
                'general': '通用',
                'education': '教育',
                'business': '商务',
                'technology': '科技',
                'medical': '医疗',
                'finance': '金融'
            }.get(cat[0], cat[0])
        } for cat in categories]
        
        return success_response({
            'categories': category_list
        })
        
    except Exception as e:
        logger.error(f"获取分类列表失败: {str(e)}")
        return error_response("获取分类列表失败", 500)