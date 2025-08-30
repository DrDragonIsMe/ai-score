#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 工具模块 - validators.py

Description:
    数据验证工具，提供各种数据格式和业务规则验证。

Author: Chang Xinglong
Date: 2025-01-20
Version: 1.0.0
License: Apache License 2.0
"""


import re
from typing import Any, Dict, List, Optional
from flask import request

def validate_email(email: str) -> bool:
    """
    验证邮箱格式
    
    Args:
        email: 邮箱地址
        
    Returns:
        bool: 是否有效
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password(password: str) -> tuple[bool, str]:
    """
    验证密码强度
    
    Args:
        password: 密码
        
    Returns:
        tuple: (是否有效, 错误信息)
    """
    if not password:
        return False, "密码不能为空"
    
    if len(password) < 6:
        return False, "密码长度至少6位"
    
    if len(password) > 128:
        return False, "密码长度不能超过128位"
    
    # 检查是否包含字母和数字
    has_letter = bool(re.search(r'[a-zA-Z]', password))
    has_digit = bool(re.search(r'\d', password))
    
    if not (has_letter and has_digit):
        return False, "密码必须包含字母和数字"
    
    return True, ""

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> tuple[bool, str]:
    """
    验证必填字段
    
    Args:
        data: 数据字典
        required_fields: 必填字段列表
        
    Returns:
        tuple: (是否有效, 错误信息)
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            missing_fields.append(field)
    
    if missing_fields:
        return False, f"缺少必填字段: {', '.join(missing_fields)}"
    
    return True, ""

def validate_enum_field(value: Any, enum_class, field_name: str = "字段") -> tuple[bool, str]:
    """
    验证枚举字段
    
    Args:
        value: 要验证的值
        enum_class: 枚举类
        field_name: 字段名称
        
    Returns:
        tuple: (是否有效, 错误信息)
    """
    try:
        if isinstance(value, str):
            enum_class(value)
        elif hasattr(enum_class, value):
            pass
        else:
            valid_values = [e.value for e in enum_class]
            return False, f"{field_name}值无效，有效值为: {', '.join(valid_values)}"
        return True, ""
    except ValueError:
        valid_values = [e.value for e in enum_class]
        return False, f"{field_name}值无效，有效值为: {', '.join(valid_values)}"

def validate_phone(phone: str) -> bool:
    """
    验证手机号格式
    
    Args:
        phone: 手机号
        
    Returns:
        bool: 是否有效
    """
    if not phone:
        return False
    
    # 中国手机号格式
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))

def validate_id_card(id_card: str) -> bool:
    """
    验证身份证号格式
    
    Args:
        id_card: 身份证号
        
    Returns:
        bool: 是否有效
    """
    if not id_card:
        return False
    
    # 18位身份证号格式
    pattern = r'^[1-9]\d{5}(18|19|20)\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$'
    return bool(re.match(pattern, id_card))

def validate_json_request() -> tuple[bool, Dict[str, Any], str]:
    """
    验证JSON请求
    
    Returns:
        tuple: (是否有效, 数据, 错误信息)
    """
    try:
        if not request.is_json:
            return False, {}, "请求必须是JSON格式"
        
        data = request.get_json()
        if data is None:
            return False, {}, "无效的JSON数据"
        
        return True, data, ""
    except Exception as e:
        return False, {}, f"JSON解析错误: {str(e)}"

def validate_pagination_params(page: Any = None, per_page: Any = None) -> tuple[int, int, str]:
    """
    验证分页参数
    
    Args:
        page: 页码
        per_page: 每页数量
        
    Returns:
        tuple: (页码, 每页数量, 错误信息)
    """
    try:
        # 默认值
        page = int(page) if page else 1
        per_page = int(per_page) if per_page else 20
        
        # 验证范围
        if page < 1:
            return 1, 20, "页码必须大于0"
        
        if per_page < 1 or per_page > 100:
            return page, 20, "每页数量必须在1-100之间"
        
        return page, per_page, ""
    except (ValueError, TypeError):
        return 1, 20, "分页参数必须是数字"