import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.exam_papers import ExamPaper
from models.knowledge import Subject
from models.tenant import Tenant

app = create_app()

with app.app_context():
    # 查询租户数据
    tenant_count = Tenant.query.count()
    print(f"数据库中租户数量: {tenant_count}")
    
    if tenant_count > 0:
        tenants = Tenant.query.limit(3).all()
        print("\n前3个租户:")
        for tenant in tenants:
            print(f"ID: {tenant.id}, 名称: {tenant.name}")
    
    # 查询试卷的tenant_id
    papers = ExamPaper.query.limit(5).all()
    print("\n前5个试卷的tenant_id:")
    for paper in papers:
        print(f"试卷ID: {paper.id}, tenant_id: {paper.tenant_id}")
    
    # 查询学科的tenant_id
    subjects = Subject.query.limit(5).all()
    print("\n前5个学科的tenant_id:")
    for subject in subjects:
        print(f"学科ID: {subject.id}, 名称: {subject.name}, tenant_id: {getattr(subject, 'tenant_id', 'N/A')}")