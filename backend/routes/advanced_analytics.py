#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级学习分析API路由
提供深度学习数据分析功能
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from services.advanced_analytics_service import AdvancedAnalyticsService
from utils.logger import logger
from utils.response import success_response, error_response

# 创建蓝图
advanced_analytics_bp = Blueprint('advanced_analytics', __name__, url_prefix='/api/advanced-analytics')

# 初始化服务
advanced_service = AdvancedAnalyticsService()

@advanced_analytics_bp.route('/efficiency-analysis', methods=['GET'])
@jwt_required()
def get_efficiency_analysis():
    """
    获取学习效率分析
    
    Query Parameters:
        period_days (int, optional): 分析周期天数，默认30天
        
    Returns:
        学习效率分析结果
    """
    try:
        user_id = get_jwt_identity()
        period_days = request.args.get('period_days', 30, type=int)
        
        # 验证参数
        if period_days <= 0 or period_days > 365:
            return error_response('分析周期必须在1-365天之间', 400)
        
        # 获取效率分析
        efficiency_data = advanced_service.analyze_learning_efficiency(user_id, period_days)
        
        if not efficiency_data:
            return error_response('获取学习效率分析失败', 500)
        
        return success_response(efficiency_data, '获取学习效率分析成功')
        
    except Exception as e:
        logger.error(f"获取学习效率分析失败: {str(e)}")
        return error_response('获取学习效率分析失败', 500)

@advanced_analytics_bp.route('/time-distribution', methods=['GET'])
@jwt_required()
def get_time_distribution():
    """
    获取时间分布分析
    
    Query Parameters:
        period_days (int, optional): 分析周期天数，默认30天
        
    Returns:
        时间分布分析结果
    """
    try:
        user_id = get_jwt_identity()
        period_days = request.args.get('period_days', 30, type=int)
        
        # 验证参数
        if period_days <= 0 or period_days > 365:
            return error_response('分析周期必须在1-365天之间', 400)
        
        # 获取时间分布分析
        time_data = advanced_service.analyze_time_distribution(user_id, period_days)
        
        if not time_data:
            return error_response('获取时间分布分析失败', 500)
        
        return success_response(time_data, '获取时间分布分析成功')
        
    except Exception as e:
        logger.error(f"获取时间分布分析失败: {str(e)}")
        return error_response('获取时间分布分析失败', 500)

@advanced_analytics_bp.route('/difficulty-adaptation', methods=['GET'])
@jwt_required()
def get_difficulty_adaptation():
    """
    获取难度适应性分析
    
    Query Parameters:
        period_days (int, optional): 分析周期天数，默认30天
        
    Returns:
        难度适应性分析结果
    """
    try:
        user_id = get_jwt_identity()
        period_days = request.args.get('period_days', 30, type=int)
        
        # 验证参数
        if period_days <= 0 or period_days > 365:
            return error_response('分析周期必须在1-365天之间', 400)
        
        # 获取难度适应性分析
        difficulty_data = advanced_service.analyze_difficulty_adaptation(user_id, period_days)
        
        if not difficulty_data:
            return error_response('获取难度适应性分析失败', 500)
        
        return success_response(difficulty_data, '获取难度适应性分析成功')
        
    except Exception as e:
        logger.error(f"获取难度适应性分析失败: {str(e)}")
        return error_response('获取难度适应性分析失败', 500)

@advanced_analytics_bp.route('/learning-patterns', methods=['GET'])
@jwt_required()
def get_learning_patterns():
    """
    获取学习模式识别
    
    Query Parameters:
        period_days (int, optional): 分析周期天数，默认60天
        
    Returns:
        学习模式识别结果
    """
    try:
        user_id = get_jwt_identity()
        period_days = request.args.get('period_days', 60, type=int)
        
        # 验证参数
        if period_days <= 0 or period_days > 365:
            return error_response('分析周期必须在1-365天之间', 400)
        
        # 获取学习模式识别
        pattern_data = advanced_service.identify_learning_patterns(user_id, period_days)
        
        if not pattern_data:
            return error_response('获取学习模式识别失败', 500)
        
        return success_response(pattern_data, '获取学习模式识别成功')
        
    except Exception as e:
        logger.error(f"获取学习模式识别失败: {str(e)}")
        return error_response('获取学习模式识别失败', 500)

@advanced_analytics_bp.route('/performance-prediction', methods=['GET'])
@jwt_required()
def get_performance_prediction():
    """
    获取学习表现预测
    
    Query Parameters:
        prediction_days (int, optional): 预测天数，默认7天
        
    Returns:
        学习表现预测结果
    """
    try:
        user_id = get_jwt_identity()
        prediction_days = request.args.get('prediction_days', 7, type=int)
        
        # 验证参数
        if prediction_days <= 0 or prediction_days > 30:
            return error_response('预测天数必须在1-30天之间', 400)
        
        # 获取学习表现预测
        prediction_data = advanced_service.predict_performance(user_id, prediction_days)
        
        if not prediction_data:
            return error_response('获取学习表现预测失败', 500)
        
        return success_response(prediction_data, '获取学习表现预测成功')
        
    except Exception as e:
        logger.error(f"获取学习表现预测失败: {str(e)}")
        return error_response('获取学习表现预测失败', 500)

