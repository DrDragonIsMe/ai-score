# -*- coding: utf-8 -*-
"""
装饰器工具
"""

from functools import wraps
from flask import request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.user import User
from models.tenant import Tenant
from utils.response import error_response

def admin_required(f):
    """
    管理员权限装饰器
    
    Args:
        f: 被装饰的函数
        
    Returns:
        function: 装饰后的函数
    """
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        try:
            # 获取当前用户
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return error_response("用户不存在", 401)
            
            # 检查是否是管理员
            if not user.is_admin:
                return error_response("需要管理员权限", 403)
            
            # 将用户信息添加到全局变量
            g.current_user = user
            
            return f(*args, **kwargs)
        except Exception as e:
            return error_response(f"权限验证失败: {str(e)}", 500)
    
    return decorated_function

def tenant_required(f):
    """
    租户权限装饰器
    
    Args:
        f: 被装饰的函数
        
    Returns:
        function: 装饰后的函数
    """
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        try:
            # 获取当前用户
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return error_response("用户不存在", 401)
            
            # 获取租户信息
            tenant = Tenant.query.get(user.tenant_id)
            if not tenant:
                return error_response("租户不存在", 401)
            
            # 检查租户状态
            if not tenant.is_active:
                return error_response("租户已被禁用", 403)
            
            # 将用户和租户信息添加到全局变量
            g.current_user = user
            g.current_tenant = tenant
            
            return f(*args, **kwargs)
        except Exception as e:
            return error_response(f"租户验证失败: {str(e)}", 500)
    
    return decorated_function

def role_required(*roles):
    """
    角色权限装饰器
    
    Args:
        *roles: 允许的角色列表
        
    Returns:
        function: 装饰器函数
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            try:
                # 获取当前用户
                current_user_id = get_jwt_identity()
                user = User.query.get(current_user_id)
                
                if not user:
                    return error_response("用户不存在", 401)
                
                # 检查用户角色
                if user.role not in roles:
                    return error_response(f"需要以下角色之一: {', '.join(roles)}", 403)
                
                # 将用户信息添加到全局变量
                g.current_user = user
                
                return f(*args, **kwargs)
            except Exception as e:
                return error_response(f"角色验证失败: {str(e)}", 500)
        
        return decorated_function
    return decorator

def validate_json(f):
    """
    JSON数据验证装饰器
    
    Args:
        f: 被装饰的函数
        
    Returns:
        function: 装饰后的函数
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return error_response("请求必须是JSON格式", 400)
        
        try:
            data = request.get_json()
            if data is None:
                return error_response("无效的JSON数据", 400)
            
            # 将数据添加到全局变量
            g.json_data = data
            
            return f(*args, **kwargs)
        except Exception as e:
            return error_response(f"JSON解析错误: {str(e)}", 400)
    
    return decorated_function

def rate_limit(max_requests=100, per_seconds=3600):
    """
    速率限制装饰器
    
    Args:
        max_requests: 最大请求数
        per_seconds: 时间窗口（秒）
        
    Returns:
        function: 装饰器函数
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 这里可以实现基于Redis的速率限制
            # 暂时跳过实现，直接调用原函数
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def cache_response(timeout=300):
    """
    响应缓存装饰器
    
    Args:
        timeout: 缓存超时时间（秒）
        
    Returns:
        function: 装饰器函数
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 这里可以实现基于Redis的响应缓存
            # 暂时跳过实现，直接调用原函数
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator