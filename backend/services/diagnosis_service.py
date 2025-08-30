# -*- coding: utf-8 -*-
"""
个性化诊断服务 - 三层诊断、AI自适应出题、学习画像
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from utils.database import db
from models.diagnosis import (
    DiagnosisReport, DiagnosisSession, QuestionResponse, WeaknessPoint, LearningProfile,
    DiagnosisType, DiagnosisStatus, DiagnosisLevel
)
from models.knowledge import KnowledgePoint, Subject
from models.user import User
from services.adaptive_service import AdaptiveService
from services.learning_profile_service import LearningProfileService
import random
import math

class DiagnosisService:
    """个性化诊断服务类"""
    
    @staticmethod
    def create_diagnosis_report(user_id: str, subject_id: str, diagnosis_config: Dict[str, Any]) -> DiagnosisReport:
        """创建诊断报告"""
        report = DiagnosisReport(
            user_id=user_id,
            subject_id=subject_id,
            name=diagnosis_config.get('name', f'诊断报告_{datetime.now().strftime("%Y%m%d_%H%M%S")}'),
            description=diagnosis_config.get('description', ''),
            diagnosis_type=DiagnosisType(diagnosis_config.get('type', 'comprehensive')),
            target_level=DiagnosisLevel(diagnosis_config.get('target_level', 'transfer')),
            total_questions_planned=diagnosis_config.get('total_questions', 30),
            time_limit=diagnosis_config.get('time_limit', 60),
            difficulty_range=diagnosis_config.get('difficulty_range', {'min': 1, 'max': 5}),
            adaptive_enabled=diagnosis_config.get('adaptive_enabled', True),
            status=DiagnosisStatus.PENDING
        )
        
        db.session.add(report)
        db.session.commit()
        
        return report
    
    @staticmethod
    def start_adaptive_diagnosis(report_id: str, session_config: Dict[str, Any]) -> DiagnosisSession:
        """开始自适应诊断会话"""
        report = DiagnosisReport.query.get(report_id)
        if not report:
            raise ValueError("诊断报告不存在")
        
        # 获取用户学习画像
        learning_profile = LearningProfileService.get_or_create_profile(report.user_id)
        
        session = DiagnosisSession(
            diagnosis_report_id=report_id,
            session_name=session_config.get('name', f'诊断会话_{datetime.now().strftime("%H%M%S")}'),
            session_type=DiagnosisLevel(session_config.get('session_type', 'memory')),
            max_questions=session_config.get('max_questions', 30),
            min_questions=session_config.get('min_questions', 10),
            target_precision=session_config.get('target_precision', 0.3)
        )
        
        db.session.add(session)
        db.session.commit()
        
        # 使用自适应服务初始化会话
        AdaptiveService.initialize_session(session, learning_profile)
        session.start_session()
        return session
    
    @staticmethod
    def get_next_question(session_id: str) -> Dict[str, Any]:
        """获取下一道自适应题目"""
        session = DiagnosisSession.query.get(session_id)
        if not session:
            raise ValueError("诊断会话不存在")
        
        # 使用自适应服务检查是否应该继续
        if not AdaptiveService.should_continue_testing(session):
            session.end_session()
            return {'finished': True, 'session_completed': True}
        
        # 获取知识点池
        report = session.diagnosis_report
        knowledge_points = DiagnosisService._get_knowledge_points_for_diagnosis(
            report.subject_id, 
            session.session_type
        )
        
        # 使用自适应服务选择题目
        available_questions = DiagnosisService._get_available_questions(
            session, knowledge_points
        )
        
        question_recommendation = AdaptiveService.generate_adaptive_recommendation(
            session, available_questions
        )
        
        if not question_recommendation:
            session.end_session()
            return {'finished': True, 'session_completed': True}
        
        # 记录题目选择历史
        session.question_selection_history.append({
            'question_index': session.current_question_index,
            'suggested_difficulty': question_recommendation.get('suggested_difficulty'),
            'actual_difficulty': question_recommendation['question']['difficulty'],
            'knowledge_point_id': question_recommendation['question']['knowledge_point_id'],
            'selection_time': datetime.utcnow().isoformat(),
            'recommendation_reason': question_recommendation.get('reason')
        })
        
        db.session.commit()
        
        return {
            'finished': False,
            'question': question_recommendation['question'],
            'recommendation': question_recommendation,
            'session_info': {
                'current_index': session.current_question_index,
                'questions_answered': session.questions_answered,
                'current_ability': session.current_ability_estimate
            }
        }
    
    @staticmethod
    def submit_answer(session_id: str, answer_data: Dict[str, Any]) -> Dict[str, Any]:
        """提交答案并更新自适应参数"""
        session = DiagnosisSession.query.get(session_id)
        if not session:
            raise ValueError("诊断会话不存在")
        
        # 创建回答记录
        response = QuestionResponse(
            diagnosis_session_id=session_id,
            question_id=answer_data.get('question_id'),
            knowledge_point_id=answer_data.get('knowledge_point_id'),
            question_content=answer_data.get('question_content'),
            question_type=answer_data.get('question_type'),
            difficulty_level=answer_data.get('difficulty_level'),
            user_answer=answer_data.get('user_answer'),
            correct_answer=answer_data.get('correct_answer'),
            is_correct=answer_data.get('is_correct', False),
            time_spent=answer_data.get('time_spent', 0),
            confidence_level=answer_data.get('confidence_level', 3),
            error_type=answer_data.get('error_type'),
            solution_steps=answer_data.get('solution_steps', [])
        )
        
        db.session.add(response)
        
        # 使用自适应服务更新能力估计
        new_ability, new_se = AdaptiveService.update_ability_estimate(
            session,
            answer_data.get('is_correct', False),
            answer_data.get('difficulty_level', 3)
        )
        
        session.current_ability_estimate = new_ability
        
        # 更新总用时
        session.total_time_spent += answer_data.get('time_spent', 0)
        
        # 使用学习画像服务更新用户画像
        report = session.diagnosis_report
        try:
            # 获取用户所有答题记录来更新画像
            all_responses = QuestionResponse.query.join(DiagnosisSession).join(DiagnosisReport).filter(
                DiagnosisReport.user_id == report.user_id
            ).all()
            LearningProfileService.create_or_update_profile(
                report.user_id, all_responses
            )
        except Exception as profile_error:
            pass  # 忽略画像更新错误
        
        db.session.commit()
        
        # 使用自适应服务分析答题模式
        response_analysis = AdaptiveService.analyze_response_pattern(session)
        
        return {
            'response_recorded': True,
            'updated_ability': session.current_ability_estimate,
            'questions_remaining': session.max_questions - session.questions_answered,
            'should_continue': AdaptiveService.should_continue_testing(session),
            'response_analysis': response_analysis
        }
    
    @staticmethod
    def complete_diagnosis(report_id: str) -> DiagnosisReport:
        """完成诊断并生成报告"""
        report = DiagnosisReport.query.get(report_id)
        if not report:
            raise ValueError("诊断报告不存在")
        
        # 收集所有会话的回答数据
        all_responses = []
        total_questions = 0
        correct_questions = 0
        total_time = 0
        
        for session in report.diagnosis_sessions:
            session_responses = session.question_responses.all()
            all_responses.extend([{
                'is_correct': r.is_correct,
                'difficulty': r.difficulty_level,
                'knowledge_point_id': r.knowledge_point_id,
                'time_spent': r.time_spent,
                'error_type': r.error_type
            } for r in session_responses])
            
            total_questions += session.questions_answered
            correct_questions += session.correct_answers
            total_time += session.total_time_spent
        
        # 更新报告统计
        report.total_questions = total_questions
        report.correct_questions = correct_questions
        report.total_time = total_time
        report.avg_time_per_question = total_time / max(1, total_questions)
        report.calculate_accuracy_rate()
        
        # 更新能力估计
        report.update_ability_estimate(all_responses)
        
        # 生成知识掌握度分析
        DiagnosisService._analyze_knowledge_mastery(report, all_responses)
        
        # 生成热力图数据
        report.generate_heatmap_data()
        
        # 生成学习路径
        report.generate_learning_path()
        
        # 生成AI分析和建议
        DiagnosisService._generate_ai_analysis(report)
        
        # 创建或更新用户学习画像
        try:
            all_question_responses = DiagnosisService._get_diagnosis_responses(report)
            LearningProfileService.create_or_update_profile(
                report.user_id, 
                all_question_responses
            )
        except Exception as profile_error:
            pass  # 忽略画像更新错误
        
        # 更新状态
        report.status = DiagnosisStatus.COMPLETED
        
        db.session.commit()
        
        return report
    
    @staticmethod
    def _get_knowledge_points_for_diagnosis(subject_id: str, diagnosis_level: DiagnosisLevel) -> List[KnowledgePoint]:
        """获取用于诊断的知识点"""
        # 根据诊断层级筛选知识点
        difficulty_range = {
            DiagnosisLevel.MEMORY: (1, 2),
            DiagnosisLevel.APPLICATION: (2, 4),
            DiagnosisLevel.TRANSFER: (3, 5)
        }.get(diagnosis_level, (1, 5))
        
        knowledge_points = KnowledgePoint.query.filter(
            KnowledgePoint.subject_id == subject_id,
            KnowledgePoint.difficulty_level.between(difficulty_range[0], difficulty_range[1])
        ).all()
        
        return knowledge_points
    
    @staticmethod
    def _get_available_questions(session: DiagnosisSession, 
                               knowledge_points: List[KnowledgePoint]) -> List[Dict[str, Any]]:
        """获取可用题目列表"""
        # 过滤已选择的知识点
        used_kp_ids = [h.get('knowledge_point_id') for h in session.question_selection_history]
        available_kps = [kp for kp in knowledge_points if str(kp.id) not in used_kp_ids]
        
        if not available_kps:
            available_kps = knowledge_points  # 如果都用完了，重新开始
        
        # 为每个知识点生成模拟题目（实际应该从题库获取）
        available_questions = []
        for kp in available_kps:
            question = {
                'id': f'q_{kp.id}_{len(session.question_selection_history)}',
                'knowledge_point_id': str(kp.id),
                'knowledge_point_name': kp.name,
                'difficulty': kp.difficulty_level,
                'content': f'这是一道关于{kp.name}的{kp.difficulty_level}级难度题目',
                'type': 'multiple_choice',
                'options': ['A. 选项1', 'B. 选项2', 'C. 选项3', 'D. 选项4'],
                'correct_answer': 'A',
                'explanation': '这是题目解析'
            }
            available_questions.append(question)
        
        return available_questions
    
    @staticmethod
    def _analyze_knowledge_mastery(report: DiagnosisReport, responses: List[Dict[str, Any]]):
        """分析知识点掌握度"""
        mastery_levels = {}
        
        # 按知识点分组统计
        kp_stats = {}
        for response in responses:
            kp_id = response.get('knowledge_point_id')
            if not kp_id:
                continue
                
            if kp_id not in kp_stats:
                kp_stats[kp_id] = {
                    'total': 0,
                    'correct': 0,
                    'total_time': 0,
                    'difficulties': [],
                    'error_types': []
                }
            
            stats = kp_stats[kp_id]
            stats['total'] += 1
            if response.get('is_correct', False):
                stats['correct'] += 1
            stats['total_time'] += response.get('time_spent', 0)
            stats['difficulties'].append(response.get('difficulty', 3))
            if response.get('error_type'):
                stats['error_types'].append(response.get('error_type'))
        
        # 计算每个知识点的掌握度
        for kp_id, stats in kp_stats.items():
            accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
            avg_difficulty = sum(stats['difficulties']) / len(stats['difficulties']) if stats['difficulties'] else 3
            avg_time = stats['total_time'] / stats['total'] if stats['total'] > 0 else 0
            
            # 综合评分（考虑正确率、难度、用时）
            mastery_score = accuracy * 100
            if avg_difficulty > 3:
                mastery_score *= 1.2  # 高难度题目正确率加权
            if avg_time > 120:  # 超过2分钟的题目
                mastery_score *= 0.9  # 用时过长扣分
            
            mastery_levels[kp_id] = {
                'score': min(100, max(0, mastery_score)),
                'accuracy': accuracy,
                'difficulty': avg_difficulty,
                'time_spent': avg_time,
                'error_rate': 1 - accuracy,
                'error_types': list(set(stats['error_types'])),
                'priority': DiagnosisService._calculate_improvement_priority(mastery_score, avg_difficulty)
            }
        
        report.mastery_levels = mastery_levels
    
    @staticmethod
    def _calculate_improvement_priority(mastery_score: float, difficulty: float) -> int:
        """计算改进优先级（1-5，1最高）"""
        if mastery_score < 40:
            return 1  # 急需改进
        elif mastery_score < 60:
            return 2  # 需要改进
        elif mastery_score < 80:
            return 3  # 一般改进
        else:
            return 4 if difficulty < 4 else 5  # 低优先级
    
    @staticmethod
    def _generate_ai_analysis(report: DiagnosisReport):
        """生成AI分析结果"""
        # 这里应该调用AI模型进行分析，现在用规则生成
        analysis = {
            'overall_assessment': DiagnosisService._generate_overall_assessment(report),
            'strength_analysis': DiagnosisService._analyze_strengths(report),
            'weakness_analysis': DiagnosisService._analyze_weaknesses(report),
            'learning_style': DiagnosisService._infer_learning_style(report),
            'improvement_suggestions': DiagnosisService._generate_improvement_suggestions(report)
        }
        
        report.ai_analysis = analysis
        
        # 生成学习建议
        recommendations = DiagnosisService._generate_recommendations(report)
        report.recommendations = recommendations
    
    @staticmethod
    def _generate_overall_assessment(report: DiagnosisReport) -> str:
        """生成整体评估"""
        accuracy = report.accuracy_rate or 0
        ability = report.ability_estimate or 0
        
        if accuracy >= 80 and ability > 1:
            return "优秀：整体表现出色，知识掌握扎实，具备良好的学习能力。"
        elif accuracy >= 60 and ability > 0:
            return "良好：基础知识掌握较好，但在某些方面还有提升空间。"
        elif accuracy >= 40:
            return "一般：基础知识掌握一般，需要加强练习和巩固。"
        else:
            return "需要努力：基础知识掌握不够扎实，建议系统性复习。"
    
    @staticmethod
    def _analyze_strengths(report: DiagnosisReport) -> List[str]:
        """分析优势点"""
        strengths = []
        
        if report.mastery_levels:
            high_mastery = [(kp_id, data) for kp_id, data in report.mastery_levels.items() 
                          if data.get('score', 0) >= 80]
            
            if high_mastery:
                strengths.append(f"在{len(high_mastery)}个知识点上表现优秀")
            
            # 分析难题表现
            hard_questions_correct = [data for data in report.mastery_levels.values() 
                                    if data.get('difficulty', 3) >= 4 and data.get('accuracy', 0) > 0.7]
            if hard_questions_correct:
                strengths.append("在高难度题目上表现良好")
        
        if report.avg_time_per_question and report.avg_time_per_question < 90:
            strengths.append("答题速度较快")
        
        return strengths
    
    @staticmethod
    def _analyze_weaknesses(report: DiagnosisReport) -> List[str]:
        """分析薄弱点"""
        weaknesses = []
        
        if report.mastery_levels:
            low_mastery = [(kp_id, data) for kp_id, data in report.mastery_levels.items() 
                         if data.get('score', 0) < 60]
            
            if low_mastery:
                weaknesses.append(f"在{len(low_mastery)}个知识点上需要加强")
            
            # 分析常见错误类型
            all_errors = []
            for data in report.mastery_levels.values():
                all_errors.extend(data.get('error_types', []))
            
            if all_errors:
                from collections import Counter
                common_errors = Counter(all_errors).most_common(3)
                for error, count in common_errors:
                    if count >= 2:
                        weaknesses.append(f"经常出现{error}类型错误")
        
        if report.avg_time_per_question and report.avg_time_per_question > 180:
            weaknesses.append("答题速度偏慢")
        
        return weaknesses
    
    @staticmethod
    def _infer_learning_style(report: DiagnosisReport) -> Dict[str, Any]:
        """推断学习风格"""
        style = {
            'pace': 'moderate',
            'difficulty_preference': 'medium',
            'error_pattern': 'mixed'
        }
        
        if report.avg_time_per_question:
            if report.avg_time_per_question < 60:
                style['pace'] = 'fast'
            elif report.avg_time_per_question > 150:
                style['pace'] = 'slow'
        
        if report.mastery_levels:
            avg_difficulty = sum(data.get('difficulty', 3) for data in report.mastery_levels.values()) / len(report.mastery_levels)
            if avg_difficulty > 3.5:
                style['difficulty_preference'] = 'high'
            elif avg_difficulty < 2.5:
                style['difficulty_preference'] = 'low'
        
        return style
    
    @staticmethod
    def _generate_improvement_suggestions(report: DiagnosisReport) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if report.accuracy_rate and report.accuracy_rate < 60:
            suggestions.append("建议加强基础知识的学习和巩固")
        
        if report.avg_time_per_question and report.avg_time_per_question > 150:
            suggestions.append("建议提高答题速度，多做限时练习")
        
        if report.mastery_levels:
            weak_points = [kp_id for kp_id, data in report.mastery_levels.items() 
                         if data.get('score', 0) < 50]
            if weak_points:
                suggestions.append(f"重点关注{len(weak_points)}个薄弱知识点的学习")
        
        suggestions.append("建议制定个性化学习计划，循序渐进")
        
        return suggestions
    
    @staticmethod
    def _generate_recommendations(report: DiagnosisReport) -> List[Dict[str, Any]]:
        """生成具体学习建议"""
        recommendations = []
        
        # 基于薄弱点生成建议
        if report.learning_path:
            for item in report.learning_path[:3]:  # 取前3个最重要的
                recommendations.append({
                    'type': 'knowledge_improvement',
                    'title': f"加强{item['knowledge_point_name']}的学习",
                    'description': f"当前掌握度{item['current_mastery']:.1f}%，建议提升至{item['target_mastery']}%",
                    'estimated_time': item['estimated_time'],
                    'priority': 'high' if item['current_mastery'] < 40 else 'medium',
                    'resources': item.get('recommended_resources', {}),
                    'strategy': item.get('practice_strategy', 'foundation_building')
                })
        
        # 基于学习风格生成建议
        if report.ai_analysis and 'learning_style' in report.ai_analysis:
            style = report.ai_analysis['learning_style']
            if style.get('pace') == 'slow':
                recommendations.append({
                    'type': 'study_method',
                    'title': '提高学习效率',
                    'description': '建议采用番茄工作法，设定时间限制进行练习',
                    'priority': 'medium'
                })
        
        return recommendations
    
    @staticmethod
    def _get_diagnosis_responses(report: DiagnosisReport) -> List[QuestionResponse]:
        """获取诊断报告的所有答题记录"""
        responses = []
        for session in report.diagnosis_sessions:
            session_responses = QuestionResponse.query.filter_by(
                diagnosis_session_id=session.id
            ).all()
            responses.extend(session_responses)
        
        return responses
    
    @staticmethod
    def get_diagnosis_statistics(user_id: str, subject_id: str = None) -> Dict[str, Any]:
        """获取诊断统计信息"""
        query = DiagnosisReport.query.filter_by(user_id=user_id)
        if subject_id:
            query = query.filter_by(subject_id=subject_id)
        
        reports = query.all()
        
        if not reports:
            return {
                'total_diagnoses': 0,
                'avg_accuracy': 0,
                'improvement_trend': [],
                'knowledge_coverage': 0
            }
        
        # 计算统计数据
        total_diagnoses = len(reports)
        accuracies = [r.accuracy_rate for r in reports if r.accuracy_rate is not None]
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
        
        # 改进趋势（按时间排序）
        sorted_reports = sorted(reports, key=lambda r: r.created_at)
        improvement_trend = [{
            'date': r.created_at.strftime('%Y-%m-%d'),
            'accuracy': r.accuracy_rate or 0,
            'ability_estimate': r.ability_estimate or 0
        } for r in sorted_reports[-10:]]  # 最近10次
        
        # 知识点覆盖度
        all_kp_ids = set()
        for report in reports:
            if report.knowledge_point_ids:
                all_kp_ids.update(report.knowledge_point_ids)
        
        total_kps = KnowledgePoint.query.filter_by(subject_id=subject_id).count() if subject_id else 0
        knowledge_coverage = len(all_kp_ids) / max(1, total_kps) * 100
        
        return {
            'total_diagnoses': total_diagnoses,
            'avg_accuracy': round(avg_accuracy, 2),
            'improvement_trend': improvement_trend,
            'knowledge_coverage': round(knowledge_coverage, 2),
            'latest_ability_estimate': sorted_reports[-1].ability_estimate if sorted_reports else 0
        }