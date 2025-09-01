#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - API接口 - subjects.py

Description:
    学科管理API接口，提供学科信息、知识点管理等功能。

Author: Chang Xinglong
Date: 2025-08-30
Version: 1.0.0
License: Apache License 2.0
"""


from flask import request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import api_bp
from models import Subject, Chapter, KnowledgePoint, SubKnowledgePoint, ExamPaper, KnowledgeGraph
from utils.database import db
from utils.response import success_response, error_response
from utils.decorators import admin_required
from sqlalchemy import desc, func

@api_bp.route('/subjects', methods=['GET'])
@jwt_required()
def get_subjects():
    """获取学科列表"""
    try:
        # 从JWT token中获取tenant_id
        current_user_identity = get_jwt_identity()
        tenant_id = current_user_identity.get('tenant_id') if isinstance(current_user_identity, dict) else g.get('tenant_id')
        include_stats = request.args.get('include_stats', 'false').lower() == 'true'
        
        query = Subject.query.filter_by(tenant_id=tenant_id, is_active=True)
        subjects = query.order_by(Subject.sort_order, Subject.name).all()
        
        result = []
        for subject in subjects:
            subject_data = subject.to_dict()
            
            if include_stats:
                # 统计章节和知识点数量
                chapter_count = Chapter.query.filter_by(
                    subject_id=subject.id, is_active=True
                ).count()
                
                knowledge_point_count = db.session.query(func.count(KnowledgePoint.id)).join(
                    Chapter
                ).filter(
                    Chapter.subject_id == subject.id,
                    Chapter.is_active == True,
                    KnowledgePoint.is_active == True
                ).scalar()
                
                subject_data['stats'] = {
                    'chapter_count': chapter_count,
                    'knowledge_point_count': knowledge_point_count or 0
                }
            
            result.append(subject_data)
        
        return success_response(result)
        
    except Exception as e:
        return error_response(f'Failed to get subjects: {str(e)}', 500)

@api_bp.route('/subjects', methods=['POST'])
@jwt_required()
@admin_required
def create_subject():
    """创建学科"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('name'):
            return error_response('Subject name is required', 400)
        
        tenant_id = g.get('tenant_id')
        
        # 检查学科名称是否已存在
        existing = Subject.query.filter_by(
            tenant_id=tenant_id,
            name=data['name'].strip()
        ).first()
        
        if existing:
            return error_response('Subject name already exists', 400)
        
        # 创建学科
        subject = Subject(
            tenant_id=tenant_id,
            name=data['name'].strip(),
            code=data.get('code', '').strip(),
            description=data.get('description', ''),
            icon=data.get('icon', ''),
            color=data.get('color', '#1890ff'),
            sort_order=data.get('sort_order', 0),
            grade_range=data.get('grade_range', []),
            total_score=data.get('total_score', 100),
            category=data.get('category', ''),
            name_en=data.get('name_en', '')
        )
        
        db.session.add(subject)
        db.session.commit()
        
        return success_response(subject.to_dict(), 'Subject created successfully')
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to create subject: {str(e)}', 500)

@api_bp.route('/subjects/<int:subject_id>', methods=['GET'])
@jwt_required()
def get_subject(subject_id):
    """获取学科详情"""
    try:
        tenant_id = g.get('tenant_id')
        include_chapters = request.args.get('include_chapters', 'false').lower() == 'true'
        
        subject = Subject.query.filter_by(
            id=subject_id,
            tenant_id=tenant_id,
            is_active=True
        ).first()
        
        if not subject:
            return error_response('Subject not found', 404)
        
        subject_data = subject.to_dict()
        
        if include_chapters:
            # 包含章节信息
            chapters = Chapter.query.filter_by(
                subject_id=subject_id,
                is_active=True
            ).order_by(Chapter.order, Chapter.name).all()
            
            subject_data['chapters'] = [chapter.to_dict() for chapter in chapters]
        
        return success_response(subject_data)
        
    except Exception as e:
        return error_response(f'Failed to get subject: {str(e)}', 500)