@advanced_analytics_bp.route('/comprehensive-insights', methods=['GET'])
@jwt_required()
def get_comprehensive_insights():
    """
    获取综合深度洞察
    
    Query Parameters:
        period_days (int, optional): 分析周期天数，默认30天
        
    Returns:
        综合深度洞察结果
    """
    try:
        user_id = get_jwt_identity()
        period_days = request.args.get('period_days', 30, type=int)
        
        # 验证参数
        if period_days <= 0 or period_days > 365:
            return error_response('分析周期必须在1-365天之间', 400)
        
        # 获取多维度分析数据
        efficiency_data = advanced_service.analyze_learning_efficiency(user_id, period_days)
        time_data = advanced_service.analyze_time_distribution(user_id, period_days)
        difficulty_data = advanced_service.analyze_difficulty_adaptation(user_id, period_days)
        pattern_data = advanced_service.identify_learning_patterns(user_id, min(period_days * 2, 60))
        prediction_data = advanced_service.predict_performance(user_id, 7)
        
        # 生成综合洞察
        insights = {
            'efficiency_analysis': efficiency_data,
            'time_distribution': time_data,
            'difficulty_adaptation': difficulty_data,
            'learning_patterns': pattern_data,
            'performance_prediction': prediction_data,
            'key_insights': _generate_key_insights(
                efficiency_data, time_data, difficulty_data, pattern_data, prediction_data
            ),
            'action_recommendations': _generate_action_recommendations(
                efficiency_data, time_data, difficulty_data, pattern_data
            ),
            'generated_at': datetime.now().isoformat()
        }
        
        return success_response(insights, '获取综合深度洞察成功')
        
    except Exception as e:
        logger.error(f"获取综合深度洞察失败: {str(e)}")
        return error_response('获取综合深度洞察失败', 500)

