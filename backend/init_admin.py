#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化管理员用户和九大学科
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import User, Tenant, UserProfile, Subject
from utils.database import db

def init_admin_and_subjects():
    """初始化管理员用户和九大学科"""
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
            
            # 初始化九大学科
            default_subjects = [
                {
                    'code': 'chinese',
                    'name': '语文',
                    'name_en': 'Chinese',
                    'category': 'language',
                    'description': '语文学科，包含现代文阅读、古诗文阅读、写作等',
                    'total_score': 150,
                    'sort_order': 1
                },
                {
                    'code': 'math',
                    'name': '数学',
                    'name_en': 'Mathematics',
                    'category': 'science',
                    'description': '数学学科，包含代数、几何、概率统计等',
                    'total_score': 150,
                    'sort_order': 2
                },
                {
                    'code': 'english',
                    'name': '英语',
                    'name_en': 'English',
                    'category': 'language',
                    'description': '英语学科，包含听力、阅读、写作等',
                    'total_score': 150,
                    'sort_order': 3
                },
                {
                    'code': 'physics',
                    'name': '物理',
                    'name_en': 'Physics',
                    'category': 'science',
                    'description': '物理学科，包含力学、电磁学、光学等',
                    'total_score': 100,
                    'sort_order': 4
                },
                {
                    'code': 'chemistry',
                    'name': '化学',
                    'name_en': 'Chemistry',
                    'category': 'science',
                    'description': '化学学科，包含无机化学、有机化学、物理化学等',
                    'total_score': 100,
                    'sort_order': 5
                },
                {
                    'code': 'biology',
                    'name': '生物',
                    'name_en': 'Biology',
                    'category': 'science',
                    'description': '生物学科，包含细胞生物学、遗传学、生态学等',
                    'total_score': 100,
                    'sort_order': 6
                },
                {
                    'code': 'history',
                    'name': '历史',
                    'name_en': 'History',
                    'category': 'liberal_arts',
                    'description': '历史学科，包含中国古代史、中国近现代史、世界史等',
                    'total_score': 100,
                    'sort_order': 7
                },
                {
                    'code': 'geography',
                    'name': '地理',
                    'name_en': 'Geography',
                    'category': 'liberal_arts',
                    'description': '地理学科，包含自然地理、人文地理、区域地理等',
                    'total_score': 100,
                    'sort_order': 8
                },
                {
                    'code': 'politics',
                    'name': '政治',
                    'name_en': 'Politics',
                    'category': 'liberal_arts',
                    'description': '政治学科，包含马克思主义基本原理、思想政治教育等',
                    'total_score': 100,
                    'sort_order': 9
                }
            ]
            
            created_subjects = []
            for subject_data in default_subjects:
                # 检查是否已存在
                existing = Subject.query.filter_by(
                    tenant_id=tenant.id,
                    code=subject_data['code']
                ).first()
                
                if not existing:
                    subject = Subject(
                        tenant_id=tenant.id,
                        **subject_data
                    )
                    db.session.add(subject)
                    created_subjects.append(subject_data['name'])
            
            db.session.commit()
            
            if created_subjects:
                print(f"成功初始化 {len(created_subjects)} 个学科: {', '.join(created_subjects)}")
            else:
                print("所有学科已存在")
            
            print("\n初始化完成！")
            print("管理员登录信息:")
            print("用户名: admin")
            print("密码: admin123")
            
        except Exception as e:
            db.session.rollback()
            print(f"初始化失败: {str(e)}")
            raise

if __name__ == '__main__':
    init_admin_and_subjects()