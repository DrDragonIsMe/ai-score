#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 业务服务 - strategy_service.py

Description:
    策略服务，提供学习策略推荐和优化。

Author: Chang Xinglong
Date: 2025-08-30
Version: 1.0.0
License: Apache License 2.0
"""


import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy import and_, or_, desc, asc

from models.exam import TimeAllocation, ScoringStrategy, ExamSession
from models.question import Question
from services.llm_service import LLMService
from utils.database import db

class StrategyService:
    """
    策略服务类
    
    提供时间分配和得分策略的创建、管理和优化功能
    """
    
    def __init__(self):
        self.llm_service = LLMService()
    
    # ==================== 时间分配策略 ====================
    
    def create_time_allocation_strategy(self, user_id: int, strategy_config: Dict) -> TimeAllocation:
        """
        创建时间分配策略
        
        Args:
            user_id: 用户ID
            strategy_config: 策略配置
                - strategy_name: 策略名称
                - strategy_description: 策略描述
                - easy_question_time: 简单题目时间（分钟）
                - medium_question_time: 中等题目时间（分钟）
                - hard_question_time: 困难题目时间（分钟）
                - review_time_percentage: 检查时间百分比
                - buffer_time: 缓冲时间（分钟）
        
        Returns:
            TimeAllocation: 创建的时间分配策略
        """
        time_allocation = TimeAllocation(
            user_id=user_id,
            strategy_name=strategy_config['strategy_name'],
            strategy_description=strategy_config.get('strategy_description', ''),
            easy_question_time=strategy_config.get('easy_question_time', 1.0),
            medium_question_time=strategy_config.get('medium_question_time', 2.0),
            hard_question_time=strategy_config.get('hard_question_time', 3.0),
            review_time_percentage=strategy_config.get('review_time_percentage', 10.0),
            buffer_time=strategy_config.get('buffer_time', 5.0)
        )
        
        # 计算时间分布
        time_allocation.time_distribution = self._calculate_time_distribution(time_allocation)
        
        db.session.add(time_allocation)
        db.session.commit()
        
        return time_allocation
    
    def _calculate_time_distribution(self, time_allocation: TimeAllocation) -> Dict:
        """
        计算时间分布
        
        Args:
            time_allocation: 时间分配策略
        
        Returns:
            Dict: 时间分布
        """
        return {
            'easy_questions': {
                'time_per_question': time_allocation.easy_question_time,
                'percentage': 30  # 假设简单题占30%
            },
            'medium_questions': {
                'time_per_question': time_allocation.medium_question_time,
                'percentage': 50  # 假设中等题占50%
            },
            'hard_questions': {
                'time_per_question': time_allocation.hard_question_time,
                'percentage': 20  # 假设困难题占20%
            },
            'review_time': {
                'percentage': time_allocation.review_time_percentage
            },
            'buffer_time': {
                'minutes': time_allocation.buffer_time
            }
        }
    
    def get_optimal_time_allocation(self, user_id: int, exam_config: Dict) -> Dict:
        """
        获取最优时间分配建议
        
        Args:
            user_id: 用户ID
            exam_config: 考试配置
                - total_time_minutes: 总时间
                - total_questions: 总题数
                - difficulty_distribution: 难度分布
                - subject_id: 科目ID
        
        Returns:
            Dict: 最优时间分配建议
        """
        # 获取用户历史表现数据
        user_performance = self._get_user_performance_data(user_id, exam_config.get('subject_id'))
        
        # 基于历史数据和考试配置生成建议
        recommendation = self._generate_time_allocation_recommendation(
            user_performance, exam_config
        )
        
        return recommendation
    
    def _get_user_performance_data(self, user_id: int, subject_id: Optional[int] = None) -> Dict:
        """
        获取用户历史表现数据
        
        Args:
            user_id: 用户ID
            subject_id: 科目ID
        
        Returns:
            Dict: 用户表现数据
        """
        # 获取最近的考试会话
        query = db.session.query(ExamSession).filter(
            and_(
                ExamSession.user_id == user_id,
                ExamSession.status == 'completed'
            )
        )
        
        if subject_id:
            query = query.filter(ExamSession.subject_id == subject_id)
        
        recent_sessions = query.order_by(desc(ExamSession.created_time)).limit(10).all()
        
        if not recent_sessions:
            return self._get_default_performance_data()
        
        # 计算平均表现
        total_sessions = len(recent_sessions)
        avg_time_efficiency = sum(s.time_efficiency for s in recent_sessions) / total_sessions
        avg_score = sum(s.score_percentage for s in recent_sessions) / total_sessions
        avg_completion_rate = sum(s.get_progress_percentage() for s in recent_sessions) / total_sessions
        
        # 分析各难度题目的表现
        difficulty_performance = self._analyze_difficulty_performance(recent_sessions)
        
        return {
            'average_time_efficiency': avg_time_efficiency,
            'average_score': avg_score,
            'average_completion_rate': avg_completion_rate,
            'difficulty_performance': difficulty_performance,
            'total_sessions': total_sessions
        }
    
    def _get_default_performance_data(self) -> Dict:
        """
        获取默认表现数据（新用户）
        
        Returns:
            Dict: 默认表现数据
        """
        return {
            'average_time_efficiency': 0.7,
            'average_score': 70.0,
            'average_completion_rate': 85.0,
            'difficulty_performance': {
                'easy': {'accuracy': 0.8, 'avg_time': 1.0},
                'medium': {'accuracy': 0.6, 'avg_time': 2.0},
                'hard': {'accuracy': 0.4, 'avg_time': 3.5}
            },
            'total_sessions': 0
        }
    
    def _analyze_difficulty_performance(self, sessions: List[ExamSession]) -> Dict:
        """
        分析各难度题目的表现
        
        Args:
            sessions: 考试会话列表
        
        Returns:
            Dict: 难度表现分析
        """
        difficulty_stats = {
            'easy': {'correct': 0, 'total': 0, 'total_time': 0},
            'medium': {'correct': 0, 'total': 0, 'total_time': 0},
            'hard': {'correct': 0, 'total': 0, 'total_time': 0}
        }
        
        for session in sessions:
            if not session.question_ids:
                continue
            
            # 获取题目信息
            questions = db.session.query(Question).filter(
                Question.id.in_(session.question_ids)
            ).all()
            
            for question in questions:
                # 确定难度级别
                if question.difficulty_score <= 0.3:
                    difficulty = 'easy'
                elif question.difficulty_score <= 0.7:
                    difficulty = 'medium'
                else:
                    difficulty = 'hard'
                
                difficulty_stats[difficulty]['total'] += 1
                
                # 检查答题时间
                question_time = session.question_times.get(str(question.id), 0)
                difficulty_stats[difficulty]['total_time'] += int(question_time)
                
                # 检查是否答对
                user_answer = session.answers.get(str(question.id))
                if user_answer:
                    # 这里简化处理，实际应该调用答案检查逻辑
                    if user_answer.strip().upper() == question.correct_answer.strip().upper():
                        difficulty_stats[difficulty]['correct'] += 1
        
        # 计算平均表现
        performance = {}
        for difficulty, stats in difficulty_stats.items():
            if stats['total'] > 0:
                performance[difficulty] = {
                    'accuracy': stats['correct'] / stats['total'],
                    'avg_time': stats['total_time'] / stats['total'] / 60  # 转换为分钟
                }
            else:
                performance[difficulty] = {
                    'accuracy': 0.5,  # 默认值
                    'avg_time': 2.0   # 默认值
                }
        
        return performance
    
    def _generate_time_allocation_recommendation(self, user_performance: Dict, exam_config: Dict) -> Dict:
        """
        生成时间分配建议
        
        Args:
            user_performance: 用户表现数据
            exam_config: 考试配置
        
        Returns:
            Dict: 时间分配建议
        """
        total_time = exam_config['total_time_minutes']
        total_questions = exam_config['total_questions']
        difficulty_dist = exam_config.get('difficulty_distribution', {
            'easy': 0.3, 'medium': 0.5, 'hard': 0.2
        })
        
        # 基于用户表现调整时间分配
        difficulty_performance = user_performance['difficulty_performance']
        
        # 计算各难度题目的建议时间
        easy_time = max(0.5, difficulty_performance['easy']['avg_time'] * 0.9)  # 略微减少简单题时间
        medium_time = difficulty_performance['medium']['avg_time']
        hard_time = min(5.0, difficulty_performance['hard']['avg_time'] * 1.1)  # 略微增加困难题时间
        
        # 计算题目数量
        easy_count = int(total_questions * difficulty_dist['easy'])
        medium_count = int(total_questions * difficulty_dist['medium'])
        hard_count = total_questions - easy_count - medium_count
        
        # 计算所需时间
        question_time = (easy_count * easy_time + 
                        medium_count * medium_time + 
                        hard_count * hard_time)
        
        # 预留检查和缓冲时间
        review_percentage = 15.0 if user_performance['average_score'] < 70 else 10.0
        buffer_time = 5.0
        
        review_time = total_time * (review_percentage / 100)
        available_question_time = total_time - review_time - buffer_time
        
        # 如果时间不够，按比例调整
        if question_time > available_question_time:
            scale_factor = available_question_time / question_time
            easy_time *= scale_factor
            medium_time *= scale_factor
            hard_time *= scale_factor
        
        return {
            'strategy_name': f"个性化时间分配策略",
            'total_time_minutes': total_time,
            'question_time_allocation': {
                'easy_questions': {
                    'count': easy_count,
                    'time_per_question': round(easy_time, 1),
                    'total_time': round(easy_count * easy_time, 1)
                },
                'medium_questions': {
                    'count': medium_count,
                    'time_per_question': round(medium_time, 1),
                    'total_time': round(medium_count * medium_time, 1)
                },
                'hard_questions': {
                    'count': hard_count,
                    'time_per_question': round(hard_time, 1),
                    'total_time': round(hard_count * hard_time, 1)
                }
            },
            'review_time_minutes': round(review_time, 1),
            'buffer_time_minutes': buffer_time,
            'time_checkpoints': self._generate_time_checkpoints(total_questions, available_question_time),
            'recommendations': self._generate_time_management_tips(user_performance)
        }
    
    def _generate_time_checkpoints(self, total_questions: int, total_time: float) -> List[Dict]:
        """
        生成时间检查点
        
        Args:
            total_questions: 总题数
            total_time: 总时间（分钟）
        
        Returns:
            List[Dict]: 时间检查点列表
        """
        checkpoints = []
        checkpoint_intervals = [0.25, 0.5, 0.75, 1.0]  # 25%, 50%, 75%, 100%
        
        for interval in checkpoint_intervals:
            checkpoint_question = int(total_questions * interval)
            checkpoint_time = total_time * interval
            
            checkpoints.append({
                'progress_percentage': int(interval * 100),
                'target_question': checkpoint_question,
                'target_time_minutes': round(checkpoint_time, 1),
                'message': f"完成第{checkpoint_question}题时，应用时不超过{checkpoint_time:.1f}分钟"
            })
        
        return checkpoints
    
    def _generate_time_management_tips(self, user_performance: Dict) -> List[str]:
        """
        生成时间管理建议
        
        Args:
            user_performance: 用户表现数据
        
        Returns:
            List[str]: 建议列表
        """
        tips = []
        
        if user_performance['average_time_efficiency'] < 0.7:
            tips.append("建议提高答题速度，可以通过限时练习来改善")
        
        if user_performance['average_completion_rate'] < 90:
            tips.append("建议优先完成有把握的题目，避免在难题上花费过多时间")
        
        if user_performance['difficulty_performance']['easy']['accuracy'] < 0.9:
            tips.append("简单题目准确率有待提高，建议仔细审题避免粗心错误")
        
        if user_performance['difficulty_performance']['hard']['avg_time'] > 4:
            tips.append("困难题目用时较长，建议设置单题时间上限，避免影响整体进度")
        
        tips.append("建议预留10-15%的时间用于检查和修改答案")
        tips.append("遇到不确定的题目可以先跳过，完成其他题目后再回来处理")
        
        return tips
    
    # ==================== 得分策略 ====================
    
    def create_scoring_strategy(self, user_id: int, strategy_config: Dict) -> ScoringStrategy:
        """
        创建得分策略
        
        Args:
            user_id: 用户ID
            strategy_config: 策略配置
                - strategy_name: 策略名称
                - strategy_type: 策略类型（conservative, aggressive, balanced）
                - skip_threshold: 跳题阈值
                - guess_threshold: 猜题阈值
                - time_pressure_threshold: 时间压力阈值
                - answer_order_strategy: 答题顺序策略
                - review_strategy: 检查策略
                - risk_tolerance: 风险容忍度
        
        Returns:
            ScoringStrategy: 创建的得分策略
        """
        scoring_strategy = ScoringStrategy(
            user_id=user_id,
            strategy_name=strategy_config['strategy_name'],
            strategy_type=strategy_config.get('strategy_type', 'balanced'),
            skip_threshold=strategy_config.get('skip_threshold', 0.3),
            guess_threshold=strategy_config.get('guess_threshold', 0.5),
            time_pressure_threshold=strategy_config.get('time_pressure_threshold', 0.8),
            answer_order_strategy=strategy_config.get('answer_order_strategy', 'sequential'),
            review_strategy=strategy_config.get('review_strategy', 'uncertain_first'),
            guess_strategy=strategy_config.get('guess_strategy', 'educated_guess'),
            risk_tolerance=strategy_config.get('risk_tolerance', 0.5),
            certainty_threshold=strategy_config.get('certainty_threshold', 0.7)
        )
        
        # 设置题目优先级
        if strategy_config['strategy_type'] == 'conservative':
            scoring_strategy.easy_question_priority = 1
            scoring_strategy.medium_question_priority = 2
            scoring_strategy.hard_question_priority = 3
        elif strategy_config['strategy_type'] == 'aggressive':
            scoring_strategy.easy_question_priority = 3
            scoring_strategy.medium_question_priority = 2
            scoring_strategy.hard_question_priority = 1
        else:  # balanced
            scoring_strategy.easy_question_priority = 1
            scoring_strategy.medium_question_priority = 1
            scoring_strategy.hard_question_priority = 2
        
        # 设置策略参数
        scoring_strategy.strategy_parameters = self._build_strategy_parameters(strategy_config)
        
        db.session.add(scoring_strategy)
        db.session.commit()
        
        return scoring_strategy
    
    def _build_strategy_parameters(self, strategy_config: Dict) -> Dict:
        """
        构建策略参数
        
        Args:
            strategy_config: 策略配置
        
        Returns:
            Dict: 策略参数
        """
        strategy_type = strategy_config.get('strategy_type', 'balanced')
        
        if strategy_type == 'conservative':
            return {
                'focus_on_accuracy': True,
                'avoid_risky_guesses': True,
                'prefer_known_topics': True,
                'time_buffer_percentage': 15,
                'max_time_per_hard_question': 4
            }
        elif strategy_type == 'aggressive':
            return {
                'focus_on_high_scores': True,
                'take_calculated_risks': True,
                'challenge_difficult_questions': True,
                'time_buffer_percentage': 5,
                'max_time_per_hard_question': 6
            }
        else:  # balanced
            return {
                'balance_accuracy_speed': True,
                'moderate_risk_taking': True,
                'adaptive_difficulty': True,
                'time_buffer_percentage': 10,
                'max_time_per_hard_question': 5
            }
    
    def get_optimal_scoring_strategy(self, user_id: int, exam_config: Dict) -> Dict:
        """
        获取最优得分策略建议
        
        Args:
            user_id: 用户ID
            exam_config: 考试配置
        
        Returns:
            Dict: 最优得分策略建议
        """
        # 获取用户历史表现数据
        user_performance = self._get_user_performance_data(user_id, exam_config.get('subject_id'))
        
        # 分析用户特点
        user_profile = self._analyze_user_profile(user_performance)
        
        # 生成策略建议
        strategy_recommendation = self._generate_scoring_strategy_recommendation(
            user_profile, exam_config
        )
        
        return strategy_recommendation
    
    def _analyze_user_profile(self, user_performance: Dict) -> Dict:
        """
        分析用户特点
        
        Args:
            user_performance: 用户表现数据
        
        Returns:
            Dict: 用户特点分析
        """
        profile = {
            'accuracy_focused': user_performance['difficulty_performance']['easy']['accuracy'] > 0.9,
            'speed_focused': user_performance['average_time_efficiency'] > 0.8,
            'risk_averse': user_performance['average_completion_rate'] > 95,
            'strong_in_basics': user_performance['difficulty_performance']['easy']['accuracy'] > 0.85,
            'struggles_with_hard': user_performance['difficulty_performance']['hard']['accuracy'] < 0.5,
            'time_management_issues': user_performance['average_time_efficiency'] < 0.7,
            'consistent_performer': abs(user_performance['average_score'] - 70) < 10
        }
        
        # 确定用户类型
        if profile['accuracy_focused'] and profile['risk_averse']:
            profile['user_type'] = 'conservative'
        elif profile['speed_focused'] and not profile['struggles_with_hard']:
            profile['user_type'] = 'aggressive'
        else:
            profile['user_type'] = 'balanced'
        
        return profile
    
    def _generate_scoring_strategy_recommendation(self, user_profile: Dict, exam_config: Dict) -> Dict:
        """
        生成得分策略建议
        
        Args:
            user_profile: 用户特点分析
            exam_config: 考试配置
        
        Returns:
            Dict: 得分策略建议
        """
        user_type = user_profile['user_type']
        
        if user_type == 'conservative':
            strategy = self._generate_conservative_strategy(user_profile)
        elif user_type == 'aggressive':
            strategy = self._generate_aggressive_strategy(user_profile)
        else:
            strategy = self._generate_balanced_strategy(user_profile)
        
        # 添加通用建议
        strategy['general_tips'] = self._generate_general_scoring_tips(user_profile)
        strategy['exam_specific_tips'] = self._generate_exam_specific_tips(exam_config)
        
        return strategy
    
    def _generate_conservative_strategy(self, user_profile: Dict) -> Dict:
        """
        生成保守型策略
        
        Args:
            user_profile: 用户特点分析
        
        Returns:
            Dict: 保守型策略
        """
        return {
            'strategy_name': '稳健得分策略',
            'strategy_type': 'conservative',
            'core_principles': [
                '优先确保简单题和中等题的准确率',
                '避免在困难题上花费过多时间',
                '谨慎猜题，只在有一定把握时才猜'
            ],
            'answer_order': 'difficulty_ascending',  # 从简单到困难
            'time_allocation': {
                'easy_questions': '快速准确完成',
                'medium_questions': '仔细思考，确保正确',
                'hard_questions': '适度尝试，及时放弃'
            },
            'skip_threshold': 0.2,  # 较低的跳题阈值
            'guess_threshold': 0.6,  # 较高的猜题阈值
            'review_priority': 'uncertain_answers',
            'risk_management': {
                'avoid_blind_guessing': True,
                'focus_on_known_strengths': True,
                'maintain_steady_pace': True
            }
        }
    
    def _generate_aggressive_strategy(self, user_profile: Dict) -> Dict:
        """
        生成进取型策略
        
        Args:
            user_profile: 用户特点分析
        
        Returns:
            Dict: 进取型策略
        """
        return {
            'strategy_name': '进取得分策略',
            'strategy_type': 'aggressive',
            'core_principles': [
                '优先攻克高分值题目',
                '合理利用猜题技巧',
                '在困难题上投入更多时间和精力'
            ],
            'answer_order': 'confidence_descending',  # 按信心度排序
            'time_allocation': {
                'easy_questions': '快速完成，节省时间',
                'medium_questions': '稳扎稳打',
                'hard_questions': '重点攻克，争取高分'
            },
            'skip_threshold': 0.4,  # 较高的跳题阈值
            'guess_threshold': 0.4,  # 较低的猜题阈值
            'review_priority': 'high_value_questions',
            'risk_management': {
                'calculated_risk_taking': True,
                'focus_on_high_rewards': True,
                'adaptive_time_management': True
            }
        }
    
    def _generate_balanced_strategy(self, user_profile: Dict) -> Dict:
        """
        生成平衡型策略
        
        Args:
            user_profile: 用户特点分析
        
        Returns:
            Dict: 平衡型策略
        """
        return {
            'strategy_name': '平衡得分策略',
            'strategy_type': 'balanced',
            'core_principles': [
                '平衡准确率和完成率',
                '合理分配时间和精力',
                '根据实际情况灵活调整'
            ],
            'answer_order': 'sequential',  # 顺序答题
            'time_allocation': {
                'easy_questions': '快速准确',
                'medium_questions': '重点关注',
                'hard_questions': '量力而行'
            },
            'skip_threshold': 0.3,  # 中等跳题阈值
            'guess_threshold': 0.5,  # 中等猜题阈值
            'review_priority': 'time_permitting',
            'risk_management': {
                'moderate_risk_taking': True,
                'balanced_approach': True,
                'flexible_adaptation': True
            }
        }
    
    def _generate_general_scoring_tips(self, user_profile: Dict) -> List[str]:
        """
        生成通用得分建议
        
        Args:
            user_profile: 用户特点分析
        
        Returns:
            List[str]: 建议列表
        """
        tips = []
        
        if user_profile.get('time_management_issues'):
            tips.append("建议制定明确的时间分配计划，并严格执行")
        
        if user_profile.get('struggles_with_hard'):
            tips.append("对于困难题目，建议先完成简单题目再回头处理")
        
        if not user_profile.get('strong_in_basics'):
            tips.append("建议加强基础知识学习，确保简单题目的高准确率")
        
        tips.extend([
            "仔细阅读题目，避免因理解错误而失分",
            "合理利用排除法，提高选择题的正确率",
            "预留时间检查答案，特别是容易出错的题目"
        ])
        
        return tips
    
    def _generate_exam_specific_tips(self, exam_config: Dict) -> List[str]:
        """
        生成考试特定建议
        
        Args:
            exam_config: 考试配置
        
        Returns:
            List[str]: 建议列表
        """
        tips = []
        
        total_time = exam_config.get('total_time_minutes', 120)
        total_questions = exam_config.get('total_questions', 50)
        
        avg_time_per_question = total_time / total_questions if total_questions > 0 else 2
        
        tips.append(f"平均每题建议用时{avg_time_per_question:.1f}分钟")
        
        if total_time >= 120:  # 2小时以上的长考试
            tips.append("考试时间较长，建议合理安排休息，保持注意力集中")
        
        if total_questions >= 100:  # 题目较多
            tips.append("题目数量较多，建议控制单题用时，确保完成所有题目")
        
        exam_type = exam_config.get('exam_type', 'practice')
        if exam_type == 'final':
            tips.append("正式考试，建议保持冷静，发挥正常水平")
        elif exam_type == 'mock':
            tips.append("模拟考试，建议按照正式考试的标准要求自己")
        
        return tips
    
    # ==================== 策略管理 ====================
    
    def get_user_time_allocations(self, user_id: int) -> List[TimeAllocation]:
        """
        获取用户的时间分配策略列表
        
        Args:
            user_id: 用户ID
        
        Returns:
            List[TimeAllocation]: 时间分配策略列表
        """
        return db.session.query(TimeAllocation).filter(
            and_(
                TimeAllocation.user_id == user_id,
                TimeAllocation.is_active == True
            )
        ).order_by(desc(TimeAllocation.created_time)).all()
    
    def get_user_scoring_strategies(self, user_id: int) -> List[ScoringStrategy]:
        """
        获取用户的得分策略列表
        
        Args:
            user_id: 用户ID
        
        Returns:
            List[ScoringStrategy]: 得分策略列表
        """
        return db.session.query(ScoringStrategy).filter(
            and_(
                ScoringStrategy.user_id == user_id,
                ScoringStrategy.is_active == True
            )
        ).order_by(desc(ScoringStrategy.created_time)).all()
    
    def update_strategy_effectiveness(self, strategy_id: int, strategy_type: str, 
                                   exam_session: ExamSession):
        """
        更新策略有效性
        
        Args:
            strategy_id: 策略ID
            strategy_type: 策略类型（'time' 或 'scoring'）
            exam_session: 考试会话
        """
        if strategy_type == 'time':
            strategy = db.session.query(TimeAllocation).get(strategy_id)
            if strategy:
                # 计算时间分配策略的执行度
                adherence_score = self._calculate_time_adherence(strategy, exam_session)
                strategy.adherence_score = adherence_score
                
                # 计算有效性
                effectiveness_score = self._calculate_time_effectiveness(exam_session)
                strategy.effectiveness_score = effectiveness_score
                
        elif strategy_type == 'scoring':
            strategy = db.session.query(ScoringStrategy).get(strategy_id)
            if strategy:
                # 更新使用统计
                strategy.update_statistics(exam_session.total_score, exam_session.max_possible_score)
        
        db.session.commit()
    
    def _calculate_time_adherence(self, time_allocation: TimeAllocation, 
                                 exam_session: ExamSession) -> float:
        """
        计算时间分配策略的执行度
        
        Args:
            time_allocation: 时间分配策略
            exam_session: 考试会话
        
        Returns:
            float: 执行度评分 0-1
        """
        if not exam_session.question_times:
            return 0.0
        
        # 简化计算：比较实际用时与计划用时的差异
        total_planned_time = (
            (time_allocation.easy_question_time or 0) * 0.3 +
            (time_allocation.medium_question_time or 0) * 0.5 +
            (time_allocation.hard_question_time or 0) * 0.2
        ) * exam_session.total_questions
        
        actual_time = sum(int(t) for t in exam_session.question_times.values()) / 60  # 转换为分钟
        
        if total_planned_time == 0:
            return 0.0
        
        # 计算偏差程度
        deviation = abs(actual_time - total_planned_time) / total_planned_time
        adherence_score = max(0.0, 1.0 - deviation)
        
        return adherence_score
    
    def _calculate_time_effectiveness(self, exam_session: ExamSession) -> float:
        """
        计算时间管理的有效性
        
        Args:
            exam_session: 考试会话
        
        Returns:
            float: 有效性评分 0-1
        """
        # 综合考虑时间效率、完成率和得分率
        time_efficiency = exam_session.time_efficiency or 0
        completion_rate = exam_session.get_progress_percentage() / 100
        score_rate = exam_session.score_percentage / 100 if exam_session.score_percentage else 0
        
        # 加权平均
        effectiveness = (time_efficiency * 0.3 + completion_rate * 0.3 + score_rate * 0.4)
        
        return effectiveness
    
    def get_strategy_recommendations(self, user_id: int) -> Dict:
        """
        获取策略优化建议
        
        Args:
            user_id: 用户ID
        
        Returns:
            Dict: 策略建议
        """
        # 获取用户最近的表现数据
        user_performance = self._get_user_performance_data(user_id)
        
        # 分析当前策略的效果
        current_strategies = {
            'time_allocations': self.get_user_time_allocations(user_id),
            'scoring_strategies': self.get_user_scoring_strategies(user_id)
        }
        
        # 生成优化建议
        recommendations = {
            'time_allocation_suggestions': self._generate_time_optimization_suggestions(user_performance),
            'scoring_strategy_suggestions': self._generate_scoring_optimization_suggestions(user_performance),
            'general_improvements': self._generate_general_improvement_suggestions(user_performance)
        }
        
        return recommendations
    
    def _generate_time_optimization_suggestions(self, user_performance: Dict) -> List[str]:
        """
        生成时间分配优化建议
        
        Args:
            user_performance: 用户表现数据
        
        Returns:
            List[str]: 优化建议
        """
        suggestions = []
        
        if user_performance['average_time_efficiency'] < 0.7:
            suggestions.append("建议减少每题平均用时，提高答题速度")
        
        if user_performance['average_completion_rate'] < 90:
            suggestions.append("建议优化时间分配，确保完成更多题目")
        
        difficulty_perf = user_performance['difficulty_performance']
        if difficulty_perf['hard']['avg_time'] > 4:
            suggestions.append("建议限制困难题目的最大用时，避免影响整体进度")
        
        return suggestions
    
    def _generate_scoring_optimization_suggestions(self, user_performance: Dict) -> List[str]:
        """
        生成得分策略优化建议
        
        Args:
            user_performance: 用户表现数据
        
        Returns:
            List[str]: 优化建议
        """
        suggestions = []
        
        if user_performance['average_score'] < 70:
            suggestions.append("建议采用保守策略，重点确保基础题目的准确率")
        elif user_performance['average_score'] > 85:
            suggestions.append("基础扎实，可以尝试更进取的策略，挑战高难度题目")
        
        difficulty_perf = user_performance['difficulty_performance']
        if difficulty_perf['easy']['accuracy'] < 0.9:
            suggestions.append("简单题目准确率有待提高，建议仔细审题")
        
        return suggestions
    
    def _generate_general_improvement_suggestions(self, user_performance: Dict) -> List[str]:
        """
        生成通用改进建议
        
        Args:
            user_performance: 用户表现数据
        
        Returns:
            List[str]: 改进建议
        """
        suggestions = [
            "定期回顾和调整策略，根据实际表现进行优化",
            "多进行模拟练习，熟悉不同类型的考试",
            "保持良好的心态，避免因紧张影响发挥"
        ]
        
        if user_performance['total_sessions'] < 5:
            suggestions.append("建议多参加练习考试，积累经验")
        
        return suggestions