@advanced_analytics_bp.route('/learning-health-score', methods=['GET'])
@jwt_required()
def get_learning_health_score():
    """
    获取学习健康度评分
    
    Returns:
        学习健康度评分和建议
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取各维度数据
        efficiency_data = advanced_service.analyze_learning_efficiency(user_id, 30)
        time_data = advanced_service.analyze_time_distribution(user_id, 30)
        pattern_data = advanced_service.identify_learning_patterns(user_id, 60)
        
        # 计算健康度评分
        health_score = _calculate_learning_health_score(
            efficiency_data, time_data, pattern_data
        )
        
        return success_response(health_score, '获取学习健康度评分成功')
        
    except Exception as e:
        logger.error(f"获取学习健康度评分失败: {str(e)}")
        return error_response('获取学习健康度评分失败', 500)

# 辅助函数
def _generate_key_insights(efficiency_data, time_data, difficulty_data, pattern_data, prediction_data):
    """
    生成关键洞察
    """
    insights = []
    
    # 效率洞察
    if efficiency_data and efficiency_data.get('overall_efficiency'):
        efficiency_score = efficiency_data['overall_efficiency'].get('efficiency_score', 0)
        if efficiency_score > 80:
            insights.append({
                'type': 'efficiency',
                'level': 'positive',
                'title': '学习效率优秀',
                'description': f'当前学习效率得分{efficiency_score:.1f}，表现优异'
            })
        elif efficiency_score < 50:
            insights.append({
                'type': 'efficiency',
                'level': 'warning',
                'title': '学习效率需要提升',
                'description': f'当前学习效率得分{efficiency_score:.1f}，建议优化学习方法'
            })
    
    # 时间洞察
    if time_data and time_data.get('optimal_times'):
        optimal_times = time_data['optimal_times']
        if optimal_times:
            best_hour = optimal_times[0]['hour']
            insights.append({
                'type': 'timing',
                'level': 'info',
                'title': '最佳学习时间',
                'description': f'您在{best_hour}:00左右学习效果最佳'
            })
    
    # 模式洞察
    if pattern_data and pattern_data.get('habit_assessment'):
        habit_score = pattern_data['habit_assessment'].get('score', 0)
        if habit_score > 80:
            insights.append({
                'type': 'habits',
                'level': 'positive',
                'title': '学习习惯良好',
                'description': f'学习习惯评分{habit_score}，保持良好的学习规律'
            })
        elif habit_score < 60:
            insights.append({
                'type': 'habits',
                'level': 'warning',
                'title': '学习习惯需要改善',
                'description': f'学习习惯评分{habit_score}，建议建立更规律的学习计划'
            })
    
    # 预测洞察
    if prediction_data and prediction_data.get('performance_trend'):
        trend = prediction_data['performance_trend'].get('trend', 'stable')
        if trend == 'improving':
            insights.append({
                'type': 'prediction',
                'level': 'positive',
                'title': '学习趋势向好',
                'description': '预测显示您的学习表现将持续改善'
            })
        elif trend == 'declining':
            insights.append({
                'type': 'prediction',
                'level': 'warning',
                'title': '需要关注学习状态',
                'description': '预测显示学习表现可能下降，建议调整学习策略'
            })
    
    return insights

def _generate_action_recommendations(efficiency_data, time_data, difficulty_data, pattern_data):
    """
    生成行动建议
    """
    recommendations = []
    
    # 从各个分析中收集建议
    if efficiency_data and efficiency_data.get('recommendations'):
        recommendations.extend(efficiency_data['recommendations'])
    
    if time_data and time_data.get('recommendations'):
        recommendations.extend(time_data['recommendations'])
    
    if difficulty_data and difficulty_data.get('recommendations'):
        recommendations.extend(difficulty_data['recommendations'])
    
    if pattern_data and pattern_data.get('recommendations'):
        recommendations.extend(pattern_data['recommendations'])
    
    # 按优先级排序并去重
    priority_order = {'high': 3, 'medium': 2, 'low': 1}
    unique_recommendations = {}
    
    for rec in recommendations:
        key = rec.get('type', 'general')
        if key not in unique_recommendations or priority_order.get(rec.get('priority', 'low'), 1) > priority_order.get(unique_recommendations[key].get('priority', 'low'), 1):
            unique_recommendations[key] = rec
    
    return list(unique_recommendations.values())[:5]  # 返回前5个最重要的建议

def _calculate_learning_health_score(efficiency_data, time_data, pattern_data):
    """
    计算学习健康度评分
    """
    scores = {
        'efficiency_score': 0,
        'consistency_score': 0,
        'balance_score': 0,
        'habit_score': 0
    }
    
    # 效率评分
    if efficiency_data and efficiency_data.get('overall_efficiency'):
        efficiency_score = efficiency_data['overall_efficiency'].get('efficiency_score', 0)
        scores['efficiency_score'] = min(100, max(0, efficiency_score))
    
    # 一致性评分（基于时间分布）
    if time_data and time_data.get('session_analysis'):
        total_sessions = time_data['session_analysis'].get('total_sessions', 0)
        if total_sessions > 0:
            scores['consistency_score'] = min(100, total_sessions * 5)  # 每个会话5分，最高100分
    
    # 平衡性评分（基于时间分布的均匀程度）
    if time_data and time_data.get('weekly_distribution'):
        weekly_dist = time_data['weekly_distribution']
        active_days = sum(1 for day in weekly_dist if day.get('question_count', 0) > 0)
        scores['balance_score'] = (active_days / 7) * 100
    
    # 习惯评分
    if pattern_data and pattern_data.get('habit_assessment'):
        habit_score = pattern_data['habit_assessment'].get('score', 0)
        scores['habit_score'] = habit_score
    
    # 计算总分
    total_score = sum(scores.values()) / len(scores)
    
    # 生成等级
    if total_score >= 90:
        grade = 'A+'
        level = 'excellent'
    elif total_score >= 80:
        grade = 'A'
        level = 'good'
    elif total_score >= 70:
        grade = 'B'
        level = 'average'
    elif total_score >= 60:
        grade = 'C'
        level = 'below_average'
    else:
        grade = 'D'
        level = 'poor'
    
    return {
        'total_score': round(total_score, 1),
        'grade': grade,
        'level': level,
        'component_scores': {k: int(round(v, 0)) for k, v in scores.items()},
        'health_indicators': [
            {
                'name': '学习效率',
                'score': int(round(scores['efficiency_score'], 0)),
                'status': 'good' if scores['efficiency_score'] >= 70 else 'needs_improvement'
            },
            {
                'name': '学习一致性',
                'score': int(round(scores['consistency_score'], 0)),
                'status': 'good' if scores['consistency_score'] >= 70 else 'needs_improvement'
            },
            {
                'name': '时间平衡性',
                'score': int(round(scores['balance_score'], 0)),
                'status': 'good' if scores['balance_score'] >= 70 else 'needs_improvement'
            },
            {
                'name': '学习习惯',
                'score': int(round(scores['habit_score'], 0)),
                'status': 'good' if scores['habit_score'] >= 70 else 'needs_improvement'
            }
        ],
        'improvement_areas': [
            name for name, score in {
                '学习效率': scores['efficiency_score'],
                '学习一致性': scores['consistency_score'],
                '时间平衡性': scores['balance_score'],
                '学习习惯': scores['habit_score']
            }.items() if score < 70
        ]
    }

# 错误处理
@advanced_analytics_bp.errorhandler(404)
def not_found(error):
    return error_response('API接口不存在', 404)

@advanced_analytics_bp.errorhandler(405)
def method_not_allowed(error):
    return error_response('请求方法不被允许', 405)

@advanced_analytics_bp.errorhandler(500)
def internal_error(error):
    return error_response('服务器内部错误', 500)