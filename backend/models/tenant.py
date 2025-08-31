#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 数据模型 - tenant.py

Description:
    租户数据模型，支持多租户架构的数据隔离。

Author: Chang Xinglong
Date: 2025-08-31
Version: 1.0.0
License: Apache License 2.0
"""


from datetime import datetime
from utils.database import db
import uuid

class Tenant(db.Model):
    """租户模型 - 支持多租户SaaS架构"""
    
    __tablename__ = 'tenants'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False, comment='租户名称')
    subdomain = db.Column(db.String(50), unique=True, nullable=False, comment='子域名')
    domain = db.Column(db.String(100), comment='自定义域名')
    
    # 租户状态
    is_active = db.Column(db.Boolean, default=True, comment='是否激活')
    plan = db.Column(db.String(20), default='basic', comment='套餐类型')
    max_users = db.Column(db.Integer, default=100, comment='最大用户数')
    
    # 配置信息
    settings = db.Column(db.JSON, default={}, comment='租户配置')
    ai_model_config = db.Column(db.JSON, default={}, comment='AI模型配置')
    
    # 联系信息
    contact_name = db.Column(db.String(50), comment='联系人姓名')
    contact_email = db.Column(db.String(100), comment='联系邮箱')
    contact_phone = db.Column(db.String(20), comment='联系电话')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    users = db.relationship('User', backref='tenant', lazy='dynamic')
    
    def __repr__(self):
        return f'<Tenant {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': str(self.id),
            'name': self.name,
            'subdomain': self.subdomain,
            'domain': self.domain,
            'is_active': self.is_active,
            'plan': self.plan,
            'max_users': self.max_users,
            'settings': self.settings,
            'ai_model_config': self.ai_model_config,
            'contact_name': self.contact_name,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_ai_model_config(self):
        """获取AI模型配置"""
        from config import Config
        default_config = {
            'current_model': Config.DEFAULT_AI_MODEL,
            'models': Config.AI_MODELS
        }
        return {**default_config, **self.ai_model_config}
    
    def update_ai_model_config(self, config):
        """更新AI模型配置"""
        current_config = self.ai_model_config or {}
        current_config.update(config)
        self.ai_model_config = current_config
        db.session.commit()
    
    @classmethod
    def get_by_subdomain(cls, subdomain):
        """根据子域名获取租户"""
        return cls.query.filter_by(subdomain=subdomain, is_active=True).first()
    
    @classmethod
    def get_by_domain(cls, domain):
        """根据域名获取租户"""
        return cls.query.filter_by(domain=domain, is_active=True).first()