#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 数据模型 - exam_papers.py

Description:
    真题试卷相关数据模型，包括真题、试卷、题目等。

Author: Chang Xinglong
Date: 2025-08-31
Version: 1.0.0
License: Apache License 2.0
"""

from datetime import datetime
from utils.database import db
import uuid

class ExamPaper(db.Model):
    """试卷模型"""
    
    __tablename__ = 'exam_papers'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    subject_id = db.Column(db.String(36), db.ForeignKey('subjects.id'), nullable=False)
    
    # 基本信息
    title = db.Column(db.String(200), nullable=False, comment='试卷标题')
    description = db.Column(db.Text, comment='试卷描述')
    year = db.Column(db.Integer, comment='考试年份')
    exam_type = db.Column(db.String(50), comment='考试类型：高考/模拟考/月考等')
    region = db.Column(db.String(50), comment='考试地区')
    
    # 试卷属性
    total_score = db.Column(db.Integer, default=150, comment='总分')
    duration = db.Column(db.Integer, comment='考试时长(分钟)')
    difficulty_level = db.Column(db.Integer, default=3, comment='难度等级1-5')
    tags = db.Column(db.JSON, default=[], comment='标签列表')
    
    # 文件信息
    file_path = db.Column(db.String(500), comment='文件路径')
    file_type = db.Column(db.String(20), comment='文件类型：pdf/image')
    file_size = db.Column(db.Integer, comment='文件大小(字节)')
    
    # 解析状态
    parse_status = db.Column(db.String(20), default='pending', comment='解析状态：pending/processing/completed/failed')
    parse_result = db.Column(db.JSON, comment='解析结果')
    
    # 统计信息
    question_count = db.Column(db.Integer, default=0, comment='题目数量')
    download_count = db.Column(db.Integer, default=0, comment='下载次数')
    
    # 状态
    is_active = db.Column(db.Boolean, default=True)
    is_public = db.Column(db.Boolean, default=False, comment='是否公开')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    questions = db.relationship('Question', backref='exam_paper', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ExamPaper {self.title}>'
    
    def to_dict(self, include_questions=False):
        data = {
            'id': str(self.id),
            'title': self.title,
            'description': self.description,
            'year': self.year,
            'exam_type': self.exam_type,
            'region': self.region,
            'total_score': self.total_score,
            'duration': self.duration,
            'difficulty_level': self.difficulty_level,
            'tags': self.tags or [],
            'file_type': self.file_type,
            'file_size': self.file_size,
            'parse_status': self.parse_status,
            'question_count': self.question_count,
            'download_count': self.download_count,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at is not None else None
        }
        
        if include_questions:
            data['questions'] = [q.to_dict() for q in self.questions.filter_by(is_active=True).all()]
        
        return data

class KnowledgeGraph(db.Model):
    """知识图谱模型 - 用于星图展示"""
    
    __tablename__ = 'knowledge_graphs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_id = db.Column(db.String(36), db.ForeignKey('subjects.id'), nullable=False)
    
    # 图谱信息
    name = db.Column(db.String(100), nullable=False, comment='图谱名称')
    description = db.Column(db.Text, comment='图谱描述')
    year = db.Column(db.Integer, comment='适用年份')
    graph_type = db.Column(db.String(50), default='exam_scope', comment='图谱类型')
    
    # 图谱数据
    nodes = db.Column(db.JSON, comment='节点数据')
    edges = db.Column(db.JSON, comment='边数据')
    layout_config = db.Column(db.JSON, comment='布局配置')
    
    # 状态
    is_active = db.Column(db.Boolean, default=True)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<KnowledgeGraph {self.name}>'
    
    def to_dict(self):
        # 从nodes中提取content（如果存在）
        content = None
        if self.nodes and len(self.nodes) > 0:
            for node in self.nodes:
                if node.get('content'):
                    content = node.get('content')
                    break
        
        # 从nodes中提取tags（统一标签体系）
        tags = []
        if self.nodes and len(self.nodes) > 0:
            tags_set = set()
            for node in self.nodes:
                node_tags = node.get('tags', [])
                if isinstance(node_tags, list):
                    for tag in node_tags:
                        if tag and isinstance(tag, str):
                            tags_set.add(tag.strip())
            tags = list(tags_set)
        
        return {
            'id': str(self.id),
            'subject_id': str(self.subject_id),
            'name': self.name,
            'description': self.description,
            'year': self.year,
            'graph_type': self.graph_type,
            'nodes': self.nodes,
            'edges': self.edges,
            'layout_config': self.layout_config,
            'content': content,
            'tags': tags,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at is not None else None
        }