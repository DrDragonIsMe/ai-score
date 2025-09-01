#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试用户
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import User, Tenant, UserProfile
from utils.database import db

def create_test_user():
    """创建测试用户"""
    app = create_app()
    with app.app_context():
        try:
            # 获取默认租户
            tenant = Tenant.query.filter_by(subdomain='default').first()
            if not tenant:
                print("错误：找不到默认租户")
                return
            
            # 检查用户是否已存在
            existing_user = User.query.filter_by(
                tenant_id=tenant.id,
                username='testuser'
            ).first()
            
            if existing_user:
                print("测试用户已存在")
                print(f"用户名: {existing_user.username}")
                print(f"邮箱: {existing_user.email}")
                print("密码: test123")
                return
            
            # 创建测试用户
            test_user = User(
                tenant_id=tenant.id,
                username='testuser',
                email='test@example.com',
                real_name='测试用户',
                role='student'  # 普通学生角色
            )
            test_user.set_password('test123')  # 设置密码
            
            db.session.add(test_user)
            db.session.flush()
            
            # 创建用户档案
            profile = UserProfile(user_id=test_user.id)
            db.session.add(profile)
            db.session.commit()
            
            print("创建测试用户成功！")
            print("用户名: testuser")
            print("邮箱: test@example.com")
            print("密码: test123")
            
        except Exception as e:
            db.session.rollback()
            print(f"创建测试用户失败: {str(e)}")
            raise

if __name__ == '__main__':
    create_test_user()