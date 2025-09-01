#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - API接口 - exam_knowledge.py

Description:
    试卷知识点映射相关API接口，提供映射关系管理、统计查询、星图数据等功能。

Author: Chang Xinglong
Date: 2025-01-21
Version: 1.0.0
License: Apache License 2.0
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from typing import Dict, Any, Optional
from services.exam_knowledge_service import ExamKnowledgeService
from models import ExamKnowledgeMapping, ExamKnowledgeStatistics
from utils.response import success_response, error_response
from utils.validators import validate_required_fields
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
exam_knowledge_bp = Blueprint('exam_knowledge', __name__, url_prefix='/api/exam-knowledge')

@exam_knowledge_bp.route('/mapping/create', methods=['POST'])
@jwt_required()
def create_mapping():
    """为试卷创建知识点映射关系"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['exam_paper_id']
        is_valid, validation_error = validate_required_fields(data, required_fields)
        if not is_valid:
            return error_response(validation_error, 400)
        
        exam_paper_id = data['exam_paper_id']
        
        # 创建映射关系
        mappings = ExamKnowledgeService.create_mapping_for_paper(exam_paper_id)
        
        return success_response({
            'message': f'成功为试卷创建 {len(mappings)} 个知识点映射',
            'mapping_count': len(mappings),
            'mappings': [{
                'id': m.id,
                'knowledge_point_id': m.knowledge_point_id,
                'question_count': m.question_count,
                'total_score': m.total_score,
                'importance_weight': m.importance_weight,
                'coverage_rate': m.coverage_rate
            } for m in mappings]
        })
        
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"创建映射关系失败: {str(e)}")
        return error_response('创建映射关系失败', 500)

@exam_knowledge_bp.route('/statistics/update', methods=['POST'])
@jwt_required()
def update_statistics():
    """更新知识点统计信息"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['subject_id']
        is_valid, validation_error = validate_required_fields(data, required_fields)
        if not is_valid:
            return error_response(validation_error, 400)
        
        subject_id = data['subject_id']
        year = data.get('year')
        exam_type = data.get('exam_type')
        region = data.get('region')
        
        # 更新统计信息
        statistics = ExamKnowledgeService.update_knowledge_statistics(
            subject_id, year, exam_type, region
        )
        
        return success_response({
            'message': f'成功更新 {len(statistics)} 个知识点的统计信息',
            'statistics_count': len(statistics),
            'updated_knowledge_points': [{
                'knowledge_point_id': s.knowledge_point_id,
                'appearance_rate': s.appearance_rate,
                'total_questions': s.total_questions,
                'importance_score': s.importance_score
            } for s in statistics[:10]]  # 只返回前10个
        })
        
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"更新统计信息失败: {str(e)}")
        return error_response('更新统计信息失败', 500)

@exam_knowledge_bp.route('/star-map/<subject_id>', methods=['GET'])
@jwt_required()
def get_star_map_data(subject_id: str):
    """获取星图展示数据"""
    try:
        # 获取查询参数
        year = request.args.get('year', type=int)
        exam_type = request.args.get('exam_type')
        
        # 获取星图数据
        star_map_data = ExamKnowledgeService.get_star_map_data(
            subject_id, year, exam_type
        )
        
        return success_response(star_map_data)
        
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"获取星图数据失败: {str(e)}")
        return error_response('获取星图数据失败', 500)

@exam_knowledge_bp.route('/knowledge-point/<knowledge_point_id>/questions', methods=['GET'])
@jwt_required()
def get_knowledge_point_questions(knowledge_point_id: str):
    """获取知识点相关的题目"""
    try:
        # 获取查询参数
        year = request.args.get('year', type=int)
        exam_type = request.args.get('exam_type')
        limit = request.args.get('limit', default=20, type=int)
        
        # 限制查询数量
        if limit > 100:
            limit = 100
        
        # 获取题目数据
        questions = ExamKnowledgeService.get_knowledge_point_questions(
            knowledge_point_id, year, exam_type, limit
        )
        
        return success_response({
            'knowledge_point_id': knowledge_point_id,
            'questions': questions,
            'total_count': len(questions)
        })
        
    except Exception as e:
        logger.error(f"获取知识点题目失败: {str(e)}")
        return error_response('获取知识点题目失败', 500)

