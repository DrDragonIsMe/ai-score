# -*- coding: utf-8 -*-
"""
记忆强化相关数据模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from utils.database import db

class MemoryCard(db.Model):
    """
    记忆卡片模型
    
    基于艾宾浩斯遗忘曲线的智能记忆卡片
    """
    __tablename__ = 'memory_cards'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    knowledge_point_id = Column(Integer, ForeignKey('knowledge_points.id'), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=True, index=True)
    
    # 卡片内容
    content_type = Column(String(50), nullable=False, default='concept')  # concept/question/formula/example
    front_content = Column(Text, nullable=False)  # 卡片正面内容（问题/提示）
    back_content = Column(Text, nullable=False)   # 卡片背面内容（答案/解释）
    tags = Column(JSON, default=list)             # 标签列表
    
    # 记忆参数
    difficulty_level = Column(Integer, default=3)      # 难度等级 1-5
    memory_strength = Column(Float, default=0.0)       # 记忆强度 0.0-1.0
    review_count = Column(Integer, default=0)          # 复习次数
    
    # 时间管理
    last_review_time = Column(DateTime, nullable=True)     # 最后复习时间
    next_review_time = Column(DateTime, nullable=False)    # 下次复习时间
    created_time = Column(DateTime, default=datetime.utcnow)
    updated_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 状态管理
    is_active = Column(Boolean, default=True)          # 是否活跃（用于暂停复习）
    is_mastered = Column(Boolean, default=False)       # 是否已掌握
    
    # 关联关系
    user = relationship('User', backref='memory_cards')
    knowledge_point = relationship('KnowledgePoint', backref='memory_cards')
    question = relationship('Question', backref='memory_cards')
    review_records = relationship('ReviewRecord', backref='memory_card', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<MemoryCard {self.id}: {self.content_type} - {self.front_content[:50]}...>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'knowledge_point_id': self.knowledge_point_id,
            'question_id': self.question_id,
            'content_type': self.content_type,
            'front_content': self.front_content,
            'back_content': self.back_content,
            'tags': self.tags or [],
            'difficulty_level': self.difficulty_level,
            'memory_strength': self.memory_strength,
            'review_count': self.review_count,
            'last_review_time': self.last_review_time.isoformat() if self.last_review_time else None,
            'next_review_time': self.next_review_time.isoformat() if self.next_review_time else None,
            'created_time': self.created_time.isoformat() if self.created_time else None,
            'updated_time': self.updated_time.isoformat() if self.updated_time else None,
            'is_active': self.is_active,
            'is_mastered': self.is_mastered,
            'knowledge_point_name': self.knowledge_point.name if self.knowledge_point else None,
            'subject_name': self.knowledge_point.subject.name if self.knowledge_point and self.knowledge_point.subject else None
        }
    
    def get_review_status(self):
        """获取复习状态"""
        now = datetime.utcnow()
        
        if not self.is_active:
            return 'inactive'
        elif self.is_mastered:
            return 'mastered'
        elif self.next_review_time <= now:
            return 'due'
        elif (self.next_review_time - now).days <= 1:
            return 'due_soon'
        else:
            return 'scheduled'
    
    def get_memory_level(self):
        """获取记忆等级"""
        if self.memory_strength >= 0.8:
            return 'excellent'
        elif self.memory_strength >= 0.6:
            return 'good'
        elif self.memory_strength >= 0.4:
            return 'fair'
        elif self.memory_strength >= 0.2:
            return 'poor'
        else:
            return 'very_poor'

class ReviewRecord(db.Model):
    """
    复习记录模型
    
    记录每次复习的详细信息
    """
    __tablename__ = 'review_records'
    
    id = Column(Integer, primary_key=True)
    memory_card_id = Column(Integer, ForeignKey('memory_cards.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # 复习表现
    performance = Column(String(20), nullable=False)  # again/poor/fair/good/excellent
    response_time = Column(Integer, nullable=True)    # 响应时间（秒）
    user_feedback = Column(Text, nullable=True)       # 用户反馈
    
    # 记忆强度变化
    memory_strength_before = Column(Float, nullable=False)  # 复习前记忆强度
    memory_strength_after = Column(Float, nullable=True)    # 复习后记忆强度
    
    # 时间信息
    review_time = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 关联关系
    user = relationship('User', backref='review_records')
    
    def __repr__(self):
        return f'<ReviewRecord {self.id}: Card {self.memory_card_id} - {self.performance}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'memory_card_id': self.memory_card_id,
            'user_id': self.user_id,
            'performance': self.performance,
            'response_time': self.response_time,
            'user_feedback': self.user_feedback,
            'memory_strength_before': self.memory_strength_before,
            'memory_strength_after': self.memory_strength_after,
            'review_time': self.review_time.isoformat() if self.review_time else None
        }
    
    def get_performance_score(self):
        """获取表现分数"""
        performance_scores = {
            'again': 0,
            'poor': 25,
            'fair': 50,
            'good': 75,
            'excellent': 100
        }
        return performance_scores.get(self.performance, 0)
    
    def get_strength_improvement(self):
        """获取记忆强度提升"""
        if self.memory_strength_after is not None:
            return self.memory_strength_after - self.memory_strength_before
        return 0.0

class MemorySession(db.Model):
    """
    记忆会话模型
    
    记录每次复习会话的整体信息
    """
    __tablename__ = 'memory_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # 会话信息
    session_type = Column(String(50), default='regular')  # regular/intensive/review
    target_count = Column(Integer, default=10)            # 目标复习数量
    completed_count = Column(Integer, default=0)          # 完成数量
    
    # 时间信息
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    total_duration = Column(Integer, nullable=True)       # 总时长（秒）
    
    # 统计信息
    total_cards_reviewed = Column(Integer, default=0)
    excellent_count = Column(Integer, default=0)
    good_count = Column(Integer, default=0)
    fair_count = Column(Integer, default=0)
    poor_count = Column(Integer, default=0)
    again_count = Column(Integer, default=0)
    
    # 平均指标
    avg_response_time = Column(Float, nullable=True)
    avg_strength_improvement = Column(Float, nullable=True)
    
    # 状态
    status = Column(String(20), default='active')  # active/completed/abandoned
    
    # 关联关系
    user = relationship('User', backref='memory_sessions')
    
    def __repr__(self):
        return f'<MemorySession {self.id}: User {self.user_id} - {self.status}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_type': self.session_type,
            'target_count': self.target_count,
            'completed_count': self.completed_count,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_duration': self.total_duration,
            'total_cards_reviewed': self.total_cards_reviewed,
            'performance_stats': {
                'excellent': self.excellent_count,
                'good': self.good_count,
                'fair': self.fair_count,
                'poor': self.poor_count,
                'again': self.again_count
            },
            'avg_response_time': self.avg_response_time,
            'avg_strength_improvement': self.avg_strength_improvement,
            'status': self.status
        }
    
    def calculate_success_rate(self):
        """计算成功率"""
        total = self.total_cards_reviewed
        if total == 0:
            return 0.0
        
        successful = self.excellent_count + self.good_count + self.fair_count
        return (successful / total) * 100
    
    def update_statistics(self, performance: str, response_time: int = None, 
                         strength_improvement: float = 0.0):
        """更新统计信息"""
        # 更新表现计数
        if performance == 'excellent':
            self.excellent_count += 1
        elif performance == 'good':
            self.good_count += 1
        elif performance == 'fair':
            self.fair_count += 1
        elif performance == 'poor':
            self.poor_count += 1
        elif performance == 'again':
            self.again_count += 1
        
        # 更新总数
        self.total_cards_reviewed += 1
        self.completed_count += 1
        
        # 更新平均响应时间
        if response_time is not None:
            if self.avg_response_time is None:
                self.avg_response_time = float(response_time)
            else:
                # 计算移动平均
                self.avg_response_time = (
                    (self.avg_response_time * (self.total_cards_reviewed - 1) + response_time) / 
                    self.total_cards_reviewed
                )
        
        # 更新平均强度提升
        if self.avg_strength_improvement is None:
            self.avg_strength_improvement = strength_improvement
        else:
            self.avg_strength_improvement = (
                (self.avg_strength_improvement * (self.total_cards_reviewed - 1) + strength_improvement) / 
                self.total_cards_reviewed
            )

class MemoryReminder(db.Model):
    """
    记忆提醒模型
    
    管理复习提醒和通知
    """
    __tablename__ = 'memory_reminders'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # 提醒设置
    reminder_type = Column(String(50), nullable=False)  # daily/due_cards/weekly_summary
    is_enabled = Column(Boolean, default=True)
    
    # 时间设置
    reminder_time = Column(String(10), nullable=True)   # HH:MM 格式
    timezone = Column(String(50), default='UTC')
    
    # 提醒内容设置
    include_due_count = Column(Boolean, default=True)
    include_weak_areas = Column(Boolean, default=True)
    include_progress_summary = Column(Boolean, default=False)
    
    # 发送渠道
    send_email = Column(Boolean, default=False)
    send_push = Column(Boolean, default=True)
    send_sms = Column(Boolean, default=False)
    
    # 状态信息
    last_sent_time = Column(DateTime, nullable=True)
    next_send_time = Column(DateTime, nullable=True)
    
    created_time = Column(DateTime, default=datetime.utcnow)
    updated_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    user = relationship('User', backref='memory_reminders')
    
    def __repr__(self):
        return f'<MemoryReminder {self.id}: {self.reminder_type} for User {self.user_id}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'reminder_type': self.reminder_type,
            'is_enabled': self.is_enabled,
            'reminder_time': self.reminder_time,
            'timezone': self.timezone,
            'content_settings': {
                'include_due_count': self.include_due_count,
                'include_weak_areas': self.include_weak_areas,
                'include_progress_summary': self.include_progress_summary
            },
            'delivery_channels': {
                'email': self.send_email,
                'push': self.send_push,
                'sms': self.send_sms
            },
            'last_sent_time': self.last_sent_time.isoformat() if self.last_sent_time else None,
            'next_send_time': self.next_send_time.isoformat() if self.next_send_time else None,
            'created_time': self.created_time.isoformat() if self.created_time else None,
            'updated_time': self.updated_time.isoformat() if self.updated_time else None
        }