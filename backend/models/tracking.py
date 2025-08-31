#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 数据模型 - tracking.py

Description:
    跟踪数据模型，定义学习行为和统计数据。

Author: Chang Xinglong
Date: 2025-01-20
Version: 1.0.0
License: Apache License 2.0
"""


import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from utils.database import db

class TrackingPeriod(Enum):
    """追踪周期"""
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    YEARLY = 'yearly'

class MetricType(Enum):
    """指标类型"""
    LEARNING_TIME = 'learning_time'  # 学习时长
    QUESTION_COUNT = 'question_count'  # 题目数量
    ACCURACY_RATE = 'accuracy_rate'  # 正确率
    COMPLETION_RATE = 'completion_rate'  # 完成率
    PROGRESS_SCORE = 'progress_score'  # 进度得分
    KNOWLEDGE_MASTERY = 'knowledge_mastery'  # 知识掌握度
    MEMORY_RETENTION = 'memory_retention'  # 记忆保持率
    EXAM_PERFORMANCE = 'exam_performance'  # 考试表现
    TUTORING_EFFECTIVENESS = 'tutoring_effectiveness'  # 辅导效果
    MISTAKE_REDUCTION = 'mistake_reduction'  # 错误减少率

class ReportType(Enum):
    """报告类型"""
    DAILY_SUMMARY = 'daily_summary'
    WEEKLY_REPORT = 'weekly_report'
    MONTHLY_REPORT = 'monthly_report'
    PROGRESS_REPORT = 'progress_report'
    PERFORMANCE_ANALYSIS = 'performance_analysis'
    IMPROVEMENT_SUGGESTION = 'improvement_suggestion'

class LearningMetric(db.Model):
    """
    学习指标模型
    
    记录各种学习指标的数据点
    """
    __tablename__ = 'learning_metrics'
    
    # 基本信息
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    
    # 指标信息
    metric_type = Column(String(50), nullable=False)  # MetricType枚举值
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20))  # 单位：分钟、个、%等
    
    # 维度信息
    subject_id = Column(Integer, ForeignKey('subjects.id'))
    knowledge_point_id = Column(Integer, ForeignKey('knowledge_points.id'))
    difficulty_level = Column(String(20))  # easy, medium, hard
    
    # 时间信息
    record_date = Column(DateTime, nullable=False, default=datetime.now)
    period_type = Column(String(20), nullable=False)  # TrackingPeriod枚举值
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # 上下文信息
    context_data = Column(JSON)  # 额外的上下文数据
    tags = Column(JSON)  # 标签列表
    
    # 元数据
    created_time = Column(DateTime, default=datetime.now)
    updated_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    user = relationship('User', backref='learning_metrics')
    subject = relationship('Subject', backref='learning_metrics')
    knowledge_point = relationship('KnowledgePoint', backref='learning_metrics')
    
    # 索引
    __table_args__ = (
        Index('idx_learning_metrics_user_date', 'user_id', 'record_date'),
        Index('idx_learning_metrics_type_period', 'metric_type', 'period_type'),
        Index('idx_learning_metrics_subject', 'subject_id', 'record_date'),
    )
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'metric_type': self.metric_type,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'metric_unit': self.metric_unit,
            'subject_id': self.subject_id,
            'knowledge_point_id': self.knowledge_point_id,
            'difficulty_level': self.difficulty_level,
            'record_date': self.record_date.isoformat() if self.record_date is not None else None,
            'period_type': self.period_type,
            'period_start': self.period_start.isoformat() if self.period_start is not None else None,
            'period_end': self.period_end.isoformat() if self.period_end is not None else None,
            'context_data': self.context_data,
            'tags': self.tags,
            'created_time': self.created_time.isoformat() if self.created_time is not None else None
        }

class PerformanceSnapshot(db.Model):
    """
    性能快照模型
    
    定期记录学习者的整体表现快照
    """
    __tablename__ = 'performance_snapshots'
    
    # 基本信息
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    
    # 快照信息
    snapshot_date = Column(DateTime, nullable=False, default=datetime.now)
    period_type = Column(String(20), nullable=False)  # TrackingPeriod枚举值
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # 综合指标
    overall_score = Column(Float)  # 综合得分 0-100
    learning_efficiency = Column(Float)  # 学习效率 0-1
    knowledge_growth = Column(Float)  # 知识增长率 0-1
    skill_improvement = Column(Float)  # 技能提升度 0-1
    
    # 分项指标
    time_metrics = Column(JSON)  # 时间相关指标
    accuracy_metrics = Column(JSON)  # 准确率相关指标
    progress_metrics = Column(JSON)  # 进度相关指标
    engagement_metrics = Column(JSON)  # 参与度相关指标
    
    # 学科表现
    subject_performance = Column(JSON)  # 各学科表现
    
    # 对比数据
    previous_snapshot_id = Column(Integer, ForeignKey('performance_snapshots.id'))
    improvement_rate = Column(Float)  # 相比上期的改进率
    
    # 预测数据
    predicted_next_score = Column(Float)  # 预测下期得分
    confidence_level = Column(Float)  # 预测置信度
    
    # 元数据
    created_time = Column(DateTime, default=datetime.now)
    updated_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    user = relationship('User', backref='performance_snapshots')
    previous_snapshot = relationship('PerformanceSnapshot', remote_side=[id])
    
    # 索引
    __table_args__ = (
        Index('idx_performance_snapshots_user_date', 'user_id', 'snapshot_date'),
        Index('idx_performance_snapshots_period', 'period_type', 'snapshot_date'),
    )
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'snapshot_date': self.snapshot_date.isoformat() if self.snapshot_date is not None else None,
            'period_type': self.period_type,
            'period_start': self.period_start.isoformat() if self.period_start is not None else None,
            'period_end': self.period_end.isoformat() if self.period_end is not None else None,
            'overall_score': self.overall_score,
            'learning_efficiency': self.learning_efficiency,
            'knowledge_growth': self.knowledge_growth,
            'skill_improvement': self.skill_improvement,
            'time_metrics': self.time_metrics,
            'accuracy_metrics': self.accuracy_metrics,
            'progress_metrics': self.progress_metrics,
            'engagement_metrics': self.engagement_metrics,
            'subject_performance': self.subject_performance,
            'improvement_rate': self.improvement_rate,
            'predicted_next_score': self.predicted_next_score,
            'confidence_level': self.confidence_level,
            'created_time': self.created_time.isoformat() if self.created_time is not None else None
        }
    
    def calculate_improvement_rate(self) -> Optional[float]:
        """计算改进率"""
        if not self.previous_snapshot:
            return None
        
        if (self.previous_snapshot.overall_score is None or 
            self.overall_score is None or 
            self.previous_snapshot.overall_score == 0):
            return None
        
        return (self.overall_score - self.previous_snapshot.overall_score) / self.previous_snapshot.overall_score
    
    def get_trend_analysis(self) -> Dict:
        """获取趋势分析"""
        improvement = self.calculate_improvement_rate()
        
        if improvement is None:
            trend = 'unknown'
        elif improvement > 0.05:  # 5%以上提升
            trend = 'improving'
        elif improvement < -0.05:  # 5%以上下降
            trend = 'declining'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'improvement_rate': improvement,
            'trend_description': self._get_trend_description(trend, improvement)
        }
    
    def _get_trend_description(self, trend: str, improvement: Optional[float]) -> str:
        """获取趋势描述"""
        if trend == 'improving':
            improvement_val = improvement if improvement is not None else 0
            return f"学习表现持续提升，相比上期提高了{improvement_val*100:.1f}%"
        elif trend == 'declining':
            improvement_val = improvement if improvement is not None else 0
            return f"学习表现有所下降，相比上期降低了{abs(improvement_val)*100:.1f}%"
        elif trend == 'stable':
            return "学习表现保持稳定"
        else:
            return "暂无对比数据"

class LearningReport(db.Model):
    """
    学习报告模型
    
    生成和存储各种类型的学习报告
    """
    __tablename__ = 'learning_reports'
    
    # 基本信息
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    
    # 报告信息
    report_type = Column(String(50), nullable=False)  # ReportType枚举值
    report_title = Column(String(200), nullable=False)
    report_period = Column(String(20), nullable=False)  # TrackingPeriod枚举值
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # 报告内容
    summary = Column(Text)  # 报告摘要
    key_insights = Column(JSON)  # 关键洞察
    performance_data = Column(JSON)  # 表现数据
    trend_analysis = Column(JSON)  # 趋势分析
    achievements = Column(JSON)  # 成就和亮点
    areas_for_improvement = Column(JSON)  # 需要改进的领域
    recommendations = Column(JSON)  # 建议和行动计划
    
    # 可视化数据
    charts_data = Column(JSON)  # 图表数据
    
    # 报告状态
    is_generated = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    generation_time = Column(DateTime)
    send_time = Column(DateTime)
    
    # 接收者信息
    recipients = Column(JSON)  # 接收者列表（学生、家长、老师等）
    
    # 元数据
    created_time = Column(DateTime, default=datetime.now)
    updated_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    user = relationship('User', backref='learning_reports')
    
    # 索引
    __table_args__ = (
        Index('idx_learning_reports_user_type', 'user_id', 'report_type'),
        Index('idx_learning_reports_period', 'report_period', 'period_start'),
    )
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'report_type': self.report_type,
            'report_title': self.report_title,
            'report_period': self.report_period,
            'period_start': self.period_start.isoformat() if self.period_start is not None else None,
            'period_end': self.period_end.isoformat() if self.period_end is not None else None,
            'summary': self.summary,
            'key_insights': self.key_insights,
            'performance_data': self.performance_data,
            'trend_analysis': self.trend_analysis,
            'achievements': self.achievements,
            'areas_for_improvement': self.areas_for_improvement,
            'recommendations': self.recommendations,
            'charts_data': self.charts_data,
            'is_generated': self.is_generated,
            'is_sent': self.is_sent,
            'generation_time': self.generation_time.isoformat() if self.generation_time is not None else None,
            'send_time': self.send_time.isoformat() if self.send_time is not None else None,
            'recipients': self.recipients,
            'created_time': self.created_time.isoformat() if self.created_time is not None else None
        }
    
    def mark_as_generated(self):
        """标记为已生成"""
        self.is_generated = True
        self.generation_time = datetime.now()
    
    def mark_as_sent(self):
        """标记为已发送"""
        self.is_sent = True
        self.send_time = datetime.now()
    
    def get_report_summary(self) -> Dict:
        """获取报告摘要"""
        period_start = getattr(self, 'period_start', None)
        period_end = getattr(self, 'period_end', None)
        period_str = "未知时间段"
        if period_start is not None and period_end is not None:
            period_str = f"{period_start.strftime('%Y-%m-%d')} 至 {period_end.strftime('%Y-%m-%d')}"
        
        is_generated = getattr(self, 'is_generated', False)
        key_insights = getattr(self, 'key_insights', None)
        recommendations = getattr(self, 'recommendations', None)
        
        return {
            'report_id': self.id,
            'title': self.report_title,
            'type': self.report_type,
            'period': period_str,
            'status': 'generated' if is_generated else 'pending',
            'key_insights_count': len(key_insights) if key_insights else 0,
            'recommendations_count': len(recommendations) if recommendations else 0
        }

class GoalTracking(db.Model):
    """
    目标追踪模型
    
    追踪学习目标的设定和完成情况
    """
    __tablename__ = 'goal_tracking'
    
    # 基本信息
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    
    # 目标信息
    goal_title = Column(String(200), nullable=False)
    goal_description = Column(Text)
    goal_type = Column(String(50), nullable=False)  # 目标类型：score, time, accuracy, completion等
    
    # 目标参数
    target_value = Column(Float, nullable=False)  # 目标值
    current_value = Column(Float, default=0)  # 当前值
    unit = Column(String(20))  # 单位
    
    # 时间范围
    start_date = Column(DateTime, nullable=False)
    target_date = Column(DateTime, nullable=False)
    completion_date = Column(DateTime)
    
    # 进度信息
    progress_percentage = Column(Float, default=0)  # 完成百分比
    is_completed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # 里程碑
    milestones = Column(JSON)  # 里程碑列表
    
    # 关联信息
    subject_id = Column(Integer, ForeignKey('subjects.id'))
    knowledge_point_id = Column(Integer, ForeignKey('knowledge_points.id'))
    
    # 元数据
    created_time = Column(DateTime, default=datetime.now)
    updated_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    user = relationship('User', backref='goal_tracking')
    subject = relationship('Subject', backref='goal_tracking')
    knowledge_point = relationship('KnowledgePoint', backref='goal_tracking')
    
    # 索引
    __table_args__ = (
        Index('idx_goal_tracking_user_active', 'user_id', 'is_active'),
        Index('idx_goal_tracking_target_date', 'target_date'),
    )
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'goal_title': self.goal_title,
            'goal_description': self.goal_description,
            'goal_type': self.goal_type,
            'target_value': self.target_value,
            'current_value': self.current_value,
            'unit': self.unit,
            'start_date': self.start_date.isoformat() if self.start_date is not None else None,
            'target_date': self.target_date.isoformat() if self.target_date is not None else None,
            'completion_date': self.completion_date.isoformat() if self.completion_date is not None else None,
            'progress_percentage': self.progress_percentage,
            'is_completed': self.is_completed,
            'is_active': self.is_active,
            'milestones': self.milestones,
            'subject_id': self.subject_id,
            'knowledge_point_id': self.knowledge_point_id,
            'created_time': self.created_time.isoformat() if self.created_time is not None else None
        }
    
    def update_progress(self, new_value: float):
        """更新进度"""
        self.current_value = new_value
        target_value = getattr(self, 'target_value', None)
        if target_value is not None and target_value > 0:
            self.progress_percentage = min(100, (new_value / target_value) * 100)
        else:
            self.progress_percentage = 0
        
        progress_percentage = getattr(self, 'progress_percentage', 0)
        is_completed = getattr(self, 'is_completed', False)
        if progress_percentage >= 100 and not is_completed:
            self.is_completed = True
            self.completion_date = datetime.now()
    
    def get_remaining_days(self) -> int:
        """获取剩余天数"""
        is_completed = getattr(self, 'is_completed', False)
        if is_completed:
            return 0
        
        target_date = getattr(self, 'target_date', None)
        if target_date is None:
            return 0
        
        remaining = target_date - datetime.now()
        return max(0, remaining.days)
    
    def get_daily_required_progress(self) -> float:
        """获取每日所需进度"""
        is_completed = getattr(self, 'is_completed', False)
        if is_completed:
            return 0
        
        remaining_days = self.get_remaining_days()
        if remaining_days == 0:
            target_value = getattr(self, 'target_value', None)
            current_value = getattr(self, 'current_value', None)
            if target_value is not None and current_value is not None:
                return target_value - current_value
            return 0
        
        target_value = getattr(self, 'target_value', None)
        current_value = getattr(self, 'current_value', None)
        if target_value is not None and current_value is not None:
            remaining_value = target_value - current_value
            return remaining_value / remaining_days
        return 0
    
    def get_status(self) -> Dict:
        """获取目标状态"""
        is_completed = getattr(self, 'is_completed', False)
        target_date = getattr(self, 'target_date', None)
        progress_percentage = getattr(self, 'progress_percentage', None)
        
        if is_completed:
            status = 'completed'
            status_text = '已完成'
        elif target_date is not None and datetime.now() > target_date:
            status = 'overdue'
            status_text = '已逾期'
        elif progress_percentage is not None and progress_percentage >= 80:
            status = 'on_track'
            status_text = '进展良好'
        elif progress_percentage is not None and progress_percentage >= 50:
            status = 'moderate'
            status_text = '进展一般'
        else:
            status = 'behind'
            status_text = '进展缓慢'
        
        return {
            'status': status,
            'status_text': status_text,
            'progress_percentage': progress_percentage,
            'remaining_days': self.get_remaining_days(),
            'daily_required_progress': self.get_daily_required_progress()
        }

class FeedbackRecord(db.Model):
    """
    反馈记录模型
    
    记录各种反馈信息和用户互动
    """
    __tablename__ = 'feedback_records'
    
    # 基本信息
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    
    # 反馈信息
    feedback_type = Column(String(50), nullable=False)  # 反馈类型：system, user, parent, teacher
    feedback_category = Column(String(50), nullable=False)  # 反馈分类：progress, performance, suggestion等
    feedback_title = Column(String(200), nullable=False)
    feedback_content = Column(Text, nullable=False)
    
    # 反馈来源
    source_type = Column(String(50), nullable=False)  # 来源类型：auto, manual
    source_id = Column(String(100))  # 来源ID（如报告ID、考试ID等）
    
    # 反馈状态
    is_read = Column(Boolean, default=False)
    is_acknowledged = Column(Boolean, default=False)
    read_time = Column(DateTime)
    acknowledge_time = Column(DateTime)
    
    # 优先级和重要性
    priority = Column(String(20), default='medium')  # high, medium, low
    importance_score = Column(Float, default=0.5)  # 0-1
    
    # 关联信息
    related_subject_id = Column(Integer, ForeignKey('subjects.id'))
    related_report_id = Column(Integer, ForeignKey('learning_reports.id'))
    
    # 用户响应
    user_response = Column(Text)  # 用户回应
    response_time = Column(DateTime)
    
    # 元数据
    created_time = Column(DateTime, default=datetime.now)
    updated_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    user = relationship('User', backref='feedback_records')
    related_subject = relationship('Subject', backref='feedback_records')
    related_report = relationship('LearningReport', backref='feedback_records')
    
    # 索引
    __table_args__ = (
        Index('idx_feedback_records_user_read', 'user_id', 'is_read'),
        Index('idx_feedback_records_type_priority', 'feedback_type', 'priority'),
    )
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'feedback_type': self.feedback_type,
            'feedback_category': self.feedback_category,
            'feedback_title': self.feedback_title,
            'feedback_content': self.feedback_content,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'is_read': self.is_read,
            'is_acknowledged': self.is_acknowledged,
            'read_time': self.read_time.isoformat() if self.read_time is not None else None,
            'acknowledge_time': self.acknowledge_time.isoformat() if self.acknowledge_time is not None else None,
            'priority': self.priority,
            'importance_score': self.importance_score,
            'related_subject_id': self.related_subject_id,
            'related_report_id': self.related_report_id,
            'user_response': self.user_response,
            'response_time': self.response_time.isoformat() if self.response_time is not None else None,
            'created_time': self.created_time.isoformat() if self.created_time is not None else None
        }
    
    def mark_as_read(self):
        """标记为已读"""
        is_read = getattr(self, 'is_read', False)
        if not is_read:
            self.is_read = True
            self.read_time = datetime.now()
    
    def acknowledge(self, user_response: Optional[str] = None):
        """确认反馈"""
        self.is_acknowledged = True
        self.acknowledge_time = datetime.now()
        if user_response:
            self.user_response = user_response
            self.response_time = datetime.now()
    
    def get_age_in_hours(self) -> float:
        """获取反馈的年龄（小时）"""
        created_time = getattr(self, 'created_time', None)
        if created_time is None:
            return 0.0
        return (datetime.now() - created_time).total_seconds() / 3600
    
    def is_urgent(self) -> bool:
        """判断是否紧急"""
        priority = getattr(self, 'priority', None)
        importance_score = getattr(self, 'importance_score', None)
        is_acknowledged = getattr(self, 'is_acknowledged', False)
        return (priority == 'high' and 
                importance_score is not None and importance_score > 0.7 and 
                not is_acknowledged and 
                self.get_age_in_hours() > 24)