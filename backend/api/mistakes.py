#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - API接口 - mistakes.py

Description:
    错题管理API接口，提供错题收集、分析、复习等功能。

Author: Chang Xinglong
Date: 2025-08-30
Version: 1.0.0
License: Apache License 2.0
"""


from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from typing import Dict, List, Optional

from services.mistake_service import MistakeService
from services.tutoring_service import TutoringService
from models.mistake import MistakeType, MistakeLevel
from utils.response import success_response, error_response
from utils.validators import validate_required_fields
from utils.logger import get_logger

logger = get_logger(__name__)

# 创建蓝图
mistakes_bp = Blueprint('mistakes', __name__, url_prefix='/api/mistakes')

# 初始化服务
mistake_service = MistakeService()
tutoring_service = TutoringService()

# ==================== 错题管理API ====================

@mistakes_bp.route('/records', methods=['POST'])
@jwt_required()
def create_mistake_record():
    """
    创建错题记录
    
    请求体:
    {
        "question_id": 123,
        "user_answer": "用户答案",
        "correct_answer": "正确答案",
        "auto_analyze": true
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证请求数据
        required_fields = ['question_id', 'user_answer', 'correct_answer']
        is_valid, error_msg = validate_required_fields(data, required_fields)
        if not is_valid:
            return error_response(
                message=error_msg,
                code=400
            )
        
        # 创建错题记录
        mistake_record = mistake_service.create_mistake_record(
            user_id=user_id,
            question_id=data['question_id'],
            user_answer=data['user_answer'],
            correct_answer=data['correct_answer'],
            auto_analyze=data.get('auto_analyze', True)
        )
        
        if not mistake_record:
            return error_response(
                message="创建错题记录失败",
                code=500
            )
        
        return success_response(
            data=mistake_record.to_dict(),
            message="错题记录创建成功"
        )
        
    except Exception as e:
        logger.error(f"创建错题记录API错误: {str(e)}")
        return error_response(
            message="服务器内部错误",
            code=500
        )

@mistakes_bp.route('/records', methods=['GET'])
@jwt_required()
def get_mistake_records():
    """
    获取错题记录列表
    
    查询参数:
    - page: 页码 (默认1)
    - per_page: 每页数量 (默认20)
    - subject_id: 学科ID
    - mistake_type: 错误类型
    - mistake_level: 错误严重程度
    - is_resolved: 是否已解决
    - review_urgency: 复习紧急程度 (urgent/due)
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # 构建筛选条件
        filters = {}
        if request.args.get('subject_id'):
            filters['subject_id'] = request.args.get('subject_id', type=int)
        if request.args.get('mistake_type'):
            filters['mistake_type'] = request.args.get('mistake_type')
        if request.args.get('mistake_level'):
            filters['mistake_level'] = request.args.get('mistake_level')
        if request.args.get('is_resolved') is not None:
            filters['is_resolved'] = request.args.get('is_resolved', type=bool)
        if request.args.get('review_urgency'):
            filters['review_urgency'] = request.args.get('review_urgency')
        
        # 获取错题记录
        result = mistake_service.get_mistake_records(
            user_id=user_id,
            filters=filters,
            page=page,
            per_page=per_page
        )
        
        return success_response(
            data=result,
            message="获取错题记录成功"
        )
        
    except Exception as e:
        logger.error(f"获取错题记录API错误: {str(e)}")
        return error_response(
            message="服务器内部错误",
            code=500
        )

@mistakes_bp.route('/records/<int:mistake_id>', methods=['GET'])
@jwt_required()
def get_mistake_record(mistake_id: int):
    """
    获取单个错题记录详情
    """
    try:
        user_id = get_jwt_identity()
        
        from models.mistake import MistakeRecord
        mistake_record = MistakeRecord.query.filter_by(
            id=mistake_id, user_id=user_id
        ).first()
        
        if not mistake_record:
            return error_response(
                message="错题记录不存在",
                code=404
            )
        
        return success_response(
            data=mistake_record.to_dict(),
            message="获取错题记录成功"
        )
        
    except Exception as e:
        logger.error(f"获取错题记录详情API错误: {str(e)}")
        return error_response(
            message="服务器内部错误",
            code=500
        )

@mistakes_bp.route('/records/<int:mistake_id>/review', methods=['POST'])
@jwt_required()
def review_mistake(mistake_id: int):
    """
    复习错题
    
    请求体:
    {
        "user_answer": "用户答案",
        "is_correct": true,
        "confidence_level": 4,
        "response_time": 120,
        "user_feedback": "用户反馈"
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        # 复习错题
        review_session = mistake_service.review_mistake(
            mistake_id=mistake_id,
            user_id=user_id,
            user_answer=data.get('user_answer'),
            is_correct=data.get('is_correct'),
            confidence_level=data.get('confidence_level'),
            response_time=data.get('response_time'),
            user_feedback=data.get('user_feedback')
        )
        
        if not review_session:
            return error_response(
                message="复习错题失败",
                code=500
            )
        
        return success_response(
            data=review_session.to_dict(),
            message="错题复习完成"
        )
        
    except Exception as e:
        logger.error(f"复习错题API错误: {str(e)}")
        return error_response(
            message="服务器内部错误",
            code=500
        )

@mistakes_bp.route('/records/<int:mistake_id>/archive', methods=['POST'])
@jwt_required()
def archive_mistake(mistake_id: int):
    """
    归档错题
    """
    try:
        user_id = get_jwt_identity()
        
        success = mistake_service.archive_mistake(mistake_id, user_id)
        
        if not success:
            return error_response(
                message="归档错题失败",
                code=500
            )
        
        return success_response(
            message="错题归档成功"
        )
        
    except Exception as e:
        logger.error(f"归档错题API错误: {str(e)}")
        return error_response(
            message="服务器内部错误",
            code=500
        )

@mistakes_bp.route('/records/batch', methods=['POST'])
@jwt_required()
def batch_create_mistakes():
    """
    批量创建错题记录
    
    请求体:
    {
        "mistakes": [
            {
                "question_id": 123,
                "user_answer": "用户答案",
                "correct_answer": "正确答案",
                "auto_analyze": true
            }
        ]
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'mistakes' not in data:
            return error_response(
                message="请提供错题数据",
                code=400
            )
        
        mistakes_data = data['mistakes']
        if not isinstance(mistakes_data, list) or len(mistakes_data) == 0:
            return error_response(
                message="错题数据格式错误",
                code=400
            )
        
        # 批量创建错题
        result = mistake_service.batch_create_mistakes(user_id, mistakes_data)
        
        return success_response(
            data=result,
            message=f"批量创建完成，成功{result['created_count']}个，失败{result['failed_count']}个"
        )
        
    except Exception as e:
        logger.error(f"批量创建错题API错误: {str(e)}")
        return error_response(
            message="服务器内部错误",
            code=500
        )

@mistakes_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_mistake_statistics():
    """
    获取错题统计信息
    
    查询参数:
    - days: 统计天数 (默认30)
    """
    try:
        user_id = get_jwt_identity()
        days = request.args.get('days', 30, type=int)
        
        statistics = mistake_service.get_mistake_statistics(user_id, days)
        
        return success_response(
            data=statistics,
            message="获取错题统计成功"
        )
        
    except Exception as e:
        logger.error(f"获取错题统计API错误: {str(e)}")
        return error_response(
            message="服务器内部错误",
            code=500
        )

@mistakes_bp.route('/patterns', methods=['GET'])
@jwt_required()
def get_mistake_patterns():
    """
    获取错误模式
    """
    try:
        user_id = get_jwt_identity()
        
        patterns = mistake_service.get_mistake_patterns(user_id)
        
        return success_response(
            data=patterns,
            message="获取错误模式成功"
        )
        
    except Exception as e:
        logger.error(f"获取错误模式API错误: {str(e)}")
        return error_response(
            message="服务器内部错误",
            code=500
        )

@mistakes_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_review_recommendations():
    """
    获取复习推荐
    
    查询参数:
    - limit: 推荐数量 (默认10)
    """
    try:
        user_id = get_jwt_identity()
        limit = min(request.args.get('limit', 10, type=int), 50)
        
        recommendations = mistake_service.get_review_recommendations(user_id, limit)
        
        return success_response(
            data=recommendations,
            message="获取复习推荐成功"
        )
        
    except Exception as e:
        logger.error(f"获取复习推荐API错误: {str(e)}")
        return error_response(
            message="服务器内部错误",
            code=500
        )

# ==================== 分层解题辅导API ====================

@mistakes_bp.route('/tutoring/sessions', methods=['POST'])
@jwt_required()
def start_tutoring_session():
    """
    开始辅导会话
    
    请求体:
    {
        "question_id": 123,
        "session_type": "problem_solving"
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证请求数据
        if not data or 'question_id' not in data:
            return error_response(
                message="请提供题目ID",
                code=400
            )
        
        # 开始辅导会话
        session = tutoring_service.start_tutoring_session(
            user_id=user_id,
            question_id=data['question_id'],
            session_type=data.get('session_type', 'problem_solving')
        )
        
        if not session:
            return error_response(
                message="开始辅导会话失败",
                code=500
            )
        
        return success_response(
            data=session.to_dict(),
            message="辅导会话开始成功"
        )
        
    except Exception as e:
        logger.error(f"开始辅导会话API错误: {str(e)}")
        return error_response(
            message="服务器内部错误",
            code=500
        )

@mistakes_bp.route('/tutoring/sessions/<int:session_id>', methods=['GET'])
@jwt_required()
def get_tutoring_session(session_id: int):
    """
    获取辅导会话信息
    """
    try:
        session_info = tutoring_service.get_tutoring_session(session_id)
        
        if not session_info:
            return error_response(
                message="辅导会话不存在",
                code=404
            )
        
        return success_response(
            data=session_info,
            message="获取辅导会话成功"
        )
        
    except Exception as e:
        logger.error(f"获取辅导会话API错误: {str(e)}")
        return error_response(
            message="服务器内部错误",
            code=500
        )

@mistakes_bp.route('/tutoring/sessions/<int:session_id>/tutor', methods=['POST'])
@jwt_required()
def provide_tutoring(session_id: int):
    """
    提供分层辅导
    
    请求体:
    {
        "user_response": "用户回应",
        "understanding_level": 3
    }
    """
    try:
        data = request.get_json() or {}
        
        # 提供辅导
        result = tutoring_service.provide_tutoring(
            session_id=session_id,
            user_response=data.get('user_response'),
            understanding_level=data.get('understanding_level')
        )
        
        if not result['success']:
            return error_response(
                message=result['message'],
                code=400
            )
        
        return success_response(
            data={
                'tutoring_content': result['tutoring_content'],
                'strategy': result['strategy'],
                'session_status': result['session_status']
            },
            message="辅导提供成功"
        )
        
    except Exception as e:
        logger.error(f"提供辅导API错误: {str(e)}")
        return error_response(
            message="服务器内部错误",
            code=500
        )

@mistakes_bp.route('/tutoring/sessions/<int:session_id>/end', methods=['POST'])
@jwt_required()
def end_tutoring_session(session_id: int):
    """
    结束辅导会话
    
    请求体:
    {
        "user_feedback": "用户反馈"
    }
    """
    try:
        data = request.get_json() or {}
        
        success = tutoring_service.end_tutoring_session(
            session_id=session_id,
            user_feedback=data.get('user_feedback')
        )
        
        if not success:
            return error_response(
                message="结束辅导会话失败",
                code=500
            )
        
        return success_response(
            message="辅导会话结束成功"
        )
        
    except Exception as e:
        logger.error(f"结束辅导会话API错误: {str(e)}")
        return error_response(
            message="服务器内部错误",
            code=500
        )

@mistakes_bp.route('/tutoring/sessions', methods=['GET'])
@jwt_required()
def get_user_tutoring_sessions():
    """
    获取用户的辅导会话列表
    
    查询参数:
    - limit: 限制数量 (默认10)
    """
    try:
        user_id = get_jwt_identity()
        limit = min(request.args.get('limit', 10, type=int), 50)
        
        sessions = tutoring_service.get_user_tutoring_sessions(user_id, limit)
        
        return success_response(
            data=sessions,
            message="获取辅导会话列表成功"
        )
        
    except Exception as e:
        logger.error(f"获取辅导会话列表API错误: {str(e)}")
        return error_response(
            message="服务器内部错误",
            code=500
        )

@mistakes_bp.route('/tutoring/statistics', methods=['GET'])
@jwt_required()
def get_tutoring_statistics():
    """
    获取辅导统计信息
    
    查询参数:
    - days: 统计天数 (默认30)
    """
    try:
        user_id = get_jwt_identity()
        days = request.args.get('days', 30, type=int)
        
        statistics = tutoring_service.get_tutoring_statistics(user_id, days)
        
        return success_response(
            data=statistics,
            message="获取辅导统计成功"
        )
        
    except Exception as e:
        logger.error(f"获取辅导统计API错误: {str(e)}")
        return error_response(
            message="服务器内部错误",
            code=500
        )

# ==================== 辅助API ====================

@mistakes_bp.route('/types', methods=['GET'])
def get_mistake_types():
    """
    获取错误类型列表
    """
    try:
        types = [
            {'value': mistake_type.value, 'label': mistake_type.value}
            for mistake_type in MistakeType
        ]
        
        return success_response(
            data=types,
            message="获取错误类型成功"
        )
        
    except Exception as e:
        logger.error(f"获取错误类型API错误: {str(e)}")
        return error_response(
            message="服务器内部错误",
            code=500
        )

@mistakes_bp.route('/levels', methods=['GET'])
def get_mistake_levels():
    """
    获取错误严重程度列表
    """
    try:
        levels = [
            {'value': mistake_level.value, 'label': mistake_level.value}
            for mistake_level in MistakeLevel
        ]
        
        return success_response(
            data=levels,
            message="获取错误严重程度成功"
        )
        
    except Exception as e:
        logger.error(f"获取错误严重程度API错误: {str(e)}")
        return error_response(
            message="服务器内部错误",
            code=500
        )

# ==================== 错误处理 ====================

@mistakes_bp.errorhandler(400)
def bad_request(error):
    return error_response(
        message="请求参数错误",
        code=400
    )

@mistakes_bp.errorhandler(401)
def unauthorized(error):
    return error_response(
        message="未授权访问",
        code=401
    )

@mistakes_bp.errorhandler(403)
def forbidden(error):
    return error_response(
        message="禁止访问",
        code=403
    )

@mistakes_bp.errorhandler(404)
def not_found(error):
    return error_response(
        message="资源不存在",
        code=404
    )

@mistakes_bp.errorhandler(500)
def internal_error(error):
    return error_response(
        message="服务器内部错误",
        code=500
    )