#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - API接口 - users.py

Description:
    用户管理API接口，提供用户信息查询、更新、权限管理等功能。

Author: Chang Xinglong
Date: 2025-08-30
Version: 1.0.0
License: Apache License 2.0
"""


from flask import request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import api_bp
from models import User, UserProfile, StudyRecord
from utils.database import db
from utils.response import success_response, error_response
from utils.decorators import admin_required
from datetime import datetime, timedelta
from sqlalchemy import func, desc

@api_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_users():
    """获取用户列表（管理员）"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search', '').strip()
        role = request.args.get('role', '').strip()
        grade = request.args.get('grade', '').strip()
        is_active = request.args.get('is_active')
        
        # 获取当前租户ID
        tenant_id = g.get('tenant_id')
        
        query = User.query.filter_by(tenant_id=tenant_id)
        
        # 搜索过滤
        if search:
            query = query.filter(
                db.or_(
                    User.username.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%'),
                    User.real_name.ilike(f'%{search}%')
                )
            )
        
        # 角色过滤
        if role:
            query = query.filter(User.role == role)
        
        # 年级过滤
        if grade:
            query = query.filter(User.grade == grade)
        
        # 状态过滤
        if is_active is not None:
            query = query.filter(User.is_active == (is_active.lower() == 'true'))
        
        # 分页
        pagination = query.order_by(desc(User.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        users = [user.to_dict() for user in pagination.items]
        
        return success_response({
            'users': users,
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
        return error_response(f'Failed to get users: {str(e)}', 500)

@api_bp.route('/users/<string:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """获取用户详情"""
    try:
        current_user_data = get_jwt_identity()
        current_user_id = current_user_data['user_id']
        current_user_role = current_user_data.get('role', 'student')
        
        # 只有管理员或用户本人可以查看详情
        if current_user_role != 'admin' and current_user_id != user_id:
            return error_response('Permission denied', 403)
        
        tenant_id = g.get('tenant_id')
        user = User.query.filter_by(id=user_id, tenant_id=tenant_id).first()
        
        if not user:
            return error_response('User not found', 404)
        
        user_data = user.to_dict(include_sensitive=(current_user_role == 'admin'))
        
        # 包含用户档案
        if user.profile:
            user_data['profile'] = user.profile.to_dict()
        
        # 包含学习统计（最近30天）
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        study_stats = db.session.query(
            func.count(StudyRecord.id).label('total_records'),
            func.sum(StudyRecord.study_duration).label('total_duration'),
            func.avg(StudyRecord.score).label('avg_score')
        ).filter(
            StudyRecord.user_id == user_id,
            StudyRecord.created_at >= thirty_days_ago
        ).first()
        
        user_data['study_stats'] = {
            'total_records': getattr(study_stats, 'total_records', 0) or 0,
            'total_duration': int(getattr(study_stats, 'total_duration', 0) or 0),
            'avg_score': float(getattr(study_stats, 'avg_score', 0) or 0)
        }
        
        return success_response(user_data)
        
    except Exception as e:
        return error_response(f'Failed to get user: {str(e)}', 500)

@api_bp.route('/users/<string:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """更新用户信息"""
    try:
        current_user_data = get_jwt_identity()
        current_user_id = current_user_data['user_id']
        current_user_role = current_user_data.get('role', 'student')
        
        # 只有管理员或用户本人可以更新
        if current_user_role != 'admin' and current_user_id != user_id:
            return error_response('Permission denied', 403)
        
        tenant_id = g.get('tenant_id')
        user = User.query.filter_by(id=user_id, tenant_id=tenant_id).first()
        
        if not user:
            return error_response('User not found', 404)
        
        data = request.get_json()
        
        # 普通用户只能更新部分字段
        if current_user_role != 'admin':
            allowed_fields = ['real_name', 'avatar', 'grade', 'school', 'language', 'timezone']
            data = {k: v for k, v in data.items() if k in allowed_fields}
        
        # 更新用户信息
        for field in ['real_name', 'avatar', 'grade', 'school', 'language', 'timezone']:
            if field in data:
                setattr(user, field, data[field])
        
        # 管理员可以更新的额外字段
        if current_user_role == 'admin':
            for field in ['role', 'is_active', 'is_verified']:
                if field in data:
                    setattr(user, field, data[field])
        
        db.session.commit()
        
        return success_response(user.to_dict(), 'User updated successfully')
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to update user: {str(e)}', 500)

@api_bp.route('/users/<string:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id):
    """删除用户（管理员）"""
    try:
        tenant_id = g.get('tenant_id')
        user = User.query.filter_by(id=user_id, tenant_id=tenant_id).first()
        
        if not user:
            return error_response('User not found', 404)
        
        # 软删除：设置为非活跃状态
        user.is_active = False
        user.deleted_at = datetime.utcnow()
        
        db.session.commit()
        
        return success_response(None, 'User deleted successfully')
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to delete user: {str(e)}', 500)

@api_bp.route('/users/<string:user_id>/study-records', methods=['GET'])
@jwt_required()
def get_user_study_records(user_id):
    """获取用户学习记录"""
    try:
        current_user_data = get_jwt_identity()
        current_user_id = current_user_data['user_id']
        current_user_role = current_user_data.get('role', 'student')
        
        # 只有管理员或用户本人可以查看学习记录
        if current_user_role != 'admin' and current_user_id != user_id:
            return error_response('Permission denied', 403)
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        study_type = request.args.get('study_type', '').strip()
        subject_id = request.args.get('subject_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = StudyRecord.query.filter_by(user_id=user_id)
        
        # 过滤条件
        if study_type:
            query = query.filter(StudyRecord.study_type == study_type)
        
        if subject_id:
            query = query.filter(StudyRecord.subject_id == subject_id)
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                query = query.filter(StudyRecord.created_at >= start_dt)
            except ValueError:
                return error_response('Invalid start_date format', 400)
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                query = query.filter(StudyRecord.created_at <= end_dt)
            except ValueError:
                return error_response('Invalid end_date format', 400)
        
        # 分页
        pagination = query.order_by(desc(StudyRecord.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        records = [record.to_dict() for record in pagination.items]
        
        return success_response({
            'records': records,
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
        return error_response(f'Failed to get study records: {str(e)}', 500)

@api_bp.route('/users/<string:user_id>/stats', methods=['GET'])
@jwt_required()
def get_user_stats(user_id):
    """获取用户统计数据"""
    try:
        current_user_data = get_jwt_identity()
        current_user_id = current_user_data['user_id']
        current_user_role = current_user_data.get('role', 'student')
        
        # 只有管理员或用户本人可以查看统计
        if current_user_role != 'admin' and current_user_id != user_id:
            return error_response('Permission denied', 403)
        
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 学习统计
        study_stats = db.session.query(
            func.count(StudyRecord.id).label('total_sessions'),
            func.sum(StudyRecord.study_duration).label('total_duration'),
            func.avg(StudyRecord.score).label('avg_score'),
            func.count(func.distinct(func.date(StudyRecord.created_at))).label('study_days')
        ).filter(
            StudyRecord.user_id == user_id,
            StudyRecord.created_at >= start_date
        ).first()
        
        # 按学科统计
        subject_stats = db.session.query(
            StudyRecord.subject_id,
            func.count(StudyRecord.id).label('sessions'),
            func.sum(StudyRecord.study_duration).label('duration'),
            func.avg(StudyRecord.score).label('avg_score')
        ).filter(
            StudyRecord.user_id == user_id,
            StudyRecord.created_at >= start_date
        ).group_by(StudyRecord.subject_id).all()
        
        # 按日期统计（最近7天）
        daily_stats = db.session.query(
            func.date(StudyRecord.created_at).label('date'),
            func.count(StudyRecord.id).label('sessions'),
            func.sum(StudyRecord.study_duration).label('duration')
        ).filter(
            StudyRecord.user_id == user_id,
            StudyRecord.created_at >= datetime.utcnow() - timedelta(days=7)
        ).group_by(func.date(StudyRecord.created_at)).all()
        
        return success_response({
            'overview': {
                'total_sessions': getattr(study_stats, 'total_sessions', 0) or 0,
                'total_duration': int(getattr(study_stats, 'total_duration', 0) or 0),
                'avg_score': float(getattr(study_stats, 'avg_score', 0) or 0),
                'study_days': getattr(study_stats, 'study_days', 0) or 0,
                'avg_daily_duration': int((getattr(study_stats, 'total_duration', 0) or 0) / max(getattr(study_stats, 'study_days', 0) or 1, 1))
            },
            'by_subject': [
                {
                    'subject_id': stat.subject_id,
                    'sessions': stat.sessions,
                    'duration': int(stat.duration),
                    'avg_score': float(stat.avg_score)
                }
                for stat in subject_stats
            ],
            'daily': [
                {
                    'date': stat.date.isoformat(),
                    'sessions': stat.sessions,
                    'duration': int(stat.duration)
                }
                for stat in daily_stats
            ]
        })
        
    except Exception as e:
        return error_response(f'Failed to get user stats: {str(e)}', 500)