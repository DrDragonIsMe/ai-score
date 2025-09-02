#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 路由 - learning_analytics.py

Description:
    学习分析相关的API路由，提供学习进度、知识点掌握、成绩趋势等分析功能。

Author: Chang Xinglong
Date: 2025-01-21
Version: 1.0.0
License: Apache License 2.0
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from services.learning_analytics_service import LearningAnalyticsService
from utils.logger import logger
from utils.response import success_response, error_response

# 创建蓝图
learning_analytics_bp = Blueprint('learning_analytics', __name__, url_prefix='/api/learning-analytics')

# 初始化服务
analytics_service = LearningAnalyticsService()

@learning_analytics_bp.route('/progress', methods=['GET'])
@jwt_required()
def get_learning_progress():
    """
    获取学习进度分析
    
    Query Parameters:
        period_days (int, optional): 分析周期天数，默认30天
        
    Returns:
        学习进度分析结果
    """
    try:
        user_id = get_jwt_identity()
        period_days = request.args.get('period_days', 30, type=int)
        
        # 验证参数
        if period_days <= 0 or period_days > 365:
            return error_response('分析周期必须在1-365天之间', 400)
        
        # 获取学习进度分析
        progress_data = analytics_service.analyze_learning_progress(user_id, period_days)
        
        if not progress_data:
            return error_response('获取学习进度分析失败', 500)
        
        return success_response(progress_data, '获取学习进度分析成功')
        
    except Exception as e:
        logger.error(f"获取学习进度分析失败: {str(e)}")
        return error_response('获取学习进度分析失败', 500)

@learning_analytics_bp.route('/knowledge-mastery', methods=['GET'])
@jwt_required()
def get_knowledge_mastery():
    """
    获取知识点掌握情况分析
    
    Query Parameters:
        subject_id (int, optional): 学科ID，不指定则分析所有学科
        
    Returns:
        知识点掌握情况分析结果
    """
    try:
        user_id = get_jwt_identity()
        subject_id = request.args.get('subject_id', type=int)
        
        # 获取知识点掌握分析
        mastery_data = analytics_service.analyze_knowledge_mastery(user_id, subject_id)
        
        if not mastery_data:
            return error_response('获取知识点掌握分析失败', 500)
        
        return success_response(mastery_data, '获取知识点掌握分析成功')
        
    except Exception as e:
        logger.error(f"获取知识点掌握分析失败: {str(e)}")
        return error_response('获取知识点掌握分析失败', 500)

@learning_analytics_bp.route('/performance-trends', methods=['GET'])
@jwt_required()
def get_performance_trends():
    """
    获取学习效果和成绩趋势分析
    
    Query Parameters:
        period_days (int, optional): 分析周期天数，默认90天
        
    Returns:
        学习效果和成绩趋势分析结果
    """
    try:
        user_id = get_jwt_identity()
        period_days = request.args.get('period_days', 90, type=int)
        
        # 验证参数
        if period_days <= 0 or period_days > 365:
            return error_response('分析周期必须在1-365天之间', 400)
        
        # 获取学习效果趋势分析
        trends_data = analytics_service.analyze_performance_trends(user_id, period_days)
        
        if not trends_data:
            return error_response('获取学习效果趋势分析失败', 500)
        
        return success_response(trends_data, '获取学习效果趋势分析成功')
        
    except Exception as e:
        logger.error(f"获取学习效果趋势分析失败: {str(e)}")
        return error_response('获取学习效果趋势分析失败', 500)

