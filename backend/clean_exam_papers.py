import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.exam_papers import ExamPaper
from models.question import Question
from utils.database import db

app = create_app()

with app.app_context():
    # 删除所有试卷数据
    Question.query.delete()
    ExamPaper.query.delete()
    
    db.session.commit()
    
    print("已清理所有试卷和题目数据")
    print(f"剩余试卷数量: {ExamPaper.query.count()}")
    print(f"剩余题目数量: {Question.query.count()}")