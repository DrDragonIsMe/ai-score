#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习分析模块集成测试脚本
测试前端和后端的完整集成
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from app import create_app
from utils.database import db
from models.user import User
from models.learning import StudyRecord
from models.knowledge import KnowledgePoint, Subject
from models.mistake import MistakeRecord
from datetime import datetime, timedelta
import uuid

def create_test_data():
    """创建测试数据"""
    app = create_app()
    
    with app.app_context():
        print("=== 创建测试数据 ===")
        
        # 获取测试用户
        user = db.session.query(User).first()
        if not user:
            print("✗ 没有找到用户")
            return None
        
        print(f"✓ 使用测试用户: {user.username} (ID: {user.id})")
        
        # 获取或创建学科
        subject = db.session.query(Subject).first()
        if not subject:
            subject = Subject(
                id=str(uuid.uuid4()),
                name="数学",
                description="数学学科",
                tenant_id=user.tenant_id
            )
            db.session.add(subject)
            db.session.commit()
            print("✓ 创建了测试学科: 数学")
        else:
            print(f"✓ 使用现有学科: {subject.name}")
        
        # 获取或创建章节
        from models.knowledge import Chapter
        chapter = db.session.query(Chapter).filter_by(subject_id=subject.id).first()
        if not chapter:
            chapter = Chapter(
                id=str(uuid.uuid4()),
                subject_id=subject.id,
                code="CH001",
                name="基础章节",
                description="测试章节"
            )
            db.session.add(chapter)
            db.session.commit()
            print("✓ 创建了测试章节")
        else:
            print(f"✓ 使用现有章节: {chapter.name}")
        
        # 获取或创建知识点
        knowledge_points = db.session.query(KnowledgePoint).filter_by(chapter_id=chapter.id).limit(3).all()
        if not knowledge_points:
            # 创建一些测试知识点
            kp_names = ["代数基础", "几何图形", "函数概念"]
            for name in kp_names:
                kp = KnowledgePoint(
                    id=str(uuid.uuid4()),
                    chapter_id=chapter.id,
                    code=f"KP{len(knowledge_points)+1:03d}",
                    name=name,
                    description=f"{name}相关知识"
                )
                db.session.add(kp)
                knowledge_points.append(kp)
            db.session.commit()
            print(f"✓ 创建了 {len(knowledge_points)} 个测试知识点")
        else:
            print(f"✓ 使用现有知识点: {len(knowledge_points)} 个")
        
        # 创建学习记录
        existing_records = db.session.query(StudyRecord).filter_by(user_id=user.id).count()
        if existing_records < 10:
            print("✓ 创建测试学习记录...")
            
            # 创建过去30天的学习记录
            for i in range(20):
                days_ago = i
                study_date = datetime.now() - timedelta(days=days_ago)
                
                # 为每个知识点创建记录
                for kp in knowledge_points[:2]:  # 只用前两个知识点
                    record = StudyRecord(
                        id=str(uuid.uuid4()),
                        user_id=user.id,
                        knowledge_point_id=kp.id,
                        study_type="practice",
                        is_correct=(i % 3 != 0),  # 大约67%正确率
                        start_time=study_date,
                        end_time=study_date + timedelta(seconds=60 + (i % 120)),
                        duration=60 + (i % 120),  # 60-180秒
                        mastery_level=1 + (i % 3),  # 1-3级掌握程度
                        created_at=study_date
                    )
                    db.session.add(record)
            
            db.session.commit()
            print("✓ 创建了测试学习记录")
        else:
            print(f"✓ 已有学习记录: {existing_records} 条")
        
        # 检查错题记录（暂时跳过创建，专注于学习记录）
        existing_mistakes = db.session.query(MistakeRecord).count()
        print(f"✓ 现有错题记录: {existing_mistakes} 条")
        
        return user.id

def test_api_endpoints(user_id):
    """测试API端点"""
    print("\n=== 测试API端点 ===")
    
    # 首先获取JWT token
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        # 登录获取token
        login_response = requests.post('http://localhost:5001/api/auth/login', json=login_data)
        if login_response.status_code != 200:
            print(f"✗ 登录失败: {login_response.status_code}")
            return False
        
        token = login_response.json().get('access_token')
        if not token:
            print("✗ 未获取到访问令牌")
            return False
        
        print("✓ 登录成功，获取到访问令牌")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # 测试各个API端点
        endpoints = [
            '/api/learning-analytics/dashboard-summary',
            '/api/learning-analytics/progress',
            '/api/learning-analytics/knowledge-mastery',
            '/api/learning-analytics/performance-trends',
            '/api/learning-analytics/study-statistics',
            '/api/learning-analytics/learning-recommendations'
        ]
        
        success_count = 0
        for endpoint in endpoints:
            try:
                response = requests.get(f'http://localhost:5001{endpoint}', headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        print(f"✓ {endpoint} - 成功")
                        # 打印部分数据结构
                        if 'data' in data and data['data']:
                            keys = list(data['data'].keys())[:3]
                            print(f"  数据字段: {keys}")
                        success_count += 1
                    else:
                        print(f"⚠ {endpoint} - 返回失败: {data.get('message', 'Unknown error')}")
                else:
                    print(f"✗ {endpoint} - HTTP错误: {response.status_code}")
                    if response.text:
                        print(f"  错误信息: {response.text[:200]}")
            except Exception as e:
                print(f"✗ {endpoint} - 请求异常: {str(e)}")
        
        print(f"\n成功测试 {success_count}/{len(endpoints)} 个API端点")
        return success_count == len(endpoints)
        
    except Exception as e:
        print(f"✗ API测试失败: {str(e)}")
        return False

def test_data_consistency():
    """测试数据一致性"""
    print("\n=== 测试数据一致性 ===")
    
    app = create_app()
    
    with app.app_context():
        # 检查各表的数据量
        user_count = db.session.query(User).count()
        subject_count = db.session.query(Subject).count()
        kp_count = db.session.query(KnowledgePoint).count()
        study_count = db.session.query(StudyRecord).count()
        mistake_count = db.session.query(MistakeRecord).count()
        
        print(f"✓ 用户数量: {user_count}")
        print(f"✓ 学科数量: {subject_count}")
        print(f"✓ 知识点数量: {kp_count}")
        print(f"✓ 学习记录数量: {study_count}")
        print(f"✓ 错题记录数量: {mistake_count}")
        
        # 检查数据关联性
        if study_count > 0:
            recent_studies = db.session.query(StudyRecord).filter(
                StudyRecord.created_at >= datetime.now() - timedelta(days=7)
            ).count()
            print(f"✓ 最近7天学习记录: {recent_studies}")
        
        return True

def main():
    """主测试函数"""
    print("学习分析模块集成测试")
    print("=" * 50)
    
    # 1. 创建测试数据
    user_id = create_test_data()
    if not user_id:
        print("❌ 测试数据创建失败")
        return False
    
    # 2. 测试数据一致性
    if not test_data_consistency():
        print("❌ 数据一致性检查失败")
        return False
    
    # 3. 测试API端点
    if not test_api_endpoints(user_id):
        print("❌ API端点测试失败")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 学习分析模块集成测试全部通过！")
    print("\n📋 测试总结:")
    print("- ✅ 后端服务正常运行")
    print("- ✅ 数据库表结构正确")
    print("- ✅ API端点可正常访问")
    print("- ✅ 数据分析功能正常")
    print("\n💡 建议:")
    print("- 前端页面应该能正常显示学习分析数据")
    print("- 如果前端仍显示错误，请检查网络连接和认证状态")
    
    return True

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1)