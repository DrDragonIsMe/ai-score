#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 数据模型 - mistake.py

Description:
    错题数据模型，定义错题信息和分析数据。

Author: Chang Xinglong
Date: 2025-08-30
Version: 1.0.0
License: Apache License 2.0
"""


from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from utils.database import db
import enum

class MistakeType(enum.Enum):
    """错误类型枚举"""
    CONCEPT_ERROR = "concept_error"          # 概念理解错误
    CALCULATION_ERROR = "calculation_error"  # 计算错误
    METHOD_ERROR = "method_error"            # 方法选择错误
    CARELESS_ERROR = "careless_error"        # 粗心错误
    KNOWLEDGE_GAP = "knowledge_gap"          # 知识缺失
    LOGIC_ERROR = "logic_error"              # 逻辑错误
    READING_ERROR = "reading_error"          # 审题错误
    TIME_PRESSURE = "time_pressure"          # 时间压力导致错误

class MistakeLevel(enum.Enum):
    """错误严重程度枚举"""
    LOW = "low"          # 轻微错误
    MEDIUM = "medium"    # 中等错误
    HIGH = "high"        # 严重错误
    CRITICAL = "critical" # 关键错误

class MistakeRecord(db.Model):
    """
    错题记录模型
    
    记录学生的错题信息和分析结果
    """
    __tablename__ = 'mistake_records'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False, index=True)
    knowledge_point_id = Column(Integer, ForeignKey('knowledge_points.id'), nullable=False, index=True)
    
    # 错误信息
    user_answer = Column(Text, nullable=False)        # 用户答案
    correct_answer = Column(Text, nullable=False)     # 正确答案
    mistake_type = Column(Enum(MistakeType), nullable=False)  # 错误类型
    mistake_level = Column(Enum(MistakeLevel), default=MistakeLevel.MEDIUM)  # 错误严重程度
    
    # 分析和建议
    error_analysis = Column(Text, nullable=True)      # 错误分析
    solution_steps = Column(JSON, nullable=True)       # 解题步骤
    key_concepts = Column(JSON, nullable=True)         # 关键概念
    similar_questions = Column(JSON, nullable=True)    # 相似题目ID列表
    
    # 改进建议
    improvement_suggestions = Column(JSON, nullable=True)  # 改进建议
    practice_recommendations = Column(JSON, nullable=True) # 练习推荐
    
    # 复习状态
    review_count = Column(Integer, default=0)         # 复习次数
    mastery_level = Column(Float, default=0.0)        # 掌握程度 0.0-1.0
    last_review_time = Column(DateTime, nullable=True) # 最后复习时间
    next_review_time = Column(DateTime, nullable=True) # 下次复习时间
    
    # 状态管理
    is_resolved = Column(Boolean, default=False)      # 是否已解决
    is_archived = Column(Boolean, default=False)      # 是否已归档
    priority_score = Column(Float, default=0.5)       # 优先级分数
    
    # 时间信息
    created_time = Column(DateTime, default=datetime.utcnow, index=True)
    updated_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_time = Column(DateTime, nullable=True)    # 解决时间
    
    # 关联关系
    user = relationship('User', backref='mistake_records')
    question = relationship('Question', backref='mistake_records')
    knowledge_point = relationship('KnowledgePoint', backref='mistake_records')
    review_sessions = relationship('MistakeReviewSession', backref='mistake_record', cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.solution_steps is None:
            self.solution_steps = []
        if self.key_concepts is None:
            self.key_concepts = []
        if self.similar_questions is None:
            self.similar_questions = []
        if self.improvement_suggestions is None:
            self.improvement_suggestions = []
        if self.practice_recommendations is None:
            self.practice_recommendations = []

    def __repr__(self):
        return f'<MistakeRecord {self.id}: User {self.user_id} - Question {self.question_id}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'question_id': self.question_id,
            'knowledge_point_id': self.knowledge_point_id,
            'user_answer': self.user_answer,
            'correct_answer': self.correct_answer,
            'mistake_type': self.mistake_type.value if self.mistake_type is not None else None,
            'mistake_level': self.mistake_level.value if self.mistake_level is not None else None,
            'error_analysis': self.error_analysis,
            'solution_steps': self.solution_steps or [],
            'key_concepts': self.key_concepts or [],
            'similar_questions': self.similar_questions or [],
            'improvement_suggestions': self.improvement_suggestions or [],
            'practice_recommendations': self.practice_recommendations or [],
            'review_count': self.review_count,
            'mastery_level': self.mastery_level,
            'last_review_time': self.last_review_time.isoformat() if self.last_review_time is not None else None,
            'next_review_time': self.next_review_time.isoformat() if self.next_review_time is not None else None,
            'is_resolved': self.is_resolved,
            'is_archived': self.is_archived,
            'priority_score': self.priority_score,
            'created_time': self.created_time.isoformat() if self.created_time is not None else None,
            'updated_time': self.updated_time.isoformat() if self.updated_time is not None else None,
            'resolved_time': self.resolved_time.isoformat() if self.resolved_time is not None else None,
            'question_content': self.question.content if self.question else None,
            'knowledge_point_name': self.knowledge_point.name if self.knowledge_point else None,
            'subject_name': self.knowledge_point.subject.name if self.knowledge_point and self.knowledge_point.subject else None
        }
    
    def get_difficulty_assessment(self):
        """获取难度评估"""
        # 获取实际值而不是Column对象
        mastery_level_val = getattr(self, 'mastery_level', None)
        if mastery_level_val is None:
            return 'unknown'
        
        mastery = float(mastery_level_val)
        if mastery >= 0.8:
            return 'easy'
        elif mastery >= 0.6:
            return 'medium'
        elif mastery >= 0.4:
            return 'hard'
        else:
            return 'very_hard'
    
    def get_review_urgency(self):
        """获取复习紧急程度"""
        # 获取实际值而不是Column对象
        is_resolved_val = getattr(self, 'is_resolved', None)
        next_review_time_val = getattr(self, 'next_review_time', None)
        mistake_level_val = getattr(self, 'mistake_level', None)
        priority_score_val = getattr(self, 'priority_score', None)
        
        if is_resolved_val:
            return 'low'
        
        now = datetime.utcnow()
        if next_review_time_val is not None and next_review_time_val <= now:
            if mistake_level_val in [MistakeLevel.HIGH, MistakeLevel.CRITICAL]:
                return 'urgent'
            else:
                return 'high'
        elif priority_score_val is not None and priority_score_val >= 0.8:
            return 'high'
        elif priority_score_val is not None and priority_score_val >= 0.6:
            return 'medium'
        else:
            return 'low'
    
    def calculate_priority_score(self):
        """计算优先级分数"""
        # 获取实际值而不是Column对象
        mistake_level_val = getattr(self, 'mistake_level', None)
        mastery_level_val = getattr(self, 'mastery_level', None)
        review_count_val = getattr(self, 'review_count', None)
        next_review_time_val = getattr(self, 'next_review_time', None)
        
        score = 0.0
        
        # 错误严重程度权重
        level_weights = {
            MistakeLevel.LOW: 0.2,
            MistakeLevel.MEDIUM: 0.4,
            MistakeLevel.HIGH: 0.7,
            MistakeLevel.CRITICAL: 1.0
        }
        if mistake_level_val is not None:
            score += level_weights.get(mistake_level_val, 0.4) * 0.4
        
        # 掌握程度权重（掌握程度越低，优先级越高）
        if mastery_level_val is not None:
            score += (1.0 - float(mastery_level_val)) * 0.3
        
        # 复习次数权重（复习次数越少，优先级越高）
        if review_count_val is not None:
            review_factor = max(0, 1.0 - float(review_count_val) * 0.1)
            score += review_factor * 0.2
        
        # 时间因素权重
        if next_review_time_val is not None:
            now = datetime.utcnow()
            if next_review_time_val <= now:
                score += 0.1  # 已到复习时间
        
        self.priority_score = min(1.0, score)
        return self.priority_score

class MistakeReviewSession(db.Model):
    """
    错题复习会话模型
    
    记录每次错题复习的详细信息
    """
    __tablename__ = 'mistake_review_sessions'
    
    id = Column(Integer, primary_key=True)
    mistake_record_id = Column(Integer, ForeignKey('mistake_records.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # 复习信息
    review_type = Column(String(50), default='regular')  # regular/intensive/quick
    user_answer = Column(Text, nullable=True)            # 复习时的用户答案
    is_correct = Column(Boolean, nullable=True)          # 是否答对
    confidence_level = Column(Integer, nullable=True)    # 信心程度 1-5
    
    # 表现评估
    understanding_level = Column(Float, nullable=True)   # 理解程度 0.0-1.0
    response_time = Column(Integer, nullable=True)       # 响应时间（秒）
    help_used = Column(Boolean, default=False)          # 是否使用了帮助
    hint_count = Column(Integer, default=0)              # 使用提示次数
    
    # 反馈信息
    user_feedback = Column(Text, nullable=True)          # 用户反馈
    difficulty_rating = Column(Integer, nullable=True)   # 难度评级 1-5
    
    # 时间信息
    review_time = Column(DateTime, default=datetime.utcnow, index=True)
    session_duration = Column(Integer, nullable=True)    # 会话时长（秒）
    
    # 关联关系
    user = relationship('User', backref='mistake_review_sessions')
    
    def __repr__(self):
        return f'<MistakeReviewSession {self.id}: Mistake {self.mistake_record_id}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'mistake_record_id': self.mistake_record_id,
            'user_id': self.user_id,
            'review_type': self.review_type,
            'user_answer': self.user_answer,
            'is_correct': self.is_correct,
            'confidence_level': self.confidence_level,
            'understanding_level': self.understanding_level,
            'response_time': self.response_time,
            'help_used': self.help_used,
            'hint_count': self.hint_count,
            'user_feedback': self.user_feedback,
            'difficulty_rating': self.difficulty_rating,
            'review_time': (lambda rt: rt.isoformat() if rt and hasattr(rt, 'isoformat') else None)(getattr(self, 'review_time', None)),
            'session_duration': self.session_duration
        }
    
    def get_performance_score(self):
        """获取表现分数"""
        # 获取实际值而不是Column对象
        is_correct_val = getattr(self, 'is_correct', None)
        confidence_level_val = getattr(self, 'confidence_level', None)
        help_used_val = getattr(self, 'help_used', None)
        hint_count_val = getattr(self, 'hint_count', None)
        
        if is_correct_val is None:
            return 0.0
        
        base_score = 100.0 if bool(is_correct_val) else 0.0
        
        # 信心程度调整
        if confidence_level_val is not None:
            confidence_factor = float(confidence_level_val) / 5.0
            base_score *= confidence_factor
        
        # 帮助使用调整
        if help_used_val is not None and bool(help_used_val):
            base_score *= 0.8
        
        # 提示次数调整
        if hint_count_val is not None and int(hint_count_val) > 0:
            hint_penalty = min(0.5, float(hint_count_val) * 0.1)
            base_score *= (1.0 - hint_penalty)
        
        return min(100.0, base_score)

class MistakePattern(db.Model):
    """
    错误模式模型
    
    分析和记录用户的错误模式
    """
    __tablename__ = 'mistake_patterns'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # 模式信息
    pattern_type = Column(String(100), nullable=False)   # 模式类型
    pattern_description = Column(Text, nullable=False)   # 模式描述
    frequency = Column(Integer, default=1)               # 出现频率
    confidence_score = Column(Float, default=0.0)        # 置信度分数
    
    # 模式特征
    related_knowledge_points = Column(JSON, nullable=True) # 相关知识点ID列表
    related_mistake_types = Column(JSON, nullable=True)    # 相关错误类型列表
    example_mistakes = Column(JSON, nullable=True)         # 示例错题ID列表
    
    # 改进计划
    improvement_plan = Column(JSON, nullable=True)         # 改进计划
    recommended_resources = Column(JSON, nullable=True)    # 推荐资源
    
    # 状态信息
    is_active = Column(Boolean, default=True)            # 是否活跃
    improvement_progress = Column(Float, default=0.0)     # 改进进度
    
    # 时间信息
    first_detected = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    user = relationship('User', backref='mistake_patterns')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.related_knowledge_points is None:
            self.related_knowledge_points = []
        if self.related_mistake_types is None:
            self.related_mistake_types = []
        if self.example_mistakes is None:
            self.example_mistakes = []
        if self.improvement_plan is None:
            self.improvement_plan = {}
        if self.recommended_resources is None:
            self.recommended_resources = []

    def __repr__(self):
        return f'<MistakePattern {self.id}: {self.pattern_type} for User {self.user_id}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'pattern_type': self.pattern_type,
            'pattern_description': self.pattern_description,
            'frequency': self.frequency,
            'confidence_score': self.confidence_score,
            'related_knowledge_points': self.related_knowledge_points or [],
            'related_mistake_types': self.related_mistake_types or [],
            'example_mistakes': self.example_mistakes or [],
            'improvement_plan': self.improvement_plan or {},
            'recommended_resources': self.recommended_resources or [],
            'is_active': self.is_active,
            'improvement_progress': self.improvement_progress,
            'first_detected': (lambda fd: fd.isoformat() if fd and hasattr(fd, 'isoformat') else None)(getattr(self, 'first_detected', None)),
            'last_updated': (lambda lu: lu.isoformat() if lu and hasattr(lu, 'isoformat') else None)(getattr(self, 'last_updated', None))
        }
    
    def get_severity_level(self):
        """获取严重程度"""
        # 获取实际值而不是Column对象
        frequency_val = getattr(self, 'frequency', None)
        confidence_score_val = getattr(self, 'confidence_score', None)
        
        freq = int(frequency_val) if frequency_val is not None else 0
        conf = float(confidence_score_val) if confidence_score_val is not None else 0.0
        
        if freq >= 10 and conf >= 0.8:
            return 'critical'
        elif freq >= 5 and conf >= 0.6:
            return 'high'
        elif freq >= 3 and conf >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def update_frequency(self):
        """更新频率"""
        # 获取实际值而不是Column对象
        frequency_val = getattr(self, 'frequency', 0)
        self.frequency = frequency_val + 1
        self.last_updated = datetime.utcnow()
        
        # 重新计算置信度
        base_confidence = min(1.0, self.frequency / 10.0)
        time_factor = 1.0  # 可以根据时间衰减调整
        self.confidence_score = base_confidence * time_factor

class TutoringSession(db.Model):
    """
    解题辅导会话模型
    
    记录分层解题辅导的会话信息
    """
    __tablename__ = 'tutoring_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False, index=True)
    
    # 会话信息
    session_type = Column(String(50), default='guided')  # guided/hint_based/step_by_step
    current_step = Column(Integer, default=0)            # 当前步骤
    total_steps = Column(Integer, default=0)             # 总步骤数
    
    # 辅导内容
    guidance_history = Column(JSON, nullable=True)        # 辅导历史
    hints_used = Column(JSON, nullable=True)              # 使用的提示
    user_responses = Column(JSON, nullable=True)          # 用户回应
    
    # 学习分析
    understanding_progress = Column(JSON, nullable=True)   # 理解进度
    difficulty_adjustments = Column(JSON, nullable=True)  # 难度调整记录
    help_effectiveness = Column(Float, nullable=True)    # 帮助有效性
    
    # 状态管理
    status = Column(String(20), default='active')        # active/completed/abandoned
    completion_rate = Column(Float, default=0.0)         # 完成率
    
    # 时间信息
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    total_duration = Column(Integer, nullable=True)      # 总时长（秒）
    
    # 关联关系
    user = relationship('User', backref='tutoring_sessions')
    question = relationship('Question', backref='tutoring_sessions')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.guidance_history is None:
            self.guidance_history = []
        if self.hints_used is None:
            self.hints_used = []
        if self.user_responses is None:
            self.user_responses = []
        if self.understanding_progress is None:
            self.understanding_progress = {}
        if self.difficulty_adjustments is None:
            self.difficulty_adjustments = []

    def __repr__(self):
        return f'<TutoringSession {self.id}: User {self.user_id} - Question {self.question_id}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'question_id': self.question_id,
            'session_type': self.session_type,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'guidance_history': self.guidance_history or [],
            'hints_used': self.hints_used or [],
            'user_responses': self.user_responses or [],
            'understanding_progress': self.understanding_progress or {},
            'difficulty_adjustments': self.difficulty_adjustments or [],
            'help_effectiveness': self.help_effectiveness,
            'status': self.status,
            'completion_rate': self.completion_rate,
            'start_time': (lambda st: st.isoformat() if st and hasattr(st, 'isoformat') else None)(getattr(self, 'start_time', None)),
            'end_time': (lambda et: et.isoformat() if et and hasattr(et, 'isoformat') else None)(getattr(self, 'end_time', None)),
            'total_duration': self.total_duration
        }
    
    def add_guidance_step(self, step_type: str, content: str, user_response: str = ""):
        """添加辅导步骤"""
        guidance_list = getattr(self, 'guidance_history', None)
        if not isinstance(guidance_list, list):
            guidance_list = []
        
        step = {
            'step_number': len(guidance_list) + 1,
            'step_type': step_type,
            'content': content,
            'timestamp': datetime.utcnow().isoformat(),
            'user_response': user_response or ''
        }
        
        guidance_list.append(step)
        self.guidance_history = guidance_list
        
        self.current_step = len(guidance_list)
        total_steps_val = getattr(self, 'total_steps', None)
        total_steps = int(total_steps_val) if total_steps_val is not None else 1
        current_step_val = getattr(self, 'current_step', 0)
        self.completion_rate = float(current_step_val) / max(1, total_steps)
    
    def add_hint(self, hint_type: str, hint_content: str, effectiveness: float = 0.0):
        """添加提示"""
        hint = {
            'hint_type': hint_type,
            'content': hint_content,
            'timestamp': datetime.utcnow().isoformat(),
            'effectiveness': effectiveness or 0.0
        }
        
        hints_list = getattr(self, 'hints_used', None)
        if not isinstance(hints_list, list):
            hints_list = []
        hints_list.append(hint)
        self.hints_used = hints_list
    
    def update_understanding_progress(self, concept: str, progress: float = 0.0):
        """更新理解进度"""
        progress_dict = getattr(self, 'understanding_progress', None)
        if not isinstance(progress_dict, dict):
            progress_dict = {}
        
        progress_dict[concept] = {
            'progress': progress or 0.0,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.understanding_progress = progress_dict
    
    def complete_session(self, final_understanding: float = 0.0):
        """完成会话"""
        self.status = 'completed'
        self.end_time = datetime.utcnow()
        self.completion_rate = 1.0
        
        start_time_val = getattr(self, 'start_time', None)
        end_time_val = getattr(self, 'end_time', None)
        if start_time_val and end_time_val:
            duration = end_time_val - start_time_val
            self.total_duration = int(duration.total_seconds())
        
        if final_understanding is not None:
            self.help_effectiveness = final_understanding or 0.0