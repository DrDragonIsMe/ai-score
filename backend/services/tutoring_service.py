#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 业务服务 - tutoring_service.py

Description:
    辅导服务，提供智能答疑和学习指导。

Author: Chang Xinglong
Date: 2025-08-31
Version: 1.0.0
License: Apache License 2.0
"""


from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from enum import Enum

from models.mistake import TutoringSession
from models.question import Question
from models.user import User
from services.llm_service import LLMService
from utils.database import db
from utils.logger import get_logger

logger = get_logger(__name__)

class TutoringLevel(Enum):
    """辅导层级"""
    HINT = "hint"  # 提示层
    GUIDANCE = "guidance"  # 引导层
    EXPLANATION = "explanation"  # 解释层
    DEMONSTRATION = "demonstration"  # 演示层

class TutoringService:
    """
    分层解题辅导服务
    
    提供智能化的分层解题辅导，根据学生理解程度动态调整辅导策略
    """
    
    def __init__(self):
        self.llm_service = LLMService()
        
        # 辅导层级配置
        self.tutoring_levels = {
            TutoringLevel.HINT: {
                'name': '提示层',
                'description': '给出关键词提示，引导学生思考',
                'max_attempts': 3
            },
            TutoringLevel.GUIDANCE: {
                'name': '引导层', 
                'description': '提供解题思路和方法指导',
                'max_attempts': 2
            },
            TutoringLevel.EXPLANATION: {
                'name': '解释层',
                'description': '详细解释概念和原理',
                'max_attempts': 2
            },
            TutoringLevel.DEMONSTRATION: {
                'name': '演示层',
                'description': '完整演示解题过程',
                'max_attempts': 1
            }
        }
    
    def start_tutoring_session(self, user_id: int, question_id: int,
                             session_type: str = 'problem_solving') -> Optional[TutoringSession]:
        """
        开始辅导会话
        
        Args:
            user_id: 用户ID
            question_id: 题目ID
            session_type: 会话类型
        
        Returns:
            辅导会话对象
        """
        try:
            # 检查题目是否存在
            question = Question.query.get(question_id)
            if not question:
                logger.error(f"题目不存在: {question_id}")
                return None
            
            # 检查是否已有进行中的会话
            existing_session = TutoringSession.query.filter_by(
                user_id=user_id,
                question_id=question_id,
                status='active'
            ).first()
            
            if existing_session:
                logger.info(f"继续现有辅导会话: {existing_session.id}")
                return existing_session
            
            # 创建新的辅导会话
            session = TutoringSession(
                user_id=user_id,
                question_id=question_id,
                session_type=session_type,
                current_step=1,
                total_steps=self._estimate_total_steps(question)
            )
            
            # 初始化辅导历史
            initial_step = {
                'step': 1,
                'level': TutoringLevel.HINT.value,
                'content': '让我们一起来解决这道题目。请先仔细阅读题目，思考一下解题思路。',
                'timestamp': datetime.utcnow().isoformat(),
                'user_response': None
            }
            session.tutoring_history = [initial_step]
            
            db.session.add(session)
            db.session.commit()
            
            logger.info(f"辅导会话开始: {session.id}")
            return session
            
        except Exception as e:
            logger.error(f"开始辅导会话失败: {str(e)}")
            db.session.rollback()
            return None
    
    def _estimate_total_steps(self, question: Question) -> int:
        """
        估算解题总步骤数
        
        Args:
            question: 题目对象
        
        Returns:
            估算的总步骤数
        """
        # 根据题目难度和类型估算步骤数
        base_steps = 3
        
        if hasattr(question, 'difficulty') and question.difficulty:
            if question.difficulty == 'easy':
                base_steps = 2
            elif question.difficulty == 'medium':
                base_steps = 3
            elif question.difficulty == 'hard':
                base_steps = 4
            elif question.difficulty == 'expert':
                base_steps = 5
        
        # 根据题目内容长度调整
        if hasattr(question, 'content') and question.content:
            content_length = len(question.content)
            if content_length > 500:
                base_steps += 1
            elif content_length > 1000:
                base_steps += 2
        
        return min(8, max(2, base_steps))  # 限制在2-8步之间
    
    def provide_tutoring(self, session_id: int, user_response: str = None,
                        understanding_level: int = None) -> Dict:
        """
        提供分层辅导
        
        Args:
            session_id: 会话ID
            user_response: 用户回应
            understanding_level: 理解程度 1-5
        
        Returns:
            辅导响应
        """
        try:
            session = TutoringSession.query.get(session_id)
            if not session or session.status != 'active':
                return {'success': False, 'message': '会话不存在或已结束'}
            
            # 更新用户回应
            if user_response and session.tutoring_history:
                session.tutoring_history[-1]['user_response'] = user_response
                session.user_responses.append({
                    'step': session.current_step,
                    'response': user_response,
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # 更新理解进度
            if understanding_level is not None:
                session.update_understanding_progress(understanding_level)
            
            # 分析用户理解程度并决定辅导策略
            tutoring_strategy = self._analyze_and_decide_strategy(
                session, user_response, understanding_level
            )
            
            # 生成辅导内容
            tutoring_content = self._generate_tutoring_content(
                session, tutoring_strategy
            )
            
            if not tutoring_content:
                return {'success': False, 'message': '生成辅导内容失败'}
            
            # 添加辅导步骤
            session.add_tutoring_step(
                level=tutoring_strategy['level'],
                content=tutoring_content['content'],
                hints=tutoring_content.get('hints', []),
                examples=tutoring_content.get('examples', [])
            )
            
            # 检查是否需要调整难度
            if tutoring_strategy.get('adjust_difficulty'):
                session.difficulty_adjustments.append({
                    'step': session.current_step,
                    'adjustment': tutoring_strategy['adjust_difficulty'],
                    'reason': tutoring_strategy.get('adjustment_reason', ''),
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # 更新会话状态
            session.current_step += 1
            session.updated_time = datetime.utcnow()
            
            # 检查是否完成
            if self._should_complete_session(session, tutoring_strategy):
                session.complete_session()
            
            db.session.commit()
            
            return {
                'success': True,
                'tutoring_content': tutoring_content,
                'strategy': tutoring_strategy,
                'session_status': {
                    'current_step': session.current_step,
                    'total_steps': session.total_steps,
                    'completion_rate': session.completion_rate,
                    'understanding_progress': session.understanding_progress,
                    'is_completed': session.status == 'completed'
                }
            }
            
        except Exception as e:
            logger.error(f"提供辅导失败: {str(e)}")
            return {'success': False, 'message': f'辅导失败: {str(e)}'}
    
    def _analyze_and_decide_strategy(self, session: TutoringSession,
                                   user_response: str = None,
                                   understanding_level: int = None) -> Dict:
        """
        分析用户状态并决定辅导策略
        
        Args:
            session: 辅导会话
            user_response: 用户回应
            understanding_level: 理解程度
        
        Returns:
            辅导策略
        """
        strategy = {
            'level': TutoringLevel.HINT.value,
            'approach': 'progressive',
            'adjust_difficulty': None,
            'reasoning': ''
        }
        
        try:
            # 获取当前理解程度
            current_understanding = (
                understanding_level if understanding_level is not None 
                else session.understanding_progress[-1] if session.understanding_progress 
                else 3
            )
            
            # 获取历史表现
            avg_understanding = (
                sum(session.understanding_progress) / len(session.understanding_progress)
                if session.understanding_progress else 3
            )
            
            # 决定辅导层级
            if current_understanding >= 4:
                # 理解良好，给予提示即可
                strategy['level'] = TutoringLevel.HINT.value
                strategy['reasoning'] = '学生理解程度良好，提供关键提示引导思考'
            elif current_understanding >= 3:
                # 理解一般，需要引导
                strategy['level'] = TutoringLevel.GUIDANCE.value
                strategy['reasoning'] = '学生需要解题思路指导'
            elif current_understanding >= 2:
                # 理解较差，需要详细解释
                strategy['level'] = TutoringLevel.EXPLANATION.value
                strategy['reasoning'] = '学生需要详细的概念解释'
            else:
                # 理解很差，需要完整演示
                strategy['level'] = TutoringLevel.DEMONSTRATION.value
                strategy['reasoning'] = '学生需要完整的解题演示'
            
            # 分析用户回应质量
            if user_response:
                response_quality = self._analyze_response_quality(
                    user_response, session.question
                )
                
                if response_quality['is_correct']:
                    # 回应正确，可以降低辅导层级
                    if strategy['level'] == TutoringLevel.EXPLANATION.value:
                        strategy['level'] = TutoringLevel.GUIDANCE.value
                    elif strategy['level'] == TutoringLevel.DEMONSTRATION.value:
                        strategy['level'] = TutoringLevel.EXPLANATION.value
                elif response_quality['shows_confusion']:
                    # 显示困惑，提高辅导层级
                    if strategy['level'] == TutoringLevel.HINT.value:
                        strategy['level'] = TutoringLevel.GUIDANCE.value
                    elif strategy['level'] == TutoringLevel.GUIDANCE.value:
                        strategy['level'] = TutoringLevel.EXPLANATION.value
            
            # 检查是否需要调整难度
            if avg_understanding < 2 and session.current_step > 3:
                strategy['adjust_difficulty'] = 'decrease'
                strategy['adjustment_reason'] = '学生持续理解困难，降低难度'
            elif avg_understanding > 4 and session.current_step <= 2:
                strategy['adjust_difficulty'] = 'increase'
                strategy['adjustment_reason'] = '学生理解能力强，可适当提高难度'
            
            return strategy
            
        except Exception as e:
            logger.error(f"分析辅导策略失败: {str(e)}")
            return strategy
    
    def _analyze_response_quality(self, user_response: str, question: Question) -> Dict:
        """
        分析用户回应质量
        
        Args:
            user_response: 用户回应
            question: 题目对象
        
        Returns:
            回应质量分析结果
        """
        try:
            # 构建分析提示词
            prompt = f"""
