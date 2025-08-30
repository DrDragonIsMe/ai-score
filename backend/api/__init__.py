#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - API接口 - __init__.py

Description:
    api模块初始化文件，定义模块导出接口和初始化逻辑。

Author: Chang Xinglong
Date: 2025-01-20
Version: 1.0.0
License: Apache License 2.0
"""


from flask import Blueprint

api_bp = Blueprint('api', __name__)

# 导入所有路由
from . import auth, users, subjects, learning, diagnosis, mistakes, exam

# 注册子蓝图
from .mistakes import mistakes_bp
api_bp.register_blueprint(mistakes_bp)
from .exam import exam_bp
api_bp.register_blueprint(exam_bp)
from .tracking import tracking_bp
api_bp.register_blueprint(tracking_bp)