@learning_analytics_bp.route('/comprehensive-report', methods=['GET'])
@jwt_required()
def get_comprehensive_report():
    """
    获取综合学习分析报告
    
    Query Parameters:
        period_days (int, optional): 分析周期天数，默认30天
        
    Returns:
        综合学习分析报告
    """
    try:
        user_id = get_jwt_identity()
        period_days = request.args.get('period_days', 30, type=int)
        
        # 验证参数
        if period_days <= 0 or period_days > 365:
            return error_response('分析周期必须在1-365天之间', 400)
        
        # 获取综合分析报告
        report_data = analytics_service.generate_comprehensive_report(user_id, period_days)
        
        if not report_data:
            return error_response('生成综合分析报告失败', 500)
        
        return success_response(report_data, '生成综合分析报告成功')
        
    except Exception as e:
        logger.error(f"生成综合分析报告失败: {str(e)}")
        return error_response('生成综合分析报告失败', 500)

@learning_analytics_bp.route('/weak-points', methods=['GET'])
@jwt_required()
def get_weak_points():
    """
    获取薄弱知识点分析
    
    Query Parameters:
        subject_id (int, optional): 学科ID，不指定则分析所有学科
        limit (int, optional): 返回数量限制，默认10个
        
    Returns:
        薄弱知识点列表
    """
    try:
        user_id = get_jwt_identity()
        subject_id = request.args.get('subject_id', type=int)
        limit = request.args.get('limit', 10, type=int)
        
        # 验证参数
        if limit <= 0 or limit > 50:
            return error_response('返回数量限制必须在1-50之间', 400)
        
        # 获取知识点掌握分析
        mastery_data = analytics_service.analyze_knowledge_mastery(user_id, subject_id)
        
        if not mastery_data or 'weak_points' not in mastery_data:
            return error_response('获取薄弱知识点分析失败', 500)
        
        # 限制返回数量
        weak_points = mastery_data['weak_points'][:limit]
        
        return success_response({
            'weak_points': weak_points,
            'total_count': len(mastery_data['weak_points']),
            'returned_count': len(weak_points)
        }, '获取薄弱知识点分析成功')
        
    except Exception as e:
        logger.error(f"获取薄弱知识点分析失败: {str(e)}")
        return error_response('获取薄弱知识点分析失败', 500)

@learning_analytics_bp.route('/study-statistics', methods=['GET'])
@jwt_required()
def get_study_statistics():
    """
    获取学习统计数据
    
    Query Parameters:
        period_days (int, optional): 统计周期天数，默认7天
        
    Returns:
        学习统计数据
    """
    try:
        user_id = get_jwt_identity()
        period_days = request.args.get('period_days', 7, type=int)
        
        # 验证参数
        if period_days <= 0 or period_days > 365:
            return error_response('统计周期必须在1-365天之间', 400)
        
        # 获取学习进度分析（包含统计数据）
        progress_data = analytics_service.analyze_learning_progress(user_id, period_days)
        
        if not progress_data or 'overall_progress' not in progress_data:
            return error_response('获取学习统计数据失败', 500)
        
        # 提取统计数据
        overall_progress = progress_data['overall_progress']
        time_distribution = progress_data.get('time_distribution', {})
        efficiency_trend = progress_data.get('efficiency_trend', [])
        
        statistics_data = {
            'period': {
                'days': period_days,
                'end_date': datetime.now().isoformat()
            },
            'study_summary': {
                'total_study_time': overall_progress.get('total_study_time', 0),
                'total_questions': overall_progress.get('total_questions', 0),
                'average_accuracy': overall_progress.get('average_accuracy', 0),
                'study_days': overall_progress.get('study_days', 0),
                'daily_average_time': overall_progress.get('daily_average_time', 0)
            },
            'time_distribution': time_distribution,
            'recent_efficiency': efficiency_trend[-7:] if efficiency_trend else []  # 最近7天效率
        }
        
        return success_response(statistics_data, '获取学习统计数据成功')
        
    except Exception as e:
        logger.error(f"获取学习统计数据失败: {str(e)}")
        return error_response('获取学习统计数据失败', 500)

