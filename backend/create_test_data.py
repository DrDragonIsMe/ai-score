#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试数据脚本
"""

from app import create_app
from utils.database import db
from models.tenant import Tenant
from models.knowledge import Subject, Chapter, KnowledgePoint
from models.question import Question, QuestionType
import uuid

def create_test_data():
    """创建测试数据"""
    app = create_app()
    with app.app_context():
        # 创建默认租户
        tenant = Tenant.query.filter_by(subdomain='default').first()
        if not tenant:
            tenant = Tenant(
                id=str(uuid.uuid4()),
                subdomain='default',
                name='默认租户',
                is_active=True
            )
            db.session.add(tenant)
            db.session.commit()
        
        # 创建数学学科
        subject = Subject(
            id='1',
            tenant_id=tenant.id,
            code='MATH',
            name='数学',
            category='science',
            grade_range=['高一', '高二', '高三'],
            total_score=150
        )
        db.session.add(subject)
        
        # 创建章节
        chapter = Chapter(
            id='1',
            subject_id='1',
            code='FUNC',
            name='函数',
            description='函数基础知识',
            grade='高一',
            semester=1,
            difficulty=3,
            importance=5
        )
        db.session.add(chapter)
        
        # 创建知识点
        knowledge_point = KnowledgePoint(
            id='1',
            chapter_id='1',
            code='FUNC_BASIC',
            name='函数的基本概念',
            description='函数的定义、定义域、值域等基本概念',
            difficulty=3,
            importance=5
        )
        db.session.add(knowledge_point)
        
        # 创建选择题类型
        question_type = QuestionType(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            code='CHOICE',
            name='选择题',
            description='单项选择题',
            scoring_method='binary'
        )
        db.session.add(question_type)
        
        # 创建测试题目
        questions = [
            Question(
                id=str(uuid.uuid4()),
                tenant_id=tenant.id,
                knowledge_point_id=knowledge_point.id,
                question_type_id=question_type.id,
                title='函数定义域题目1',
                content='函数f(x) = x² + 1的定义域是？',
                options=['A. (-∞, +∞)', 'B. [0, +∞)', 'C. (-∞, 0]', 'D. [1, +∞)'],
                answer='A',
                solution='二次函数的定义域是全体实数',
                difficulty=2,
                score=5,
                estimated_time=120
            ),
            Question(
                id=str(uuid.uuid4()),
                tenant_id=tenant.id,
                knowledge_point_id=knowledge_point.id,
                question_type_id=question_type.id,
                title='函数定义域题目2',
                content='函数f(x) = √(x-1)的定义域是？',
                options=['A. (-∞, +∞)', 'B. [1, +∞)', 'C. (-∞, 1]', 'D. (1, +∞)'],
                answer='B',
                solution='根式函数要求被开方数非负',
                difficulty=2,
                score=5,
                estimated_time=120
            ),
            Question(
                id=str(uuid.uuid4()),
                tenant_id=tenant.id,
                knowledge_point_id=knowledge_point.id,
                question_type_id=question_type.id,
                title='函数值域题目',
                content='函数f(x) = 1/x的值域是？',
                options=['A. (-∞, +∞)', 'B. (-∞, 0)∪(0, +∞)', 'C. [0, +∞)', 'D. (-∞, 0]'],
                answer='B',
                solution='反比例函数的值域不包含0',
                difficulty=2,
                score=5,
                estimated_time=120
            ),
            Question(
                id=str(uuid.uuid4()),
                tenant_id=tenant.id,
                knowledge_point_id=knowledge_point.id,
                question_type_id=question_type.id,
                title='函数性质题目',
                content='函数f(x) = |x|的性质是？',
                options=['A. 奇函数', 'B. 偶函数', 'C. 既奇又偶', 'D. 非奇非偶'],
                answer='B',
                solution='绝对值函数关于y轴对称，是偶函数',
                difficulty=1,
                score=5,
                estimated_time=90
            ),
            Question(
                id=str(uuid.uuid4()),
                tenant_id=tenant.id,
                knowledge_point_id=knowledge_point.id,
                question_type_id=question_type.id,
                title='函数单调性题目',
                content='函数f(x) = x³的单调性是？',
                options=['A. 单调递增', 'B. 单调递减', 'C. 先减后增', 'D. 先增后减'],
                answer='A',
                solution='三次函数f(x)=x³在整个定义域上单调递增',
                difficulty=1,
                score=5,
                estimated_time=90
            )
        ]
        
        for question in questions:
            db.session.add(question)
        
        db.session.commit()
        print("测试数据创建成功！")
        print(f"学科数量: {Subject.query.count()}")
        print(f"章节数量: {Chapter.query.count()}")
        print(f"知识点数量: {KnowledgePoint.query.count()}")
        print(f"题目数量: {Question.query.count()}")

if __name__ == '__main__':
    create_test_data()