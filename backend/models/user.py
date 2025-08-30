#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 数据模型 - user.py

Description:
    用户数据模型，定义用户信息、权限等数据结构。

Author: Chang Xinglong
Date: 2025-01-20
Version: 1.0.0
License: Apache License 2.0
"""


from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token
from utils.database import db
import uuid

class User(db.Model):
    """用户模型"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    
    # 基本信息
    username = db.Column(db.String(50), nullable=False, comment='用户名')
    email = db.Column(db.String(100), nullable=False, comment='邮箱')
    phone = db.Column(db.String(20), comment='手机号')
    password_hash = db.Column(db.String(255), nullable=False, comment='密码哈希')
    
    # 用户状态
    is_active = db.Column(db.Boolean, default=True, comment='是否激活')
    is_verified = db.Column(db.Boolean, default=False, comment='是否验证')
    role = db.Column(db.String(20), default='student', comment='角色：student/teacher/admin')
    
    # 个人信息
    real_name = db.Column(db.String(50), comment='真实姓名')
    avatar = db.Column(db.String(200), comment='头像URL')
    grade = db.Column(db.String(10), comment='年级')
    school = db.Column(db.String(100), comment='学校')
    
    # 偏好设置
    language = db.Column(db.String(10), default='zh', comment='语言偏好')
    timezone = db.Column(db.String(50), default='Asia/Shanghai', comment='时区')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    last_login_at = db.Column(db.DateTime, comment='最后登录时间')
    
    # 关系
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    study_records = db.relationship('StudyRecord', backref='user', lazy='dynamic')
    memory_cards = db.relationship('MemoryCard', backref='user', lazy='dynamic')
    
    # 唯一约束：同一租户下用户名和邮箱唯一
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'username', name='uq_tenant_username'),
        db.UniqueConstraint('tenant_id', 'email', name='uq_tenant_email'),
    )
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def generate_tokens(self):
        """生成JWT令牌"""
        identity = {
            'user_id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'role': self.role
        }
        access_token = create_access_token(identity=identity)
        refresh_token = create_refresh_token(identity=identity)
        return access_token, refresh_token
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            'id': str(self.id),
            'username': self.username,
            'email': self.email if include_sensitive else None,
            'phone': self.phone if include_sensitive else None,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'role': self.role,
            'real_name': self.real_name,
            'avatar': self.avatar,
            'grade': self.grade,
            'school': self.school,
            'language': self.language,
            'timezone': self.timezone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }
        return {k: v for k, v in data.items() if v is not None}

class UserProfile(db.Model):
    """用户学习档案"""
    
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # 学习目标
    target_score = db.Column(db.Integer, comment='目标分数')
    current_score = db.Column(db.Integer, comment='当前分数')
    target_subjects = db.Column(db.JSON, default=[], comment='目标科目')
    
    # 学习特征
    learning_style = db.Column(db.String(20), comment='学习风格：visual/auditory/kinesthetic')
    study_time_preference = db.Column(db.String(20), comment='学习时间偏好：morning/afternoon/evening')
    difficulty_preference = db.Column(db.Integer, default=3, comment='难度偏好1-5')
    
    # 遗忘曲线参数
    memory_strength = db.Column(db.Float, default=1.0, comment='记忆强度')
    forgetting_rate = db.Column(db.Float, default=0.5, comment='遗忘率')
    
    # 答题习惯
    avg_answer_time = db.Column(db.Float, comment='平均答题时间(秒)')
    accuracy_rate = db.Column(db.Float, comment='正确率')
    common_mistakes = db.Column(db.JSON, default=[], comment='常见错误类型')
    
    # 学习统计
    total_study_time = db.Column(db.Integer, default=0, comment='总学习时间(分钟)')
    total_questions = db.Column(db.Integer, default=0, comment='总题目数')
    correct_questions = db.Column(db.Integer, default=0, comment='正确题目数')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserProfile {self.user_id}>'
    
    def get_accuracy_rate(self):
        """计算正确率"""
        if self.total_questions == 0:
            return 0
        return round(self.correct_questions / self.total_questions * 100, 2)
    
    def update_stats(self, is_correct, time_spent):
        """更新统计数据"""
        self.total_questions += 1
        if is_correct:
            self.correct_questions += 1
        
        # 更新平均答题时间
        if self.avg_answer_time:
            self.avg_answer_time = (self.avg_answer_time * (self.total_questions - 1) + time_spent) / self.total_questions
        else:
            self.avg_answer_time = time_spent
        
        self.accuracy_rate = self.get_accuracy_rate()
        db.session.commit()
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': str(self.id),
            'target_score': self.target_score,
            'current_score': self.current_score,
            'target_subjects': self.target_subjects,
            'learning_style': self.learning_style,
            'study_time_preference': self.study_time_preference,
            'difficulty_preference': self.difficulty_preference,
            'memory_strength': self.memory_strength,
            'forgetting_rate': self.forgetting_rate,
            'avg_answer_time': self.avg_answer_time,
            'accuracy_rate': self.accuracy_rate,
            'common_mistakes': self.common_mistakes,
            'total_study_time': self.total_study_time,
            'total_questions': self.total_questions,
            'correct_questions': self.correct_questions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }