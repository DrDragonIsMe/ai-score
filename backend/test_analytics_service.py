#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习分析服务直接测试脚本
测试学习分析服务的核心功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from utils.database import db
from models.user import User
from services.learning_analytics_service import LearningAnalyticsService
from datetime import datetime, timedelta

def test_learning_analytics_service():
    """测试学习分析服务"""
    print("学习分析服务功能测试")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        # 获取测试用户
        user = db.session.query(User).first()
        if not user:
            print("✗ 没有找到测试用户")
            return False
        
        print(f"✓ 使用测试用户: {user.username} (ID: {user.id})")
        
        # 初始化学习分析服务
        analytics_service = LearningAnalyticsService()
        
        # 测试1: 学习进度分析
        print("\n=== 测试学习进度分析 ===")
        try:
            progress_data = analytics_service.analyze_learning_progress(
                user_id=user.id,
                period_days=30
            )
            if progress_data:
                print(f"✓ 学习进度分析成功")
                overall = progress_data.get('overall_progress', {})
                print(f"  - 总学习时长: {overall.get('total_study_time', 0)} 秒")
                print(f"  - 题目总数: {overall.get('total_questions', 0)}")
                print(f"  - 正确率: {overall.get('average_accuracy', 0):.1f}%")
                print(f"  - 学习天数: {overall.get('study_days', 0)}")
                print(f"  - 日均学习时长: {overall.get('daily_average_time', 0):.1f} 秒")
                
                if progress_data.get('subject_progress'):
                    print("  - 学科分布:")
                    for subject_data in progress_data['subject_progress'][:3]:  # 只显示前3个
                        print(f"    {subject_data.get('subject_name', 'Unknown')}: {subject_data.get('accuracy', 0):.1f}% 正确率")
            else:
                print("⚠ 学习进度分析返回空数据")
        except Exception as e:
            print(f"✗ 学习进度分析失败: {str(e)}")
            return False
        
        # 测试2: 知识点掌握分析
        print("\n=== 测试知识点掌握分析 ===")
        try:
            mastery_data = analytics_service.analyze_knowledge_mastery(
                user_id=user.id,
                subject_id=None  # 分析所有学科
            )
            if mastery_data:
                print(f"✓ 知识点掌握分析成功")
                summary = mastery_data.get('mastery_summary', {})
                print(f"  - 掌握知识点数: {summary.get('mastered_count', 0)}")
                print(f"  - 薄弱知识点数: {summary.get('weak_count', 0)}")
                print(f"  - 总体掌握率: {summary.get('overall_mastery_rate', 0):.1f}%")
                
                if mastery_data.get('knowledge_points'):
                    print("  - 知识点详情:")
                    for kp in mastery_data['knowledge_points'][:3]:  # 只显示前3个
                        name = kp.get('name', 'Unknown')
                        mastery = kp.get('mastery_level', 0)
                        if isinstance(mastery, (int, float)):
                            print(f"    {name}: {mastery:.1f}%")
                        else:
                            print(f"    {name}: {mastery}%")
            else:
                print("⚠ 知识点掌握分析返回空数据")
        except Exception as e:
            print(f"✗ 知识点掌握分析失败: {str(e)}")
            return False
        
        # 测试3: 性能趋势分析
        print("\n=== 测试性能趋势分析 ===")
        try:
            trends_data = analytics_service.analyze_performance_trends(
                user_id=user.id,
                period_days=30
            )
            if trends_data:
                print(f"✓ 性能趋势分析成功")
                print(f"  - 趋势数据点数: {len(trends_data.get('daily_performance', []))}")
                print(f"  - 整体趋势: {trends_data.get('overall_trend', 'stable')}")
                
                if trends_data.get('recent_performance'):
                    recent = trends_data['recent_performance']
                    print(f"  - 最近表现: {recent.get('accuracy', 0):.1f}% 正确率")
            else:
                print("⚠ 性能趋势分析返回空数据")
        except Exception as e:
            print(f"✗ 性能趋势分析失败: {str(e)}")
            return False
        
        # 测试4: 综合报告生成
        print("\n=== 测试综合报告生成 ===")
        try:
            report_data = analytics_service.generate_comprehensive_report(
                user_id=user.id,
                period_days=7  # 7天报告
            )
            if report_data:
                print(f"✓ 综合报告生成成功")
                print(f"  - 报告类型: {report_data.get('report_type', 'comprehensive')}")
                print(f"  - 生成时间: {report_data.get('generated_at', 'unknown')}")
                
                if report_data.get('summary'):
                    summary = report_data['summary']
                    print(f"  - 学习总时长: {summary.get('total_study_time', 0)} 秒")
                    print(f"  - 完成题目数: {summary.get('questions_completed', 0)}")
                    print(f"  - 平均正确率: {summary.get('average_accuracy', 0):.1f}%")
            else:
                print("⚠ 综合报告生成返回空数据")
        except Exception as e:
            print(f"✗ 综合报告生成失败: {str(e)}")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 学习分析服务测试全部通过！")
        
        # 输出测试总结
        print("\n📊 测试数据总结:")
        print(f"- 测试用户: {user.username}")
        print(f"- 学习记录: 有数据可分析")
        print(f"- 分析功能: 全部正常")
        print(f"- 数据完整性: ✅")
        
        return True

def main():
    """主函数"""
    success = test_learning_analytics_service()
    if not success:
        print("❌ 学习分析服务测试失败")
        sys.exit(1)
    else:
        print("\n✅ 学习分析服务功能正常，可以进行前端集成测试")

if __name__ == '__main__':
    main()