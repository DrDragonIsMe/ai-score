#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 业务服务 - tracking_service.py

Description:
    跟踪服务，提供学习行为分析和统计。

Author: Chang Xinglong
Date: 2025-01-20
Version: 1.0.0
License: Apache License 2.0
"""


import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import sessionmaker

from models.tracking import (
    LearningMetric, PerformanceSnapshot, LearningReport, GoalTracking, FeedbackRecord
)
from models.user import User
from models.knowledge import Subject
from models.knowledge import KnowledgePoint
from models.question import Question
from models.learning import LearningPath, StudyRecord
from models.learning import MemoryCard
from models.mistake import MistakeRecord
from models.exam import ExamSession
# from services.ai_service import AIService  # 模块不存在，暂时注释
from utils.database import db
from utils.logger import logger

class TrackingService:
    """
    追踪服务类
    
    提供学习效果追踪、数据分析和报告生成的核心功能
    """
    
    def __init__(self):
        pass  # AIService not available
    
    # ==================== 数据收集 ====================
    
    def collect_learning_metrics(self, user_id: int, period_start: datetime, period_end: datetime) -> List[Dict]:
        """
        收集学习指标数据
        
        Args:
            user_id: 用户ID
            period_start: 统计开始时间
            period_end: 统计结束时间
            
        Returns:
            指标数据列表
        """
        try:
            metrics = []
            
            # 学习时长指标
            learning_time = self._collect_learning_time_metrics(user_id, period_start, period_end)
            metrics.extend(learning_time)
            
            # 题目数量指标
            question_metrics = self._collect_question_metrics(user_id, period_start, period_end)
            metrics.extend(question_metrics)
            
            # 准确率指标
            accuracy_metrics = self._collect_accuracy_metrics(user_id, period_start, period_end)
            metrics.extend(accuracy_metrics)
            
            # 进度指标
            progress_metrics = self._collect_progress_metrics(user_id, period_start, period_end)
            metrics.extend(progress_metrics)
            
            # 记忆保持率指标
            memory_metrics = self._collect_memory_metrics(user_id, period_start, period_end)
            metrics.extend(memory_metrics)
            
            # 考试表现指标
            exam_metrics = self._collect_exam_metrics(user_id, period_start, period_end)
            metrics.extend(exam_metrics)
            
            # 错误减少率指标
            mistake_metrics = self._collect_mistake_metrics(user_id, period_start, period_end)
            metrics.extend(mistake_metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"收集学习指标失败: {str(e)}")
            return []
    
    def _collect_learning_time_metrics(self, user_id: int, period_start: datetime, period_end: datetime) -> List[Dict]:
        """收集学习时长指标"""
        metrics = []
        
        # 总学习时长
        total_time = db.session.query(func.sum(LearningSession.duration_minutes)).filter(
            LearningSession.user_id == user_id,
            LearningSession.start_time >= period_start,
            LearningSession.start_time <= period_end
        ).scalar() or 0
        
        metrics.append({
            'metric_type': MetricType.LEARNING_TIME.value,
            'metric_name': '总学习时长',
            'metric_value': total_time,
            'metric_unit': '分钟'
        })
        
        # 平均每日学习时长
        days = (period_end - period_start).days + 1
        avg_daily_time = total_time / days if days > 0 else 0
        
        metrics.append({
            'metric_type': MetricType.LEARNING_TIME.value,
            'metric_name': '平均每日学习时长',
            'metric_value': avg_daily_time,
            'metric_unit': '分钟'
        })
        
        # 按学科统计学习时长
        subject_times = db.session.query(
            Subject.name,
            func.sum(LearningSession.duration_minutes)
        ).join(LearningSession).filter(
            LearningSession.user_id == user_id,
            LearningSession.start_time >= period_start,
            LearningSession.start_time <= period_end
        ).group_by(Subject.id).all()
        
        for subject_name, subject_time in subject_times:
            metrics.append({
                'metric_type': MetricType.LEARNING_TIME.value,
                'metric_name': f'{subject_name}学习时长',
                'metric_value': subject_time or 0,
                'metric_unit': '分钟',
                'context_data': {'subject': subject_name}
            })
        
        return metrics
    
    def _collect_question_metrics(self, user_id: int, period_start: datetime, period_end: datetime) -> List[Dict]:
        """收集题目数量指标"""
        metrics = []
        
        # 总答题数
        total_questions = db.session.query(func.count(UserAnswer.id)).filter(
            UserAnswer.user_id == user_id,
            UserAnswer.created_time >= period_start,
            UserAnswer.created_time <= period_end
        ).scalar() or 0
        
        metrics.append({
            'metric_type': MetricType.QUESTION_COUNT.value,
            'metric_name': '总答题数',
            'metric_value': total_questions,
            'metric_unit': '题'
        })
        
        # 按难度统计答题数
        difficulty_counts = db.session.query(
            Question.difficulty_level,
            func.count(UserAnswer.id)
        ).join(UserAnswer).filter(
            UserAnswer.user_id == user_id,
            UserAnswer.created_time >= period_start,
            UserAnswer.created_time <= period_end
        ).group_by(Question.difficulty_level).all()
        
        for difficulty, count in difficulty_counts:
            metrics.append({
                'metric_type': MetricType.QUESTION_COUNT.value,
                'metric_name': f'{difficulty}难度答题数',
                'metric_value': count,
                'metric_unit': '题',
                'context_data': {'difficulty': difficulty}
            })
        
        return metrics
    
    def _collect_accuracy_metrics(self, user_id: int, period_start: datetime, period_end: datetime) -> List[Dict]:
        """收集准确率指标"""
        metrics = []
        
        # 总体准确率
        total_answers = db.session.query(func.count(UserAnswer.id)).filter(
            UserAnswer.user_id == user_id,
            UserAnswer.created_time >= period_start,
            UserAnswer.created_time <= period_end
        ).scalar() or 0
        
        correct_answers = db.session.query(func.count(UserAnswer.id)).filter(
            UserAnswer.user_id == user_id,
            UserAnswer.is_correct == True,
            UserAnswer.created_time >= period_start,
            UserAnswer.created_time <= period_end
        ).scalar() or 0
        
        overall_accuracy = (correct_answers / total_answers * 100) if total_answers > 0 else 0
        
        metrics.append({
            'metric_type': MetricType.ACCURACY_RATE.value,
            'metric_name': '总体准确率',
            'metric_value': overall_accuracy,
            'metric_unit': '%'
        })
        
        # 按学科统计准确率
        subject_accuracy = db.session.query(
            Subject.name,
            func.count(UserAnswer.id).label('total'),
            func.sum(func.cast(UserAnswer.is_correct, db.Integer)).label('correct')
        ).join(Question).join(UserAnswer).filter(
            UserAnswer.user_id == user_id,
            UserAnswer.created_time >= period_start,
            UserAnswer.created_time <= period_end
        ).group_by(Subject.id).all()
        
        for subject_name, total, correct in subject_accuracy:
            accuracy = (correct / total * 100) if total > 0 else 0
            metrics.append({
                'metric_type': MetricType.ACCURACY_RATE.value,
                'metric_name': f'{subject_name}准确率',
                'metric_value': accuracy,
                'metric_unit': '%',
                'context_data': {'subject': subject_name}
            })
        
        return metrics
    
    def _collect_progress_metrics(self, user_id: int, period_start: datetime, period_end: datetime) -> List[Dict]:
        """收集进度指标"""
        metrics = []
        
        # 知识点掌握进度
        progress_records = db.session.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.updated_time >= period_start,
            LearningProgress.updated_time <= period_end
        ).all()
        
        if progress_records:
            avg_mastery = statistics.mean([p.mastery_level for p in progress_records])
            metrics.append({
                'metric_type': MetricType.KNOWLEDGE_MASTERY.value,
                'metric_name': '平均知识掌握度',
                'metric_value': avg_mastery * 100,
                'metric_unit': '%'
            })
        
        return metrics
    
    def _collect_memory_metrics(self, user_id: int, period_start: datetime, period_end: datetime) -> List[Dict]:
        """收集记忆保持率指标"""
        metrics = []
        
        # 复习记录统计
        review_records = db.session.query(ReviewRecord).filter(
            ReviewRecord.user_id == user_id,
            ReviewRecord.review_time >= period_start,
            ReviewRecord.review_time <= period_end
        ).all()
        
        if review_records:
            # 记忆保持率
            correct_reviews = sum(1 for r in review_records if r.is_correct)
            retention_rate = (correct_reviews / len(review_records) * 100) if review_records else 0
            
            metrics.append({
                'metric_type': MetricType.MEMORY_RETENTION.value,
                'metric_name': '记忆保持率',
                'metric_value': retention_rate,
                'metric_unit': '%'
            })
        
        return metrics
    
    def _collect_exam_metrics(self, user_id: int, period_start: datetime, period_end: datetime) -> List[Dict]:
        """收集考试表现指标"""
        metrics = []
        
        # 考试成绩统计
        exam_sessions = db.session.query(ExamSession).filter(
            ExamSession.user_id == user_id,
            ExamSession.start_time >= period_start,
            ExamSession.start_time <= period_end,
            ExamSession.status == 'completed'
        ).all()
        
        if exam_sessions:
            avg_score = statistics.mean([e.final_score for e in exam_sessions if e.final_score])
            metrics.append({
                'metric_type': MetricType.EXAM_PERFORMANCE.value,
                'metric_name': '平均考试成绩',
                'metric_value': avg_score,
                'metric_unit': '分'
            })
        
        return metrics
    
    def _collect_mistake_metrics(self, user_id: int, period_start: datetime, period_end: datetime) -> List[Dict]:
        """收集错误减少率指标"""
        metrics = []
        
        # 错题记录统计
        mistake_count = db.session.query(func.count(MistakeRecord.id)).filter(
            MistakeRecord.user_id == user_id,
            MistakeRecord.created_time >= period_start,
            MistakeRecord.created_time <= period_end
        ).scalar() or 0
        
        # 计算错误减少率（需要对比前一个周期）
        prev_period_start = period_start - (period_end - period_start)
        prev_mistake_count = db.session.query(func.count(MistakeRecord.id)).filter(
            MistakeRecord.user_id == user_id,
            MistakeRecord.created_time >= prev_period_start,
            MistakeRecord.created_time < period_start
        ).scalar() or 0
        
        if prev_mistake_count > 0:
            reduction_rate = ((prev_mistake_count - mistake_count) / prev_mistake_count * 100)
        else:
            reduction_rate = 0
        
        metrics.append({
            'metric_type': MetricType.MISTAKE_REDUCTION.value,
            'metric_name': '错误减少率',
            'metric_value': reduction_rate,
            'metric_unit': '%'
        })
        
        return metrics
    
    def save_learning_metrics(self, user_id: int, tenant_id: int, metrics: List[Dict], 
                            period_type: str, period_start: datetime, period_end: datetime) -> List[LearningMetric]:
        """
        保存学习指标数据
        
        Args:
            user_id: 用户ID
            tenant_id: 租户ID
            metrics: 指标数据列表
            period_type: 周期类型
            period_start: 周期开始时间
            period_end: 周期结束时间
            
        Returns:
            保存的指标记录列表
        """
        try:
            saved_metrics = []
            
            for metric_data in metrics:
                metric = LearningMetric(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    metric_type=metric_data['metric_type'],
                    metric_name=metric_data['metric_name'],
                    metric_value=metric_data['metric_value'],
                    metric_unit=metric_data.get('metric_unit'),
                    subject_id=metric_data.get('subject_id'),
                    knowledge_point_id=metric_data.get('knowledge_point_id'),
                    difficulty_level=metric_data.get('difficulty_level'),
                    period_type=period_type,
                    period_start=period_start,
                    period_end=period_end,
                    context_data=metric_data.get('context_data'),
                    tags=metric_data.get('tags')
                )
                
                db.session.add(metric)
                saved_metrics.append(metric)
            
            db.session.commit()
            return saved_metrics
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"保存学习指标失败: {str(e)}")
            return []
    
    # ==================== 性能快照 ====================
    
    def create_performance_snapshot(self, user_id: int, tenant_id: int, period_type: str, 
                                  period_start: datetime, period_end: datetime) -> Optional[PerformanceSnapshot]:
        """
        创建性能快照
        
        Args:
            user_id: 用户ID
            tenant_id: 租户ID
            period_type: 周期类型
            period_start: 周期开始时间
            period_end: 周期结束时间
            
        Returns:
            性能快照对象
        """
        try:
            # 收集指标数据
            metrics = self.collect_learning_metrics(user_id, period_start, period_end)
            
            # 计算综合指标
            overall_score = self._calculate_overall_score(metrics)
            learning_efficiency = self._calculate_learning_efficiency(metrics)
            knowledge_growth = self._calculate_knowledge_growth(user_id, period_start, period_end)
            skill_improvement = self._calculate_skill_improvement(user_id, period_start, period_end)
            
            # 分项指标
            time_metrics = self._extract_time_metrics(metrics)
            accuracy_metrics = self._extract_accuracy_metrics(metrics)
            progress_metrics = self._extract_progress_metrics(metrics)
            engagement_metrics = self._calculate_engagement_metrics(user_id, period_start, period_end)
            
            # 学科表现
            subject_performance = self._calculate_subject_performance(user_id, period_start, period_end)
            
            # 获取上一个快照
            previous_snapshot = db.session.query(PerformanceSnapshot).filter(
                PerformanceSnapshot.user_id == user_id,
                PerformanceSnapshot.period_type == period_type,
                PerformanceSnapshot.snapshot_date < period_end
            ).order_by(PerformanceSnapshot.snapshot_date.desc()).first()
            
            # 计算改进率
            improvement_rate = None
            if previous_snapshot and previous_snapshot.overall_score:
                improvement_rate = (overall_score - previous_snapshot.overall_score) / previous_snapshot.overall_score
            
            # 预测下期得分
            predicted_score, confidence = self._predict_next_performance(user_id, overall_score, improvement_rate)
            
            # 创建快照
            snapshot = PerformanceSnapshot(
                user_id=user_id,
                tenant_id=tenant_id,
                period_type=period_type,
                period_start=period_start,
                period_end=period_end,
                overall_score=overall_score,
                learning_efficiency=learning_efficiency,
                knowledge_growth=knowledge_growth,
                skill_improvement=skill_improvement,
                time_metrics=time_metrics,
                accuracy_metrics=accuracy_metrics,
                progress_metrics=progress_metrics,
                engagement_metrics=engagement_metrics,
                subject_performance=subject_performance,
                previous_snapshot_id=previous_snapshot.id if previous_snapshot else None,
                improvement_rate=improvement_rate,
                predicted_next_score=predicted_score,
                confidence_level=confidence
            )
            
            db.session.add(snapshot)
            db.session.commit()
            
            return snapshot
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建性能快照失败: {str(e)}")
            return None
    
    def _calculate_overall_score(self, metrics: List[Dict]) -> float:
        """计算综合得分"""
        if not metrics:
            return 0.0
        
        # 权重配置
        weights = {
            MetricType.ACCURACY_RATE.value: 0.3,
            MetricType.LEARNING_TIME.value: 0.2,
            MetricType.KNOWLEDGE_MASTERY.value: 0.2,
            MetricType.MEMORY_RETENTION.value: 0.15,
            MetricType.EXAM_PERFORMANCE.value: 0.15
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric in metrics:
            metric_type = metric['metric_type']
            if metric_type in weights:
                # 标准化指标值到0-100范围
                normalized_value = self._normalize_metric_value(metric)
                weighted_sum += normalized_value * weights[metric_type]
                total_weight += weights[metric_type]
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _normalize_metric_value(self, metric: Dict) -> float:
        """标准化指标值"""
        metric_type = metric['metric_type']
        value = metric['metric_value']
        
        if metric_type == MetricType.ACCURACY_RATE.value:
            return min(100, max(0, value))  # 已经是百分比
        elif metric_type == MetricType.LEARNING_TIME.value:
            # 学习时长：假设每日2小时为满分
            if '每日' in metric['metric_name']:
                return min(100, (value / 120) * 100)
            else:
                return min(100, (value / 3600) * 100)  # 月度总时长
        elif metric_type in [MetricType.KNOWLEDGE_MASTERY.value, MetricType.MEMORY_RETENTION.value]:
            return min(100, max(0, value))  # 已经是百分比
        elif metric_type == MetricType.EXAM_PERFORMANCE.value:
            return min(100, max(0, value))  # 考试分数
        else:
            return value
    
    def _calculate_learning_efficiency(self, metrics: List[Dict]) -> float:
        """计算学习效率"""
        # 学习效率 = 准确率 / 学习时长（标准化）
        accuracy = 0
        time_spent = 0
        
        for metric in metrics:
            if metric['metric_type'] == MetricType.ACCURACY_RATE.value and '总体' in metric['metric_name']:
                accuracy = metric['metric_value']
            elif metric['metric_type'] == MetricType.LEARNING_TIME.value and '平均每日' in metric['metric_name']:
                time_spent = metric['metric_value']
        
        if time_spent > 0:
            efficiency = (accuracy / 100) * (120 / max(time_spent, 30))  # 标准化到2小时
            return min(1.0, efficiency)
        
        return 0.0
    
    def _calculate_knowledge_growth(self, user_id: int, period_start: datetime, period_end: datetime) -> float:
        """计算知识增长率"""
        # 比较期初期末的知识掌握度
        start_mastery = db.session.query(func.avg(LearningProgress.mastery_level)).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.updated_time <= period_start
        ).scalar() or 0
        
        end_mastery = db.session.query(func.avg(LearningProgress.mastery_level)).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.updated_time <= period_end
        ).scalar() or 0
        
        if start_mastery > 0:
            growth = (end_mastery - start_mastery) / start_mastery
            return max(0, min(1, growth))
        
        return 0.0
    
    def _calculate_skill_improvement(self, user_id: int, period_start: datetime, period_end: datetime) -> float:
        """计算技能提升度"""
        # 基于答题准确率的提升
        period_duration = period_end - period_start
        mid_point = period_start + period_duration / 2
        
        # 前半期准确率
        early_accuracy = self._get_accuracy_for_period(user_id, period_start, mid_point)
        # 后半期准确率
        late_accuracy = self._get_accuracy_for_period(user_id, mid_point, period_end)
        
        if early_accuracy > 0:
            improvement = (late_accuracy - early_accuracy) / early_accuracy
            return max(0, min(1, improvement))
        
        return 0.0
    
    def _get_accuracy_for_period(self, user_id: int, start_time: datetime, end_time: datetime) -> float:
        """获取指定时期的准确率"""
        total = db.session.query(func.count(UserAnswer.id)).filter(
            UserAnswer.user_id == user_id,
            UserAnswer.created_time >= start_time,
            UserAnswer.created_time <= end_time
        ).scalar() or 0
        
        correct = db.session.query(func.count(UserAnswer.id)).filter(
            UserAnswer.user_id == user_id,
            UserAnswer.is_correct == True,
            UserAnswer.created_time >= start_time,
            UserAnswer.created_time <= end_time
        ).scalar() or 0
        
        return (correct / total * 100) if total > 0 else 0
    
    def _extract_time_metrics(self, metrics: List[Dict]) -> Dict:
        """提取时间相关指标"""
        time_metrics = {}
        for metric in metrics:
            if metric['metric_type'] == MetricType.LEARNING_TIME.value:
                time_metrics[metric['metric_name']] = {
                    'value': metric['metric_value'],
                    'unit': metric['metric_unit']
                }
        return time_metrics
    
    def _extract_accuracy_metrics(self, metrics: List[Dict]) -> Dict:
        """提取准确率相关指标"""
        accuracy_metrics = {}
        for metric in metrics:
            if metric['metric_type'] == MetricType.ACCURACY_RATE.value:
                accuracy_metrics[metric['metric_name']] = {
                    'value': metric['metric_value'],
                    'unit': metric['metric_unit']
                }
        return accuracy_metrics
    
    def _extract_progress_metrics(self, metrics: List[Dict]) -> Dict:
        """提取进度相关指标"""
        progress_metrics = {}
        for metric in metrics:
            if metric['metric_type'] in [MetricType.KNOWLEDGE_MASTERY.value, MetricType.PROGRESS_SCORE.value]:
                progress_metrics[metric['metric_name']] = {
                    'value': metric['metric_value'],
                    'unit': metric['metric_unit']
                }
        return progress_metrics
    
    def _calculate_engagement_metrics(self, user_id: int, period_start: datetime, period_end: datetime) -> Dict:
        """计算参与度指标"""
        # 学习天数
        learning_days = db.session.query(func.count(func.distinct(func.date(LearningSession.start_time)))).filter(
            LearningSession.user_id == user_id,
            LearningSession.start_time >= period_start,
            LearningSession.start_time <= period_end
        ).scalar() or 0
        
        total_days = (period_end - period_start).days + 1
        engagement_rate = (learning_days / total_days * 100) if total_days > 0 else 0
        
        # 平均会话时长
        avg_session_duration = db.session.query(func.avg(LearningSession.duration_minutes)).filter(
            LearningSession.user_id == user_id,
            LearningSession.start_time >= period_start,
            LearningSession.start_time <= period_end
        ).scalar() or 0
        
        return {
            'learning_days': learning_days,
            'total_days': total_days,
            'engagement_rate': engagement_rate,
            'avg_session_duration': avg_session_duration
        }
    
    def _calculate_subject_performance(self, user_id: int, period_start: datetime, period_end: datetime) -> Dict:
        """计算学科表现"""
        subject_performance = {}
        
        subjects = db.session.query(Subject).all()
        for subject in subjects:
            # 该学科的准确率
            accuracy = self._get_subject_accuracy(user_id, subject.id, period_start, period_end)
            
            # 该学科的学习时长
            learning_time = db.session.query(func.sum(LearningSession.duration_minutes)).filter(
                LearningSession.user_id == user_id,
                LearningSession.subject_id == subject.id,
                LearningSession.start_time >= period_start,
                LearningSession.start_time <= period_end
            ).scalar() or 0
            
            # 该学科的题目数量
            question_count = db.session.query(func.count(UserAnswer.id)).join(Question).filter(
                UserAnswer.user_id == user_id,
                Question.subject_id == subject.id,
                UserAnswer.created_time >= period_start,
                UserAnswer.created_time <= period_end
            ).scalar() or 0
            
            subject_performance[subject.name] = {
                'accuracy': accuracy,
                'learning_time': learning_time,
                'question_count': question_count,
                'score': (accuracy + min(100, learning_time/10) + min(100, question_count)) / 3
            }
        
        return subject_performance
    
    def _get_subject_accuracy(self, user_id: int, subject_id: int, period_start: datetime, period_end: datetime) -> float:
        """获取学科准确率"""
        total = db.session.query(func.count(UserAnswer.id)).join(Question).filter(
            UserAnswer.user_id == user_id,
            Question.subject_id == subject_id,
            UserAnswer.created_time >= period_start,
            UserAnswer.created_time <= period_end
        ).scalar() or 0
        
        correct = db.session.query(func.count(UserAnswer.id)).join(Question).filter(
            UserAnswer.user_id == user_id,
            Question.subject_id == subject_id,
            UserAnswer.is_correct == True,
            UserAnswer.created_time >= period_start,
            UserAnswer.created_time <= period_end
        ).scalar() or 0
        
        return (correct / total * 100) if total > 0 else 0
    
    def _predict_next_performance(self, user_id: int, current_score: float, improvement_rate: Optional[float]) -> Tuple[float, float]:
        """预测下期表现"""
        # 简单的线性预测模型
        if improvement_rate is not None:
            predicted_score = current_score * (1 + improvement_rate)
            confidence = 0.7  # 基础置信度
            
            # 根据历史数据调整置信度
            historical_snapshots = db.session.query(PerformanceSnapshot).filter(
                PerformanceSnapshot.user_id == user_id
            ).order_by(PerformanceSnapshot.snapshot_date.desc()).limit(5).all()
            
            if len(historical_snapshots) >= 3:
                # 如果趋势稳定，提高置信度
                recent_improvements = [s.improvement_rate for s in historical_snapshots if s.improvement_rate is not None]
                if recent_improvements:
                    variance = statistics.variance(recent_improvements) if len(recent_improvements) > 1 else 0
                    confidence = max(0.5, min(0.9, 0.7 - variance))
        else:
            predicted_score = current_score
            confidence = 0.5
        
        return min(100, max(0, predicted_score)), confidence
    
    # ==================== 报告生成 ====================
    
    def generate_learning_report(self, user_id: int, tenant_id: int, report_type: str, 
                               period_start: datetime, period_end: datetime) -> Optional[LearningReport]:
        """
        生成学习报告
        
        Args:
            user_id: 用户ID
            tenant_id: 租户ID
            report_type: 报告类型
            period_start: 报告周期开始时间
            period_end: 报告周期结束时间
            
        Returns:
            学习报告对象
        """
        try:
            # 获取用户信息
            user = db.session.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            # 生成报告标题
            report_title = self._generate_report_title(report_type, period_start, period_end)
            
            # 获取性能快照
            snapshot = db.session.query(PerformanceSnapshot).filter(
                PerformanceSnapshot.user_id == user_id,
                PerformanceSnapshot.period_start == period_start,
                PerformanceSnapshot.period_end == period_end
            ).first()
            
            if not snapshot:
                # 如果没有快照，先创建一个
                period_type = self._determine_period_type(period_start, period_end)
                snapshot = self.create_performance_snapshot(user_id, tenant_id, period_type, period_start, period_end)
            
            if not snapshot:
                return None
            
            # 生成报告内容
            summary = self._generate_report_summary(user, snapshot, report_type)
            key_insights = self._generate_key_insights(snapshot)
            performance_data = self._prepare_performance_data(snapshot)
            trend_analysis = self._generate_trend_analysis(user_id, snapshot)
            achievements = self._identify_achievements(snapshot)
            areas_for_improvement = self._identify_improvement_areas(snapshot)
            recommendations = self._generate_recommendations(snapshot)
            charts_data = self._prepare_charts_data(snapshot)
            
            # 创建报告
            report = LearningReport(
                user_id=user_id,
                tenant_id=tenant_id,
                report_type=report_type,
                report_title=report_title,
                report_period=self._determine_period_type(period_start, period_end),
                period_start=period_start,
                period_end=period_end,
                summary=summary,
                key_insights=key_insights,
                performance_data=performance_data,
                trend_analysis=trend_analysis,
                achievements=achievements,
                areas_for_improvement=areas_for_improvement,
                recommendations=recommendations,
                charts_data=charts_data,
                recipients=[{'type': 'student', 'id': user_id, 'name': user.username}]
            )
            
            db.session.add(report)
            db.session.commit()
            
            # 标记为已生成
            report.mark_as_generated()
            db.session.commit()
            
            return report
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"生成学习报告失败: {str(e)}")
            return None
    
    def _generate_report_title(self, report_type: str, period_start: datetime, period_end: datetime) -> str:
        """生成报告标题"""
        period_str = f"{period_start.strftime('%Y年%m月%d日')} 至 {period_end.strftime('%Y年%m月%d日')}"
        
        title_map = {
            ReportType.DAILY_SUMMARY.value: f"每日学习总结 - {period_str}",
            ReportType.WEEKLY_REPORT.value: f"周度学习报告 - {period_str}",
            ReportType.MONTHLY_REPORT.value: f"月度学习报告 - {period_str}",
            ReportType.PROGRESS_REPORT.value: f"学习进度报告 - {period_str}",
            ReportType.PERFORMANCE_ANALYSIS.value: f"学习表现分析 - {period_str}",
            ReportType.IMPROVEMENT_SUGGESTION.value: f"学习改进建议 - {period_str}"
        }
        
        return title_map.get(report_type, f"学习报告 - {period_str}")
    
    def _determine_period_type(self, period_start: datetime, period_end: datetime) -> str:
        """确定周期类型"""
        duration = period_end - period_start
        
        if duration.days <= 1:
            return TrackingPeriod.DAILY.value
        elif duration.days <= 7:
            return TrackingPeriod.WEEKLY.value
        elif duration.days <= 31:
            return TrackingPeriod.MONTHLY.value
        elif duration.days <= 93:
            return TrackingPeriod.QUARTERLY.value
        else:
            return TrackingPeriod.YEARLY.value
    
    def _generate_report_summary(self, user: User, snapshot: PerformanceSnapshot, report_type: str) -> str:
        """生成报告摘要"""
        summary_parts = [
            f"亲爱的{user.username}，",
            f"在本报告周期内，您的综合学习表现得分为{snapshot.overall_score:.1f}分。"
        ]
        
        if snapshot.improvement_rate is not None:
            if snapshot.improvement_rate > 0:
                summary_parts.append(f"相比上一周期，您的表现提升了{snapshot.improvement_rate*100:.1f}%，继续保持！")
            elif snapshot.improvement_rate < 0:
                summary_parts.append(f"相比上一周期，您的表现下降了{abs(snapshot.improvement_rate)*100:.1f}%，需要加油哦！")
            else:
                summary_parts.append("您的表现保持稳定。")
        
        # 添加学习效率评价
        if snapshot.learning_efficiency > 0.8:
            summary_parts.append("您的学习效率很高，能够在较短时间内取得良好效果。")
        elif snapshot.learning_efficiency > 0.6:
            summary_parts.append("您的学习效率中等，还有提升空间。")
        else:
            summary_parts.append("建议优化学习方法，提高学习效率。")
        
        return " ".join(summary_parts)
    
    def _generate_key_insights(self, snapshot: PerformanceSnapshot) -> List[Dict]:
        """生成关键洞察"""
        insights = []
        
        # 最强学科
        if snapshot.subject_performance:
            best_subject = max(snapshot.subject_performance.items(), key=lambda x: x[1]['score'])
            insights.append({
                'type': 'strength',
                'title': '最强学科',
                'content': f"{best_subject[0]}是您的强项，准确率达到{best_subject[1]['accuracy']:.1f}%",
                'score': best_subject[1]['score']
            })
        
        # 需要关注的学科
        if snapshot.subject_performance:
            weak_subject = min(snapshot.subject_performance.items(), key=lambda x: x[1]['score'])
            if weak_subject[1]['score'] < 60:
                insights.append({
                    'type': 'weakness',
                    'title': '需要关注',
                    'content': f"{weak_subject[0]}需要更多练习，当前准确率为{weak_subject[1]['accuracy']:.1f}%",
                    'score': weak_subject[1]['score']
                })
        
        # 学习习惯洞察
        if snapshot.engagement_metrics:
            engagement_rate = snapshot.engagement_metrics.get('engagement_rate', 0)
            if engagement_rate > 80:
                insights.append({
                    'type': 'habit',
                    'title': '学习习惯',
                    'content': f"您的学习习惯很好，{engagement_rate:.1f}%的时间都在学习",
                    'score': engagement_rate
                })
            elif engagement_rate < 50:
                insights.append({
                    'type': 'habit',
                    'title': '学习习惯',
                    'content': f"建议保持更规律的学习习惯，当前学习频率为{engagement_rate:.1f}%",
                    'score': engagement_rate
                })
        
        return insights
    
    def _prepare_performance_data(self, snapshot: PerformanceSnapshot) -> Dict:
        """准备表现数据"""
        return {
            'overall_score': snapshot.overall_score,
            'learning_efficiency': snapshot.learning_efficiency,
            'knowledge_growth': snapshot.knowledge_growth,
            'skill_improvement': snapshot.skill_improvement,
            'time_metrics': snapshot.time_metrics,
            'accuracy_metrics': snapshot.accuracy_metrics,
            'progress_metrics': snapshot.progress_metrics,
            'engagement_metrics': snapshot.engagement_metrics,
            'subject_performance': snapshot.subject_performance
        }
    
    def _generate_trend_analysis(self, user_id: int, current_snapshot: PerformanceSnapshot) -> Dict:
        """生成趋势分析"""
        # 获取历史快照
        historical_snapshots = db.session.query(PerformanceSnapshot).filter(
            PerformanceSnapshot.user_id == user_id,
            PerformanceSnapshot.id != current_snapshot.id
        ).order_by(PerformanceSnapshot.snapshot_date.desc()).limit(5).all()
        
        if not historical_snapshots:
            return {'trend': 'insufficient_data', 'description': '数据不足，无法进行趋势分析'}
        
        # 分析整体趋势
        scores = [current_snapshot.overall_score] + [s.overall_score for s in historical_snapshots]
        scores.reverse()  # 按时间顺序排列
        
        if len(scores) >= 3:
            recent_trend = scores[-1] - scores[-3]
            if recent_trend > 5:
                trend = 'improving'
                description = '您的学习表现呈上升趋势，继续保持！'
            elif recent_trend < -5:
                trend = 'declining'
                description = '最近表现有所下降，建议调整学习策略。'
            else:
                trend = 'stable'
                description = '您的表现保持稳定。'
        else:
            trend = 'stable'
            description = '表现基本稳定。'
        
        return {
            'trend': trend,
            'description': description,
            'historical_scores': scores,
            'improvement_rate': current_snapshot.improvement_rate
        }
    
    def _identify_achievements(self, snapshot: PerformanceSnapshot) -> List[Dict]:
        """识别成就和亮点"""
        achievements = []
        
        # 综合得分成就
        if snapshot.overall_score >= 90:
            achievements.append({
                'type': 'score',
                'title': '学霸表现',
                'description': f'综合得分达到{snapshot.overall_score:.1f}分，表现优异！',
                'icon': '🏆'
            })
        elif snapshot.overall_score >= 80:
            achievements.append({
                'type': 'score',
                'title': '优秀表现',
                'description': f'综合得分{snapshot.overall_score:.1f}分，表现良好！',
                'icon': '⭐'
            })
        
        # 学习效率成就
        if snapshot.learning_efficiency > 0.8:
            achievements.append({
                'type': 'efficiency',
                'title': '高效学习',
                'description': '学习效率很高，能够快速掌握知识点',
                'icon': '⚡'
            })
        
        # 知识增长成就
        if snapshot.knowledge_growth > 0.2:
            achievements.append({
                'type': 'growth',
                'title': '快速进步',
                'description': '知识掌握度显著提升',
                'icon': '📈'
            })
        
        # 学科表现成就
        if snapshot.subject_performance:
            excellent_subjects = [name for name, perf in snapshot.subject_performance.items() if perf['accuracy'] >= 90]
            if excellent_subjects:
                achievements.append({
                    'type': 'subject',
                    'title': '学科专家',
                    'description': f'在{"、".join(excellent_subjects)}方面表现卓越',
                    'icon': '🎯'
                })
        
        # 坚持学习成就
        if snapshot.engagement_metrics and snapshot.engagement_metrics.get('engagement_rate', 0) > 85:
            achievements.append({
                'type': 'persistence',
                'title': '坚持不懈',
                'description': '保持了很好的学习习惯和频率',
                'icon': '💪'
            })
        
        return achievements
    
    def _identify_improvement_areas(self, snapshot: PerformanceSnapshot) -> List[Dict]:
        """识别需要改进的领域"""
        areas = []
        
        # 学科薄弱点
        if snapshot.subject_performance:
            weak_subjects = [(name, perf) for name, perf in snapshot.subject_performance.items() if perf['accuracy'] < 70]
            for subject_name, perf in weak_subjects:
                areas.append({
                    'type': 'subject_weakness',
                    'title': f'{subject_name}需要加强',
                    'description': f'当前准确率{perf["accuracy"]:.1f}%，建议增加练习',
                    'priority': 'high' if perf['accuracy'] < 50 else 'medium',
                    'current_score': perf['accuracy'],
                    'target_score': 80
                })
        
        # 学习效率
        if snapshot.learning_efficiency < 0.5:
            areas.append({
                'type': 'efficiency',
                'title': '学习效率有待提高',
                'description': '建议优化学习方法，提高单位时间的学习效果',
                'priority': 'medium',
                'suggestions': ['制定学习计划', '使用番茄工作法', '减少干扰因素']
            })
        
        # 学习频率
        if snapshot.engagement_metrics and snapshot.engagement_metrics.get('engagement_rate', 0) < 60:
            areas.append({
                'type': 'frequency',
                'title': '学习频率需要提升',
                'description': '建议保持更规律的学习习惯',
                'priority': 'high',
                'current_rate': snapshot.engagement_metrics.get('engagement_rate', 0),
                'target_rate': 80
            })
        
        # 知识巩固
        if snapshot.knowledge_growth < 0.1:
            areas.append({
                'type': 'consolidation',
                'title': '知识巩固不足',
                'description': '建议加强复习，巩固已学知识',
                'priority': 'medium',
                'suggestions': ['定期复习', '使用记忆卡片', '做错题集']
            })
        
        return areas
    
    def _generate_recommendations(self, snapshot: PerformanceSnapshot) -> List[Dict]:
        """生成建议和行动计划"""
        recommendations = []
        
        # 基于综合得分的建议
        if snapshot.overall_score < 60:
            recommendations.append({
                'category': 'overall',
                'priority': 'high',
                'title': '全面提升学习效果',
                'description': '当前综合表现需要全面改进',
                'actions': [
                    '制定详细的学习计划',
                    '每日至少学习2小时',
                    '重点攻克薄弱学科',
                    '寻求老师或同学帮助'
                ],
                'timeline': '2-4周'
            })
        elif snapshot.overall_score < 80:
            recommendations.append({
                'category': 'improvement',
                'priority': 'medium',
                'title': '稳步提升学习水平',
                'description': '在现有基础上进一步提高',
                'actions': [
                    '针对性练习薄弱知识点',
                    '提高答题准确率',
                    '增加学习时间投入',
                    '定期自我测试'
                ],
                'timeline': '1-2周'
            })
        
        # 基于学科表现的建议
        if snapshot.subject_performance:
            weak_subjects = [name for name, perf in snapshot.subject_performance.items() if perf['accuracy'] < 70]
            if weak_subjects:
                recommendations.append({
                    'category': 'subject',
                    'priority': 'high',
                    'title': f'重点提升{"、".join(weak_subjects[:2])}',
                    'description': '这些学科需要额外关注',
                    'actions': [
                        '每日专门练习30分钟',
                        '整理错题和知识点',
                        '寻找相关学习资源',
                        '与老师讨论学习方法'
                    ],
                    'timeline': '持续进行'
                })
        
        # 基于学习习惯的建议
        if snapshot.engagement_metrics and snapshot.engagement_metrics.get('engagement_rate', 0) < 70:
            recommendations.append({
                'category': 'habit',
                'priority': 'medium',
                'title': '建立规律学习习惯',
                'description': '提高学习频率和持续性',
                'actions': [
                    '设定固定学习时间',
                    '使用学习提醒功能',
                    '制定每日学习目标',
                    '记录学习进度'
                ],
                'timeline': '1周内建立'
            })
        
        # 基于学习效率的建议
        if snapshot.learning_efficiency < 0.6:
            recommendations.append({
                'category': 'efficiency',
                'priority': 'medium',
                'title': '优化学习方法',
                'description': '提高学习效率和效果',
                'actions': [
                    '尝试不同的学习技巧',
                    '减少学习时的干扰',
                    '合理安排休息时间',
                    '使用思维导图等工具'
                ],
                'timeline': '逐步调整'
            })
        
        return recommendations
    
    def _prepare_charts_data(self, snapshot: PerformanceSnapshot) -> Dict:
        """准备图表数据"""
        charts_data = {}
        
        # 综合表现雷达图
        charts_data['performance_radar'] = {
            'type': 'radar',
            'title': '综合表现雷达图',
            'data': {
                'labels': ['综合得分', '学习效率', '知识增长', '技能提升'],
                'values': [
                    snapshot.overall_score,
                    snapshot.learning_efficiency * 100,
                    snapshot.knowledge_growth * 100,
                    snapshot.skill_improvement * 100
                ]
            }
        }
        
        # 学科表现柱状图
        if snapshot.subject_performance:
            subjects = list(snapshot.subject_performance.keys())
            accuracies = [snapshot.subject_performance[s]['accuracy'] for s in subjects]
            
            charts_data['subject_performance'] = {
                'type': 'bar',
                'title': '各学科准确率',
                'data': {
                    'labels': subjects,
                    'values': accuracies
                }
            }
        
        # 时间分配饼图
        if snapshot.time_metrics:
            time_data = {}
            for metric_name, metric_info in snapshot.time_metrics.items():
                if '学习时长' in metric_name and metric_name != '总学习时长':
                    subject = metric_name.replace('学习时长', '')
                    time_data[subject] = metric_info['value']
            
            if time_data:
                charts_data['time_allocation'] = {
                    'type': 'pie',
                    'title': '学习时间分配',
                    'data': {
                        'labels': list(time_data.keys()),
                        'values': list(time_data.values())
                    }
                }
        
        return charts_data
    
    # ==================== 目标追踪 ====================
    
    def create_learning_goal(self, user_id: int, tenant_id: int, goal_data: Dict) -> Optional[GoalTracking]:
        """
        创建学习目标
        
        Args:
            user_id: 用户ID
            tenant_id: 租户ID
            goal_data: 目标数据
            
        Returns:
            目标追踪对象
        """
        try:
            goal = GoalTracking(
                user_id=user_id,
                tenant_id=tenant_id,
                goal_title=goal_data['goal_title'],
                goal_description=goal_data.get('goal_description'),
                goal_type=goal_data['goal_type'],
                target_value=goal_data['target_value'],
                unit=goal_data.get('unit'),
                start_date=goal_data['start_date'],
                target_date=goal_data['target_date'],
                subject_id=goal_data.get('subject_id'),
                knowledge_point_id=goal_data.get('knowledge_point_id'),
                milestones=goal_data.get('milestones', [])
            )
            
            db.session.add(goal)
            db.session.commit()
            
            return goal
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建学习目标失败: {str(e)}")
            return None
    
    def update_goal_progress(self, goal_id: int, new_value: float) -> bool:
        """
        更新目标进度
        
        Args:
            goal_id: 目标ID
            new_value: 新的进度值
            
        Returns:
            是否更新成功
        """
        try:
            goal = db.session.query(GoalTracking).filter(GoalTracking.id == goal_id).first()
            if not goal:
                return False
            
            goal.update_progress(new_value)
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"更新目标进度失败: {str(e)}")
            return False
    
    def get_user_goals(self, user_id: int, is_active: Optional[bool] = None) -> List[GoalTracking]:
        """
        获取用户目标列表
        
        Args:
            user_id: 用户ID
            is_active: 是否只获取活跃目标
            
        Returns:
            目标列表
        """
        query = db.session.query(GoalTracking).filter(GoalTracking.user_id == user_id)
        
        if is_active is not None:
            query = query.filter(GoalTracking.is_active == is_active)
        
        return query.order_by(GoalTracking.target_date.asc()).all()
    
    # ==================== 反馈管理 ====================
    
    def create_feedback(self, user_id: int, tenant_id: int, feedback_data: Dict) -> Optional[FeedbackRecord]:
        """
        创建反馈记录
        
        Args:
            user_id: 用户ID
            tenant_id: 租户ID
            feedback_data: 反馈数据
            
        Returns:
            反馈记录对象
        """
        try:
            feedback = FeedbackRecord(
                user_id=user_id,
                tenant_id=tenant_id,
                feedback_type=feedback_data['feedback_type'],
                feedback_category=feedback_data['feedback_category'],
                feedback_title=feedback_data['feedback_title'],
                feedback_content=feedback_data['feedback_content'],
                source_type=feedback_data['source_type'],
                source_id=feedback_data.get('source_id'),
                priority=feedback_data.get('priority', 'medium'),
                importance_score=feedback_data.get('importance_score', 0.5),
                related_subject_id=feedback_data.get('related_subject_id'),
                related_report_id=feedback_data.get('related_report_id')
            )
            
            db.session.add(feedback)
            db.session.commit()
            
            return feedback
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建反馈记录失败: {str(e)}")
            return None
    
    def get_user_feedback(self, user_id: int, is_read: Optional[bool] = None, 
                         priority: Optional[str] = None, limit: int = 50) -> List[FeedbackRecord]:
        """
        获取用户反馈列表
        
        Args:
            user_id: 用户ID
            is_read: 是否已读
            priority: 优先级过滤
            limit: 返回数量限制
            
        Returns:
            反馈记录列表
        """
        query = db.session.query(FeedbackRecord).filter(FeedbackRecord.user_id == user_id)
        
        if is_read is not None:
            query = query.filter(FeedbackRecord.is_read == is_read)
        
        if priority:
            query = query.filter(FeedbackRecord.priority == priority)
        
        return query.order_by(FeedbackRecord.created_time.desc()).limit(limit).all()
    
    def mark_feedback_as_read(self, feedback_id: int) -> bool:
        """
        标记反馈为已读
        
        Args:
            feedback_id: 反馈ID
            
        Returns:
            是否标记成功
        """
        try:
            feedback = db.session.query(FeedbackRecord).filter(FeedbackRecord.id == feedback_id).first()
            if not feedback:
                return False
            
            feedback.mark_as_read()
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"标记反馈已读失败: {str(e)}")
            return False
    
    # ==================== 数据统计 ====================
    
    def get_learning_statistics(self, user_id: int, period_start: datetime, period_end: datetime) -> Dict:
        """
        获取学习统计数据
        
        Args:
            user_id: 用户ID
            period_start: 统计开始时间
            period_end: 统计结束时间
            
        Returns:
            统计数据字典
        """
        try:
            stats = {}
            
            # 基础统计
            stats['basic'] = self._get_basic_statistics(user_id, period_start, period_end)
            
            # 学习时间统计
            stats['time'] = self._get_time_statistics(user_id, period_start, period_end)
            
            # 答题统计
            stats['questions'] = self._get_question_statistics(user_id, period_start, period_end)
            
            # 准确率统计
            stats['accuracy'] = self._get_accuracy_statistics(user_id, period_start, period_end)
            
            # 进度统计
            stats['progress'] = self._get_progress_statistics(user_id, period_start, period_end)
            
            # 目标完成统计
            stats['goals'] = self._get_goal_statistics(user_id, period_start, period_end)
            
            return stats
            
        except Exception as e:
            logger.error(f"获取学习统计失败: {str(e)}")
            return {}
    
    def _get_basic_statistics(self, user_id: int, period_start: datetime, period_end: datetime) -> Dict:
        """获取基础统计"""
        # 学习天数
        learning_days = db.session.query(func.count(func.distinct(func.date(LearningSession.start_time)))).filter(
            LearningSession.user_id == user_id,
            LearningSession.start_time >= period_start,
            LearningSession.start_time <= period_end
        ).scalar() or 0
        
        # 学习会话数
        session_count = db.session.query(func.count(LearningSession.id)).filter(
            LearningSession.user_id == user_id,
            LearningSession.start_time >= period_start,
            LearningSession.start_time <= period_end
        ).scalar() or 0
        
        # 总学习时长
        total_time = db.session.query(func.sum(LearningSession.duration_minutes)).filter(
            LearningSession.user_id == user_id,
            LearningSession.start_time >= period_start,
            LearningSession.start_time <= period_end
        ).scalar() or 0
        
        return {
            'learning_days': learning_days,
            'session_count': session_count,
            'total_time_minutes': total_time,
            'avg_session_time': total_time / session_count if session_count > 0 else 0
        }
    
    def _get_time_statistics(self, user_id: int, period_start: datetime, period_end: datetime) -> Dict:
        """获取时间统计"""
        # 按学科统计时间
        subject_times = db.session.query(
            Subject.name,
            func.sum(LearningSession.duration_minutes)
        ).join(LearningSession).filter(
            LearningSession.user_id == user_id,
            LearningSession.start_time >= period_start,
            LearningSession.start_time <= period_end
        ).group_by(Subject.id).all()
        
        # 按日期统计时间
        daily_times = db.session.query(
            func.date(LearningSession.start_time).label('date'),
            func.sum(LearningSession.duration_minutes).label('total_time')
        ).filter(
            LearningSession.user_id == user_id,
            LearningSession.start_time >= period_start,
            LearningSession.start_time <= period_end
        ).group_by(func.date(LearningSession.start_time)).all()
        
        return {
            'subject_distribution': {name: time for name, time in subject_times},
            'daily_distribution': {str(date): time for date, time in daily_times}
        }
    
    def _get_question_statistics(self, user_id: int, period_start: datetime, period_end: datetime) -> Dict:
        """获取答题统计"""
        # 总答题数
        total_questions = db.session.query(func.count(UserAnswer.id)).filter(
            UserAnswer.user_id == user_id,
            UserAnswer.created_time >= period_start,
            UserAnswer.created_time <= period_end
        ).scalar() or 0
        
        # 按难度统计
        difficulty_stats = db.session.query(
            Question.difficulty_level,
            func.count(UserAnswer.id)
        ).join(UserAnswer).filter(
            UserAnswer.user_id == user_id,
            UserAnswer.created_time >= period_start,
            UserAnswer.created_time <= period_end
        ).group_by(Question.difficulty_level).all()
        
        # 按学科统计
        subject_stats = db.session.query(
            Subject.name,
            func.count(UserAnswer.id)
        ).join(Question).join(UserAnswer).filter(
            UserAnswer.user_id == user_id,
            UserAnswer.created_time >= period_start,
            UserAnswer.created_time <= period_end
        ).group_by(Subject.id).all()
        
        return {
            'total_questions': total_questions,
            'difficulty_distribution': {level: count for level, count in difficulty_stats},
            'subject_distribution': {name: count for name, count in subject_stats}
        }
    
    def _get_accuracy_statistics(self, user_id: int, period_start: datetime, period_end: datetime) -> Dict:
        """获取准确率统计"""
        # 总体准确率
        total_answers = db.session.query(func.count(UserAnswer.id)).filter(
            UserAnswer.user_id == user_id,
            UserAnswer.created_time >= period_start,
            UserAnswer.created_time <= period_end
        ).scalar() or 0
        
        correct_answers = db.session.query(func.count(UserAnswer.id)).filter(
            UserAnswer.user_id == user_id,
            UserAnswer.is_correct == True,
            UserAnswer.created_time >= period_start,
            UserAnswer.created_time <= period_end
        ).scalar() or 0
        
        overall_accuracy = (correct_answers / total_answers * 100) if total_answers > 0 else 0
        
        # 按学科统计准确率
        subject_accuracy = db.session.query(
            Subject.name,
            func.count(UserAnswer.id).label('total'),
            func.sum(func.cast(UserAnswer.is_correct, db.Integer)).label('correct')
        ).join(Question).join(UserAnswer).filter(
            UserAnswer.user_id == user_id,
            UserAnswer.created_time >= period_start,
            UserAnswer.created_time <= period_end
        ).group_by(Subject.id).all()
        
        return {
            'overall_accuracy': overall_accuracy,
            'subject_accuracy': {name: (correct/total*100 if total > 0 else 0) for name, total, correct in subject_accuracy}
        }
    
    def _get_progress_statistics(self, user_id: int, period_start: datetime, period_end: datetime) -> Dict:
        """获取进度统计"""
        # 知识点掌握情况
        progress_records = db.session.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.updated_time >= period_start,
            LearningProgress.updated_time <= period_end
        ).all()
        
        if not progress_records:
            return {'avg_mastery': 0, 'mastery_distribution': {}}
        
        avg_mastery = statistics.mean([p.mastery_level for p in progress_records])
        
        # 掌握度分布
        mastery_ranges = {
            '优秀(90-100%)': 0,
            '良好(80-89%)': 0,
            '一般(70-79%)': 0,
            '待提高(60-69%)': 0,
            '需加强(<60%)': 0
        }
        
        for progress in progress_records:
            mastery_percent = progress.mastery_level * 100
            if mastery_percent >= 90:
                mastery_ranges['优秀(90-100%)'] += 1
            elif mastery_percent >= 80:
                mastery_ranges['良好(80-89%)'] += 1
            elif mastery_percent >= 70:
                mastery_ranges['一般(70-79%)'] += 1
            elif mastery_percent >= 60:
                mastery_ranges['待提高(60-69%)'] += 1
            else:
                mastery_ranges['需加强(<60%)'] += 1
        
        return {
            'avg_mastery': avg_mastery * 100,
            'mastery_distribution': mastery_ranges
        }
    
    def _get_goal_statistics(self, user_id: int, period_start: datetime, period_end: datetime) -> Dict:
        """获取目标统计"""
        # 该时期内的目标
        goals = db.session.query(GoalTracking).filter(
            GoalTracking.user_id == user_id,
            or_(
                and_(GoalTracking.start_date >= period_start, GoalTracking.start_date <= period_end),
                and_(GoalTracking.target_date >= period_start, GoalTracking.target_date <= period_end),
                and_(GoalTracking.start_date <= period_start, GoalTracking.target_date >= period_end)
            )
        ).all()
        
        if not goals:
            return {'total_goals': 0, 'completed_goals': 0, 'completion_rate': 0}
        
        completed_goals = sum(1 for goal in goals if goal.is_completed)
        completion_rate = (completed_goals / len(goals) * 100) if goals else 0
        
        return {
            'total_goals': len(goals),
            'completed_goals': completed_goals,
            'completion_rate': completion_rate,
            'active_goals': sum(1 for goal in goals if goal.is_active and not goal.is_completed)
        }
    
    # ==================== 辅助方法 ====================
    
    def get_user_metrics(self, user_id: int, metric_type: Optional[str] = None, 
                        period_start: Optional[datetime] = None, period_end: Optional[datetime] = None,
                        subject_id: Optional[int] = None, limit: int = 100) -> List[LearningMetric]:
        """
        获取用户指标数据
        
        Args:
            user_id: 用户ID
            metric_type: 指标类型
            period_start: 开始时间
            period_end: 结束时间
            subject_id: 学科ID
            limit: 返回数量限制
            
        Returns:
            指标记录列表
        """
        query = db.session.query(LearningMetric).filter(LearningMetric.user_id == user_id)
        
        if metric_type:
            query = query.filter(LearningMetric.metric_type == metric_type)
        
        if period_start:
            query = query.filter(LearningMetric.recorded_time >= period_start)
        
        if period_end:
            query = query.filter(LearningMetric.recorded_time <= period_end)
        
        if subject_id:
            query = query.filter(LearningMetric.subject_id == subject_id)
        
        return query.order_by(LearningMetric.recorded_time.desc()).limit(limit).all()
    
    def get_user_snapshots(self, user_id: int, snapshot_type: Optional[str] = None,
                          period_start: Optional[datetime] = None, period_end: Optional[datetime] = None,
                          limit: int = 50) -> List[PerformanceSnapshot]:
        """
        获取用户性能快照列表
        
        Args:
            user_id: 用户ID
            snapshot_type: 快照类型
            period_start: 开始时间
            period_end: 结束时间
            limit: 返回数量限制
            
        Returns:
            快照记录列表
        """
        query = db.session.query(PerformanceSnapshot).filter(PerformanceSnapshot.user_id == user_id)
        
        if snapshot_type:
            query = query.filter(PerformanceSnapshot.snapshot_type == snapshot_type)
        
        if period_start:
            query = query.filter(PerformanceSnapshot.period_start >= period_start)
        
        if period_end:
            query = query.filter(PerformanceSnapshot.period_end <= period_end)
        
        return query.order_by(PerformanceSnapshot.created_time.desc()).limit(limit).all()
    
    def get_snapshot_by_id(self, snapshot_id: int, user_id: int) -> Optional[PerformanceSnapshot]:
        """
        根据ID获取快照详情
        
        Args:
            snapshot_id: 快照ID
            user_id: 用户ID
            
        Returns:
            快照对象
        """
        return db.session.query(PerformanceSnapshot).filter(
            PerformanceSnapshot.id == snapshot_id,
            PerformanceSnapshot.user_id == user_id
        ).first()
    
    def get_user_reports(self, user_id: int, report_type: Optional[str] = None,
                        period_start: Optional[datetime] = None, period_end: Optional[datetime] = None,
                        limit: int = 50) -> List[LearningReport]:
        """
        获取用户学习报告列表
        
        Args:
            user_id: 用户ID
            report_type: 报告类型
            period_start: 开始时间
            period_end: 结束时间
            limit: 返回数量限制
            
        Returns:
            报告记录列表
        """
        query = db.session.query(LearningReport).filter(LearningReport.user_id == user_id)
        
        if report_type:
            query = query.filter(LearningReport.report_type == report_type)
        
        if period_start:
            query = query.filter(LearningReport.period_start >= period_start)
        
        if period_end:
            query = query.filter(LearningReport.period_end <= period_end)
        
        return query.order_by(LearningReport.generated_time.desc()).limit(limit).all()
    
    def get_report_by_id(self, report_id: int, user_id: int) -> Optional[LearningReport]:
        """
        根据ID获取报告详情
        
        Args:
            report_id: 报告ID
            user_id: 用户ID
            
        Returns:
            报告对象
        """
        return db.session.query(LearningReport).filter(
            LearningReport.id == report_id,
            LearningReport.user_id == user_id
        ).first()
    
    def update_goal_progress(self, goal_id: int, user_id: int, current_value: float, progress_note: str = '') -> bool:
        """
        更新目标进度（重载方法，增加用户验证）
        
        Args:
            goal_id: 目标ID
            user_id: 用户ID
            current_value: 当前值
            progress_note: 进度备注
            
        Returns:
            是否更新成功
        """
        try:
            goal = db.session.query(GoalTracking).filter(
                GoalTracking.id == goal_id,
                GoalTracking.user_id == user_id
            ).first()
            
            if not goal:
                return False
            
            goal.update_progress(current_value, progress_note)
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"更新目标进度失败: {str(e)}")
            return False