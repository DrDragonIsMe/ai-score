#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化管理员用户
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import User, Tenant, UserProfile
from utils.database import db

def init_admin():
    """初始化管理员用户"""
    app = create_app()
    with app.app_context():
        try:
            # 创建或获取默认租户
            tenant = Tenant.query.filter_by(subdomain='default').first()
            if not tenant:
                tenant = Tenant(
                    name='Default Tenant',
                    subdomain='default',
                    is_active=True
                )
                db.session.add(tenant)
                db.session.commit()
                print("创建默认租户成功")
            
            # 创建管理员用户
            admin_user = User.query.filter_by(
                tenant_id=tenant.id,
                username='admin'
            ).first()
            
            if not admin_user:
                admin_user = User(
                    tenant_id=tenant.id,
                    username='admin',
                    email='admin@example.com',
                    real_name='系统管理员',
                    role='admin'  # 设置为管理员角色
                )
                admin_user.set_password('admin123')  # 设置默认密码
                
                db.session.add(admin_user)
                db.session.flush()
                
                # 创建用户档案
                profile = UserProfile(user_id=admin_user.id)
                db.session.add(profile)
                db.session.commit()
                
                print("创建管理员用户成功: admin / admin123")
            else:
                print("管理员用户已存在")
            
            print("\n初始化完成！")
            print("管理员登录信息:")
            print("用户名: admin")
            print("密码: admin123")
            
        except Exception as e:
            db.session.rollback()
            print(f"初始化失败: {str(e)}")
            raise

if __name__ == '__main__':
    init_admin()