请分析学生对以下题目的回应质量：

题目：{question.content}
学生回应：{user_response}

请判断：
1. 回应是否正确或部分正确
2. 是否显示出困惑或误解
3. 理解程度如何（1-5分）
4. 需要什么类型的帮助

请以JSON格式返回分析结果：
{{
    "is_correct": true/false,
    "is_partially_correct": true/false,
    "shows_confusion": true/false,
    "understanding_score": 1-5,
    "help_needed": "提示/引导/解释/演示",
    "analysis": "详细分析"
}}
"""
            
            result = self.llm_service.generate_content(
                prompt=prompt,
                max_tokens=500,
                temperature=0.3
            )
            
            if result and result.get('success'):
                try:
                    import json
                    analysis = json.loads(result['content'])
                    return analysis
                except json.JSONDecodeError:
                    pass
            
            # 默认分析结果
            return {
                'is_correct': False,
                'is_partially_correct': False,
                'shows_confusion': True,
                'understanding_score': 2,
                'help_needed': '引导',
                'analysis': '无法分析用户回应'
            }
            
        except Exception as e:
            logger.error(f"分析回应质量失败: {str(e)}")
            return {
                'is_correct': False,
                'is_partially_correct': False,
                'shows_confusion': True,
                'understanding_score': 2,
                'help_needed': '引导',
                'analysis': f'分析失败: {str(e)}'
            }
    
    def _generate_tutoring_content(self, session: TutoringSession,
                                 strategy: Dict) -> Optional[Dict]:
        """
        生成辅导内容
        
        Args:
            session: 辅导会话
            strategy: 辅导策略
        
        Returns:
            辅导内容
        """
        try:
            question = session.question
            level = strategy['level']
            
            # 构建上下文
            context = self._build_tutoring_context(session)
            
            # 根据辅导层级生成不同类型的内容
            if level == TutoringLevel.HINT.value:
                content = self._generate_hint_content(question, context)
            elif level == TutoringLevel.GUIDANCE.value:
                content = self._generate_guidance_content(question, context)
            elif level == TutoringLevel.EXPLANATION.value:
                content = self._generate_explanation_content(question, context)
            elif level == TutoringLevel.DEMONSTRATION.value:
                content = self._generate_demonstration_content(question, context)
            else:
                content = self._generate_hint_content(question, context)
            
            return content
            
        except Exception as e:
            logger.error(f"生成辅导内容失败: {str(e)}")
            return None
    
    def _build_tutoring_context(self, session: TutoringSession) -> str:
        """
        构建辅导上下文
        
        Args:
            session: 辅导会话
        
        Returns:
            上下文字符串
        """
        context_parts = []
        
        # 添加历史对话
        if session.tutoring_history:
            context_parts.append("历史对话：")
            for step in session.tutoring_history[-3:]:  # 只取最近3步
                context_parts.append(f"步骤{step['step']}: {step['content']}")
                if step.get('user_response'):
                    context_parts.append(f"学生回应: {step['user_response']}")
        
        # 添加理解进度
        if session.understanding_progress:
            avg_progress = sum(session.understanding_progress) / len(session.understanding_progress)
            context_parts.append(f"当前理解程度: {avg_progress:.1f}/5")
        
        # 添加使用的提示
        if session.hints_used:
            context_parts.append(f"已使用提示: {len(session.hints_used)}个")
        
        return "\n".join(context_parts)
    
    def _generate_hint_content(self, question: Question, context: str) -> Dict:
        """
        生成提示层内容
        """
        prompt = f"""
