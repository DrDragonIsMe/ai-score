#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 数据模型 - exam_knowledge_mapping.py

Description:
    试卷知识点映射关系模型，用于建立试卷与知识点的关联关系，支持星图可视化。

Author: Chang Xinglong
Date: 2025-08-31
Version: 1.0.0
License: Apache License 2.0
"""

from datetime import datetime
from utils.database import db
import uuid

class ExamKnowledgeMapping(db.Model):
    """试卷知识点映射表 - 建立试卷与知识点的多对多关系"""
    
    __tablename__ = 'exam_knowledge_mappings'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    exam_paper_id = db.Column(db.String(36), db.ForeignKey('exam_papers.id'), nullable=False)
    knowledge_point_id = db.Column(db.String(36), db.ForeignKey('knowledge_points.id'), nullable=False)
    
    # 映射统计信息
    question_count = db.Column(db.Integer, default=0, comment='该知识点在试卷中的题目数量')
    total_score = db.Column(db.Integer, default=0, comment='该知识点在试卷中的总分值')
    avg_difficulty = db.Column(db.Float, comment='该知识点在试卷中的平均难度')
    
    # 题型分布
    choice_count = db.Column(db.Integer, default=0, comment='选择题数量')
    fill_count = db.Column(db.Integer, default=0, comment='填空题数量')
    essay_count = db.Column(db.Integer, default=0, comment='解答题数量')
    other_count = db.Column(db.Integer, default=0, comment='其他题型数量')
    
    # 分值分布
    choice_score = db.Column(db.Integer, default=0, comment='选择题总分')
    fill_score = db.Column(db.Integer, default=0, comment='填空题总分')
    essay_score = db.Column(db.Integer, default=0, comment='解答题总分')
    other_score = db.Column(db.Integer, default=0, comment='其他题型总分')
    
    # 重要程度评估
    importance_weight = db.Column(db.Float, default=1.0, comment='重要程度权重(基于分值和题目数量)')
    coverage_rate = db.Column(db.Float, comment='知识点覆盖率(该知识点分值/试卷总分)')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('exam_paper_id', 'knowledge_point_id', name='uq_exam_knowledge'),
    )
    
    def __repr__(self):
        return f'<ExamKnowledgeMapping {self.exam_paper_id}-{self.knowledge_point_id}>'
    
    def calculate_importance_weight(self):
        """计算重要程度权重"""
        if self.question_count == 0:
            return 0.0
        
        # 基于题目数量和分值的权重计算
        question_weight = self.question_count * 0.3
        score_weight = self.total_score * 0.7
        
        return (question_weight + score_weight) / 100.0
    
    def update_statistics(self):
        """更新统计信息"""
        from models.question import Question
        
        # 获取该映射关系下的所有题目
        questions = Question.query.filter_by(
            exam_paper_id=self.exam_paper_id,
            knowledge_point_id=self.knowledge_point_id,
            is_active=True
        ).all()
        
        if not questions:
            return
        
        # 重置统计数据
        self.question_count = len(questions)
        self.total_score = sum(q.score for q in questions)
        self.avg_difficulty = sum(q.difficulty for q in questions) / len(questions)
        
        # 重置题型统计
        self.choice_count = self.fill_count = self.essay_count = self.other_count = 0
        self.choice_score = self.fill_score = self.essay_score = self.other_score = 0
        
        # 统计题型分布
        for question in questions:
            if hasattr(question, 'question_type') and question.question_type:
                category = question.question_type.category
                if category == 'choice':
                    self.choice_count += 1
                    self.choice_score += question.score
                elif category == 'fill':
                    self.fill_count += 1
                    self.fill_score += question.score
                elif category == 'essay':
                    self.essay_count += 1
                    self.essay_score += question.score
                else:
                    self.other_count += 1
                    self.other_score += question.score
        
        # 计算重要程度权重
        self.importance_weight = self.calculate_importance_weight()
        
        # 计算覆盖率（需要试卷总分信息）
        from models.exam_papers import ExamPaper
        exam_paper = ExamPaper.query.get(self.exam_paper_id)
        if exam_paper and exam_paper.total_score > 0:
            self.coverage_rate = self.total_score / exam_paper.total_score
        
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'exam_paper_id': str(self.exam_paper_id),
            'knowledge_point_id': str(self.knowledge_point_id),
            'question_count': self.question_count,
            'total_score': self.total_score,
            'avg_difficulty': self.avg_difficulty,
            'choice_count': self.choice_count,
            'fill_count': self.fill_count,
            'essay_count': self.essay_count,
            'other_count': self.other_count,
            'choice_score': self.choice_score,
            'fill_score': self.fill_score,
            'essay_score': self.essay_score,
            'other_score': self.other_score,
            'importance_weight': self.importance_weight,
            'coverage_rate': self.coverage_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ExamKnowledgeStatistics(db.Model):
    """试卷知识点统计表 - 用于快速查询和星图展示"""
    
    __tablename__ = 'exam_knowledge_statistics'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_id = db.Column(db.String(36), db.ForeignKey('subjects.id'), nullable=False)
    knowledge_point_id = db.Column(db.String(36), db.ForeignKey('knowledge_points.id'), nullable=False)
    
    # 统计维度
    year = db.Column(db.Integer, comment='统计年份')
    exam_type = db.Column(db.String(50), comment='考试类型')
    region = db.Column(db.String(50), comment='地区')
    
    # 出现频率统计
    total_papers = db.Column(db.Integer, default=0, comment='总试卷数')
    appeared_papers = db.Column(db.Integer, default=0, comment='出现该知识点的试卷数')
    appearance_rate = db.Column(db.Float, default=0.0, comment='出现频率')
    
    # 题目统计
    total_questions = db.Column(db.Integer, default=0, comment='总题目数')
    avg_questions_per_paper = db.Column(db.Float, default=0.0, comment='平均每份试卷题目数')
    
    # 分值统计
    total_score = db.Column(db.Integer, default=0, comment='总分值')
    avg_score_per_paper = db.Column(db.Float, default=0.0, comment='平均每份试卷分值')
    max_score_per_paper = db.Column(db.Integer, default=0, comment='单份试卷最高分值')
    
    # 难度统计
    avg_difficulty = db.Column(db.Float, comment='平均难度')
    difficulty_distribution = db.Column(db.JSON, comment='难度分布')
    
    # 题型分布
    question_type_distribution = db.Column(db.JSON, comment='题型分布')
    score_type_distribution = db.Column(db.JSON, comment='分值分布')
    
    # 重要程度评估
    importance_score = db.Column(db.Float, default=0.0, comment='重要程度评分')
    trend_analysis = db.Column(db.JSON, comment='趋势分析')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('subject_id', 'knowledge_point_id', 'year', 'exam_type', 'region', 
                          name='uq_knowledge_statistics'),
    )
    
    def __repr__(self):
        return f'<ExamKnowledgeStatistics {self.knowledge_point_id}-{self.year}>'
    
    def calculate_importance_score(self):
        """计算重要程度评分"""
        if self.total_papers == 0:
            return 0.0
        
        # 基于多个维度计算重要程度
        frequency_score = self.appearance_rate * 40  # 出现频率权重40%
        score_score = (self.avg_score_per_paper / 10) * 30  # 分值权重30%
        question_score = (self.avg_questions_per_paper / 5) * 20  # 题目数量权重20%
        difficulty_score = (self.avg_difficulty or 3) * 2  # 难度权重10%
        
        return min(100.0, frequency_score + score_score + question_score + difficulty_score)
    
    def update_statistics_from_mappings(self):
        """从映射表更新统计信息"""
        from models.exam_papers import ExamPaper
        
        # 构建查询条件
        query_filters = {'subject_id': self.subject_id}
        if self.year:
            query_filters['year'] = self.year
        if self.exam_type:
            query_filters['exam_type'] = self.exam_type
        if self.region:
            query_filters['region'] = self.region
        
        # 获取符合条件的试卷ID
        exam_paper_ids = [ep.id for ep in ExamPaper.query.filter_by(**query_filters).all()]
        
        # 获取相关的映射关系
        mappings = ExamKnowledgeMapping.query.filter(
            ExamKnowledgeMapping.knowledge_point_id == self.knowledge_point_id,
            ExamKnowledgeMapping.exam_paper_id.in_(exam_paper_ids)
        ).all()
        
        if not mappings:
            return
        
        # 更新基础统计
        self.appeared_papers = len(mappings)
        self.total_questions = sum(m.question_count for m in mappings)
        self.total_score = sum(m.total_score for m in mappings)
        
        if self.appeared_papers > 0:
            self.avg_questions_per_paper = self.total_questions / self.appeared_papers
            self.avg_score_per_paper = self.total_score / self.appeared_papers
            self.max_score_per_paper = max(m.total_score for m in mappings)
            self.avg_difficulty = sum(m.avg_difficulty for m in mappings if m.avg_difficulty) / len([m for m in mappings if m.avg_difficulty])
        
        # 计算重要程度评分
        self.importance_score = self.calculate_importance_score()
        
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'subject_id': str(self.subject_id),
            'knowledge_point_id': str(self.knowledge_point_id),
            'year': self.year,
            'exam_type': self.exam_type,
            'region': self.region,
            'total_papers': self.total_papers,
            'appeared_papers': self.appeared_papers,
            'appearance_rate': self.appearance_rate,
            'total_questions': self.total_questions,
            'avg_questions_per_paper': self.avg_questions_per_paper,
            'total_score': self.total_score,
            'avg_score_per_paper': self.avg_score_per_paper,
            'max_score_per_paper': self.max_score_per_paper,
            'avg_difficulty': self.avg_difficulty,
            'difficulty_distribution': self.difficulty_distribution,
            'question_type_distribution': self.question_type_distribution,
            'score_type_distribution': self.score_type_distribution,
            'importance_score': self.importance_score,
            'trend_analysis': self.trend_analysis,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }