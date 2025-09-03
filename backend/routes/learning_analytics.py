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

# 导入API适配器函数
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api_adapter import (
    adapt_dashboard_summary,
    adapt_learning_progress,
    adapt_knowledge_mastery,
    adapt_study_statistics,
    adapt_learning_recommendations
)

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
        
        # 适配数据格式
        adapted_data = adapt_learning_progress(progress_data)
        
        return success_response(adapted_data, '获取学习进度分析成功')
        
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
        
        # 适配数据格式
        adapted_data = adapt_knowledge_mastery(mastery_data)
        
        return success_response(adapted_data, '获取知识点掌握分析成功')
        
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
        
        # 获取学习进度分析
        progress_data = analytics_service.analyze_learning_progress(user_id, period_days)
        
        if not progress_data:
            return error_response('获取学习统计数据失败', 500)
        
        # 使用适配器转换数据格式
        statistics_data = adapt_study_statistics(progress_data)
        
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
        
        # 获取知识点掌握分析
        mastery_data = analytics_service.analyze_knowledge_mastery(user_id)
        
        if not mastery_data:
            return error_response('获取学习建议失败', 500)
        
        # 使用适配器转换数据格式
        recommendations_data = adapt_learning_recommendations(mastery_data)
        
        return success_response(recommendations_data, '获取学习建议成功')
        
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
        
        # 获取最近30天的学习进度
        recent_progress = analytics_service.analyze_learning_progress(user_id, 30)
        
        if not recent_progress:
            return error_response('获取仪表板数据失败', 500)
        
        # 使用适配器转换数据格式
        dashboard_data = adapt_dashboard_summary(recent_progress)
        
        return success_response(dashboard_data, '获取仪表板摘要成功')
        
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