#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - API接口 - document.py

Description:
    文档管理API接口，提供PDF文件上传、解析、分类、存储等功能。

Author: Chang Xinglong
Date: 2025-01-21
Version: 1.0.0
License: Apache License 2.0
"""

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from typing import Dict, Any
import os

from services.document_service import get_document_service
from services.knowledge_graph_service import knowledge_graph_service
from models.document import Document, DocumentCategory
from models.knowledge import Subject
from utils.response import success_response, error_response
from utils.logger import get_logger
from utils.database import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

logger = get_logger(__name__)

# 创建蓝图
document_bp = Blueprint('document', __name__, url_prefix='/api/document')

@document_bp.route('/upload', methods=['POST'])
def upload_document():
    """
    上传文档文件
    
    请求参数:
    - file: 文档文件（multipart/form-data）
    - title: 文档标题（可选）
    - description: 文档描述（可选）
    - category_id: 分类ID（可选）
    - tags: 标签列表，逗号分隔（可选）
    """
    try:
        logger.info(f"收到文档上传请求，files: {list(request.files.keys())}, form: {dict(request.form)}")
        
        # 检查文件是否存在
        if 'file' not in request.files:
            logger.error(f"未找到上传文件，可用字段: {list(request.files.keys())}")
            return error_response("未找到上传文件", 400)
        
        file = request.files['file']
        if file.filename == '':
            logger.error("文件名为空")
            return error_response("未选择文件", 400)
        
        logger.info(f"准备上传文件: {file.filename}, 大小: {file.content_length if hasattr(file, 'content_length') else 'unknown'}")
        
        # 获取其他参数
        title = request.form.get('title')
        description = request.form.get('description')
        category_id = request.form.get('category_id')
        tags_str = request.form.get('tags', '')
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else None
        
        # 暂时使用固定的用户ID和租户ID
        user_id = "1"
        tenant_id = "default"
        
        # 创建文档
        document_service = get_document_service()
        document = document_service.create_document(
            file=file,
            user_id=user_id,
            tenant_id=tenant_id,
            title=title,
            description=description,
            category_id=category_id,
            tags=tags
        )
        
        return success_response({
            'document_id': document.id,
            'filename': document.filename,
            'title': document.title,
            'file_size': document.file_size,
            'file_type': document.file_type,
            'parse_status': document.parse_status,
            'created_at': document.created_at.isoformat()
        }, "文档上传成功")
        
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"文档上传失败: {e}")
        return error_response("文档上传失败", 500)

@document_bp.route('/list', methods=['GET'])
def list_documents():
    """
    获取文档列表
    
    查询参数:
    - category_id: 分类ID（可选）
    - search: 搜索关键词（可选）
    - page: 页码，默认1
    - per_page: 每页数量，默认20
    """
    try:
        # 获取查询参数
        category_id = request.args.get('category_id')
        search = request.args.get('search')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # 暂时使用固定的用户ID和租户ID
        user_id = "1"
        tenant_id = "default"
        
        # 获取文档列表
        document_service = get_document_service()
        result = document_service.get_documents(
            user_id=user_id,
            tenant_id=tenant_id,
            category_id=category_id,
            search=search,
            page=page,
            per_page=per_page
        )
        
        return success_response(result, "获取文档列表成功")
        
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        return error_response("获取文档列表失败", 500)

@document_bp.route('/<document_id>', methods=['GET'])
def get_document(document_id: str):
    """
    获取文档详情
    
    路径参数:
    - document_id: 文档ID
    """
    try:
        # 暂时使用固定的用户ID
        user_id = "1"
        
        document = Document.query.filter_by(id=document_id, user_id=user_id).first()
        if not document:
            return error_response("文档不存在或无权限访问", 404)
        
        # 获取文档页面内容
        pages = [page.to_dict() for page in document.pages]
        
        # 获取分析结果
        analyses = [analysis.to_dict() for analysis in document.analyses]
        
        result = {
            **document.to_dict(),
            'pages': pages,
            'analyses': analyses
        }
        
        return success_response(result, "获取文档详情成功")
        
    except Exception as e:
        logger.error(f"获取文档详情失败: {e}")
        return error_response("获取文档详情失败", 500)

@document_bp.route('/<document_id>/download', methods=['GET'])
def download_document(document_id: str):
    """
    下载文档文件
    
    路径参数:
    - document_id: 文档ID
    """
    try:
        # 查找文档，不限制用户ID（因为PPT生成的文档应该可以被任何用户下载）
        document = Document.query.filter_by(id=document_id).first()
        if not document:
            return error_response("文档不存在", 404)
        
        if not os.path.exists(document.file_path):
            return error_response("文件不存在", 404)
        
        return send_file(
            document.file_path,
            as_attachment=True,
            download_name=document.filename
        )
        
    except Exception as e:
        logger.error(f"文档下载失败: {e}")
        return error_response("文档下载失败", 500)

@document_bp.route('/<document_id>/preview', methods=['GET'])
def preview_document(document_id: str):
    """
    预览PDF文档
    
    路径参数:
    - document_id: 文档ID
    """
    try:
        # 暂时使用固定的用户ID
        user_id = "1"
        
        document = Document.query.filter_by(id=document_id, user_id=user_id).first()
        if not document:
            return error_response("文档不存在或无权限访问", 404)
        
        # 检查文件类型是否为PDF
        if document.file_type.lower() != 'pdf':
            return error_response("只支持PDF文件预览", 400)
        
        # 如果file_path为空，尝试根据文件名在uploads/documents目录中查找
        file_path = document.file_path
        if not file_path or not os.path.exists(file_path):
            # 在uploads/documents目录中查找包含文档文件名的文件
            uploads_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'documents')
            uploads_dir = os.path.abspath(uploads_dir)
            
            if os.path.exists(uploads_dir):
                for filename in os.listdir(uploads_dir):
                    if document.filename in filename and filename.endswith('.pdf'):
                        file_path = os.path.join(uploads_dir, filename)
                        break
        
        if not file_path or not os.path.exists(file_path):
            return error_response("文件不存在", 404)
        
        return send_file(
            file_path,
            as_attachment=False,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"文档预览失败: {e}")
        return error_response("文档预览失败", 500)

@document_bp.route('/<document_id>', methods=['PUT'])
def update_document(document_id: str):
    """
    更新文档信息
    
    路径参数:
    - document_id: 文档ID
    
    请求参数:
    - title: 文档标题（可选）
    - description: 文档描述（可选）
    - category_id: 分类ID（可选）
    - tags: 标签列表（可选）
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("缺少请求数据", 400)
        
        # 暂时使用固定的用户ID
        user_id = "1"
        
        document = Document.query.filter_by(id=document_id, user_id=user_id).first()
        if not document:
            return error_response("文档不存在或无权限访问", 404)
        
        # 更新文档信息
        if 'title' in data:
            document.title = data['title']
        if 'description' in data:
            document.description = data['description']
        if 'category_id' in data:
            document.category_id = data['category_id']
        if 'tags' in data:
            document.tags = data['tags']
        
        db.session.commit()
        
        return success_response(document.to_dict(), "文档更新成功")
        
    except Exception as e:
        logger.error(f"文档更新失败: {e}")
        db.session.rollback()
        return error_response("文档更新失败", 500)

