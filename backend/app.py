#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 主应用入口文件

Description:
    Flask应用的主入口文件，负责应用初始化、配置加载、
    蓝图注册和中间件设置等核心功能。

Author: Chang Xinglong
Date: 2025-08-30
Version: 1.0.0
License: Apache License 2.0
"""

from flask import Flask, request, g
from flask_babel import Babel
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from utils.database import db, migrate
import os

# 导入所有模型以确保表被创建
from models import (
    Tenant, User, UserProfile, Subject, Chapter, KnowledgePoint, SubKnowledgePoint,
    Question, QuestionType, ExamPaper, LearningPath, StudyRecord, MemoryCard,
    DiagnosisReport, WeaknessPoint, LearningProfile, AIModelConfig,
    MistakeRecord, TutoringSession, ExamSession, TimeAllocation, ScoringStrategy,
    ExamAnalytics, LearningMetric, PerformanceSnapshot, LearningReport,
    GoalTracking, FeedbackRecord, ExamKnowledgeMapping, ExamKnowledgeStatistics,
    PPTTemplate
)

# 创建扩展实例
babel = Babel()
jwt = JWTManager()

def create_app(config_class=Config):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    babel.init_app(app)
    jwt.init_app(app)
    CORS(app)
    
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    # 多租户中间件
    @app.before_request
    def load_tenant():
        """根据JWT token或域名加载租户信息"""
        from flask_jwt_extended import get_jwt_identity, jwt_required
        
        # 优先从JWT token中获取tenant_id
        try:
            current_user_info = get_jwt_identity()
            if current_user_info and isinstance(current_user_info, dict):
                tenant_id = current_user_info.get('tenant_id')
                if tenant_id:
                    g.tenant_id = tenant_id
                    return
        except:
            pass
        
        # 如果JWT中没有tenant_id，则从域名中提取
        host = request.headers.get('Host', 'localhost')
        tenant_id = extract_tenant_from_host(host)
        g.tenant_id = tenant_id
    
    # 国际化支持
    def get_locale():
        """选择语言"""
        # 优先级：URL参数 > 用户设置 > Accept-Language > 默认
        if request.args.get('lang'):
            return request.args.get('lang')
        return request.accept_languages.best_match(['zh', 'en', 'ja', 'ko']) or 'zh'
    
    babel.init_app(app, locale_selector=get_locale)
    
    # JWT错误处理器
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        print(f"JWT过期错误: {jwt_payload}")  # 调试日志
        return {'error': 'Token has expired'}, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        # 获取Authorization头部进行调试
        auth_header = request.headers.get('Authorization', '')
        print(f"JWT无效错误: {error}")  # 调试日志
        print(f"Authorization头部: '{auth_header}'")  # 调试日志
        return {'error': 'Invalid token'}, 422
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        print(f"JWT缺失错误: {error}")  # 调试日志
        return {'error': 'Authorization token is required'}, 401
    
    # 错误处理器
    @app.errorhandler(Exception)
    def handle_exception(e):
        import traceback
        print(f"未处理的异常: {str(e)}")
        print(f"错误堆栈: {traceback.format_exc()}")
        return {'error': str(e), 'traceback': traceback.format_exc()}, 500
    
    # 注册蓝图
    from api import api_bp
    from api.subject_initializer import subject_initializer_bp
    from api.settings import settings_bp
    from api.document import document_bp
    from api.ppt_template import ppt_template_bp
    from routes.learning_analytics import learning_analytics_bp
    from routes.advanced_analytics import advanced_analytics_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(subject_initializer_bp)
    app.register_blueprint(settings_bp, url_prefix='/api')
    app.register_blueprint(document_bp)
    app.register_blueprint(ppt_template_bp)
    app.register_blueprint(learning_analytics_bp)
    app.register_blueprint(advanced_analytics_bp)
    
    return app

def extract_tenant_from_host(host):
    """从主机名提取租户ID"""
    # 示例：tenant1.aiscore.com -> tenant1
    if '.' in host and not host.startswith('localhost'):
        return host.split('.')[0]
    return 'default'

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5001)