作为一名优秀的数学老师，请为以下题目提供关键词提示，引导学生思考：

题目：{question.content}

上下文：{context}

要求：
1. 只给出关键词或短语提示
2. 不要直接给出答案
3. 引导学生思考解题方向
4. 提示要简洁明了

请以JSON格式返回：
{{
    "content": "主要提示内容",
    "hints": ["提示1", "提示2", "提示3"],
    "question": "引导性问题"
}}
"""
        
        result = self.llm_service.generate_content(
            prompt=prompt,
            max_tokens=300,
            temperature=0.4
        )
        
        if result and result.get('success'):
            try:
                import json
                return json.loads(result['content'])
            except json.JSONDecodeError:
                pass
        
        # 默认提示内容
        return {
            'content': '让我们一步步来分析这道题目。请先确定题目要求什么？',
            'hints': ['仔细阅读题目', '确定已知条件', '明确求解目标'],
            'question': '你能告诉我这道题目的关键信息是什么吗？'
        }
    
    def _generate_guidance_content(self, question: Question, context: str) -> Dict:
        """
        生成引导层内容
        """
        prompt = f"""
作为一名优秀的数学老师，请为以下题目提供解题思路指导：

题目：{question.content}

上下文：{context}

要求：
1. 提供解题思路和方法
2. 不要给出具体计算过程
3. 引导学生理解解题逻辑
4. 可以提供相似例子