@document_bp.route('/<document_id>', methods=['DELETE'])
def delete_document(document_id: str):
    """
    删除文档
    
    路径参数:
    - document_id: 文档ID
    """
    try:
        # 暂时使用固定的用户ID
        user_id = "1"
        
        document_service = get_document_service()
        success = document_service.delete_document(document_id, user_id)
        
        if success:
            return success_response({}, "文档删除成功")
        else:
            return error_response("文档删除失败", 500)
        
    except Exception as e:
        logger.error(f"文档删除失败: {e}")
        return error_response("文档删除失败", 500)

@document_bp.route('/<document_id>/parse-status', methods=['GET'])
def get_parse_status(document_id: str):
    """
    获取文档解析状态
    
    路径参数:
    - document_id: 文档ID
    """
    try:
        # 暂时使用固定的用户ID
        user_id = "1"
        
        document = Document.query.filter_by(id=document_id, user_id=user_id).first()
        if not document:
            return error_response("文档不存在或无权限访问", 404)
        
        result = {
            'document_id': document.id,
            'parse_status': document.parse_status,
            'parse_progress': document.parse_progress,
            'parse_error': document.parse_error,
            'parsed_at': document.parsed_at.isoformat() if document.parsed_at else None
        }
        
        return success_response(result, "获取解析状态成功")
        
    except Exception as e:
        logger.error(f"获取解析状态失败: {e}")
        return error_response("获取解析状态失败", 500)

