#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 工具模块 - response.py

Description:
    响应工具，提供统一的API响应格式处理。

Author: Chang Xinglong
Date: 2025-08-31
Version: 1.0.0
License: Apache License 2.0
"""


from flask import jsonify
from typing import Any, Dict, Optional

def success_response(data: Any = None, message: str = "操作成功", code: int = 200) -> Dict:
    """
    成功响应
    
    Args:
        data: 响应数据
        message: 响应消息
        code: 状态码
        
    Returns:
        Dict: 响应字典
    """
    response = {
        "success": True,
        "code": code,
        "message": message
    }
    
    if data is not None:
        response["data"] = data
    
    return jsonify(response), code

def error_response(message: str = "操作失败", code: int = 400, error_code: Optional[str] = None) -> Dict:
    """
    错误响应
    
    Args:
        message: 错误消息
        code: HTTP状态码
        error_code: 业务错误码
        
    Returns:
        Dict: 响应字典
    """
    response = {
        "success": False,
        "code": code,
        "message": message
    }
    
    if error_code:
        response["error_code"] = error_code
    
    return jsonify(response), code

def paginated_response(data: list, total: int, page: int, per_page: int, message: str = "获取成功") -> Dict:
    """
    分页响应
    
    Args:
        data: 数据列表
        total: 总数量
        page: 当前页码
        per_page: 每页数量
        message: 响应消息
        
    Returns:
        Dict: 响应字典
    """
    total_pages = (total + per_page - 1) // per_page
    
    response_data = {
        "items": data,
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages
        }
    }
    
    return success_response(response_data, message)