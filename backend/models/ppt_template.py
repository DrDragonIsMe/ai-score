#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 数据模型 - ppt_template.py

Description:
    PPT模板数据模型，用于管理PPT模板的存储和配置。

Author: Chang Xinglong
Date: 2025-08-31
Version: 1.0.0
License: Apache License 2.0
"""

from datetime import datetime
from utils.database import db
import uuid

class PPTTemplate(db.Model):
    """
    PPT模板模型
    """
    __tablename__ = 'ppt_templates'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 基本信息
    name = db.Column(db.String(100), nullable=False, comment='模板名称')
    description = db.Column(db.Text, comment='模板描述')
    category = db.Column(db.String(50), default='general', comment='模板分类')
    
    # 模板文件信息
    template_file_path = db.Column(db.String(500), comment='模板文件路径')
    preview_image_path = db.Column(db.String(500), comment='预览图片路径')
    file_size = db.Column(db.Integer, comment='文件大小（字节）')
    
    # 模板配置
    config = db.Column(db.JSON, comment='模板配置信息（字体、颜色、布局等）')
    
    # 状态信息
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    is_default = db.Column(db.Boolean, default=False, comment='是否为默认模板')
    is_system = db.Column(db.Boolean, default=False, comment='是否为系统模板')
    
    # 使用统计
    usage_count = db.Column(db.Integer, default=0, comment='使用次数')
    
    # 创建者信息
    created_by = db.Column(db.String(50), comment='创建者ID')
    tenant_id = db.Column(db.String(50), default='default', comment='租户ID')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PPTTemplate {self.name}>'
    
    def to_dict(self):
        """
        转换为字典格式
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'template_file_path': self.template_file_path,
            'preview_image_path': self.preview_image_path,
            'file_size': self.file_size,
            'config': self.config,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'is_system': self.is_system,
            'usage_count': self.usage_count,
            'created_by': self.created_by,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_active_templates(cls, tenant_id='default', category=None):
        """
        获取活跃的模板列表
        """
        query = cls.query.filter_by(is_active=True, tenant_id=tenant_id)
        if category:
            query = query.filter_by(category=category)
        return query.order_by(cls.is_default.desc(), cls.usage_count.desc(), cls.created_at.desc()).all()  # type: ignore
    
    @classmethod
    def get_default_template(cls, tenant_id='default'):
        """
        获取默认模板
        """
        return cls.query.filter_by(is_default=True, is_active=True, tenant_id=tenant_id).first()
    
    def increment_usage(self):
        """
        增加使用次数
        """
        self.usage_count = (self.usage_count or 0) + 1
        db.session.commit()