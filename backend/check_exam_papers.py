import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.exam_papers import ExamPaper
from models.knowledge import Subject

app = create_app()

with app.app_context():
    # 查询试卷数量
    paper_count = ExamPaper.query.count()
    print(f"数据库中试卷数量: {paper_count}")
    
    if paper_count > 0:
        # 查询前5个试卷
        papers = ExamPaper.query.limit(5).all()
        print("\n前5个试卷:")
        for paper in papers:
            print(f"ID: {paper.id}, 标题: {paper.title}, 学科ID: {paper.subject_id}, 年份: {paper.year}")
    
    # 查询学科数量
    subject_count = Subject.query.count()
    print(f"\n数据库中学科数量: {subject_count}")
    
    if subject_count > 0:
        # 查询前5个学科
        subjects = Subject.query.limit(5).all()
        print("\n前5个学科:")
        for subject in subjects:
            print(f"ID: {subject.id}, 名称: {subject.name}, 代码: {subject.code}")