@learning_analytics_bp.route('/learning-recommendations', methods=['GET'])
@jwt_required()
def get_learning_recommendations():
    """
    获取个性化学习建议
    
    Returns:
        个性化学习建议列表
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取知识点掌握分析（包含学习建议）
        mastery_data = analytics_service.analyze_knowledge_mastery(user_id)
        
        if not mastery_data or 'recommendations' not in mastery_data:
            return error_response('获取学习建议失败', 500)
        
        recommendations = mastery_data['recommendations']
        
        # 获取综合分析报告中的改进建议
        report_data = analytics_service.generate_comprehensive_report(user_id, 30)
        improvement_suggestions = report_data.get('improvement_suggestions', []) if report_data else []
        goal_suggestions = report_data.get('goal_suggestions', []) if report_data else []
        
        return success_response({
            'knowledge_recommendations': recommendations,
            'improvement_suggestions': improvement_suggestions,
            'goal_suggestions': goal_suggestions,
            'generated_at': datetime.now().isoformat()
        }, '获取学习建议成功')
        
    except Exception as e:
        logger.error(f"获取学习建议失败: {str(e)}")
        return error_response('获取学习建议失败', 500)

@learning_analytics_bp.route('/subject-comparison', methods=['GET'])
@jwt_required()
def get_subject_comparison():
    """
    获取学科对比分析
    
    Query Parameters:
        period_days (int, optional): 分析周期天数，默认30天
        
    Returns:
        学科对比分析结果
    """
    try:
        user_id = get_jwt_identity()
        period_days = request.args.get('period_days', 30, type=int)
        
        # 验证参数
        if period_days <= 0 or period_days > 365:
            return error_response('分析周期必须在1-365天之间', 400)
        
        # 获取学习进度分析
        progress_data = analytics_service.analyze_learning_progress(user_id, period_days)
        
        if not progress_data or 'subject_progress' not in progress_data:
            return error_response('获取学科对比分析失败', 500)
        
        subject_progress = progress_data['subject_progress']
        
        # 计算学科排名和对比
        if subject_progress:
            # 按准确率排序
            accuracy_ranking = sorted(subject_progress, key=lambda x: x['accuracy_rate'], reverse=True)
            
            # 按学习时间排序
            time_ranking = sorted(subject_progress, key=lambda x: x['study_time'], reverse=True)
            
            # 计算平均值
            avg_accuracy = sum(s['accuracy_rate'] for s in subject_progress) / len(subject_progress)
            avg_study_time = sum(s['study_time'] for s in subject_progress) / len(subject_progress)
            
            comparison_data = {
                'period': {
                    'days': period_days,
                    'end_date': datetime.now().isoformat()
                },
                'subject_details': subject_progress,
                'rankings': {
                    'by_accuracy': accuracy_ranking,
                    'by_study_time': time_ranking
                },
                'averages': {
                    'accuracy_rate': avg_accuracy,
                    'study_time': avg_study_time
                },
                'insights': {
                    'best_accuracy_subject': accuracy_ranking[0]['subject_name'] if accuracy_ranking else None,
                    'most_studied_subject': time_ranking[0]['subject_name'] if time_ranking else None,
                    'needs_attention': [s for s in subject_progress if s['accuracy_rate'] < avg_accuracy * 0.8]
                }
            }
        else:
            comparison_data = {
                'period': {
                    'days': period_days,
                    'end_date': datetime.now().isoformat()
                },
                'subject_details': [],
                'message': '暂无学科学习数据'
            }
        
        return success_response(comparison_data, '获取学科对比分析成功')
        
    except Exception as e:
        logger.error(f"获取学科对比分析失败: {str(e)}")
        return error_response('获取学科对比分析失败', 500)

@learning_analytics_bp.route('/learning-goals', methods=['GET'])
@jwt_required()
def get_learning_goals():
    """
    获取学习目标建议
    
    Returns:
        学习目标建议列表
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取综合分析报告中的目标建议
        report_data = analytics_service.generate_comprehensive_report(user_id, 30)
        
        if not report_data or 'goal_suggestions' not in report_data:
            return error_response('获取学习目标建议失败', 500)
        
        goal_suggestions = report_data['goal_suggestions']
        overall_score = report_data.get('overall_score', {})
        
        return success_response({
            'current_performance': {
                'overall_score': overall_score.get('total_score', 0),
                'grade': overall_score.get('grade', 'N/A'),
                'component_scores': overall_score.get('component_scores', {})
            },
            'goal_suggestions': goal_suggestions,
            'generated_at': datetime.now().isoformat()
        }, '获取学习目标建议成功')
        
    except Exception as e:
        logger.error(f"获取学习目标建议失败: {str(e)}")
        return error_response('获取学习目标建议失败', 500)

