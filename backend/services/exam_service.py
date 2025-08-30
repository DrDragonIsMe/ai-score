# -*- coding: utf-8 -*-
"""
应试优化服务

提供限时模拟、时间分配、得分策略等功能
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.orm import sessionmaker

from models.exam import (
    ExamSession, TimeAllocation, ScoringStrategy, ExamAnalytics,
    ExamType, ExamStatus, DifficultyLevel
)
from models.question import Question
from models.knowledge import Subject
from services.llm_service import LLMService
from utils.database import db

class ExamService:
    """
    应试优化服务类
    
    提供考试会话管理、时间分配、得分策略等功能
    """
    
    def __init__(self):
        self.llm_service = LLMService()
    
    def create_exam_session(self, user_id: int, exam_config: Dict) -> ExamSession:
        """
        创建考试会话
        
        Args:
            user_id: 用户ID
            exam_config: 考试配置
                - title: 考试标题
                - description: 考试描述
                - exam_type: 考试类型
                - subject_id: 科目ID
                - total_questions: 题目总数
                - total_time_minutes: 总时间（分钟）
                - difficulty_level: 难度等级
                - question_filters: 题目筛选条件
        
        Returns:
            ExamSession: 创建的考试会话
        """
        # 创建考试会话
        exam_session = ExamSession(
            user_id=user_id,
            title=exam_config['title'],
            description=exam_config.get('description', ''),
            exam_type=exam_config.get('exam_type', ExamType.PRACTICE.value),
            subject_id=exam_config.get('subject_id'),
            total_questions=exam_config['total_questions'],
            total_time_minutes=exam_config['total_time_minutes'],
            difficulty_level=exam_config.get('difficulty_level', DifficultyLevel.MEDIUM.value),
            scheduled_start_time=exam_config.get('scheduled_start_time')
        )
        
        # 计算每题平均时间
        if exam_session.total_questions > 0:
            exam_session.time_per_question = exam_session.total_time_minutes / exam_session.total_questions
        
        # 选择题目
        questions = self._select_questions(
            subject_id=exam_config.get('subject_id'),
            total_questions=exam_config['total_questions'],
            difficulty_level=exam_config.get('difficulty_level'),
            filters=exam_config.get('question_filters', {})
        )
        
        exam_session.question_ids = [q.id for q in questions]
        exam_session.max_possible_score = sum(q.score for q in questions)
        
        db.session.add(exam_session)
        db.session.commit()
        
        return exam_session
    
    def _select_questions(self, subject_id: Optional[int], total_questions: int, 
                         difficulty_level: str, filters: Dict) -> List[Question]:
        """
        选择考试题目
        
        Args:
            subject_id: 科目ID
            total_questions: 题目总数
            difficulty_level: 难度等级
            filters: 筛选条件
        
        Returns:
            List[Question]: 选中的题目列表
        """
        query = db.session.query(Question)
        
        # 科目筛选
        if subject_id:
            query = query.filter(Question.subject_id == subject_id)
        
        # 难度筛选
        if difficulty_level != 'mixed':
            difficulty_map = {
                DifficultyLevel.EASY.value: (0.0, 0.3),
                DifficultyLevel.MEDIUM.value: (0.3, 0.7),
                DifficultyLevel.HARD.value: (0.7, 0.9),
                DifficultyLevel.EXPERT.value: (0.9, 1.0)
            }
            if difficulty_level in difficulty_map:
                min_diff, max_diff = difficulty_map[difficulty_level]
                query = query.filter(
                    and_(
                        Question.difficulty_score >= min_diff,
                        Question.difficulty_score <= max_diff
                    )
                )
        
        # 其他筛选条件
        if filters.get('question_types'):
            query = query.filter(Question.question_type.in_(filters['question_types']))
        
        if filters.get('knowledge_point_ids'):
            query = query.filter(Question.knowledge_point_id.in_(filters['knowledge_point_ids']))
        
        # 获取所有符合条件的题目
        all_questions = query.all()
        
        # 如果题目数量不足，返回所有题目
        if len(all_questions) <= total_questions:
            return all_questions
        
        # 智能选题：确保难度分布合理
        if difficulty_level == 'mixed':
            return self._select_mixed_difficulty_questions(all_questions, total_questions)
        else:
            # 随机选择
            return random.sample(all_questions, total_questions)
    
    def _select_mixed_difficulty_questions(self, questions: List[Question], total_count: int) -> List[Question]:
        """
        选择混合难度的题目
        
        Args:
            questions: 候选题目列表
            total_count: 需要选择的题目数量
        
        Returns:
            List[Question]: 选中的题目列表
        """
        # 按难度分组
        easy_questions = [q for q in questions if q.difficulty_score <= 0.3]
        medium_questions = [q for q in questions if 0.3 < q.difficulty_score <= 0.7]
        hard_questions = [q for q in questions if q.difficulty_score > 0.7]
        
        # 计算各难度题目数量（30% 简单，50% 中等，20% 困难）
        easy_count = int(total_count * 0.3)
        medium_count = int(total_count * 0.5)
        hard_count = total_count - easy_count - medium_count
        
        selected_questions = []
        
        # 选择简单题目
        if easy_questions and easy_count > 0:
            selected_questions.extend(
                random.sample(easy_questions, min(easy_count, len(easy_questions)))
            )
        
        # 选择中等题目
        if medium_questions and medium_count > 0:
            selected_questions.extend(
                random.sample(medium_questions, min(medium_count, len(medium_questions)))
            )
        
        # 选择困难题目
        if hard_questions and hard_count > 0:
            selected_questions.extend(
                random.sample(hard_questions, min(hard_count, len(hard_questions)))
            )
        
        # 如果选中的题目不足，从剩余题目中补充
        if len(selected_questions) < total_count:
            remaining_questions = [q for q in questions if q not in selected_questions]
            additional_count = total_count - len(selected_questions)
            if remaining_questions:
                selected_questions.extend(
                    random.sample(remaining_questions, min(additional_count, len(remaining_questions)))
                )
        
        return selected_questions
    
    def start_exam(self, exam_session_id: int, user_id: int) -> Dict:
        """
        开始考试
        
        Args:
            exam_session_id: 考试会话ID
            user_id: 用户ID
        
        Returns:
            Dict: 考试开始信息
        """
        exam_session = db.session.query(ExamSession).filter(
            and_(
                ExamSession.id == exam_session_id,
                ExamSession.user_id == user_id
            )
        ).first()
        
        if not exam_session:
            raise ValueError("考试会话不存在")
        
        if exam_session.status != ExamStatus.SCHEDULED.value:
            raise ValueError(f"考试状态不正确，当前状态：{exam_session.status}")
        
        # 开始考试
        exam_session.start_exam()
        db.session.commit()
        
        # 获取第一题
        first_question = self._get_question_by_index(exam_session, 0)
        
        return {
            'exam_session': exam_session.to_dict(),
            'current_question': first_question,
            'total_questions': exam_session.total_questions,
            'remaining_time': exam_session.get_remaining_time()
        }
    
    def submit_answer(self, exam_session_id: int, user_id: int, question_id: int, 
                     answer: str, time_spent: int, confidence: float = 0.5) -> Dict:
        """
        提交答案
        
        Args:
            exam_session_id: 考试会话ID
            user_id: 用户ID
            question_id: 题目ID
            answer: 用户答案
            time_spent: 用时（秒）
            confidence: 信心度 0-1
        
        Returns:
            Dict: 提交结果
        """
        exam_session = db.session.query(ExamSession).filter(
            and_(
                ExamSession.id == exam_session_id,
                ExamSession.user_id == user_id
            )
        ).first()
        
        if not exam_session:
            raise ValueError("考试会话不存在")
        
        if exam_session.status != ExamStatus.IN_PROGRESS.value:
            raise ValueError(f"考试状态不正确，当前状态：{exam_session.status}")
        
        # 检查是否超时
        if exam_session.is_expired():
            exam_session.status = ExamStatus.EXPIRED.value
            db.session.commit()
            raise ValueError("考试时间已到")
        
        # 添加答案
        exam_session.add_answer(question_id, answer, time_spent)
        
        # 评分
        question = db.session.query(Question).get(question_id)
        if question:
            is_correct = self._check_answer(question, answer)
            if is_correct:
                exam_session.correct_answers += 1
                exam_session.total_score += question.score
            else:
                exam_session.wrong_answers += 1
        
        # 更新当前题目索引
        if exam_session.current_question_index < len(exam_session.question_ids) - 1:
            exam_session.current_question_index += 1
            next_question = self._get_question_by_index(exam_session, exam_session.current_question_index)
        else:
            next_question = None
            # 如果是最后一题，自动完成考试
            if exam_session.completed_questions >= exam_session.total_questions:
                exam_session.complete_exam()
        
        db.session.commit()
        
        result = {
            'is_correct': is_correct if question else False,
            'score_earned': question.score if question and is_correct else 0,
            'total_score': exam_session.total_score,
            'remaining_time': exam_session.get_remaining_time(),
            'progress': exam_session.get_progress_percentage(),
            'next_question': next_question,
            'is_completed': exam_session.status == ExamStatus.COMPLETED.value
        }
        
        return result
    
    def _check_answer(self, question: Question, user_answer: str) -> bool:
        """
        检查答案是否正确
        
        Args:
            question: 题目对象
            user_answer: 用户答案
        
        Returns:
            bool: 是否正确
        """
        if question.question_type == 'single_choice':
            return user_answer.strip().upper() == question.correct_answer.strip().upper()
        elif question.question_type == 'multiple_choice':
            # 多选题需要完全匹配
            user_choices = set(user_answer.strip().upper().split(','))
            correct_choices = set(question.correct_answer.strip().upper().split(','))
            return user_choices == correct_choices
        elif question.question_type == 'true_false':
            return user_answer.strip().lower() == question.correct_answer.strip().lower()
        else:
            # 主观题使用LLM评分
            return self._evaluate_subjective_answer(question, user_answer)
    
    def _evaluate_subjective_answer(self, question: Question, user_answer: str) -> bool:
        """
        评估主观题答案
        
        Args:
            question: 题目对象
            user_answer: 用户答案
        
        Returns:
            bool: 是否正确（得分是否超过60%）
        """
        try:
            prompt = f"""
            请评估以下主观题的答案：
            
            题目：{question.content}
            标准答案：{question.correct_answer}
            学生答案：{user_answer}
            
            请给出评分（0-100分）和评价，返回JSON格式：
            {{
                "score": 85,
                "is_correct": true,
                "evaluation": "答案基本正确，要点完整..."
            }}
            """
            
            response = self.llm_service.generate_response(prompt)
            result = json.loads(response)
            
            return result.get('score', 0) >= 60
        except Exception as e:
            print(f"主观题评分失败: {e}")
            return False
    
    def _get_question_by_index(self, exam_session: ExamSession, index: int) -> Optional[Dict]:
        """
        根据索引获取题目
        
        Args:
            exam_session: 考试会话
            index: 题目索引
        
        Returns:
            Optional[Dict]: 题目信息
        """
        if index >= len(exam_session.question_ids):
            return None
        
        question_id = exam_session.question_ids[index]
        question = db.session.query(Question).get(question_id)
        
        if not question:
            return None
        
        return {
            'id': question.id,
            'content': question.content,
            'question_type': question.question_type,
            'options': question.options,
            'difficulty_score': question.difficulty_score,
            'score': question.score,
            'index': index + 1,
            'total': len(exam_session.question_ids)
        }
    
    def pause_exam(self, exam_session_id: int, user_id: int) -> Dict:
        """
        暂停考试
        
        Args:
            exam_session_id: 考试会话ID
            user_id: 用户ID
        
        Returns:
            Dict: 暂停结果
        """
        exam_session = db.session.query(ExamSession).filter(
            and_(
                ExamSession.id == exam_session_id,
                ExamSession.user_id == user_id
            )
        ).first()
        
        if not exam_session:
            raise ValueError("考试会话不存在")
        
        if exam_session.status != ExamStatus.IN_PROGRESS.value:
            raise ValueError(f"考试状态不正确，当前状态：{exam_session.status}")
        
        exam_session.pause_exam()
        db.session.commit()
        
        return {
            'status': exam_session.status,
            'remaining_time': exam_session.get_remaining_time(),
            'message': '考试已暂停'
        }
    
    def resume_exam(self, exam_session_id: int, user_id: int) -> Dict:
        """
        恢复考试
        
        Args:
            exam_session_id: 考试会话ID
            user_id: 用户ID
        
        Returns:
            Dict: 恢复结果
        """
        exam_session = db.session.query(ExamSession).filter(
            and_(
                ExamSession.id == exam_session_id,
                ExamSession.user_id == user_id
            )
        ).first()
        
        if not exam_session:
            raise ValueError("考试会话不存在")
        
        if exam_session.status != ExamStatus.PAUSED.value:
            raise ValueError(f"考试状态不正确，当前状态：{exam_session.status}")
        
        # 检查是否超时
        if exam_session.is_expired():
            exam_session.status = ExamStatus.EXPIRED.value
            db.session.commit()
            raise ValueError("考试时间已到")
        
        exam_session.resume_exam()
        db.session.commit()
        
        # 获取当前题目
        current_question = self._get_question_by_index(exam_session, exam_session.current_question_index)
        
        return {
            'status': exam_session.status,
            'current_question': current_question,
            'remaining_time': exam_session.get_remaining_time(),
            'message': '考试已恢复'
        }
    
    def complete_exam(self, exam_session_id: int, user_id: int) -> Dict:
        """
        完成考试
        
        Args:
            exam_session_id: 考试会话ID
            user_id: 用户ID
        
        Returns:
            Dict: 考试结果
        """
        exam_session = db.session.query(ExamSession).filter(
            and_(
                ExamSession.id == exam_session_id,
                ExamSession.user_id == user_id
            )
        ).first()
        
        if not exam_session:
            raise ValueError("考试会话不存在")
        
        if exam_session.status not in [ExamStatus.IN_PROGRESS.value, ExamStatus.PAUSED.value]:
            raise ValueError(f"考试状态不正确，当前状态：{exam_session.status}")
        
        # 完成考试
        exam_session.complete_exam()
        
        # 计算未答题数
        exam_session.skipped_questions = exam_session.total_questions - exam_session.completed_questions
        
        db.session.commit()
        
        # 生成分析报告
        analytics = self._generate_exam_analytics(exam_session)
        
        return {
            'exam_session': exam_session.to_dict(),
            'analytics': analytics.to_dict() if analytics else None,
            'message': '考试已完成'
        }
    
    def _generate_exam_analytics(self, exam_session: ExamSession) -> Optional[ExamAnalytics]:
        """
        生成考试分析报告
        
        Args:
            exam_session: 考试会话
        
        Returns:
            Optional[ExamAnalytics]: 分析报告
        """
        try:
            analytics = ExamAnalytics(
                exam_session_id=exam_session.id,
                user_id=exam_session.user_id
            )
            
            # 时间分析
            analytics.time_analysis = self._analyze_time_usage(exam_session)
            analytics.time_efficiency_score = exam_session.time_efficiency
            analytics.time_management_suggestions = self._generate_time_suggestions(exam_session)
            
            # 答题分析
            analytics.answer_pattern_analysis = self._analyze_answer_patterns(exam_session)
            analytics.accuracy_by_difficulty = self._analyze_accuracy_by_difficulty(exam_session)
            
            # 策略分析
            analytics.strategy_effectiveness = self._analyze_strategy_effectiveness(exam_session)
            
            # 改进建议
            strengths, weaknesses = self._identify_strengths_weaknesses(exam_session)
            analytics.strengths = strengths
            analytics.weaknesses = weaknesses
            analytics.improvement_priorities = self._generate_improvement_priorities(weaknesses)
            analytics.specific_recommendations = self._generate_specific_recommendations(exam_session)
            
            db.session.add(analytics)
            db.session.commit()
            
            return analytics
        except Exception as e:
            print(f"生成考试分析失败: {e}")
            return None
    
    def _analyze_time_usage(self, exam_session: ExamSession) -> Dict:
        """
        分析时间使用情况
        
        Args:
            exam_session: 考试会话
        
        Returns:
            Dict: 时间分析结果
        """
        if not exam_session.question_times:
            return {}
        
        question_times = [int(t) for t in exam_session.question_times.values()]
        
        return {
            'total_time_used': sum(question_times),
            'average_time_per_question': sum(question_times) / len(question_times) if question_times else 0,
            'fastest_question_time': min(question_times) if question_times else 0,
            'slowest_question_time': max(question_times) if question_times else 0,
            'time_variance': self._calculate_variance(question_times),
            'questions_over_average': len([t for t in question_times if t > exam_session.time_per_question * 60]) if exam_session.time_per_question else 0
        }
    
    def _calculate_variance(self, values: List[float]) -> float:
        """
        计算方差
        
        Args:
            values: 数值列表
        
        Returns:
            float: 方差
        """
        if not values:
            return 0.0
        
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)
    
    def _generate_time_suggestions(self, exam_session: ExamSession) -> List[str]:
        """
        生成时间管理建议
        
        Args:
            exam_session: 考试会话
        
        Returns:
            List[str]: 建议列表
        """
        suggestions = []
        
        if exam_session.time_efficiency < 0.7:
            suggestions.append("建议提高答题速度，可以通过更多练习来熟悉题型")
        
        if exam_session.average_time_per_question > exam_session.time_per_question * 1.2:
            suggestions.append("平均答题时间超出预期，建议合理分配时间")
        
        if exam_session.skipped_questions > exam_session.total_questions * 0.1:
            suggestions.append("跳题较多，建议先完成有把握的题目，再回头处理难题")
        
        return suggestions
    
    def _analyze_answer_patterns(self, exam_session: ExamSession) -> Dict:
        """
        分析答题模式
        
        Args:
            exam_session: 考试会话
        
        Returns:
            Dict: 答题模式分析
        """
        return {
            'completion_rate': (exam_session.completed_questions / exam_session.total_questions) * 100,
            'accuracy_rate': (exam_session.correct_answers / exam_session.completed_questions) * 100 if exam_session.completed_questions > 0 else 0,
            'skip_rate': (exam_session.skipped_questions / exam_session.total_questions) * 100,
            'average_attempts_per_question': sum(exam_session.question_attempts.values()) / len(exam_session.question_attempts) if exam_session.question_attempts else 1
        }
    
    def _analyze_accuracy_by_difficulty(self, exam_session: ExamSession) -> Dict:
        """
        按难度分析准确率
        
        Args:
            exam_session: 考试会话
        
        Returns:
            Dict: 各难度准确率
        """
        # 获取题目信息
        questions = db.session.query(Question).filter(
            Question.id.in_(exam_session.question_ids)
        ).all()
        
        difficulty_stats = {
            'easy': {'correct': 0, 'total': 0},
            'medium': {'correct': 0, 'total': 0},
            'hard': {'correct': 0, 'total': 0}
        }
        
        for question in questions:
            # 确定难度级别
            if question.difficulty_score <= 0.3:
                difficulty = 'easy'
            elif question.difficulty_score <= 0.7:
                difficulty = 'medium'
            else:
                difficulty = 'hard'
            
            difficulty_stats[difficulty]['total'] += 1
            
            # 检查是否答对
            user_answer = exam_session.answers.get(str(question.id))
            if user_answer and self._check_answer(question, user_answer):
                difficulty_stats[difficulty]['correct'] += 1
        
        # 计算准确率
        accuracy_by_difficulty = {}
        for difficulty, stats in difficulty_stats.items():
            if stats['total'] > 0:
                accuracy_by_difficulty[difficulty] = (stats['correct'] / stats['total']) * 100
            else:
                accuracy_by_difficulty[difficulty] = 0
        
        return accuracy_by_difficulty
    
    def _analyze_strategy_effectiveness(self, exam_session: ExamSession) -> Dict:
        """
        分析策略有效性
        
        Args:
            exam_session: 考试会话
        
        Returns:
            Dict: 策略有效性分析
        """
        return {
            'time_management_effectiveness': exam_session.time_efficiency,
            'completion_strategy_effectiveness': exam_session.get_progress_percentage() / 100,
            'accuracy_strategy_effectiveness': (exam_session.correct_answers / exam_session.completed_questions) if exam_session.completed_questions > 0 else 0,
            'overall_effectiveness': exam_session.score_percentage / 100 if exam_session.score_percentage else 0
        }
    
    def _identify_strengths_weaknesses(self, exam_session: ExamSession) -> Tuple[List[str], List[str]]:
        """
        识别优势和薄弱领域
        
        Args:
            exam_session: 考试会话
        
        Returns:
            Tuple[List[str], List[str]]: 优势和薄弱领域
        """
        strengths = []
        weaknesses = []
        
        # 时间管理
        if exam_session.time_efficiency > 0.8:
            strengths.append("时间管理能力强")
        elif exam_session.time_efficiency < 0.6:
            weaknesses.append("时间管理需要改进")
        
        # 完成率
        completion_rate = exam_session.get_progress_percentage()
        if completion_rate > 90:
            strengths.append("题目完成率高")
        elif completion_rate < 70:
            weaknesses.append("题目完成率偏低")
        
        # 准确率
        accuracy_rate = (exam_session.correct_answers / exam_session.completed_questions) * 100 if exam_session.completed_questions > 0 else 0
        if accuracy_rate > 80:
            strengths.append("答题准确率高")
        elif accuracy_rate < 60:
            weaknesses.append("答题准确率需要提升")
        
        return strengths, weaknesses
    
    def _generate_improvement_priorities(self, weaknesses: List[str]) -> List[Dict]:
        """
        生成改进优先级
        
        Args:
            weaknesses: 薄弱领域列表
        
        Returns:
            List[Dict]: 改进优先级列表
        """
        priorities = []
        
        for i, weakness in enumerate(weaknesses):
            priorities.append({
                'priority': i + 1,
                'area': weakness,
                'importance': 'high' if i < 2 else 'medium',
                'suggested_actions': self._get_improvement_actions(weakness)
            })
        
        return priorities
    
    def _get_improvement_actions(self, weakness: str) -> List[str]:
        """
        获取改进行动建议
        
        Args:
            weakness: 薄弱领域
        
        Returns:
            List[str]: 行动建议
        """
        action_map = {
            "时间管理需要改进": [
                "制定详细的时间分配计划",
                "练习限时答题",
                "学习快速阅读技巧"
            ],
            "题目完成率偏低": [
                "优先完成有把握的题目",
                "合理安排答题顺序",
                "提高答题速度"
            ],
            "答题准确率需要提升": [
                "加强基础知识学习",
                "多做相关练习题",
                "仔细审题，避免粗心错误"
            ]
        }
        
        return action_map.get(weakness, ["针对性练习和复习"])
    
    def _generate_specific_recommendations(self, exam_session: ExamSession) -> List[str]:
        """
        生成具体建议
        
        Args:
            exam_session: 考试会话
        
        Returns:
            List[str]: 具体建议列表
        """
        recommendations = []
        
        # 基于得分给出建议
        if exam_session.score_percentage < 60:
            recommendations.append("建议加强基础知识学习，多做练习题")
        elif exam_session.score_percentage < 80:
            recommendations.append("基础较好，建议针对错题进行专项练习")
        else:
            recommendations.append("成绩优秀，建议挑战更高难度的题目")
        
        # 基于时间效率给出建议
        if exam_session.time_efficiency < 0.7:
            recommendations.append("建议提高答题速度，可通过限时练习改善")
        
        # 基于完成率给出建议
        if exam_session.get_progress_percentage() < 90:
            recommendations.append("建议优化答题策略，确保完成所有题目")
        
        return recommendations
    
    def get_exam_session(self, exam_session_id: int, user_id: int) -> Optional[ExamSession]:
        """
        获取考试会话
        
        Args:
            exam_session_id: 考试会话ID
            user_id: 用户ID
        
        Returns:
            Optional[ExamSession]: 考试会话
        """
        return db.session.query(ExamSession).filter(
            and_(
                ExamSession.id == exam_session_id,
                ExamSession.user_id == user_id
            )
        ).first()
    
    def get_user_exam_sessions(self, user_id: int, exam_type: Optional[str] = None, 
                              status: Optional[str] = None, limit: int = 20) -> List[ExamSession]:
        """
        获取用户考试会话列表
        
        Args:
            user_id: 用户ID
            exam_type: 考试类型筛选
            status: 状态筛选
            limit: 返回数量限制
        
        Returns:
            List[ExamSession]: 考试会话列表
        """
        query = db.session.query(ExamSession).filter(ExamSession.user_id == user_id)
        
        if exam_type:
            query = query.filter(ExamSession.exam_type == exam_type)
        
        if status:
            query = query.filter(ExamSession.status == status)
        
        return query.order_by(desc(ExamSession.created_time)).limit(limit).all()
    
    def get_exam_statistics(self, user_id: int, days: int = 30) -> Dict:
        """
        获取考试统计信息
        
        Args:
            user_id: 用户ID
            days: 统计天数
        
        Returns:
            Dict: 统计信息
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 获取指定时间内的考试会话
        sessions = db.session.query(ExamSession).filter(
            and_(
                ExamSession.user_id == user_id,
                ExamSession.created_time >= start_date
            )
        ).all()
        
        if not sessions:
            return {
                'total_exams': 0,
                'completed_exams': 0,
                'average_score': 0,
                'total_time_spent': 0,
                'improvement_trend': []
            }
        
        completed_sessions = [s for s in sessions if s.status == ExamStatus.COMPLETED.value]
        
        # 计算统计数据
        total_time_spent = sum(
            (s.end_time - s.actual_start_time).total_seconds() / 60 
            for s in completed_sessions 
            if s.actual_start_time and s.end_time
        )
        
        average_score = sum(s.score_percentage for s in completed_sessions) / len(completed_sessions) if completed_sessions else 0
        
        return {
            'total_exams': len(sessions),
            'completed_exams': len(completed_sessions),
            'completion_rate': (len(completed_sessions) / len(sessions)) * 100 if sessions else 0,
            'average_score': average_score,
            'total_time_spent': total_time_spent,
            'average_time_per_exam': total_time_spent / len(completed_sessions) if completed_sessions else 0,
            'exam_types': self._get_exam_type_distribution(sessions),
            'score_distribution': self._get_score_distribution(completed_sessions),
            'improvement_trend': self._calculate_improvement_trend(completed_sessions)
        }
    
    def _get_exam_type_distribution(self, sessions: List[ExamSession]) -> Dict:
        """
        获取考试类型分布
        
        Args:
            sessions: 考试会话列表
        
        Returns:
            Dict: 类型分布
        """
        distribution = {}
        for session in sessions:
            exam_type = session.exam_type
            distribution[exam_type] = distribution.get(exam_type, 0) + 1
        return distribution
    
    def _get_score_distribution(self, sessions: List[ExamSession]) -> Dict:
        """
        获取得分分布
        
        Args:
            sessions: 考试会话列表
        
        Returns:
            Dict: 得分分布
        """
        distribution = {
            '0-60': 0,
            '60-70': 0,
            '70-80': 0,
            '80-90': 0,
            '90-100': 0
        }
        
        for session in sessions:
            score = session.score_percentage
            if score < 60:
                distribution['0-60'] += 1
            elif score < 70:
                distribution['60-70'] += 1
            elif score < 80:
                distribution['70-80'] += 1
            elif score < 90:
                distribution['80-90'] += 1
            else:
                distribution['90-100'] += 1
        
        return distribution
    
    def _calculate_improvement_trend(self, sessions: List[ExamSession]) -> List[Dict]:
        """
        计算改进趋势
        
        Args:
            sessions: 考试会话列表
        
        Returns:
            List[Dict]: 趋势数据
        """
        # 按时间排序
        sorted_sessions = sorted(sessions, key=lambda s: s.created_time)
        
        trend = []
        for i, session in enumerate(sorted_sessions):
            trend.append({
                'exam_number': i + 1,
                'score': session.score_percentage,
                'time_efficiency': session.time_efficiency,
                'date': session.created_time.strftime('%Y-%m-%d')
            })
        
        return trend