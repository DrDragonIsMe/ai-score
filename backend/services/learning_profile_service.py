# -*- coding: utf-8 -*-
"""
学习画像服务 - 个性化学习特征分析
"""

import json
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from models.diagnosis import DiagnosisReport, DiagnosisSession, QuestionResponse, LearningProfile
from models.knowledge import KnowledgePoint, Subject
from models.user import User
from utils.database import db
from utils.logger import get_logger

logger = get_logger(__name__)

class LearningProfileService:
    """学习画像服务"""
    
    @staticmethod
    def create_or_update_profile(user_id: str, subject_id: str) -> LearningProfile:
        """
        创建或更新学习画像
        
        Args:
            user_id: 用户ID
            subject_id: 学科ID
            
        Returns:
            学习画像对象
        """
        try:
            # 查找现有画像
            profile = LearningProfile.query.filter_by(
                user_id=user_id,
                subject_id=subject_id
            ).first()
            
            if not profile:
                profile = LearningProfile(
                    user_id=user_id,
                    subject_id=subject_id
                )
                db.session.add(profile)
            
            # 更新画像数据
            LearningProfileService._update_profile_data(profile)
            
            db.session.commit()
            return profile
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建或更新学习画像失败: {e}")
            raise
    
    @staticmethod
    def _update_profile_data(profile: LearningProfile):
        """
        更新学习画像数据
        
        Args:
            profile: 学习画像对象
        """
        try:
            # 获取用户在该学科的所有诊断报告
            reports = DiagnosisReport.query.filter_by(
                user_id=profile.user_id,
                subject_id=profile.subject_id
            ).all()
            
            if not reports:
                return
            
            # 分析学习能力
            ability_analysis = LearningProfileService._analyze_learning_ability(reports)
            profile.ability_scores = ability_analysis
            
            # 分析学习偏好
            preference_analysis = LearningProfileService._analyze_learning_preferences(reports)
            profile.learning_preferences = preference_analysis
            
            # 分析学习行为
            behavior_analysis = LearningProfileService._analyze_learning_behavior(reports)
            profile.behavior_patterns = behavior_analysis
            
            # 分析知识掌握情况
            mastery_analysis = LearningProfileService._analyze_knowledge_mastery(reports)
            profile.knowledge_mastery = mastery_analysis
            
            # 分析遗忘曲线
            forgetting_analysis = LearningProfileService._analyze_forgetting_curve(reports)
            profile.forgetting_curve_params = forgetting_analysis
            
            # 生成学习建议
            recommendations = LearningProfileService._generate_learning_recommendations(profile)
            profile.learning_recommendations = recommendations
            
            # 更新统计信息
            profile.total_diagnoses = len(reports)
            profile.last_diagnosis_date = max(r.created_at for r in reports) if reports else None
            
            # 计算整体学习水平
            profile.overall_level = LearningProfileService._calculate_overall_level(ability_analysis)
            
        except Exception as e:
            logger.error(f"更新学习画像数据失败: {e}")
            raise
    
    @staticmethod
    def _analyze_learning_ability(reports: List[DiagnosisReport]) -> Dict:
        """
        分析学习能力
        
        Args:
            reports: 诊断报告列表
            
        Returns:
            学习能力分析结果
        """
        try:
            if not reports:
                return {}
            
            # 收集所有会话数据
            all_sessions = []
            for report in reports:
                all_sessions.extend(report.diagnosis_sessions.all())
            
            if not all_sessions:
                return {}
            
            # 分析不同层级的能力
            ability_by_level = {
                'memory': [],  # 记忆层
                'application': [],  # 应用层
                'transfer': []  # 迁移层
            }
            
            for session in all_sessions:
                session_type = session.session_type
                if session_type in ability_by_level:
                    ability_by_level[session_type].append(session.current_ability)
            
            # 计算各层级平均能力
            ability_scores = {}
            for level, abilities in ability_by_level.items():
                if abilities:
                    ability_scores[level] = {
                        'mean': sum(abilities) / len(abilities),
                        'std': math.sqrt(sum((x - sum(abilities)/len(abilities))**2 for x in abilities) / len(abilities)) if len(abilities) > 1 else 0,
                        'count': len(abilities),
                        'trend': LearningProfileService._calculate_trend(abilities)
                    }
                else:
                    ability_scores[level] = {
                        'mean': 0.0,
                        'std': 0.0,
                        'count': 0,
                        'trend': 'unknown'
                    }
            
            # 计算综合能力指标
            all_abilities = []
            for abilities in ability_by_level.values():
                all_abilities.extend(abilities)
            
            if all_abilities:
                ability_scores['overall'] = {
                    'mean': sum(all_abilities) / len(all_abilities),
                    'std': math.sqrt(sum((x - sum(all_abilities)/len(all_abilities))**2 for x in all_abilities) / len(all_abilities)) if len(all_abilities) > 1 else 0,
                    'range': max(all_abilities) - min(all_abilities),
                    'stability': 1 / (1 + math.sqrt(sum((x - sum(all_abilities)/len(all_abilities))**2 for x in all_abilities) / len(all_abilities))) if len(all_abilities) > 1 else 1.0
                }
            
            return ability_scores
            
        except Exception as e:
            logger.error(f"分析学习能力失败: {e}")
            return {}
    
    @staticmethod
    def _analyze_learning_preferences(reports: List[DiagnosisReport]) -> Dict:
        """
        分析学习偏好
        
        Args:
            reports: 诊断报告列表
            
        Returns:
            学习偏好分析结果
        """
        try:
            if not reports:
                return {}
            
            # 收集所有答题记录
            all_responses = []
            for report in reports:
                for session in report.diagnosis_sessions.all():
                    all_responses.extend(session.question_responses.all())
            
            if not all_responses:
                return {}
            
            preferences = {}
            
            # 1. 难度偏好分析
            difficulty_performance = defaultdict(list)
            for response in all_responses:
                difficulty_performance[response.difficulty_level].append(
                    1 if response.is_correct else 0
                )
            
            difficulty_preferences = {}
            for difficulty, results in difficulty_performance.items():
                if results:
                    accuracy = sum(results) / len(results)
                    difficulty_preferences[str(difficulty)] = {
                        'accuracy': accuracy,
                        'count': len(results),
                        'preference_score': accuracy * math.log(len(results) + 1)  # 考虑准确率和题目数量
                    }
            
            preferences['difficulty'] = difficulty_preferences
            
            # 2. 题型偏好分析
            question_type_performance = defaultdict(list)
            for response in all_responses:
                if response.question_type:
                    question_type_performance[response.question_type].append(
                        1 if response.is_correct else 0
                    )
            
            type_preferences = {}
            for qtype, results in question_type_performance.items():
                if results:
                    accuracy = sum(results) / len(results)
                    type_preferences[qtype] = {
                        'accuracy': accuracy,
                        'count': len(results),
                        'preference_score': accuracy * math.log(len(results) + 1)
                    }
            
            preferences['question_type'] = type_preferences
            
            # 3. 时间偏好分析
            time_analysis = LearningProfileService._analyze_time_preferences(all_responses)
            preferences['time'] = time_analysis
            
            # 4. 知识点偏好分析
            kp_performance = defaultdict(list)
            for response in all_responses:
                if response.knowledge_point_id:
                    kp_performance[response.knowledge_point_id].append(
                        1 if response.is_correct else 0
                    )
            
            # 找出表现最好和最差的知识点
            kp_preferences = {
                'strong_points': [],
                'weak_points': []
            }
            
            for kp_id, results in kp_performance.items():
                if len(results) >= 3:  # 至少3题才有统计意义
                    accuracy = sum(results) / len(results)
                    kp_info = {
                        'knowledge_point_id': kp_id,
                        'accuracy': accuracy,
                        'count': len(results)
                    }
                    
                    if accuracy >= 0.8:
                        kp_preferences['strong_points'].append(kp_info)
                    elif accuracy <= 0.4:
                        kp_preferences['weak_points'].append(kp_info)
            
            # 按准确率排序
            kp_preferences['strong_points'].sort(key=lambda x: x['accuracy'], reverse=True)
            kp_preferences['weak_points'].sort(key=lambda x: x['accuracy'])
            
            preferences['knowledge_points'] = kp_preferences
            
            return preferences
            
        except Exception as e:
            logger.error(f"分析学习偏好失败: {e}")
            return {}
    
    @staticmethod
    def _analyze_time_preferences(responses: List[QuestionResponse]) -> Dict:
        """
        分析时间偏好
        
        Args:
            responses: 答题记录列表
            
        Returns:
            时间偏好分析结果
        """
        try:
            if not responses:
                return {}
            
            # 按难度分组分析用时
            time_by_difficulty = defaultdict(list)
            for response in responses:
                if response.time_spent and response.time_spent > 0:
                    time_by_difficulty[response.difficulty_level].append(response.time_spent)
            
            time_analysis = {
                'average_time_by_difficulty': {},
                'time_efficiency': {},
                'time_consistency': 0.0,
                'preferred_pace': 'normal'
            }
            
            all_times = []
            for difficulty, times in time_by_difficulty.items():
                if times:
                    avg_time = sum(times) / len(times)
                    time_analysis['average_time_by_difficulty'][str(difficulty)] = avg_time
                    all_times.extend(times)
                    
                    # 计算时间效率（正确率/平均用时）
                    correct_responses = [r for r in responses 
                                       if r.difficulty_level == difficulty and r.is_correct]
                    if correct_responses and times:
                        efficiency = len(correct_responses) / len([r for r in responses if r.difficulty_level == difficulty]) / avg_time
                        time_analysis['time_efficiency'][str(difficulty)] = efficiency
            
            # 计算时间一致性
            if all_times and len(all_times) > 1:
                mean_time = sum(all_times) / len(all_times)
                variance = sum((t - mean_time) ** 2 for t in all_times) / len(all_times)
                cv = math.sqrt(variance) / mean_time if mean_time > 0 else 0
                time_analysis['time_consistency'] = max(0, 1 - cv)  # 变异系数越小，一致性越高
            
            # 判断偏好的答题节奏
            if all_times:
                avg_time = sum(all_times) / len(all_times)
                if avg_time < 30:  # 30秒以下
                    time_analysis['preferred_pace'] = 'fast'
                elif avg_time > 120:  # 2分钟以上
                    time_analysis['preferred_pace'] = 'slow'
                else:
                    time_analysis['preferred_pace'] = 'normal'
            
            return time_analysis
            
        except Exception as e:
            logger.error(f"分析时间偏好失败: {e}")
            return {}
    
    @staticmethod
    def _analyze_learning_behavior(reports: List[DiagnosisReport]) -> Dict:
        """
        分析学习行为模式
        
        Args:
            reports: 诊断报告列表
            
        Returns:
            学习行为分析结果
        """
        try:
            if not reports:
                return {}
            
            behavior_patterns = {
                'consistency': 0.0,
                'persistence': 0.0,
                'adaptability': 0.0,
                'error_recovery': 0.0,
                'learning_style': 'balanced',
                'motivation_level': 'medium'
            }
            
            # 收集所有会话数据
            all_sessions = []
            for report in reports:
                all_sessions.extend(report.diagnosis_sessions.all())
            
            if not all_sessions:
                return behavior_patterns
            
            # 1. 分析一致性（表现的稳定性）
            consistency_scores = []
            for session in all_sessions:
                responses = session.question_responses.all()
                if len(responses) >= 5:
                    accuracies = [1 if r.is_correct else 0 for r in responses]
                    # 计算滑动窗口准确率的方差
                    window_size = min(5, len(accuracies))
                    window_accuracies = []
                    for i in range(len(accuracies) - window_size + 1):
                        window_acc = sum(accuracies[i:i+window_size]) / window_size
                        window_accuracies.append(window_acc)
                    
                    if window_accuracies:
                        variance = sum((acc - sum(window_accuracies)/len(window_accuracies))**2 for acc in window_accuracies) / len(window_accuracies)
                        consistency = max(0, 1 - variance)  # 方差越小，一致性越高
                        consistency_scores.append(consistency)
            
            if consistency_scores:
                behavior_patterns['consistency'] = sum(consistency_scores) / len(consistency_scores)
            
            # 2. 分析坚持性（完成率和持续时间）
            completion_rates = []
            for session in all_sessions:
                planned_questions = session.max_questions
                actual_questions = session.questions_answered
                if planned_questions > 0:
                    completion_rate = min(1.0, actual_questions / planned_questions)
                    completion_rates.append(completion_rate)
            
            if completion_rates:
                behavior_patterns['persistence'] = sum(completion_rates) / len(completion_rates)
            
            # 3. 分析适应性（能力估计的收敛速度）
            adaptability_scores = []
            for session in all_sessions:
                if session.questions_answered >= 10:
                    # 计算能力估计的收敛速度
                    initial_se = 1.0  # 初始标准误差
                    final_se = session.ability_se
                    convergence_rate = (initial_se - final_se) / session.questions_answered
                    adaptability_scores.append(min(1.0, convergence_rate * 10))  # 归一化
            
            if adaptability_scores:
                behavior_patterns['adaptability'] = sum(adaptability_scores) / len(adaptability_scores)
            
            # 4. 分析错误恢复能力
            error_recovery_scores = []
            for session in all_sessions:
                responses = list(session.question_responses.order_by(QuestionResponse.created_at.asc()).all())
                if len(responses) >= 5:
                    recovery_count = 0
                    error_count = 0
                    
                    for i in range(len(responses) - 1):
                        if not responses[i].is_correct:
                            error_count += 1
                            # 检查后续3题的表现
                            next_responses = responses[i+1:i+4]
                            if next_responses:
                                recovery_rate = sum(1 for r in next_responses if r.is_correct) / len(next_responses)
                                if recovery_rate >= 0.67:  # 后续题目正确率>=67%
                                    recovery_count += 1
                    
                    if error_count > 0:
                        recovery_score = recovery_count / error_count
                        error_recovery_scores.append(recovery_score)
            
            if error_recovery_scores:
                behavior_patterns['error_recovery'] = sum(error_recovery_scores) / len(error_recovery_scores)
            
            # 5. 判断学习风格
            behavior_patterns['learning_style'] = LearningProfileService._determine_learning_style(behavior_patterns)
            
            # 6. 评估动机水平
            behavior_patterns['motivation_level'] = LearningProfileService._assess_motivation_level(
                behavior_patterns, len(reports)
            )
            
            return behavior_patterns
            
        except Exception as e:
            logger.error(f"分析学习行为失败: {e}")
            return {}
    
    @staticmethod
    def _determine_learning_style(behavior_patterns: Dict) -> str:
        """
        根据行为模式判断学习风格
        
        Args:
            behavior_patterns: 行为模式数据
            
        Returns:
            学习风格类型
        """
        try:
            consistency = behavior_patterns.get('consistency', 0.5)
            persistence = behavior_patterns.get('persistence', 0.5)
            adaptability = behavior_patterns.get('adaptability', 0.5)
            
            if consistency >= 0.7 and persistence >= 0.7:
                return 'systematic'  # 系统型
            elif adaptability >= 0.7:
                return 'adaptive'  # 适应型
            elif persistence >= 0.8:
                return 'persistent'  # 坚持型
            elif consistency <= 0.3 and adaptability <= 0.3:
                return 'exploratory'  # 探索型
            else:
                return 'balanced'  # 平衡型
                
        except Exception as e:
            logger.error(f"判断学习风格失败: {e}")
            return 'balanced'
    
    @staticmethod
    def _assess_motivation_level(behavior_patterns: Dict, report_count: int) -> str:
        """
        评估动机水平
        
        Args:
            behavior_patterns: 行为模式数据
            report_count: 报告数量
            
        Returns:
            动机水平
        """
        try:
            persistence = behavior_patterns.get('persistence', 0.5)
            consistency = behavior_patterns.get('consistency', 0.5)
            
            # 综合考虑坚持性、一致性和活跃度
            activity_score = min(1.0, report_count / 10)  # 10次诊断为满分
            motivation_score = (persistence + consistency + activity_score) / 3
            
            if motivation_score >= 0.7:
                return 'high'
            elif motivation_score >= 0.4:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            logger.error(f"评估动机水平失败: {e}")
            return 'medium'
    
    @staticmethod
    def _analyze_knowledge_mastery(reports: List[DiagnosisReport]) -> Dict:
        """
        分析知识掌握情况
        
        Args:
            reports: 诊断报告列表
            
        Returns:
            知识掌握分析结果
        """
        try:
            if not reports:
                return {}
            
            # 收集所有知识点的掌握数据
            kp_mastery = defaultdict(list)
            
            for report in reports:
                if report.mastery_levels:
                    for kp_id, mastery_score in report.mastery_levels.items():
                        kp_mastery[kp_id].append({
                            'score': mastery_score,
                            'date': report.created_at
                        })
            
            mastery_analysis = {
                'knowledge_points': {},
                'overall_mastery': 0.0,
                'mastery_distribution': {
                    'excellent': 0,  # >= 0.9
                    'good': 0,       # 0.7-0.89
                    'fair': 0,       # 0.5-0.69
                    'poor': 0        # < 0.5
                },
                'improvement_trend': {},
                'stable_points': [],
                'improving_points': [],
                'declining_points': []
            }
            
            all_scores = []
            
            for kp_id, mastery_data in kp_mastery.items():
                if mastery_data:
                    # 按时间排序
                    mastery_data.sort(key=lambda x: x['date'])
                    
                    scores = [d['score'] for d in mastery_data]
                    latest_score = scores[-1]
                    all_scores.append(latest_score)
                    
                    # 计算趋势
                    trend = LearningProfileService._calculate_trend(scores)
                    
                    kp_analysis = {
                        'current_mastery': latest_score,
                        'average_mastery': sum(scores) / len(scores),
                        'trend': trend,
                        'stability': LearningProfileService._calculate_stability(scores),
                        'assessment_count': len(scores)
                    }
                    
                    mastery_analysis['knowledge_points'][kp_id] = kp_analysis
                    
                    # 分类知识点
                    if trend == 'improving':
                        mastery_analysis['improving_points'].append(kp_id)
                    elif trend == 'declining':
                        mastery_analysis['declining_points'].append(kp_id)
                    else:
                        mastery_analysis['stable_points'].append(kp_id)
                    
                    # 统计掌握程度分布
                    if latest_score >= 0.9:
                        mastery_analysis['mastery_distribution']['excellent'] += 1
                    elif latest_score >= 0.7:
                        mastery_analysis['mastery_distribution']['good'] += 1
                    elif latest_score >= 0.5:
                        mastery_analysis['mastery_distribution']['fair'] += 1
                    else:
                        mastery_analysis['mastery_distribution']['poor'] += 1
            
            # 计算整体掌握度
            if all_scores:
                mastery_analysis['overall_mastery'] = sum(all_scores) / len(all_scores)
            
            return mastery_analysis
            
        except Exception as e:
            logger.error(f"分析知识掌握情况失败: {e}")
            return {}
    
    @staticmethod
    def _calculate_trend(values: List[float]) -> str:
        """
        计算数值序列的趋势
        
        Args:
            values: 数值列表
            
        Returns:
            趋势类型: 'improving', 'declining', 'stable'
        """
        try:
            if len(values) < 2:
                return 'stable'
            
            # 简单线性回归计算斜率
            n = len(values)
            x_mean = (n - 1) / 2
            y_mean = sum(values) / n
            
            numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            
            if denominator == 0:
                return 'stable'
            
            slope = numerator / denominator
            
            # 根据斜率判断趋势
            if slope > 0.05:  # 阈值可调整
                return 'improving'
            elif slope < -0.05:
                return 'declining'
            else:
                return 'stable'
                
        except Exception as e:
            logger.error(f"计算趋势失败: {e}")
            return 'stable'
    
    @staticmethod
    def _calculate_stability(values: List[float]) -> float:
        """
        计算数值序列的稳定性
        
        Args:
            values: 数值列表
            
        Returns:
            稳定性分数 (0-1)
        """
        try:
            if len(values) < 2:
                return 1.0
            
            mean_val = sum(values) / len(values)
            variance = sum((v - mean_val) ** 2 for v in values) / len(values)
            cv = math.sqrt(variance) / mean_val if mean_val > 0 else 0
            
            # 变异系数越小，稳定性越高
            stability = max(0, 1 - cv)
            return min(1.0, stability)
            
        except Exception as e:
            logger.error(f"计算稳定性失败: {e}")
            return 0.5
    
    @staticmethod
    def _analyze_forgetting_curve(reports: List[DiagnosisReport]) -> Dict:
        """
        分析遗忘曲线参数
        
        Args:
            reports: 诊断报告列表
            
        Returns:
            遗忘曲线参数
        """
        try:
            if len(reports) < 2:
                return {
                    'initial_strength': 0.8,
                    'decay_rate': 0.3,
                    'retention_factor': 0.7,
                    'optimal_review_interval': 7
                }
            
            # 分析重复测试的知识点
            kp_performances = defaultdict(list)
            
            for report in reports:
                if report.mastery_levels:
                    for kp_id, mastery_score in report.mastery_levels.items():
                        kp_performances[kp_id].append({
                            'score': mastery_score,
                            'date': report.created_at
                        })
            
            # 计算遗忘曲线参数
            decay_rates = []
            retention_factors = []
            
            for kp_id, performances in kp_performances.items():
                if len(performances) >= 2:
                    # 按时间排序
                    performances.sort(key=lambda x: x['date'])
                    
                    for i in range(len(performances) - 1):
                        current = performances[i]
                        next_perf = performances[i + 1]
                        
                        # 计算时间间隔（天）
                        time_diff = (next_perf['date'] - current['date']).days
                        if time_diff > 0:
                            # 计算遗忘率
                            initial_score = current['score']
                            retained_score = next_perf['score']
                            
                            if initial_score > 0:
                                retention_rate = retained_score / initial_score
                                retention_factors.append(retention_rate)
                                
                                # 估算衰减率 (简化的指数衰减模型)
                                if retention_rate > 0 and retention_rate < 1:
                                    decay_rate = -math.log(retention_rate) / time_diff
                                    decay_rates.append(decay_rate)
            
            # 计算平均参数
            forgetting_params = {
                'initial_strength': 0.8,  # 初始记忆强度
                'decay_rate': sum(decay_rates) / len(decay_rates) if decay_rates else 0.1,
                'retention_factor': sum(retention_factors) / len(retention_factors) if retention_factors else 0.7,
                'optimal_review_interval': 7  # 最优复习间隔（天）
            }
            
            # 根据衰减率计算最优复习间隔
            if forgetting_params['decay_rate'] > 0:
                # 当记忆强度降到70%时进行复习
                target_retention = 0.7
                optimal_interval = -math.log(target_retention) / forgetting_params['decay_rate']
                forgetting_params['optimal_review_interval'] = max(1, min(30, int(optimal_interval)))
            
            return forgetting_params
            
        except Exception as e:
            logger.error(f"分析遗忘曲线失败: {e}")
            return {
                'initial_strength': 0.8,
                'decay_rate': 0.1,
                'retention_factor': 0.7,
                'optimal_review_interval': 7
            }
    
    @staticmethod
    def _generate_learning_recommendations(profile: LearningProfile) -> List[Dict]:
        """
        生成个性化学习建议
        
        Args:
            profile: 学习画像对象
            
        Returns:
            学习建议列表
        """
        try:
            recommendations = []
            
            # 基于能力分析的建议
            if profile.ability_scores:
                ability_recs = LearningProfileService._generate_ability_recommendations(profile.ability_scores)
                recommendations.extend(ability_recs)
            
            # 基于学习偏好的建议
            if profile.learning_preferences:
                preference_recs = LearningProfileService._generate_preference_recommendations(profile.learning_preferences)
                recommendations.extend(preference_recs)
            
            # 基于行为模式的建议
            if profile.behavior_patterns:
                behavior_recs = LearningProfileService._generate_behavior_recommendations(profile.behavior_patterns)
                recommendations.extend(behavior_recs)
            
            # 基于知识掌握的建议
            if profile.knowledge_mastery:
                mastery_recs = LearningProfileService._generate_mastery_recommendations(profile.knowledge_mastery)
                recommendations.extend(mastery_recs)
            
            # 基于遗忘曲线的建议
            if profile.forgetting_curve_params:
                forgetting_recs = LearningProfileService._generate_forgetting_recommendations(profile.forgetting_curve_params)
                recommendations.extend(forgetting_recs)
            
            return recommendations[:10]  # 限制建议数量
            
        except Exception as e:
            logger.error(f"生成学习建议失败: {e}")
            return []
    
    @staticmethod
    def _generate_ability_recommendations(ability_scores: Dict) -> List[Dict]:
        """
        基于能力分析生成建议
        
        Args:
            ability_scores: 能力分析结果
            
        Returns:
            建议列表
        """
        recommendations = []
        
        try:
            # 分析各层级能力
            for level in ['memory', 'application', 'transfer']:
                if level in ability_scores:
                    ability_data = ability_scores[level]
                    mean_ability = ability_data.get('mean', 0)
                    
                    level_names = {
                        'memory': '记忆层',
                        'application': '应用层', 
                        'transfer': '迁移层'
                    }
                    
                    if mean_ability < -0.5:
                        recommendations.append({
                            'type': 'ability_improvement',
                            'priority': 'high',
                            'title': f'加强{level_names[level]}能力训练',
                            'description': f'您在{level_names[level]}的表现需要提升，建议增加相关练习',
                            'action_items': [
                                f'每日进行{level_names[level]}专项练习',
                                '从基础题目开始，逐步提高难度',
                                '注重理解概念，而非死记硬背'
                            ]
                        })
                    elif mean_ability > 1.0:
                        recommendations.append({
                            'type': 'ability_challenge',
                            'priority': 'medium',
                            'title': f'{level_names[level]}能力优秀，可挑战更高难度',
                            'description': f'您在{level_names[level]}表现优秀，可以尝试更有挑战性的题目',
                            'action_items': [
                                '尝试解决综合性问题',
                                '参与竞赛或高阶练习',
                                '帮助其他同学，巩固知识'
                            ]
                        })
            
            # 分析能力稳定性
            if 'overall' in ability_scores:
                stability = ability_scores['overall'].get('stability', 0.5)
                if stability < 0.3:
                    recommendations.append({
                        'type': 'stability_improvement',
                        'priority': 'medium',
                        'title': '提高学习表现的稳定性',
                        'description': '您的学习表现波动较大，建议建立更规律的学习习惯',
                        'action_items': [
                            '制定固定的学习时间表',
                            '保持良好的作息习惯',
                            '定期复习，避免遗忘'
                        ]
                    })
            
        except Exception as e:
            logger.error(f"生成能力建议失败: {e}")
        
        return recommendations
    
    @staticmethod
    def _generate_preference_recommendations(preferences: Dict) -> List[Dict]:
        """
        基于学习偏好生成建议
        
        Args:
            preferences: 学习偏好数据
            
        Returns:
            建议列表
        """
        recommendations = []
        
        try:
            # 基于难度偏好的建议
            if 'difficulty' in preferences:
                difficulty_prefs = preferences['difficulty']
                best_difficulty = max(difficulty_prefs.items(), 
                                    key=lambda x: x[1].get('preference_score', 0))[0]
                
                recommendations.append({
                    'type': 'difficulty_optimization',
                    'priority': 'medium',
                    'title': f'优化练习难度设置',
                    'description': f'您在难度{best_difficulty}的题目上表现最佳，建议以此为基础进行练习',
                    'action_items': [
                        f'主要练习难度{best_difficulty}的题目',
                        '逐步向更高难度挑战',
                        '保持适当的挑战性'
                    ]
                })
            
            # 基于时间偏好的建议
            if 'time' in preferences:
                time_prefs = preferences['time']
                preferred_pace = time_prefs.get('preferred_pace', 'normal')
                
                pace_advice = {
                    'fast': {
                        'title': '控制答题速度，提高准确性',
                        'description': '您答题速度较快，建议适当放慢节奏以提高准确率',
                        'actions': ['仔细审题', '检查答案', '避免粗心错误']
                    },
                    'slow': {
                        'title': '提高答题效率',
                        'description': '您答题较为谨慎，可以适当提高速度',
                        'actions': ['限时练习', '提高解题熟练度', '学习快速解题技巧']
                    },
                    'normal': {
                        'title': '保持良好的答题节奏',
                        'description': '您的答题节奏适中，继续保持',
                        'actions': ['维持当前节奏', '根据题目难度调整时间分配']
                    }
                }
                
                if preferred_pace in pace_advice:
                    advice = pace_advice[preferred_pace]
                    recommendations.append({
                        'type': 'time_management',
                        'priority': 'low',
                        'title': advice['title'],
                        'description': advice['description'],
                        'action_items': advice['actions']
                    })
            
        except Exception as e:
            logger.error(f"生成偏好建议失败: {e}")
        
        return recommendations
    
    @staticmethod
    def _generate_behavior_recommendations(behavior_patterns: Dict) -> List[Dict]:
        """
        基于行为模式生成建议
        
        Args:
            behavior_patterns: 行为模式数据
            
        Returns:
            建议列表
        """
        recommendations = []
        
        try:
            learning_style = behavior_patterns.get('learning_style', 'balanced')
            motivation_level = behavior_patterns.get('motivation_level', 'medium')
            
            # 基于学习风格的建议
            style_advice = {
                'systematic': {
                    'title': '发挥系统性学习优势',
                    'description': '您具有很好的系统性学习能力，建议制定详细的学习计划',
                    'actions': ['制定长期学习规划', '按计划执行', '定期总结反思']
                },
                'adaptive': {
                    'title': '利用适应性强的优势',
                    'description': '您的适应能力很强，可以尝试多样化的学习方法',
                    'actions': ['尝试不同学习方法', '根据效果调整策略', '保持学习的灵活性']
                },
                'persistent': {
                    'title': '发挥坚持性优势',
                    'description': '您有很好的坚持性，适合攻克难题',
                    'actions': ['挑战困难题目', '深入研究问题', '不轻易放弃']
                },
                'exploratory': {
                    'title': '引导探索性学习',
                    'description': '您喜欢探索，建议在有指导的情况下进行学习',
                    'actions': ['寻求学习指导', '制定基本框架', '在框架内自由探索']
                }
            }
            
            if learning_style in style_advice:
                advice = style_advice[learning_style]
                recommendations.append({
                    'type': 'learning_style',
                    'priority': 'medium',
                    'title': advice['title'],
                    'description': advice['description'],
                    'action_items': advice['actions']
                })
            
            # 基于动机水平的建议
            if motivation_level == 'low':
                recommendations.append({
                    'type': 'motivation_boost',
                    'priority': 'high',
                    'title': '提升学习动机',
                    'description': '建议通过设定小目标和奖励机制来提升学习动机',
                    'action_items': [
                        '设定短期可达成的目标',
                        '完成目标后给自己奖励',
                        '寻找学习伙伴互相鼓励'
                    ]
                })
            
        except Exception as e:
            logger.error(f"生成行为建议失败: {e}")
        
        return recommendations
    
    @staticmethod
    def _generate_mastery_recommendations(knowledge_mastery: Dict) -> List[Dict]:
        """
        基于知识掌握情况生成建议
        
        Args:
            knowledge_mastery: 知识掌握数据
            
        Returns:
            建议列表
        """
        recommendations = []
        
        try:
            # 针对薄弱知识点的建议
            distribution = knowledge_mastery.get('mastery_distribution', {})
            poor_count = distribution.get('poor', 0)
            
            if poor_count > 0:
                recommendations.append({
                    'type': 'weakness_improvement',
                    'priority': 'high',
                    'title': '重点攻克薄弱知识点',
                    'description': f'您有{poor_count}个知识点掌握不够理想，需要重点加强',
                    'action_items': [
                        '识别具体的薄弱知识点',
                        '制定针对性的复习计划',
                        '多做相关练习题',
                        '寻求老师或同学的帮助'
                    ]
                })
            
            # 针对下降知识点的建议
            declining_points = knowledge_mastery.get('declining_points', [])
            if declining_points:
                recommendations.append({
                    'type': 'retention_improvement',
                    'priority': 'medium',
                    'title': '防止知识遗忘',
                    'description': f'有{len(declining_points)}个知识点出现掌握度下降，需要及时复习',
                    'action_items': [
                        '定期复习下降的知识点',
                        '使用间隔重复学习法',
                        '将知识点与实际应用结合'
                    ]
                })
            
        except Exception as e:
            logger.error(f"生成掌握度建议失败: {e}")
        
        return recommendations
    
    @staticmethod
    def _generate_forgetting_recommendations(forgetting_params: Dict) -> List[Dict]:
        """
        基于遗忘曲线生成建议
        
        Args:
            forgetting_params: 遗忘曲线参数
            
        Returns:
            建议列表
        """
        recommendations = []
        
        try:
            optimal_interval = forgetting_params.get('optimal_review_interval', 7)
            decay_rate = forgetting_params.get('decay_rate', 0.1)
            
            if decay_rate > 0.2:  # 遗忘较快
                recommendations.append({
                    'type': 'review_frequency',
                    'priority': 'medium',
                    'title': '增加复习频率',
                    'description': '您的遗忘速度较快，建议增加复习频率',
                    'action_items': [
                        f'每{max(1, optimal_interval//2)}天复习一次',
                        '使用记忆卡片等工具',
                        '采用多种感官记忆方法'
                    ]
                })
            else:
                recommendations.append({
                    'type': 'review_optimization',
                    'priority': 'low',
                    'title': '优化复习计划',
                    'description': f'建议每{optimal_interval}天进行一次复习',
                    'action_items': [
                        f'制定{optimal_interval}天的复习周期',
                        '重点复习薄弱知识点',
                        '结合实际应用加深记忆'
                    ]
                })
            
        except Exception as e:
            logger.error(f"生成遗忘建议失败: {e}")
        
        return recommendations
    
    @staticmethod
    def _calculate_overall_level(ability_scores: Dict) -> str:
        """
        计算整体学习水平
        
        Args:
            ability_scores: 能力分析结果
            
        Returns:
            学习水平等级
        """
        try:
            if not ability_scores or 'overall' not in ability_scores:
                return 'intermediate'
            
            overall_ability = ability_scores['overall'].get('mean', 0)
            
            if overall_ability >= 1.5:
                return 'advanced'
            elif overall_ability >= 0.5:
                return 'intermediate'
            elif overall_ability >= -0.5:
                return 'basic'
            else:
                return 'beginner'
                
        except Exception as e:
            logger.error(f"计算整体水平失败: {e}")
            return 'intermediate'
    
    @staticmethod
    def get_profile_summary(user_id: str, subject_id: str) -> Dict:
        """
        获取学习画像摘要
        
        Args:
            user_id: 用户ID
            subject_id: 学科ID
            
        Returns:
            学习画像摘要
        """
        try:
            profile = LearningProfile.query.filter_by(
                user_id=user_id,
                subject_id=subject_id
            ).first()
            
            if not profile:
                return {}
            
            summary = {
                'overall_level': profile.overall_level,
                'total_diagnoses': profile.total_diagnoses,
                'last_diagnosis_date': profile.last_diagnosis_date.isoformat() if profile.last_diagnosis_date else None,
                'learning_style': profile.behavior_patterns.get('learning_style', 'balanced') if profile.behavior_patterns else 'balanced',
                'motivation_level': profile.behavior_patterns.get('motivation_level', 'medium') if profile.behavior_patterns else 'medium',
                'top_recommendations': profile.learning_recommendations[:3] if profile.learning_recommendations else [],
                'mastery_overview': {
                    'overall_mastery': profile.knowledge_mastery.get('overall_mastery', 0) if profile.knowledge_mastery else 0,
                    'strong_areas': len(profile.knowledge_mastery.get('improving_points', [])) if profile.knowledge_mastery else 0,
                    'weak_areas': len(profile.knowledge_mastery.get('declining_points', [])) if profile.knowledge_mastery else 0
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"获取学习画像摘要失败: {e}")
            return {}
    
    @staticmethod
    def get_or_create_profile(user_id: str, subject_id: str) -> LearningProfile:
        """
        获取或创建学习画像
        
        Args:
            user_id: 用户ID
            subject_id: 学科ID
            
        Returns:
            学习画像对象
        """
        try:
            profile = LearningProfile.query.filter_by(
                user_id=user_id,
                subject_id=subject_id
            ).first()
            
            if not profile:
                profile = LearningProfile(
                    user_id=user_id,
                    subject_id=subject_id,
                    overall_level='intermediate',
                    ability_scores={},
                    learning_preferences={},
                    behavior_patterns={},
                    knowledge_mastery={},
                    forgetting_curve_params={},
                    learning_recommendations=[]
                )
                db.session.add(profile)
                db.session.commit()
            
            return profile
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"获取或创建学习画像失败: {e}")
            raise