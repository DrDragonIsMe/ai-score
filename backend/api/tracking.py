#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - API接口 - tracking.py

Description:
    跟踪数据模型，定义学习行为和统计数据。

Author: Chang Xinglong
Date: 2025-08-31
Version: 1.0.0
License: Apache License 2.0
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from services.tracking_service import TrackingService
from models.tracking import LearningMetric, PerformanceSnapshot, LearningReport, GoalTracking, FeedbackRecord
from utils.validators import validate_required_fields, validate_date_range
from utils.response import success_response, error_response

logger = logging.getLogger(__name__)

# 创建蓝图
tracking_bp = Blueprint('tracking', __name__, url_prefix='/api/tracking')
tracking_service = TrackingService()

# ==================== 学习指标收集 ====================

@tracking_bp.route('/metrics/collect', methods=['POST'])
@jwt_required()
def collect_metrics():
    """
    收集学习指标数据
    
    请求体:
    {
        "period_start": "2024-01-01T00:00:00",
        "period_end": "2024-01-07T23:59:59",
        "force_recalculate": false
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['period_start', 'period_end']
        is_valid, error_msg = validate_required_fields(data, required_fields)
        if not is_valid:
            return error_response(error_msg, 400)
        
        # 解析时间
        try:
            period_start = datetime.fromisoformat(data['period_start'].replace('Z', '+00:00'))
            period_end = datetime.fromisoformat(data['period_end'].replace('Z', '+00:00'))
        except ValueError:
            return error_response('时间格式错误', 400)
        
        # 验证时间范围
        if not validate_date_range(period_start, period_end):
            return error_response('时间范围无效', 400)
        
        force_recalculate = data.get('force_recalculate', False)
        
        # 收集指标
        metrics = tracking_service.collect_learning_metrics(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end
        )
        
        if not metrics:
            return error_response('指标收集失败', 500)
        
        return success_response({
            'metrics_count': len(metrics),
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat(),
            'collected_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"收集学习指标失败: {str(e)}")
        return error_response('服务器内部错误', 500)

@tracking_bp.route('/metrics', methods=['GET'])
@jwt_required()
def get_metrics():
    """
    获取学习指标数据
    
    查询参数:
    - metric_type: 指标类型
    - period_start: 开始时间
    - period_end: 结束时间
    - subject_id: 学科ID
    - limit: 返回数量限制
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取查询参数
        metric_type = request.args.get('metric_type')
        period_start_str = request.args.get('period_start')
        period_end_str = request.args.get('period_end')
        subject_id = request.args.get('subject_id', type=int)
        limit = request.args.get('limit', 100, type=int)
        
        # 解析时间
        period_start = None
        period_end = None
        if period_start_str:
            try:
                period_start = datetime.fromisoformat(period_start_str.replace('Z', '+00:00'))
            except ValueError:
                return error_response('开始时间格式错误', 400)
        
        if period_end_str:
            try:
                period_end = datetime.fromisoformat(period_end_str.replace('Z', '+00:00'))
            except ValueError:
                return error_response('结束时间格式错误', 400)
        
        # 获取指标数据
        metrics = tracking_service.get_user_metrics(
            user_id=user_id,
            metric_type=metric_type,
            period_start=period_start,
            period_end=period_end,
            subject_id=subject_id,
            limit=limit
        )
        
        # 格式化返回数据
        metrics_data = []
        for metric in metrics:
            metrics_data.append({
                'id': metric.id,
                'metric_type': metric.metric_type,
                'metric_value': metric.metric_value,
                'metric_unit': metric.metric_unit,
                'subject_id': metric.subject_id,
                'knowledge_point_id': metric.knowledge_point_id,
                'difficulty_level': metric.difficulty_level,
                'recorded_time': metric.recorded_time.isoformat(),
                'context_data': metric.context_data
            })
        
        return success_response({
            'metrics': metrics_data,
            'total_count': len(metrics_data)
        })
        
    except Exception as e:
        logger.error(f"获取学习指标失败: {str(e)}")
        return error_response('服务器内部错误', 500)

# ==================== 性能快照 ====================