@learning_analytics_bp.route('/dashboard-summary', methods=['GET'])
@jwt_required()
def get_dashboard_summary():
    """
    获取仪表板摘要数据
    
    Returns:
        仪表板摘要数据，包含关键指标和趋势
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取最近7天的学习统计
        recent_progress = analytics_service.analyze_learning_progress(user_id, 7)
        
        # 获取最近30天的综合报告
        comprehensive_report = analytics_service.generate_comprehensive_report(user_id, 30)
        
        # 获取知识点掌握情况
        knowledge_mastery = analytics_service.analyze_knowledge_mastery(user_id)
        
        if not recent_progress or not comprehensive_report:
            return error_response('获取仪表板数据失败', 500)
        
        # 构建摘要数据
        overall_progress = recent_progress.get('overall_progress', {})
        overall_score = comprehensive_report.get('overall_score', {})
        key_insights = comprehensive_report.get('key_insights', [])
        
        # 知识点掌握统计
        mastery_stats = knowledge_mastery.get('overall_statistics', {}) if knowledge_mastery else {}
        
        summary_data = {
            'performance_overview': {
                'overall_score': overall_score.get('total_score', 0),
                'grade': overall_score.get('grade', 'N/A'),
                'recent_accuracy': overall_progress.get('average_accuracy', 0),
                'study_days_this_week': overall_progress.get('study_days', 0)
            },
            'learning_statistics': {
                'total_study_time_week': overall_progress.get('total_study_time', 0),
                'questions_answered_week': overall_progress.get('total_questions', 0),
                'daily_average_time': overall_progress.get('daily_average_time', 0)
            },
            'knowledge_mastery': {
                'total_knowledge_points': mastery_stats.get('total_knowledge_points', 0),
                'mastered_count': mastery_stats.get('mastered_count', 0),
                'mastery_rate': mastery_stats.get('mastery_rate', 0),
                'struggling_count': mastery_stats.get('struggling_count', 0)
            },
            'key_insights': key_insights[:3],  # 显示前3个关键洞察
            'quick_actions': [
                {
                    'type': 'review_weak_points',
                    'title': '复习薄弱知识点',
                    'description': '重点关注掌握不佳的知识点',
                    'priority': 'high' if mastery_stats.get('struggling_count', 0) > 0 else 'medium'
                },
                {
                    'type': 'daily_practice',
                    'title': '每日练习',
                    'description': '保持每天学习的习惯',
                    'priority': 'medium'
                },
                {
                    'type': 'view_progress',
                    'title': '查看详细进度',
                    'description': '了解学习进度和趋势',
                    'priority': 'low'
                }
            ],
            'generated_at': datetime.now().isoformat()
        }
        
        return success_response(summary_data, '获取仪表板摘要成功')
        
    except Exception as e:
        logger.error(f"获取仪表板摘要失败: {str(e)}")
        return error_response('获取仪表板摘要失败', 500)

# 错误处理
@learning_analytics_bp.errorhandler(404)
def not_found(error):
    return error_response('API接口不存在', 404)

@learning_analytics_bp.errorhandler(405)
def method_not_allowed(error):
    return error_response('请求方法不被允许', 405)

@learning_analytics_bp.errorhandler(500)
def internal_error(error):
    return error_response('服务器内部错误', 500)