#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 服务 - learning_analytics_service.py

Description:
    学习分析服务，提供学习进度、知识点掌握、成绩趋势等分析功能。

Author: Chang Xinglong
Date: 2025-01-21
Version: 1.0.0
License: Apache License 2.0
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from statistics import mean, median
import json

from utils.database import db
from utils.logger import logger
from models.tracking import LearningMetric, PerformanceSnapshot, LearningReport
from models.exam import ExamSession
from models.learning import StudyRecord
from models.mistake import MistakeRecord
from models.knowledge import KnowledgePoint, Subject
from models.user import User

class LearningAnalyticsService:
    """
    学习分析服务
    
    提供全面的学习数据分析功能，包括：
    - 学习进度分析
    - 知识点掌握情况分析
    - 学习效果和成绩趋势分析
    - 综合学习报告生成
    """
    
    def __init__(self):
        """初始化学习分析服务"""
        self.logger = logger
    
    def analyze_learning_progress(self, user_id: str, period_days: int = 30) -> Optional[Dict[str, Any]]:
        """
        分析学习进度
        
        Args:
            user_id: 用户ID
            period_days: 分析周期（天数）
            
        Returns:
            学习进度分析结果
        """
        try:
            # 确保user_id是字符串
            user_id_str = str(user_id) if not isinstance(user_id, str) else user_id
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
            
            # 获取学习记录
            study_records = db.session.query(StudyRecord).filter(
                StudyRecord.user_id == user_id_str,
                StudyRecord.created_at >= start_date
            ).all()
            
            if not study_records:
                return {
                    'overall_progress': {
                        'total_study_time': 0,
                        'total_questions': 0,
                        'average_accuracy': 0,
                        'study_days': 0,
                        'daily_average_time': 0
                    },
                    'subject_progress': [],
                    'time_distribution': {},
                    'efficiency_trend': [],
                    'period': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'days': period_days
                    }
                }
            
            # 计算总体进度
            total_study_time = sum(record.duration or 0 for record in study_records)
            total_questions = len(study_records)
            correct_answers = sum(1 for record in study_records if record.is_correct)
            average_accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
            
            # 计算学习天数
            study_dates = set(record.created_at.date() for record in study_records if record.created_at)
            study_days = len(study_dates)
            daily_average_time = (total_study_time / study_days) if study_days > 0 else 0
            
            # 按学科统计
            subject_stats = {}
            
            for record in study_records:
                 if hasattr(record, 'knowledge_point') and record.knowledge_point:
                     kp = record.knowledge_point
                     if hasattr(kp, 'subject_id') and kp.subject_id:
                         subject_id = str(kp.subject_id)
                         if subject_id not in subject_stats:
                             subject_stats[subject_id] = {
                                 'study_time': 0,
                                 'questions': 0,
                                 'correct': 0,
                                 'subject_name': '未知学科'
                             }
                         
                         subject_stats[subject_id]['study_time'] += int(record.duration or 0)
                         subject_stats[subject_id]['questions'] += 1
                         if record.is_correct:
                             subject_stats[subject_id]['correct'] += 1
                         
                         # 获取学科名称
                         if hasattr(kp, 'subject') and kp.subject:
                             subject_stats[subject_id]['subject_name'] = str(kp.subject.name)
            
            # 转换为列表格式
            subject_progress = []
            for subject_id, stats in subject_stats.items():
                questions_count = int(stats['questions'])
                correct_count = int(stats['correct'])
                accuracy_rate = (correct_count / questions_count * 100) if questions_count > 0 else 0
                subject_progress.append({
                    'subject_id': subject_id,
                    'subject_name': stats['subject_name'],
                    'study_time': int(stats['study_time']),
                    'questions_count': questions_count,
                    'correct_count': correct_count,
                    'accuracy_rate': accuracy_rate
                })
            
            # 时间分布（按小时）
            time_distribution = defaultdict(int)
            for record in study_records:
                if record.created_at:
                    hour = record.created_at.hour
                    time_distribution[f"{hour:02d}:00"] += record.duration or 0
            
            # 效率趋势（按天）
            daily_efficiency = defaultdict(lambda: {'time': 0, 'questions': 0, 'correct': 0})
            for record in study_records:
                if record.created_at:
                    date_str = record.created_at.date().isoformat()
                    daily_efficiency[date_str]['time'] += record.duration or 0
                    daily_efficiency[date_str]['questions'] += 1
                    if record.is_correct:
                        daily_efficiency[date_str]['correct'] += 1
            
            efficiency_trend = []
            for date_str in sorted(daily_efficiency.keys()):
                stats = daily_efficiency[date_str]
                accuracy = (stats['correct'] / stats['questions'] * 100) if stats['questions'] > 0 else 0
                efficiency = accuracy * (stats['questions'] / max(stats['time'], 1))  # 简单效率计算
                efficiency_trend.append({
                    'date': date_str,
                    'study_time': stats['time'],
                    'questions': stats['questions'],
                    'accuracy': accuracy,
                    'efficiency': efficiency
                })
            
            return {
                'overall_progress': {
                    'total_study_time': total_study_time,
                    'total_questions': total_questions,
                    'average_accuracy': average_accuracy,
                    'study_days': study_days,
                    'daily_average_time': daily_average_time
                },
                'subject_progress': subject_progress,
                'time_distribution': dict(time_distribution),
                'efficiency_trend': efficiency_trend,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': period_days
                }
            }
            
        except Exception as e:
            self.logger.error(f"分析学习进度失败: {str(e)}")
            return None
    
    def analyze_knowledge_mastery(self, user_id: str, subject_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        分析知识点掌握情况
        
        Args:
            user_id: 用户ID
            subject_id: 学科ID（可选）
            
        Returns:
            知识点掌握情况分析结果
        """
        try:
            # 确保user_id是字符串
            user_id_str = str(user_id) if not isinstance(user_id, str) else user_id
            
            # 构建查询条件
            query = db.session.query(StudyRecord).filter(StudyRecord.user_id == user_id_str)
            
            if subject_id:
                # 通过知识点关联查询特定学科
                query = query.join(KnowledgePoint).filter(KnowledgePoint.subject_id == subject_id)
            
            study_records = query.all()
            
            if not study_records:
                return {
                    'overall_statistics': {
                        'total_knowledge_points': 0,
                        'mastered_count': 0,
                        'mastery_rate': 0,
                        'struggling_count': 0
                    },
                    'knowledge_points': [],
                    'weak_points': [],
                    'strong_points': [],
                    'recommendations': []
                }
            
            # 按知识点统计
            kp_stats = {}
            
            for record in study_records:
                kp_id = record.knowledge_point_id
                if kp_id:
                    kp_id_str = str(kp_id)
                    if kp_id_str not in kp_stats:
                        kp_stats[kp_id_str] = {
                            'total_attempts': 0,
                            'correct_attempts': 0,
                            'total_time': 0,
                            'recent_performance': [],
                            'knowledge_point_name': '未知知识点'
                        }
                    
                    kp_stats[kp_id_str]['total_attempts'] += 1
                    if record.is_correct:
                        kp_stats[kp_id_str]['correct_attempts'] += 1
                    kp_stats[kp_id_str]['total_time'] += int(record.duration or 0)
                    
                    # 记录最近表现
                    kp_stats[kp_id_str]['recent_performance'].append({
                        'is_correct': bool(record.is_correct),
                        'date': record.created_at.isoformat() if record.created_at else None
                    })
                    
                    # 获取知识点名称
                    if hasattr(record, 'knowledge_point') and record.knowledge_point:
                        kp_stats[kp_id_str]['knowledge_point_name'] = str(record.knowledge_point.name)
            
            # 分析每个知识点的掌握情况
            knowledge_points = []
            weak_points = []
            strong_points = []
            
            for kp_id, stats in kp_stats.items():
                total_attempts = int(stats['total_attempts'])
                correct_attempts = int(stats['correct_attempts'])
                total_time = int(stats['total_time'])
                accuracy_rate = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
                avg_time = (total_time / total_attempts) if total_attempts > 0 else 0
                
                # 判断掌握程度
                if accuracy_rate >= 80:
                    mastery_level = 'mastered'
                elif accuracy_rate >= 60:
                    mastery_level = 'learning'
                else:
                    mastery_level = 'struggling'
                
                recent_performance = stats['recent_performance']
                if isinstance(recent_performance, list):
                    recent_trend = self._analyze_recent_trend(recent_performance)
                else:
                    recent_trend = 'insufficient_data'
                
                kp_analysis = {
                    'knowledge_point_id': kp_id,
                    'knowledge_point_name': str(stats['knowledge_point_name']),
                    'total_attempts': total_attempts,
                    'correct_attempts': correct_attempts,
                    'accuracy_rate': accuracy_rate,
                    'average_time': avg_time,
                    'mastery_level': mastery_level,
                    'recent_trend': recent_trend
                }
                
                knowledge_points.append(kp_analysis)
                
                # 分类薄弱和强势知识点
                if mastery_level == 'struggling':
                    weak_points.append(kp_analysis)
                elif mastery_level == 'mastered':
                    strong_points.append(kp_analysis)
            
            # 排序
            weak_points.sort(key=lambda x: x['accuracy_rate'])
            strong_points.sort(key=lambda x: x['accuracy_rate'], reverse=True)
            
            # 生成学习建议
            recommendations = self._generate_learning_recommendations(weak_points, strong_points)
            
            # 计算总体统计
            total_kps = len(knowledge_points)
            mastered_count = len([kp for kp in knowledge_points if kp['mastery_level'] == 'mastered'])
            struggling_count = len(weak_points)
            mastery_rate = (mastered_count / total_kps * 100) if total_kps > 0 else 0
            
            return {
                'overall_statistics': {
                    'total_knowledge_points': total_kps,
                    'mastered_count': mastered_count,
                    'mastery_rate': mastery_rate,
                    'struggling_count': struggling_count
                },
                'knowledge_points': knowledge_points,
                'weak_points': weak_points,
                'strong_points': strong_points,
                'recommendations': recommendations
            }
            
        except Exception as e:
            self.logger.error(f"分析知识点掌握情况失败: {str(e)}")
            return None
    
    def analyze_performance_trends(self, user_id: str, period_days: int = 90) -> Optional[Dict[str, Any]]:
        """
        分析学习效果和成绩趋势
        
        Args:
            user_id: 用户ID
            period_days: 分析周期（天数）
            
        Returns:
            学习效果和成绩趋势分析结果
        """
        try:
            # 确保user_id是字符串
            user_id_str = str(user_id) if not isinstance(user_id, str) else user_id
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
            
            # 获取考试记录
            exam_sessions = db.session.query(ExamSession).filter(
                ExamSession.user_id == user_id_str
            ).filter(
                ExamSession.created_time >= start_date
            ).filter(
                ExamSession.status == 'completed'  # type: ignore
            ).all()
            
            if not exam_sessions:
                return {
                    'score_trends': [],
                    'performance_summary': {
                        'total_exams': 0,
                        'average_score': 0,
                        'best_score': 0,
                        'improvement_rate': 0
                    },
                    'period': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'days': period_days
                    }
                }
            
            # 分析成绩趋势
            score_trends = []
            scores = []
            
            for exam in exam_sessions:
                if hasattr(exam, 'total_score') and exam.total_score is not None:
                    score_percentage = 0
                    max_score = getattr(exam, 'max_possible_score', None)
                    if max_score is not None and max_score > 0:
                        score_percentage = (exam.total_score / max_score * 100)
                    
                    score_trends.append({
                        'exam_id': exam.id,
                        'exam_type': exam.exam_type,
                        'score': exam.total_score,
                        'max_score': max_score or 0,
                        'percentage': score_percentage,
                        'date': exam.created_time.isoformat() if hasattr(exam, 'created_time') and exam.created_time is not None else None
                    })
                    scores.append(score_percentage)
            
            # 计算趋势指标
            if scores:
                average_score = mean(scores)
                best_score = max(scores)
                
                # 简单的改进率计算（后半部分vs前半部分）
                mid_point = len(scores) // 2
                if mid_point > 0:
                    early_avg = mean(scores[:mid_point])
                    recent_avg = mean(scores[mid_point:])
                    improvement_rate = ((recent_avg - early_avg) / early_avg * 100) if early_avg > 0 else 0
                else:
                    improvement_rate = 0
            else:
                average_score = 0
                best_score = 0
                improvement_rate = 0
            
            return {
                'score_trends': score_trends,
                'performance_summary': {
                    'total_exams': len(exam_sessions),
                    'average_score': average_score,
                    'best_score': best_score,
                    'improvement_rate': improvement_rate
                },
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': period_days
                }
            }
            
        except Exception as e:
            self.logger.error(f"分析学习效果趋势失败: {str(e)}")
            return None
    
    def generate_comprehensive_report(self, user_id: str, period_days: int = 30) -> Optional[Dict[str, Any]]:
        """
        生成综合学习分析报告
        
        Args:
            user_id: 用户ID
            period_days: 分析周期（天数）
            
        Returns:
            综合学习分析报告
        """
        try:
            # 确保user_id是字符串
            user_id_str = str(user_id) if not isinstance(user_id, str) else user_id
            
            # 获取各项分析结果
            progress_analysis = self.analyze_learning_progress(user_id_str, period_days)
            knowledge_analysis = self.analyze_knowledge_mastery(user_id_str)
            performance_analysis = self.analyze_performance_trends(user_id_str, period_days)
            
            if not progress_analysis or not knowledge_analysis:
                return None
            
            # 计算综合评分
            overall_score = self._calculate_overall_score(
                progress_analysis, knowledge_analysis, performance_analysis
            )
            
            # 生成关键洞察
            key_insights = self._generate_key_insights(
                progress_analysis, knowledge_analysis, performance_analysis
            )
            
            # 生成改进建议
            improvement_suggestions = self._generate_improvement_suggestions(
                progress_analysis, knowledge_analysis, performance_analysis
            )
            
            # 生成目标建议
            goal_suggestions = self._generate_goal_suggestions(
                progress_analysis, knowledge_analysis, performance_analysis
            )
            
            return {
                'overall_score': overall_score,
                'key_insights': key_insights,
                'improvement_suggestions': improvement_suggestions,
                'goal_suggestions': goal_suggestions,
                'progress_analysis': progress_analysis,
                'knowledge_analysis': knowledge_analysis,
                'performance_analysis': performance_analysis,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"生成综合分析报告失败: {str(e)}")
            return None
    
    def _analyze_recent_trend(self, performance_history: List[Dict]) -> str:
        """
        分析最近的学习趋势
        
        Args:
            performance_history: 表现历史记录
            
        Returns:
            趋势描述
        """
        if len(performance_history) < 3:
            return 'insufficient_data'
        
        # 取最近的记录
        recent_records = performance_history[-5:]
        correct_count = sum(1 for record in recent_records if record['is_correct'])
        
        if correct_count >= 4:
            return 'improving'
        elif correct_count >= 2:
            return 'stable'
        else:
            return 'declining'
    
    def _generate_learning_recommendations(self, weak_points: List[Dict], strong_points: List[Dict]) -> List[Dict]:
        """
        生成学习建议
        
        Args:
            weak_points: 薄弱知识点
            strong_points: 强势知识点
            
        Returns:
            学习建议列表
        """
        recommendations = []
        
        # 针对薄弱知识点的建议
        if weak_points:
            top_weak = weak_points[:3]  # 最薄弱的3个
            for kp in top_weak:
                recommendations.append({
                    'type': 'focus_practice',
                    'priority': 'high',
                    'title': f"重点练习：{kp['knowledge_point_name']}",
                    'description': f"当前准确率仅{kp['accuracy_rate']:.1f}%，建议加强练习",
                    'knowledge_point_id': kp['knowledge_point_id']
                })
        
        # 基于强势知识点的建议
        if strong_points:
            recommendations.append({
                'type': 'maintain_strength',
                'priority': 'medium',
                'title': '保持优势领域',
                'description': f"在{len(strong_points)}个知识点上表现优秀，继续保持",
                'knowledge_point_ids': [kp['knowledge_point_id'] for kp in strong_points]
            })
        
        # 通用建议
        recommendations.append({
            'type': 'regular_review',
            'priority': 'medium',
            'title': '定期复习',
            'description': '建议每周安排时间复习已学知识点，巩固记忆'
        })
        
        return recommendations
    
    def _calculate_overall_score(self, progress_analysis: Dict, knowledge_analysis: Dict, performance_analysis: Optional[Dict]) -> Dict:
        """
        计算综合评分
        
        Args:
            progress_analysis: 进度分析结果
            knowledge_analysis: 知识点分析结果
            performance_analysis: 表现分析结果
            
        Returns:
            综合评分
        """
        # 进度评分（40%）
        progress_score = min(progress_analysis['overall_progress']['average_accuracy'], 100)
        
        # 知识点掌握评分（40%）
        mastery_score = knowledge_analysis['overall_statistics']['mastery_rate']
        
        # 表现趋势评分（20%）
        trend_score = 70  # 默认分数
        if performance_analysis and performance_analysis['performance_summary']['improvement_rate'] > 0:
            trend_score = min(70 + performance_analysis['performance_summary']['improvement_rate'], 100)
        
        # 加权计算总分
        total_score = (progress_score * 0.4 + mastery_score * 0.4 + trend_score * 0.2)
        
        # 确定等级
        if total_score >= 90:
            grade = 'A'
        elif total_score >= 80:
            grade = 'B'
        elif total_score >= 70:
            grade = 'C'
        elif total_score >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        return {
            'total_score': round(total_score, 1),
            'grade': grade,
            'component_scores': {
                'progress_score': round(progress_score, 1),
                'mastery_score': round(mastery_score, 1),
                'trend_score': round(trend_score, 1)
            }
        }
    
    def _generate_key_insights(self, progress_analysis: Dict, knowledge_analysis: Dict, performance_analysis: Optional[Dict]) -> List[str]:
        """
        生成关键洞察
        
        Args:
            progress_analysis: 进度分析结果
            knowledge_analysis: 知识点分析结果
            performance_analysis: 表现分析结果
            
        Returns:
            关键洞察列表
        """
        insights = []
        
        # 学习时间洞察
        daily_time = progress_analysis['overall_progress']['daily_average_time']
        if daily_time > 120:  # 2小时
            insights.append(f"学习时间充足，日均{daily_time:.0f}分钟")
        elif daily_time > 60:  # 1小时
            insights.append(f"学习时间适中，日均{daily_time:.0f}分钟")
        else:
            insights.append(f"学习时间偏少，日均仅{daily_time:.0f}分钟，建议增加学习时间")
        
        # 准确率洞察
        accuracy = progress_analysis['overall_progress']['average_accuracy']
        if accuracy >= 80:
            insights.append(f"学习效果良好，准确率达{accuracy:.1f}%")
        elif accuracy >= 60:
            insights.append(f"学习效果一般，准确率{accuracy:.1f}%，有提升空间")
        else:
            insights.append(f"学习效果需要改进，准确率仅{accuracy:.1f}%")
        
        # 知识点掌握洞察
        mastery_rate = knowledge_analysis['overall_statistics']['mastery_rate']
        struggling_count = knowledge_analysis['overall_statistics']['struggling_count']
        if struggling_count > 0:
            insights.append(f"有{struggling_count}个薄弱知识点需要重点关注")
        if mastery_rate >= 70:
            insights.append(f"知识点掌握情况良好，掌握率{mastery_rate:.1f}%")
        
        return insights
    
    def _generate_improvement_suggestions(self, progress_analysis: Dict, knowledge_analysis: Dict, performance_analysis: Optional[Dict]) -> List[Dict]:
        """
        生成改进建议
        
        Args:
            progress_analysis: 进度分析结果
            knowledge_analysis: 知识点分析结果
            performance_analysis: 表现分析结果
            
        Returns:
            改进建议列表
        """
        suggestions = []
        
        # 基于准确率的建议
        accuracy = progress_analysis['overall_progress']['average_accuracy']
        if accuracy < 70:
            suggestions.append({
                'category': 'accuracy',
                'priority': 'high',
                'title': '提高答题准确率',
                'description': '当前准确率偏低，建议放慢答题速度，仔细审题',
                'action_items': ['仔细阅读题目', '检查答案', '总结错题原因']
            })
        
        # 基于学习时间的建议
        daily_time = progress_analysis['overall_progress']['daily_average_time']
        if daily_time < 60:
            suggestions.append({
                'category': 'time_management',
                'priority': 'medium',
                'title': '增加学习时间',
                'description': '每日学习时间不足，建议制定学习计划',
                'action_items': ['制定每日学习计划', '设置学习提醒', '找到固定学习时间']
            })
        
        # 基于薄弱知识点的建议
        weak_points = knowledge_analysis['weak_points']
        if len(weak_points) > 3:
            suggestions.append({
                'category': 'knowledge_gaps',
                'priority': 'high',
                'title': '重点攻克薄弱知识点',
                'description': f'有{len(weak_points)}个薄弱知识点，建议逐个突破',
                'action_items': ['制定知识点学习计划', '寻找相关学习资源', '定期自测']
            })
        
        return suggestions
    
    def _generate_goal_suggestions(self, progress_analysis: Dict, knowledge_analysis: Dict, performance_analysis: Optional[Dict]) -> List[Dict]:
        """
        生成目标建议
        
        Args:
            progress_analysis: 进度分析结果
            knowledge_analysis: 知识点分析结果
            performance_analysis: 表现分析结果
            
        Returns:
            目标建议列表
        """
        goals = []
        
        # 准确率目标
        current_accuracy = progress_analysis['overall_progress']['average_accuracy']
        target_accuracy = min(current_accuracy + 10, 95)
        goals.append({
            'type': 'accuracy',
            'title': f'提高准确率至{target_accuracy:.0f}%',
            'current_value': current_accuracy,
            'target_value': target_accuracy,
            'timeframe': '30天',
            'difficulty': 'medium'
        })
        
        # 学习时间目标
        current_time = progress_analysis['overall_progress']['daily_average_time']
        target_time = max(current_time + 15, 90)  # 至少90分钟
        goals.append({
            'type': 'study_time',
            'title': f'每日学习时间达到{target_time:.0f}分钟',
            'current_value': current_time,
            'target_value': target_time,
            'timeframe': '14天',
            'difficulty': 'easy'
        })
        
        # 知识点掌握目标
        current_mastery = knowledge_analysis['overall_statistics']['mastery_rate']
        target_mastery = min(current_mastery + 15, 90)
        goals.append({
            'type': 'mastery_rate',
            'title': f'知识点掌握率达到{target_mastery:.0f}%',
            'current_value': current_mastery,
            'target_value': target_mastery,
            'timeframe': '45天',
            'difficulty': 'hard'
        })
        
        return goals