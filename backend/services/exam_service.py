#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 服务层 - exam_service.py

Description:
    考试服务，处理考试创建、答题、评分等业务逻辑。

Author: Chang Xinglong
Date: 2025-08-30
Version: 1.0.0
License: Apache License 2.0
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import and_, update
from sqlalchemy.orm import Session

from models.exam import ExamSession, ExamType, ExamStatus, DifficultyLevel
from models.question import Question, QuestionType
from models.knowledge import KnowledgePoint, Chapter, Subject
from services.llm_service import LLMService
from utils.database import db


class ExamService:
    """考试服务类"""

    def __init__(self):
        """初始化考试服务"""
        self.llm_service = LLMService()

    def create_exam_session(self, user_id: str, exam_config: Dict[str, Any]) -> Dict[str, Any]:
        """创建考试会话"""
        try:
            # 解析配置
            exam_name = exam_config['exam_name']
            exam_type = exam_config.get('exam_type', 'practice')
            subject_id = exam_config['subject_id']
            total_questions = exam_config['total_questions']
            total_time_minutes = exam_config.get('total_time_minutes', exam_config.get('time_limit', 60))
            difficulty_level = exam_config.get('difficulty_level', 'medium')
            question_filters = exam_config.get('question_filters', {})

            # 选择题目
            questions = self._select_questions(
                subject_id=subject_id,
                question_count=total_questions,
                difficulty_level=difficulty_level,
                filters=question_filters
            )

            if not questions:
                raise ValueError("没有找到符合条件的题目")

            # 计算考试参数
            question_ids = [str(q.id) for q in questions]
            max_possible_score = sum(getattr(q, 'score', 5) for q in questions)

            # 创建考试会话
            exam_session = ExamSession(
                user_id=user_id,
                exam_type=exam_type,
                title=exam_name,
                subject_id=subject_id,
                difficulty_level=difficulty_level,
                total_questions=total_questions,
                total_time_minutes=total_time_minutes,
                max_possible_score=max_possible_score,
                status=ExamStatus.SCHEDULED.value,
                completed_questions=0
            )

            # 保存到数据库并获取ID
            db.session.add(exam_session)
            db.session.flush()  # 获取ID但不提交

            # 设置JSON字段
            exam_session.question_ids = question_ids
            exam_session.answers = {}
            exam_session.question_times = {}
            exam_session.question_attempts = {}

            db.session.commit()

            return {
                'session_id': exam_session.id,
                'exam_name': exam_name,
                'status': exam_session.status,
                'total_questions': total_questions,
                'total_time_minutes': total_time_minutes,
                'created_time': exam_session.created_time.isoformat()
            }

        except Exception as e:
            db.session.rollback()
            import traceback
            print(f"创建考试会话失败 - 详细错误: {str(e)}")
            print(f"错误堆栈: {traceback.format_exc()}")
            raise ValueError(f"创建考试会话失败: {str(e)}")

    def _select_questions(self, subject_id: str, question_count: int, 
                         difficulty_level: str, filters: Dict[str, Any]) -> List[Question]:
        """选择题目"""
        try:
            # 构建查询 - 通过关联查询来筛选学科
            query = db.session.query(Question).join(
                KnowledgePoint, Question.knowledge_point_id == KnowledgePoint.id
            ).join(
                Chapter, KnowledgePoint.chapter_id == Chapter.id
            ).join(
                Subject, Chapter.subject_id == Subject.id
            ).filter(
                Subject.id == subject_id
            ).filter(
                Question.is_active == True
            )
            
            # 添加难度过滤
            if difficulty_level != 'mixed':
                # 将字符串难度转换为数字
                difficulty_map = {'easy': 1, 'medium': 2, 'hard': 3}
                difficulty_num = difficulty_map.get(difficulty_level, 2)
                query = query.filter(Question.difficulty == difficulty_num)
            
            # 添加知识点过滤
            if 'knowledge_point_ids' in filters:
                kp_ids = filters['knowledge_point_ids']
                if kp_ids:
                    query = query.filter(Question.knowledge_point_id.in_(kp_ids))
            
            # 添加题目类型过滤
            if 'question_types' in filters:
                q_types = filters['question_types']
                if q_types:
                    query = query.filter(Question.type.in_(q_types))
            
            available_questions = query.all()
            
            if len(available_questions) < question_count:
                # 如果题目不够，返回所有可用题目
                return available_questions
            
            # 随机选择题目
            return random.sample(available_questions, question_count)

        except Exception as e:
            raise Exception(f"选择题目失败: {str(e)}")

    def start_exam(self, user_id: str, session_id: int) -> Dict[str, Any]:
        """开始考试"""
        try:
            # 获取考试会话
            exam_session = db.session.query(ExamSession).filter(
                and_(
                    ExamSession.id == session_id,
                    ExamSession.user_id == user_id
                )
            ).first()

            if not exam_session:
                raise ValueError("考试会话不存在")

            status_val = getattr(exam_session, 'status', None)
            if status_val != ExamStatus.SCHEDULED.value:
                raise ValueError("考试状态不正确")

            # 更新状态和开始时间
            db.session.execute(
                update(ExamSession)
                .where(ExamSession.id == session_id)
                .values(
                    status=ExamStatus.IN_PROGRESS.value,
                    actual_start_time=datetime.utcnow(),
                    current_question_index=0,
                    updated_time=datetime.utcnow()
                )
            )

            db.session.commit()

            # 获取第一题
            first_question = self._get_question_by_index(exam_session, 0)

            # 获取实际开始时间
            actual_start_time = getattr(exam_session, 'actual_start_time', None)
            start_time_iso = actual_start_time.isoformat() if actual_start_time else None
            
            return {
                'session_id': session_id,
                'status': ExamStatus.IN_PROGRESS.value,
                'start_time': start_time_iso,
                'total_time_minutes': exam_session.total_time_minutes,
                'current_question': first_question,
                'progress': {
                    'current_index': 0,
                    'total_questions': exam_session.total_questions,
                    'percentage': 0.0
                }
            }

        except Exception as e:
            db.session.rollback()
            raise Exception(f"开始考试失败: {str(e)}")

    def submit_answer(self, user_id: str, session_id: int, question_id: int,
                     answer: str, time_spent: int, confidence_level: Optional[float] = None,
                     is_guess: bool = False) -> Dict[str, Any]:
        """提交答案"""
        try:
            # 获取考试会话
            exam_session = db.session.query(ExamSession).filter(
                and_(
                    ExamSession.id == session_id,
                    ExamSession.user_id == user_id
                )
            ).first()

            if not exam_session:
                raise ValueError("考试会话不存在")

            status_val = getattr(exam_session, 'status', None)
            if status_val != ExamStatus.IN_PROGRESS.value:
                raise ValueError("考试未在进行中")

            # 检查题目是否属于当前考试
            question_ids_list = exam_session.question_ids or []
            if str(question_id) not in question_ids_list:
                raise ValueError("题目不属于当前考试")

            # 获取题目信息
            question = db.session.query(Question).get(question_id)
            if not question:
                raise ValueError("题目不存在")

            # 检查答案并计算得分
            is_correct, score = self._check_answer(question, answer)

            # 更新答案记录
            current_answers = getattr(exam_session, 'answers', None) or {}
            current_times = getattr(exam_session, 'question_times', None) or {}
            current_attempts = getattr(exam_session, 'question_attempts', None) or {}

            # 检查是否是新答案
            is_new_answer = str(question_id) not in current_answers

            current_answers[str(question_id)] = {
                'answer': answer,
                'is_correct': is_correct,
                'score': score,
                'confidence_level': confidence_level,
                'is_guess': is_guess,
                'submitted_at': datetime.utcnow().isoformat()
            }
            current_times[str(question_id)] = time_spent
            current_attempts[str(question_id)] = current_attempts.get(str(question_id), 0) + 1

            # 更新完成题目数（只有新答案才增加）
            completed_count = getattr(exam_session, 'completed_questions', 0) or 0
            if is_new_answer:
                completed_count += 1

            # 更新当前题目索引
            current_index = exam_session.current_question_index or 0
            next_index = current_index + 1

            # 使用update方法更新会话数据
            db.session.execute(
                update(ExamSession)
                .where(ExamSession.id == session_id)
                .values(
                    answers=current_answers,
                    question_times=current_times,
                    question_attempts=current_attempts,
                    current_question_index=next_index,
                    updated_time=datetime.utcnow(),
                    completed_questions=completed_count
                )
            )

            db.session.commit()

            # 获取下一题
            next_question = None
            total_questions_count = getattr(exam_session, 'total_questions', 0) or 0
            # 确保next_index是整数类型
            next_index_int = int(next_index) if isinstance(next_index, (int, float)) else 0
            if next_index_int < total_questions_count:
                next_question = self._get_question_by_index(exam_session, next_index_int)

            # 计算统计信息
            correct_count = sum(1 for ans in current_answers.values() if ans.get('is_correct', False))
            total_score = sum(ans.get('score', 0) for ans in current_answers.values())

            return {
                'is_correct': is_correct,
                'score': score,
                'explanation': getattr(question, 'explanation', ''),
                'next_question': next_question,
                'progress': {
                    'answered': completed_count,
                    'total': total_questions_count,
                    'percentage': (completed_count / total_questions_count) * 100 if total_questions_count > 0 else 0
                },
                'statistics': {
                    'correct_answers': correct_count,
                    'total_score': total_score,
                    'accuracy': (correct_count / completed_count) * 100 if completed_count > 0 else 0
                }
            }

        except Exception as e:
            db.session.rollback()
            raise Exception(f"提交答案失败: {str(e)}")

    def _check_answer(self, question: Question, answer: str) -> Tuple[bool, float]:
        """检查答案正确性"""
        try:
            correct_answer = question.correct_answer
            question_type = question.type
            base_score = getattr(question, 'score', 5)

            if question_type in ['single_choice', 'multiple_choice', 'true_false']:
                # 选择题和判断题
                is_correct = answer.strip().upper() == correct_answer.strip().upper()
                return is_correct, base_score if is_correct else 0

            elif question_type == 'fill_blank':
                # 填空题
                # 简单的字符串匹配，可以扩展为更复杂的匹配逻辑
                is_correct = answer.strip().lower() == correct_answer.strip().lower()
                return is_correct, base_score if is_correct else 0

            elif question_type in ['short_answer', 'essay']:
                # 主观题，使用AI评分
                return self._evaluate_subjective_answer(question, answer)

            else:
                # 未知题型，默认不正确
                return False, 0

        except Exception as e:
            # 评分失败，给予部分分数
            return False, getattr(question, 'score', 5) * 0.3

    def _evaluate_subjective_answer(self, question: Question, answer: str) -> Tuple[bool, float]:
        """评估主观题答案"""
        try:
            # 使用LLM服务评分
            evaluation_result = self.llm_service.evaluate_answer(
                question_text=question.content,
                correct_answer=question.correct_answer,
                student_answer=answer,
                question_type=question.type
            )

            score_percentage = evaluation_result.get('score_percentage', 0.5)
            base_score = getattr(question, 'score', 5)
            actual_score = base_score * score_percentage
            is_correct = score_percentage >= 0.6  # 60%以上认为正确

            return is_correct, actual_score

        except Exception as e:
            # AI评分失败，给予中等分数
            base_score = getattr(question, 'score', 5)
            return False, base_score * 0.5

    def _get_question_by_index(self, exam_session: ExamSession, index: int) -> Optional[Dict[str, Any]]:
        """根据索引获取题目"""
        try:
            question_ids_list = getattr(exam_session, 'question_ids', None)
            question_ids_list = question_ids_list if isinstance(question_ids_list, list) else []
            if index >= len(question_ids_list):
                return None

            question_id = question_ids_list[index]
            question = db.session.query(Question).get(int(question_id))

            if not question:
                return None

            return {
                'question_id': question.id,
                'question_index': index,
                'question_text': question.content,
                'question_type': question.type,
                'options': getattr(question, 'options', []),
                'score': getattr(question, 'score', 5)
            }

        except Exception:
            return None

    def complete_exam(self, user_id: str, session_id: int) -> Dict[str, Any]:
        """完成考试"""
        try:
            # 获取考试会话
            exam_session = db.session.query(ExamSession).filter(
                and_(
                    ExamSession.id == session_id,
                    ExamSession.user_id == user_id
                )
            ).first()

            if not exam_session:
                raise ValueError("考试会话不存在")

            status_val = getattr(exam_session, 'status', None)
            if status_val != ExamStatus.IN_PROGRESS.value:
                raise ValueError("考试未在进行中")

            # 计算最终统计
            statistics = self._calculate_final_statistics(exam_session)

            # 更新考试状态
            exam_session.status = ExamStatus.COMPLETED.value
            exam_session.end_time = datetime.utcnow()
            exam_session.total_score = statistics['total_score']
            exam_session.score_percentage = statistics['score_percentage']
            exam_session.correct_answers = statistics['correct_answers']
            exam_session.wrong_answers = statistics['wrong_answers']
            exam_session.updated_time = datetime.utcnow()

            db.session.commit()

            return {
                'session_id': session_id,
                'status': ExamStatus.COMPLETED.value,
                'statistics': statistics,
                'completed_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            db.session.rollback()
            raise Exception(f"完成考试失败: {str(e)}")

    def _calculate_final_statistics(self, exam_session: ExamSession) -> Dict[str, Any]:
        """计算最终统计信息"""
        answers = getattr(exam_session, 'answers', None)
        answers = answers if isinstance(answers, dict) else {}
        question_times = getattr(exam_session, 'question_times', None)
        question_times = question_times if isinstance(question_times, dict) else {}

        total_questions = len(answers)
        correct_count = sum(1 for ans in answers.values() if ans.get('is_correct', False))
        wrong_count = total_questions - correct_count
        total_score = sum(ans.get('score', 0) for ans in answers.values())
        max_score = getattr(exam_session, 'max_possible_score', None) or 100
        score_percentage = (total_score / max_score * 100) if max_score > 0 else 0
        accuracy = (correct_count / total_questions * 100) if total_questions > 0 else 0
        total_time = sum(question_times.values())

        return {
            'total_questions': total_questions,
            'correct_answers': correct_count,
            'wrong_answers': wrong_count,
            'total_score': total_score,
            'max_possible_score': max_score,
            'score_percentage': score_percentage,
            'accuracy_percentage': accuracy,
            'total_time_seconds': total_time,
            'average_time_per_question': total_time / total_questions if total_questions > 0 else 0
        }

    def get_exam_session(self, session_id: int, user_id: Optional[str] = None) -> Optional[ExamSession]:
        """获取考试会话"""
        try:
            query = db.session.query(ExamSession).filter(ExamSession.id == session_id)
            if user_id:
                query = query.filter(ExamSession.user_id == str(user_id))
            return query.first()
        except Exception:
            return None

    def reset_exam_session(self, session_id: int, user_id: str) -> bool:
        """重置考试会话"""
        try:
            # 获取考试会话
            session = self.get_exam_session(session_id, user_id)
            
            # 检查考试会话是否存在且属于该用户
            if not session or str(session.user_id) != str(user_id):
                return False
            
            # 检查是否暂停
            is_paused_val = getattr(session, 'is_paused', False)
            if is_paused_val:
                return False
            
            # 重置考试状态
            db.session.execute(
                update(ExamSession)
                .where(ExamSession.id == session_id)
                .values(
                    status=ExamStatus.IN_PROGRESS.value,
                    actual_start_time=datetime.utcnow(),
                    current_question_index=0,
                    updated_time=datetime.utcnow()
                )
            )
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            return False

    def submit_question_answer(self, session_id: int, user_id: str, question_index: int, answer: str) -> Optional[Dict[str, Any]]:
        """提交题目答案"""
        try:
            # 获取考试会话
            session = self.get_exam_session(session_id, user_id)
            
            # 检查考试会话是否存在且属于该用户
            if not session or str(session.user_id) != str(user_id):
                return None
            
            # 获取当前答案字典
            answers = getattr(session, 'answers', None)
            answers = answers if isinstance(answers, dict) else {}
            
            # 检查答案正确性
            question_ids = getattr(session, 'question_ids', None)
            question_ids = question_ids if isinstance(question_ids, list) else []
            if question_index >= len(question_ids):
                return None
                
            question_id = question_ids[question_index]
            question = db.session.query(Question).get(int(question_id))
            if not question:
                return None
                
            is_correct, score = self._check_answer(question, answer)
            
            # 更新答案
            current_answers = getattr(session, 'answers', None) or {}
            current_answers[str(question_index)] = {
                'answer': answer,
                'is_correct': is_correct,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # 更新完成题目数
            completed_count = getattr(session, 'completed_questions', 0) or 0
            db.session.execute(
                update(ExamSession)
                .where(ExamSession.id == session_id)
                .values(
                    answers=current_answers,
                    completed_questions=completed_count + 1
                )
            )
            
            # 移动到下一题
            current_index = getattr(session, 'current_question_index', 0) or 0
            db.session.execute(
                update(ExamSession)
                .where(ExamSession.id == session_id)
                .values(current_question_index=current_index + 1)
            )
            
            db.session.commit()
            
            # 重新查询更新后的session
            session = db.session.get(ExamSession, session_id)
            if not session:
                return None
                
            # 检查是否完成所有题目
            question_ids = getattr(session, 'question_ids', None)
            question_ids = question_ids if isinstance(question_ids, list) else []
            current_index = getattr(session, 'current_question_index', 0) or 0
            if current_index >= len(question_ids):
                return self._get_question_by_index(session, current_index)
            
            # 获取下一题
            next_question_index = getattr(session, 'current_question_index', 0) or 0
            next_question = self._get_question_by_index(session, next_question_index)
            
            return {
                'is_correct': is_correct,
                'score': score,
                'next_question': next_question
            }
            
        except Exception as e:
            db.session.rollback()
            return None

    def get_current_question(self, session_id: int, user_id: str) -> Optional[Dict[str, Any]]:
        """获取当前题目"""
        try:
            # 获取考试会话
            session = self.get_exam_session(session_id, user_id)
            
            # 检查考试会话是否存在且属于该用户
            if not session or str(session.user_id) != str(user_id):
                return None
            
            current_index = getattr(session, 'current_question_index', 0) or 0
            return self._get_question_by_index(session, current_index)
            
        except Exception:
            return None

    def get_question_by_index_safe(self, session_id: int, user_id: str, index: int) -> Optional[Dict[str, Any]]:
        """安全地根据索引获取题目"""
        try:
            # 获取考试会话
            session = self.get_exam_session(session_id, user_id)
            
            # 检查考试会话是否存在且属于该用户
            if not session or str(session.user_id) != str(user_id):
                return None
            
            # 检查考试是否已结束或题目索引是否有效
            question_ids = getattr(session, 'question_ids', None)
            question_ids = question_ids if isinstance(question_ids, list) else []
            status = getattr(session, 'status', None)
            if status == 'completed' or index >= len(question_ids):
                return None
            
            return self._get_question_by_index(session, index)
            
        except Exception:
            return None

    def pause_exam(self, session_id: int, user_id: str) -> bool:
        """暂停考试"""
        try:
            session = self.get_exam_session(session_id, user_id)
            is_paused_val = getattr(session, 'is_paused', False)
            if not session or is_paused_val:
                return False
            
            db.session.execute(
                update(ExamSession)
                .where(ExamSession.id == session_id)
                .values(
                    is_paused=True,
                    pause_time=datetime.utcnow()
                )
            )
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    def resume_exam(self, session_id: int, user_id: str) -> bool:
        """恢复考试"""
        try:
            session = self.get_exam_session(session_id, user_id)
            is_paused_val = getattr(session, 'is_paused', False)
            if not session or not is_paused_val:
                return False
            
            db.session.execute(
                update(ExamSession)
                .where(ExamSession.id == session_id)
                .values(
                    is_paused=False,
                    resume_time=datetime.utcnow()
                )
            )
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    def get_exam_statistics(self, session_id: int, user_id: str) -> Optional[Dict[str, Any]]:
        """获取考试统计信息"""
        try:
            # 获取考试会话
            session = self.get_exam_session(session_id, user_id)
            
            # 检查考试会话是否存在且属于该用户
            if not session or str(session.user_id) != str(user_id):
                return None
            
            question_ids = getattr(session, 'question_ids', None)
            question_ids = question_ids if isinstance(question_ids, list) else []
            answers = getattr(session, 'answers', None)
            answers = answers if isinstance(answers, dict) else {}
            question_times = getattr(session, 'question_times', None)
            question_times = question_times if isinstance(question_times, dict) else {}
            
            total_questions = len(question_ids)
            
            # 计算正确答案数
            correct_answers = sum(1 for answer in answers.values() if answer.get('is_correct', False))
            completed_questions = getattr(session, 'completed_questions', 0) or 0
            
            return {
                'total_questions': total_questions,
                'completed_questions': completed_questions,
                'correct_answers': correct_answers,
                'accuracy': (correct_answers / len(answers)) * 100 if answers else 0
            }
            
        except Exception:
            return None
