#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 业务服务 - mistake_service.py

Description:
    错题服务，提供错题分析和推荐功能。

Author: Chang Xinglong
Date: 2025-08-30
Version: 1.0.0
License: Apache License 2.0
"""


from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import joinedload

from models.mistake import (
    MistakeRecord, MistakeReviewSession, MistakePattern, TutoringSession,
    MistakeType, MistakeLevel
)
from models.question import Question
from models.knowledge import KnowledgePoint
from models.user import User
from services.llm_service import LLMService
from utils.database import db
from utils.logger import get_logger

logger = get_logger(__name__)

class MistakeService:
    """
    错题管理服务
    
    提供错题记录、分析、复习和模式识别功能
    """
    
    def __init__(self):
        self.llm_service = LLMService()
    
    def create_mistake_record(self, user_id: int, question_id: int, 
                            user_answer: str, correct_answer: str,
                            auto_analyze: bool = True) -> Optional[MistakeRecord]:
        """
        创建错题记录
        
        Args:
            user_id: 用户ID
            question_id: 题目ID
            user_answer: 用户答案
            correct_answer: 正确答案
            auto_analyze: 是否自动分析错误
        
        Returns:
            创建的错题记录
        """
        try:
            # 检查题目是否存在
            question = Question.query.get(question_id)
            if not question:
                logger.error(f"题目不存在: {question_id}")
                return None
            
            # 检查是否已存在相同错题记录
            existing_record = MistakeRecord.query.filter_by(
                user_id=user_id,
                question_id=question_id,
                is_archived=False
            ).first()
            
            if existing_record:
                # 更新现有记录
                existing_record.user_answer = user_answer
                existing_record.updated_time = datetime.utcnow()
                existing_record.is_resolved = False
                db.session.commit()
                
                if auto_analyze:
                    self._analyze_mistake(existing_record)
                
                return existing_record
            
            # 创建新的错题记录
            mistake_record = MistakeRecord(
                user_id=user_id,
                question_id=question_id,
                knowledge_point_id=question.knowledge_point_id,
                user_answer=user_answer,
                correct_answer=correct_answer
            )
            
            db.session.add(mistake_record)
            db.session.commit()
            
            # 自动分析错误
            if auto_analyze:
                self._analyze_mistake(mistake_record)
            
            # 更新错误模式
            self._update_mistake_patterns(user_id, mistake_record)
            
            logger.info(f"创建错题记录成功: {mistake_record.id}")
            return mistake_record
            
        except Exception as e:
            logger.error(f"创建错题记录失败: {str(e)}")
            db.session.rollback()
            return None
    
    def _analyze_mistake(self, mistake_record: MistakeRecord) -> bool:
        """
        分析错误类型和原因
        
        Args:
            mistake_record: 错题记录
        
        Returns:
            是否分析成功
        """
        try:
            question = mistake_record.question
            if not question:
                return False
            
            # 构建分析提示词
            prompt = self._build_mistake_analysis_prompt(
                question.content,
                question.options if hasattr(question, 'options') else None,
                mistake_record.correct_answer,
                mistake_record.user_answer,
                question.explanation if hasattr(question, 'explanation') else None
            )
            
            # 调用LLM分析
            analysis_result = self.llm_service.generate_content(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.3
            )
            
            if analysis_result and analysis_result.get('success'):
                analysis_data = self._parse_mistake_analysis(analysis_result['content'])
                
                # 更新错题记录
                mistake_record.mistake_type = MistakeType(analysis_data.get('mistake_type', 'concept_error'))
                mistake_record.mistake_level = MistakeLevel(analysis_data.get('mistake_level', 'medium'))
                mistake_record.error_analysis = analysis_data.get('error_analysis', '')
                mistake_record.solution_steps = analysis_data.get('solution_steps', [])
                mistake_record.key_concepts = analysis_data.get('key_concepts', [])
                mistake_record.improvement_suggestions = analysis_data.get('improvement_suggestions', [])
                
                # 计算优先级分数
                mistake_record.calculate_priority_score()
                
                # 设置下次复习时间
                mistake_record.next_review_time = datetime.utcnow() + timedelta(days=1)
                
                db.session.commit()
                
                logger.info(f"错误分析完成: {mistake_record.id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"错误分析失败: {str(e)}")
            return False
    
    def _build_mistake_analysis_prompt(self, question_content: str, options: Optional[List],
                                     correct_answer: str, user_answer: str,
                                     explanation: Optional[str] = None) -> str:
        """
        构建错误分析提示词
        """
        prompt = f"""