@tracking_bp.route('/snapshots/create', methods=['POST'])
@jwt_required()
def create_snapshot():
    """
    创建性能快照
    
    请求体:
    {
        "period_start": "2024-01-01T00:00:00",
        "period_end": "2024-01-07T23:59:59",
        "snapshot_type": "weekly"
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['period_start', 'period_end']
        is_valid, error_msg = validate_required_fields(data, required_fields)
        if not is_valid:
            return error_response(error_msg, 400)
        
        # 解析时间
        try:
            period_start = datetime.fromisoformat(data['period_start'].replace('Z', '+00:00'))
            period_end = datetime.fromisoformat(data['period_end'].replace('Z', '+00:00'))
        except ValueError:
            return error_response('时间格式错误', 400)
        
        # 验证时间范围
        if not validate_date_range(period_start, period_end):
            return error_response('时间范围无效', 400)
        
        snapshot_type = data.get('snapshot_type', 'manual')
        
        # 创建快照
        snapshot = tracking_service.create_performance_snapshot(
            user_id=user_id,
            tenant_id=1,  # 临时使用默认值
            period_type=snapshot_type,
            period_start=period_start,
            period_end=period_end
        )
        
        if not snapshot:
            return error_response('快照创建失败', 500)
        
        return success_response({
            'snapshot_id': snapshot.id,
            'overall_score': snapshot.overall_score,
            'learning_efficiency': snapshot.learning_efficiency,
            'knowledge_growth': snapshot.knowledge_growth,
            'skill_improvement': snapshot.skill_improvement,
            'created_time': snapshot.created_time.isoformat()
        })
        
    except Exception as e:
        logger.error(f"创建性能快照失败: {str(e)}")
        return error_response('服务器内部错误', 500)

@tracking_bp.route('/snapshots', methods=['GET'])
@jwt_required()
def get_snapshots():
    """
    获取性能快照列表
    
    查询参数:
    - snapshot_type: 快照类型
    - period_start: 开始时间
    - period_end: 结束时间
    - limit: 返回数量限制
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取查询参数
        snapshot_type = request.args.get('snapshot_type')
        period_start_str = request.args.get('period_start')
        period_end_str = request.args.get('period_end')
        limit = request.args.get('limit', 50, type=int)
        
        # 解析时间
        period_start = None
        period_end = None
        if period_start_str:
            try:
                period_start = datetime.fromisoformat(period_start_str.replace('Z', '+00:00'))
            except ValueError:
                return error_response('开始时间格式错误', 400)
        
        if period_end_str:
            try:
                period_end = datetime.fromisoformat(period_end_str.replace('Z', '+00:00'))
            except ValueError:
                return error_response('结束时间格式错误', 400)
        
        # 获取快照列表
        snapshots = tracking_service.get_user_snapshots(
            user_id=user_id,
            snapshot_type=snapshot_type,
            period_start=period_start,
            period_end=period_end,
            limit=limit
        )
        
        # 格式化返回数据
        snapshots_data = []
        for snapshot in snapshots:
            snapshots_data.append({
                'id': snapshot.id,
                'snapshot_type': snapshot.snapshot_type,
                'period_start': snapshot.period_start.isoformat(),
                'period_end': snapshot.period_end.isoformat(),
                'overall_score': snapshot.overall_score,
                'learning_efficiency': snapshot.learning_efficiency,
                'knowledge_growth': snapshot.knowledge_growth,
                'skill_improvement': snapshot.skill_improvement,
                'time_metrics': snapshot.time_metrics,
                'accuracy_metrics': snapshot.accuracy_metrics,
                'progress_metrics': snapshot.progress_metrics,
                'engagement_metrics': snapshot.engagement_metrics,
                'subject_performance': snapshot.subject_performance,
                'created_time': snapshot.created_time.isoformat()
            })
        
        return success_response({
            'snapshots': snapshots_data,
            'total_count': len(snapshots_data)
        })
        
    except Exception as e:
        logger.error(f"获取性能快照失败: {str(e)}")
        return error_response('服务器内部错误', 500)

