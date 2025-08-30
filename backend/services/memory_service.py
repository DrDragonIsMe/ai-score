#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 业务服务 - memory_service.py

Description:
    记忆服务，实现艾宾浩斯记忆曲线算法。

Author: Chang Xinglong
Date: 2025-01-20
Version: 1.0.0
License: Apache License 2.0
"""


from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import and_, or_, desc
from models.learning import MemoryCard
from models.knowledge import KnowledgePoint
from models.question import Question
from models.user import User
from services.llm_service import LLMService
from utils.logger import get_logger
from utils.database import db
import math
import random

logger = get_logger(__name__)

class MemoryService:
    """
    记忆强化服务类
    
    实现基于艾宾浩斯遗忘曲线的智能复习系统，包括：
    - 动态记忆卡片生成
    - 复习时间计算
    - 记忆强度评估
    - 个性化复习策略
    """
    
    # 艾宾浩斯遗忘曲线参数
    FORGETTING_CURVE_INTERVALS = {
        1: 1,      # 第1次复习：1天后
        2: 2,      # 第2次复习：2天后
        3: 4,      # 第3次复习：4天后
        4: 7,      # 第4次复习：7天后
        5: 15,     # 第5次复习：15天后
        6: 30,     # 第6次复习：30天后
        7: 60,     # 第7次复习：60天后
        8: 120     # 第8次复习：120天后
    }
    
    # 记忆强度等级
    MEMORY_STRENGTH_LEVELS = {
        'very_weak': 0.2,
        'weak': 0.4,
        'medium': 0.6,
        'strong': 0.8,
        'very_strong': 1.0
    }
    
    @staticmethod
    def create_memory_card(user_id: int, knowledge_point_id: int, 
                          question_id: Optional[int] = None,
                          content_type: str = 'concept',
                          custom_content: Optional[Dict[str, Any]] = None) -> MemoryCard:
        """
        创建记忆卡片
        
        Args:
            user_id: 用户ID
            knowledge_point_id: 知识点ID
            question_id: 题目ID（可选）
            content_type: 内容类型（concept/question/formula/example）
            custom_content: 自定义内容
            
        Returns:
            创建的记忆卡片
        """
        try:
            # 检查是否已存在相同的记忆卡片
            existing_card = MemoryCard.query.filter_by(
                user_id=user_id,
                knowledge_point_id=knowledge_point_id,
                question_id=question_id,
                content_type=content_type
            ).first()
            
            if existing_card:
                logger.info(f"记忆卡片已存在: {existing_card.id}")
                return existing_card
            
            # 获取知识点信息
            knowledge_point = KnowledgePoint.query.get(knowledge_point_id)
            if not knowledge_point:
                raise ValueError(f"知识点不存在: {knowledge_point_id}")
            
            # 生成卡片内容
            if custom_content:
                card_content = custom_content
            else:
                card_content = MemoryService._generate_card_content(
                    knowledge_point, question_id, content_type
                )
            
            # 创建记忆卡片
            memory_card = MemoryCard(
                user_id=user_id,
                knowledge_point_id=knowledge_point_id,
                question_id=question_id,
                content_type=content_type,
                front_content=card_content.get('front', ''),
                back_content=card_content.get('back', ''),
                tags=card_content.get('tags', []),
                difficulty_level=card_content.get('difficulty', 3),
                memory_strength=0.0,
                review_count=0,
                last_review_time=None,
                next_review_time=datetime.utcnow() + timedelta(days=1),
                created_time=datetime.utcnow(),
                updated_time=datetime.utcnow()
            )
            
            db.session.add(memory_card)
            db.session.commit()
            
            logger.info(f"创建记忆卡片成功: {memory_card.id}")
            return memory_card
            
        except Exception as e:
            logger.error(f"创建记忆卡片失败: {e}")
            db.session.rollback()
            raise
    
    @staticmethod
    def get_due_cards(user_id: int, subject_id: Optional[int] = None, 
                     limit: int = 20) -> List[MemoryCard]:
        """
        获取需要复习的卡片
        
        Args:
            user_id: 用户ID
            subject_id: 学科ID（可选）
            limit: 返回数量限制
            
        Returns:
            需要复习的卡片列表
        """
        try:
            current_time = datetime.utcnow()
            
            # 构建查询条件
            query = MemoryCard.query.filter(
                and_(
                    MemoryCard.user_id == user_id,
                    MemoryCard.next_review_time <= current_time,
                    MemoryCard.is_active == True
                )
            )
            
            # 如果指定了学科，添加学科过滤
            if subject_id:
                query = query.join(KnowledgePoint).filter(
                    KnowledgePoint.subject_id == subject_id
                )
            
            # 按优先级排序：记忆强度低的优先，然后按到期时间
            due_cards = query.order_by(
                MemoryCard.memory_strength.asc(),
                MemoryCard.next_review_time.asc()
            ).limit(limit).all()
            
            logger.info(f"获取到期卡片: 用户{user_id}, 数量{len(due_cards)}")
            return due_cards
            
        except Exception as e:
            logger.error(f"获取到期卡片失败: {e}")
            return []
    
    @staticmethod
    def review_card(card_id: int, user_id: int, performance: str, 
                   response_time: Optional[int] = None,
                   user_feedback: Optional[str] = None) -> bool:
        """
        复习卡片并更新记忆强度
        
        Args:
            card_id: 卡片ID
            user_id: 用户ID
            performance: 复习表现（excellent/good/fair/poor/again）
            response_time: 响应时间（秒）
            user_feedback: 用户反馈
            
        Returns:
            是否成功
        """
        try:
            # 获取记忆卡片
            memory_card = MemoryCard.query.filter_by(
                id=card_id, user_id=user_id
            ).first()
            
            if not memory_card:
                logger.error(f"记忆卡片不存在: {card_id}")
                return False
            
            # 记录复习记录
            review_record = ReviewRecord(
                memory_card_id=card_id,
                user_id=user_id,
                performance=performance,
                response_time=response_time,
                user_feedback=user_feedback,
                review_time=datetime.utcnow(),
                memory_strength_before=memory_card.memory_strength
            )
            
            # 更新记忆强度和下次复习时间
            new_strength, next_interval = MemoryService._calculate_memory_update(
                memory_card, performance, response_time
            )
            
            memory_card.memory_strength = new_strength
            memory_card.review_count += 1
            memory_card.last_review_time = datetime.utcnow()
            memory_card.next_review_time = datetime.utcnow() + timedelta(days=next_interval)
            memory_card.updated_time = datetime.utcnow()
            
            # 如果记忆强度很高，可以设置为非活跃状态
            if new_strength >= 0.95 and memory_card.review_count >= 5:
                memory_card.is_active = False
            
            review_record.memory_strength_after = new_strength
            
            db.session.add(review_record)
            db.session.commit()
            
            logger.info(f"复习卡片成功: {card_id}, 新强度: {new_strength:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"复习卡片失败: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_review_statistics(user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        获取复习统计信息
        
        Args:
            user_id: 用户ID
            days: 统计天数
            
        Returns:
            统计信息
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # 总卡片数
            total_cards = MemoryCard.query.filter_by(
                user_id=user_id, is_active=True
            ).count()
            
            # 复习记录统计
            review_records = ReviewRecord.query.filter(
                and_(
                    ReviewRecord.user_id == user_id,
                    ReviewRecord.review_time >= start_date
                )
            ).all()
            
            # 按表现分组统计
            performance_stats = {}
            total_reviews = len(review_records)
            
            for record in review_records:
                perf = record.performance
                if perf not in performance_stats:
                    performance_stats[perf] = 0
                performance_stats[perf] += 1
            
            # 计算平均响应时间
            response_times = [r.response_time for r in review_records if r.response_time]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # 到期卡片数
            due_cards_count = len(MemoryService.get_due_cards(user_id))
            
            # 记忆强度分布
            strength_distribution = MemoryService._get_strength_distribution(user_id)
            
            # 学习效率趋势
            efficiency_trend = MemoryService._calculate_efficiency_trend(user_id, days)
            
            return {
                'user_id': user_id,
                'period_days': days,
                'total_cards': total_cards,
                'total_reviews': total_reviews,
                'due_cards': due_cards_count,
                'performance_stats': performance_stats,
                'avg_response_time': round(avg_response_time, 2),
                'strength_distribution': strength_distribution,
                'efficiency_trend': efficiency_trend,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取复习统计失败: {e}")
            return {}
    
    @staticmethod
    def get_personalized_recommendations(user_id: int) -> Dict[str, Any]:
        """
        获取个性化复习建议
        
        Args:
            user_id: 用户ID
            
        Returns:
            个性化建议
        """
        try:
            # 获取用户复习统计
            stats = MemoryService.get_review_statistics(user_id, 14)
            
            # 获取薄弱卡片
            weak_cards = MemoryCard.query.filter(
                and_(
                    MemoryCard.user_id == user_id,
                    MemoryCard.memory_strength < 0.5,
                    MemoryCard.is_active == True
                )
            ).order_by(MemoryCard.memory_strength.asc()).limit(10).all()
            
            # 分析学习模式
            learning_pattern = MemoryService._analyze_learning_pattern(user_id)
            
            # 生成建议
            recommendations = {
                'daily_review_target': MemoryService._calculate_daily_target(user_id),
                'focus_areas': MemoryService._identify_focus_areas(user_id),
                'optimal_review_times': MemoryService._suggest_review_times(user_id),
                'weak_knowledge_points': [
                    {
                        'card_id': card.id,
                        'knowledge_point': card.knowledge_point.name if card.knowledge_point else '',
                        'strength': card.memory_strength,
                        'review_count': card.review_count
                    } for card in weak_cards
                ],
                'learning_pattern': learning_pattern,
                'improvement_suggestions': MemoryService._generate_improvement_suggestions(stats, learning_pattern)
            }
            
            return recommendations
            
        except Exception as e:
            logger.error(f"获取个性化建议失败: {e}")
            return {}
    
    @staticmethod
    def batch_create_cards(user_id: int, knowledge_point_ids: List[int],
                          content_types: List[str] = None) -> List[MemoryCard]:
        """
        批量创建记忆卡片
        
        Args:
            user_id: 用户ID
            knowledge_point_ids: 知识点ID列表
            content_types: 内容类型列表
            
        Returns:
            创建的卡片列表
        """
        try:
            if not content_types:
                content_types = ['concept']
            
            created_cards = []
            
            for kp_id in knowledge_point_ids:
                for content_type in content_types:
                    try:
                        card = MemoryService.create_memory_card(
                            user_id=user_id,
                            knowledge_point_id=kp_id,
                            content_type=content_type
                        )
                        created_cards.append(card)
                    except Exception as e:
                        logger.error(f"创建卡片失败 - 知识点{kp_id}, 类型{content_type}: {e}")
                        continue
            
            logger.info(f"批量创建卡片完成: 用户{user_id}, 成功{len(created_cards)}张")
            return created_cards
            
        except Exception as e:
            logger.error(f"批量创建卡片失败: {e}")
            return []
    
    @staticmethod
    def _generate_card_content(knowledge_point: KnowledgePoint, 
                              question_id: Optional[int],
                              content_type: str) -> Dict[str, Any]:
        """
        生成卡片内容
        
        Args:
            knowledge_point: 知识点
            question_id: 题目ID
            content_type: 内容类型
            
        Returns:
            卡片内容
        """
        try:
            if content_type == 'concept':
                return MemoryService._generate_concept_card(knowledge_point)
            elif content_type == 'question' and question_id:
                return MemoryService._generate_question_card(question_id)
            elif content_type == 'formula':
                return MemoryService._generate_formula_card(knowledge_point)
            elif content_type == 'example':
                return MemoryService._generate_example_card(knowledge_point)
            else:
                # 默认概念卡片
                return MemoryService._generate_concept_card(knowledge_point)
                
        except Exception as e:
            logger.error(f"生成卡片内容失败: {e}")
            return {
                'front': knowledge_point.name,
                'back': knowledge_point.description or '暂无描述',
                'tags': [knowledge_point.subject.name if knowledge_point.subject else ''],
                'difficulty': 3
            }
    
    @staticmethod
    def _generate_concept_card(knowledge_point: KnowledgePoint) -> Dict[str, Any]:
        """
        生成概念卡片
        
        Args:
            knowledge_point: 知识点
            
        Returns:
            卡片内容
        """
        try:
            # 使用LLM生成概念卡片内容
            prompt = f"""
            请为以下知识点生成一张记忆卡片：
            
            知识点名称：{knowledge_point.name}
            知识点描述：{knowledge_point.description or '无'}
            学科：{knowledge_point.subject.name if knowledge_point.subject else '无'}
            
            请生成：
            1. 正面（问题）：一个简洁的问题或提示
            2. 背面（答案）：详细的解释和要点
            3. 标签：相关的关键词标签
            4. 难度等级：1-5（1最简单，5最难）
            
            请以JSON格式返回，包含front、back、tags、difficulty字段。
            """
            
            response = LLMService.generate_content(prompt)
            
            # 解析LLM响应
            import json
            try:
                content = json.loads(response)
                return {
                    'front': content.get('front', knowledge_point.name),
                    'back': content.get('back', knowledge_point.description or ''),
                    'tags': content.get('tags', [knowledge_point.subject.name if knowledge_point.subject else '']),
                    'difficulty': content.get('difficulty', 3)
                }
            except json.JSONDecodeError:
                # 如果解析失败，使用默认内容
                return {
                    'front': f"什么是{knowledge_point.name}？",
                    'back': knowledge_point.description or f"{knowledge_point.name}的相关知识点",
                    'tags': [knowledge_point.subject.name if knowledge_point.subject else ''],
                    'difficulty': 3
                }
                
        except Exception as e:
            logger.error(f"生成概念卡片失败: {e}")
            return {
                'front': f"什么是{knowledge_point.name}？",
                'back': knowledge_point.description or f"{knowledge_point.name}的相关知识点",
                'tags': [knowledge_point.subject.name if knowledge_point.subject else ''],
                'difficulty': 3
            }
    
    @staticmethod
    def _generate_question_card(question_id: int) -> Dict[str, Any]:
        """
        生成题目卡片
        
        Args:
            question_id: 题目ID
            
        Returns:
            卡片内容
        """
        try:
            question = Question.query.get(question_id)
            if not question:
                raise ValueError(f"题目不存在: {question_id}")
            
            return {
                'front': question.content,
                'back': f"答案：{question.correct_answer}\n\n解析：{question.explanation or '暂无解析'}",
                'tags': [kp.name for kp in question.knowledge_points] if question.knowledge_points else [],
                'difficulty': question.difficulty_level or 3
            }
            
        except Exception as e:
            logger.error(f"生成题目卡片失败: {e}")
            return {
                'front': '题目内容获取失败',
                'back': '请检查题目是否存在',
                'tags': [],
                'difficulty': 3
            }
    
    @staticmethod
    def _generate_formula_card(knowledge_point: KnowledgePoint) -> Dict[str, Any]:
        """
        生成公式卡片
        
        Args:
            knowledge_point: 知识点
            
        Returns:
            卡片内容
        """
        try:
            # 使用LLM生成公式卡片
            prompt = f"""
            请为知识点"{knowledge_point.name}"生成一张公式记忆卡片。
            
            如果这个知识点包含重要公式，请生成：
            1. 正面：公式的名称或应用场景
            2. 背面：完整的公式及其说明
            3. 标签：相关概念标签
            4. 难度：1-5
            
            如果不包含公式，请生成相关的重要概念卡片。
            
            请以JSON格式返回。
            """
            
            response = LLMService.generate_content(prompt)
            
            import json
            try:
                content = json.loads(response)
                return content
            except json.JSONDecodeError:
                return {
                    'front': f"{knowledge_point.name}的相关公式",
                    'back': knowledge_point.description or '请查阅相关资料',
                    'tags': [knowledge_point.subject.name if knowledge_point.subject else ''],
                    'difficulty': 4
                }
                
        except Exception as e:
            logger.error(f"生成公式卡片失败: {e}")
            return {
                'front': f"{knowledge_point.name}的相关公式",
                'back': knowledge_point.description or '请查阅相关资料',
                'tags': [knowledge_point.subject.name if knowledge_point.subject else ''],
                'difficulty': 4
            }
    
    @staticmethod
    def _generate_example_card(knowledge_point: KnowledgePoint) -> Dict[str, Any]:
        """
        生成例子卡片
        
        Args:
            knowledge_point: 知识点
            
        Returns:
            卡片内容
        """
        try:
            # 使用LLM生成例子卡片
            prompt = f"""
            请为知识点"{knowledge_point.name}"生成一张例子记忆卡片。
            
            请生成：
            1. 正面：一个具体的例子或应用场景
            2. 背面：例子的详细解释和与知识点的关联
            3. 标签：相关标签
            4. 难度：1-5
            
            请以JSON格式返回。
            """
            
            response = LLMService.generate_content(prompt)
            
            import json
            try:
                content = json.loads(response)
                return content
            except json.JSONDecodeError:
                return {
                    'front': f"{knowledge_point.name}的应用例子",
                    'back': knowledge_point.description or '请查阅相关例子',
                    'tags': [knowledge_point.subject.name if knowledge_point.subject else ''],
                    'difficulty': 3
                }
                
        except Exception as e:
            logger.error(f"生成例子卡片失败: {e}")
            return {
                'front': f"{knowledge_point.name}的应用例子",
                'back': knowledge_point.description or '请查阅相关例子',
                'tags': [knowledge_point.subject.name if knowledge_point.subject else ''],
                'difficulty': 3
            }
    
    @staticmethod
    def _calculate_memory_update(memory_card: MemoryCard, performance: str,
                               response_time: Optional[int]) -> Tuple[float, int]:
        """
        计算记忆强度更新和下次复习间隔
        
        Args:
            memory_card: 记忆卡片
            performance: 复习表现
            response_time: 响应时间
            
        Returns:
            (新的记忆强度, 下次复习间隔天数)
        """
        try:
            current_strength = memory_card.memory_strength
            review_count = memory_card.review_count + 1
            
            # 基于表现的强度调整
            performance_adjustments = {
                'again': -0.3,      # 完全不记得
                'poor': -0.15,      # 记得很少
                'fair': 0.0,        # 勉强记得
                'good': 0.15,       # 记得较好
                'excellent': 0.25   # 完全记得
            }
            
            strength_change = performance_adjustments.get(performance, 0.0)
            
            # 响应时间调整（如果提供）
            if response_time:
                # 响应时间越短，记忆越牢固
                if response_time <= 3:
                    strength_change += 0.05
                elif response_time <= 10:
                    strength_change += 0.02
                elif response_time >= 30:
                    strength_change -= 0.05
            
            # 计算新的记忆强度
            new_strength = max(0.0, min(1.0, current_strength + strength_change))
            
            # 基于记忆强度和复习次数计算下次复习间隔
            if performance in ['again', 'poor']:
                # 表现差，缩短间隔
                next_interval = 1
            else:
                # 基础间隔
                base_interval = MemoryService.FORGETTING_CURVE_INTERVALS.get(
                    min(review_count, 8), 120
                )
                
                # 根据记忆强度调整间隔
                strength_multiplier = 0.5 + new_strength
                next_interval = max(1, int(base_interval * strength_multiplier))
            
            return new_strength, next_interval
            
        except Exception as e:
            logger.error(f"计算记忆更新失败: {e}")
            return memory_card.memory_strength, 1
    
    @staticmethod
    def _get_strength_distribution(user_id: int) -> Dict[str, int]:
        """
        获取记忆强度分布
        
        Args:
            user_id: 用户ID
            
        Returns:
            强度分布统计
        """
        try:
            cards = MemoryCard.query.filter_by(
                user_id=user_id, is_active=True
            ).all()
            
            distribution = {
                'very_weak': 0,    # 0.0-0.2
                'weak': 0,         # 0.2-0.4
                'medium': 0,       # 0.4-0.6
                'strong': 0,       # 0.6-0.8
                'very_strong': 0   # 0.8-1.0
            }
            
            for card in cards:
                strength = card.memory_strength
                if strength < 0.2:
                    distribution['very_weak'] += 1
                elif strength < 0.4:
                    distribution['weak'] += 1
                elif strength < 0.6:
                    distribution['medium'] += 1
                elif strength < 0.8:
                    distribution['strong'] += 1
                else:
                    distribution['very_strong'] += 1
            
            return distribution
            
        except Exception as e:
            logger.error(f"获取强度分布失败: {e}")
            return {}
    
    @staticmethod
    def _calculate_efficiency_trend(user_id: int, days: int) -> List[Dict[str, Any]]:
        """
        计算学习效率趋势
        
        Args:
            user_id: 用户ID
            days: 统计天数
            
        Returns:
            效率趋势数据
        """
        try:
            # 按天统计复习记录
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # 获取每天的复习记录
            daily_stats = []
            for i in range(days):
                day_start = start_date + timedelta(days=i)
                day_end = day_start + timedelta(days=1)
                
                day_reviews = ReviewRecord.query.filter(
                    and_(
                        ReviewRecord.user_id == user_id,
                        ReviewRecord.review_time >= day_start,
                        ReviewRecord.review_time < day_end
                    )
                ).all()
                
                # 计算当天效率指标
                total_reviews = len(day_reviews)
                good_reviews = len([r for r in day_reviews if r.performance in ['good', 'excellent']])
                efficiency = (good_reviews / total_reviews * 100) if total_reviews > 0 else 0
                
                daily_stats.append({
                    'date': day_start.strftime('%Y-%m-%d'),
                    'total_reviews': total_reviews,
                    'good_reviews': good_reviews,
                    'efficiency_percentage': round(efficiency, 1)
                })
            
            return daily_stats
            
        except Exception as e:
            logger.error(f"计算效率趋势失败: {e}")
            return []
    
    @staticmethod
    def _analyze_learning_pattern(user_id: int) -> Dict[str, Any]:
        """
        分析学习模式
        
        Args:
            user_id: 用户ID
            
        Returns:
            学习模式分析
        """
        try:
            # 获取最近30天的复习记录
            start_date = datetime.utcnow() - timedelta(days=30)
            reviews = ReviewRecord.query.filter(
                and_(
                    ReviewRecord.user_id == user_id,
                    ReviewRecord.review_time >= start_date
                )
            ).all()
            
            if not reviews:
                return {'pattern': 'insufficient_data'}
            
            # 分析复习时间分布
            hour_distribution = {}
            for review in reviews:
                hour = review.review_time.hour
                hour_distribution[hour] = hour_distribution.get(hour, 0) + 1
            
            # 找出最活跃的时间段
            peak_hours = sorted(hour_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # 分析复习频率
            review_dates = set(r.review_time.date() for r in reviews)
            active_days = len(review_dates)
            avg_reviews_per_day = len(reviews) / 30
            
            # 分析表现趋势
            recent_performance = [r.performance for r in reviews[-20:]]  # 最近20次
            good_performance_rate = len([p for p in recent_performance if p in ['good', 'excellent']]) / len(recent_performance) if recent_performance else 0
            
            return {
                'pattern': 'active' if active_days >= 15 else 'irregular',
                'peak_hours': [h[0] for h in peak_hours],
                'active_days_per_month': active_days,
                'avg_reviews_per_day': round(avg_reviews_per_day, 1),
                'good_performance_rate': round(good_performance_rate * 100, 1),
                'consistency_score': min(100, (active_days / 30) * 100)
            }
            
        except Exception as e:
            logger.error(f"分析学习模式失败: {e}")
            return {'pattern': 'unknown'}
    
    @staticmethod
    def _calculate_daily_target(user_id: int) -> int:
        """
        计算每日复习目标
        
        Args:
            user_id: 用户ID
            
        Returns:
            建议的每日复习卡片数
        """
        try:
            # 获取到期卡片数
            due_count = len(MemoryService.get_due_cards(user_id))
            
            # 获取用户历史平均复习量
            recent_reviews = ReviewRecord.query.filter(
                and_(
                    ReviewRecord.user_id == user_id,
                    ReviewRecord.review_time >= datetime.utcnow() - timedelta(days=7)
                )
            ).count()
            
            avg_daily_reviews = recent_reviews / 7
            
            # 基于到期卡片和历史习惯计算目标
            if due_count == 0:
                return max(5, int(avg_daily_reviews))
            elif due_count <= 10:
                return due_count + 5
            else:
                return min(30, due_count + int(avg_daily_reviews))
                
        except Exception as e:
            logger.error(f"计算每日目标失败: {e}")
            return 10
    
    @staticmethod
    def _identify_focus_areas(user_id: int) -> List[Dict[str, Any]]:
        """
        识别需要重点关注的领域
        
        Args:
            user_id: 用户ID
            
        Returns:
            重点关注领域列表
        """
        try:
            # 获取记忆强度低的卡片，按学科分组
            weak_cards = MemoryCard.query.filter(
                and_(
                    MemoryCard.user_id == user_id,
                    MemoryCard.memory_strength < 0.4,
                    MemoryCard.is_active == True
                )
            ).join(KnowledgePoint).all()
            
            # 按学科统计
            subject_stats = {}
            for card in weak_cards:
                if card.knowledge_point and card.knowledge_point.subject:
                    subject_name = card.knowledge_point.subject.name
                    if subject_name not in subject_stats:
                        subject_stats[subject_name] = {
                            'subject_name': subject_name,
                            'weak_cards_count': 0,
                            'avg_strength': 0,
                            'knowledge_points': set()
                        }
                    
                    subject_stats[subject_name]['weak_cards_count'] += 1
                    subject_stats[subject_name]['avg_strength'] += card.memory_strength
                    if card.knowledge_point:
                        subject_stats[subject_name]['knowledge_points'].add(card.knowledge_point.name)
            
            # 计算平均强度并排序
            focus_areas = []
            for subject, stats in subject_stats.items():
                if stats['weak_cards_count'] > 0:
                    stats['avg_strength'] /= stats['weak_cards_count']
                    stats['knowledge_points'] = list(stats['knowledge_points'])
                    focus_areas.append(stats)
            
            # 按薄弱程度排序
            focus_areas.sort(key=lambda x: (x['weak_cards_count'], -x['avg_strength']), reverse=True)
            
            return focus_areas[:5]  # 返回前5个重点领域
            
        except Exception as e:
            logger.error(f"识别重点领域失败: {e}")
            return []
    
    @staticmethod
    def _suggest_review_times(user_id: int) -> List[str]:
        """
        建议最佳复习时间
        
        Args:
            user_id: 用户ID
            
        Returns:
            建议的复习时间段
        """
        try:
            # 分析用户的历史复习时间
            pattern = MemoryService._analyze_learning_pattern(user_id)
            peak_hours = pattern.get('peak_hours', [])
            
            # 基于科学研究的最佳记忆时间
            optimal_hours = [8, 9, 10, 15, 16, 20, 21]  # 上午8-10点，下午3-4点，晚上8-9点
            
            # 结合用户习惯和科学建议
            suggested_times = []
            
            # 优先推荐用户习惯的时间（如果在最佳时间内）
            for hour in peak_hours:
                if hour in optimal_hours:
                    suggested_times.append(f"{hour:02d}:00-{hour+1:02d}:00")
            
            # 如果用户习惯时间不够，补充科学建议的时间
            if len(suggested_times) < 3:
                for hour in optimal_hours:
                    if hour not in peak_hours:
                        suggested_times.append(f"{hour:02d}:00-{hour+1:02d}:00")
                        if len(suggested_times) >= 3:
                            break
            
            return suggested_times[:3]
            
        except Exception as e:
            logger.error(f"建议复习时间失败: {e}")
            return ['08:00-09:00', '15:00-16:00', '20:00-21:00']
    
    @staticmethod
    def _generate_improvement_suggestions(stats: Dict[str, Any], 
                                        pattern: Dict[str, Any]) -> List[str]:
        """
        生成改进建议
        
        Args:
            stats: 复习统计
            pattern: 学习模式
            
        Returns:
            改进建议列表
        """
        suggestions = []
        
        try:
            # 基于复习频率的建议
            if pattern.get('consistency_score', 0) < 50:
                suggestions.append('建议保持更规律的复习习惯，每天至少复习一次')
            
            # 基于表现的建议
            good_rate = pattern.get('good_performance_rate', 0)
            if good_rate < 60:
                suggestions.append('复习效果有待提高，建议放慢复习速度，确保理解每个概念')
            elif good_rate > 85:
                suggestions.append('复习效果很好！可以适当增加新卡片的学习')
            
            # 基于到期卡片数的建议
            due_cards = stats.get('due_cards', 0)
            if due_cards > 50:
                suggestions.append('到期卡片较多，建议优先复习记忆强度最低的卡片')
            elif due_cards == 0:
                suggestions.append('没有到期卡片，可以学习新的知识点或创建新卡片')
            
            # 基于响应时间的建议
            avg_response_time = stats.get('avg_response_time', 0)
            if avg_response_time > 20:
                suggestions.append('平均响应时间较长，建议加强基础概念的理解')
            elif avg_response_time < 5:
                suggestions.append('响应很快！可以尝试更有挑战性的内容')
            
            # 基于学习时间的建议
            peak_hours = pattern.get('peak_hours', [])
            if len(peak_hours) < 2:
                suggestions.append('建议在一天中安排2-3个固定的复习时间段')
            
            # 默认建议
            if not suggestions:
                suggestions.append('继续保持良好的学习习惯，定期复习是记忆的关键')
            
            return suggestions
            
        except Exception as e:
            logger.error(f"生成改进建议失败: {e}")
            return ['建议保持规律的复习习惯，持续学习是成功的关键']