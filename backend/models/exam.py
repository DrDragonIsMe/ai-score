# -*- coding: utf-8 -*-
"""
应试优化数据模型

包含限时模拟、时间分配、得分策略等相关模型
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
    time_extensions = Column(JSON, default=list)  # 时间延长记录
    
    # 考试状态
    status = Column(String(20), nullable=False, default=ExamStatus.SCHEDULED.value)
    current_question_index = Column(Integer, default=0)
    completed_questions = Column(Integer, default=0)
    
    # 答题记录
    question_ids = Column(JSON, default=list)  # 题目ID列表
    answers = Column(JSON, default=dict)  # 答案记录 {question_id: answer}
    question_times = Column(JSON, default=dict)  # 每题用时 {question_id: seconds}
    question_attempts = Column(JSON, default=dict)  # 每题尝试次数
    
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
    time_distribution = Column(JSON, default=dict)  # 时间分布分析
    
    # 策略分析
    strategy_analysis = Column(JSON, default=dict)  # 答题策略分析
    improvement_suggestions = Column(JSON, default=list)  # 改进建议
    
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
            'scheduled_start_time': self.scheduled_start_time.isoformat() if self.scheduled_start_time else None,
            'actual_start_time': self.actual_start_time.isoformat() if self.actual_start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
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
            'created_time': self.created_time.isoformat(),
            'updated_time': self.updated_time.isoformat()
        }
    
    def get_progress_percentage(self) -> float:
        """获取进度百分比"""
        if self.total_questions == 0:
            return 0.0
        return (self.completed_questions / self.total_questions) * 100
    
    def get_remaining_time(self) -> Optional[int]:
        """获取剩余时间（秒）"""
        if not self.actual_start_time or self.status not in [ExamStatus.IN_PROGRESS.value, ExamStatus.PAUSED.value]:
            return None
        
        total_seconds = self.total_time_minutes * 60
        elapsed_seconds = (datetime.utcnow() - self.actual_start_time).total_seconds()
        elapsed_seconds -= self.pause_duration  # 减去暂停时间
        
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
        if self.status == ExamStatus.IN_PROGRESS.value:
            self.status = ExamStatus.PAUSED.value
            self.updated_time = datetime.utcnow()
    
    def resume_exam(self):
        """恢复考试"""
        if self.status == ExamStatus.PAUSED.value:
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
        if not self.actual_start_time or not self.end_time:
            return
        
        # 计算总用时
        total_duration = (self.end_time - self.actual_start_time).total_seconds() - self.pause_duration
        
        # 计算平均每题用时
        if self.completed_questions > 0:
            self.average_time_per_question = total_duration / self.completed_questions / 60  # 转换为分钟
        
        # 计算时间效率
        expected_time = self.total_time_minutes * 60
        if expected_time > 0:
            self.time_efficiency = min(1.0, expected_time / total_duration)
        
        # 计算得分百分比
        if self.max_possible_score > 0:
            self.score_percentage = (self.total_score / self.max_possible_score) * 100
    
    def add_answer(self, question_id: int, answer: str, time_spent: int):
        """添加答案"""
        if not self.answers:
            self.answers = {}
        if not self.question_times:
            self.question_times = {}
        if not self.question_attempts:
            self.question_attempts = {}
        
        self.answers[str(question_id)] = answer
        self.question_times[str(question_id)] = time_spent
        
        # 更新尝试次数
        question_key = str(question_id)
        self.question_attempts[question_key] = self.question_attempts.get(question_key, 0) + 1
        
        # 更新完成题目数
        if question_key not in self.answers or self.answers[question_key] != answer:
            self.completed_questions += 1
        
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
    
    # 时间分布
    time_distribution = Column(JSON, default=dict)  # 各部分时间分布
    buffer_time = Column(Float, default=5.0)  # 缓冲时间（分钟）
    
    # 执行情况
    actual_time_usage = Column(JSON, default=dict)  # 实际时间使用
    adherence_score = Column(Float, default=0.0)  # 执行度评分 0-1
    
    # 效果分析
    effectiveness_score = Column(Float, default=0.0)  # 有效性评分 0-1
    improvement_areas = Column(JSON, default=list)  # 改进领域
    
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
            'created_time': self.created_time.isoformat(),
            'updated_time': self.updated_time.isoformat()
        }
    
    def calculate_total_time(self, question_distribution: Dict[str, int]) -> float:
        """计算总时间需求"""
        total_time = 0.0
        
        # 各难度题目时间
        total_time += question_distribution.get('easy', 0) * (self.easy_question_time or 0)
        total_time += question_distribution.get('medium', 0) * (self.medium_question_time or 0)
        total_time += question_distribution.get('hard', 0) * (self.hard_question_time or 0)
        
        # 检查时间
        review_time = total_time * (self.review_time_percentage / 100)
        total_time += review_time
        
        # 缓冲时间
        total_time += self.buffer_time or 0
        
        return total_time
    
    def get_time_allocation_plan(self, total_questions: int, total_time: int) -> Dict:
        """获取时间分配计划"""
        plan = {
            'total_time_minutes': total_time,
            'question_time_minutes': total_time * (1 - self.review_time_percentage / 100) - (self.buffer_time or 0),
            'review_time_minutes': total_time * (self.review_time_percentage / 100),
            'buffer_time_minutes': self.buffer_time or 0,
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
    
    # 策略参数
    strategy_parameters = Column(JSON, default=dict)  # 其他策略参数
    
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
            'created_time': self.created_time.isoformat(),
            'updated_time': self.updated_time.isoformat()
        }
    
    def get_question_order(self, questions: List[Dict]) -> List[Dict]:
        """根据策略获取题目顺序"""
        if self.answer_order_strategy == 'difficulty_ascending':
            # 按难度递增排序
            return sorted(questions, key=lambda q: q.get('difficulty_score', 0.5))
        elif self.answer_order_strategy == 'difficulty_descending':
            # 按难度递减排序
            return sorted(questions, key=lambda q: q.get('difficulty_score', 0.5), reverse=True)
        elif self.answer_order_strategy == 'confidence_descending':
            # 按信心度递减排序
            return sorted(questions, key=lambda q: q.get('confidence_score', 0.5), reverse=True)
        else:
            # 默认顺序
            return questions
    
    def should_skip_question(self, confidence: float, time_remaining_ratio: float) -> bool:
        """判断是否应该跳过题目"""
        # 信心度过低
        if confidence < self.skip_threshold:
            return True
        
        # 时间压力过大且信心度不高
        if time_remaining_ratio < self.time_pressure_threshold and confidence < self.certainty_threshold:
            return True
        
        return False
    
    def should_guess(self, confidence: float, time_remaining_ratio: float) -> bool:
        """判断是否应该猜题"""
        # 时间不足时降低猜题阈值
        adjusted_threshold = self.guess_threshold
        if time_remaining_ratio < 0.2:  # 剩余时间不足20%
            adjusted_threshold *= 0.7
        
        return confidence >= adjusted_threshold
    
    def update_statistics(self, score: float, total_score: float):
        """更新策略统计"""
        self.usage_count += 1
        
        # 更新平均得分
        if self.usage_count == 1:
            self.average_score = score
        else:
            self.average_score = (self.average_score * (self.usage_count - 1) + score) / self.usage_count
        
        # 更新成功率（假设60%以上为成功）
        success_threshold = total_score * 0.6
        if score >= success_threshold:
            success_count = (self.success_rate * (self.usage_count - 1)) + 1
        else:
            success_count = self.success_rate * (self.usage_count - 1)
        
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
    time_analysis = Column(JSON, default=dict)  # 时间使用分析
    time_efficiency_score = Column(Float, default=0.0)  # 时间效率评分
    time_management_suggestions = Column(JSON, default=list)  # 时间管理建议
    
    # 答题分析
    answer_pattern_analysis = Column(JSON, default=dict)  # 答题模式分析
    accuracy_by_difficulty = Column(JSON, default=dict)  # 各难度准确率
    accuracy_by_topic = Column(JSON, default=dict)  # 各主题准确率
    
    # 策略分析
    strategy_effectiveness = Column(JSON, default=dict)  # 策略有效性
    optimal_strategy_suggestions = Column(JSON, default=list)  # 最优策略建议
    
    # 改进建议
    strengths = Column(JSON, default=list)  # 优势领域
    weaknesses = Column(JSON, default=list)  # 薄弱领域
    improvement_priorities = Column(JSON, default=list)  # 改进优先级
    specific_recommendations = Column(JSON, default=list)  # 具体建议
    
    # 预测分析
    predicted_improvement = Column(JSON, default=dict)  # 预测改进幅度
    next_exam_recommendations = Column(JSON, default=list)  # 下次考试建议
    
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
            'created_time': self.created_time.isoformat(),
            'updated_time': self.updated_time.isoformat()
        }