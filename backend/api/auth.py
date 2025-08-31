#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - API接口 - auth.py

Description:
    用户认证API接口，提供登录、注册、令牌刷新等认证相关功能。

Author: Chang Xinglong
Date: 2025-08-30
Version: 1.0.0
License: Apache License 2.0
"""


from flask import request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, create_refresh_token
from . import api_bp
from models import User, Tenant, UserProfile
from utils.database import db
from utils.validators import validate_email, validate_password
from utils.response import success_response, error_response
from datetime import datetime

@api_bp.route('/auth/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return error_response(f'{field} is required', 400)
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        
        # 验证邮箱格式
        if not validate_email(email):
            return error_response('Invalid email format', 400)
        
        # 验证密码强度
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            return error_response(error_msg, 400)
        
        # 获取租户信息
        tenant_id = g.get('tenant_id', 'default')
        tenant = Tenant.query.filter_by(subdomain=tenant_id, is_active=True).first()
        if not tenant:
            # 如果找不到租户，创建默认租户
            tenant = Tenant(
                name='Default Tenant',
                subdomain=tenant_id,
                is_active=True
            )
            db.session.add(tenant)
            db.session.commit()
        
        # 检查用户名和邮箱是否已存在
        existing_user = User.query.filter_by(
            tenant_id=tenant.id,
            username=username
        ).first()
        if existing_user:
            return error_response('Username already exists', 400)
        
        existing_email = User.query.filter_by(
            tenant_id=tenant.id,
            email=email
        ).first()
        if existing_email:
            return error_response('Email already exists', 400)
        
        # 创建用户
        user = User(
            tenant_id=tenant.id,
            username=username,
            email=email,
            real_name=data.get('real_name', ''),
            grade=data.get('grade', ''),
            school=data.get('school', ''),
            language=data.get('language', 'zh')
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.flush()  # 获取用户ID
        
        # 创建用户档案
        profile = UserProfile(
            user_id=user.id,
            target_subjects=data.get('target_subjects', []),
            target_score=data.get('target_score')
        )
        db.session.add(profile)
        db.session.commit()
        
        # 生成JWT令牌
        access_token, refresh_token = user.generate_tokens()
        
        return success_response({
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }, 'Registration successful')
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Registration failed: {str(e)}', 500)

@api_bp.route('/auth/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('username') or not data.get('password'):
            return error_response('Username and password are required', 400)
        
        username = data['username'].strip()
        password = data['password']
        
        # 获取租户信息
        tenant_id = g.get('tenant_id', 'default')
        tenant = Tenant.query.filter_by(subdomain=tenant_id, is_active=True).first()
        if not tenant:
            return error_response('Invalid tenant', 400)
        
        # 查找用户（支持用户名或邮箱登录）
        user = User.query.filter_by(
            tenant_id=tenant.id,
            username=username,
            is_active=True
        ).first()
        
        if not user:
            user = User.query.filter_by(
                tenant_id=tenant.id,
                email=username,
                is_active=True
            ).first()
        
        if not user or not user.check_password(password):
            return error_response('Invalid username or password', 401)
        
        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        db.session.commit()
        
        # 生成JWT令牌
        access_token, refresh_token = user.generate_tokens()
        
        return success_response({
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }, 'Login successful')
        
    except Exception as e:
        return error_response(f'Login failed: {str(e)}', 500)

@api_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新访问令牌"""
    try:
        current_user_data = get_jwt_identity()
        user_id = current_user_data['user_id']
        
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return error_response('User not found or inactive', 404)
        
        # 生成新的访问令牌
        access_token = create_access_token(identity=current_user_data)
        
        return success_response({
            'access_token': access_token
        }, 'Token refreshed successfully')
        
    except Exception as e:
        return error_response(f'Token refresh failed: {str(e)}', 500)

@api_bp.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    # 在实际应用中，这里应该将令牌加入黑名单
    # 目前只是返回成功响应
    return success_response(None, 'Logout successful')

@api_bp.route('/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取用户档案"""
    try:
        current_user_data = get_jwt_identity()
        user_id = current_user_data['user_id']
        
        user = User.query.get(user_id)
        if not user:
            return error_response('User not found', 404)
        
        profile_data = user.to_dict(include_sensitive=True)
        if user.profile:
            profile_data['profile'] = user.profile.to_dict()
        
        return success_response(profile_data)
        
    except Exception as e:
        return error_response(f'Failed to get profile: {str(e)}', 500)

@api_bp.route('/auth/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新用户档案"""
    try:
        current_user_data = get_jwt_identity()
        user_id = current_user_data['user_id']
        
        user = User.query.get(user_id)
        if not user:
            return error_response('User not found', 404)
        
        data = request.get_json()
        
        # 更新用户基本信息
        if 'real_name' in data:
            user.real_name = data['real_name']
        if 'avatar' in data:
            user.avatar = data['avatar']
        if 'grade' in data:
            user.grade = data['grade']
        if 'school' in data:
            user.school = data['school']
        if 'language' in data:
            user.language = data['language']
        if 'timezone' in data:
            user.timezone = data['timezone']
        
        # 更新用户档案
        if not user.profile:
            user.profile = UserProfile(user_id=user.id)
        
        profile = user.profile
        if 'target_score' in data:
            profile.target_score = data['target_score']
        if 'current_score' in data:
            profile.current_score = data['current_score']
        if 'target_subjects' in data:
            profile.target_subjects = data['target_subjects']
        if 'learning_style' in data:
            profile.learning_style = data['learning_style']
        if 'study_time_preference' in data:
            profile.study_time_preference = data['study_time_preference']
        if 'difficulty_preference' in data:
            profile.difficulty_preference = data['difficulty_preference']
        
        db.session.commit()
        
        profile_data = user.to_dict()
        profile_data['profile'] = profile.to_dict()
        
        return success_response(profile_data, 'Profile updated successfully')
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to update profile: {str(e)}', 500)

@api_bp.route('/auth/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """修改密码"""
    try:
        current_user_data = get_jwt_identity()
        user_id = current_user_data['user_id']
        
        user = User.query.get(user_id)
        if not user:
            return error_response('User not found', 404)
        
        data = request.get_json()
        
        if not data.get('current_password') or not data.get('new_password'):
            return error_response('Current password and new password are required', 400)
        
        # 验证当前密码
        if not user.check_password(data['current_password']):
            return error_response('Current password is incorrect', 400)
        
        # 验证新密码强度
        if not validate_password(data['new_password']):
            return error_response('New password must be at least 8 characters long', 400)
        
        # 更新密码
        user.set_password(data['new_password'])
        db.session.commit()
        
        return success_response(None, 'Password changed successfully')
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to change password: {str(e)}', 500)