@exam_knowledge_bp.route('/statistics/<subject_id>', methods=['GET'])
@jwt_required()
def get_knowledge_statistics(subject_id: str):
    """获取知识点统计信息"""
    try:
        # 获取查询参数
        year = request.args.get('year', type=int)
        exam_type = request.args.get('exam_type')
        region = request.args.get('region')
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=20, type=int)
        
        # 限制每页数量
        if per_page > 100:
            per_page = 100
        
        # 构建查询
        query = ExamKnowledgeStatistics.query.filter_by(subject_id=subject_id)
        if year:
            query = query.filter_by(year=year)
        if exam_type:
            query = query.filter_by(exam_type=exam_type)
        if region:
            query = query.filter_by(region=region)
        
        # 分页查询
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        statistics = [{
            'id': s.id,
            'knowledge_point_id': s.knowledge_point_id,
            'knowledge_point_name': s.knowledge_point.name if s.knowledge_point else None,
            'chapter_name': s.knowledge_point.chapter.name if s.knowledge_point and s.knowledge_point.chapter else None,
            'total_papers': s.total_papers,
            'appeared_papers': s.appeared_papers,
            'appearance_rate': s.appearance_rate,
            'total_questions': s.total_questions,
            'total_score': s.total_score,
            'avg_questions_per_paper': s.avg_questions_per_paper,
            'avg_score_per_paper': s.avg_score_per_paper,
            'max_score_per_paper': s.max_score_per_paper,
            'avg_difficulty': s.avg_difficulty,
            'importance_score': s.importance_score,
            'difficulty_distribution': s.difficulty_distribution,
            'question_type_distribution': s.question_type_distribution,
            'score_type_distribution': s.score_type_distribution,
            'year': s.year,
            'exam_type': s.exam_type,
            'region': s.region
        } for s in pagination.items]
        
        return success_response({
            'statistics': statistics,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        })
        
    except Exception as e:
        logger.error(f"获取知识点统计失败: {str(e)}")
        return error_response('获取知识点统计失败', 500)

@exam_knowledge_bp.route('/mapping/<exam_paper_id>', methods=['GET'])
@jwt_required()
def get_paper_mappings(exam_paper_id: str):
    """获取试卷的知识点映射关系"""
    try:
        # 获取映射关系
        mappings = ExamKnowledgeMapping.query.filter_by(
            exam_paper_id=exam_paper_id
        ).all()
        
        mapping_data = [{
            'id': m.id,
            'knowledge_point_id': m.knowledge_point_id,
            'knowledge_point_name': m.knowledge_point.name if m.knowledge_point else None,
            'chapter_name': m.knowledge_point.chapter.name if m.knowledge_point and m.knowledge_point.chapter else None,
            'question_count': m.question_count,
            'total_score': m.total_score,
            'avg_difficulty': m.avg_difficulty,
            'importance_weight': m.importance_weight,
            'coverage_rate': m.coverage_rate,
            'choice_count': m.choice_count,
            'fill_count': m.fill_count,
            'essay_count': m.essay_count,
            'other_count': m.other_count,
            'choice_score': m.choice_score,
            'fill_score': m.fill_score,
            'essay_score': m.essay_score,
            'other_score': m.other_score
        } for m in mappings]
        
        return success_response({
            'exam_paper_id': exam_paper_id,
            'mappings': mapping_data,
            'total_count': len(mapping_data)
        })
        
    except Exception as e:
        logger.error(f"获取试卷映射关系失败: {str(e)}")
        return error_response('获取试卷映射关系失败', 500)

