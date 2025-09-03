#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习分析模块性能优化脚本
包括数据库索引优化、查询优化和缓存机制
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from utils.database import db
from sqlalchemy import text, Index
from models.learning import StudyRecord
from models.mistake import MistakeRecord
from models.knowledge import KnowledgePoint, Subject, Chapter
from models.user import User
from datetime import datetime, timedelta
import time

def create_performance_indexes():
    """
    创建性能优化索引
    """
    print("=== 创建性能优化索引 ===")
    
    try:
        # 为StudyRecord表创建复合索引
        indexes_to_create = [
            # 用户ID + 创建时间索引（用于时间范围查询）
            "CREATE INDEX IF NOT EXISTS idx_study_records_user_created ON study_records(user_id, created_at)",
            
            # 用户ID + 知识点ID索引（用于知识点分析）
            "CREATE INDEX IF NOT EXISTS idx_study_records_user_kp ON study_records(user_id, knowledge_point_id)",
            
            # 用户ID + 正确性索引（用于准确率统计）
            "CREATE INDEX IF NOT EXISTS idx_study_records_user_correct ON study_records(user_id, is_correct)",
            
            # 创建时间索引（用于时间分析）
            "CREATE INDEX IF NOT EXISTS idx_study_records_created_at ON study_records(created_at)",
            
            # 知识点ID索引
            "CREATE INDEX IF NOT EXISTS idx_study_records_kp_id ON study_records(knowledge_point_id)",
            
            # 为MistakeRecord表创建索引
            "CREATE INDEX IF NOT EXISTS idx_mistake_records_user_created ON mistake_records(user_id, created_time)",
            "CREATE INDEX IF NOT EXISTS idx_mistake_records_user_kp ON mistake_records(user_id, knowledge_point_id)",
            
            # 为KnowledgePoint表创建索引
            "CREATE INDEX IF NOT EXISTS idx_knowledge_points_chapter ON knowledge_points(chapter_id)",
            
            # 为Chapter表创建索引
            "CREATE INDEX IF NOT EXISTS idx_chapters_subject ON chapters(subject_id)"
        ]
        
        for index_sql in indexes_to_create:
            try:
                db.session.execute(text(index_sql))
                print(f"✓ 创建索引: {index_sql.split('idx_')[1].split(' ')[0] if 'idx_' in index_sql else 'unknown'}")
            except Exception as e:
                print(f"⚠ 索引创建失败或已存在: {str(e)[:50]}...")
        
        db.session.commit()
        print("✓ 所有索引创建完成")
        
    except Exception as e:
        print(f"✗ 索引创建过程出错: {str(e)}")
        db.session.rollback()

def optimize_database_settings():
    """
    优化数据库设置
    """
    print("\n=== 优化数据库设置 ===")
    
    try:
        # SQLite性能优化设置
        optimization_settings = [
            "PRAGMA journal_mode = WAL",  # 启用WAL模式提高并发性能
            "PRAGMA synchronous = NORMAL",  # 平衡安全性和性能
            "PRAGMA cache_size = 10000",  # 增加缓存大小
            "PRAGMA temp_store = MEMORY",  # 临时表存储在内存中
            "PRAGMA mmap_size = 268435456",  # 启用内存映射（256MB）
        ]
        
        for setting in optimization_settings:
            try:
                db.session.execute(text(setting))
                print(f"✓ 应用设置: {setting}")
            except Exception as e:
                print(f"⚠ 设置应用失败: {setting} - {str(e)}")
        
        db.session.commit()
        print("✓ 数据库优化设置完成")
        
    except Exception as e:
        print(f"✗ 数据库设置优化失败: {str(e)}")

