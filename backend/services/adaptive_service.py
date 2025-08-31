#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 业务服务 - adaptive_service.py

Description:
    自适应服务，提供个性化学习适配功能。

Author: Chang Xinglong
Date: 2025-08-30
Version: 1.0.0
License: Apache License 2.0
"""


import math
import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from models.diagnosis import DiagnosisSession, QuestionResponse
from models.knowledge import KnowledgePoint
from utils.database import db
from utils.logger import get_logger

logger = get_logger(__name__)

class AdaptiveService:
    """自适应出题服务"""
    
    @staticmethod
    def calculate_irt_probability(ability: float, difficulty: float, discrimination: float = 1.0) -> float:
        """
        计算IRT模型中答对题目的概率
        
        Args:
            ability: 学生能力值 (theta)
            difficulty: 题目难度值 (b)
            discrimination: 题目区分度 (a)
            
        Returns:
            答对概率 (0-1)
        """
        try:
            exponent = discrimination * (ability - difficulty)
            # 防止数值溢出
            if exponent > 700:
                return 1.0
            elif exponent < -700:
                return 0.0
            
            probability = 1 / (1 + math.exp(-exponent))
            return max(0.0, min(1.0, probability))
        except Exception as e:
            logger.error(f"计算IRT概率失败: {e}")
            return 0.5
    
    @staticmethod
    def update_ability_estimate(session: DiagnosisSession, is_correct: bool, 
                              difficulty: float, discrimination: float = 1.0) -> Tuple[float, float]:
        """
        使用贝叶斯方法更新能力估计
        
        Args:
            session: 诊断会话
            is_correct: 是否答对
            difficulty: 题目难度
            discrimination: 题目区分度
            
        Returns:
            (新的能力估计值, 新的标准误差)
        """
        try:
            current_ability = getattr(session, 'current_ability', 0.0)
            current_se = getattr(session, 'ability_se', 1.0)
            
            # 计算当前概率
            prob = AdaptiveService.calculate_irt_probability(current_ability, difficulty, discrimination)
            
            # 计算信息量 (Fisher Information)
            info = discrimination ** 2 * prob * (1 - prob)
            
            # 更新能力估计 (Maximum Likelihood Estimation)
            if is_correct:
                ability_update = discrimination * (1 - prob) / info if info > 0 else 0
            else:
                ability_update = -discrimination * prob / info if info > 0 else 0
            
            new_ability = current_ability + ability_update
            
            # 更新标准误差
            if info > 0:
                new_se = 1 / math.sqrt(1 / (current_se ** 2) + info)
            else:
                new_se = current_se
            
            # 限制能力值范围
            new_ability = max(-3.0, min(3.0, new_ability))
            new_se = max(0.1, min(2.0, new_se))
            
            return new_ability, new_se
            
        except Exception as e:
            logger.error(f"更新能力估计失败: {e}")
            return getattr(session, 'current_ability', 0.0), getattr(session, 'ability_se', 1.0)
    
    @staticmethod
    def calculate_information(ability: float, difficulty: float, discrimination: float = 1.0) -> float:
        """
        计算题目在给定能力水平下的信息量
        
        Args:
            ability: 学生能力值
            difficulty: 题目难度值
            discrimination: 题目区分度
            
        Returns:
            信息量
        """
        try:
            prob = AdaptiveService.calculate_irt_probability(ability, difficulty, discrimination)
            information = discrimination ** 2 * prob * (1 - prob)
            return information
        except Exception as e:
            logger.error(f"计算信息量失败: {e}")
            return 0.0
    
    @staticmethod
    def select_optimal_difficulty(session: DiagnosisSession, 
                                available_difficulties: List[float]) -> float:
        """
        选择最优难度的题目
        
        Args:
            session: 诊断会话
            available_difficulties: 可用的难度列表
            
        Returns:
            最优难度值
        """
        try:
            current_ability = session.current_ability
            
            # 计算每个难度的信息量
            difficulty_info = []
            for difficulty in available_difficulties:
                info = AdaptiveService.calculate_information(current_ability, difficulty)
                difficulty_info.append((difficulty, info))
            
            # 选择信息量最大的难度
            if difficulty_info:
                optimal_difficulty = max(difficulty_info, key=lambda x: x[1])[0]
                return optimal_difficulty
            else:
                # 如果没有可用难度，返回接近能力值的难度
                return current_ability
                
        except Exception as e:
            logger.error(f"选择最优难度失败: {e}")
            return 0.0
    
    @staticmethod
    def should_continue_testing(session: DiagnosisSession) -> bool:
        """
        判断是否应该继续测试
        
        Args:
            session: 诊断会话
            
        Returns:
            是否继续测试
        """
        try:
            min_questions = getattr(session, 'min_questions', 10)
            max_questions = getattr(session, 'max_questions', 30)
            questions_answered = getattr(session, 'questions_answered', 0)
            ability_se = getattr(session, 'ability_se', 1.0)
            target_precision = getattr(session, 'target_precision', 0.3)
            
            # 检查最小题目数
            if questions_answered < min_questions:
                return True
            
            # 检查最大题目数
            if questions_answered >= max_questions:
                return False
            
            # 检查精度要求
            if ability_se <= target_precision:
                return False
            
            # 检查连续答对/答错情况
            try:
                recent_responses = session.question_responses.order_by(
                    QuestionResponse.created_at.desc()
                ).limit(5).all()
                
                if len(recent_responses) >= 5:
                    all_correct = all(r.is_correct for r in recent_responses)
                    all_incorrect = all(not r.is_correct for r in recent_responses)
                    
                    # 如果连续5题都对或都错，可能需要调整难度范围
                    if all_correct or all_incorrect:
                        return questions_answered < max_questions * 0.8
            except AttributeError:
                pass  # 忽略关系查询错误
            
            return True
            
        except Exception as e:
            logger.error(f"判断是否继续测试失败: {e}")
            return False
    
    @staticmethod
    def get_knowledge_point_priority(session: DiagnosisSession, 
                                   knowledge_points: List[KnowledgePoint]) -> List[Tuple[str, float]]:
        """
        计算知识点的测试优先级
        
        Args:
            session: 诊断会话
            knowledge_points: 知识点列表
            
        Returns:
            (知识点ID, 优先级分数) 的列表，按优先级降序排列
        """
        try:
            priorities = []
            
            # 获取已测试的知识点
            tested_points = set()
            for response in session.question_responses.all():
                tested_points.add(response.knowledge_point_id)
            
            for kp in knowledge_points:
                priority_score = 0.0
                
                # 1. 未测试的知识点优先级更高
                if kp.id not in tested_points:
                    priority_score += 10.0
                
                # 2. 核心知识点优先级更高
                if kp.is_core:
                    priority_score += 5.0
                
                # 3. 根据知识点重要性调整
                if hasattr(kp, 'importance_score'):
                    priority_score += kp.importance_score * 2
                
                # 4. 根据前置知识点的掌握情况调整
                if kp.prerequisites:
                    prerequisite_mastery = AdaptiveService._calculate_prerequisite_mastery(
                        session, kp.prerequisites
                    )
                    priority_score += prerequisite_mastery * 3
                
                # 5. 根据知识点层级调整（基础知识点优先）
                if kp.level == 1:  # 基础层
                    priority_score += 3.0
                elif kp.level == 2:  # 应用层
                    priority_score += 2.0
                elif kp.level == 3:  # 综合层
                    priority_score += 1.0
                
                priorities.append((kp.id, priority_score))
            
            # 按优先级降序排列
            priorities.sort(key=lambda x: x[1], reverse=True)
            return priorities
            
        except Exception as e:
            logger.error(f"计算知识点优先级失败: {e}")
            return [(kp.id, 1.0) for kp in knowledge_points]
    
    @staticmethod
    def _calculate_prerequisite_mastery(session: DiagnosisSession, 
                                      prerequisites: List[str]) -> float:
        """
        计算前置知识点的掌握程度
        
        Args:
            session: 诊断会话
            prerequisites: 前置知识点ID列表
            
        Returns:
            掌握程度 (0-1)
        """
        try:
            if not prerequisites:
                return 1.0
            
            mastery_scores = []
            
            for prereq_id in prerequisites:
                # 获取该前置知识点的答题记录
                responses = session.question_responses.filter_by(
                    knowledge_point_id=prereq_id
                ).all()
                
                if responses:
                    correct_count = sum(1 for r in responses if r.is_correct)
                    mastery_score = correct_count / len(responses)
                    mastery_scores.append(mastery_score)
                else:
                    # 如果没有测试记录，假设掌握程度为中等
                    mastery_scores.append(0.5)
            
            return sum(mastery_scores) / len(mastery_scores) if mastery_scores else 0.5
            
        except Exception as e:
            logger.error(f"计算前置知识点掌握程度失败: {e}")
            return 0.5
    
    @staticmethod
    def adjust_difficulty_range(session: DiagnosisSession) -> Tuple[float, float]:
        """
        根据答题情况动态调整难度范围
        
        Args:
            session: 诊断会话
            
        Returns:
            (最小难度, 最大难度)
        """
        try:
            current_ability = session.current_ability
            ability_se = session.ability_se
            
            # 基础难度范围
            base_range = 1.5
            
            # 根据标准误差调整范围
            if ability_se > 1.0:
                # 标准误差大，扩大搜索范围
                range_multiplier = 1.5
            elif ability_se < 0.3:
                # 标准误差小，缩小搜索范围
                range_multiplier = 0.8
            else:
                range_multiplier = 1.0
            
            adjusted_range = base_range * range_multiplier
            
            min_difficulty = current_ability - adjusted_range
            max_difficulty = current_ability + adjusted_range
            
            # 限制在合理范围内
            min_difficulty = max(-3.0, min_difficulty)
            max_difficulty = min(3.0, max_difficulty)
            
            # 确保最小值小于最大值
            if min_difficulty >= max_difficulty:
                min_difficulty = max_difficulty - 0.5
            
            return min_difficulty, max_difficulty
            
        except Exception as e:
            logger.error(f"调整难度范围失败: {e}")
            return -1.5, 1.5
    
    @staticmethod
    def calculate_exposure_control(question_id: str, session: DiagnosisSession) -> float:
        """
        计算题目曝光控制权重
        
        Args:
            question_id: 题目ID
            session: 诊断会话
            
        Returns:
            曝光控制权重 (0-1，越小表示越不应该选择)
        """
        try:
            # 简化的曝光控制：避免重复选择相同题目
            used_questions = set()
            for response in session.question_responses.all():
                used_questions.add(response.question_id)
            
            if question_id in used_questions:
                return 0.0  # 已经使用过的题目权重为0
            
            # 可以根据题目的历史使用频率进一步调整
            # 这里简化为固定权重
            return 1.0
            
        except Exception as e:
            logger.error(f"计算曝光控制权重失败: {e}")
            return 1.0
    
    @staticmethod
    def generate_adaptive_recommendation(session: DiagnosisSession, 
                                       available_questions: List[Dict]) -> Optional[Dict]:
        """
        生成自适应题目推荐
        
        Args:
            session: 诊断会话
            available_questions: 可用题目列表
            
        Returns:
            推荐的题目信息
        """
        try:
            if not available_questions:
                return None
            
            current_ability = session.current_ability
            
            # 计算每个题目的综合得分
            question_scores = []
            
            for question in available_questions:
                question_id = question.get('id')
                difficulty = question.get('difficulty', 0.0)
                discrimination = question.get('discrimination', 1.0)
                knowledge_point_id = question.get('knowledge_point_id')
                
                # 1. 信息量得分
                info_score = AdaptiveService.calculate_information(
                    current_ability, difficulty, discrimination
                )
                
                # 2. 曝光控制得分
                exposure_score = AdaptiveService.calculate_exposure_control(
                    question_id, session
                )
                
                # 3. 知识点优先级得分（简化版）
                kp_priority_score = 1.0
                if knowledge_point_id:
                    # 检查该知识点是否已充分测试
                    kp_responses = session.question_responses.filter_by(
                        knowledge_point_id=knowledge_point_id
                    ).count()
                    if kp_responses < 2:  # 每个知识点至少测试2题
                        kp_priority_score = 2.0
                
                # 综合得分
                total_score = info_score * exposure_score * kp_priority_score
                
                question_scores.append((question, total_score))
            
            # 选择得分最高的题目
            if question_scores:
                best_question = max(question_scores, key=lambda x: x[1])[0]
                
                # 添加推荐理由
                best_question['recommendation_reason'] = {
                    'target_ability': current_ability,
                    'question_difficulty': best_question.get('difficulty', 0.0),
                    'expected_information': AdaptiveService.calculate_information(
                        current_ability, best_question.get('difficulty', 0.0)
                    ),
                    'selection_strategy': 'maximum_information'
                }
                
                return best_question
            
            return None
            
        except Exception as e:
            logger.error(f"生成自适应推荐失败: {e}")
            return available_questions[0] if available_questions else None
    
    @staticmethod
    def analyze_response_pattern(session: DiagnosisSession) -> Dict:
        """
        分析答题模式
        
        Args:
            session: 诊断会话
            
        Returns:
            答题模式分析结果
        """
        try:
            try:
                responses = session.question_responses.order_by(
                    QuestionResponse.created_at.asc()
                ).all()
            except AttributeError:
                responses = []
            
            if not responses:
                return {}
            
            analysis = {
                'total_questions': len(responses),
                'correct_count': sum(1 for r in responses if r.is_correct),
                'accuracy_rate': 0.0,
                'average_time': 0.0,
                'difficulty_progression': [],
                'ability_progression': [],
                'consistency_score': 0.0,
                'learning_trend': 'stable'
            }
            
            # 计算准确率
            if responses:
                analysis['accuracy_rate'] = analysis['correct_count'] / len(responses)
            
            # 计算平均用时
            total_time = sum(getattr(r, 'time_spent', 0) for r in responses if getattr(r, 'time_spent', 0))
            if responses:
                analysis['average_time'] = total_time / len(responses)
            
            # 分析难度和能力变化趋势
            for i, response in enumerate(responses):
                analysis['difficulty_progression'].append({
                    'question_index': i + 1,
                    'difficulty': getattr(response, 'difficulty_level', 0.0),
                    'is_correct': response.is_correct,
                    'time_spent': getattr(response, 'time_spent', 0)
                })
            
            # 计算一致性得分（基于期望表现与实际表现的差异）
            consistency_scores = []
            current_ability = getattr(session, 'current_ability', 0.0)
            for response in responses:
                expected_prob = AdaptiveService.calculate_irt_probability(
                    current_ability, getattr(response, 'difficulty_level', 0.0)
                )
                actual_result = 1.0 if response.is_correct else 0.0
                consistency_scores.append(1 - abs(expected_prob - actual_result))
            
            if consistency_scores:
                analysis['consistency_score'] = sum(consistency_scores) / len(consistency_scores)
            
            # 分析学习趋势
            if len(responses) >= 5:
                recent_accuracy = sum(1 for r in responses[-5:] if r.is_correct) / 5
                early_accuracy = sum(1 for r in responses[:5] if r.is_correct) / 5
                
                if recent_accuracy > early_accuracy + 0.1:
                    analysis['learning_trend'] = 'improving'
                elif recent_accuracy < early_accuracy - 0.1:
                    analysis['learning_trend'] = 'declining'
                else:
                    analysis['learning_trend'] = 'stable'
            
            return analysis
            
        except Exception as e:
            logger.error(f"分析答题模式失败: {e}")
            return {}