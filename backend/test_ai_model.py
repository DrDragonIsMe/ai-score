#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app
from services.llm_service import LLMService
from models.ai_model import AIModelConfig
from utils.database import db

def test_ai_model():
    app = create_app()
    with app.app_context():
        try:
            # 检查AI模型配置
            models = AIModelConfig.query.all()
            print(f'数据库中有 {len(models)} 个AI模型配置:')
            
            for model in models:
                print(f'- {model.model_name} ({model.model_type})')
                print(f'  激活: {model.is_active}, 默认: {model.is_default}')
                print(f'  API URL: {model.api_base_url}')
                print()
            
            # 测试LLM服务
            print('测试LLM服务...')
            llm_service = LLMService()
            llm_service._ensure_initialized()
            
            # 获取默认模型
            if llm_service.default_model:
                print(f'默认模型: {llm_service.default_model.model_name}')
                
                # 测试简单的API调用
                try:
                    response = llm_service.generate_text(
                        prompt="你好，请回复'测试成功'",
                        max_tokens=50
                    )
                    print(f'API测试结果: {response}')
                    print('AI模型配置成功！')
                except Exception as api_error:
                    print(f'API调用失败: {str(api_error)}')
            else:
                print('未找到默认模型')
                
        except Exception as e:
            print(f'测试失败: {str(e)}')
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_ai_model()