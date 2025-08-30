# -*- coding: utf-8 -*-
"""
数据库工具
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