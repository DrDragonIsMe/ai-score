#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习分析模块测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from utils.database import db
from models.user import User
from models.tracking import LearningMetric, PerformanceSnapshot
from services.learning_analytics_service import LearningAnalyticsService
from datetime import datetime, timedelta
import json

def test_learning_analytics():
    """测试学习分析功能"""
    app = create_app()
    
    with app.app_context():
        print("=== 学习分析模块测试 ===")
        
        # 1. 测试服务初始化
        try:
            analytics_service = LearningAnalyticsService()
            print("✓ 学习分析服务初始化成功")
        except Exception as e:
            print(f"✗ 学习分析服务初始化失败: {e}")
            return False
        
        # 2. 检查数据库表是否存在
        try:
            # 检查学习指标表
            metrics_count = db.session.query(LearningMetric).count()
            print(f"✓ 学习指标表存在，当前记录数: {metrics_count}")
            
            # 检查性能快照表
            snapshots_count = db.session.query(PerformanceSnapshot).count()
            print(f"✓ 性能快照表存在，当前记录数: {snapshots_count}")
            
        except Exception as e:
            print(f"✗ 数据库表检查失败: {e}")
            return False
        
        # 3. 测试用户查找
        try:
            users = db.session.query(User).limit(5).all()
            print(f"✓ 找到 {len(users)} 个用户")
            
            if users:
                test_user = users[0]
                print(f"  测试用户: {test_user.username} (ID: {test_user.id})")
                
                # 4. 测试学习进度分析
                try:
                    progress_data = analytics_service.analyze_learning_progress(test_user.id)
                    if progress_data:
                        print("✓ 学习进度分析成功")
                        print(f"  分析期间: {progress_data.get('period', {})}")
                        print(f"  总体进度: {progress_data.get('overall_progress', {})}")
                    else:
                        print("⚠ 学习进度分析返回空数据（可能是用户没有学习记录）")
                except Exception as e:
                    print(f"✗ 学习进度分析失败: {e}")
                
                # 5. 测试知识点掌握分析
                try:
                    mastery_data = analytics_service.analyze_knowledge_mastery(test_user.id)
                    if mastery_data:
                        print("✓ 知识点掌握分析成功")
                        print(f"  掌握统计: {mastery_data.get('mastery_stats', {})}")
                    else:
                        print("⚠ 知识点掌握分析返回空数据")
                except Exception as e:
                    print(f"✗ 知识点掌握分析失败: {e}")
                
                # 5. 测试性能趋势分析
                try:
                    trends_data = analytics_service.analyze_performance_trends(test_user.id)
                    if trends_data:
                        print("✓ 性能趋势分析成功")
                        print(f"  趋势指标: {trends_data.get('trend_summary', {})}")
                    else:
                        print("⚠ 性能趋势分析返回空数据")
                except Exception as e:
                    print(f"✗ 性能趋势分析失败: {e}")
                
                # 7. 测试综合报告生成
                try:
                    report_data = analytics_service.generate_comprehensive_report(test_user.id, 30)
                    if report_data:
                        print("✓ 综合报告生成成功")
                        print(f"  报告摘要: {report_data.get('summary', 'N/A')[:100]}...")
                    else:
                        print("⚠ 综合报告生成返回空数据")
                except Exception as e:
                    print(f"✗ 综合报告生成失败: {e}")
            
            else:
                print("⚠ 没有找到测试用户")
                
        except Exception as e:
            print(f"✗ 用户查找失败: {e}")
            return False
        
        print("\n=== 测试完成 ===")
        return True

def test_api_routes():
    """测试API路由"""
    app = create_app()
    
    with app.app_context():
        print("\n=== API路由测试 ===")
        
        # 获取所有路由
        routes = []
        for rule in app.url_map.iter_rules():
            if 'learning-analytics' in rule.rule:
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': list(rule.methods),
                    'rule': rule.rule
                })
        
        if routes:
            print(f"✓ 找到 {len(routes)} 个学习分析API路由:")
            for route in routes:
                methods_list = list(route['methods']) if route['methods'] else []
                print(f"  {route['rule']} [{', '.join(methods_list)}]")
        else:
            print("✗ 没有找到学习分析API路由")
            return False
        
        return True

if __name__ == '__main__':
    success = test_learning_analytics()
    api_success = test_api_routes()
    
    if success and api_success:
        print("\n🎉 学习分析模块测试通过！")
    else:
        print("\n❌ 学习分析模块存在问题，需要修复")
        sys.exit(1)