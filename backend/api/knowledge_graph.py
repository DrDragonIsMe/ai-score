#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - API接口 - knowledge_graph.py

Description:
    知识图谱星图展示API接口，提供知识点可视化、关联分析等功能。

Author: Chang Xinglong
Date: 2025-08-31
Version: 1.0.0
License: Apache License 2.0
"""

from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.decorators import admin_required
from models import Subject, Chapter, KnowledgePoint, SubKnowledgePoint, KnowledgeGraph, ExamPaper, Question
from services.knowledge_graph_service import knowledge_graph_service
from services.mastery_classification_service import mastery_classification_service
from utils.database import db
from utils.response import success_response, error_response
from utils.decorators import admin_required
from sqlalchemy import desc, func, and_
import json
from datetime import datetime

from sqlalchemy.orm.attributes import flag_modified

knowledge_graph_bp = Blueprint('knowledge_graph', __name__)

@knowledge_graph_bp.route('/knowledge-graph', methods=['GET'])
@jwt_required()
def get_knowledge_graphs():
    """获取知识图谱列表"""
    try:
        # 从JWT token中获取tenant_id
        current_user_identity = get_jwt_identity()
        tenant_id = current_user_identity.get('tenant_id')
        
        # 获取查询参数
        subject_id = request.args.get('subject_id')
        year = request.args.get('year', datetime.now().year, type=int)
        graph_type = request.args.get('type', 'exam_scope')
        
        # 构建查询条件
        query = KnowledgeGraph.query.filter_by(is_active=True)
        
        if subject_id:
            # 验证学科是否存在且属于当前租户
            subject = Subject.query.filter_by(id=subject_id, tenant_id=tenant_id).first()
            if not subject:
                return error_response('Subject not found', 404)
            query = query.filter_by(subject_id=subject_id)
        
        if year:
            query = query.filter_by(year=year)
            
        if graph_type:
            query = query.filter_by(graph_type=graph_type)
        
        # 获取知识图谱列表
        knowledge_graphs = query.order_by(desc(KnowledgeGraph.created_at)).all()
        
        # 转换为字典格式
        result = [kg.to_dict() for kg in knowledge_graphs]
        
        return success_response(result)
        
    except Exception as e:
        return error_response(f'Failed to get knowledge graphs: {str(e)}', 500)

@knowledge_graph_bp.route('/knowledge-graph/<id_param>', methods=['GET'])
@jwt_required()
def get_subject_knowledge_graph(id_param):
    """获取学科知识图谱或单个知识图谱"""
    try:
        # 尝试按图谱ID获取
        knowledge_graph = KnowledgeGraph.query.filter_by(id=id_param, is_active=True).first()
        if knowledge_graph:
            current_user_identity = get_jwt_identity()
            tenant_id = current_user_identity.get('tenant_id')
            subject = Subject.query.filter_by(id=knowledge_graph.subject_id, tenant_id=tenant_id).first()
            if not subject:
                return error_response('Access denied to this knowledge graph', 403)
            return success_response(knowledge_graph.to_dict())

        # 如果不是图谱ID，则按学科ID处理
        subject_id = id_param
        current_user_identity = get_jwt_identity()
        tenant_id = current_user_identity.get('tenant_id')
        year = request.args.get('year', datetime.now().year, type=int)
        graph_type = request.args.get('type', 'exam_scope')

        subject = Subject.query.filter_by(id=subject_id, tenant_id=tenant_id).first()
        if not subject:
            return error_response('Knowledge graph or Subject not found', 404)

        # 查找现有的知识图谱
        existing_graph = KnowledgeGraph.query.filter_by(
            subject_id=subject_id, year=year, graph_type=graph_type, is_active=True
        ).first()
        
        if existing_graph:
            return success_response(existing_graph.to_dict())
        
        # 根据图谱类型生成不同的图谱数据
        if graph_type == 'exam_scope':
            graph_data = generate_exam_scope_graph(subject_id, year)
        elif graph_type == 'full_knowledge':
            graph_data = generate_knowledge_graph(subject_id, year)
        elif graph_type == 'mastery_level':
            graph_data = generate_mastery_level_graph(subject_id, year)
        else:
            graph_data = generate_knowledge_graph(subject_id, year)
        
        # 保存生成的图谱
        new_graph = KnowledgeGraph(
            subject_id=subject_id,
            name=f"{subject.name}{get_graph_type_name(graph_type)}{year}",
            description=f"{year}年{subject.name}{get_graph_type_name(graph_type)}知识点关系图",
            year=year,
            graph_type=graph_type,
            nodes=graph_data['nodes'],
            edges=graph_data['edges'],
            layout_config=graph_data['layout_config']
        )
        
        db.session.add(new_graph)
        db.session.commit()
        
        return success_response(new_graph.to_dict())
        
    except Exception as e:
        return error_response(f'Failed to get knowledge graph: {str(e)}', 500)

@knowledge_graph_bp.route('/knowledge-graph/nodes', methods=['POST'])
@jwt_required()
def create_knowledge_node():
    """创建知识点节点"""
    try:
        # 从JWT token中获取用户信息
        current_user_identity = get_jwt_identity()
        tenant_id = current_user_identity.get('tenant_id')
        user_id = current_user_identity.get('user_id')
        
        data = request.get_json()
        subject_id = data.get('subject_id')
        title = data.get('title')
        content = data.get('content')
        tags = data.get('tags', '')
        difficulty_level = data.get('difficulty_level', 1)
        
        # 验证必填字段
        if not all([subject_id, title, content]):
            return error_response('Missing required fields: subject_id, title, content', 400)
        
        # 验证学科是否存在
        subject = Subject.query.filter_by(id=subject_id, tenant_id=tenant_id).first()
        if not subject:
            return error_response('Subject not found', 404)
        
        # 创建知识点
        knowledge_point = KnowledgePoint(
            name=title,
            description=content,
            subject_id=subject_id,
            difficulty_level=difficulty_level,
            tenant_id=tenant_id,
            created_by=user_id
        )
        
        # 处理标签
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            knowledge_point.tags = ','.join(tag_list)
        
        db.session.add(knowledge_point)
        db.session.commit()
        
        return success_response({
            'id': knowledge_point.id,
            'name': knowledge_point.name,
            'description': knowledge_point.description,
            'subject_id': knowledge_point.subject_id,
            'difficulty_level': knowledge_point.difficulty_level,
            'tags': knowledge_point.tags,
            'created_at': knowledge_point.created_at.isoformat() if knowledge_point.created_at else None
        }, 'Knowledge node created successfully')
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to create knowledge node: {str(e)}', 500)

@knowledge_graph_bp.route('/knowledge-graph/nodes/<node_id>', methods=['PUT'])
@jwt_required()
def update_knowledge_node(node_id):
    """更新知识图谱节点"""
    try:
        current_user_identity = get_jwt_identity()
        tenant_id = current_user_identity.get('tenant_id')
        
        data = request.get_json()
        
        # 查找知识图谱
        knowledge_graph = KnowledgeGraph.query.filter_by(
            id=node_id,
            is_active=True
        ).first()
        
        if not knowledge_graph:
            return error_response('Knowledge graph node not found', 404)
        
        # 更新字段
        if 'content' in data:
            knowledge_graph.content = data['content']
        
        # 统一标签体系：更新nodes数组中的标签
        if knowledge_graph.nodes:
            if knowledge_graph.graph_type == 'ai_assistant_content':
                # AI内容类型：只更新第一个节点
                if knowledge_graph.nodes:
                    node = knowledge_graph.nodes[0]
                    if 'content' in data:
                        node['content'] = data['content']
                    if 'tags' in data:
                        node['tags'] = data['tags'] if isinstance(data['tags'], list) else []
                    # 标记nodes字段已修改
                    flag_modified(knowledge_graph, 'nodes')
            else:
                # 其他类型：将标签应用到所有节点
                if 'tags' in data:
                    tags_to_apply = data['tags'] if isinstance(data['tags'], list) else []
                    for node in knowledge_graph.nodes:
                        node['tags'] = tags_to_apply
                    # 标记nodes字段已修改
                    flag_modified(knowledge_graph, 'nodes')
        
        if 'subject_id' in data:
            # 验证目标学科是否存在
            target_subject = Subject.query.filter_by(
                id=data['subject_id'],
                tenant_id=tenant_id,
                is_active=True
            ).first()
            if target_subject:
                knowledge_graph.subject_id = data['subject_id']
                # 同时更新nodes数组中的subject_id
                if knowledge_graph.graph_type == 'ai_assistant_content' and knowledge_graph.nodes:
                    knowledge_graph.nodes[0]['subject_id'] = data['subject_id']
                    # 标记nodes字段已修改
                    flag_modified(knowledge_graph, 'nodes')
            else:
                return error_response('Target subject not found', 404)
        
        knowledge_graph.updated_at = datetime.utcnow()
        
        db.session.commit()
        db.session.refresh(knowledge_graph)
        
        return success_response(knowledge_graph.to_dict(), 'Knowledge node updated successfully')
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to update knowledge node: {str(e)}', 500)

@knowledge_graph_bp.route('/knowledge-graph/nodes/<node_id>', methods=['DELETE'])
@jwt_required()
def delete_knowledge_node(node_id):
    """删除知识图谱节点"""
    try:
        # 查找AI内容节点
        knowledge_graph = KnowledgeGraph.query.filter_by(
            id=node_id,
            is_active=True
        ).first()
        
        if not knowledge_graph:
            return error_response('Knowledge graph node not found', 404)
        
        # 软删除
        knowledge_graph.is_active = False
        knowledge_graph.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return success_response({
            'id': knowledge_graph.id,
            'message': 'Knowledge node deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to delete knowledge node: {str(e)}', 500)

@knowledge_graph_bp.route('/knowledge-graph/<subject_id>', methods=['POST'])
@jwt_required()
@admin_required
def create_knowledge_graph(subject_id):
    """创建或更新知识图谱"""
    try:
        # 从JWT token中获取tenant_id
        current_user_identity = get_jwt_identity()
        tenant_id = current_user_identity.get('tenant_id')
        data = request.get_json()
        
        # 验证学科
        subject = Subject.query.filter_by(id=subject_id, tenant_id=tenant_id).first()
        if not subject:
            return error_response('Subject not found', 404)
        
        year = data.get('year', datetime.now().year)
        
        # 查找现有图谱
        existing_graph = KnowledgeGraph.query.filter_by(
            subject_id=subject_id, year=year, is_active=True
        ).first()
        
        if existing_graph:
            # 更新现有图谱
            existing_graph.nodes = data.get('nodes', existing_graph.nodes)
            existing_graph.edges = data.get('edges', existing_graph.edges)
            existing_graph.layout_config = data.get('layout_config', existing_graph.layout_config)
            existing_graph.updated_at = datetime.utcnow()
            
            db.session.commit()
            return success_response(existing_graph.to_dict())
        else:
            # 创建新图谱
            new_graph = KnowledgeGraph(
                subject_id=subject_id,
                name=data.get('name', f"{subject.name}知识图谱{year}"),
                description=data.get('description', ''),
                year=year,
                nodes=data.get('nodes', []),
                edges=data.get('edges', []),
                layout_config=data.get('layout_config', {})
            )
            
            db.session.add(new_graph)
            db.session.commit()
            
            return success_response(new_graph.to_dict()), 201
        
    except Exception as e:
        return error_response(f'Failed to create knowledge graph: {str(e)}', 500)

@knowledge_graph_bp.route('/knowledge-graph/knowledge-points/<point_id>/questions', methods=['GET'])
@jwt_required()
def get_knowledge_point_questions(point_id):
    """获取知识点相关的题目"""
    try:
        tenant_id = g.get('tenant_id')
        
        # 验证知识点
        knowledge_point = KnowledgePoint.query.filter_by(id=point_id, is_active=True).first()
        if not knowledge_point:
            return error_response('Knowledge point not found', 404)
        
        # 查找相关题目
        questions = Question.query.join(ExamPaper).filter(
            ExamPaper.tenant_id == tenant_id,
            ExamPaper.is_active == True,
            Question.is_active == True,
            Question.knowledge_points.contains([point_id])
        ).order_by(desc(ExamPaper.year)).all()
        
        result = []
        for question in questions:
            question_data = question.to_dict()
            question_data['exam_paper'] = {
                'id': question.exam_paper.id,
                'title': question.exam_paper.title,
                'year': question.exam_paper.year,
                'exam_type': question.exam_paper.exam_type
            }
            result.append(question_data)
        
        return success_response(result)
        
    except Exception as e:
        return error_response(f'Failed to get knowledge point questions: {str(e)}', 500)

@knowledge_graph_bp.route('/knowledge-graph/questions/<question_id>/knowledge-points', methods=['GET'])
@jwt_required()
def get_question_knowledge_points(question_id):
    """获取题目关联的知识点（用于星图高亮）"""
    try:
        tenant_id = g.get('tenant_id')
        
        # 验证题目
        question = Question.query.join(ExamPaper).filter(
            Question.id == question_id,
            ExamPaper.tenant_id == tenant_id,
            Question.is_active == True
        ).first()
        
        if not question:
            return error_response('Question not found', 404)
        
        # 获取关联的知识点详情
        knowledge_points = []
        if question.knowledge_points:
            points = KnowledgePoint.query.filter(
                KnowledgePoint.id.in_(question.knowledge_points),
                KnowledgePoint.is_active == True
            ).all()
            
            for point in points:
                knowledge_points.append({
                    'id': point.id,
                    'name': point.name,
                    'code': point.code,
                    'difficulty': point.difficulty,
                    'importance': point.importance,
                    'chapter': {
                        'id': point.chapter.id,
                        'name': point.chapter.name
                    }
                })
        
        return success_response({
            'question': question.to_dict(),
            'knowledge_points': knowledge_points,
            'highlight_nodes': [kp['id'] for kp in knowledge_points]
        })
        
    except Exception as e:
        return error_response(f'Failed to get question knowledge points: {str(e)}', 500)


@knowledge_graph_bp.route('/knowledge-graph/exam-papers/<paper_id>/star-map', methods=['GET'])
@jwt_required()
def get_exam_paper_star_map(paper_id):
    """获取试卷的知识点星图数据（试卷与星图联动）"""
    try:
        tenant_id = g.get('tenant_id')
        
        # 验证试卷
        paper = ExamPaper.query.filter(
            ExamPaper.id == paper_id,
            ExamPaper.tenant_id == tenant_id,
            ExamPaper.is_active == True
        ).first()
        
        if not paper:
            return error_response('Exam paper not found', 404)
        
        # 获取试卷中所有题目的知识点
        questions = Question.query.filter(
            Question.paper_id == paper_id,
            Question.is_active == True
        ).all()
        
        # 统计知识点分布
        knowledge_point_stats = {}
        all_knowledge_points = set()
        
        for question in questions:
            if question.knowledge_points:
                for kp_id in question.knowledge_points:
                    all_knowledge_points.add(kp_id)
                    if kp_id not in knowledge_point_stats:
                        knowledge_point_stats[kp_id] = {
                            'question_count': 0,
                            'total_score': 0,
                            'difficulties': [],
                            'question_types': []
                        }
                    
                    knowledge_point_stats[kp_id]['question_count'] += 1
                    knowledge_point_stats[kp_id]['total_score'] += question.score or 0
                    knowledge_point_stats[kp_id]['difficulties'].append(question.difficulty or 0)
                    knowledge_point_stats[kp_id]['question_types'].append(question.type or '')
        
        # 获取知识点详细信息
        if all_knowledge_points:
            knowledge_points = KnowledgePoint.query.filter(
                KnowledgePoint.id.in_(all_knowledge_points),
                KnowledgePoint.is_active == True
            ).all()
        else:
            knowledge_points = []
        
        # 构建星图数据
        star_map_data = {
            'paper_info': {
                'id': paper.id,
                'title': paper.title,
                'year': paper.year,
                'exam_type': paper.exam_type,
                'total_score': paper.total_score,
                'question_count': len(questions)
            },
            'knowledge_points': [],
            'highlight_nodes': list(all_knowledge_points),
            'statistics': {
                'total_knowledge_points': len(all_knowledge_points),
                'coverage_rate': 0  # 将在前端计算
            }
        }
        
        # 添加知识点详情和统计信息
        for kp in knowledge_points:
            stats = knowledge_point_stats.get(str(kp.id), {})
            avg_difficulty = sum(stats.get('difficulties', [0])) / max(len(stats.get('difficulties', [1])), 1)
            
            star_map_data['knowledge_points'].append({
                'id': str(kp.id),
                'name': kp.name,
                'code': kp.code,
                'difficulty': kp.difficulty,
                'importance': kp.importance,
                'chapter': {
                    'id': kp.chapter.id,
                    'name': kp.chapter.name
                } if kp.chapter else None,
                'paper_stats': {
                    'question_count': stats.get('question_count', 0),
                    'total_score': stats.get('total_score', 0),
                    'avg_difficulty': round(avg_difficulty, 2),
                    'question_types': list(set(stats.get('question_types', [])))
                }
            })
        
        return success_response(star_map_data)
        
    except Exception as e:
        return error_response(f'Failed to get exam paper star map: {str(e)}', 500)

@knowledge_graph_bp.route('/knowledge-graph/<subject_id>/exam-scope', methods=['GET'])
@jwt_required()
def get_exam_scope(subject_id):
    """获取学科考试范围"""
    try:
        # 从JWT token中获取tenant_id
        current_user_identity = get_jwt_identity()
        tenant_id = current_user_identity.get('tenant_id')
        year = request.args.get('year', datetime.now().year, type=int)
        
        # 验证学科
        subject = Subject.query.filter_by(id=subject_id, tenant_id=tenant_id).first()
        if not subject:
            return error_response('Subject not found', 404)
        
        # 获取考试范围配置
        exam_scope = subject.exam_scope or {}
        
        # 如果没有配置，根据知识点生成默认范围
        if not exam_scope:
            exam_scope = generate_exam_scope(subject_id, year)
        
        return success_response(exam_scope)
        
    except Exception as e:
        return error_response(f'Failed to get exam scope: {str(e)}', 500)

@knowledge_graph_bp.route('/knowledge-graph/<subject_id>/exam-scope', methods=['PUT'])
@jwt_required()
@admin_required
def update_exam_scope(subject_id):
    """更新学科考试范围"""
    try:
        # 从JWT token中获取tenant_id
        current_user_identity = get_jwt_identity()
        tenant_id = current_user_identity.get('tenant_id')
        data = request.get_json()
        
        # 验证学科
        subject = Subject.query.filter_by(id=subject_id, tenant_id=tenant_id).first()
        if not subject:
            return error_response('Subject not found', 404)
        
        # 更新考试范围
        subject.exam_scope = data.get('exam_scope', {})
        subject.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return success_response(subject.to_dict())
        
    except Exception as e:
        return error_response(f'Failed to update exam scope: {str(e)}', 500)

def generate_knowledge_graph(subject_id, year):
    """生成知识图谱数据"""
    # 获取学科的所有章节和知识点
    chapters = Chapter.query.filter_by(subject_id=subject_id, is_active=True).all()
    
    nodes = []
    edges = []
    
    # 生成章节节点
    for chapter in chapters:
        nodes.append({
            'id': f'chapter_{chapter.id}',
            'type': 'chapter',
            'name': chapter.name,
            'level': 1,
            'importance': chapter.importance,
            'difficulty': chapter.difficulty,
            'x': 0,  # 将由前端布局算法计算
            'y': 0
        })
        
        # 生成知识点节点
        knowledge_points = chapter.knowledge_points.filter_by(is_active=True).all()
        for kp in knowledge_points:
            nodes.append({
                'id': f'kp_{kp.id}',
                'type': 'knowledge_point',
                'name': kp.name,
                'level': 2,
                'importance': kp.importance,
                'difficulty': kp.difficulty,
                'exam_frequency': kp.exam_frequency,
                'x': 0,
                'y': 0
            })
            
            # 章节到知识点的边
            edges.append({
                'source': f'chapter_{chapter.id}',
                'target': f'kp_{kp.id}',
                'type': 'contains',
                'weight': 1
            })
            
            # 知识点之间的关联边
            if kp.prerequisites:
                for prereq_id in kp.prerequisites:
                    edges.append({
                        'source': f'kp_{prereq_id}',
                        'target': f'kp_{kp.id}',
                        'type': 'prerequisite',
                        'weight': 2
                    })
            
            if kp.related_points:
                for related_id in kp.related_points:
                    edges.append({
                        'source': f'kp_{kp.id}',
                        'target': f'kp_{related_id}',
                        'type': 'related',
                        'weight': 1
                    })
    
    layout_config = {
        'algorithm': 'force',
        'iterations': 100,
        'node_size_factor': 1.0,
        'edge_length': 100,
        'repulsion_strength': 1000
    }
    
    return {
        'nodes': nodes,
        'edges': edges,
        'layout_config': layout_config
    }

def generate_exam_scope(subject_id, year):
    """生成考试范围配置"""
    chapters = Chapter.query.filter_by(subject_id=subject_id, is_active=True).all()
    
    scope = {
        'year': year,
        'chapters': [],
        'key_knowledge_points': [],
        'difficulty_distribution': {
            'easy': 30,
            'medium': 50,
            'hard': 20
        }
    }
    
    for chapter in chapters:
        chapter_scope = {
            'id': chapter.id,
            'name': chapter.name,
            'importance': chapter.importance,
            'included': True,
            'knowledge_points': []
        }
        
        # 获取重要知识点
        important_kps = chapter.knowledge_points.filter(
            KnowledgePoint.importance >= 4,
            KnowledgePoint.is_active == True
        ).all()
        
        for kp in important_kps:
            chapter_scope['knowledge_points'].append({
                'id': kp.id,
                'name': kp.name,
                'importance': kp.importance,
                'exam_frequency': kp.exam_frequency
            })
            
            if kp.importance >= 4:
                scope['key_knowledge_points'].append({
                    'id': kp.id,
                    'name': kp.name,
                    'chapter_name': chapter.name
                })
        
        scope['chapters'].append(chapter_scope)
    
    return scope

def get_graph_type_name(graph_type):
    """获取图谱类型的中文名称"""
    type_names = {
        'exam_scope': '考试范围',
        'full_knowledge': '完整知识图谱',
        'mastery_level': '掌握情况图谱'
    }
    return type_names.get(graph_type, '知识图谱')

def generate_exam_scope_graph(subject_id, year):
    """生成考试范围知识图谱"""
    # 获取学科章节和重要知识点
    chapters = Chapter.query.filter_by(subject_id=subject_id, is_active=True).all()
    
    nodes = []
    edges = []
    
    # 添加学科根节点
    subject = Subject.query.get(subject_id)
    nodes.append({
        'id': f'subject_{subject_id}',
        'name': subject.name,
        'type': 'subject',
        'level': 0,
        'difficulty': 0,
        'importance': 5,
        'mastery_level': 0,
        'question_count': 0
    })
    
    for chapter in chapters:
        # 添加章节节点
        nodes.append({
            'id': f'chapter_{chapter.id}',
            'name': chapter.name,
            'type': 'chapter',
            'level': 1,
            'difficulty': chapter.difficulty,
            'importance': chapter.importance,
            'mastery_level': 0,
            'question_count': 0
        })
        
        # 添加学科到章节的边
        edges.append({
            'source': f'subject_{subject_id}',
            'target': f'chapter_{chapter.id}',
            'type': 'hierarchy',
            'strength': 1.0
        })
        
        # 只包含重要的知识点（考试范围）
        important_kps = chapter.knowledge_points.filter(
            KnowledgePoint.importance >= 4,
            KnowledgePoint.is_active == True
        ).all()
        
        for kp in important_kps:
            # 计算题目数量
            question_count = kp.questions.count() if hasattr(kp, 'questions') else 0
            
            nodes.append({
                'id': f'kp_{kp.id}',
                'name': kp.name,
                'type': 'knowledge_point',
                'level': 2,
                'difficulty': kp.difficulty,
                'importance': kp.importance,
                'mastery_level': 0,  # 默认掌握度为0
                'question_count': question_count
            })
            
            # 添加章节到知识点的边
            edges.append({
                'source': f'chapter_{chapter.id}',
                'target': f'kp_{kp.id}',
                'type': 'hierarchy',
                'strength': 0.8
            })
    
    return {
        'nodes': nodes,
        'edges': edges,
        'layout_config': {
            'layout': 'force',
            'node_size_factor': 1.2,
            'link_strength_factor': 0.8,
            'color_scheme': 'exam_scope'
        }
    }

def generate_mastery_level_graph(subject_id, year):
    """生成掌握情况知识图谱"""
    # 获取学科章节和知识点
    chapters = Chapter.query.filter_by(subject_id=subject_id, is_active=True).all()
    
    nodes = []
    edges = []
    
    # 添加学科根节点
    subject = Subject.query.get(subject_id)
    nodes.append({
        'id': f'subject_{subject_id}',
        'name': subject.name,
        'type': 'subject',
        'level': 0,
        'difficulty': 0,
        'importance': 5,
        'mastery_level': 0,
        'question_count': 0
    })
    
    for chapter in chapters:
        # 计算章节平均掌握度（由于KnowledgePoint没有mastery_level字段，设为默认值0）
        chapter_mastery = 0
        
        # 添加章节节点
        nodes.append({
            'id': f'chapter_{chapter.id}',
            'name': chapter.name,
            'type': 'chapter',
            'level': 1,
            'difficulty': chapter.difficulty,
            'importance': chapter.importance,
            'mastery_level': chapter_mastery,
            'question_count': 0
        })
        
        # 添加学科到章节的边
        edges.append({
            'source': f'subject_{subject_id}',
            'target': f'chapter_{chapter.id}',
            'type': 'hierarchy',
            'strength': 1.0
        })
        
        # 获取所有知识点，按掌握度分组显示
        knowledge_points = chapter.knowledge_points.filter(
            KnowledgePoint.is_active == True
        ).all()
        
        for kp in knowledge_points:
            # 计算题目数量
            question_count = kp.questions.count() if hasattr(kp, 'questions') else 0
            mastery_level = 0  # 默认掌握度为0
            
            nodes.append({
                'id': f'kp_{kp.id}',
                'name': kp.name,
                'type': 'knowledge_point',
                'level': 2,
                'difficulty': kp.difficulty,
                'importance': kp.importance,
                'mastery_level': mastery_level,
                'question_count': question_count
            })
            
            # 添加章节到知识点的边，强度基于掌握度
            strength = 0.5 + (mastery_level / 10.0) * 0.5
            edges.append({
                'source': f'chapter_{chapter.id}',
                'target': f'kp_{kp.id}',
                'type': 'hierarchy',
                'strength': strength
            })
    
    return {
        'nodes': nodes,
        'edges': edges,
        'layout_config': {
            'layout': 'force',
            'node_size_factor': 1.0,
            'link_strength_factor': 1.0,
            'color_scheme': 'mastery_level'
        }
    }

@knowledge_graph_bp.route('/mastery-star-map/<subject_id>', methods=['GET'])
@jwt_required()
def get_mastery_star_map(subject_id):
    """获取基于掌握程度的星图"""
    try:
        current_user_identity = get_jwt_identity()
        user_id = current_user_identity.get('user_id')
        tenant_id = current_user_identity.get('tenant_id')
        
        # 验证学科
        subject = Subject.query.filter_by(id=subject_id, tenant_id=tenant_id).first()
        if not subject:
            return error_response('Subject not found', 404)
        
        # 生成基于掌握程度的知识图谱
        knowledge_graph = knowledge_graph_service.generate_knowledge_graph(
            subject_id=subject_id,
            user_id=user_id
        )
        
        return success_response({
            'subject_id': subject_id,
            'subject_name': knowledge_graph['subject_name'],
            'star_map': knowledge_graph['star_map'],
            'statistics': knowledge_graph['statistics'],
            'generated_at': knowledge_graph['generated_at']
        })
        
    except Exception as e:
        return error_response(f'Error generating mastery star map: {str(e)}', 500)

@knowledge_graph_bp.route('/mastery-classification/<subject_id>', methods=['GET'])
@jwt_required()
def get_mastery_classification(subject_id):
    """获取知识点掌握程度分类"""
    try:
        current_user_identity = get_jwt_identity()
        user_id = current_user_identity.get('user_id')
        tenant_id = current_user_identity.get('tenant_id')
        
        # 验证学科
        subject = Subject.query.filter_by(id=subject_id, tenant_id=tenant_id).first()
        if not subject:
            return error_response('Subject not found', 404)
        
        # 获取该学科的所有知识点分类
        classification_result = mastery_classification_service.classify_user_knowledge_points(
            user_id=user_id,
            subject_id=subject_id
        )
        
        return success_response({
            'subject_id': subject_id,
            'subject_name': subject.name,
            'classification': classification_result,
            'color_standards': {
                'red': {'threshold': '< 60%', 'description': '薄弱知识点，需要重点学习'},
                'yellow': {'threshold': '60% - 80%', 'description': '待巩固知识点，需要练习巩固'},
                'green': {'threshold': '> 80%', 'description': '已掌握知识点，可以拓展学习'}
            }
        })
        
    except Exception as e:
        return error_response(f'Error getting mastery classification: {str(e)}', 500)

@knowledge_graph_bp.route('/update-mastery-color', methods=['POST'])
@jwt_required()
def update_mastery_color():
    """更新知识点掌握程度颜色"""
    try:
        current_user_identity = get_jwt_identity()
        user_id = current_user_identity.get('user_id')
        
        data = request.get_json()
        if not data or 'knowledge_point_id' not in data:
            return error_response('Missing knowledge_point_id', 400)
        
        knowledge_point_id = data['knowledge_point_id']
        
        # 重新计算并更新颜色分类
        new_color = mastery_classification_service.classify_knowledge_point(
            user_id=user_id,
            knowledge_point_id=knowledge_point_id
        )
        
        return success_response({
            'knowledge_point_id': knowledge_point_id,
            'new_color': new_color,
            'message': f'知识点颜色已更新为{new_color}'
        })
        
    except Exception as e:
        return error_response(f'Error updating mastery color: {str(e)}', 500)