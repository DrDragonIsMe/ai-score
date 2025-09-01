#!/usr/bin/env python3
"""
数据库迁移脚本：创建试卷知识点映射表

运行方式：
python migrations/create_exam_knowledge_mapping.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from utils.database import db
from models import ExamPaper, Question, Subject
from models.exam_knowledge_mapping import ExamKnowledgeMapping, ExamKnowledgeStatistics

def create_tables():
    """创建试卷知识点映射相关表"""
    app = create_app()
    
    with app.app_context():
        try:
            # 创建表
            db.create_all()
            print("✅ 成功创建试卷知识点映射表:")
            print("   - exam_knowledge_mappings")
            print("   - exam_knowledge_statistics")
            
            # 检查表是否存在
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'exam_knowledge_mappings' in tables:
                print("✅ exam_knowledge_mappings 表已创建")
            else:
                print("❌ exam_knowledge_mappings 表创建失败")
                
            if 'exam_knowledge_statistics' in tables:
                print("✅ exam_knowledge_statistics 表已创建")
            else:
                print("❌ exam_knowledge_statistics 表创建失败")
                
        except Exception as e:
            print(f"❌ 创建表失败: {e}")
            return False
            
    return True

def populate_initial_data():
    """填充初始数据 - 为现有试卷创建知识点映射"""
    from services.exam_knowledge_service import ExamKnowledgeService
    
    app = create_app()
    
    with app.app_context():
        try:
            service = ExamKnowledgeService()
            
            # 获取所有试卷
            papers = ExamPaper.query.all()
            print(f"📊 找到 {len(papers)} 份试卷，开始创建知识点映射...")
            
            success_count = 0
            for paper in papers:
                try:
                    # 为每份试卷创建知识点映射
                    service.create_mapping_for_paper(paper.id)
                    success_count += 1
                    print(f"✅ 已为试卷 '{paper.title}' 创建知识点映射")
                except Exception as e:
                    print(f"❌ 为试卷 '{paper.title}' 创建映射失败: {e}")
                    
            print(f"\n📈 映射创建完成: {success_count}/{len(papers)} 份试卷")
            
            # 更新统计信息
            print("\n🔄 更新知识点统计信息...")
            
            # 获取所有学科并更新统计
            subjects = Subject.query.all()
            
            for subject in subjects:
                try:
                    service.update_knowledge_statistics(subject.id)
                    print(f"✅ 已更新学科 '{subject.name}' 的统计信息")
                except Exception as e:
                    print(f"❌ 更新学科 '{subject.name}' 统计失败: {e}")
                    
        except Exception as e:
            print(f"❌ 填充初始数据失败: {e}")
            return False
            
    return True

if __name__ == '__main__':
    print("🚀 开始创建试卷知识点映射表...")
    
    # 创建表
    if create_tables():
        print("\n🔄 开始填充初始数据...")
        
        # 填充初始数据
        if populate_initial_data():
            print("\n🎉 试卷知识点映射系统初始化完成！")
        else:
            print("\n⚠️  表创建成功，但初始数据填充失败")
    else:
        print("\n❌ 表创建失败，请检查数据库连接和配置")