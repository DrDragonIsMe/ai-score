# -*- coding: utf-8 -*-
"""
应试优化API

提供限时模拟考试、时间分配策略和得分策略的API端点
"""

from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from typing import Dict, List, Optional

from services.exam_service import ExamService
from services.strategy_service import StrategyService
from models.exam import ExamSession, TimeAllocation, ScoringStrategy
from utils.validators import validate_required_fields, validate_enum_field
from utils.response import success_response, error_response
from utils.database import db

# 创建蓝图
exam_bp = Blueprint('exam', __name__, url_prefix='/exam')

# 初始化服务
exam_service = ExamService()
strategy_service = StrategyService()

# ==================== 考试会话管理 ====================

@exam_bp.route('/sessions', methods=['POST'])
@jwt_required()
def create_exam_session():
    """
    创建考试会话
    
    请求体:
    {
        "exam_name": "数学模拟考试",
        "exam_type": "mock",  # practice, mock, final
        "subject_id": 1,
        "total_questions": 50,
        "total_time_minutes": 120,
        "difficulty_level": "medium",  # easy, medium, hard, mixed
        "question_filters": {
            "knowledge_point_ids": [1, 2, 3],
            "question_types": ["single_choice", "multiple_choice"]
        },
        "time_allocation_id": 1,  # 可选
        "scoring_strategy_id": 1  # 可选
    }
    
    返回:
    {
        "code": 200,
        "message": "考试会话创建成功",
        "data": {
            "session_id": 1,
            "exam_name": "数学模拟考试",
            "status": "created",
            "total_questions": 50,
            "total_time_minutes": 120,
            "created_time": "2024-01-01T10:00:00"
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['exam_name', 'subject_id', 'total_questions', 'total_time_minutes']
        if not validate_required_fields(data, required_fields):
            return error_response('缺少必需字段', 400)
        
        # 验证枚举字段
        if not validate_enum_field(data.get('exam_type', 'practice'), 
                                 ['practice', 'mock', 'final']):
            return error_response('无效的考试类型', 400)
        
        if not validate_enum_field(data.get('difficulty_level', 'medium'), 
                                 ['easy', 'medium', 'hard', 'mixed']):
            return error_response('无效的难度级别', 400)
        
        # 创建考试会话
        exam_session = exam_service.create_exam_session(
            user_id=user_id,
            exam_config={
                'exam_name': data['exam_name'],
                'exam_type': data.get('exam_type', 'practice'),
                'subject_id': data['subject_id'],
                'total_questions': data['total_questions'],
                'total_time_minutes': data['total_time_minutes'],
                'difficulty_level': data.get('difficulty_level', 'medium'),
                'question_filters': data.get('question_filters', {}),
                'time_allocation_id': data.get('time_allocation_id'),
                'scoring_strategy_id': data.get('scoring_strategy_id')
            }
        )
        
        return success_response(
            message='考试会话创建成功',
            data={
                'session_id': exam_session.id,
                'exam_name': exam_session.exam_name,
                'status': exam_session.status,
                'total_questions': exam_session.total_questions,
                'total_time_minutes': exam_session.total_time_minutes,
                'created_time': exam_session.created_time.isoformat()
            }
        )
        
    except Exception as e:
        return error_response(f'创建考试会话失败: {str(e)}', 500)

@exam_bp.route('/sessions/<int:session_id>/start', methods=['POST'])
@jwt_required()
def start_exam(session_id: int):
    """
    开始考试
    
    返回:
    {
        "code": 200,
        "message": "考试开始成功",
        "data": {
            "session_id": 1,
            "status": "in_progress",
            "start_time": "2024-01-01T10:00:00",
            "end_time": "2024-01-01T12:00:00",
            "current_question": {
                "question_id": 1,
                "question_index": 0,
                "question_text": "题目内容",
                "options": ["A", "B", "C", "D"],
                "question_type": "single_choice"
            },
            "time_allocation_plan": {
                "easy_questions": {"count": 15, "time_per_question": 1.5},
                "medium_questions": {"count": 25, "time_per_question": 2.0},
                "hard_questions": {"count": 10, "time_per_question": 3.0}
            }
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        
        # 开始考试
        result = exam_service.start_exam(user_id, session_id)
        
        return success_response(
            message='考试开始成功',
            data=result
        )
        
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(f'开始考试失败: {str(e)}', 500)

@exam_bp.route('/sessions/<int:session_id>/answer', methods=['POST'])
@jwt_required()
def submit_answer(session_id: int):
    """
    提交答案
    
    请求体:
    {
        "question_id": 1,
        "answer": "A",
        "time_spent": 90,  # 秒
        "confidence_level": 0.8,  # 0-1
        "is_guess": false
    }
    
    返回:
    {
        "code": 200,
        "message": "答案提交成功",
        "data": {
            "is_correct": true,
            "score": 5,
            "explanation": "答案解析",
            "next_question": {
                "question_id": 2,
                "question_index": 1,
                "question_text": "下一题内容"
            },
            "progress": {
                "answered": 1,
                "total": 50,
                "percentage": 2.0
            },
            "time_status": {
                "elapsed_minutes": 1.5,
                "remaining_minutes": 118.5,
                "on_track": true
            }
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['question_id', 'answer', 'time_spent']
        if not validate_required_fields(data, required_fields):
            return error_response('缺少必需字段', 400)
        
        # 提交答案
        result = exam_service.submit_answer(
            user_id=user_id,
            session_id=session_id,
            question_id=data['question_id'],
            answer=data['answer'],
            time_spent=data['time_spent'],
            confidence_level=data.get('confidence_level'),
            is_guess=data.get('is_guess', False)
        )
        
        return success_response(
            message='答案提交成功',
            data=result
        )
        
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(f'提交答案失败: {str(e)}', 500)

@exam_bp.route('/sessions/<int:session_id>/pause', methods=['POST'])
@jwt_required()
def pause_exam(session_id: int):
    """
    暂停考试
    
    返回:
    {
        "code": 200,
        "message": "考试暂停成功",
        "data": {
            "session_id": 1,
            "status": "paused",
            "pause_time": "2024-01-01T10:30:00",
            "elapsed_time_minutes": 30
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        
        exam_session = exam_service.pause_exam(user_id, session_id)
        
        return success_response(
            message='考试暂停成功',
            data={
                'session_id': exam_session.id,
                'status': exam_session.status,
                'pause_time': exam_session.pause_time.isoformat() if exam_session.pause_time else None,
                'elapsed_time_minutes': exam_session.elapsed_time_minutes
            }
        )
        
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(f'暂停考试失败: {str(e)}', 500)

@exam_bp.route('/sessions/<int:session_id>/resume', methods=['POST'])
@jwt_required()
def resume_exam(session_id: int):
    """
    恢复考试
    
    返回:
    {
        "code": 200,
        "message": "考试恢复成功",
        "data": {
            "session_id": 1,
            "status": "in_progress",
            "resume_time": "2024-01-01T10:35:00",
            "remaining_time_minutes": 85
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        
        exam_session = exam_service.resume_exam(user_id, session_id)
        
        return success_response(
            message='考试恢复成功',
            data={
                'session_id': exam_session.id,
                'status': exam_session.status,
                'resume_time': datetime.now().isoformat(),
                'remaining_time_minutes': exam_session.get_remaining_time_minutes()
            }
        )
        
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(f'恢复考试失败: {str(e)}', 500)

@exam_bp.route('/sessions/<int:session_id>/complete', methods=['POST'])
@jwt_required()
def complete_exam(session_id: int):
    """
    完成考试
    
    返回:
    {
        "code": 200,
        "message": "考试完成",
        "data": {
            "session_id": 1,
            "status": "completed",
            "final_score": 85,
            "total_score": 100,
            "score_percentage": 85.0,
            "completion_rate": 100.0,
            "time_efficiency": 0.8,
            "analytics_id": 1
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        
        result = exam_service.complete_exam(user_id, session_id)
        
        return success_response(
            message='考试完成',
            data=result
        )
        
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(f'完成考试失败: {str(e)}', 500)

@exam_bp.route('/sessions/<int:session_id>', methods=['GET'])
@jwt_required()
def get_exam_session(session_id: int):
    """
    获取考试会话详情
    
    返回:
    {
        "code": 200,
        "message": "获取成功",
        "data": {
            "session_id": 1,
            "exam_name": "数学模拟考试",
            "status": "in_progress",
            "progress": {
                "answered": 25,
                "total": 50,
                "percentage": 50.0
            },
            "time_info": {
                "elapsed_minutes": 60,
                "remaining_minutes": 60,
                "total_minutes": 120
            },
            "score_info": {
                "current_score": 20,
                "max_possible_score": 25,
                "percentage": 80.0
            }
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        
        exam_session = exam_service.get_exam_session(user_id, session_id)
        
        return success_response(
            message='获取成功',
            data=exam_session.to_dict()
        )
        
    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f'获取考试会话失败: {str(e)}', 500)

@exam_bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_user_exam_sessions():
    """
    获取用户考试会话列表
    
    查询参数:
    - status: 状态筛选 (created, in_progress, paused, completed, expired)
    - exam_type: 考试类型筛选 (practice, mock, final)
    - subject_id: 科目筛选
    - page: 页码 (默认1)
    - per_page: 每页数量 (默认20)
    
    返回:
    {
        "code": 200,
        "message": "获取成功",
        "data": {
            "sessions": [
                {
                    "session_id": 1,
                    "exam_name": "数学模拟考试",
                    "status": "completed",
                    "score_percentage": 85.0,
                    "created_time": "2024-01-01T10:00:00"
                }
            ],
            "pagination": {
                "page": 1,
                "per_page": 20,
                "total": 1,
                "pages": 1
            }
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取查询参数
        status = request.args.get('status')
        exam_type = request.args.get('exam_type')
        subject_id = request.args.get('subject_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # 获取考试会话列表
        result = exam_service.get_user_exam_sessions(
            user_id=user_id,
            status=status,
            exam_type=exam_type,
            subject_id=subject_id,
            page=page,
            per_page=per_page
        )
        
        return success_response(
            message='获取成功',
            data=result
        )
        
    except Exception as e:
        return error_response(f'获取考试会话列表失败: {str(e)}', 500)

# ==================== 时间分配策略 ====================

@exam_bp.route('/time-allocations', methods=['POST'])
@jwt_required()
def create_time_allocation():
    """
    创建时间分配策略
    
    请求体:
    {
        "strategy_name": "快速答题策略",
        "strategy_description": "适合基础扎实的学生",
        "easy_question_time": 1.0,
        "medium_question_time": 2.0,
        "hard_question_time": 3.0,
        "review_time_percentage": 10.0,
        "buffer_time": 5.0
    }
    
    返回:
    {
        "code": 200,
        "message": "时间分配策略创建成功",
        "data": {
            "allocation_id": 1,
            "strategy_name": "快速答题策略",
            "total_time_requirement": 120.5
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['strategy_name']
        if not validate_required_fields(data, required_fields):
            return error_response('缺少必需字段', 400)
        
        # 创建时间分配策略
        time_allocation = strategy_service.create_time_allocation_strategy(
            user_id=user_id,
            strategy_config=data
        )
        
        return success_response(
            message='时间分配策略创建成功',
            data={
                'allocation_id': time_allocation.id,
                'strategy_name': time_allocation.strategy_name,
                'total_time_requirement': time_allocation.get_total_time_requirement(50)  # 假设50题
            }
        )
        
    except Exception as e:
        return error_response(f'创建时间分配策略失败: {str(e)}', 500)

@exam_bp.route('/time-allocations/recommendations', methods=['POST'])
@jwt_required()
def get_time_allocation_recommendations():
    """
    获取时间分配建议
    
    请求体:
    {
        "total_time_minutes": 120,
        "total_questions": 50,
        "difficulty_distribution": {
            "easy": 0.3,
            "medium": 0.5,
            "hard": 0.2
        },
        "subject_id": 1
    }
    
    返回:
    {
        "code": 200,
        "message": "获取建议成功",
        "data": {
            "strategy_name": "个性化时间分配策略",
            "question_time_allocation": {
                "easy_questions": {"count": 15, "time_per_question": 1.2, "total_time": 18.0},
                "medium_questions": {"count": 25, "time_per_question": 2.0, "total_time": 50.0},
                "hard_questions": {"count": 10, "time_per_question": 3.5, "total_time": 35.0}
            },
            "review_time_minutes": 12.0,
            "buffer_time_minutes": 5.0,
            "time_checkpoints": [
                {"progress_percentage": 25, "target_question": 13, "target_time_minutes": 25.8}
            ],
            "recommendations": ["建议预留10-15%的时间用于检查"]
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['total_time_minutes', 'total_questions']
        if not validate_required_fields(data, required_fields):
            return error_response('缺少必需字段', 400)
        
        # 获取时间分配建议
        recommendations = strategy_service.get_optimal_time_allocation(
            user_id=user_id,
            exam_config=data
        )
        
        return success_response(
            message='获取建议成功',
            data=recommendations
        )
        
    except Exception as e:
        return error_response(f'获取时间分配建议失败: {str(e)}', 500)

@exam_bp.route('/time-allocations', methods=['GET'])
@jwt_required()
def get_user_time_allocations():
    """
    获取用户时间分配策略列表
    
    返回:
    {
        "code": 200,
        "message": "获取成功",
        "data": {
            "time_allocations": [
                {
                    "allocation_id": 1,
                    "strategy_name": "快速答题策略",
                    "effectiveness_score": 0.85,
                    "usage_count": 5,
                    "created_time": "2024-01-01T10:00:00"
                }
            ]
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        
        time_allocations = strategy_service.get_user_time_allocations(user_id)
        
        return success_response(
            message='获取成功',
            data={
                'time_allocations': [allocation.to_dict() for allocation in time_allocations]
            }
        )
        
    except Exception as e:
        return error_response(f'获取时间分配策略失败: {str(e)}', 500)

# ==================== 得分策略 ====================

@exam_bp.route('/scoring-strategies', methods=['POST'])
@jwt_required()
def create_scoring_strategy():
    """
    创建得分策略
    
    请求体:
    {
        "strategy_name": "稳健得分策略",
        "strategy_type": "conservative",  # conservative, aggressive, balanced
        "skip_threshold": 0.3,
        "guess_threshold": 0.5,
        "time_pressure_threshold": 0.8,
        "answer_order_strategy": "difficulty_ascending",
        "review_strategy": "uncertain_first",
        "risk_tolerance": 0.3
    }
    
    返回:
    {
        "code": 200,
        "message": "得分策略创建成功",
        "data": {
            "strategy_id": 1,
            "strategy_name": "稳健得分策略",
            "strategy_type": "conservative"
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['strategy_name']
        if not validate_required_fields(data, required_fields):
            return error_response('缺少必需字段', 400)
        
        # 验证策略类型
        if not validate_enum_field(data.get('strategy_type', 'balanced'), 
                                 ['conservative', 'aggressive', 'balanced']):
            return error_response('无效的策略类型', 400)
        
        # 创建得分策略
        scoring_strategy = strategy_service.create_scoring_strategy(
            user_id=user_id,
            strategy_config=data
        )
        
        return success_response(
            message='得分策略创建成功',
            data={
                'strategy_id': scoring_strategy.id,
                'strategy_name': scoring_strategy.strategy_name,
                'strategy_type': scoring_strategy.strategy_type
            }
        )
        
    except Exception as e:
        return error_response(f'创建得分策略失败: {str(e)}', 500)

@exam_bp.route('/scoring-strategies/recommendations', methods=['POST'])
@jwt_required()
def get_scoring_strategy_recommendations():
    """
    获取得分策略建议
    
    请求体:
    {
        "exam_type": "mock",
        "subject_id": 1,
        "total_time_minutes": 120,
        "total_questions": 50
    }
    
    返回:
    {
        "code": 200,
        "message": "获取建议成功",
        "data": {
            "strategy_name": "平衡得分策略",
            "strategy_type": "balanced",
            "core_principles": ["平衡准确率和完成率"],
            "answer_order": "sequential",
            "time_allocation": {
                "easy_questions": "快速准确",
                "medium_questions": "重点关注",
                "hard_questions": "量力而行"
            },
            "general_tips": ["仔细阅读题目，避免因理解错误而失分"],
            "exam_specific_tips": ["平均每题建议用时2.4分钟"]
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 获取得分策略建议
        recommendations = strategy_service.get_optimal_scoring_strategy(
            user_id=user_id,
            exam_config=data
        )
        
        return success_response(
            message='获取建议成功',
            data=recommendations
        )
        
    except Exception as e:
        return error_response(f'获取得分策略建议失败: {str(e)}', 500)

@exam_bp.route('/scoring-strategies', methods=['GET'])
@jwt_required()
def get_user_scoring_strategies():
    """
    获取用户得分策略列表
    
    返回:
    {
        "code": 200,
        "message": "获取成功",
        "data": {
            "scoring_strategies": [
                {
                    "strategy_id": 1,
                    "strategy_name": "稳健得分策略",
                    "strategy_type": "conservative",
                    "average_score": 85.5,
                    "usage_count": 3,
                    "created_time": "2024-01-01T10:00:00"
                }
            ]
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        
        scoring_strategies = strategy_service.get_user_scoring_strategies(user_id)
        
        return success_response(
            message='获取成功',
            data={
                'scoring_strategies': [strategy.to_dict() for strategy in scoring_strategies]
            }
        )
        
    except Exception as e:
        return error_response(f'获取得分策略失败: {str(e)}', 500)

# ==================== 统计和分析 ====================

@exam_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_exam_statistics():
    """
    获取考试统计信息
    
    查询参数:
    - subject_id: 科目筛选
    - exam_type: 考试类型筛选
    - days: 统计天数 (默认30)
    
    返回:
    {
        "code": 200,
        "message": "获取成功",
        "data": {
            "total_exams": 10,
            "completed_exams": 8,
            "completion_rate": 80.0,
            "average_score": 75.5,
            "total_time_hours": 20.5,
            "exam_type_distribution": {
                "practice": 5,
                "mock": 3,
                "final": 2
            },
            "score_distribution": {
                "90-100": 2,
                "80-89": 3,
                "70-79": 2,
                "60-69": 1,
                "below_60": 0
            },
            "improvement_trend": [
                {"week": "2024-W01", "average_score": 70.0, "exam_count": 2},
                {"week": "2024-W02", "average_score": 75.0, "exam_count": 3}
            ]
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取查询参数
        subject_id = request.args.get('subject_id', type=int)
        exam_type = request.args.get('exam_type')
        days = request.args.get('days', 30, type=int)
        
        # 获取统计信息
        statistics = exam_service.get_exam_statistics(
            user_id=user_id,
            subject_id=subject_id,
            exam_type=exam_type,
            days=days
        )
        
        return success_response(
            message='获取成功',
            data=statistics
        )
        
    except Exception as e:
        return error_response(f'获取考试统计失败: {str(e)}', 500)

@exam_bp.route('/analytics/<int:analytics_id>', methods=['GET'])
@jwt_required()
def get_exam_analytics(analytics_id: int):
    """
    获取考试分析报告
    
    返回:
    {
        "code": 200,
        "message": "获取成功",
        "data": {
            "analytics_id": 1,
            "session_id": 1,
            "time_analysis": {
                "total_time_minutes": 115.5,
                "average_time_per_question": 2.31,
                "time_efficiency": 0.85
            },
            "answer_analysis": {
                "completion_rate": 100.0,
                "accuracy_rate": 85.0,
                "skip_rate": 0.0
            },
            "strategy_analysis": {
                "strategy_adherence": 0.9,
                "effective_decisions": 42,
                "questionable_decisions": 3
            },
            "strengths": ["时间管理良好", "基础题目准确率高"],
            "weaknesses": ["困难题目准确率有待提高"],
            "improvement_suggestions": [
                {"priority": "high", "suggestion": "加强困难题目练习"},
                {"priority": "medium", "suggestion": "提高答题速度"}
            ]
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        
        # 这里需要实现获取分析报告的逻辑
        # 暂时返回示例数据
        analytics_data = {
            'analytics_id': analytics_id,
            'message': '分析报告功能正在开发中'
        }
        
        return success_response(
            message='获取成功',
            data=analytics_data
        )
        
    except Exception as e:
        return error_response(f'获取考试分析失败: {str(e)}', 500)

@exam_bp.route('/strategies/recommendations', methods=['GET'])
@jwt_required()
def get_strategy_recommendations():
    """
    获取策略优化建议
    
    返回:
    {
        "code": 200,
        "message": "获取成功",
        "data": {
            "time_allocation_suggestions": [
                "建议减少每题平均用时，提高答题速度"
            ],
            "scoring_strategy_suggestions": [
                "基础扎实，可以尝试更进取的策略"
            ],
            "general_improvements": [
                "定期回顾和调整策略，根据实际表现进行优化"
            ]
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        
        recommendations = strategy_service.get_strategy_recommendations(user_id)
        
        return success_response(
            message='获取成功',
            data=recommendations
        )
        
    except Exception as e:
        return error_response(f'获取策略建议失败: {str(e)}', 500)

# ==================== 辅助接口 ====================

@exam_bp.route('/types', methods=['GET'])
def get_exam_types():
    """
    获取考试类型列表
    
    返回:
    {
        "code": 200,
        "message": "获取成功",
        "data": {
            "exam_types": [
                {"value": "practice", "label": "练习考试", "description": "日常练习，不计入正式成绩"},
                {"value": "mock", "label": "模拟考试", "description": "模拟正式考试环境"},
                {"value": "final", "label": "正式考试", "description": "正式考试，计入成绩"}
            ]
        }
    }
    """
    exam_types = [
        {'value': 'practice', 'label': '练习考试', 'description': '日常练习，不计入正式成绩'},
        {'value': 'mock', 'label': '模拟考试', 'description': '模拟正式考试环境'},
        {'value': 'final', 'label': '正式考试', 'description': '正式考试，计入成绩'}
    ]
    
    return success_response(
        message='获取成功',
        data={'exam_types': exam_types}
    )

@exam_bp.route('/difficulty-levels', methods=['GET'])
def get_difficulty_levels():
    """
    获取难度级别列表
    
    返回:
    {
        "code": 200,
        "message": "获取成功",
        "data": {
            "difficulty_levels": [
                {"value": "easy", "label": "简单", "description": "基础题目，适合入门"},
                {"value": "medium", "label": "中等", "description": "中等难度，适合提高"},
                {"value": "hard", "label": "困难", "description": "高难度题目，适合挑战"},
                {"value": "mixed", "label": "混合", "description": "包含各种难度的题目"}
            ]
        }
    }
    """
    difficulty_levels = [
        {'value': 'easy', 'label': '简单', 'description': '基础题目，适合入门'},
        {'value': 'medium', 'label': '中等', 'description': '中等难度，适合提高'},
        {'value': 'hard', 'label': '困难', 'description': '高难度题目，适合挑战'},
        {'value': 'mixed', 'label': '混合', 'description': '包含各种难度的题目'}
    ]
    
    return success_response(
        message='获取成功',
        data={'difficulty_levels': difficulty_levels}
    )

@exam_bp.route('/strategy-types', methods=['GET'])
def get_strategy_types():
    """
    获取策略类型列表
    
    返回:
    {
        "code": 200,
        "message": "获取成功",
        "data": {
            "strategy_types": [
                {"value": "conservative", "label": "保守型", "description": "注重准确率，稳扎稳打"},
                {"value": "aggressive", "label": "进取型", "description": "追求高分，敢于挑战"},
                {"value": "balanced", "label": "平衡型", "description": "平衡各方面因素"}
            ]
        }
    }
    """
    strategy_types = [
        {'value': 'conservative', 'label': '保守型', 'description': '注重准确率，稳扎稳打'},
        {'value': 'aggressive', 'label': '进取型', 'description': '追求高分，敢于挑战'},
        {'value': 'balanced', 'label': '平衡型', 'description': '平衡各方面因素'}
    ]
    
    return success_response(
        message='获取成功',
        data={'strategy_types': strategy_types}
    )