@document_bp.route('/categories', methods=['GET'])
def list_categories():
    """
    获取文档分类列表
    """
    try:
        # 暂时使用固定的租户ID
        tenant_id = "default"
        
        categories = DocumentCategory.query.filter_by(tenant_id=tenant_id).all()
        result = [category.to_dict() for category in categories]
        
        return success_response(result, "获取分类列表成功")
        
    except Exception as e:
        logger.error(f"获取分类列表失败: {e}")
        return error_response("获取分类列表失败", 500)

@document_bp.route('/categories', methods=['POST'])
def create_category():
    """
    创建文档分类
    
    请求参数:
    - name: 分类名称
    - description: 分类描述（可选）
    - parent_id: 父分类ID（可选）
    """
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return error_response("缺少必要参数：name", 400)
        
        # 暂时使用固定的租户ID
        tenant_id = "default"
        
        category = DocumentCategory(
            tenant_id=tenant_id,
            name=data['name'],
            description=data.get('description'),
            parent_id=data.get('parent_id')
        )
        
        db.session.add(category)
        db.session.commit()
        
        return success_response(category.to_dict(), "分类创建成功")
        
    except Exception as e:
        logger.error(f"分类创建失败: {e}")
        db.session.rollback()
        return error_response("分类创建失败", 500)

@document_bp.route('/stats', methods=['GET'])
def get_document_stats():
    """
    获取文档统计信息
    """
    try:
        # 暂时使用固定的用户ID和租户ID
        user_id = "1"
        tenant_id = "default"
        
        # 统计文档数量
        total_documents = Document.query.filter_by(user_id=user_id, tenant_id=tenant_id).count()
        
        # 按状态统计
        pending_count = Document.query.filter_by(
            user_id=user_id, tenant_id=tenant_id, parse_status='pending'
        ).count()
        
        processing_count = Document.query.filter_by(
            user_id=user_id, tenant_id=tenant_id, parse_status='processing'
        ).count()
        
        completed_count = Document.query.filter_by(
            user_id=user_id, tenant_id=tenant_id, parse_status='completed'
        ).count()
        
        failed_count = Document.query.filter_by(
            user_id=user_id, tenant_id=tenant_id, parse_status='failed'
        ).count()
        
        # 按文件类型统计
        from sqlalchemy import func
        type_stats = db.session.query(
            Document.file_type,
            func.count(Document.id).label('count')
        ).filter_by(
            user_id=user_id, tenant_id=tenant_id
        ).group_by(Document.file_type).all()
        
        result = {
            'total_documents': total_documents,
            'status_stats': {
                'pending': pending_count,
                'processing': processing_count,
                'completed': completed_count,
                'failed': failed_count
            },
            'type_stats': {stat.file_type: stat.count for stat in type_stats}
        }
        
        return success_response(result, "获取统计信息成功")
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return error_response("获取统计信息失败", 500)

@document_bp.route('/upload-by-subject', methods=['POST'])
@jwt_required()
def upload_document_by_subject():
    """
    按学科上传文档并自动生成知识图谱
    
    请求参数:
    - file: 文档文件（multipart/form-data）
    - subject_id: 学科ID（必需）
    - title: 文档标题（可选）
    - description: 文档描述（可选）
    - tags: 标签列表，逗号分隔（可选）
    - auto_generate_knowledge_graph: 是否自动生成知识图谱（默认true）
    """
    try:
        current_user_identity = get_jwt_identity()
        user_id = current_user_identity.get('user_id')
        tenant_id = current_user_identity.get('tenant_id')
        
        # 检查文件是否存在
        if 'file' not in request.files:
            return error_response("未找到上传文件", 400)
        
        file = request.files['file']
        if file.filename == '':
            return error_response("未选择文件", 400)
        
        # 获取参数
        subject_id = request.form.get('subject_id')
        if not subject_id:
            return error_response("学科ID不能为空", 400)
        
        # 验证学科
        subject = Subject.query.filter_by(id=subject_id, tenant_id=tenant_id).first()
        if not subject:
            return error_response('学科不存在', 404)
        
        title = request.form.get('title')
        description = request.form.get('description')
        tags_str = request.form.get('tags', '')
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
        
        # 添加学科标签
        if subject.name not in tags:
            tags.append(subject.name)
        
        auto_generate_kg = request.form.get('auto_generate_knowledge_graph', 'true').lower() == 'true'
        
        # 创建文档
        document_service = get_document_service()
        document = document_service.create_document(
             file=file,
             user_id=user_id,
             tenant_id=tenant_id,
             title=title,
             description=description,
             category_id=None,
             tags=tags
         )
        
        result = {
            'document_id': document.id,
            'filename': document.filename,
            'title': document.title,
            'file_size': document.file_size,
            'file_type': document.file_type,
            'parse_status': document.parse_status,
            'subject_id': subject_id,
            'subject_name': subject.name,
            'tags': tags,
            'created_at': document.created_at.isoformat()
        }
        
        # 自动生成知识图谱
        if auto_generate_kg:
            try:
                # 更新知识点（从文档中提取）
                knowledge_graph_service.update_knowledge_point_from_document(
                    document_id=document.id
                )
                
                # 生成知识图谱
                knowledge_graph = knowledge_graph_service.generate_knowledge_graph(
                    subject_id=subject_id,
                    user_id=user_id
                )
                
                result['knowledge_graph_generated'] = True
                result['knowledge_graph_stats'] = knowledge_graph.get('statistics', {})
                
            except Exception as kg_error:
                logger.warning(f"知识图谱生成失败: {kg_error}")
                result['knowledge_graph_generated'] = False
                result['knowledge_graph_error'] = str(kg_error)
        
        return success_response(result, "文档上传成功")
        
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"按学科上传文档失败: {e}")
        return error_response("文档上传失败", 500)