请以JSON格式返回：
{{
    "content": "主要指导内容",
    "method": "解题方法",
    "steps": ["步骤1", "步骤2", "步骤3"],
    "examples": ["相似例子"]
}}
"""
        
        result = self.llm_service.generate_content(
            prompt=prompt,
            max_tokens=500,
            temperature=0.4
        )
        
        if result and result.get('success'):
            try:
                import json
                return json.loads(result['content'])
            except json.JSONDecodeError:
                pass
        
        # 默认引导内容
        return {
            'content': '这类题目通常需要先分析已知条件，然后选择合适的解题方法。',
            'method': '分析法',
            'steps': ['分析已知条件', '确定解题方法', '逐步求解'],
            'examples': ['类似的题目通常这样解决...']
        }
    
    def _generate_explanation_content(self, question: Question, context: str) -> Dict:
        """
        生成解释层内容
        """
        prompt = f"""
作为一名优秀的数学老师，请详细解释以下题目涉及的概念和原理：

题目：{question.content}

上下文：{context}

要求：
1. 详细解释相关概念
2. 说明解题原理
3. 解释为什么这样解题
4. 可以包含必要的公式

请以JSON格式返回：
{{
    "content": "主要解释内容",
    "concepts": ["概念1", "概念2"],
    "principles": "解题原理",
    "formulas": ["相关公式"]
}}
"""
        
        result = self.llm_service.generate_content(
            prompt=prompt,
            max_tokens=800,
            temperature=0.3
        )
        
        if result and result.get('success'):
            try:
                import json
                return json.loads(result['content'])
            except json.JSONDecodeError:
                pass
        
        # 默认解释内容
        return {
            'content': '让我详细解释一下这道题目涉及的概念和解题原理。',
            'concepts': ['相关概念需要详细解释'],
            'principles': '解题的基本原理是...',
            'formulas': ['相关公式']
        }
    
    def _generate_demonstration_content(self, question: Question, context: str) -> Dict:
        """
        生成演示层内容
        """
        prompt = f"""
