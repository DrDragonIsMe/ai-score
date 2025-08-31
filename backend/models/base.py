#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 数据模型 - base.py

Description:
    数据模型基类，定义通用字段和方法。

Author: Chang Xinglong
Date: 2025-08-30
Version: 1.0.0
License: Apache License 2.0
"""


from datetime import datetime
from utils.database import db
from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.ext.declarative import declared_attr

class BaseModel(db.Model):
    """
    基础模型类，包含通用字段和方法
    """
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    @declared_attr
    def __tablename__(cls):
        """
        自动生成表名
        """
        return cls.__name__.lower()
    
    def save(self):
        """
        保存到数据库
        """
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    def delete(self):
        """
        从数据库删除
        """
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    def update(self, **kwargs):
        """
        更新字段
        
        Args:
            **kwargs: 要更新的字段
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    def to_dict(self):
        """
        转换为字典
        
        Returns:
            dict: 模型字典表示
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
    
    @classmethod
    def get_by_id(cls, id):
        """
        根据ID获取记录
        
        Args:
            id: 记录ID
            
        Returns:
            BaseModel: 模型实例或None
        """
        return cls.query.get(id)
    
    @classmethod
    def get_all(cls):
        """
        获取所有记录
        
        Returns:
            list: 模型实例列表
        """
        return cls.query.all()
    
    @classmethod
    def paginate(cls, page=1, per_page=20, **filters):
        """
        分页查询
        
        Args:
            page: 页码
            per_page: 每页数量
            **filters: 过滤条件
            
        Returns:
            Pagination: 分页对象
        """
        query = cls.query
        
        # 应用过滤条件
        for key, value in filters.items():
            if hasattr(cls, key) and value is not None:
                query = query.filter(getattr(cls, key) == value)
        
        return query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"