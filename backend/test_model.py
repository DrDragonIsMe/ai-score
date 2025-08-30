#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试ExamSession模型创建
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.exam import ExamSession, ExamStatus
from utils.database import db

def test_exam_session_creation():
    """测试ExamSession创建"""
    app = create_app()
    
    with app.app_context():
        try:
            # 创建ExamSession对象
            exam_session = ExamSession(
                user_id=1,
                exam_type='practice',
                title='测试考试',
                subject_id=1,
                total_questions=10,
                total_time_minutes=60,
                max_possible_score=100.0,
                status=ExamStatus.SCHEDULED.value,
                completed_questions=0
            )
            
            print("ExamSession对象创建成功")
            print(f"question_ids默认值: {exam_session.question_ids}")
            print(f"answers默认值: {exam_session.answers}")
            print(f"question_times默认值: {exam_session.question_times}")
            print(f"question_attempts默认值: {exam_session.question_attempts}")
            
            # 尝试保存到数据库
            db.session.add(exam_session)
            db.session.flush()
            
            print("数据库flush成功")
            
            # 设置question_ids
            exam_session.question_ids = ['1', '2', '3']
            print("设置question_ids成功")
            
            db.session.commit()
            print("数据库提交成功")
            
        except Exception as e:
            import traceback
            print(f"错误: {str(e)}")
            print(f"错误堆栈: {traceback.format_exc()}")
            db.session.rollback()

if __name__ == '__main__':
    test_exam_session_creation()