@tracking_bp.route('/snapshots/<int:snapshot_id>', methods=['GET'])
@jwt_required()
def get_snapshot_detail(snapshot_id):
    """
    获取性能快照详情
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取快照详情
        snapshot = tracking_service.get_snapshot_by_id(snapshot_id, user_id)
        
        if not snapshot:
            return error_response('快照不存在', 404)
        
        return success_response({
            'id': snapshot.id,
            'snapshot_type': snapshot.snapshot_type,
            'period_start': snapshot.period_start.isoformat(),
            'period_end': snapshot.period_end.isoformat(),
            'overall_score': snapshot.overall_score,
            'learning_efficiency': snapshot.learning_efficiency,
            'knowledge_growth': snapshot.knowledge_growth,
            'skill_improvement': snapshot.skill_improvement,
            'time_metrics': snapshot.time_metrics,
            'accuracy_metrics': snapshot.accuracy_metrics,
            'progress_metrics': snapshot.progress_metrics,
            'engagement_metrics': snapshot.engagement_metrics,
            'subject_performance': snapshot.subject_performance,
            'comparison_data': snapshot.comparison_data,
            'prediction_data': snapshot.prediction_data,
            'created_time': snapshot.created_time.isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取快照详情失败: {str(e)}")
        return error_response('服务器内部错误', 500)

# ==================== 学习报告 ====================

@tracking_bp.route('/reports/generate', methods=['POST'])
@jwt_required()
def generate_report():
    """
    生成学习报告
    
    请求体:
    {
        "report_type": "weekly",
        "period_start": "2024-01-01T00:00:00",
        "period_end": "2024-01-07T23:59:59",
        "include_charts": true
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['report_type', 'period_start', 'period_end']
        is_valid, error_msg = validate_required_fields(data, required_fields)
        if not is_valid:
            return error_response(error_msg, 400)
        
        # 解析时间
        try:
            period_start = datetime.fromisoformat(data['period_start'].replace('Z', '+00:00'))
            period_end = datetime.fromisoformat(data['period_end'].replace('Z', '+00:00'))
        except ValueError:
            return error_response('时间格式错误', 400)
        
        # 验证时间范围
        if not validate_date_range(period_start, period_end):
            return error_response('时间范围无效', 400)
        
        report_type = data['report_type']
        include_charts = data.get('include_charts', True)
        
        # 生成报告
        report = tracking_service.generate_learning_report(
            user_id=user_id,
            tenant_id=1,  # 临时使用默认值
            report_type=report_type,
            period_start=period_start,
            period_end=period_end
        )
        
        if not report:
            return error_response('报告生成失败', 500)
        
        return success_response({
            'report_id': report.id,
            'report_title': report.report_title,
            'report_type': report.report_type,
            'period_start': report.period_start.isoformat(),
            'period_end': report.period_end.isoformat(),
            'generated_time': report.generated_time.isoformat()
        })
        
    except Exception as e:
        logger.error(f"生成学习报告失败: {str(e)}")
        return error_response('服务器内部错误', 500)

@tracking_bp.route('/reports', methods=['GET'])
@jwt_required()
def get_reports():
    """
    获取学习报告列表
    
    查询参数:
    - report_type: 报告类型
    - period_start: 开始时间
    - period_end: 结束时间
    - limit: 返回数量限制
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取查询参数
        report_type = request.args.get('report_type')
        period_start_str = request.args.get('period_start')
        period_end_str = request.args.get('period_end')
        limit = request.args.get('limit', 50, type=int)
        
        # 解析时间
        period_start = None
        period_end = None
        if period_start_str:
            try:
                period_start = datetime.fromisoformat(period_start_str.replace('Z', '+00:00'))
            except ValueError:
                return error_response('开始时间格式错误', 400)
        
        if period_end_str:
            try:
                period_end = datetime.fromisoformat(period_end_str.replace('Z', '+00:00'))
            except ValueError:
                return error_response('结束时间格式错误', 400)
        
        # 获取报告列表
        reports = tracking_service.get_user_reports(
            user_id=user_id,
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            limit=limit
        )
        
        # 格式化返回数据
        reports_data = []
        for report in reports:
            reports_data.append({
                'id': report.id,
                'report_title': report.report_title,
                'report_type': report.report_type,
                'period_start': report.period_start.isoformat(),
                'period_end': report.period_end.isoformat(),
                'summary': report.summary,
                'is_generated': report.is_generated,
                'is_sent': report.is_sent,
                'generated_time': report.generated_time.isoformat() if report.generated_time else None,
                'sent_time': report.sent_time.isoformat() if report.sent_time else None
            })
        
        return success_response({
            'reports': reports_data,
            'total_count': len(reports_data)
        })
        
    except Exception as e:
        logger.error(f"获取学习报告失败: {str(e)}")
        return error_response('服务器内部错误', 500)

@tracking_bp.route('/reports/<int:report_id>', methods=['GET'])
@jwt_required()
def get_report_detail(report_id):
    """
    获取学习报告详情
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取报告详情
        report = tracking_service.get_report_by_id(report_id, user_id)
        
        if not report:
            return error_response('报告不存在', 404)
        
        return success_response({
            'id': report.id,
            'report_title': report.report_title,
            'report_type': report.report_type,
            'period_start': report.period_start.isoformat(),
            'period_end': report.period_end.isoformat(),
            'summary': report.summary,
            'key_insights': report.key_insights,
            'performance_data': report.performance_data,
            'trend_analysis': report.trend_analysis,
            'achievements': report.achievements,
            'improvement_areas': report.improvement_areas,
            'recommendations': report.recommendations,
            'charts_data': report.charts_data,
            'is_generated': report.is_generated,
            'is_sent': report.is_sent,
            'generated_time': report.generated_time.isoformat() if report.generated_time else None,
            'sent_time': report.sent_time.isoformat() if report.sent_time else None
        })
        
    except Exception as e:
        logger.error(f"获取报告详情失败: {str(e)}")
        return error_response('服务器内部错误', 500)

# ==================== 目标追踪 ====================

@tracking_bp.route('/goals', methods=['POST'])
@jwt_required()
def create_goal():
    """
    创建学习目标
    
    请求体:
    {
        "goal_type": "accuracy_improvement",
        "goal_title": "提高数学准确率",
        "goal_description": "在一个月内将数学准确率提高到85%以上",
        "target_value": 85.0,
        "current_value": 75.0,
        "target_date": "2024-02-01T00:00:00",
        "subject_id": 1,
        "priority": "high"
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['goal_type', 'goal_title', 'target_value', 'target_date']
        is_valid, error_msg = validate_required_fields(data, required_fields)
        if not is_valid:
            return error_response(error_msg, 400)
        
        # 解析目标日期
        try:
            target_date = datetime.fromisoformat(data['target_date'].replace('Z', '+00:00')).date()
        except ValueError:
            return error_response('目标日期格式错误', 400)
        
        # 创建目标
        goal = tracking_service.create_learning_goal(
            user_id=user_id,
            tenant_id=1,  # 临时使用默认值
            goal_data={
                'goal_type': data['goal_type'],
                'goal_title': data['goal_title'],
                'goal_description': data.get('goal_description', ''),
                'target_value': data['target_value'],
                'current_value': data.get('current_value', 0.0),
                'target_date': target_date,
                'subject_id': data.get('subject_id'),
                'knowledge_point_id': data.get('knowledge_point_id'),
                'priority': data.get('priority', 'medium')
            }
        )
        
        if not goal:
            return error_response('目标创建失败', 500)
        
        return success_response({
            'goal_id': goal.id,
            'goal_title': goal.goal_title,
            'goal_type': goal.goal_type,
            'target_value': goal.target_value,
            'current_value': goal.current_value,
            'progress_percentage': goal.progress_percentage,
            'target_date': goal.target_date.isoformat(),
            'created_time': goal.created_time.isoformat()
        })
        
    except Exception as e:
        logger.error(f"创建学习目标失败: {str(e)}")
        return error_response('服务器内部错误', 500)

@tracking_bp.route('/goals', methods=['GET'])
@jwt_required()
def get_goals():
    """
    获取学习目标列表
    
    查询参数:
    - goal_type: 目标类型
    - is_active: 是否活跃
    - is_completed: 是否完成
    - subject_id: 学科ID
    - limit: 返回数量限制
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取查询参数
        goal_type = request.args.get('goal_type')
        is_active = request.args.get('is_active', type=bool)
        is_completed = request.args.get('is_completed', type=bool)
        subject_id = request.args.get('subject_id', type=int)
        limit = request.args.get('limit', 50, type=int)
        
        # 获取目标列表
        goals = tracking_service.get_user_goals(
            user_id=user_id,
            is_active=is_active
        )
        
        # 格式化返回数据
        goals_data = []
        for goal in goals:
            goals_data.append({
                'id': goal.id,
                'goal_type': goal.goal_type,
                'goal_title': goal.goal_title,
                'goal_description': goal.goal_description,
                'target_value': goal.target_value,
                'current_value': goal.current_value,
                'progress_percentage': goal.progress_percentage,
                'start_date': goal.start_date.isoformat(),
                'target_date': goal.target_date.isoformat(),
                'is_active': goal.is_active,
                'is_completed': goal.is_completed,
                'priority': goal.priority,
                'subject_id': goal.subject_id,
                'knowledge_point_id': goal.knowledge_point_id,
                'created_time': goal.created_time.isoformat(),
                'days_remaining': goal.get_days_remaining(),
                'daily_required_progress': goal.get_daily_required_progress()
            })
        
        return success_response({
            'goals': goals_data,
            'total_count': len(goals_data)
        })
        
    except Exception as e:
        logger.error(f"获取学习目标失败: {str(e)}")
        return error_response('服务器内部错误', 500)

@tracking_bp.route('/goals/<int:goal_id>/progress', methods=['PUT'])
@jwt_required()
def update_goal_progress(goal_id):
    """
    更新目标进度
    
    请求体:
    {
        "current_value": 80.0,
        "progress_note": "本周数学准确率有所提升"
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证必需字段
        if 'current_value' not in data:
            return error_response('缺少当前值', 400)
        
        # 更新进度
        success = tracking_service.update_goal_progress(
            goal_id=goal_id,
            user_id=user_id,
            current_value=data['current_value'],
            progress_note=data.get('progress_note', '')
        )
        
        if not success:
            return error_response('目标进度更新失败', 500)
        
        return success_response({
            'message': '目标进度更新成功',
            'updated_time': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"更新目标进度失败: {str(e)}")
        return error_response('服务器内部错误', 500)

# ==================== 反馈管理 ====================

@tracking_bp.route('/feedback', methods=['POST'])
@jwt_required()
def create_feedback():
    """
    创建反馈记录
    
    请求体:
    {
        "feedback_type": "system_suggestion",
        "feedback_category": "learning_improvement",
        "feedback_title": "学习建议",
        "feedback_content": "建议增加数学练习时间",
        "source_type": "ai_analysis",
        "priority": "medium",
        "importance_score": 0.7
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['feedback_type', 'feedback_category', 'feedback_title', 'feedback_content', 'source_type']
        is_valid, error_msg = validate_required_fields(data, required_fields)
        if not is_valid:
            return error_response(error_msg, 400)
        
        # 创建反馈
        feedback = tracking_service.create_feedback(
            user_id=user_id,
            tenant_id=1,  # 临时使用默认值
            feedback_data={
                'feedback_type': data['feedback_type'],
                'feedback_category': data['feedback_category'],
                'feedback_title': data['feedback_title'],
                'feedback_content': data['feedback_content'],
                'source_type': data['source_type'],
                'source_id': data.get('source_id'),
                'priority': data.get('priority', 'medium'),
                'importance_score': data.get('importance_score', 0.5),
                'related_subject_id': data.get('related_subject_id'),
                'related_report_id': data.get('related_report_id')
            }
        )
        
        if not feedback:
            return error_response('反馈创建失败', 500)
        
        return success_response({
            'feedback_id': feedback.id,
            'feedback_title': feedback.feedback_title,
            'feedback_type': feedback.feedback_type,
            'priority': feedback.priority,
            'is_urgent': feedback.is_urgent(),
            'created_time': feedback.created_time.isoformat()
        })
        
    except Exception as e:
        logger.error(f"创建反馈失败: {str(e)}")
        return error_response('服务器内部错误', 500)

@tracking_bp.route('/feedback', methods=['GET'])
@jwt_required()
def get_feedback():
    """
    获取反馈列表
    
    查询参数:
    - is_read: 是否已读
    - priority: 优先级
    - feedback_type: 反馈类型
    - limit: 返回数量限制
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取查询参数
        is_read = request.args.get('is_read', type=bool)
        priority = request.args.get('priority')
        feedback_type = request.args.get('feedback_type')
        limit = request.args.get('limit', 50, type=int)
        
        # 获取反馈列表
        feedback_list = tracking_service.get_user_feedback(
            user_id=user_id,
            is_read=is_read,
            priority=priority,
            limit=limit
        )
        
        # 格式化返回数据
        feedback_data = []
        for feedback in feedback_list:
            feedback_data.append({
                'id': feedback.id,
                'feedback_type': feedback.feedback_type,
                'feedback_category': feedback.feedback_category,
                'feedback_title': feedback.feedback_title,
                'feedback_content': feedback.feedback_content,
                'source_type': feedback.source_type,
                'priority': feedback.priority,
                'importance_score': feedback.importance_score,
                'is_read': feedback.is_read,
                'is_urgent': feedback.is_urgent(),
                'created_time': feedback.created_time.isoformat(),
                'read_time': (lambda rt: rt.isoformat() if rt and hasattr(rt, 'isoformat') else None)(getattr(feedback, 'read_time', None))
            })
        
        return success_response({
            'feedback': feedback_data,
            'total_count': len(feedback_data)
        })
        
    except Exception as e:
        logger.error(f"获取反馈列表失败: {str(e)}")
        return error_response('服务器内部错误', 500)

@tracking_bp.route('/feedback/<int:feedback_id>/read', methods=['PUT'])
@jwt_required()
def mark_feedback_read(feedback_id):
    """
    标记反馈为已读
    """
    try:
        # 标记已读
        success = tracking_service.mark_feedback_as_read(feedback_id)
        
        if not success:
            return error_response('标记失败', 500)
        
        return success_response({
            'message': '反馈已标记为已读',
            'read_time': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"标记反馈已读失败: {str(e)}")
        return error_response('服务器内部错误', 500)

# ==================== 统计分析 ====================

@tracking_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    """
    获取学习统计数据
    
    查询参数:
    - period_start: 开始时间
    - period_end: 结束时间
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取查询参数
        period_start_str = request.args.get('period_start')
        period_end_str = request.args.get('period_end')
        
        # 默认时间范围（最近30天）
        if not period_start_str or not period_end_str:
            period_end = datetime.now()
            period_start = period_end - timedelta(days=30)
        else:
            try:
                period_start = datetime.fromisoformat(period_start_str.replace('Z', '+00:00'))
                period_end = datetime.fromisoformat(period_end_str.replace('Z', '+00:00'))
            except ValueError:
                return error_response('时间格式错误', 400)
        
        # 获取统计数据
        statistics = tracking_service.get_learning_statistics(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end
        )
        
        return success_response({
            'statistics': statistics,
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取学习统计失败: {str(e)}")
        return error_response('服务器内部错误', 500)

# ==================== 辅助接口 ====================

@tracking_bp.route('/metric-types', methods=['GET'])
def get_metric_types():
    """
    获取指标类型列表
    """
    metric_types = [
        {'value': 'learning_time', 'label': '学习时长'},
        {'value': 'question_count', 'label': '答题数量'},
        {'value': 'accuracy_rate', 'label': '准确率'},
        {'value': 'progress_rate', 'label': '进度'},
        {'value': 'memory_retention', 'label': '记忆保持率'},
        {'value': 'exam_score', 'label': '考试成绩'},
        {'value': 'mistake_reduction', 'label': '错误减少率'}
    ]
    
    return success_response({'metric_types': metric_types})

@tracking_bp.route('/report-types', methods=['GET'])
def get_report_types():
    """
    获取报告类型列表
    """
    report_types = [
        {'value': 'daily', 'label': '日报'},
        {'value': 'weekly', 'label': '周报'},
        {'value': 'monthly', 'label': '月报'},
        {'value': 'custom', 'label': '自定义'}
    ]
    
    return success_response({'report_types': report_types})

@tracking_bp.route('/goal-types', methods=['GET'])
def get_goal_types():
    """
    获取目标类型列表
    """
    goal_types = [
        {'value': 'accuracy_improvement', 'label': '准确率提升'},
        {'value': 'time_management', 'label': '时间管理'},
        {'value': 'knowledge_mastery', 'label': '知识掌握'},
        {'value': 'exam_score', 'label': '考试成绩'},
        {'value': 'learning_consistency', 'label': '学习连续性'},
        {'value': 'mistake_reduction', 'label': '错误减少'}
    ]
    
    return success_response({'goal_types': goal_types})

@tracking_bp.route('/feedback-types', methods=['GET'])
def get_feedback_types():
    """
    获取反馈类型列表
    """
    feedback_types = [
        {'value': 'system_suggestion', 'label': '系统建议'},
        {'value': 'performance_alert', 'label': '表现提醒'},
        {'value': 'goal_reminder', 'label': '目标提醒'},
        {'value': 'achievement_notification', 'label': '成就通知'},
        {'value': 'improvement_tip', 'label': '改进提示'}
    ]
    
    return success_response({'feedback_types': feedback_types})