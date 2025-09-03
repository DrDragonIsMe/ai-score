#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app
from models.ai_model import AIModelConfig
from utils.database import db

def check_ai_models():
    app = create_app()
    with app.app_context():
        try:
            models = AIModelConfig.query.all()
            print(f'找到 {len(models)} 个AI模型配置:')
            
            if models:
                for m in models:
                    print(f'- {m.model_name} ({m.model_type}) - 激活: {m.is_active}, 默认: {m.is_default}')
                    print(f'  API密钥: {m.api_key[:10] if m.api_key else "未设置"}...')
                    print(f'  API URL: {m.api_base_url}')
                    print()
            else:
                print('数据库中没有AI模型配置')
                
        except Exception as e:
            print(f'查询失败: {str(e)}')

if __name__ == '__main__':
    check_ai_models()