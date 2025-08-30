# -*- coding: utf-8 -*-
"""
日志工具
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logger(app):
    """
    设置应用日志
    
    Args:
        app: Flask应用实例
    """
    if not app.debug and not app.testing:
        # 创建日志目录
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # 设置文件处理器
        file_handler = RotatingFileHandler(
            'logs/ai-score.log', 
            maxBytes=10240000, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('AI Score startup')

def get_logger(name):
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        Logger: 日志记录器实例
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        file_handler = RotatingFileHandler(
            f'logs/{name}.log',
            maxBytes=1024*1024*10,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        logger.setLevel(logging.INFO)
    
    return logger

# 创建默认logger
logger = get_logger('ai-score')