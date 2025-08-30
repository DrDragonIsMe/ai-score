# -*- coding: utf-8 -*-
"""
AI模型配置模型
"""

from datetime import datetime
from utils.database import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class AIModelConfig(db.Model):
    """AI模型配置模型"""
    
    __tablename__ = 'ai_model_configs'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tenants.id'), nullable=False)
    
    # 模型基本信息
    model_name = db.Column(db.String(50), nullable=False, comment='模型名称')
    model_type = db.Column(db.String(20), nullable=False, comment='模型类型：doubao/openai/claude/custom')
    model_id = db.Column(db.String(100), nullable=False, comment='模型ID')
    
    # API配置
    api_key = db.Column(db.String(200), comment='API密钥')
    api_base_url = db.Column(db.String(200), comment='API基础URL')
    api_version = db.Column(db.String(20), comment='API版本')
    
    # 模型参数
    max_tokens = db.Column(db.Integer, default=2000, comment='最大令牌数')
    temperature = db.Column(db.Float, default=0.7, comment='温度参数')
    top_p = db.Column(db.Float, default=0.9, comment='Top-p参数')
    frequency_penalty = db.Column(db.Float, default=0.0, comment='频率惩罚')
    presence_penalty = db.Column(db.Float, default=0.0, comment='存在惩罚')
    
    # 功能配置
    supported_features = db.Column(db.JSON, default=[], comment='支持的功能列表')
    use_cases = db.Column(db.JSON, default=[], comment='使用场景')
    
    # 性能配置
    rate_limit = db.Column(db.Integer, comment='速率限制(请求/分钟)')
    timeout = db.Column(db.Integer, default=30, comment='超时时间(秒)')
    retry_count = db.Column(db.Integer, default=3, comment='重试次数')
    
    # 成本配置
    cost_per_1k_tokens = db.Column(db.Float, comment='每1K令牌成本')
    monthly_quota = db.Column(db.Integer, comment='月度配额')
    current_usage = db.Column(db.Integer, default=0, comment='当前使用量')
    
    # 状态
    is_active = db.Column(db.Boolean, default=True, comment='是否激活')
    is_default = db.Column(db.Boolean, default=False, comment='是否默认模型')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<AIModelConfig {self.model_name}>'
    
    def get_api_config(self):
        """获取API配置"""
        return {
            'api_key': self.api_key,
            'base_url': self.api_base_url,
            'model_id': self.model_id,
            'api_version': self.api_version,
            'timeout': self.timeout,
            'max_retries': self.retry_count
        }
    
    def get_model_params(self):
        """获取模型参数"""
        return {
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'frequency_penalty': self.frequency_penalty,
            'presence_penalty': self.presence_penalty
        }
    
    def check_quota(self, tokens_needed):
        """检查配额是否足够"""
        if not self.monthly_quota:
            return True
        return (self.current_usage + tokens_needed) <= self.monthly_quota
    
    def update_usage(self, tokens_used):
        """更新使用量"""
        self.current_usage += tokens_used
        db.session.commit()
    
    def reset_monthly_usage(self):
        """重置月度使用量"""
        self.current_usage = 0
        db.session.commit()
    
    def to_dict(self, include_sensitive=False):
        data = {
            'id': str(self.id),
            'model_name': self.model_name,
            'model_type': self.model_type,
            'model_id': self.model_id,
            'api_base_url': self.api_base_url,
            'api_version': self.api_version,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'frequency_penalty': self.frequency_penalty,
            'presence_penalty': self.presence_penalty,
            'supported_features': self.supported_features,
            'use_cases': self.use_cases,
            'rate_limit': self.rate_limit,
            'timeout': self.timeout,
            'retry_count': self.retry_count,
            'cost_per_1k_tokens': self.cost_per_1k_tokens,
            'monthly_quota': self.monthly_quota,
            'current_usage': self.current_usage,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            data['api_key'] = self.api_key
        
        return data
    
    @classmethod
    def get_default_model(cls, tenant_id):
        """获取默认模型"""
        return cls.query.filter_by(
            tenant_id=tenant_id,
            is_default=True,
            is_active=True
        ).first()
    
    @classmethod
    def get_available_models(cls, tenant_id):
        """获取可用模型列表"""
        return cls.query.filter_by(
            tenant_id=tenant_id,
            is_active=True
        ).order_by(cls.is_default.desc(), cls.model_name).all()