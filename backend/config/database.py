#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 配置模块 - database.py

Description:
    数据库配置，定义数据库连接和ORM配置。

Author: Chang Xinglong
Date: 2025-08-31
Version: 1.0.0
License: Apache License 2.0
"""


import os
from urllib.parse import quote_plus


class DatabaseConfig:
    """数据库配置类"""

    # 基础配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.getenv('DB_POOL_SIZE', 10)),
        'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', 30)),
        'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', 3600)),
        'pool_pre_ping': True,
        'max_overflow': 20,
        'echo': os.getenv('SQLALCHEMY_ECHO', 'False').lower() == 'true'
    }

    @staticmethod
    def get_database_uri(env='development'):
        """获取数据库连接URI

        Args:
            env: 环境名称 (development, testing, production)

        Returns:
            str: 数据库连接URI
        """
        if env == 'testing':
            return os.getenv('TEST_DATABASE_URL', 'sqlite:///test.db')

        # 从环境变量获取数据库URL
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            return database_url

        # 构建数据库URL
        db_type = os.getenv('DB_TYPE', 'mysql')
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '3306' if db_type == 'mysql' else '5432')
        db_name = os.getenv('DB_NAME', 'ai_score')
        db_user = os.getenv('DB_USER', 'root')
        db_password = os.getenv('DB_PASSWORD', '')

        # URL编码密码中的特殊字符
        if db_password:
            db_password = quote_plus(db_password)

        if db_type == 'mysql':
            driver = os.getenv('DB_DRIVER', 'pymysql')
            return f'mysql+{driver}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4'
        elif db_type == 'postgresql':
            driver = os.getenv('DB_DRIVER', 'psycopg2')
            return f'postgresql+{driver}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
        elif db_type == 'sqlite':
            db_path = os.getenv('DB_PATH', 'ai_score.db')
            return f'sqlite:///{db_path}'
        else:
            raise ValueError(f'不支持的数据库类型: {db_type}')

    @staticmethod
    def get_redis_config():
        """获取Redis配置

        Returns:
            dict: Redis配置字典
        """
        redis_url = os.getenv('REDIS_URL')
        if redis_url:
            return {'url': redis_url}

        return {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', 6379)),
            'db': int(os.getenv('REDIS_DB', 0)),
            'password': os.getenv('REDIS_PASSWORD', None),
            'decode_responses': True,
            'socket_timeout': 5,
            'socket_connect_timeout': 5,
            'retry_on_timeout': True,
            'health_check_interval': 30
        }

    @staticmethod
    def get_cache_config():
        """获取缓存配置

        Returns:
            dict: 缓存配置字典
        """
        cache_type = os.getenv('CACHE_TYPE', 'redis')

        if cache_type == 'redis':
            redis_config = DatabaseConfig.get_redis_config()
            if 'url' in redis_config:
                return {
                    'CACHE_TYPE': 'RedisCache',
                    'CACHE_REDIS_URL': redis_config['url'],
                    'CACHE_DEFAULT_TIMEOUT': int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))
                }
            else:
                return {
                    'CACHE_TYPE': 'RedisCache',
                    'CACHE_REDIS_HOST': redis_config['host'],
                    'CACHE_REDIS_PORT': redis_config['port'],
                    'CACHE_REDIS_DB': redis_config['db'],
                    'CACHE_REDIS_PASSWORD': redis_config['password'],
                    'CACHE_DEFAULT_TIMEOUT': int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))
                }
        elif cache_type == 'simple':
            return {
                'CACHE_TYPE': 'SimpleCache',
                'CACHE_DEFAULT_TIMEOUT': int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))
            }
        elif cache_type == 'memcached':
            return {
                'CACHE_TYPE': 'MemcachedCache',
                'CACHE_MEMCACHED_SERVERS': os.getenv('MEMCACHED_SERVERS', 'localhost:11211').split(','),
                'CACHE_DEFAULT_TIMEOUT': int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))
            }
        else:
            # 默认使用简单缓存
            return {
                'CACHE_TYPE': 'SimpleCache',
                'CACHE_DEFAULT_TIMEOUT': int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))
            }


class DevelopmentDatabaseConfig(DatabaseConfig):
    """开发环境数据库配置"""

    SQLALCHEMY_DATABASE_URI = DatabaseConfig.get_database_uri('development')
    SQLALCHEMY_ENGINE_OPTIONS = {
        **DatabaseConfig.SQLALCHEMY_ENGINE_OPTIONS,
        'echo': True  # 开发环境显示SQL语句
    }


class TestingDatabaseConfig(DatabaseConfig):
    """测试环境数据库配置"""

    SQLALCHEMY_DATABASE_URI = DatabaseConfig.get_database_uri('testing')
    SQLALCHEMY_ENGINE_OPTIONS = {
        **DatabaseConfig.SQLALCHEMY_ENGINE_OPTIONS,
        'pool_size': 1,  # 测试环境使用较小的连接池
        'echo': False
    }


class ProductionDatabaseConfig(DatabaseConfig):
    """生产环境数据库配置"""

    SQLALCHEMY_DATABASE_URI = DatabaseConfig.get_database_uri('production')
    SQLALCHEMY_ENGINE_OPTIONS = {
        **DatabaseConfig.SQLALCHEMY_ENGINE_OPTIONS,
        'pool_size': int(os.getenv('DB_POOL_SIZE', 20)),  # 生产环境使用更大的连接池
        'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', 30)),
        'echo': False  # 生产环境不显示SQL语句
    }


# 配置映射
DATABASE_CONFIGS = {
    'development': DevelopmentDatabaseConfig,
    'testing': TestingDatabaseConfig,
    'production': ProductionDatabaseConfig
}


def get_database_config(env=None):
    """获取数据库配置类

    Args:
        env: 环境名称，如果为None则从环境变量获取

    Returns:
        DatabaseConfig: 数据库配置类
    """
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')

    return DATABASE_CONFIGS.get(env, DevelopmentDatabaseConfig)
