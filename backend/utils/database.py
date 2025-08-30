#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 工具模块 - database.py

Description:
    数据库配置，定义数据库连接和ORM配置。

Author: Chang Xinglong
Date: 2025-01-20
Version: 1.0.0
License: Apache License 2.0
"""


from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# 创建数据库实例
db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """
    初始化数据库
    
    Args:
        app: Flask应用实例
    """
    db.init_app(app)
    migrate.init_app(app, db)
    
    # 创建所有表
    with app.app_context():
        db.create_all()

def get_db():
    """
    获取数据库实例
    
    Returns:
        SQLAlchemy: 数据库实例
    """
    return db