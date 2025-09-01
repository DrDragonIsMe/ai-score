#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - API接口 - exam_papers.py

Description:
    真题试卷管理API接口，提供试卷上传、解析、管理等功能。

Author: Chang Xinglong
Date: 2025-01-21
Version: 1.0.0
License: Apache License 2.0
"""

import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, g, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from models import ExamPaper, Question, Subject, KnowledgePoint, KnowledgeGraph
from utils.database import db
from utils.response import success_response, error_response
from utils.decorators import admin_required
from sqlalchemy import desc, func, and_
from services.ai_parser import AIParser
from services.paper_downloader import PaperDownloader

exam_papers_bp = Blueprint('exam_papers', __name__)

# 允许的文件类型
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """检查文件类型是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@exam_papers_bp.route('/exam-papers', methods=['GET'])
@jwt_required()
def get_exam_papers():
    """获取试卷列表"""
    try:
        # 从JWT token中获取tenant_id
        current_user_identity = get_jwt_identity()
        tenant_id = current_user_identity.get('tenant_id') if isinstance(current_user_identity, dict) else g.get('tenant_id')
        subject_id = request.args.get('subject_id')
        year = request.args.get('year', type=int)
        exam_type = request.args.get('exam_type')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = ExamPaper.query.filter_by(tenant_id=tenant_id, is_active=True)
        
        # 筛选条件
        if subject_id:
            query = query.filter_by(subject_id=subject_id)
        if year:
            query = query.filter_by(year=year)
        if exam_type:
            query = query.filter_by(exam_type=exam_type)
        
        # 分页
        pagination = query.order_by(desc(ExamPaper.year), desc(ExamPaper.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = {
            'papers': [paper.to_dict() for paper in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }
        
        return success_response(result)
        
    except Exception as e:
        return error_response(f'Failed to get exam papers: {str(e)}', 500)

@exam_papers_bp.route('/exam-papers/upload', methods=['POST'])
@jwt_required()
def upload_exam_paper():
    """上传试卷文件"""
    try:
        # 从JWT token中获取tenant_id
        current_user = get_jwt_identity()
        tenant_id = current_user.get('tenant_id')
        
        # 检查文件
        if 'file' not in request.files:
            return error_response('No file provided', 400)
        
        file = request.files['file']
        if file.filename == '':
            return error_response('No file selected', 400)
        
        if not allowed_file(file.filename):
            return error_response('File type not allowed', 400)
        
        # 获取表单数据
        title = request.form.get('title', '').strip()
        subject_id = request.form.get('subject_id', '').strip()
        year = request.form.get('year', type=int)
        exam_type = request.form.get('exam_type', '').strip()
        region = request.form.get('region', '').strip()
        description = request.form.get('description', '').strip()
        
        if not all([title, subject_id]):
            return error_response('Title and subject_id are required', 400)
        
        # 验证学科是否存在
        subject = Subject.query.filter_by(id=subject_id, tenant_id=tenant_id).first()
        if not subject:
            return error_response('Subject not found', 404)
        
        # 保存文件
        if not file.filename:
            return error_response('Invalid filename', 400)
        
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        new_filename = f"{uuid.uuid4().hex}.{file_ext}"
        
        # 创建上传目录
        upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'exam_papers')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, new_filename)
        file.save(file_path)
        
        # 创建试卷记录
        exam_paper = ExamPaper(
            tenant_id=tenant_id,
            subject_id=subject_id,
            title=title,
            description=description,
            year=year,
            exam_type=exam_type,
            region=region,
            file_path=file_path,
            file_type=file_ext,
            file_size=os.path.getsize(file_path)
        )
        
        db.session.add(exam_paper)
        db.session.commit()
        
        # 启动AI解析任务
        try:
            ai_parser = AIParser()
            ai_parser.parse_exam_paper(exam_paper.id)
            
            # 更新解析状态
            exam_paper.parse_status = 'completed'
            db.session.commit()
            
        except Exception as parse_error:
            # 解析失败，更新状态
            exam_paper.parse_status = 'failed'
            exam_paper.parse_result = {'error': str(parse_error)}
            db.session.commit()
            current_app.logger.error(f'Failed to parse exam paper {exam_paper.id}: {str(parse_error)}')
        
        return success_response(exam_paper.to_dict())
        
    except Exception as e:
        return error_response(f'Failed to upload exam paper: {str(e)}', 500)

@exam_papers_bp.route('/exam-papers/<paper_id>/parse-status', methods=['GET'])
@jwt_required()
def get_parse_status(paper_id):
    """获取试卷解析状态"""
    try:
        # 从JWT token中获取tenant_id
        current_user = get_jwt_identity()
        tenant_id = current_user.get('tenant_id')
        
        exam_paper = ExamPaper.query.filter_by(
            id=paper_id, 
            tenant_id=tenant_id
        ).first()
        
        if not exam_paper:
            return error_response('Exam paper not found', 404)
        
        return success_response({
            'parse_status': exam_paper.parse_status,
            'parse_result': exam_paper.parse_result,
            'question_count': exam_paper.question_count
        })
        
    except Exception as e:
        return error_response(f'Failed to get parse status: {str(e)}', 500)

@exam_papers_bp.route('/exam-papers/<paper_id>', methods=['GET'])
@jwt_required()
def get_exam_paper(paper_id):
    """获取试卷详情"""
    try:
        tenant_id = g.get('tenant_id')
        include_questions = request.args.get('include_questions', 'false').lower() == 'true'
        
        paper = ExamPaper.query.filter_by(
            id=paper_id, tenant_id=tenant_id, is_active=True
        ).first()
        
        if not paper:
            return error_response('Exam paper not found', 404)
        
        return success_response(paper.to_dict(include_questions=include_questions))
        
    except Exception as e:
        return error_response(f'Failed to get exam paper: {str(e)}', 500)

@exam_papers_bp.route('/exam-papers/<paper_id>', methods=['PUT'])
@jwt_required()
def update_exam_paper(paper_id):
    """更新试卷信息"""
    try:
        tenant_id = g.get('tenant_id')
        data = request.get_json()
        
        paper = ExamPaper.query.filter_by(
            id=paper_id, tenant_id=tenant_id, is_active=True
        ).first()
        
        if not paper:
            return error_response('Exam paper not found', 404)
        
        # 更新字段
        if 'title' in data:
            paper.title = data['title'].strip()
        if 'description' in data:
            paper.description = data['description'].strip()
        if 'year' in data:
            paper.year = data['year']
        if 'exam_type' in data:
            paper.exam_type = data['exam_type'].strip()
        if 'region' in data:
            paper.region = data['region'].strip()
        if 'total_score' in data:
            paper.total_score = data['total_score']
        if 'duration' in data:
            paper.duration = data['duration']
        if 'difficulty_level' in data:
            paper.difficulty_level = data['difficulty_level']
        
        paper.updated_at = datetime.utcnow()
        db.session.commit()
        
        return success_response(paper.to_dict())
        
    except Exception as e:
        return error_response(f'Failed to update exam paper: {str(e)}', 500)

@exam_papers_bp.route('/exam-papers/<paper_id>', methods=['DELETE'])
@jwt_required()
def delete_exam_paper(paper_id):
    """删除试卷"""
    try:
        tenant_id = g.get('tenant_id')
        
        paper = ExamPaper.query.filter_by(
            id=paper_id, tenant_id=tenant_id, is_active=True
        ).first()
        
        if not paper:
            return error_response('Exam paper not found', 404)
        
        # 软删除
        paper.is_active = False
        paper.updated_at = datetime.utcnow()
        db.session.commit()
        
        return success_response({'message': 'Exam paper deleted successfully'})
        
    except Exception as e:
        return error_response(f'Failed to delete exam paper: {str(e)}', 500)

@exam_papers_bp.route('/exam-papers/<paper_id>/questions', methods=['GET'])
@jwt_required()
def get_paper_questions(paper_id):
    """获取试卷题目列表"""
    try:
        tenant_id = g.get('tenant_id')
        
        paper = ExamPaper.query.filter_by(
            id=paper_id, tenant_id=tenant_id, is_active=True
        ).first()
        
        if not paper:
            return error_response('Exam paper not found', 404)
        
        questions = Question.query.filter_by(
            exam_paper_id=paper_id, is_active=True
        ).order_by(Question.question_number).all()
        
        return success_response([q.to_dict() for q in questions])
        
    except Exception as e:
        return error_response(f'Failed to get paper questions: {str(e)}', 500)

@exam_papers_bp.route('/exam-papers/<paper_id>/questions/<question_id>/knowledge-points', methods=['POST'])
@jwt_required()
def link_question_knowledge_points(paper_id, question_id):
    """关联题目与知识点"""
    try:
        tenant_id = g.get('tenant_id')
        data = request.get_json()
        knowledge_point_ids = data.get('knowledge_point_ids', [])
        
        # 验证试卷和题目
        paper = ExamPaper.query.filter_by(
            id=paper_id, tenant_id=tenant_id, is_active=True
        ).first()
        
        if not paper:
            return error_response('Exam paper not found', 404)
        
        question = Question.query.filter_by(
            id=question_id, exam_paper_id=paper_id, is_active=True
        ).first()
        
        if not question:
            return error_response('Question not found', 404)
        
        # 验证知识点
        valid_points = KnowledgePoint.query.filter(
            KnowledgePoint.id.in_(knowledge_point_ids),
            KnowledgePoint.is_active == True
        ).all()
        
        if len(valid_points) != len(knowledge_point_ids):
            return error_response('Some knowledge points not found', 400)
        
        # 更新关联
        question.knowledge_points = knowledge_point_ids
        question.updated_at = datetime.utcnow()
        db.session.commit()
        
        return success_response(question.to_dict())
        
    except Exception as e:
        return error_response(f'Failed to link question knowledge points: {str(e)}', 500)

@exam_papers_bp.route('/subjects/<subject_id>/download-papers', methods=['POST'])
@jwt_required()
def download_subject_papers(subject_id):
    """下载学科真题"""
    try:
        # 从JWT token中获取tenant_id
        current_user = get_jwt_identity()
        tenant_id = current_user.get('tenant_id')
        data = request.get_json()
        years = data.get('years', 10)  # 默认下载近10年
        
        # 验证学科
        subject = Subject.query.filter_by(id=subject_id, tenant_id=tenant_id).first()
        if not subject:
            return error_response('Subject not found', 404)
        
        # 创建下载器实例并开始下载
        downloader = PaperDownloader()
        result = downloader.download_subject_papers(subject_id, years, tenant_id)
        
        if result['success']:
            return success_response({
                'message': f'Successfully downloaded papers for {subject.name}',
                'subject_name': result['subject_name'],
                'years': years,
                'total_found': result['total_found'],
                'saved_count': result['saved_count'],
                'status': 'completed'
            })
        else:
            return error_response(f'Download failed: {result.get("error", "Unknown error")}', 500)
        
    except Exception as e:
        return error_response(f'Failed to start download: {str(e)}', 500)