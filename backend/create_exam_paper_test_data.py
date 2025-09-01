#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建试卷测试数据脚本
"""

from app import create_app
from utils.database import db
from models.tenant import Tenant
from models.knowledge import Subject
from models.exam_papers import ExamPaper
from models.question import Question, QuestionType
import uuid
from datetime import datetime, timezone

def create_exam_paper_test_data():
    """创建试卷测试数据"""
    app = create_app()
    with app.app_context():
        # 获取默认租户
        tenant = Tenant.query.filter_by(subdomain='default').first()
        if not tenant:
            print("请先运行 create_test_data.py 创建基础数据")
            return
        
        # 获取数学学科
        subject = Subject.query.filter_by(code='math').first()
        if not subject:
            print("数学学科不存在，请检查学科数据")
            return
        
        # 创建题型数据
        question_types = {
            'single_choice': QuestionType(
                id=str(uuid.uuid4()),
                tenant_id=tenant.id,
                code='single_choice',
                name='单选题',
                description='单项选择题',
                category='choice',
                scoring_method='standard',
                time_limit=120,
                is_active=True
            ),
            'calculation': QuestionType(
                id=str(uuid.uuid4()),
                tenant_id=tenant.id,
                code='calculation',
                name='计算题',
                description='计算解答题',
                category='calculation',
                scoring_method='standard',
                time_limit=300,
                is_active=True
            )
        }
        
        for qt in question_types.values():
            existing_qt = QuestionType.query.filter_by(tenant_id=tenant.id, code=qt.code).first()
            if not existing_qt:
                db.session.add(qt)
        
        db.session.commit()
        
        # 创建测试试卷数据
        exam_papers = [
            {
                'title': '2024年高考数学全国卷I',
                'description': '2024年普通高等学校招生全国统一考试数学试题（全国卷I）',
                'year': 2024,
                'exam_type': '高考',
                'region': '全国',
                'total_score': 150,
                'duration': 120,
                'difficulty_level': 'hard'
            },
            {
                'title': '2024年高考数学全国卷II',
                'description': '2024年普通高等学校招生全国统一考试数学试题（全国卷II）',
                'year': 2024,
                'exam_type': '高考',
                'region': '全国',
                'total_score': 150,
                'duration': 120,
                'difficulty_level': 'hard'
            },
            {
                'title': '2023年高考数学全国卷I',
                'description': '2023年普通高等学校招生全国统一考试数学试题（全国卷I）',
                'year': 2023,
                'exam_type': '高考',
                'region': '全国',
                'total_score': 150,
                'duration': 120,
                'difficulty_level': 'hard'
            },
            {
                'title': '2024年北京市高考数学试卷',
                'description': '2024年北京市普通高等学校招生全国统一考试数学试题',
                'year': 2024,
                'exam_type': '高考',
                'region': '北京',
                'total_score': 150,
                'duration': 120,
                'difficulty_level': 'hard'
            },
            {
                'title': '2024年上海市高考数学试卷',
                'description': '2024年上海市普通高等学校招生全国统一考试数学试题',
                'year': 2024,
                'exam_type': '高考',
                'region': '上海',
                'total_score': 150,
                'duration': 120,
                'difficulty_level': 'hard'
            },
            {
                'title': '2024年高三第一次模拟考试数学',
                'description': '高三第一次模拟考试数学试题，难度适中',
                'year': 2024,
                'exam_type': '模拟考试',
                'region': '全国',
                'total_score': 150,
                'duration': 120,
                'difficulty_level': 'medium'
            },
            {
                'title': '2024年高三第二次模拟考试数学',
                'description': '高三第二次模拟考试数学试题，接近高考难度',
                'year': 2024,
                'exam_type': '模拟考试',
                'region': '全国',
                'total_score': 150,
                'duration': 120,
                'difficulty_level': 'hard'
            },
            {
                'title': '2024年高二期末考试数学',
                'description': '高二下学期期末考试数学试题',
                'year': 2024,
                'exam_type': '期末考试',
                'region': '全国',
                'total_score': 150,
                'duration': 120,
                'difficulty_level': 'medium'
            },
            {
                'title': '2024年高一期中考试数学',
                'description': '高一上学期期中考试数学试题',
                'year': 2024,
                'exam_type': '期中考试',
                'region': '全国',
                'total_score': 150,
                'duration': 120,
                'difficulty_level': 'easy'
            },
            {
                'title': '2022年高考数学全国卷I',
                'description': '2022年普通高等学校招生全国统一考试数学试题（全国卷I）',
                'year': 2022,
                'exam_type': '高考',
                'region': '全国',
                'total_score': 150,
                'duration': 120,
                'difficulty_level': 'hard'
            }
        ]
        
        created_papers = []
        for paper_data in exam_papers:
            exam_paper = ExamPaper(
                id=str(uuid.uuid4()),
                tenant_id=tenant.id,
                subject_id=subject.id,
                title=paper_data['title'],
                description=paper_data['description'],
                year=paper_data['year'],
                exam_type=paper_data['exam_type'],
                region=paper_data['region'],
                total_score=paper_data['total_score'],
                duration=paper_data['duration'],
                difficulty_level=paper_data['difficulty_level'],
                file_path=f'/uploads/exam_papers/{uuid.uuid4().hex}.pdf',  # 模拟文件路径
                file_type='pdf',
                file_size=1024000,  # 1MB
                parse_status='completed',
                question_count=20,  # 假设每份试卷20题
                is_public=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.session.add(exam_paper)
            created_papers.append(exam_paper)
        
        # 获取创建的题型
        single_choice_type = QuestionType.query.filter_by(tenant_id=tenant.id, code='single_choice').first()
        calculation_type = QuestionType.query.filter_by(tenant_id=tenant.id, code='calculation').first()
        
        # 为每份试卷创建一些示例题目
        question_templates = [
            {
                'title': '函数单调性判断',
                'content': '判断函数f(x) = x³ - 3x的单调性',
                'question_type_id': single_choice_type.id,
                'options': ['A. 单调递增', 'B. 单调递减', 'C. 先减后增再减', 'D. 先增后减再增'],
                'answer': 'C',
                'solution': '对f(x) = x³ - 3x求导，f\'(x) = 3x² - 3 = 3(x² - 1) = 3(x-1)(x+1)，当x<-1或x>1时f\'(x)>0，当-1<x<1时f\'(x)<0，所以函数先增后减再增',
                'difficulty': 3,
                'score': 5
            },
            {
                'title': '三角函数化简',
                'content': '化简sin²x + cos²x的值',
                'question_type_id': single_choice_type.id,
                'options': ['A. 0', 'B. 1', 'C. 2', 'D. -1'],
                'answer': 'B',
                'solution': '根据三角恒等式sin²x + cos²x = 1',
                'difficulty': 1,
                'score': 5
            },
            {
                'title': '导数应用',
                'content': '求函数f(x) = x² - 4x + 3的最小值',
                'question_type_id': calculation_type.id,
                'options': [],
                'answer': '-1',
                'solution': 'f\'(x) = 2x - 4 = 0，得x = 2，f(2) = 4 - 8 + 3 = -1',
                'difficulty': 2,
                'score': 10
            }
        ]
        
        for paper in created_papers:
            for i, template in enumerate(question_templates):
                question = Question(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant.id,
                    exam_paper_id=paper.id,
                    knowledge_point_id='1',  # 使用之前创建的知识点ID
                    question_type_id=template['question_type_id'],
                    title=template['title'],
                    content=template['content'],
                    options=template['options'],
                    answer=template['answer'],
                    solution=template['solution'],
                    difficulty=template['difficulty'],
                    score=template['score'],
                    estimated_time=120,  # 2分钟
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                db.session.add(question)
        
        db.session.commit()
        print("试卷测试数据创建成功！")
        print(f"创建试卷数量: {len(created_papers)}")
        print(f"总试卷数量: {ExamPaper.query.count()}")
        print(f"总题目数量: {Question.query.count()}")
        
        # 显示创建的试卷列表
        print("\n创建的试卷列表:")
        for paper in created_papers:
            print(f"- {paper.title} ({paper.year}年, {paper.exam_type}, {paper.region})")

if __name__ == '__main__':
    create_exam_paper_test_data()