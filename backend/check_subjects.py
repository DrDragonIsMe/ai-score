#!/usr/bin/env python3

import sys
sys.path.append('.')

from app import create_app
from models import Subject

app = create_app()
with app.app_context():
    count = Subject.query.count()
    print(f'学科数量: {count}')
    
    if count > 0:
        subjects = Subject.query.all()
        print('现有学科:')
        for s in subjects[:10]:
            print(f'- {s.name} (ID: {s.id})')
    else:
        print('数据库中没有学科数据')