@api_bp.route('/subjects/<int:subject_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_subject(subject_id):
    """更新学科"""
    try:
        tenant_id = g.get('tenant_id')
        subject = Subject.query.filter_by(
            id=subject_id,
            tenant_id=tenant_id
        ).first()
        
        if not subject:
            return error_response('Subject not found', 404)
        
        data = request.get_json()
        
        # 检查名称是否重复
        if 'name' in data and data['name'] != subject.name:
            existing = Subject.query.filter_by(
                tenant_id=tenant_id,
                name=data['name'].strip()
            ).first()
            
            if existing:
                return error_response('Subject name already exists', 400)
        
        # 更新字段
        updatable_fields = [
            'name', 'code', 'description', 'icon', 'color', 'sort_order',
            'grade_range', 'total_score', 'is_active', 'category', 'name_en'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(subject, field, data[field])
        
        db.session.commit()
        
        return success_response(subject.to_dict(), 'Subject updated successfully')
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to update subject: {str(e)}', 500)

@api_bp.route('/subjects/<int:subject_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_subject(subject_id):
    """删除学科"""
    try:
        tenant_id = g.get('tenant_id')
        subject = Subject.query.filter_by(
            id=subject_id,
            tenant_id=tenant_id
        ).first()
        
        if not subject:
            return error_response('Subject not found', 404)
        
        # 软删除
        subject.is_active = False
        db.session.commit()
        
        return success_response(None, 'Subject deleted successfully')
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to delete subject: {str(e)}', 500)

@api_bp.route('/subjects/<int:subject_id>/chapters', methods=['GET'])
@jwt_required()
def get_chapters(subject_id):
    """获取学科章节列表"""
    try:
        tenant_id = g.get('tenant_id')
        include_knowledge_points = request.args.get('include_knowledge_points', 'false').lower() == 'true'
        
        # 验证学科存在
        subject = Subject.query.filter_by(
            id=subject_id,
            tenant_id=tenant_id,
            is_active=True
        ).first()
        
        if not subject:
            return error_response('Subject not found', 404)
        
        chapters = Chapter.query.filter_by(
            subject_id=subject_id,
            is_active=True
        ).order_by(Chapter.order, Chapter.name).all()
        
        result = []
        for chapter in chapters:
            chapter_data = chapter.to_dict()
            
            if include_knowledge_points:
                # 包含知识点
                knowledge_points = KnowledgePoint.query.filter_by(
                    chapter_id=chapter.id,
                    is_active=True
                ).order_by(KnowledgePoint.order, KnowledgePoint.name).all()
                
                chapter_data['knowledge_points'] = [
                    kp.to_dict() for kp in knowledge_points
                ]
            
            result.append(chapter_data)
        
        return success_response(result)
        
    except Exception as e:
        return error_response(f'Failed to get chapters: {str(e)}', 500)

@api_bp.route('/subjects/<int:subject_id>/chapters', methods=['POST'])
@jwt_required()
@admin_required
def create_chapter(subject_id):
    """创建章节"""
    try:
        tenant_id = g.get('tenant_id')
        
        # 验证学科存在
        subject = Subject.query.filter_by(
            id=subject_id,
            tenant_id=tenant_id,
            is_active=True
        ).first()
        
        if not subject:
            return error_response('Subject not found', 404)
        
        data = request.get_json()
        
        if not data.get('name'):
            return error_response('Chapter name is required', 400)
        
        # 检查章节名称是否已存在
        existing = Chapter.query.filter_by(
            subject_id=subject_id,
            name=data['name'].strip()
        ).first()
        
        if existing:
            return error_response('Chapter name already exists', 400)
        
        # 创建章节
        chapter = Chapter(
            subject_id=subject_id,
            name=data['name'].strip(),
            description=data.get('description', ''),
            order=data.get('order', 0),
            difficulty_level=data.get('difficulty_level', 1),
            exam_frequency=data.get('exam_frequency', 0),
            tags=data.get('tags', [])
        )
        
        db.session.add(chapter)
        db.session.commit()
        
        return success_response(chapter.to_dict(), 'Chapter created successfully')
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to create chapter: {str(e)}', 500)

@api_bp.route('/chapters/<int:chapter_id>', methods=['GET'])
@jwt_required()
def get_chapter(chapter_id):
    """获取章节详情"""
    try:
        include_knowledge_points = request.args.get('include_knowledge_points', 'false').lower() == 'true'
        
        chapter = Chapter.query.filter_by(
            id=chapter_id,
            is_active=True
        ).first()
        
        if not chapter:
            return error_response('Chapter not found', 404)
        
        chapter_data = chapter.to_dict()
        
        if include_knowledge_points:
            # 包含知识点
            knowledge_points = KnowledgePoint.query.filter_by(
                chapter_id=chapter_id,
                is_active=True
            ).order_by(KnowledgePoint.order, KnowledgePoint.name).all()
            
            kp_list = []
            for kp in knowledge_points:
                kp_data = kp.to_dict()
                
                # 包含子知识点
                sub_kps = SubKnowledgePoint.query.filter_by(
                    knowledge_point_id=kp.id,
                    is_active=True
                ).order_by(SubKnowledgePoint.order, SubKnowledgePoint.name).all()
                
                kp_data['sub_knowledge_points'] = [sub_kp.to_dict() for sub_kp in sub_kps]
                kp_list.append(kp_data)
            
            chapter_data['knowledge_points'] = kp_list
        
        return success_response(chapter_data)
        
    except Exception as e:
        return error_response(f'Failed to get chapter: {str(e)}', 500)

@api_bp.route('/chapters/<int:chapter_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_chapter(chapter_id):
    """更新章节"""
    try:
        chapter = Chapter.query.filter_by(
            id=chapter_id,
            is_active=True
        ).first()
        
        if not chapter:
            return error_response('Chapter not found', 404)
        
        data = request.get_json()
        
        # 检查名称是否重复
        if 'name' in data and data['name'] != chapter.name:
            existing = Chapter.query.filter_by(
                subject_id=chapter.subject_id,
                name=data['name'].strip()
            ).first()
            
            if existing:
                return error_response('Chapter name already exists', 400)
        
        # 更新字段
        updatable_fields = [
            'name', 'description', 'order', 'difficulty_level',
            'exam_frequency', 'tags', 'is_active'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(chapter, field, data[field])
        
        db.session.commit()
        
        return success_response(chapter.to_dict(), 'Chapter updated successfully')
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to update chapter: {str(e)}', 500)

@api_bp.route('/chapters/<int:chapter_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_chapter(chapter_id):
    """删除章节"""
    try:
        chapter = Chapter.query.filter_by(
            id=chapter_id,
            is_active=True
        ).first()
        
        if not chapter:
            return error_response('Chapter not found', 404)
        
        # 软删除
        chapter.is_active = False
        db.session.commit()
        
        return success_response(None, 'Chapter deleted successfully')
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to delete chapter: {str(e)}', 500)

@api_bp.route('/subjects/initialize-default', methods=['POST'])
@jwt_required()
@admin_required
def initialize_default_subjects():
    """初始化九大学科"""
    try:
        tenant_id = g.get('tenant_id')
        
        # 九大学科配置
        default_subjects = [
            {
                'code': 'chinese',
                'name': '语文',
                'name_en': 'Chinese',
                'category': 'language',
                'description': '语文学科，包含现代文阅读、古诗文阅读、写作等',
                'total_score': 150,
                'sort_order': 1
            },
            {
                'code': 'math',
                'name': '数学',
                'name_en': 'Mathematics',
                'category': 'science',
                'description': '数学学科，包含代数、几何、概率统计等',
                'total_score': 150,
                'sort_order': 2
            },
            {
                'code': 'english',
                'name': '英语',
                'name_en': 'English',
                'category': 'language',
                'description': '英语学科，包含听力、阅读、写作等',
                'total_score': 150,
                'sort_order': 3
            },
            {
                'code': 'physics',
                'name': '物理',
                'name_en': 'Physics',
                'category': 'science',
                'description': '物理学科，包含力学、电磁学、光学等',
                'total_score': 100,
                'sort_order': 4
            },
            {
                'code': 'chemistry',
                'name': '化学',
                'name_en': 'Chemistry',
                'category': 'science',
                'description': '化学学科，包含无机化学、有机化学、物理化学等',
                'total_score': 100,
                'sort_order': 5
            },
            {
                'code': 'biology',
                'name': '生物',
                'name_en': 'Biology',
                'category': 'science',
                'description': '生物学科，包含细胞生物学、遗传学、生态学等',
                'total_score': 100,
                'sort_order': 6
            },
            {
                'code': 'history',
                'name': '历史',
                'name_en': 'History',
                'category': 'liberal_arts',
                'description': '历史学科，包含中国古代史、中国近现代史、世界史等',
                'total_score': 100,
                'sort_order': 7
            },
            {
                'code': 'geography',
                'name': '地理',
                'name_en': 'Geography',
                'category': 'liberal_arts',
                'description': '地理学科，包含自然地理、人文地理、区域地理等',
                'total_score': 100,
                'sort_order': 8
            },
            {
                'code': 'politics',
                'name': '政治',
                'name_en': 'Politics',
                'category': 'liberal_arts',
                'description': '政治学科，包含马克思主义基本原理、思想政治教育等',
                'total_score': 100,
                'sort_order': 9
            }
        ]
        
        created_subjects = []
        
        for subject_data in default_subjects:
            # 检查是否已存在
            existing = Subject.query.filter_by(
                tenant_id=tenant_id,
                code=subject_data['code']
            ).first()
            
            if not existing:
                subject = Subject(
                    tenant_id=tenant_id,
                    **subject_data
                )
                db.session.add(subject)
                created_subjects.append(subject_data['name'])
        
        db.session.commit()
        
        return success_response({
            'message': f'Successfully initialized {len(created_subjects)} subjects',
            'created_subjects': created_subjects
        })
        
    except Exception as e:
        return error_response(f'Failed to initialize subjects: {str(e)}', 500)

@api_bp.route('/subjects/<subject_id>/statistics', methods=['GET'])
@jwt_required()
def get_subject_statistics(subject_id):
    """获取学科统计信息"""
    try:
        tenant_id = g.get('tenant_id')
        
        subject = Subject.query.filter_by(
            id=subject_id, tenant_id=tenant_id, is_active=True
        ).first()
        
        if not subject:
            return error_response('Subject not found', 404)
        
        # 统计章节数量
        chapter_count = Chapter.query.filter_by(
            subject_id=subject_id, is_active=True
        ).count()
        
        # 统计知识点数量
        knowledge_point_count = db.session.query(func.count(KnowledgePoint.id)).join(
            Chapter
        ).filter(
            Chapter.subject_id == subject_id,
            Chapter.is_active == True,
            KnowledgePoint.is_active == True
        ).scalar()
        
        # 统计试卷数量
        paper_count = ExamPaper.query.filter_by(
            subject_id=subject_id, is_active=True
        ).count()
        
        # 统计知识图谱数量
        graph_count = KnowledgeGraph.query.filter_by(
            subject_id=subject_id, is_active=True
        ).count()
        
        # 按年份统计试卷
        paper_by_year = db.session.query(
            ExamPaper.year,
            func.count(ExamPaper.id).label('count')
        ).filter_by(
            subject_id=subject_id, is_active=True
        ).group_by(ExamPaper.year).order_by(desc(ExamPaper.year)).all()
        
        # 按难度统计知识点
        kp_by_difficulty = db.session.query(
            KnowledgePoint.difficulty,
            func.count(KnowledgePoint.id).label('count')
        ).join(Chapter).filter(
            Chapter.subject_id == subject_id,
            Chapter.is_active == True,
            KnowledgePoint.is_active == True
        ).group_by(KnowledgePoint.difficulty).all()
        
        statistics = {
            'basic_stats': {
                'chapter_count': chapter_count,
                'knowledge_point_count': knowledge_point_count or 0,
                'paper_count': paper_count,
                'graph_count': graph_count
            },
            'paper_by_year': [{'year': year, 'count': count} for year, count in paper_by_year],
            'knowledge_point_by_difficulty': [
                {'difficulty': diff, 'count': count} for diff, count in kp_by_difficulty
            ]
        }
        
        return success_response(statistics)
        
    except Exception as e:
        return error_response(f'Failed to get subject statistics: {str(e)}', 500)