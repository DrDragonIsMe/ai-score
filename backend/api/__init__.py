# -*- coding: utf-8 -*-
"""
API蓝图
"""

from flask import Blueprint

api_bp = Blueprint('api', __name__)

# 导入所有路由
from . import auth, users, subjects, knowledge, questions, learning, diagnosis, ai_models, admin, memory, mistakes, exam

# 注册子蓝图
from .mistakes import mistakes_bp
api_bp.register_blueprint(mistakes_bp)
from .exam import exam_bp
api_bp.register_blueprint(exam_bp)
from .tracking import tracking_bp
api_bp.register_blueprint(tracking_bp)