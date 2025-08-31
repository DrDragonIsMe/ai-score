#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 配置模块 - multi_tenant.py

Description:
    多租户配置，定义租户隔离和管理配置。

Author: Chang Xinglong
Date: 2025-08-30
Version: 1.0.0
License: Apache License 2.0
"""


import os
from typing import Dict, Any, Optional, List
from enum import Enum


class TenantIsolationLevel(Enum):
    """租户隔离级别枚举"""
    SHARED_DATABASE = "shared_database"  # 共享数据库，通过tenant_id区分
    SEPARATE_SCHEMA = "separate_schema"  # 独立模式，每个租户一个schema
    SEPARATE_DATABASE = "separate_database"  # 独立数据库，每个租户一个数据库


class TenantStatus(Enum):
    """租户状态枚举"""
    ACTIVE = "active"  # 活跃
    INACTIVE = "inactive"  # 非活跃
    SUSPENDED = "suspended"  # 暂停
    TRIAL = "trial"  # 试用
    EXPIRED = "expired"  # 过期


class MultiTenantConfig:
    """多租户配置类"""
    
    # 基础配置
    MULTI_TENANT_ENABLED = os.getenv('MULTI_TENANT_ENABLED', '1') == '1'
    DEFAULT_TENANT = os.getenv('DEFAULT_TENANT', 'default')
    TENANT_HEADER = os.getenv('TENANT_HEADER', 'X-Tenant-ID')
    TENANT_QUERY_PARAM = os.getenv('TENANT_QUERY_PARAM', 'tenant')
    TENANT_SUBDOMAIN_ENABLED = os.getenv('TENANT_SUBDOMAIN_ENABLED', '0') == '1'
    
    # 隔离级别配置
    ISOLATION_LEVEL = TenantIsolationLevel(os.getenv('TENANT_ISOLATION_LEVEL', 'shared_database'))
    
    # 租户发现配置
    TENANT_DISCOVERY_METHODS = [
        'header',      # 通过HTTP头
        'subdomain',   # 通过子域名
        'query_param', # 通过查询参数
        'path_prefix'  # 通过路径前缀
    ]
    
    # 租户缓存配置
    TENANT_CACHE_ENABLED = os.getenv('TENANT_CACHE_ENABLED', '1') == '1'
    TENANT_CACHE_TTL = int(os.getenv('TENANT_CACHE_TTL', 3600))  # 1小时
    TENANT_CACHE_PREFIX = 'tenant:'
    
    # 租户限制配置
    MAX_TENANTS = int(os.getenv('MAX_TENANTS', 1000))
    MAX_USERS_PER_TENANT = int(os.getenv('MAX_USERS_PER_TENANT', 10000))
    MAX_STORAGE_PER_TENANT = int(os.getenv('MAX_STORAGE_PER_TENANT', 1024 * 1024 * 1024))  # 1GB
    MAX_API_CALLS_PER_TENANT = int(os.getenv('MAX_API_CALLS_PER_TENANT', 100000))  # 每月
    
    # 租户数据库配置
    TENANT_DB_PREFIX = os.getenv('TENANT_DB_PREFIX', 'tenant_')
    TENANT_SCHEMA_PREFIX = os.getenv('TENANT_SCHEMA_PREFIX', 'tenant_')
    
    # 租户文件存储配置
    TENANT_STORAGE_ISOLATION = os.getenv('TENANT_STORAGE_ISOLATION', '1') == '1'
    TENANT_STORAGE_PREFIX = os.getenv('TENANT_STORAGE_PREFIX', 'tenant')
    
    # 租户功能配置
    TENANT_FEATURES = {
        'ai_models': True,
        'advanced_analytics': False,
        'custom_branding': False,
        'api_access': True,
        'export_data': True,
        'backup_restore': False,
        'sso_integration': False,
        'custom_domains': False
    }
    
    # 租户计费配置
    BILLING_ENABLED = os.getenv('BILLING_ENABLED', '0') == '1'
    BILLING_CURRENCY = os.getenv('BILLING_CURRENCY', 'CNY')
    BILLING_CYCLE = os.getenv('BILLING_CYCLE', 'monthly')  # monthly, yearly
    
    @staticmethod
    def get_tenant_config(tenant_id: str) -> Dict[str, Any]:
        """获取租户配置
        
        Args:
            tenant_id: 租户ID
            
        Returns:
            dict: 租户配置字典
        """
        # 这里可以从数据库或配置文件中获取租户特定配置
        # 目前返回默认配置
        return {
            'tenant_id': tenant_id,
            'status': TenantStatus.ACTIVE.value,
            'isolation_level': MultiTenantConfig.ISOLATION_LEVEL.value,
            'features': MultiTenantConfig.TENANT_FEATURES.copy(),
            'limits': {
                'max_users': MultiTenantConfig.MAX_USERS_PER_TENANT,
                'max_storage': MultiTenantConfig.MAX_STORAGE_PER_TENANT,
                'max_api_calls': MultiTenantConfig.MAX_API_CALLS_PER_TENANT
            },
            'database': {
                'prefix': MultiTenantConfig.TENANT_DB_PREFIX,
                'schema_prefix': MultiTenantConfig.TENANT_SCHEMA_PREFIX
            },
            'storage': {
                'isolation': MultiTenantConfig.TENANT_STORAGE_ISOLATION,
                'prefix': MultiTenantConfig.TENANT_STORAGE_PREFIX
            },
            'billing': {
                'enabled': MultiTenantConfig.BILLING_ENABLED,
                'currency': MultiTenantConfig.BILLING_CURRENCY,
                'cycle': MultiTenantConfig.BILLING_CYCLE
            }
        }
    
    @staticmethod
    def get_database_name(tenant_id: str) -> str:
        """获取租户数据库名称
        
        Args:
            tenant_id: 租户ID
            
        Returns:
            str: 数据库名称
        """
        if MultiTenantConfig.ISOLATION_LEVEL == TenantIsolationLevel.SEPARATE_DATABASE:
            return f"{MultiTenantConfig.TENANT_DB_PREFIX}{tenant_id}"
        else:
            # 共享数据库或独立模式使用默认数据库名
            return os.getenv('DB_NAME', 'ai_score')
    
    @staticmethod
    def get_schema_name(tenant_id: str) -> Optional[str]:
        """获取租户模式名称
        
        Args:
            tenant_id: 租户ID
            
        Returns:
            str: 模式名称，如果不使用独立模式则返回None
        """
        if MultiTenantConfig.ISOLATION_LEVEL == TenantIsolationLevel.SEPARATE_SCHEMA:
            return f"{MultiTenantConfig.TENANT_SCHEMA_PREFIX}{tenant_id}"
        return None
    
    @staticmethod
    def get_storage_path(tenant_id: str, path: str = '') -> str:
        """获取租户存储路径
        
        Args:
            tenant_id: 租户ID
            path: 相对路径
            
        Returns:
            str: 完整存储路径
        """
        if MultiTenantConfig.TENANT_STORAGE_ISOLATION:
            base_path = f"{MultiTenantConfig.TENANT_STORAGE_PREFIX}/{tenant_id}"
            return f"{base_path}/{path}" if path else base_path
        else:
            return path
    
    @staticmethod
    def extract_tenant_from_request(request) -> Optional[str]:
        """从请求中提取租户ID
        
        Args:
            request: Flask请求对象
            
        Returns:
            str: 租户ID，如果未找到则返回None
        """
        tenant_id = None
        
        # 方法1: 从HTTP头中获取
        if 'header' in MultiTenantConfig.TENANT_DISCOVERY_METHODS:
            tenant_id = request.headers.get(MultiTenantConfig.TENANT_HEADER)
            if tenant_id:
                return tenant_id
        
        # 方法2: 从子域名中获取
        if 'subdomain' in MultiTenantConfig.TENANT_DISCOVERY_METHODS and MultiTenantConfig.TENANT_SUBDOMAIN_ENABLED:
            host = request.headers.get('Host', '')
            if '.' in host:
                subdomain = host.split('.')[0]
                if subdomain and subdomain != 'www':
                    return subdomain
        
        # 方法3: 从查询参数中获取
        if 'query_param' in MultiTenantConfig.TENANT_DISCOVERY_METHODS:
            tenant_id = request.args.get(MultiTenantConfig.TENANT_QUERY_PARAM)
            if tenant_id:
                return tenant_id
        
        # 方法4: 从路径前缀中获取
        if 'path_prefix' in MultiTenantConfig.TENANT_DISCOVERY_METHODS:
            path_parts = request.path.strip('/').split('/')
            if len(path_parts) > 1 and path_parts[0] == 'tenant':
                return path_parts[1]
        
        # 如果都没找到，返回默认租户
        return MultiTenantConfig.DEFAULT_TENANT
    
    @staticmethod
    def is_tenant_feature_enabled(tenant_id: str, feature: str) -> bool:
        """检查租户功能是否启用
        
        Args:
            tenant_id: 租户ID
            feature: 功能名称
            
        Returns:
            bool: 功能是否启用
        """
        tenant_config = MultiTenantConfig.get_tenant_config(tenant_id)
        return tenant_config.get('features', {}).get(feature, False)
    
    @staticmethod
    def get_tenant_limits(tenant_id: str) -> Dict[str, int]:
        """获取租户限制
        
        Args:
            tenant_id: 租户ID
            
        Returns:
            dict: 租户限制字典
        """
        tenant_config = MultiTenantConfig.get_tenant_config(tenant_id)
        return tenant_config.get('limits', {})
    
    @staticmethod
    def validate_tenant_access(tenant_id: str, user_id: str = None) -> bool:
        """验证租户访问权限
        
        Args:
            tenant_id: 租户ID
            user_id: 用户ID（可选）
            
        Returns:
            bool: 是否有访问权限
        """
        # 检查租户是否存在且状态正常
        tenant_config = MultiTenantConfig.get_tenant_config(tenant_id)
        status = tenant_config.get('status')
        
        if status in [TenantStatus.SUSPENDED.value, TenantStatus.EXPIRED.value]:
            return False
        
        # 如果提供了用户ID，可以进一步检查用户是否属于该租户
        # 这里需要查询数据库，暂时返回True
        return True
    
    @staticmethod
    def get_tenant_database_uri(tenant_id: str, base_uri: str) -> str:
        """获取租户数据库连接URI
        
        Args:
            tenant_id: 租户ID
            base_uri: 基础数据库URI
            
        Returns:
            str: 租户数据库URI
        """
        if MultiTenantConfig.ISOLATION_LEVEL == TenantIsolationLevel.SEPARATE_DATABASE:
            # 替换数据库名
            db_name = MultiTenantConfig.get_database_name(tenant_id)
            # 简单的URI替换，实际应用中可能需要更复杂的解析
            if '/' in base_uri:
                parts = base_uri.rsplit('/', 1)
                if '?' in parts[1]:
                    db_part, query_part = parts[1].split('?', 1)
                    return f"{parts[0]}/{db_name}?{query_part}"
                else:
                    return f"{parts[0]}/{db_name}"
        
        return base_uri


class TenantContext:
    """租户上下文管理器"""
    
    def __init__(self):
        self._current_tenant = None
        self._tenant_config = None
    
    def set_current_tenant(self, tenant_id: str):
        """设置当前租户
        
        Args:
            tenant_id: 租户ID
        """
        self._current_tenant = tenant_id
        self._tenant_config = MultiTenantConfig.get_tenant_config(tenant_id)
    
    def get_current_tenant(self) -> Optional[str]:
        """获取当前租户ID
        
        Returns:
            str: 当前租户ID
        """
        return self._current_tenant
    
    def get_current_tenant_config(self) -> Optional[Dict[str, Any]]:
        """获取当前租户配置
        
        Returns:
            dict: 当前租户配置
        """
        return self._tenant_config
    
    def clear(self):
        """清除租户上下文"""
        self._current_tenant = None
        self._tenant_config = None
    
    def is_feature_enabled(self, feature: str) -> bool:
        """检查当前租户功能是否启用
        
        Args:
            feature: 功能名称
            
        Returns:
            bool: 功能是否启用
        """
        if not self._current_tenant:
            return False
        return MultiTenantConfig.is_tenant_feature_enabled(self._current_tenant, feature)
    
    def get_limits(self) -> Dict[str, int]:
        """获取当前租户限制
        
        Returns:
            dict: 租户限制字典
        """
        if not self._current_tenant:
            return {}
        return MultiTenantConfig.get_tenant_limits(self._current_tenant)


# 全局租户上下文实例
tenant_context = TenantContext()


def get_current_tenant() -> Optional[str]:
    """获取当前租户ID
    
    Returns:
        str: 当前租户ID
    """
    return tenant_context.get_current_tenant()


def get_current_tenant_config() -> Optional[Dict[str, Any]]:
    """获取当前租户配置
    
    Returns:
        dict: 当前租户配置
    """
    return tenant_context.get_current_tenant_config()


def set_current_tenant(tenant_id: str):
    """设置当前租户
    
    Args:
        tenant_id: 租户ID
    """
    tenant_context.set_current_tenant(tenant_id)


def is_multi_tenant_enabled() -> bool:
    """检查是否启用多租户
    
    Returns:
        bool: 是否启用多租户
    """
    return MultiTenantConfig.MULTI_TENANT_ENABLED