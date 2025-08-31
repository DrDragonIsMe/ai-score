#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 数据模型 - exam.py

Description:
    考试数据模型，定义考试信息、成绩等数据结构。

Author: Chang Xinglong
Date: 2025-01-20
Version: 1.0.0
License: Apache License 2.0
"""


from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from utils.database import db

class ExamType(Enum):
    """考试类型"""
    MOCK = "mock"  # 模拟考试
    PRACTICE = "practice"  # 练习测试
    DIAGNOSTIC = "diagnostic"  # 诊断测试
    FINAL = "final"  # 正式考试

class ExamStatus(Enum):
    """考试状态"""
    SCHEDULED = "scheduled"  # 已安排
    IN_PROGRESS = "in_progress"  # 进行中
    PAUSED = "paused"  # 暂停
    COMPLETED = "completed"  # 已完成
    EXPIRED = "expired"  # 已过期
    CANCELLED = "cancelled"  # 已取消

class DifficultyLevel(Enum):
    """难度等级"""
    EASY = "easy"  # 简单
    MEDIUM = "medium"  # 中等
    HARD = "hard"  # 困难
    EXPERT = "expert"  # 专家级

class ExamSession(db.Model):
    """
    考试会话模型
    
    记录每次考试的完整信息，包括时间管理、答题记录、得分策略等
    """
    __tablename__ = 'exam_sessions'
    
    # 基本信息
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    exam_type = Column(String(20), nullable=False, default=ExamType.PRACTICE.value)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # 考试配置
    subject_id = Column(Integer, ForeignKey('subjects.id'))
    total_questions = Column(Integer, nullable=False, default=0)
    total_time_minutes = Column(Integer, nullable=False)  # 总时间（分钟）
    time_per_question = Column(Float)  # 每题平均时间（分钟）
    difficulty_level = Column(String(20), default=DifficultyLevel.MEDIUM.value)
    
    # 时间管理
    scheduled_start_time = Column(DateTime)
    actual_start_time = Column(DateTime)
    end_time = Column(DateTime)
    pause_duration = Column(Integer, default=0)  # 暂停总时长（秒）
    time_extensions = Column(JSON, nullable=True)  # 时间延长记录
    
    # 考试状态
    status = Column(String(20), nullable=False, default=ExamStatus.SCHEDULED.value)
    current_question_index = Column(Integer, default=0)
    completed_questions = Column(Integer, default=0)
    
    # 题目和答案记录
    question_ids = Column(JSON, nullable=True)  # 题目ID列表
    answers = Column(JSON, nullable=True)  # 答案记录 {question_id: answer}
    question_times = Column(JSON, nullable=True)  # 每题用时 {question_id: seconds}
    question_attempts = Column(JSON, nullable=True)  # 每题尝试次数
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.question_ids is None:
            self.question_ids = []
        if self.answers is None:
            self.answers = {}
        if self.question_times is None:
            self.question_times = {}
        if self.question_attempts is None:
            self.question_attempts = {}
        if self.time_extensions is None:
            self.time_extensions = []
        if self.time_distribution is None:
            self.time_distribution = {}
        if self.strategy_analysis is None:
            self.strategy_analysis = {}
        if self.improvement_suggestions is None:
            self.improvement_suggestions = []
    
    # 得分和分析
    total_score = Column(Float, default=0.0)
    max_possible_score = Column(Float, default=0.0)
    score_percentage = Column(Float, default=0.0)
    correct_answers = Column(Integer, default=0)
    wrong_answers = Column(Integer, default=0)
    skipped_questions = Column(Integer, default=0)
    
    # 时间分析
    time_efficiency = Column(Float, default=0.0)  # 时间效率 0-1
    average_time_per_question = Column(Float, default=0.0)  # 平均每题用时
    time_distribution = Column(JSON, nullable=True)  # 时间分布分析
    
    # 策略分析
    strategy_analysis = Column(JSON, nullable=True)  # 答题策略分析
    improvement_suggestions = Column(JSON, nullable=True)  # 改进建议
    
    # 元数据
    created_time = Column(DateTime, default=datetime.utcnow)
    updated_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship('User', backref='exam_sessions')
    subject = relationship('Subject', backref='exam_sessions')
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'exam_type': self.exam_type,
            'title': self.title,
            'description': self.description,
            'subject_id': self.subject_id,
            'total_questions': self.total_questions,
            'total_time_minutes': self.total_time_minutes,
            'time_per_question': self.time_per_question,
            'difficulty_level': self.difficulty_level,
            'scheduled_start_time': (lambda t: t.isoformat() if t and hasattr(t, 'isoformat') else None)(getattr(self, 'scheduled_start_time', None)),
            'actual_start_time': (lambda t: t.isoformat() if t and hasattr(t, 'isoformat') else None)(getattr(self, 'actual_start_time', None)),
            'end_time': (lambda t: t.isoformat() if t and hasattr(t, 'isoformat') else None)(getattr(self, 'end_time', None)),
            'pause_duration': self.pause_duration,
            'time_extensions': self.time_extensions or [],
            'status': self.status,
            'current_question_index': self.current_question_index,
            'completed_questions': self.completed_questions,
            'progress_percentage': self.get_progress_percentage(),
            'question_ids': self.question_ids or [],
            'total_score': self.total_score,
            'max_possible_score': self.max_possible_score,
            'score_percentage': self.score_percentage,
            'correct_answers': self.correct_answers,
            'wrong_answers': self.wrong_answers,
            'skipped_questions': self.skipped_questions,
            'time_efficiency': self.time_efficiency,
            'average_time_per_question': self.average_time_per_question,
            'time_distribution': self.time_distribution or {},
            'strategy_analysis': self.strategy_analysis or {},
            'improvement_suggestions': self.improvement_suggestions or [],
            'remaining_time': self.get_remaining_time(),
            'is_expired': self.is_expired(),
            'created_time': (lambda t: t.isoformat() if t and hasattr(t, 'isoformat') else None)(getattr(self, 'created_time', None)),
            'updated_time': (lambda t: t.isoformat() if t and hasattr(t, 'isoformat') else None)(getattr(self, 'updated_time', None))
        }
    
    def get_progress_percentage(self) -> float:
        """获取进度百分比"""
        # 获取实际值而不是Column对象
        total_questions_val = getattr(self, 'total_questions', None)
        completed_questions_val = getattr(self, 'completed_questions', None)
        
        total = int(total_questions_val) if total_questions_val is not None else 0
        completed = int(completed_questions_val) if completed_questions_val is not None else 0
        
        if total == 0:
            return 0.0
        return (completed / total) * 100
    
    def get_remaining_time(self) -> Optional[int]:
        """获取剩余时间（秒）"""
        # 获取实际值而不是Column对象
        actual_start_time_val = getattr(self, 'actual_start_time', None)
        status_val = getattr(self, 'status', None)
        total_time_minutes_val = getattr(self, 'total_time_minutes', None)
        pause_duration_val = getattr(self, 'pause_duration', None)
        
        if actual_start_time_val is None or status_val not in [ExamStatus.IN_PROGRESS.value, ExamStatus.PAUSED.value]:
            return None
        
        total_minutes = int(total_time_minutes_val) if total_time_minutes_val is not None else 0
        pause_duration = int(pause_duration_val) if pause_duration_val is not None else 0
        
        total_seconds = total_minutes * 60
        elapsed_seconds = (datetime.utcnow() - actual_start_time_val).total_seconds()
        elapsed_seconds -= pause_duration  # 减去暂停时间
        
        remaining = total_seconds - elapsed_seconds
        return max(0, int(remaining))
    
    def is_expired(self) -> bool:
        """检查是否已过期"""
        remaining_time = self.get_remaining_time()
        return remaining_time is not None and remaining_time <= 0
    
    def start_exam(self):
        """开始考试"""
        self.actual_start_time = datetime.utcnow()
        self.status = ExamStatus.IN_PROGRESS.value
        self.updated_time = datetime.utcnow()
    
    def pause_exam(self):
        """暂停考试"""
        status_val = getattr(self, 'status', None)
        if status_val == ExamStatus.IN_PROGRESS.value:
            self.status = ExamStatus.PAUSED.value
            self.updated_time = datetime.utcnow()
    
    def resume_exam(self):
        """恢复考试"""
        status_val = getattr(self, 'status', None)
        if status_val == ExamStatus.PAUSED.value:
            self.status = ExamStatus.IN_PROGRESS.value
            self.updated_time = datetime.utcnow()
    
    def complete_exam(self):
        """完成考试"""
        self.end_time = datetime.utcnow()
        self.status = ExamStatus.COMPLETED.value
        self.updated_time = datetime.utcnow()
        
        # 计算最终统计
        self._calculate_final_statistics()
    
    def _calculate_final_statistics(self):
        """计算最终统计数据"""
        # 获取实际值而不是Column对象
        actual_start_time_val = getattr(self, 'actual_start_time', None)
        end_time_val = getattr(self, 'end_time', None)
        pause_duration_val = getattr(self, 'pause_duration', None)
        completed_questions_val = getattr(self, 'completed_questions', None)
        total_time_minutes_val = getattr(self, 'total_time_minutes', None)
        max_possible_score_val = getattr(self, 'max_possible_score', None)
        total_score_val = getattr(self, 'total_score', None)
        
        if actual_start_time_val is None or end_time_val is None:
            return
        
        # 计算总用时
        pause_duration = int(pause_duration_val) if pause_duration_val is not None else 0
        total_duration = (end_time_val - actual_start_time_val).total_seconds() - pause_duration
        
        # 计算平均每题用时
        completed = int(completed_questions_val) if completed_questions_val is not None else 0
        if completed > 0:
            self.average_time_per_question = total_duration / completed / 60  # 转换为分钟
        
        # 计算时间效率
        total_minutes = int(total_time_minutes_val) if total_time_minutes_val is not None else 0
        expected_time = total_minutes * 60
        if expected_time > 0:
            self.time_efficiency = min(1.0, expected_time / total_duration)
        
        # 计算得分百分比
        max_score = float(max_possible_score_val) if max_possible_score_val is not None else 0.0
        total_score = float(total_score_val) if total_score_val is not None else 0.0
        if max_score > 0:
            self.score_percentage = (total_score / max_score) * 100
    
    def add_answer(self, question_id: int, answer: str, time_spent: int):
        """添加答案"""
        # 获取实际值而不是Column对象
        answers_val = getattr(self, 'answers', None)
        question_times_val = getattr(self, 'question_times', None)
        question_attempts_val = getattr(self, 'question_attempts', None)
        completed_questions_val = getattr(self, 'completed_questions', None)
        
        if answers_val is None:
            self.answers = {}
            answers_val = {}
        if question_times_val is None:
            self.question_times = {}
            question_times_val = {}
        if question_attempts_val is None:
            self.question_attempts = {}
            question_attempts_val = {}
        
        # 更新答案和时间
        answers_dict = dict(answers_val) if answers_val else {}
        question_times_dict = dict(question_times_val) if question_times_val else {}
        question_attempts_dict = dict(question_attempts_val) if question_attempts_val else {}
        
        question_key = str(question_id)
        answers_dict[question_key] = answer
        question_times_dict[question_key] = time_spent
        question_attempts_dict[question_key] = question_attempts_dict.get(question_key, 0) + 1
        
        # 更新完成题目数
        if question_key not in answers_dict or answers_dict[question_key] != answer:
            completed = int(completed_questions_val) if completed_questions_val is not None else 0
            self.completed_questions = completed + 1
        
        # 保存更新后的字典
        self.answers = answers_dict
        self.question_times = question_times_dict
        self.question_attempts = question_attempts_dict
        self.updated_time = datetime.utcnow()

class TimeAllocation(db.Model):
    """
    时间分配模型
    
    记录和分析用户的时间分配策略
    """
    __tablename__ = 'time_allocations'
    
    # 基本信息
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    exam_session_id = Column(Integer, ForeignKey('exam_sessions.id'))
    
    # 时间分配策略
    strategy_name = Column(String(100), nullable=False)
    strategy_description = Column(Text)
    
    # 分配规则
    easy_question_time = Column(Float)  # 简单题目时间（分钟）
    medium_question_time = Column(Float)  # 中等题目时间（分钟）
    hard_question_time = Column(Float)  # 困难题目时间（分钟）
    review_time_percentage = Column(Float, default=10.0)  # 检查时间百分比
    
    # 时间分配策略
    time_distribution = Column(JSON, nullable=True)  # 各部分时间分布
    buffer_time = Column(Float, default=5.0)  # 缓冲时间（分钟）
    
    # 执行情况
    actual_time_usage = Column(JSON, nullable=True)  # 实际时间使用
    adherence_score = Column(Float, default=0.0)  # 执行度评分 0-1
    
    # 效果评估
    effectiveness_score = Column(Float, default=0.0)  # 有效性评分 0-1
    improvement_areas = Column(JSON, nullable=True)  # 改进领域
    
    # 元数据
    is_active = Column(Boolean, default=True)
    created_time = Column(DateTime, default=datetime.utcnow)
    updated_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship('User', backref='time_allocations')
    exam_session = relationship('ExamSession', backref='time_allocations')
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'exam_session_id': self.exam_session_id,
            'strategy_name': self.strategy_name,
            'strategy_description': self.strategy_description,
            'easy_question_time': self.easy_question_time,
            'medium_question_time': self.medium_question_time,
            'hard_question_time': self.hard_question_time,
            'review_time_percentage': self.review_time_percentage,
            'time_distribution': self.time_distribution or {},
            'buffer_time': self.buffer_time,
            'actual_time_usage': self.actual_time_usage or {},
            'adherence_score': self.adherence_score,
            'effectiveness_score': self.effectiveness_score,
            'improvement_areas': self.improvement_areas or [],
            'is_active': self.is_active,
            'created_time': (lambda t: t.isoformat() if t and hasattr(t, 'isoformat') else None)(getattr(self, 'created_time', None)),
            'updated_time': (lambda t: t.isoformat() if t and hasattr(t, 'isoformat') else None)(getattr(self, 'updated_time', None))
        }
    
    def calculate_total_time(self, question_distribution: Dict[str, int]) -> float:
        """计算总时间需求"""
        total_time = 0.0
        
        # 各难度题目时间
        easy_question_time_val = getattr(self, 'easy_question_time', None)
        medium_question_time_val = getattr(self, 'medium_question_time', None)
        hard_question_time_val = getattr(self, 'hard_question_time', None)
        
        easy_time = float(easy_question_time_val) if easy_question_time_val is not None else 0.0
        medium_time = float(medium_question_time_val) if medium_question_time_val is not None else 0.0
        hard_time = float(hard_question_time_val) if hard_question_time_val is not None else 0.0
        
        total_time += question_distribution.get('easy', 0) * easy_time
        total_time += question_distribution.get('medium', 0) * medium_time
        total_time += question_distribution.get('hard', 0) * hard_time
        
        # 检查时间
        review_time_percentage_val = getattr(self, 'review_time_percentage', None)
        review_percentage = float(review_time_percentage_val) if review_time_percentage_val is not None else 10.0
        review_time = total_time * (review_percentage / 100)
        total_time += review_time
        
        # 缓冲时间
        buffer_time_val = getattr(self, 'buffer_time', None)
        buffer_time = float(buffer_time_val) if buffer_time_val is not None else 0.0
        total_time += buffer_time
        
        return total_time
    
    def get_time_allocation_plan(self, total_questions: int, total_time: int) -> Dict:
        """获取时间分配计划"""
        review_time_percentage_val = getattr(self, 'review_time_percentage', None)
        buffer_time_val = getattr(self, 'buffer_time', None)
        
        review_percentage = float(review_time_percentage_val) if review_time_percentage_val is not None else 10.0
        buffer_time = float(buffer_time_val) if buffer_time_val is not None else 0.0
        
        plan = {
            'total_time_minutes': total_time,
            'question_time_minutes': total_time * (1 - review_percentage / 100) - buffer_time,
            'review_time_minutes': total_time * (review_percentage / 100),
            'buffer_time_minutes': buffer_time,
            'average_time_per_question': 0,
            'time_checkpoints': []
        }
        
        if total_questions > 0:
            plan['average_time_per_question'] = plan['question_time_minutes'] / total_questions
            
            # 生成时间检查点
            checkpoint_interval = max(1, total_questions // 4)  # 每25%设置一个检查点
            for i in range(1, 5):
                checkpoint_question = min(total_questions, i * checkpoint_interval)
                checkpoint_time = plan['question_time_minutes'] * (i / 4)
                plan['time_checkpoints'].append({
                    'question_number': checkpoint_question,
                    'target_time_minutes': checkpoint_time,
                    'progress_percentage': (i / 4) * 100
                })
        
        return plan

class ScoringStrategy(db.Model):
    """
    得分策略模型
    
    记录和分析用户的得分策略和优化建议
    """
    __tablename__ = 'scoring_strategies'
    
    # 基本信息
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    strategy_name = Column(String(100), nullable=False)
    strategy_type = Column(String(50), nullable=False)  # 策略类型：conservative, aggressive, balanced
    
    # 策略配置
    skip_threshold = Column(Float, default=0.3)  # 跳题阈值（不确定度）
    guess_threshold = Column(Float, default=0.5)  # 猜题阈值
    time_pressure_threshold = Column(Float, default=0.8)  # 时间压力阈值
    
    # 题目优先级
    easy_question_priority = Column(Integer, default=1)  # 简单题优先级
    medium_question_priority = Column(Integer, default=2)  # 中等题优先级
    hard_question_priority = Column(Integer, default=3)  # 困难题优先级
    
    # 答题策略
    answer_order_strategy = Column(String(50), default='sequential')  # 答题顺序策略
    review_strategy = Column(String(50), default='uncertain_first')  # 检查策略
    guess_strategy = Column(String(50), default='educated_guess')  # 猜题策略
    
    # 风险管理
    risk_tolerance = Column(Float, default=0.5)  # 风险容忍度 0-1
    certainty_threshold = Column(Float, default=0.7)  # 确定性阈值
    
    # 其他策略参数
    strategy_parameters = Column(JSON, nullable=True)  # 其他策略参数
    
    # 效果统计
    usage_count = Column(Integer, default=0)  # 使用次数
    average_score = Column(Float, default=0.0)  # 平均得分
    success_rate = Column(Float, default=0.0)  # 成功率
    
    # 元数据
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_time = Column(DateTime, default=datetime.utcnow)
    updated_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship('User', backref='scoring_strategies')
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'strategy_name': self.strategy_name,
            'strategy_type': self.strategy_type,
            'skip_threshold': self.skip_threshold,
            'guess_threshold': self.guess_threshold,
            'time_pressure_threshold': self.time_pressure_threshold,
            'easy_question_priority': self.easy_question_priority,
            'medium_question_priority': self.medium_question_priority,
            'hard_question_priority': self.hard_question_priority,
            'answer_order_strategy': self.answer_order_strategy,
            'review_strategy': self.review_strategy,
            'guess_strategy': self.guess_strategy,
            'risk_tolerance': self.risk_tolerance,
            'certainty_threshold': self.certainty_threshold,
            'strategy_parameters': self.strategy_parameters or {},
            'usage_count': self.usage_count,
            'average_score': self.average_score,
            'success_rate': self.success_rate,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'created_time': (lambda t: t.isoformat() if t and hasattr(t, 'isoformat') else None)(getattr(self, 'created_time', None)),
            'updated_time': (lambda t: t.isoformat() if t and hasattr(t, 'isoformat') else None)(getattr(self, 'updated_time', None))
        }
    
    def get_question_order(self, questions: List[Dict]) -> List[Dict]:
        """根据策略获取题目顺序"""
        answer_order_strategy = getattr(self, 'answer_order_strategy', None)
        if answer_order_strategy == 'difficulty_ascending':
            # 按难度递增排序
            return sorted(questions, key=lambda q: q.get('difficulty_score', 0.5))
        elif answer_order_strategy == 'difficulty_descending':
            # 按难度递减排序
            return sorted(questions, key=lambda q: q.get('difficulty_score', 0.5), reverse=True)
        elif answer_order_strategy == 'confidence_descending':
            # 按信心度递减排序
            return sorted(questions, key=lambda q: q.get('confidence_score', 0.5), reverse=True)
        else:
            # 默认顺序
            return questions
    
    def should_skip_question(self, confidence: float, time_remaining_ratio: float) -> bool:
        """判断是否应该跳过题目"""
        skip_threshold_val = getattr(self, 'skip_threshold', None)
        time_pressure_threshold_val = getattr(self, 'time_pressure_threshold', None)
        certainty_threshold_val = getattr(self, 'certainty_threshold', None)
        
        skip_threshold = float(skip_threshold_val) if skip_threshold_val is not None else 0.3
        time_pressure_threshold = float(time_pressure_threshold_val) if time_pressure_threshold_val is not None else 0.8
        certainty_threshold = float(certainty_threshold_val) if certainty_threshold_val is not None else 0.7
        
        # 信心度过低
        if confidence < skip_threshold:
            return True
        
        # 时间压力过大且信心度不高
        if time_remaining_ratio < time_pressure_threshold and confidence < certainty_threshold:
            return True
        
        return False
    
    def should_guess(self, confidence: float, time_remaining_ratio: float) -> bool:
        """判断是否应该猜题"""
        guess_threshold_val = getattr(self, 'guess_threshold', None)
        guess_threshold = float(guess_threshold_val) if guess_threshold_val is not None else 0.5
        
        # 时间不足时降低猜题阈值
        adjusted_threshold = guess_threshold
        if time_remaining_ratio < 0.2:  # 剩余时间不足20%
            adjusted_threshold *= 0.7
        
        return confidence >= adjusted_threshold
    
    def update_statistics(self, score: float, total_score: float):
        """更新策略统计"""
        usage_count_val = getattr(self, 'usage_count', None)
        average_score_val = getattr(self, 'average_score', None)
        success_rate_val = getattr(self, 'success_rate', None)
        
        usage_count = int(usage_count_val) if usage_count_val is not None else 0
        average_score = float(average_score_val) if average_score_val is not None else 0.0
        
        self.usage_count = usage_count + 1
        
        # 更新平均得分
        if self.usage_count == 1:
            self.average_score = score
        else:
            self.average_score = (average_score * usage_count + score) / self.usage_count
        
        # 更新成功率（假设60%以上为成功）
        success_threshold = total_score * 0.6
        success_rate = float(success_rate_val) if success_rate_val is not None else 0.0
        if score >= success_threshold:
            success_count = (success_rate * (self.usage_count - 1)) + 1
        else:
            success_count = success_rate * (self.usage_count - 1)
        
        self.success_rate = success_count / self.usage_count
        self.updated_time = datetime.utcnow()

class ExamAnalytics(db.Model):
    """
    考试分析模型
    
    存储考试的详细分析结果和改进建议
    """
    __tablename__ = 'exam_analytics'
    
    # 基本信息
    id = Column(Integer, primary_key=True)
    exam_session_id = Column(Integer, ForeignKey('exam_sessions.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # 时间分析
    time_analysis = Column(JSON, nullable=True)  # 时间使用分析
    time_efficiency_score = Column(Float, default=0.0)  # 时间效率评分
    time_management_suggestions = Column(JSON, nullable=True)  # 时间管理建议
    
    # 答题分析
    answer_pattern_analysis = Column(JSON, nullable=True)  # 答题模式分析
    accuracy_by_difficulty = Column(JSON, nullable=True)  # 各难度准确率
    accuracy_by_topic = Column(JSON, nullable=True)  # 各主题准确率
    
    # 策略分析
    strategy_effectiveness = Column(JSON, nullable=True)  # 策略有效性
    optimal_strategy_suggestions = Column(JSON, nullable=True)  # 最优策略建议
    
    # 改进建议
    strengths = Column(JSON, nullable=True)  # 优势领域
    weaknesses = Column(JSON, nullable=True)  # 薄弱领域
    improvement_priorities = Column(JSON, nullable=True)  # 改进优先级
    specific_recommendations = Column(JSON, nullable=True)  # 具体建议
    
    # 预测分析
    predicted_improvement = Column(JSON, nullable=True)  # 预测改进幅度
    next_exam_recommendations = Column(JSON, nullable=True)  # 下次考试建议
    
    # 元数据
    analysis_version = Column(String(20), default='1.0')
    created_time = Column(DateTime, default=datetime.utcnow)
    updated_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    exam_session = relationship('ExamSession', backref='analytics')
    user = relationship('User', backref='exam_analytics')
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'exam_session_id': self.exam_session_id,
            'user_id': self.user_id,
            'time_analysis': self.time_analysis or {},
            'time_efficiency_score': self.time_efficiency_score,
            'time_management_suggestions': self.time_management_suggestions or [],
            'answer_pattern_analysis': self.answer_pattern_analysis or {},
            'accuracy_by_difficulty': self.accuracy_by_difficulty or {},
            'accuracy_by_topic': self.accuracy_by_topic or {},
            'strategy_effectiveness': self.strategy_effectiveness or {},
            'optimal_strategy_suggestions': self.optimal_strategy_suggestions or [],
            'strengths': self.strengths or [],
            'weaknesses': self.weaknesses or [],
            'improvement_priorities': self.improvement_priorities or [],
            'specific_recommendations': self.specific_recommendations or [],
            'predicted_improvement': self.predicted_improvement or {},
            'next_exam_recommendations': self.next_exam_recommendations or [],
            'analysis_version': self.analysis_version,
            'created_time': (lambda t: t.isoformat() if t and hasattr(t, 'isoformat') else None)(getattr(self, 'created_time', None)),
            'updated_time': (lambda t: t.isoformat() if t and hasattr(t, 'isoformat') else None)(getattr(self, 'updated_time', None))
        }