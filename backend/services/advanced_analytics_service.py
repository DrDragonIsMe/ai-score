#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级学习分析服务 - 提供更深入的学习数据分析功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from statistics import mean, median, stdev
import math

from utils.database import db
from utils.logger import logger
from models.learning import StudyRecord
from models.mistake import MistakeRecord
from models.knowledge import KnowledgePoint, Subject, Chapter
from models.user import User

class AdvancedAnalyticsService:
    """
    高级学习分析服务
    
    提供深度学习数据分析功能：
    - 学习效率分析
    - 时间分布分析
    - 难度适应性分析
    - 学习模式识别
    - 预测性分析
    """
    
    def __init__(self):
        """初始化高级分析服务"""
        self.logger = logger
    
    def analyze_learning_efficiency(self, user_id: str, period_days: int = 30) -> Optional[Dict[str, Any]]:
        """
        分析学习效率
        
        Args:
            user_id: 用户ID
            period_days: 分析周期（天数）
            
        Returns:
            学习效率分析结果
        """
        try:
            user_id_str = str(user_id) if not isinstance(user_id, str) else user_id
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
            
            # 获取学习记录
            study_records = db.session.query(StudyRecord).filter(
                StudyRecord.user_id == user_id_str,
                StudyRecord.created_at >= start_date
            ).all()
            
            if not study_records:
                return self._empty_efficiency_result()
            
            # 计算基础效率指标
            total_time = sum(record.duration or 0 for record in study_records)
            total_questions = len(study_records)
            correct_answers = sum(1 for record in study_records if record.is_correct)
            
            # 平均答题时间
            avg_time_per_question = total_time / total_questions if total_questions > 0 else 0
            
            # 效率得分（正确率 × 速度因子）
            accuracy_rate = (correct_answers / total_questions * 100) if total_questions > 0 else 0
            speed_factor = max(0.1, min(2.0, 120 / max(avg_time_per_question, 30)))  # 理想答题时间120秒
            efficiency_score = accuracy_rate * speed_factor
            
            # 按时间段分析效率变化
            daily_efficiency = self._calculate_daily_efficiency(study_records)
            
            # 按知识点分析效率
            knowledge_efficiency = self._calculate_knowledge_efficiency(study_records)
            
            # 按难度分析效率
            difficulty_efficiency = self._calculate_difficulty_efficiency(study_records)
            
            return {
                'overall_efficiency': {
                    'efficiency_score': round(efficiency_score, 2),
                    'accuracy_rate': round(accuracy_rate, 2),
                    'avg_time_per_question': round(avg_time_per_question, 2),
                    'speed_factor': round(speed_factor, 2),
                    'total_study_time': total_time,
                    'total_questions': total_questions
                },
                'daily_efficiency': daily_efficiency,
                'knowledge_efficiency': knowledge_efficiency,
                'difficulty_efficiency': difficulty_efficiency,
                'efficiency_trends': self._analyze_efficiency_trends(daily_efficiency),
                'recommendations': self._generate_efficiency_recommendations(efficiency_score, accuracy_rate, avg_time_per_question)
            }
            
        except Exception as e:
            self.logger.error(f"学习效率分析失败: {str(e)}")
            return None
    
    def analyze_time_distribution(self, user_id: str, period_days: int = 30) -> Optional[Dict[str, Any]]:
        """
        分析时间分布模式
        
        Args:
            user_id: 用户ID
            period_days: 分析周期（天数）
            
        Returns:
            时间分布分析结果
        """
        try:
            user_id_str = str(user_id) if not isinstance(user_id, str) else user_id
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
            
            # 获取学习记录
            study_records = db.session.query(StudyRecord).filter(
                StudyRecord.user_id == user_id_str,
                StudyRecord.created_at >= start_date
            ).all()
            
            if not study_records:
                return self._empty_time_distribution_result()
            
            # 按小时分析
            hourly_distribution = self._calculate_hourly_distribution(study_records)
            
            # 按星期分析
            weekly_distribution = self._calculate_weekly_distribution(study_records)
            
            # 学习会话分析
            session_analysis = self._analyze_study_sessions(study_records)
            
            # 最佳学习时间识别
            optimal_times = self._identify_optimal_study_times(study_records)
            
            return {
                'hourly_distribution': hourly_distribution,
                'weekly_distribution': weekly_distribution,
                'session_analysis': session_analysis,
                'optimal_times': optimal_times,
                'time_patterns': self._identify_time_patterns(hourly_distribution, weekly_distribution),
                'recommendations': self._generate_time_recommendations(optimal_times, session_analysis)
            }
            
        except Exception as e:
            self.logger.error(f"时间分布分析失败: {str(e)}")
            return None
    
    def analyze_difficulty_adaptation(self, user_id: str, period_days: int = 30) -> Optional[Dict[str, Any]]:
        """
        分析难度适应性
        
        Args:
            user_id: 用户ID
            period_days: 分析周期（天数）
            
        Returns:
            难度适应性分析结果
        """
        try:
            user_id_str = str(user_id) if not isinstance(user_id, str) else user_id
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
            
            # 获取学习记录
            study_records = db.session.query(StudyRecord).filter(
                StudyRecord.user_id == user_id_str,
                StudyRecord.created_at >= start_date
            ).all()
            
            if not study_records:
                return self._empty_difficulty_adaptation_result()
            
            # 按难度级别分析表现
            difficulty_performance = self._calculate_difficulty_performance(study_records)
            
            # 难度进步趋势
            difficulty_progress = self._analyze_difficulty_progress(study_records)
            
            # 适应性评分
            adaptation_score = self._calculate_adaptation_score(difficulty_performance)
            
            # 推荐难度
            recommended_difficulty = self._recommend_optimal_difficulty(difficulty_performance)
            
            return {
                'difficulty_performance': difficulty_performance,
                'difficulty_progress': difficulty_progress,
                'adaptation_score': adaptation_score,
                'recommended_difficulty': recommended_difficulty,
                'challenge_readiness': self._assess_challenge_readiness(difficulty_performance),
                'recommendations': self._generate_difficulty_recommendations(adaptation_score, recommended_difficulty)
            }
            
        except Exception as e:
            self.logger.error(f"难度适应性分析失败: {str(e)}")
            return None
    
    def identify_learning_patterns(self, user_id: str, period_days: int = 60) -> Optional[Dict[str, Any]]:
        """
        识别学习模式
        
        Args:
            user_id: 用户ID
            period_days: 分析周期（天数）
            
        Returns:
            学习模式识别结果
        """
        try:
            user_id_str = str(user_id) if not isinstance(user_id, str) else user_id
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
            
            # 获取学习记录
            study_records = db.session.query(StudyRecord).filter(
                StudyRecord.user_id == user_id_str,
                StudyRecord.created_at >= start_date
            ).all()
            
            if not study_records:
                return self._empty_learning_patterns_result()
            
            # 学习频率模式
            frequency_pattern = self._analyze_frequency_pattern(study_records)
            
            # 学习强度模式
            intensity_pattern = self._analyze_intensity_pattern(study_records)
            
            # 学习偏好模式
            preference_pattern = self._analyze_preference_pattern(study_records)
            
            # 学习习惯评估
            habit_assessment = self._assess_learning_habits(study_records)
            
            return {
                'frequency_pattern': frequency_pattern,
                'intensity_pattern': intensity_pattern,
                'preference_pattern': preference_pattern,
                'habit_assessment': habit_assessment,
                'learning_style': self._identify_learning_style(frequency_pattern, intensity_pattern, preference_pattern),
                'recommendations': self._generate_pattern_recommendations(habit_assessment)
            }
            
        except Exception as e:
            self.logger.error(f"学习模式识别失败: {str(e)}")
            return None
    
    def predict_performance(self, user_id: str, prediction_days: int = 7) -> Optional[Dict[str, Any]]:
        """
        预测学习表现
        
        Args:
            user_id: 用户ID
            prediction_days: 预测天数
            
        Returns:
            学习表现预测结果
        """
        try:
            user_id_str = str(user_id) if not isinstance(user_id, str) else user_id
            
            # 获取历史数据（过去30天）
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            study_records = db.session.query(StudyRecord).filter(
                StudyRecord.user_id == user_id_str,
                StudyRecord.created_at >= start_date
            ).all()
            
            if len(study_records) < 10:  # 数据不足
                return self._empty_prediction_result()
            
            # 趋势分析
            performance_trend = self._analyze_performance_trend(study_records)
            
            # 预测准确率
            predicted_accuracy = self._predict_accuracy(study_records, prediction_days)
            
            # 预测学习时间
            predicted_study_time = self._predict_study_time(study_records, prediction_days)
            
            # 预测学习效率
            predicted_efficiency = self._predict_efficiency(study_records, prediction_days)
            
            # 风险评估
            risk_assessment = self._assess_learning_risks(study_records)
            
            return {
                'performance_trend': performance_trend,
                'predictions': {
                    'accuracy': predicted_accuracy,
                    'study_time': predicted_study_time,
                    'efficiency': predicted_efficiency
                },
                'risk_assessment': risk_assessment,
                'confidence_level': self._calculate_prediction_confidence(study_records),
                'recommendations': self._generate_prediction_recommendations(risk_assessment, performance_trend)
            }
            
        except Exception as e:
            self.logger.error(f"学习表现预测失败: {str(e)}")
            return None
    
    # 辅助方法
    def _empty_efficiency_result(self) -> Dict[str, Any]:
        """返回空的效率分析结果"""
        return {
            'overall_efficiency': {
                'efficiency_score': 0,
                'accuracy_rate': 0,
                'avg_time_per_question': 0,
                'speed_factor': 0,
                'total_study_time': 0,
                'total_questions': 0
            },
            'daily_efficiency': [],
            'knowledge_efficiency': [],
            'difficulty_efficiency': [],
            'efficiency_trends': {'trend': 'stable', 'change_rate': 0},
            'recommendations': []
        }
    
    def _empty_time_distribution_result(self) -> Dict[str, Any]:
        """返回空的时间分布结果"""
        return {
            'hourly_distribution': [],
            'weekly_distribution': [],
            'session_analysis': {'avg_session_length': 0, 'total_sessions': 0},
            'optimal_times': [],
            'time_patterns': [],
            'recommendations': []
        }
    
    def _empty_difficulty_adaptation_result(self) -> Dict[str, Any]:
        """返回空的难度适应性结果"""
        return {
            'difficulty_performance': [],
            'difficulty_progress': {'trend': 'stable', 'progress_rate': 0},
            'adaptation_score': 0,
            'recommended_difficulty': 1,
            'challenge_readiness': 'low',
            'recommendations': []
        }
    
    def _empty_learning_patterns_result(self) -> Dict[str, Any]:
        """返回空的学习模式结果"""
        return {
            'frequency_pattern': {'type': 'irregular', 'consistency': 0},
            'intensity_pattern': {'type': 'low', 'average_intensity': 0},
            'preference_pattern': {'preferred_subjects': [], 'preferred_times': []},
            'habit_assessment': {'score': 0, 'strengths': [], 'areas_for_improvement': []},
            'learning_style': 'undefined',
            'recommendations': []
        }
    
    def _empty_prediction_result(self) -> Dict[str, Any]:
        """返回空的预测结果"""
        return {
            'performance_trend': {'trend': 'stable', 'confidence': 0},
            'predictions': {
                'accuracy': {'value': 0, 'confidence': 0},
                'study_time': {'value': 0, 'confidence': 0},
                'efficiency': {'value': 0, 'confidence': 0}
            },
            'risk_assessment': {'risk_level': 'low', 'risk_factors': []},
            'confidence_level': 0,
            'recommendations': []
        }
    
    def _calculate_daily_efficiency(self, study_records: List[StudyRecord]) -> List[Dict[str, Any]]:
        """计算每日效率"""
        daily_data = defaultdict(lambda: {'total_time': 0, 'total_questions': 0, 'correct_answers': 0})
        
        for record in study_records:
            if record.created_at:
                date_key = record.created_at.date().isoformat()
                daily_data[date_key]['total_time'] += record.duration or 0
                daily_data[date_key]['total_questions'] += 1
                if record.is_correct:
                    daily_data[date_key]['correct_answers'] += 1
        
        result = []
        for date, data in sorted(daily_data.items()):
            accuracy = (data['correct_answers'] / data['total_questions'] * 100) if data['total_questions'] > 0 else 0
            avg_time = data['total_time'] / data['total_questions'] if data['total_questions'] > 0 else 0
            efficiency = accuracy * max(0.1, min(2.0, 120 / max(avg_time, 30)))
            
            result.append({
                'date': date,
                'efficiency_score': round(efficiency, 2),
                'accuracy': round(accuracy, 2),
                'avg_time_per_question': round(avg_time, 2),
                'total_questions': data['total_questions']
            })
        
        return result
    
    def _calculate_knowledge_efficiency(self, study_records: List[StudyRecord]) -> List[Dict[str, Any]]:
        """计算知识点效率"""
        knowledge_data = defaultdict(lambda: {'total_time': 0, 'total_questions': 0, 'correct_answers': 0})
        
        for record in study_records:
            if record.knowledge_point_id:
                kp_id = record.knowledge_point_id
                knowledge_data[kp_id]['total_time'] += record.duration or 0
                knowledge_data[kp_id]['total_questions'] += 1
                if record.is_correct:
                    knowledge_data[kp_id]['correct_answers'] += 1
        
        result = []
        for kp_id, data in knowledge_data.items():
            # 获取知识点名称
            kp = db.session.query(KnowledgePoint).filter_by(id=kp_id).first()
            kp_name = kp.name if kp else f"知识点{kp_id}"
            
            accuracy = (data['correct_answers'] / data['total_questions'] * 100) if data['total_questions'] > 0 else 0
            avg_time = data['total_time'] / data['total_questions'] if data['total_questions'] > 0 else 0
            efficiency = accuracy * max(0.1, min(2.0, 120 / max(avg_time, 30)))
            
            result.append({
                'knowledge_point_id': kp_id,
                'knowledge_point_name': kp_name,
                'efficiency_score': round(efficiency, 2),
                'accuracy': round(accuracy, 2),
                'avg_time_per_question': round(avg_time, 2),
                'total_questions': data['total_questions']
            })
        
        return sorted(result, key=lambda x: x['efficiency_score'], reverse=True)
    
    def _calculate_difficulty_efficiency(self, study_records: List[StudyRecord]) -> List[Dict[str, Any]]:
        """计算难度效率"""
        difficulty_data = defaultdict(lambda: {'total_time': 0, 'total_questions': 0, 'correct_answers': 0})
        
        for record in study_records:
            # 使用掌握程度作为难度指标
            difficulty = getattr(record, 'mastery_level', 1) or 1
            difficulty_data[difficulty]['total_time'] += record.duration or 0
            difficulty_data[difficulty]['total_questions'] += 1
            if record.is_correct:
                difficulty_data[difficulty]['correct_answers'] += 1
        
        result = []
        for difficulty, data in sorted(difficulty_data.items()):
            accuracy = (data['correct_answers'] / data['total_questions'] * 100) if data['total_questions'] > 0 else 0
            avg_time = data['total_time'] / data['total_questions'] if data['total_questions'] > 0 else 0
            efficiency = accuracy * max(0.1, min(2.0, 120 / max(avg_time, 30)))
            
            result.append({
                'difficulty_level': difficulty,
                'efficiency_score': round(efficiency, 2),
                'accuracy': round(accuracy, 2),
                'avg_time_per_question': round(avg_time, 2),
                'total_questions': data['total_questions']
            })
        
        return result
    
    def _analyze_efficiency_trends(self, daily_efficiency: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析效率趋势"""
        if len(daily_efficiency) < 3:
            return {'trend': 'stable', 'change_rate': 0}
        
        scores = [day['efficiency_score'] for day in daily_efficiency]
        
        # 简单线性趋势分析
        n = len(scores)
        x_mean = (n - 1) / 2
        y_mean = sum(scores) / n
        
        numerator = sum((i - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # 判断趋势
        if slope > 0.5:
            trend = 'improving'
        elif slope < -0.5:
            trend = 'declining'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'change_rate': round(slope, 3),
            'recent_average': round(mean(scores[-7:]) if len(scores) >= 7 else mean(scores), 2)
        }
    
    def _generate_efficiency_recommendations(self, efficiency_score: float, accuracy_rate: float, avg_time: float) -> List[Dict[str, Any]]:
        """生成效率建议"""
        recommendations = []
        
        if efficiency_score < 50:
            recommendations.append({
                'type': 'efficiency_improvement',
                'priority': 'high',
                'title': '提升学习效率',
                'description': '当前学习效率较低，建议优化学习方法和时间管理',
                'actions': ['制定学习计划', '减少干扰因素', '采用番茄工作法']
            })
        
        if accuracy_rate < 60:
            recommendations.append({
                'type': 'accuracy_improvement',
                'priority': 'high',
                'title': '提高答题准确率',
                'description': '正确率偏低，需要加强基础知识学习',
                'actions': ['复习基础概念', '多做练习题', '寻求帮助']
            })
        
        if avg_time > 180:  # 超过3分钟
            recommendations.append({
                'type': 'speed_improvement',
                'priority': 'medium',
                'title': '提升答题速度',
                'description': '答题速度较慢，建议提高熟练度',
                'actions': ['增加练习量', '掌握解题技巧', '限时练习']
            })
        
        return recommendations
    
    # 其他辅助方法的实现...
    def _calculate_hourly_distribution(self, study_records: List[StudyRecord]) -> List[Dict[str, Any]]:
        """计算小时分布"""
        hourly_data = defaultdict(lambda: {'study_time': 0, 'question_count': 0, 'accuracy': 0})
        
        for record in study_records:
            if record.created_at:
                hour = record.created_at.hour
                hourly_data[hour]['study_time'] += record.duration or 0
                hourly_data[hour]['question_count'] += 1
                if record.is_correct:
                    hourly_data[hour]['accuracy'] += 1
        
        result = []
        for hour in range(24):
            data = hourly_data[hour]
            accuracy_rate = (data['accuracy'] / data['question_count'] * 100) if data['question_count'] > 0 else 0
            
            result.append({
                'hour': hour,
                'study_time': data['study_time'],
                'question_count': data['question_count'],
                'accuracy_rate': round(accuracy_rate, 2)
            })
        
        return result
    
    def _calculate_weekly_distribution(self, study_records: List[StudyRecord]) -> List[Dict[str, Any]]:
        """计算星期分布"""
        weekly_data = defaultdict(lambda: {'study_time': 0, 'question_count': 0, 'accuracy': 0})
        
        for record in study_records:
            if record.created_at:
                weekday = record.created_at.weekday()  # 0=Monday, 6=Sunday
                weekly_data[weekday]['study_time'] += record.duration or 0
                weekly_data[weekday]['question_count'] += 1
                if record.is_correct:
                    weekly_data[weekday]['accuracy'] += 1
        
        weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        result = []
        
        for weekday in range(7):
            data = weekly_data[weekday]
            accuracy_rate = (data['accuracy'] / data['question_count'] * 100) if data['question_count'] > 0 else 0
            
            result.append({
                'weekday': weekday,
                'weekday_name': weekday_names[weekday],
                'study_time': data['study_time'],
                'question_count': data['question_count'],
                'accuracy_rate': round(accuracy_rate, 2)
            })
        
        return result
    
    def _analyze_study_sessions(self, study_records: List[StudyRecord]) -> Dict[str, Any]:
        """分析学习会话"""
        if not study_records:
            return {'avg_session_length': 0, 'total_sessions': 0, 'session_distribution': []}
        
        # 按时间排序
        sorted_records = sorted(study_records, key=lambda x: x.created_at or datetime.min)
        
        sessions = []
        current_session = [sorted_records[0]]
        
        # 将记录分组为会话（间隔超过30分钟算新会话）
        for i in range(1, len(sorted_records)):
            prev_time = sorted_records[i-1].created_at or datetime.min
            curr_time = sorted_records[i].created_at or datetime.min
            
            if (curr_time - prev_time).total_seconds() > 1800:  # 30分钟
                sessions.append(current_session)
                current_session = [sorted_records[i]]
            else:
                current_session.append(sorted_records[i])
        
        sessions.append(current_session)
        
        # 计算会话统计
        session_lengths = []
        session_questions = []
        
        for session in sessions:
            session_time = sum(record.duration or 0 for record in session)
            session_lengths.append(session_time)
            session_questions.append(len(session))
        
        return {
            'avg_session_length': round(mean(session_lengths), 2) if session_lengths else 0,
            'total_sessions': len(sessions),
            'avg_questions_per_session': round(mean(session_questions), 2) if session_questions else 0,
            'session_distribution': [
                {'length_range': '0-30分钟', 'count': sum(1 for length in session_lengths if length <= 1800)},
                {'length_range': '30-60分钟', 'count': sum(1 for length in session_lengths if 1800 < length <= 3600)},
                {'length_range': '60-120分钟', 'count': sum(1 for length in session_lengths if 3600 < length <= 7200)},
                {'length_range': '120分钟以上', 'count': sum(1 for length in session_lengths if length > 7200)}
            ]
        }
    
    def _identify_optimal_study_times(self, study_records: List[StudyRecord]) -> List[Dict[str, Any]]:
        """识别最佳学习时间"""
        hourly_performance = defaultdict(lambda: {'total_questions': 0, 'correct_answers': 0, 'total_time': 0})
        
        for record in study_records:
            if record.created_at:
                hour = record.created_at.hour
                hourly_performance[hour]['total_questions'] += 1
                hourly_performance[hour]['total_time'] += record.duration or 0
                if record.is_correct:
                    hourly_performance[hour]['correct_answers'] += 1
        
        # 计算每小时的综合表现分数
        hour_scores = []
        for hour, data in hourly_performance.items():
            if data['total_questions'] >= 3:  # 至少3道题才有统计意义
                accuracy = data['correct_answers'] / data['total_questions']
                avg_time = data['total_time'] / data['total_questions']
                efficiency = accuracy * max(0.1, min(2.0, 120 / max(avg_time, 30)))
                
                hour_scores.append({
                    'hour': hour,
                    'performance_score': efficiency,
                    'accuracy': accuracy * 100,
                    'avg_time': avg_time,
                    'question_count': data['total_questions']
                })
        
        # 按表现分数排序，返回前3个最佳时间
        optimal_times = sorted(hour_scores, key=lambda x: x['performance_score'], reverse=True)[:3]
        
        return optimal_times
    
    def _identify_time_patterns(self, hourly_dist: List[Dict], weekly_dist: List[Dict]) -> List[Dict[str, Any]]:
        """识别时间模式"""
        patterns = []
        
        # 分析活跃时段
        active_hours = [h for h in hourly_dist if h['question_count'] > 0]
        if active_hours:
            peak_hour = max(active_hours, key=lambda x: x['question_count'])
            patterns.append({
                'type': 'peak_activity',
                'description': f"最活跃时段：{peak_hour['hour']}:00",
                'details': f"该时段完成了{peak_hour['question_count']}道题目"
            })
        
        # 分析学习习惯
        morning_activity = sum(h['question_count'] for h in hourly_dist if 6 <= h['hour'] < 12)
        afternoon_activity = sum(h['question_count'] for h in hourly_dist if 12 <= h['hour'] < 18)
        evening_activity = sum(h['question_count'] for h in hourly_dist if 18 <= h['hour'] < 24)
        
        max_activity = max(morning_activity, afternoon_activity, evening_activity)
        if max_activity > 0:
            if morning_activity == max_activity:
                habit_type = "晨型学习者"
            elif afternoon_activity == max_activity:
                habit_type = "午后学习者"
            else:
                habit_type = "夜型学习者"
            
            patterns.append({
                'type': 'learning_habit',
                'description': f"学习习惯：{habit_type}",
                'details': f"主要在相应时段进行学习活动"
            })
        
        return patterns
    
    def _generate_time_recommendations(self, optimal_times: List[Dict], session_analysis: Dict) -> List[Dict[str, Any]]:
        """生成时间建议"""
        recommendations = []
        
        if optimal_times:
            best_time = optimal_times[0]
            recommendations.append({
                'type': 'optimal_timing',
                'priority': 'high',
                'title': '优化学习时间',
                'description': f"建议在{best_time['hour']}:00左右学习，此时表现最佳",
                'actions': [f"安排重要学习任务在{best_time['hour']}:00", '保持规律的学习时间']
            })
        
        avg_session = session_analysis.get('avg_session_length', 0)
        if avg_session > 7200:  # 超过2小时
            recommendations.append({
                'type': 'session_length',
                'priority': 'medium',
                'title': '调整学习时长',
                'description': '学习会话时间过长，建议适当休息',
                'actions': ['每60-90分钟休息一次', '使用番茄工作法', '保持注意力集中']
            })
        elif avg_session < 1800:  # 少于30分钟
            recommendations.append({
                'type': 'session_length',
                'priority': 'medium',
                'title': '延长学习时间',
                'description': '学习会话时间较短，建议延长以提高效果',
                'actions': ['设定最少45分钟学习时间', '减少学习中断', '创造专注环境']
            })
        
        return recommendations
    
    # 更多辅助方法的占位符...
    def _calculate_difficulty_performance(self, study_records: List[StudyRecord]) -> List[Dict[str, Any]]:
        """计算难度表现（占位符）"""
        return []
    
    def _analyze_difficulty_progress(self, study_records: List[StudyRecord]) -> Dict[str, Any]:
        """分析难度进步（占位符）"""
        return {'trend': 'stable', 'progress_rate': 0}
    
    def _calculate_adaptation_score(self, difficulty_performance: List[Dict]) -> float:
        """计算适应性评分（占位符）"""
        return 0.0
    
    def _recommend_optimal_difficulty(self, difficulty_performance: List[Dict]) -> int:
        """推荐最佳难度（占位符）"""
        return 2
    
    def _assess_challenge_readiness(self, difficulty_performance: List[Dict]) -> str:
        """评估挑战准备度（占位符）"""
        return 'medium'
    
    def _generate_difficulty_recommendations(self, adaptation_score: float, recommended_difficulty: int) -> List[Dict[str, Any]]:
        """生成难度建议（占位符）"""
        return []
    
    def _analyze_frequency_pattern(self, study_records: List[StudyRecord]) -> Dict[str, Any]:
        """分析频率模式（占位符）"""
        return {'type': 'regular', 'consistency': 0.8}
    
    def _analyze_intensity_pattern(self, study_records: List[StudyRecord]) -> Dict[str, Any]:
        """分析强度模式（占位符）"""
        return {'type': 'moderate', 'average_intensity': 0.6}
    
    def _analyze_preference_pattern(self, study_records: List[StudyRecord]) -> Dict[str, Any]:
        """分析偏好模式（占位符）"""
        return {'preferred_subjects': [], 'preferred_times': []}
    
    def _assess_learning_habits(self, study_records: List[StudyRecord]) -> Dict[str, Any]:
        """评估学习习惯（占位符）"""
        return {'score': 75, 'strengths': ['规律性好'], 'areas_for_improvement': ['需要提高专注度']}
    
    def _identify_learning_style(self, frequency: Dict, intensity: Dict, preference: Dict) -> str:
        """识别学习风格（占位符）"""
        return 'balanced_learner'
    
    def _generate_pattern_recommendations(self, habit_assessment: Dict) -> List[Dict[str, Any]]:
        """生成模式建议（占位符）"""
        return []
    
    def _analyze_performance_trend(self, study_records: List[StudyRecord]) -> Dict[str, Any]:
        """分析表现趋势（占位符）"""
        return {'trend': 'improving', 'confidence': 0.8}
    
    def _predict_accuracy(self, study_records: List[StudyRecord], days: int) -> Dict[str, Any]:
        """预测准确率（占位符）"""
        return {'value': 75.0, 'confidence': 0.7}
    
    def _predict_study_time(self, study_records: List[StudyRecord], days: int) -> Dict[str, Any]:
        """预测学习时间（占位符）"""
        return {'value': 120, 'confidence': 0.8}
    
    def _predict_efficiency(self, study_records: List[StudyRecord], days: int) -> Dict[str, Any]:
        """预测学习效率（占位符）"""
        return {'value': 85.0, 'confidence': 0.75}
    
    def _assess_learning_risks(self, study_records: List[StudyRecord]) -> Dict[str, Any]:
        """评估学习风险（占位符）"""
        return {'risk_level': 'low', 'risk_factors': []}
    
    def _calculate_prediction_confidence(self, study_records: List[StudyRecord]) -> float:
        """计算预测置信度（占位符）"""
        return 0.8
    
    def _generate_prediction_recommendations(self, risk_assessment: Dict, performance_trend: Dict) -> List[Dict[str, Any]]:
        """生成预测建议（占位符）"""
        return []