@document_bp.route('/search-by-subject/<subject_id>', methods=['GET'])
@jwt_required()
def search_documents_by_subject(subject_id):
    """
    按学科搜索文档
    
    查询参数:
    - query: 搜索关键词（可选）
    - tags: 标签过滤，逗号分隔（可选）
    - page: 页码（默认1）
    - per_page: 每页数量（默认20）
    """
    try:
        current_user_identity = get_jwt_identity()
        user_id = current_user_identity.get('user_id')
        tenant_id = current_user_identity.get('tenant_id')
        
        # 验证学科
        subject = Subject.query.filter_by(id=subject_id, tenant_id=tenant_id).first()
        if not subject:
            return error_response('学科不存在', 404)
        
        # 获取查询参数
        query = request.args.get('query', '')
        tags_str = request.args.get('tags', '')
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        # 添加学科标签到搜索条件
        if subject.name not in tags:
            tags.append(subject.name)
        
        # 搜索文档
        document_service = get_document_service()
        results = document_service.search_documents(
            query=query,
            user_id=user_id,
            tenant_id=tenant_id,
            search_tags=True,
            subject_filter=subject_id
        )
        
        # 处理分页
        total = len(results)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_docs = results[start_idx:end_idx]
        
        return success_response({
            'subject_id': subject_id,
            'subject_name': subject.name,
            'documents': paginated_docs,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        logger.error(f"按学科搜索文档失败: {e}")
        return error_response("搜索失败", 500)

@document_bp.route('/generate-knowledge-graph/<subject_id>', methods=['POST'])
@jwt_required()
def generate_knowledge_graph_from_documents(subject_id):
    """
    从文档生成知识图谱
    
    请求参数:
    - document_ids: 文档ID列表（可选，不提供则使用该学科的所有文档）
    """
    try:
        current_user_identity = get_jwt_identity()
        user_id = current_user_identity.get('user_id')
        tenant_id = current_user_identity.get('tenant_id')
        
        # 验证学科
        subject = Subject.query.filter_by(id=subject_id, tenant_id=tenant_id).first()
        if not subject:
            return error_response('学科不存在', 404)
        
        data = request.get_json() or {}
        document_ids = data.get('document_ids', [])
        
        # 更新知识点（从文档中提取）
        if document_ids:
            for doc_id in document_ids:
                knowledge_graph_service.update_knowledge_point_from_document(
                    document_id=doc_id
                )
        else:
            # 处理该学科的所有文档
            documents = Document.query.filter_by(tenant_id=tenant_id).all()
            for doc in documents:
                if subject.name in (doc.tags or []):
                    knowledge_graph_service.update_knowledge_point_from_document(
                        document_id=doc.id
                    )
        
        # 生成知识图谱
        knowledge_graph = knowledge_graph_service.generate_knowledge_graph(
            subject_id=subject_id,
            user_id=user_id
        )
        
        return success_response({
            'subject_id': subject_id,
            'subject_name': subject.name,
            'knowledge_graph': knowledge_graph,
            'generated_at': datetime.now().isoformat()
        }, "知识图谱生成成功")
        
    except Exception as e:
        logger.error(f"生成知识图谱失败: {e}")
        return error_response("生成知识图谱失败", 500)