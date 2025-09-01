#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取管理员用户的JWT token
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import User, Tenant
from utils.database import db

def get_admin_token():
    """获取管理员用户的JWT token"""
    app = create_app()
    with app.app_context():
        try:
            # 获取默认租户
            tenant = Tenant.query.filter_by(subdomain='default').first()
            if not tenant:
                print("错误：找不到默认租户")
                return None
            
            # 获取管理员用户
            admin_user = User.query.filter_by(
                tenant_id=tenant.id,
                username='admin',
                role='admin'
            ).first()
            
            if not admin_user:
                print("错误：找不到管理员用户")
                return None
            
            # 生成JWT令牌
            access_token, refresh_token = admin_user.generate_tokens()
            
            print("管理员Token获取成功！")
            print(f"Access Token: {access_token}")
            print(f"\n用户信息:")
            print(f"用户名: {admin_user.username}")
            print(f"邮箱: {admin_user.email}")
            print(f"角色: {admin_user.role}")
            
            return access_token
            
        except Exception as e:
            print(f"获取Token失败: {str(e)}")
            return None

if __name__ == '__main__':
    get_admin_token()