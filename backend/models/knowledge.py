#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 数据模型 - knowledge.py

Description:
    知识点数据模型，定义学科知识体系结构。

Author: Chang Xinglong
Date: 2025-08-31
Version: 1.0.0
License: Apache License 2.0
"""


from datetime import datetime
from utils.database import db
import uuid

class Subject(db.Model):
    """学科模型 - 九科知识图谱"""
    
    __tablename__ = 'subjects'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    
    # 基本信息
    code = db.Column(db.String(20), nullable=False, comment='学科代码')
    name = db.Column(db.String(50), nullable=False, comment='学科名称')
    name_en = db.Column(db.String(50), comment='英文名称')
    description = db.Column(db.Text, comment='学科描述')
    
    # 学科属性
    category = db.Column(db.String(20), comment='学科类别：science/liberal_arts/language')
    grade_range = db.Column(db.JSON, default=[], comment='适用年级范围')
    total_score = db.Column(db.Integer, default=150, comment='总分')
    
    # 状态
    is_active = db.Column(db.Boolean, default=True, comment='是否激活')
    sort_order = db.Column(db.Integer, default=0, comment='排序')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    chapters = db.relationship('Chapter', backref='subject', lazy='dynamic', cascade='all, delete-orphan')
    
    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'code', name='uq_tenant_subject_code'),
    )
    
    def __repr__(self):
        return f'<Subject {self.name}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'code': self.code,
            'name': self.name,
            'name_en': self.name_en,
            'description': self.description,
            'category': self.category,
            'grade_range': self.grade_range,
            'total_score': self.total_score,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'chapter_count': self.chapters.count()
        }

class Chapter(db.Model):
    """章节模型"""
    
    __tablename__ = 'chapters'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_id = db.Column(db.String(36), db.ForeignKey('subjects.id'), nullable=False)
    
    # 基本信息
    code = db.Column(db.String(20), nullable=False, comment='章节代码')
    name = db.Column(db.String(100), nullable=False, comment='章节名称')
    description = db.Column(db.Text, comment='章节描述')
    
    # 章节属性
    grade = db.Column(db.String(10), comment='适用年级')
    semester = db.Column(db.Integer, comment='学期：1上学期，2下学期')
    difficulty = db.Column(db.Integer, default=3, comment='难度等级1-5')
    importance = db.Column(db.Integer, default=3, comment='重要程度1-5')
    
    # 考试相关
    exam_frequency = db.Column(db.Integer, default=0, comment='近5年高考出现次数')
    avg_score_rate = db.Column(db.Float, comment='平均得分率')
    
    # 状态
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    knowledge_points = db.relationship('KnowledgePoint', backref='chapter', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Chapter {self.name}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'subject_id': str(self.subject_id),
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'grade': self.grade,
            'semester': self.semester,
            'difficulty': self.difficulty,
            'importance': self.importance,
            'exam_frequency': self.exam_frequency,
            'avg_score_rate': self.avg_score_rate,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'knowledge_point_count': self.knowledge_points.count()
        }

class KnowledgePoint(db.Model):
    """知识点模型"""
    
    __tablename__ = 'knowledge_points'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chapter_id = db.Column(db.String(36), db.ForeignKey('chapters.id'), nullable=False)
    
    # 基本信息
    code = db.Column(db.String(30), nullable=False, comment='知识点代码')
    name = db.Column(db.String(100), nullable=False, comment='知识点名称')
    description = db.Column(db.Text, comment='知识点描述')
    content = db.Column(db.Text, comment='知识点内容')
    
    # 知识点属性
    difficulty = db.Column(db.Integer, default=3, comment='难度等级1-5')
    importance = db.Column(db.Integer, default=3, comment='重要程度1-5')
    exam_frequency = db.Column(db.Integer, default=0, comment='近5年高考出现次数')
    
    # 学习相关
    estimated_time = db.Column(db.Integer, comment='预估学习时间(分钟)')
    prerequisites = db.Column(db.JSON, default=[], comment='前置知识点ID列表')
    related_points = db.Column(db.JSON, default=[], comment='相关知识点ID列表')
    
    # 标签
    tags = db.Column(db.JSON, default=[], comment='标签列表')
    keywords = db.Column(db.JSON, default=[], comment='关键词列表')
    
    # 状态
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    sub_knowledge_points = db.relationship('SubKnowledgePoint', backref='knowledge_point', lazy='dynamic', cascade='all, delete-orphan')
    questions = db.relationship('Question', backref='knowledge_point', lazy='dynamic')
    
    def __repr__(self):
        return f'<KnowledgePoint {self.name}>'
    
    def get_related_points(self):
        """获取相关知识点"""
        if not self.related_points:
            return []
        return KnowledgePoint.query.filter(KnowledgePoint.id.in_(self.related_points)).all()
    
    def get_prerequisites(self):
        """获取前置知识点"""
        if not self.prerequisites:
            return []
        return KnowledgePoint.query.filter(KnowledgePoint.id.in_(self.prerequisites)).all()
    
    def to_dict(self, include_content=False):
        data = {
            'id': str(self.id),
            'chapter_id': str(self.chapter_id),
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'difficulty': self.difficulty,
            'importance': self.importance,
            'exam_frequency': self.exam_frequency,
            'estimated_time': self.estimated_time,
            'prerequisites': self.prerequisites,
            'related_points': self.related_points,
            'tags': self.tags,
            'keywords': self.keywords,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'sub_point_count': self.sub_knowledge_points.count(),
            'question_count': self.questions.count()
        }
        if include_content:
            data['content'] = self.content
        return data

class SubKnowledgePoint(db.Model):
    """子知识点模型"""
    
    __tablename__ = 'sub_knowledge_points'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    knowledge_point_id = db.Column(db.String(36), db.ForeignKey('knowledge_points.id'), nullable=False)
    
    # 基本信息
    code = db.Column(db.String(40), nullable=False, comment='子知识点代码')
    name = db.Column(db.String(100), nullable=False, comment='子知识点名称')
    description = db.Column(db.Text, comment='子知识点描述')
    content = db.Column(db.Text, comment='子知识点内容')
    
    # 属性
    difficulty = db.Column(db.Integer, default=3, comment='难度等级1-5')
    exam_frequency = db.Column(db.Integer, default=0, comment='近5年高考出现次数')
    estimated_time = db.Column(db.Integer, comment='预估学习时间(分钟)')
    
    # 学习要点
    key_points = db.Column(db.JSON, default=[], comment='关键要点')
    formulas = db.Column(db.JSON, default=[], comment='相关公式')
    examples = db.Column(db.JSON, default=[], comment='典型例题')
    
    # 状态
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SubKnowledgePoint {self.name}>'
    
    def to_dict(self, include_content=False):
        data = {
            'id': str(self.id),
            'knowledge_point_id': str(self.knowledge_point_id),
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'difficulty': self.difficulty,
            'exam_frequency': self.exam_frequency,
            'estimated_time': self.estimated_time,
            'key_points': self.key_points,
            'formulas': self.formulas,
            'examples': self.examples,
            'is_active': self.is_active,
            'sort_order': self.sort_order
        }
        if include_content:
            data['content'] = self.content
        return data