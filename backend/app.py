# -*- coding: utf-8 -*-
"""
AI Score - 高中生提分系统
主应用入口文件
"""

from flask import Flask, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_babel import Babel
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
import os

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()
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
    
    # 多租户中间件
    @app.before_request
    def load_tenant():
        """根据域名加载租户信息"""
        host = request.headers.get('Host', 'localhost')
        # 从域名中提取租户标识
        tenant_id = extract_tenant_from_host(host)
        g.tenant_id = tenant_id
    
    # 国际化支持
    @babel.localeselector
    def get_locale():
        """选择语言"""
        # 优先级：URL参数 > 用户设置 > Accept-Language > 默认
        if request.args.get('lang'):
            return request.args.get('lang')
        return request.accept_languages.best_match(['zh', 'en', 'ja', 'ko']) or 'zh'
    
    # 注册蓝图
    from api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app

def extract_tenant_from_host(host):
    """从主机名提取租户ID"""
    # 示例：tenant1.aiscore.com -> tenant1
    if '.' in host and not host.startswith('localhost'):
        return host.split('.')[0]
    return 'default'

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)