请分析以下错题，识别错误类型和原因，并提供改进建议。

题目内容：
{question_content}

"""
        
        if options:
            prompt += f"""
选项：
{chr(10).join([f"{chr(65+i)}. {opt}" for i, opt in enumerate(options)])}

"""
        
        prompt += f"""
正确答案：{correct_answer}
用户答案：{user_answer}
"""
        
        if explanation:
            prompt += f"""
题目解析：{explanation}
"""
        
        prompt += """

请按以下JSON格式返回分析结果：
{
    "mistake_type": "错误类型（concept_error/calculation_error/method_error/careless_error/knowledge_gap/logic_error/reading_error/time_pressure）",
    "mistake_level": "错误严重程度（low/medium/high/critical）",
    "error_analysis": "详细的错误分析",
    "solution_steps": ["解题步骤1", "解题步骤2", "..."],
    "key_concepts": ["关键概念1", "关键概念2", "..."],
    "improvement_suggestions": ["改进建议1", "改进建议2", "..."]
}
"""
        
        return prompt
    
    def _parse_mistake_analysis(self, content: str) -> Dict:
        """
        解析错误分析结果
        """
        try:
            import json
            
            # 尝试解析JSON
            if content.strip().startswith('{'):
                return json.loads(content)
            
            # 如果不是JSON格式，尝试提取关键信息
            result = {
                'mistake_type': 'concept_error',
                'mistake_level': 'medium',
                'error_analysis': content,
                'solution_steps': [],
                'key_concepts': [],
                'improvement_suggestions': []
            }
            
            # 简单的关键词匹配来确定错误类型
            content_lower = content.lower()
            if '计算' in content_lower or 'calculation' in content_lower:
                result['mistake_type'] = 'calculation_error'
            elif '方法' in content_lower or 'method' in content_lower:
                result['mistake_type'] = 'method_error'
            elif '粗心' in content_lower or 'careless' in content_lower:
                result['mistake_type'] = 'careless_error'
            elif '知识' in content_lower or 'knowledge' in content_lower:
                result['mistake_type'] = 'knowledge_gap'
            elif '逻辑' in content_lower or 'logic' in content_lower:
                result['mistake_type'] = 'logic_error'
            elif '审题' in content_lower or 'reading' in content_lower:
                result['mistake_type'] = 'reading_error'
            
            return result
            
        except Exception as e:
            logger.error(f"解析错误分析结果失败: {str(e)}")
            return {
                'mistake_type': 'concept_error',
                'mistake_level': 'medium',
                'error_analysis': content,
                'solution_steps': [],
                'key_concepts': [],
                'improvement_suggestions': []
            }
    
    def get_mistake_records(self, user_id: int, filters: Dict = None,
                          page: int = 1, per_page: int = 20) -> Dict:
        """
        获取错题记录列表
        
        Args:
            user_id: 用户ID
            filters: 筛选条件
            page: 页码
            per_page: 每页数量
        
        Returns:
            错题记录列表和分页信息
        """
        try:
            query = MistakeRecord.query.filter_by(user_id=user_id, is_archived=False)
            
            # 添加关联查询
            query = query.options(
                joinedload(MistakeRecord.question),
                joinedload(MistakeRecord.knowledge_point)
            )
            
            # 应用筛选条件
            if filters:
                if filters.get('subject_id'):
                    query = query.join(KnowledgePoint).filter(
                        KnowledgePoint.subject_id == filters['subject_id']
                    )
                
                if filters.get('mistake_type'):
                    query = query.filter(
                        MistakeRecord.mistake_type == MistakeType(filters['mistake_type'])
                    )
                
                if filters.get('mistake_level'):
                    query = query.filter(
                        MistakeRecord.mistake_level == MistakeLevel(filters['mistake_level'])
                    )
                
                if filters.get('is_resolved') is not None:
                    query = query.filter(
                        MistakeRecord.is_resolved == filters['is_resolved']
                    )
                
                if filters.get('review_urgency'):
                    now = datetime.utcnow()
                    if filters['review_urgency'] == 'urgent':
                        query = query.filter(
                            and_(
                                MistakeRecord.next_review_time <= now,
                                MistakeRecord.mistake_level.in_([MistakeLevel.HIGH, MistakeLevel.CRITICAL])
                            )
                        )
                    elif filters['review_urgency'] == 'due':
                        query = query.filter(MistakeRecord.next_review_time <= now)
            
            # 排序
            query = query.order_by(
                desc(MistakeRecord.priority_score),
                MistakeRecord.next_review_time.asc(),
                desc(MistakeRecord.created_time)
            )
            
            # 分页
            pagination = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'records': [record.to_dict() for record in pagination.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next
                }
            }
            
        except Exception as e:
            logger.error(f"获取错题记录失败: {str(e)}")
            return {'records': [], 'pagination': {}}
    
    def review_mistake(self, mistake_id: int, user_id: int,
                      user_answer: str = None, is_correct: bool = None,
                      confidence_level: int = None, response_time: int = None,
                      user_feedback: str = None) -> Optional[MistakeReviewSession]:
        """
        复习错题
        
        Args:
            mistake_id: 错题ID
            user_id: 用户ID
            user_answer: 用户答案
            is_correct: 是否正确
            confidence_level: 信心程度 1-5
            response_time: 响应时间（秒）
            user_feedback: 用户反馈
        
        Returns:
            复习会话记录
        """
        try:
            # 获取错题记录
            mistake_record = MistakeRecord.query.filter_by(
                id=mistake_id, user_id=user_id
            ).first()
            
            if not mistake_record:
                logger.error(f"错题记录不存在: {mistake_id}")
                return None
            
            # 创建复习会话
            review_session = MistakeReviewSession(
                mistake_record_id=mistake_id,
                user_id=user_id,
                user_answer=user_answer,
                is_correct=is_correct,
                confidence_level=confidence_level,
                response_time=response_time,
                user_feedback=user_feedback
            )
            
            # 计算理解程度
            if is_correct is not None:
                understanding_level = self._calculate_understanding_level(
                    is_correct, confidence_level, response_time
                )
                review_session.understanding_level = understanding_level
            
            db.session.add(review_session)
            
            # 更新错题记录
            mistake_record.review_count += 1
            mistake_record.last_review_time = datetime.utcnow()
            
            # 更新掌握程度
            if review_session.understanding_level is not None:
                # 使用指数移动平均更新掌握程度
                alpha = 0.3  # 学习率
                mistake_record.mastery_level = (
                    alpha * review_session.understanding_level + 
                    (1 - alpha) * mistake_record.mastery_level
                )
            
            # 更新下次复习时间
            self._update_next_review_time(mistake_record, review_session)
            
            # 检查是否已解决
            if mistake_record.mastery_level >= 0.8 and mistake_record.review_count >= 3:
                mistake_record.is_resolved = True
                mistake_record.resolved_time = datetime.utcnow()
            
            # 重新计算优先级
            mistake_record.calculate_priority_score()
            
            db.session.commit()
            
            logger.info(f"错题复习完成: {mistake_id}")
            return review_session
            
        except Exception as e:
            logger.error(f"错题复习失败: {str(e)}")
            db.session.rollback()
            return None
    
    def _calculate_understanding_level(self, is_correct: bool, 
                                     confidence_level: int = None,
                                     response_time: int = None) -> float:
        """
        计算理解程度
        """
        base_score = 1.0 if is_correct else 0.0
        
        # 信心程度调整
        if confidence_level is not None:
            confidence_factor = confidence_level / 5.0
            if is_correct:
                base_score = base_score * (0.7 + 0.3 * confidence_factor)
            else:
                base_score = base_score + 0.2 * confidence_factor
        
        # 响应时间调整（假设合理时间为60秒）
        if response_time is not None and is_correct:
            if response_time <= 30:
                base_score = min(1.0, base_score * 1.1)
            elif response_time > 120:
                base_score = base_score * 0.9
        
        return max(0.0, min(1.0, base_score))
    
    def _update_next_review_time(self, mistake_record: MistakeRecord,
                               review_session: MistakeReviewSession):
        """
        更新下次复习时间（基于间隔重复算法）
        """
        base_intervals = [1, 3, 7, 14, 30, 60]  # 基础间隔（天）
        
        # 根据表现调整间隔
        if review_session.understanding_level is not None:
            if review_session.understanding_level >= 0.8:
                # 表现良好，延长间隔
                interval_index = min(len(base_intervals) - 1, mistake_record.review_count)
                interval = base_intervals[interval_index]
            elif review_session.understanding_level >= 0.6:
                # 表现一般，保持间隔
                interval_index = min(len(base_intervals) - 1, max(0, mistake_record.review_count - 1))
                interval = base_intervals[interval_index]
            else:
                # 表现不佳，缩短间隔
                interval = 1
        else:
            # 默认间隔
            interval = 3
        
        # 根据错误严重程度调整
        if mistake_record.mistake_level == MistakeLevel.CRITICAL:
            interval = max(1, interval // 2)
        elif mistake_record.mistake_level == MistakeLevel.HIGH:
            interval = max(1, int(interval * 0.7))
        
        mistake_record.next_review_time = datetime.utcnow() + timedelta(days=interval)
    
    def _update_mistake_patterns(self, user_id: int, mistake_record: MistakeRecord):
        """
        更新错误模式
        """
        try:
            # 基于错误类型的模式
            pattern_type = f"mistake_type_{mistake_record.mistake_type.value}"
            pattern = MistakePattern.query.filter_by(
                user_id=user_id,
                pattern_type=pattern_type
            ).first()
            
            if pattern:
                pattern.update_frequency()
                if mistake_record.id not in pattern.example_mistakes:
                    pattern.example_mistakes.append(mistake_record.id)
            else:
                pattern = MistakePattern(
                    user_id=user_id,
                    pattern_type=pattern_type,
                    pattern_description=f"经常出现{mistake_record.mistake_type.value}类型的错误",
                    related_knowledge_points=[mistake_record.knowledge_point_id],
                    related_mistake_types=[mistake_record.mistake_type.value],
                    example_mistakes=[mistake_record.id]
                )
                db.session.add(pattern)
            
            # 基于知识点的模式
            kp_pattern_type = f"knowledge_point_{mistake_record.knowledge_point_id}"
            kp_pattern = MistakePattern.query.filter_by(
                user_id=user_id,
                pattern_type=kp_pattern_type
            ).first()
            
            if kp_pattern:
                kp_pattern.update_frequency()
            else:
                knowledge_point = mistake_record.knowledge_point
                if knowledge_point:
                    kp_pattern = MistakePattern(
                        user_id=user_id,
                        pattern_type=kp_pattern_type,
                        pattern_description=f"在{knowledge_point.name}知识点上经常出错",
                        related_knowledge_points=[mistake_record.knowledge_point_id],
                        example_mistakes=[mistake_record.id]
                    )
                    db.session.add(kp_pattern)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"更新错误模式失败: {str(e)}")
    
    def get_mistake_statistics(self, user_id: int, days: int = 30) -> Dict:
        """
        获取错题统计信息
        
        Args:
            user_id: 用户ID
            days: 统计天数
        
        Returns:
            统计信息
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # 基础统计
            total_mistakes = MistakeRecord.query.filter_by(
                user_id=user_id, is_archived=False
            ).count()
            
            recent_mistakes = MistakeRecord.query.filter(
                and_(
                    MistakeRecord.user_id == user_id,
                    MistakeRecord.created_time >= start_date,
                    MistakeRecord.is_archived == False
                )
            ).count()
            
            resolved_mistakes = MistakeRecord.query.filter_by(
                user_id=user_id, is_resolved=True, is_archived=False
            ).count()
            
            # 错误类型分布
            mistake_type_stats = db.session.query(
                MistakeRecord.mistake_type,
                func.count(MistakeRecord.id).label('count')
            ).filter_by(
                user_id=user_id, is_archived=False
            ).group_by(MistakeRecord.mistake_type).all()
            
            # 错误严重程度分布
            mistake_level_stats = db.session.query(
                MistakeRecord.mistake_level,
                func.count(MistakeRecord.id).label('count')
            ).filter_by(
                user_id=user_id, is_archived=False
            ).group_by(MistakeRecord.mistake_level).all()
            
            # 复习统计
            total_reviews = MistakeReviewSession.query.filter_by(user_id=user_id).count()
            
            recent_reviews = MistakeReviewSession.query.filter(
                and_(
                    MistakeReviewSession.user_id == user_id,
                    MistakeReviewSession.review_time >= start_date
                )
            ).count()
            
            # 平均掌握程度
            avg_mastery = db.session.query(
                func.avg(MistakeRecord.mastery_level)
            ).filter_by(
                user_id=user_id, is_archived=False
            ).scalar() or 0.0
            
            return {
                'total_mistakes': total_mistakes,
                'recent_mistakes': recent_mistakes,
                'resolved_mistakes': resolved_mistakes,
                'resolution_rate': resolved_mistakes / max(1, total_mistakes),
                'mistake_type_distribution': {
                    stat.mistake_type.value if stat.mistake_type else 'unknown': stat.count 
                    for stat in mistake_type_stats
                },
                'mistake_level_distribution': {
                    stat.mistake_level.value if stat.mistake_level else 'unknown': stat.count 
                    for stat in mistake_level_stats
                },
                'total_reviews': total_reviews,
                'recent_reviews': recent_reviews,
                'average_mastery_level': float(avg_mastery),
                'improvement_trend': self._calculate_improvement_trend(user_id, days)
            }
            
        except Exception as e:
            logger.error(f"获取错题统计失败: {str(e)}")
            return {}
    
    def _calculate_improvement_trend(self, user_id: int, days: int) -> List[Dict]:
        """
        计算改进趋势
        """
        try:
            # 按周统计改进情况
            weeks = days // 7
            trend_data = []
            
            for week in range(weeks):
                start_date = datetime.utcnow() - timedelta(days=(week + 1) * 7)
                end_date = datetime.utcnow() - timedelta(days=week * 7)
                
                # 该周新增错题数
                new_mistakes = MistakeRecord.query.filter(
                    and_(
                        MistakeRecord.user_id == user_id,
                        MistakeRecord.created_time >= start_date,
                        MistakeRecord.created_time < end_date,
                        MistakeRecord.is_archived == False
                    )
                ).count()
                
                # 该周解决错题数
                resolved_mistakes = MistakeRecord.query.filter(
                    and_(
                        MistakeRecord.user_id == user_id,
                        MistakeRecord.resolved_time >= start_date,
                        MistakeRecord.resolved_time < end_date
                    )
                ).count()
                
                # 该周复习次数
                reviews = MistakeReviewSession.query.filter(
                    and_(
                        MistakeReviewSession.user_id == user_id,
                        MistakeReviewSession.review_time >= start_date,
                        MistakeReviewSession.review_time < end_date
                    )
                ).count()
                
                trend_data.append({
                    'week': f"第{weeks - week}周",
                    'new_mistakes': new_mistakes,
                    'resolved_mistakes': resolved_mistakes,
                    'reviews': reviews,
                    'net_improvement': resolved_mistakes - new_mistakes
                })
            
            return list(reversed(trend_data))
            
        except Exception as e:
            logger.error(f"计算改进趋势失败: {str(e)}")
            return []
    
    def get_mistake_patterns(self, user_id: int) -> List[Dict]:
        """
        获取错误模式
        
        Args:
            user_id: 用户ID
        
        Returns:
            错误模式列表
        """
        try:
            patterns = MistakePattern.query.filter_by(
                user_id=user_id, is_active=True
            ).order_by(
                desc(MistakePattern.confidence_score),
                desc(MistakePattern.frequency)
            ).all()
            
            return [pattern.to_dict() for pattern in patterns]
            
        except Exception as e:
            logger.error(f"获取错误模式失败: {str(e)}")
            return []
    
    def get_review_recommendations(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        获取复习推荐
        
        Args:
            user_id: 用户ID
            limit: 推荐数量限制
        
        Returns:
            推荐的错题列表
        """
        try:
            now = datetime.utcnow()
            
            # 获取需要复习的错题
            query = MistakeRecord.query.filter(
                and_(
                    MistakeRecord.user_id == user_id,
                    MistakeRecord.is_resolved == False,
                    MistakeRecord.is_archived == False,
                    or_(
                        MistakeRecord.next_review_time <= now,
                        MistakeRecord.next_review_time.is_(None)
                    )
                )
            ).options(
                joinedload(MistakeRecord.question),
                joinedload(MistakeRecord.knowledge_point)
            ).order_by(
                desc(MistakeRecord.priority_score),
                MistakeRecord.next_review_time.asc()
            ).limit(limit)
            
            records = query.all()
            
            recommendations = []
            for record in records:
                recommendations.append({
                    **record.to_dict(),
                    'review_urgency': record.get_review_urgency(),
                    'difficulty_assessment': record.get_difficulty_assessment(),
                    'days_since_last_review': (
                        (now - record.last_review_time).days 
                        if record.last_review_time else None
                    )
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"获取复习推荐失败: {str(e)}")
            return []
    
    def archive_mistake(self, mistake_id: int, user_id: int) -> bool:
        """
        归档错题
        
        Args:
            mistake_id: 错题ID
            user_id: 用户ID
        
        Returns:
            是否成功
        """
        try:
            mistake_record = MistakeRecord.query.filter_by(
                id=mistake_id, user_id=user_id
            ).first()
            
            if not mistake_record:
                return False
            
            mistake_record.is_archived = True
            mistake_record.updated_time = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"错题归档成功: {mistake_id}")
            return True
            
        except Exception as e:
            logger.error(f"错题归档失败: {str(e)}")
            db.session.rollback()
            return False
    
    def batch_create_mistakes(self, user_id: int, mistakes_data: List[Dict]) -> Dict:
        """
        批量创建错题记录
        
        Args:
            user_id: 用户ID
            mistakes_data: 错题数据列表
        
        Returns:
            创建结果统计
        """
        created_count = 0
        failed_count = 0
        created_records = []
        
        try:
            for mistake_data in mistakes_data:
                record = self.create_mistake_record(
                    user_id=user_id,
                    question_id=mistake_data.get('question_id'),
                    user_answer=mistake_data.get('user_answer', ''),
                    correct_answer=mistake_data.get('correct_answer', ''),
                    auto_analyze=mistake_data.get('auto_analyze', True)
                )
                
                if record:
                    created_count += 1
                    created_records.append(record)
                else:
                    failed_count += 1
            
            return {
                'created_count': created_count,
                'failed_count': failed_count,
                'total_requested': len(mistakes_data),
                'created_records': [record.to_dict() for record in created_records]
            }
            
        except Exception as e:
            logger.error(f"批量创建错题失败: {str(e)}")
            return {
                'created_count': 0,
                'failed_count': len(mistakes_data),
                'total_requested': len(mistakes_data),
                'created_records': []
            }