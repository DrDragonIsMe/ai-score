#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - API接口 - diagnosis.py

Description:
    诊断数据模型，定义学习诊断结果和分析数据。

Author: Chang Xinglong
Date: 2025-08-31
Version: 1.0.0
License: Apache License 2.0
"""


from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from services.diagnosis_service import DiagnosisService
from services.adaptive_service import AdaptiveService
from services.learning_profile_service import LearningProfileService
from models.diagnosis import DiagnosisReport, DiagnosisSession, DiagnosisType, DiagnosisLevel
from models.user import User
from models.knowledge import Subject
from utils.decorators import admin_required
from utils.response import success_response, error_response
from datetime import datetime
from typing import Dict, Any

diagnosis_bp = Blueprint('diagnosis', __name__, url_prefix='/api/diagnosis')

# 请求验证模式
class DiagnosisCreateSchema(Schema):
    """创建诊断请求验证"""
    subject_id = fields.Str(required=True, error_messages={'required': '学科ID不能为空'})
    name = fields.Str(load_default=None)
    description = fields.Str(load_default='')
    diagnosis_type = fields.Str(load_default='comprehensive', validate=lambda x: x in ['basic', 'comprehensive', 'adaptive', 'targeted'])
    target_level = fields.Str(load_default='transfer', validate=lambda x: x in ['memory', 'application', 'transfer'])
    total_questions = fields.Int(load_default=30, validate=lambda x: 5 <= x <= 100)
    time_limit = fields.Int(load_default=60, validate=lambda x: x > 0)
    difficulty_range = fields.Dict(load_default={'min': 1, 'max': 5})
    adaptive_enabled = fields.Bool(load_default=True)

class SessionCreateSchema(Schema):
    """创建诊断会话请求验证"""
    name = fields.Str(load_default=None)
    session_type = fields.Str(required=True, validate=lambda x: x in ['memory', 'application', 'transfer'])
    max_questions = fields.Int(load_default=30, validate=lambda x: 5 <= x <= 50)
    min_questions = fields.Int(load_default=10, validate=lambda x: 3 <= x <= 20)
    target_precision = fields.Float(load_default=0.3, validate=lambda x: 0.1 <= x <= 1.0)

class AnswerSubmitSchema(Schema):
    """提交答案请求验证"""
    question_id = fields.Str(required=True)
    knowledge_point_id = fields.Str(required=True)
    question_content = fields.Str(required=True)
    question_type = fields.Str(required=True)
    difficulty_level = fields.Int(required=True, validate=lambda x: 1 <= x <= 5)
    user_answer = fields.Str(required=True)
    correct_answer = fields.Str(required=True)
    is_correct = fields.Bool(required=True)
    time_spent = fields.Int(required=True, validate=lambda x: x >= 0)
    confidence_level = fields.Int(load_default=3, validate=lambda x: 1 <= x <= 5)
    error_type = fields.Str(load_default=None)
    solution_steps = fields.List(fields.Dict(), load_default=[])

class DiagnosisSearchSchema(Schema):
    """诊断搜索请求验证"""
    subject_id = fields.Str(load_default=None)
    diagnosis_type = fields.Str(load_default=None)
    status = fields.Str(load_default=None)
    start_date = fields.DateTime(load_default=None)
    end_date = fields.DateTime(load_default=None)
    page = fields.Int(load_default=1, validate=lambda x: x > 0)
    per_page = fields.Int(load_default=20, validate=lambda x: 1 <= x <= 100)

@diagnosis_bp.route('/reports', methods=['GET'])
@jwt_required()
def get_diagnosis_reports(current_user):
    """获取诊断报告列表"""
    try:
        # 验证请求参数
        schema = DiagnosisSearchSchema()
        loaded_params = schema.load(request.args)
        params: Dict[str, Any] = loaded_params if isinstance(loaded_params, dict) else {}
        
        # 构建查询
        query = DiagnosisReport.query.filter_by(user_id=current_user.id)
        
        subject_id = params.get('subject_id')
        if subject_id:
            query = query.filter_by(subject_id=subject_id)
        
        diagnosis_type = params.get('diagnosis_type')
        if diagnosis_type:
            query = query.filter_by(diagnosis_type=DiagnosisType(diagnosis_type))
        
        status = params.get('status')
        if status:
            from models.diagnosis import DiagnosisStatus
            query = query.filter_by(status=DiagnosisStatus(status))
        
        start_date = params.get('start_date')
        if start_date:
            query = query.filter(DiagnosisReport.created_at >= start_date)
        
        end_date = params.get('end_date')
        if end_date:
            query = query.filter(DiagnosisReport.created_at <= end_date)
        
        # 分页查询
        page = params.get('page', 1)
        per_page = params.get('per_page', 20)
        
        pagination = query.order_by(DiagnosisReport.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        reports = [report.to_dict() for report in pagination.items]
        
        return success_response({
            'reports': reports,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })
        
    except ValidationError as e:
        return error_response('参数验证失败')
    except Exception as e:
        return error_response(f'获取诊断报告失败: {str(e)}')

@diagnosis_bp.route('/reports', methods=['POST'])
@jwt_required()
def create_diagnosis_report(current_user):
    """创建诊断报告"""
    try:
        # 验证请求数据
        schema = DiagnosisCreateSchema()
        loaded_data = schema.load(request.get_json() or {})
        data: Dict[str, Any] = loaded_data if isinstance(loaded_data, dict) else {}
        
        # 验证学科是否存在
        subject = Subject.query.get(data['subject_id'])
        if not subject:
            return error_response('学科不存在')
        
        # 创建诊断报告
        report = DiagnosisService.create_diagnosis_report(
            user_id=current_user.id,
            subject_id=data['subject_id'],
            diagnosis_config=data
        )
        
        return success_response({
            'report': report.to_dict(include_details=True),
            'message': '诊断报告创建成功'
        })
        
    except ValidationError as e:
        return error_response('参数验证失败')
    except Exception as e:
        return error_response(f'创建诊断报告失败: {str(e)}')

@diagnosis_bp.route('/reports/<report_id>', methods=['GET'])
@jwt_required()
def get_diagnosis_report(current_user, report_id):
    """获取诊断报告详情"""
    try:
        report = DiagnosisReport.query.filter_by(
            id=report_id, 
            user_id=current_user.id
        ).first()
        
        if not report:
            return error_response('诊断报告不存在')
        
        return success_response({
            'report': report.to_dict(include_details=True)
        })
        
    except Exception as e:
        return error_response(f'获取诊断报告失败: {str(e)}')

@diagnosis_bp.route('/reports/<report_id>/sessions', methods=['POST'])
@jwt_required()
def create_diagnosis_session(current_user, report_id):
    """创建诊断会话"""
    try:
        # 验证报告是否存在且属于当前用户
        report = DiagnosisReport.query.filter_by(
            id=report_id, 
            user_id=current_user.id
        ).first()
        
        if not report:
            return error_response('诊断报告不存在')
        
        # 验证请求数据
        schema = SessionCreateSchema()
        loaded_data = schema.load(request.get_json() or {})
        data: Dict[str, Any] = loaded_data if isinstance(loaded_data, dict) else {}
        
        # 创建诊断会话
        session = DiagnosisService.start_adaptive_diagnosis(
            report_id=report_id,
            session_config=data
        )
        
        return success_response({
            'session': session.to_dict(),
            'message': '诊断会话创建成功'
        })
        
    except ValidationError as e:
        return error_response('参数验证失败')
    except Exception as e:
        return error_response(f'创建诊断会话失败: {str(e)}')

@diagnosis_bp.route('/sessions/<session_id>/next-question', methods=['GET'])
@jwt_required()
def get_next_question(current_user, session_id):
    """获取下一道自适应题目"""
    try:
        # 验证会话是否存在且属于当前用户
        session = DiagnosisSession.query.join(DiagnosisReport).filter(
            DiagnosisSession.id == session_id,
            DiagnosisReport.user_id == current_user.id
        ).first()
        
        if not session:
            return error_response('诊断会话不存在')
        
        # 获取下一道题目
        result = DiagnosisService.get_next_question(session_id, session.diagnosis_report.subject_id)
        
        # 如果诊断完成，添加学习建议
        if result.get('finished'):
            learning_profile = LearningProfileService.get_profile_summary(current_user.id)
            result['learning_suggestions'] = learning_profile.get('recommendations', [])
        
        return success_response(result)
        
    except Exception as e:
        return error_response(f'获取题目失败: {str(e)}')

@diagnosis_bp.route('/sessions/<session_id>/submit-answer', methods=['POST'])
@jwt_required()
def submit_answer(current_user, session_id):
    """提交答案"""
    try:
        # 验证会话是否存在且属于当前用户
        session = DiagnosisSession.query.join(DiagnosisReport).filter(
            DiagnosisSession.id == session_id,
            DiagnosisReport.user_id == current_user.id
        ).first()
        
        if not session:
            return error_response('诊断会话不存在')
        
        # 验证请求数据
        schema = AnswerSubmitSchema()
        loaded_data = schema.load(request.get_json() or {})
        data: Dict[str, Any] = loaded_data if isinstance(loaded_data, dict) else {}
        
        # 提交答案
        result = DiagnosisService.submit_answer(session_id, data)
        
        # 添加自适应分析结果
        if result.get('response_analysis'):
            result['adaptive_insights'] = {
                'ability_trend': result['response_analysis'].get('ability_trend'),
                'consistency_score': result['response_analysis'].get('consistency_score'),
                'learning_efficiency': result['response_analysis'].get('learning_efficiency')
            }
        
        return success_response(result)
        
    except ValidationError as e:
        return error_response('参数验证失败')
    except Exception as e:
        return error_response(f'提交答案失败: {str(e)}')

@diagnosis_bp.route('/reports/<report_id>/complete', methods=['POST'])
@jwt_required()
def complete_diagnosis(current_user, report_id):
    """完成诊断"""
    try:
        # 验证报告是否存在且属于当前用户
        report = DiagnosisReport.query.filter_by(
            id=report_id, 
            user_id=current_user.id
        ).first()
        
        if not report:
            return error_response('诊断报告不存在')
        
        # 完成诊断
        completed_report = DiagnosisService.complete_diagnosis(report_id)
        
        return success_response({
            'report': completed_report.to_dict(include_details=True),
            'message': '诊断完成，报告已生成'
        })
        
    except Exception as e:
        return error_response(f'完成诊断失败: {str(e)}')

@diagnosis_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_diagnosis_statistics(current_user):
    """获取诊断统计信息"""
    try:
        subject_id = request.args.get('subject_id')
        
        if subject_id:
            stats = DiagnosisService.get_diagnosis_statistics(
                user_id=current_user.id,
                subject_id=subject_id
            )
        else:
            stats = DiagnosisService.get_diagnosis_statistics(
                user_id=current_user.id
            )
        
        return success_response({
            'statistics': stats
        })
        
    except Exception as e:
        return error_response(f'获取统计信息失败: {str(e)}')

@diagnosis_bp.route('/reports/<report_id>/heatmap', methods=['GET'])
@jwt_required()
def get_knowledge_heatmap(current_user, report_id):
    """获取知识热力图数据"""
    try:
        report = DiagnosisReport.query.filter_by(
            id=report_id, 
            user_id=current_user.id
        ).first()
        
        if not report:
            return error_response('诊断报告不存在')
        
        # 生成或获取热力图数据
        heatmap_data = report.generate_heatmap_data(report.subject_id)
        
        return success_response({
            'heatmap': heatmap_data
        })
        
    except Exception as e:
        return error_response(f'获取热力图数据失败: {str(e)}')

@diagnosis_bp.route('/reports/<report_id>/learning-path', methods=['GET'])
@jwt_required()
def get_learning_path(current_user, report_id):
    """获取个性化学习路径"""
    try:
        report = DiagnosisReport.query.filter_by(
            id=report_id, 
            user_id=current_user.id
        ).first()
        
        if not report:
            return error_response('诊断报告不存在')
        
        # 获取基础学习路径
        learning_path = report.generate_learning_path(report.subject_id)
        
        # 获取用户学习画像，提供个性化建议
        learning_profile = LearningProfileService.get_profile_summary(current_user.id)
        
        # 整合个性化建议
        enhanced_path = {
            'learning_path': learning_path,
            'recommendations': report.recommendations or [],
            'personalized_recommendations': learning_profile.get('recommendations', []),
            'learning_style': learning_profile.get('learning_style'),
            'optimal_study_time': learning_profile.get('time_preferences', {}).get('optimal_duration', 30),
            'preferred_difficulty': learning_profile.get('difficulty_preference')
        }
        
        return success_response(enhanced_path)
        
    except Exception as e:
        return error_response(f'获取学习路径失败: {str(e)}')

@diagnosis_bp.route('/reports/<report_id>/weakness-analysis', methods=['GET'])
@jwt_required()
def get_weakness_analysis(current_user, report_id):
    """获取薄弱点分析"""
    try:
        report = DiagnosisReport.query.filter_by(
            id=report_id, 
            user_id=current_user.id
        ).first()
        
        if not report:
            return error_response('诊断报告不存在')
        
        # 获取薄弱点分析
        weakness_analysis = report.get_weakness_analysis()
        
        return success_response({
            'weakness_analysis': weakness_analysis
        })
        
    except Exception as e:
        return error_response(f'获取薄弱点分析失败: {str(e)}')

@diagnosis_bp.route('/enums', methods=['GET'])
def get_diagnosis_enums():
    """获取诊断相关枚举值"""
    try:
        return success_response({
            'diagnosis_types': [{
                'value': dt.value,
                'label': {
                    'basic': '基础诊断',
                    'comprehensive': '综合诊断', 
                    'adaptive': '自适应诊断',
                    'targeted': '针对性诊断'
                }.get(dt.value, dt.value)
            } for dt in DiagnosisType],
            'diagnosis_levels': [{
                'value': dl.value,
                'label': {
                    'memory': '记忆层',
                    'application': '应用层',
                    'transfer': '迁移层'
                }.get(dl.value, dl.value)
            } for dl in DiagnosisLevel],
            'difficulty_levels': [
                {'value': 1, 'label': '很简单'},
                {'value': 2, 'label': '简单'},
                {'value': 3, 'label': '中等'},
                {'value': 4, 'label': '困难'},
                {'value': 5, 'label': '很困难'}
            ],
            'confidence_levels': [
                {'value': 1, 'label': '很不确定'},
                {'value': 2, 'label': '不确定'},
                {'value': 3, 'label': '一般'},
                {'value': 4, 'label': '比较确定'},
                {'value': 5, 'label': '非常确定'}
            ]
        })
        
    except Exception as e:
        return error_response(f'获取枚举值失败: {str(e)}')

@diagnosis_bp.route('/sessions/<session_id>', methods=['GET'])
@jwt_required()
def get_diagnosis_session(current_user, session_id):
    """获取诊断会话详情"""
    try:
        session = DiagnosisSession.query.join(DiagnosisReport).filter(
            DiagnosisSession.id == session_id,
            DiagnosisReport.user_id == current_user.id
        ).first()
        
        if not session:
            return error_response('诊断会话不存在')
        
        # 获取会话的所有回答记录
        responses = [response.to_dict() for response in session.question_responses.all()]
        
        # 获取自适应分析结果
        adaptive_analysis = AdaptiveService.analyze_response_pattern(session)
        
        session_data = session.to_dict()
        session_data['responses'] = responses
        session_data['adaptive_analysis'] = adaptive_analysis
        
        return success_response({
            'session': session_data
        })
        
    except Exception as e:
        return error_response(f'获取诊断会话失败: {str(e)}')

@diagnosis_bp.route('/learning-profile', methods=['GET'])
@jwt_required()
def get_learning_profile(current_user):
    """获取用户学习画像"""
    try:
        profile_summary = LearningProfileService.get_profile_summary(current_user.id)
        return success_response(profile_summary)
    except Exception as e:
        return error_response(f'获取学习画像失败: {str(e)}')

@diagnosis_bp.route('/adaptive-recommendations/<session_id>', methods=['GET'])
@jwt_required()
def get_adaptive_recommendations(current_user, session_id):
    """获取自适应推荐"""
    try:
        session = DiagnosisSession.query.join(DiagnosisReport).filter(
            DiagnosisSession.id == session_id,
            DiagnosisReport.user_id == current_user.id
        ).first()
        
        if not session:
            return error_response('诊断会话不存在')
        
        # 获取知识点和可用题目
        try:
            from services.diagnosis_service import DiagnosisService as DS
            knowledge_points = DS.get_diagnosis_knowledge_points(
                session.diagnosis_report.subject_id,
                session.session_type
            )
            available_questions = DS.get_available_questions(
                session, knowledge_points
            )
        except AttributeError:
            # 如果方法不存在，使用默认值
            knowledge_points = []
            available_questions = []
        
        # 生成推荐
        recommendation = AdaptiveService.generate_adaptive_recommendation(
            session, available_questions
        )
        
        return success_response({
            'recommendation': recommendation,
            'session_analysis': AdaptiveService.analyze_response_pattern(session)
        })
    except Exception as e:
        return error_response(f'获取自适应推荐失败: {str(e)}')

@diagnosis_bp.route('/ability-estimate/<session_id>', methods=['GET'])
@jwt_required()
def get_ability_estimate(current_user, session_id):
    """获取能力估计详情"""
    try:
        session = DiagnosisSession.query.join(DiagnosisReport).filter(
            DiagnosisSession.id == session_id,
            DiagnosisReport.user_id == current_user.id
        ).first()
        
        if not session:
            return error_response('诊断会话不存在')
        
        # 获取能力估计历史
        from models.diagnosis import QuestionResponse
        responses = QuestionResponse.query.filter_by(
            diagnosis_session_id=session_id
        ).order_by(QuestionResponse.created_at).all()
        
        ability_history = []
        current_ability = 0.0
        current_se = 1.0
        
        for response in responses:
            current_ability, current_se = AdaptiveService.update_ability_estimate(
                session, response.is_correct, response.difficulty_level
            )
            ability_history.append({
                'question_index': len(ability_history) + 1,
                'ability_estimate': current_ability,
                'standard_error': current_se,
                'confidence_interval': {
                    'lower': current_ability - 1.96 * current_se,
                    'upper': current_ability + 1.96 * current_se
                },
                'is_correct': response.is_correct,
                'difficulty': response.difficulty_level
            })
        
        return success_response({
            'current_ability': session.current_ability,
            'current_se': session.ability_se,
            'ability_history': ability_history,
            'convergence_status': {
                'is_converged': session.ability_se < session.target_precision,
                'target_precision': session.target_precision,
                'questions_answered': session.questions_answered
            }
        })
    except Exception as e:
        return error_response(f'获取能力估计失败: {str(e)}')