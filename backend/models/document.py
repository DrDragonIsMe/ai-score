#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 数据模型 - document.py

Description:
    文档数据模型，定义PDF文件信息、分类、解析内容等数据结构。

Author: Chang Xinglong
Date: 2025-01-21
Version: 1.0.0
License: Apache License 2.0
"""

from datetime import datetime
from utils.database import db
import uuid

class DocumentCategory(db.Model):
    """文档分类模型"""
    
    __tablename__ = 'document_categories'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    
    # 基本信息
    name = db.Column(db.String(50), nullable=False, comment='分类名称')
    description = db.Column(db.Text, comment='分类描述')
    color = db.Column(db.String(7), default='#1976d2', comment='分类颜色')
    icon = db.Column(db.String(50), default='folder', comment='分类图标')
    
    # 分类属性
    parent_id = db.Column(db.String(36), db.ForeignKey('document_categories.id'), nullable=True)
    sort_order = db.Column(db.Integer, default=0, comment='排序顺序')
    is_system = db.Column(db.Boolean, default=False, comment='是否系统分类')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    parent = db.relationship('DocumentCategory', remote_side=[id], backref='children')
    documents = db.relationship('Document', backref='category', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'parent_id': self.parent_id,
            'sort_order': self.sort_order,
            'is_system': self.is_system,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'document_count': self.documents.count()
        }

class Document(db.Model):
    """文档模型"""
    
    __tablename__ = 'documents'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.String(36), db.ForeignKey('document_categories.id'), nullable=True)
    
    # 文件基本信息
    filename = db.Column(db.String(255), nullable=False, comment='原始文件名')
    file_path = db.Column(db.String(500), nullable=False, comment='文件存储路径')
    file_size = db.Column(db.BigInteger, nullable=False, comment='文件大小(字节)')
    file_type = db.Column(db.String(20), nullable=False, comment='文件类型')
    mime_type = db.Column(db.String(100), comment='MIME类型')
    file_hash = db.Column(db.String(64), comment='文件哈希值')
    
    # 文档元信息
    title = db.Column(db.String(200), comment='文档标题')
    description = db.Column(db.Text, comment='文档描述')
    tags = db.Column(db.JSON, default=[], comment='标签列表')
    language = db.Column(db.String(10), default='zh', comment='文档语言')
    
    # 解析状态
    parse_status = db.Column(db.String(20), default='pending', comment='解析状态：pending/processing/completed/failed')
    parse_progress = db.Column(db.Integer, default=0, comment='解析进度(0-100)')
    parse_error = db.Column(db.Text, comment='解析错误信息')
    parsed_at = db.Column(db.DateTime, comment='解析完成时间')
    
    # 文档统计
    page_count = db.Column(db.Integer, comment='页数')
    word_count = db.Column(db.Integer, comment='字数')
    character_count = db.Column(db.Integer, comment='字符数')
    
    # 访问控制
    is_public = db.Column(db.Boolean, default=False, comment='是否公开')
    is_favorite = db.Column(db.Boolean, default=False, comment='是否收藏')
    access_count = db.Column(db.Integer, default=0, comment='访问次数')
    last_accessed = db.Column(db.DateTime, comment='最后访问时间')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = db.relationship('User', backref='documents')
    pages = db.relationship('DocumentPage', backref='document', lazy='dynamic', cascade='all, delete-orphan')
    annotations = db.relationship('DocumentAnnotation', backref='document', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'title': self.title,
            'description': self.description,
            'tags': self.tags,
            'language': self.language,
            'parse_status': self.parse_status,
            'parse_progress': self.parse_progress,
            'page_count': self.page_count,
            'word_count': self.word_count,
            'character_count': self.character_count,
            'is_public': self.is_public,
            'is_favorite': self.is_favorite,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'category': self.category.to_dict() if self.category else None
        }

class DocumentPage(db.Model):
    """文档页面模型"""
    
    __tablename__ = 'document_pages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = db.Column(db.String(36), db.ForeignKey('documents.id'), nullable=False)
    
    # 页面信息
    page_number = db.Column(db.Integer, nullable=False, comment='页码')
    page_content = db.Column(db.Text, comment='页面文本内容')
    page_image_path = db.Column(db.String(500), comment='页面图片路径')
    
    # 解析信息
    ocr_confidence = db.Column(db.Float, comment='OCR识别置信度')
    extracted_elements = db.Column(db.JSON, default=[], comment='提取的元素(图片、表格等)')
    
    # AI分析结果
    content_type = db.Column(db.String(50), comment='内容类型：text/image/table/mixed')
    topics = db.Column(db.JSON, default=[], comment='主题标签')
    key_concepts = db.Column(db.JSON, default=[], comment='关键概念')
    summary = db.Column(db.Text, comment='页面摘要')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'page_number': self.page_number,
            'page_content': self.page_content,
            'ocr_confidence': self.ocr_confidence,
            'content_type': self.content_type,
            'topics': self.topics,
            'key_concepts': self.key_concepts,
            'summary': self.summary,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class DocumentAnnotation(db.Model):
    """文档标注模型"""
    
    __tablename__ = 'document_annotations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = db.Column(db.String(36), db.ForeignKey('documents.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # 标注信息
    annotation_type = db.Column(db.String(20), nullable=False, comment='标注类型：highlight/note/bookmark')
    page_number = db.Column(db.Integer, comment='页码')
    position = db.Column(db.JSON, comment='标注位置信息')
    selected_text = db.Column(db.Text, comment='选中的文本')
    
    # 标注内容
    content = db.Column(db.Text, comment='标注内容')
    color = db.Column(db.String(7), default='#ffeb3b', comment='标注颜色')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = db.relationship('User', backref='document_annotations')
    
    def to_dict(self):
        return {
            'id': self.id,
            'annotation_type': self.annotation_type,
            'page_number': self.page_number,
            'position': self.position,
            'selected_text': self.selected_text,
            'content': self.content,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class DocumentAnalysis(db.Model):
    """文档AI分析结果模型"""
    
    __tablename__ = 'document_analyses'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = db.Column(db.String(36), db.ForeignKey('documents.id'), nullable=False)
    
    # 分析类型
    analysis_type = db.Column(db.String(50), nullable=False, comment='分析类型：classification/summary/qa/knowledge_extraction')
    analysis_version = db.Column(db.String(20), default='1.0', comment='分析版本')
    
    # 分析结果
    result = db.Column(db.JSON, nullable=False, comment='分析结果')
    confidence_score = db.Column(db.Float, comment='置信度分数')
    processing_time = db.Column(db.Float, comment='处理时间(秒)')
    
    # 分析状态
    status = db.Column(db.String(20), default='completed', comment='分析状态')
    error_message = db.Column(db.Text, comment='错误信息')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    document = db.relationship('Document', backref='analyses')
    
    def to_dict(self):
        return {
            'id': self.id,
            'analysis_type': self.analysis_type,
            'analysis_version': self.analysis_version,
            'result': self.result,
            'confidence_score': self.confidence_score,
            'processing_time': self.processing_time,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }