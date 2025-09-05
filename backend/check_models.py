from app import create_app
from models.ai_model import AIModelConfig
from services.llm_service import llm_service

app = create_app()
with app.app_context():
    # 检查数据库中的模型
    models = AIModelConfig.query.filter_by(is_default=True).all()
    print(f'Default models in DB: {len(models)}')
    for m in models:
        print(f'  Model: {m.model_name}, Type: {m.model_type}, API Base: {m.api_base_url}, Default: {m.is_default}')
        print(f'  Model ID (deployment): {m.model_id}')
        print(f'  API Key: {m.api_key[:10] if m.api_key else "None"}...')
        print(f'  Tenant ID: {m.tenant_id}')
        print(f'  Active: {m.is_active}')
    
    # 检查LLM服务的状态
    print('\nLLM Service Status:')
    print(f'  Initialized: {llm_service._initialized}')
    
    # 强制初始化LLM服务
    llm_service._ensure_initialized()
    print(f'  After init - Initialized: {llm_service._initialized}')
    
    if llm_service.default_model:
        print(f'  Default model: {llm_service.default_model.model_name}')
        print(f'  Model type: {getattr(llm_service.default_model, "model_type", "Unknown")}')
        print(f'  API URL: {getattr(llm_service.default_model, "api_base_url", "Unknown")}')
        print(f'  Is fallback: {type(llm_service.default_model).__name__}')
    else:
        print('  No default model found')
    
    # 测试生成文本
    print('\nTesting text generation:')
    try:
        result = llm_service.generate_text('Hello, this is a test.')
        print(f'  Result: {result[:100]}...' if len(result) > 100 else f'  Result: {result}')
    except Exception as e:
        print(f'  Error: {str(e)}')