作为一名优秀的数学老师，请完整演示以下题目的解题过程：

题目：{question.content}

上下文：{context}

要求：
1. 完整的解题步骤
2. 每步都要有详细说明
3. 包含必要的计算过程
4. 最终给出答案

请以JSON格式返回：
{{
    "content": "完整解题演示",
    "detailed_steps": [
        {{"step": 1, "description": "步骤描述", "calculation": "计算过程"}}
    ],
    "final_answer": "最终答案",
    "verification": "验证过程"
}}
"""
        
        result = self.llm_service.generate_content(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.2
        )
        
        if result and result.get('success'):
            try:
                import json
                return json.loads(result['content'])
            except json.JSONDecodeError:
                pass
        
        # 默认演示内容
        return {
            'content': '让我完整演示这道题目的解题过程。',
            'detailed_steps': [
                {'step': 1, 'description': '分析题目', 'calculation': '确定已知条件'},
                {'step': 2, 'description': '选择方法', 'calculation': '应用相关公式'},
                {'step': 3, 'description': '计算结果', 'calculation': '得出答案'}
            ],
            'final_answer': '需要具体计算',
            'verification': '检验答案的合理性'
        }
    
    def _should_complete_session(self, session: TutoringSession, strategy: Dict) -> bool:
        """
        判断是否应该完成会话
        
        Args:
            session: 辅导会话
            strategy: 当前策略
        
        Returns:
            是否应该完成
        """
        # 达到最大步骤数
        if session.current_step >= session.total_steps:
            return True
        
        # 学生理解程度持续良好
        if (len(session.understanding_progress) >= 3 and 
            all(score >= 4 for score in session.understanding_progress[-3:])):
            return True
        
        # 已经进行了演示层辅导
        if (session.tutoring_history and 
            session.tutoring_history[-1].get('level') == TutoringLevel.DEMONSTRATION.value):
            return True
        
        return False
    
    def get_tutoring_session(self, session_id: int) -> Optional[Dict]:
        """
        获取辅导会话信息
        
        Args:
            session_id: 会话ID
        
        Returns:
            会话信息
        """
        try:
            session = TutoringSession.query.get(session_id)
            if not session:
                return None
            
            return session.to_dict()
            
        except Exception as e:
            logger.error(f"获取辅导会话失败: {str(e)}")
            return None
    
    def get_user_tutoring_sessions(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        获取用户的辅导会话列表
        
        Args:
            user_id: 用户ID
            limit: 限制数量
        
        Returns:
            会话列表
        """
        try:
            sessions = TutoringSession.query.filter_by(
                user_id=user_id
            ).order_by(
                TutoringSession.updated_time.desc()
            ).limit(limit).all()
            
            return [session.to_dict() for session in sessions]
            
        except Exception as e:
            logger.error(f"获取用户辅导会话失败: {str(e)}")
            return []
    
    def end_tutoring_session(self, session_id: int, user_feedback: str = None) -> bool:
        """
        结束辅导会话
        
        Args:
            session_id: 会话ID
            user_feedback: 用户反馈
        
        Returns:
            是否成功
        """
        try:
            session = TutoringSession.query.get(session_id)
            if not session:
                return False
            
            # 完成会话
            session.complete_session()
            
            # 添加用户反馈
            if user_feedback:
                if not session.user_responses:
                    session.user_responses = []
                session.user_responses.append({
                    'type': 'feedback',
                    'content': user_feedback,
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            db.session.commit()
            
            logger.info(f"辅导会话结束: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"结束辅导会话失败: {str(e)}")
            db.session.rollback()
            return False
    
    def get_tutoring_statistics(self, user_id: int, days: int = 30) -> Dict:
        """
        获取辅导统计信息
        
        Args:
            user_id: 用户ID
            days: 统计天数
        
        Returns:
            统计信息
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # 基础统计
            total_sessions = TutoringSession.query.filter_by(user_id=user_id).count()
            
            recent_sessions = TutoringSession.query.filter(
                TutoringSession.user_id == user_id,
                TutoringSession.created_time >= start_date
            ).count()
            
            completed_sessions = TutoringSession.query.filter_by(
                user_id=user_id, status='completed'
            ).count()
            
            # 平均完成率
            avg_completion_rate = db.session.query(
                func.avg(TutoringSession.completion_rate)
            ).filter_by(user_id=user_id).scalar() or 0.0
            
            # 平均理解进度
            sessions_with_progress = TutoringSession.query.filter(
                TutoringSession.user_id == user_id,
                TutoringSession.understanding_progress.isnot(None)
            ).all()
            
            avg_understanding = 0.0
            if sessions_with_progress:
                all_progress = []
                for session in sessions_with_progress:
                    if session.understanding_progress:
                        all_progress.extend(session.understanding_progress)
                
                if all_progress:
                    avg_understanding = sum(all_progress) / len(all_progress)
            
            # 辅导层级使用统计
            level_usage = {level.value: 0 for level in TutoringLevel}
            for session in sessions_with_progress:
                if session.tutoring_history:
                    for step in session.tutoring_history:
                        level = step.get('level')
                        if level in level_usage:
                            level_usage[level] += 1
            
            return {
                'total_sessions': total_sessions,
                'recent_sessions': recent_sessions,
                'completed_sessions': completed_sessions,
                'completion_rate': completed_sessions / max(1, total_sessions),
                'average_completion_rate': float(avg_completion_rate),
                'average_understanding': float(avg_understanding),
                'tutoring_level_usage': level_usage,
                'improvement_trend': self._calculate_tutoring_trend(user_id, days)
            }
            
        except Exception as e:
            logger.error(f"获取辅导统计失败: {str(e)}")
            return {}
    
    def _calculate_tutoring_trend(self, user_id: int, days: int) -> List[Dict]:
        """
        计算辅导趋势
        
        Args:
            user_id: 用户ID
            days: 统计天数
        
        Returns:
            趋势数据
        """
        try:
            weeks = days // 7
            trend_data = []
            
            for week in range(weeks):
                start_date = datetime.utcnow() - timedelta(days=(week + 1) * 7)
                end_date = datetime.utcnow() - timedelta(days=week * 7)
                
                # 该周的辅导会话
                week_sessions = TutoringSession.query.filter(
                    TutoringSession.user_id == user_id,
                    TutoringSession.created_time >= start_date,
                    TutoringSession.created_time < end_date
                ).all()
                
                # 统计该周数据
                session_count = len(week_sessions)
                completed_count = sum(1 for s in week_sessions if s.status == 'completed')
                
                avg_understanding = 0.0
                if week_sessions:
                    all_progress = []
                    for session in week_sessions:
                        if session.understanding_progress:
                            all_progress.extend(session.understanding_progress)
                    
                    if all_progress:
                        avg_understanding = sum(all_progress) / len(all_progress)
                
                trend_data.append({
                    'week': f"第{weeks - week}周",
                    'sessions': session_count,
                    'completed': completed_count,
                    'completion_rate': completed_count / max(1, session_count),
                    'avg_understanding': avg_understanding
                })
            
            return list(reversed(trend_data))
            
        except Exception as e:
            logger.error(f"计算辅导趋势失败: {str(e)}")
            return []