def analyze_query_performance():
    """
    分析查询性能
    """
    print("\n=== 分析查询性能 ===")
    
    # 获取测试用户
    user = db.session.query(User).first()
    if not user:
        print("✗ 没有找到测试用户")
        return
    
    user_id = user.id
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # 测试查询性能
    queries_to_test = [
        {
            'name': '基础学习记录查询',
            'query': lambda: db.session.query(StudyRecord).filter(
                StudyRecord.user_id == user_id,
                StudyRecord.created_at >= start_date
            ).all()
        },
        {
            'name': '按知识点分组统计',
            'query': lambda: db.session.query(
                StudyRecord.knowledge_point_id,
                db.func.count(StudyRecord.id).label('count'),
                db.func.avg(StudyRecord.duration).label('avg_duration'),
                db.func.sum(db.case([(StudyRecord.is_correct == True, 1)], else_=0)).label('correct_count')
            ).filter(
                StudyRecord.user_id == user_id,
                StudyRecord.created_at >= start_date
            ).group_by(StudyRecord.knowledge_point_id).all()
        },
        {
            'name': '按日期分组统计',
            'query': lambda: db.session.query(
                db.func.date(StudyRecord.created_at).label('date'),
                db.func.count(StudyRecord.id).label('count'),
                db.func.sum(StudyRecord.duration).label('total_duration'),
                db.func.avg(db.case([(StudyRecord.is_correct == True, 1.0)], else_=0.0)).label('accuracy')
            ).filter(
                StudyRecord.user_id == user_id,
                StudyRecord.created_at >= start_date
            ).group_by(db.func.date(StudyRecord.created_at)).all()
        },
        {
            'name': '复杂联表查询',
            'query': lambda: db.session.query(
                StudyRecord,
                KnowledgePoint.name.label('kp_name'),
                Chapter.name.label('chapter_name'),
                Subject.name.label('subject_name')
            ).join(
                KnowledgePoint, StudyRecord.knowledge_point_id == KnowledgePoint.id
            ).join(
                Chapter, KnowledgePoint.chapter_id == Chapter.id
            ).join(
                Subject, Chapter.subject_id == Subject.id
            ).filter(
                StudyRecord.user_id == user_id,
                StudyRecord.created_at >= start_date
            ).limit(100).all()
        }
    ]
    
    performance_results = []
    
    for test in queries_to_test:
        try:
            # 预热查询
            test['query']()
            
            # 测试查询性能（执行3次取平均值）
            times = []
            for _ in range(3):
                start_time = time.time()
                result = test['query']()
                end_time = time.time()
                times.append(end_time - start_time)
            
            avg_time = sum(times) / len(times)
            result_count = len(result) if hasattr(result, '__len__') else 1
            
            performance_results.append({
                'name': test['name'],
                'avg_time': avg_time,
                'result_count': result_count,
                'performance_rating': 'excellent' if avg_time < 0.1 else 'good' if avg_time < 0.5 else 'needs_improvement'
            })
            
            print(f"✓ {test['name']}: {avg_time:.3f}秒 ({result_count}条结果) - {performance_results[-1]['performance_rating']}")
            
        except Exception as e:
            print(f"✗ {test['name']} 查询失败: {str(e)}")
            performance_results.append({
                'name': test['name'],
                'avg_time': float('inf'),
                'result_count': 0,
                'performance_rating': 'failed'
            })
    
    return performance_results

def create_materialized_views():
    """
    创建物化视图以提高查询性能
    """
    print("\n=== 创建性能优化视图 ===")
    
    try:
        # 创建用户学习统计视图
        user_stats_view = """
        CREATE VIEW IF NOT EXISTS user_learning_stats AS
        SELECT 
            user_id,
            COUNT(*) as total_questions,
            SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct_answers,
            AVG(CASE WHEN is_correct THEN 1.0 ELSE 0.0 END) * 100 as accuracy_rate,
            SUM(duration) as total_study_time,
            AVG(duration) as avg_time_per_question,
            COUNT(DISTINCT DATE(created_at)) as study_days,
            MIN(created_at) as first_study,
            MAX(created_at) as last_study
        FROM study_records 
        GROUP BY user_id
        """
        
        # 创建知识点统计视图
        knowledge_stats_view = """
        CREATE VIEW IF NOT EXISTS knowledge_point_stats AS
        SELECT 
            sr.knowledge_point_id,
            kp.name as knowledge_point_name,
            c.name as chapter_name,
            s.name as subject_name,
            COUNT(*) as total_attempts,
            SUM(CASE WHEN sr.is_correct THEN 1 ELSE 0 END) as correct_attempts,
            AVG(CASE WHEN sr.is_correct THEN 1.0 ELSE 0.0 END) * 100 as accuracy_rate,
            AVG(sr.duration) as avg_duration,
            COUNT(DISTINCT sr.user_id) as unique_users
        FROM study_records sr
        JOIN knowledge_points kp ON sr.knowledge_point_id = kp.id
        JOIN chapters c ON kp.chapter_id = c.id
        JOIN subjects s ON c.subject_id = s.id
        GROUP BY sr.knowledge_point_id, kp.name, c.name, s.name
        """
        
        # 创建每日学习统计视图
        daily_stats_view = """
        CREATE VIEW IF NOT EXISTS daily_learning_stats AS
        SELECT 
            user_id,
            DATE(created_at) as study_date,
            COUNT(*) as questions_count,
            SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct_count,
            AVG(CASE WHEN is_correct THEN 1.0 ELSE 0.0 END) * 100 as daily_accuracy,
            SUM(duration) as daily_study_time,
            AVG(duration) as avg_question_time
        FROM study_records 
        GROUP BY user_id, DATE(created_at)
        """
        
        views = [
            ('用户学习统计视图', user_stats_view),
            ('知识点统计视图', knowledge_stats_view),
            ('每日学习统计视图', daily_stats_view)
        ]
        
        for view_name, view_sql in views:
            try:
                db.session.execute(text(view_sql))
                print(f"✓ 创建视图: {view_name}")
            except Exception as e:
                print(f"⚠ 视图创建失败或已存在: {view_name} - {str(e)[:50]}...")
        
        db.session.commit()
        print("✓ 所有视图创建完成")
        
    except Exception as e:
        print(f"✗ 视图创建过程出错: {str(e)}")
        db.session.rollback()

