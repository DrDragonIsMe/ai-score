#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - API接口 - subjects.py

Description:
    学科管理API接口，提供学科信息、知识点管理等功能。

Author: Chang Xinglong
Date: 2025-08-31
Version: 1.0.0
License: Apache License 2.0
"""


from flask import request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import api_bp
from models import Subject, Chapter, KnowledgePoint, SubKnowledgePoint
from utils.database import db
from utils.response import success_response, error_response
from utils.decorators import admin_required
from sqlalchemy import desc, func

@api_bp.route('/subjects', methods=['GET'])
@jwt_required()
def get_subjects():
    """获取学科列表"""
    try:
        tenant_id = g.get('tenant_id')
        include_stats = request.args.get('include_stats', 'false').lower() == 'true'
        
        query = Subject.query.filter_by(tenant_id=tenant_id, is_active=True)
        subjects = query.order_by(Subject.order, Subject.name).all()
        
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
            order=data.get('order', 0),
            grade_levels=data.get('grade_levels', []),
            exam_types=data.get('exam_types', []),
            total_score=data.get('total_score', 100)
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
            'name', 'code', 'description', 'icon', 'color', 'order',
            'grade_levels', 'exam_types', 'total_score', 'is_active'
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