@exam_knowledge_bp.route('/batch-update/<subject_id>', methods=['POST'])
@jwt_required()
def batch_update_mappings(subject_id: str):
    """批量更新学科下所有试卷的映射关系"""
    try:
        # 执行批量更新
        result = ExamKnowledgeService.batch_update_mappings(subject_id)
        
        return success_response({
            'message': '批量更新完成',
            'total_papers': result['total_papers'],
            'updated_count': result['updated_count'],
            'failed_count': result['failed_count'],
            'success_rate': result['updated_count'] / result['total_papers'] if result['total_papers'] > 0 else 0
        })
        
    except Exception as e:
        logger.error(f"批量更新映射关系失败: {str(e)}")
        return error_response('批量更新映射关系失败', 500)

@exam_knowledge_bp.route('/analysis/<subject_id>', methods=['GET'])
@jwt_required()
def get_knowledge_analysis(subject_id: str):
    """获取知识点分析报告"""
    try:
        # 获取查询参数
        year = request.args.get('year', type=int)
        exam_type = request.args.get('exam_type')
        
        # 构建查询
        query = ExamKnowledgeStatistics.query.filter_by(subject_id=subject_id)
        if year:
            query = query.filter_by(year=year)
        if exam_type:
            query = query.filter_by(exam_type=exam_type)
        
        statistics = query.all()
        
        if not statistics:
            return success_response({
                'message': '暂无统计数据',
                'analysis': {}
            })
        
        # 计算分析数据
        total_knowledge_points = len(statistics)
        high_frequency_points = [s for s in statistics if s.appearance_rate >= 0.8]
        medium_frequency_points = [s for s in statistics if 0.4 <= s.appearance_rate < 0.8]
        low_frequency_points = [s for s in statistics if s.appearance_rate < 0.4]
        
        # 难度分析
        difficulty_stats = {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0}
        for s in statistics:
            if s.avg_difficulty:
                level = str(round(s.avg_difficulty))
                if level in difficulty_stats:
                    difficulty_stats[level] += 1
        
        # 重要程度分析
        importance_levels = [s.importance_score for s in statistics if s.importance_score]
        avg_importance = sum(importance_levels) / len(importance_levels) if importance_levels else 0
        
        # 题型分析
        total_questions_by_type = {'choice': 0, 'fill': 0, 'essay': 0, 'other': 0}
        for s in statistics:
            if s.question_type_distribution:
                for qtype, count in s.question_type_distribution.items():
                    if qtype in total_questions_by_type:
                        total_questions_by_type[qtype] += count
        
        analysis = {
            'overview': {
                'total_knowledge_points': total_knowledge_points,
                'high_frequency_count': len(high_frequency_points),
                'medium_frequency_count': len(medium_frequency_points),
                'low_frequency_count': len(low_frequency_points),
                'avg_importance_score': round(avg_importance, 2)
            },
            'frequency_distribution': {
                'high': len(high_frequency_points),
                'medium': len(medium_frequency_points),
                'low': len(low_frequency_points)
            },
            'difficulty_distribution': difficulty_stats,
            'question_type_distribution': total_questions_by_type,
            'top_knowledge_points': {
                'most_frequent': sorted(statistics, key=lambda x: x.appearance_rate, reverse=True)[:10],
                'most_important': sorted([s for s in statistics if s.importance_score], 
                                       key=lambda x: x.importance_score, reverse=True)[:10],
                'highest_score': sorted(statistics, key=lambda x: x.max_score_per_paper or 0, reverse=True)[:10]
            }
        }
        
        # 转换为可序列化的格式
        for category in analysis['top_knowledge_points']:
            analysis['top_knowledge_points'][category] = [{
                'knowledge_point_id': s.knowledge_point_id,
                'knowledge_point_name': s.knowledge_point.name if s.knowledge_point else None,
                'appearance_rate': s.appearance_rate,
                'importance_score': s.importance_score,
                'max_score_per_paper': s.max_score_per_paper
            } for s in analysis['top_knowledge_points'][category]]
        
        return success_response({
            'subject_id': subject_id,
            'year': year,
            'exam_type': exam_type,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"获取知识点分析失败: {str(e)}")
        return error_response('获取知识点分析失败', 500)