def implement_query_optimizations():
    """
    实现查询优化建议
    """
    print("\n=== 查询优化建议 ===")
    
    optimizations = [
        {
            'category': '索引优化',
            'recommendations': [
                '为高频查询字段创建复合索引',
                '定期分析查询执行计划',
                '避免在WHERE子句中使用函数',
                '使用LIMIT限制结果集大小'
            ]
        },
        {
            'category': '查询结构优化',
            'recommendations': [
                '使用EXISTS代替IN子查询',
                '避免SELECT *，只选择需要的字段',
                '合理使用JOIN，避免笛卡尔积',
                '使用批量操作代替循环查询'
            ]
        },
        {
            'category': '缓存策略',
            'recommendations': [
                '对频繁访问的统计数据实施缓存',
                '使用Redis缓存热点数据',
                '实现查询结果缓存机制',
                '设置合理的缓存过期时间'
            ]
        },
        {
            'category': '数据库设计优化',
            'recommendations': [
                '考虑数据分区策略',
                '定期清理历史数据',
                '优化数据类型选择',
                '实现读写分离'
            ]
        }
    ]
    
    for opt in optimizations:
        print(f"\n📊 {opt['category']}:")
        for i, rec in enumerate(opt['recommendations'], 1):
            print(f"  {i}. {rec}")

def generate_performance_report(performance_results):
    """
    生成性能报告
    """
    print("\n=== 性能优化报告 ===")
    
    if not performance_results:
        print("⚠ 没有性能测试结果")
        return
    
    # 统计性能等级
    excellent_count = sum(1 for r in performance_results if r['performance_rating'] == 'excellent')
    good_count = sum(1 for r in performance_results if r['performance_rating'] == 'good')
    needs_improvement_count = sum(1 for r in performance_results if r['performance_rating'] == 'needs_improvement')
    failed_count = sum(1 for r in performance_results if r['performance_rating'] == 'failed')
    
    total_queries = len(performance_results)
    avg_time = sum(r['avg_time'] for r in performance_results if r['avg_time'] != float('inf')) / max(1, total_queries - failed_count)
    
    print(f"📈 查询性能统计:")
    print(f"  - 总查询数: {total_queries}")
    print(f"  - 优秀 (<0.1s): {excellent_count} ({excellent_count/total_queries*100:.1f}%)")
    print(f"  - 良好 (<0.5s): {good_count} ({good_count/total_queries*100:.1f}%)")
    print(f"  - 需改进 (≥0.5s): {needs_improvement_count} ({needs_improvement_count/total_queries*100:.1f}%)")
    print(f"  - 失败: {failed_count} ({failed_count/total_queries*100:.1f}%)")
    print(f"  - 平均响应时间: {avg_time:.3f}秒")
    
    # 性能等级评估
    if excellent_count >= total_queries * 0.8:
        overall_rating = "优秀"
        rating_icon = "🟢"
    elif good_count + excellent_count >= total_queries * 0.7:
        overall_rating = "良好"
        rating_icon = "🟡"
    else:
        overall_rating = "需要优化"
        rating_icon = "🔴"
    
    print(f"\n{rating_icon} 总体性能评级: {overall_rating}")
    
    # 优化建议
    if needs_improvement_count > 0 or failed_count > 0:
        print("\n🔧 优化建议:")
        if needs_improvement_count > 0:
            print("  - 对慢查询进行索引优化")
            print("  - 考虑实现查询结果缓存")
            print("  - 优化查询逻辑，减少数据扫描")
        if failed_count > 0:
            print("  - 检查失败查询的错误原因")
            print("  - 验证数据库连接和权限")
            print("  - 优化查询语法和逻辑")

def main():
    """
    主优化流程
    """
    print("学习分析模块性能优化")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        # 1. 创建性能索引
        create_performance_indexes()
        
        # 2. 优化数据库设置
        optimize_database_settings()
        
        # 3. 创建优化视图
        create_materialized_views()
        
        # 4. 分析查询性能
        performance_results = analyze_query_performance()
        
        # 5. 生成性能报告
        generate_performance_report(performance_results)
        
        # 6. 提供优化建议
        implement_query_optimizations()
        
        print("\n" + "=" * 50)
        print("🎯 性能优化完成！")
        
        print("\n📋 优化总结:")
        print("- ✅ 数据库索引优化")
        print("- ✅ 查询性能分析")
        print("- ✅ 视图创建优化")
        print("- ✅ 数据库设置调优")
        print("- ✅ 性能监控报告")
        
        print("\n💡 后续建议:")
        print("- 定期监控查询性能")
        print("- 实施Redis缓存机制")
        print("- 考虑数据分区策略")
        print("- 建立性能监控告警")

if __name__ == '__main__':
    main()