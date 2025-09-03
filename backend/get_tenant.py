#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app
from models.tenant import Tenant
from utils.database import db

def get_tenant_info():
    app = create_app()
    with app.app_context():
        try:
            tenants = Tenant.query.all()
            print(f'找到 {len(tenants)} 个租户:')
            
            if tenants:
                for tenant in tenants:
                    print(f'- ID: {tenant.id}')
                    print(f'  名称: {tenant.name}')
                    print(f'  域名: {tenant.domain}')
                    print(f'  状态: {"激活" if tenant.is_active else "未激活"}')
                    print()
                return tenants[0].id if tenants else None
            else:
                print('数据库中没有租户信息')
                # 创建默认租户
                default_tenant = Tenant(
                    name='默认租户',
                    domain='localhost',
                    is_active=True
                )
                db.session.add(default_tenant)
                db.session.commit()
                print(f'已创建默认租户，ID: {default_tenant.id}')
                return default_tenant.id
                
        except Exception as e:
            print(f'查询失败: {str(e)}')
            return None

if __name__ == '__main__':
    tenant_id = get_tenant_info()
    if tenant_id:
        print(f'\n可用的租户ID: {tenant_id}')