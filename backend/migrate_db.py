#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app
from utils.database import db
from models.user import User

def migrate_database():
    """更新数据库表结构"""
    app = create_app()
    
    with app.app_context():
        try:
            # 删除所有表并重新创建
            db.drop_all()
            db.create_all()
            print("数据库表重新创建完成")
            
            # 验证表是否创建成功
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"已创建的表: {tables}")
            
            if 'users' in tables:
                columns = [col['name'] for col in inspector.get_columns('users')]
                print(f"users表字段: {columns}")
                
                required_columns = ['nickname', 'bio', 'preferred_greeting']
                missing_columns = [col for col in required_columns if col not in columns]
                
                if missing_columns:
                    print(f"缺少字段: {missing_columns}")
                else:
                    print("所有必需字段都已存在")
            else:
                print("users表未创建成功")
                
        except Exception as e:
            print(f"数据库更新失败: {e}")
            return False
    
    return True

if __name__ == '__main__':
    migrate_database()