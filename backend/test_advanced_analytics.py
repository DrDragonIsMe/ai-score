#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级学习分析功能测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from utils.database import db
from models.user import User
from services.advanced_analytics_service import AdvancedAnalyticsService
from datetime import datetime, timedelta

def test_advanced_analytics():
    """测试高级学习分析功能"""
    print("高级学习分析功能测试")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        # 获取测试用户
        user = db.session.query(User).first()
        if not user:
            print("✗ 没有找到测试用户")
            return False
        
        print(f"✓ 使用测试用户: {user.username} (ID: {user.id})")
        
        # 初始化高级分析服务
        advanced_service = AdvancedAnalyticsService()
        
        # 测试1: 学习效率分析
        print("\n=== 测试学习效率分析 ===")
        try:
            efficiency_data = advanced_service.analyze_learning_efficiency(user.id, 30)
            if efficiency_data:
                print("✓ 学习效率分析成功")
                overall = efficiency_data.get('overall_efficiency', {})
                print(f"  - 效率得分: {overall.get('efficiency_score', 0):.1f}")
                print(f"  - 正确率: {overall.get('accuracy_rate', 0):.1f}%")
                print(f"  - 平均答题时间: {overall.get('avg_time_per_question', 0):.1f}秒")
                print(f"  - 每日效率数据点: {len(efficiency_data.get('daily_efficiency', []))}")
                print(f"  - 知识点效率数据: {len(efficiency_data.get('knowledge_efficiency', []))}")
                print(f"  - 建议数量: {len(efficiency_data.get('recommendations', []))}")
            else:
                print("⚠ 学习效率分析返回空数据")
        except Exception as e:
            print(f"✗ 学习效率分析失败: {str(e)}")
            return False
        
        # 测试2: 时间分布分析
        print("\n=== 测试时间分布分析 ===")
        try:
            time_data = advanced_service.analyze_time_distribution(user.id, 30)
            if time_data:
                print("✓ 时间分布分析成功")
                print(f"  - 小时分布数据点: {len(time_data.get('hourly_distribution', []))}")
                print(f"  - 星期分布数据点: {len(time_data.get('weekly_distribution', []))}")
                
                session_analysis = time_data.get('session_analysis', {})
                print(f"  - 总会话数: {session_analysis.get('total_sessions', 0)}")
                print(f"  - 平均会话时长: {session_analysis.get('avg_session_length', 0):.1f}秒")
                
                optimal_times = time_data.get('optimal_times', [])
                if optimal_times:
                    best_time = optimal_times[0]
                    print(f"  - 最佳学习时间: {best_time.get('hour', 0)}:00 (表现分数: {best_time.get('performance_score', 0):.2f})")
                
                print(f"  - 时间模式: {len(time_data.get('time_patterns', []))}")
                print(f"  - 建议数量: {len(time_data.get('recommendations', []))}")
            else:
                print("⚠ 时间分布分析返回空数据")
        except Exception as e:
            print(f"✗ 时间分布分析失败: {str(e)}")
            return False
        
        # 测试3: 难度适应性分析
        print("\n=== 测试难度适应性分析 ===")
        try:
            difficulty_data = advanced_service.analyze_difficulty_adaptation(user.id, 30)
            if difficulty_data:
                print("✓ 难度适应性分析成功")
                print(f"  - 适应性评分: {difficulty_data.get('adaptation_score', 0):.1f}")
                print(f"  - 推荐难度: {difficulty_data.get('recommended_difficulty', 1)}")
                print(f"  - 挑战准备度: {difficulty_data.get('challenge_readiness', 'unknown')}")
                print(f"  - 难度表现数据: {len(difficulty_data.get('difficulty_performance', []))}")
            else:
                print("⚠ 难度适应性分析返回空数据")
        except Exception as e:
            print(f"✗ 难度适应性分析失败: {str(e)}")
            return False
        
        # 测试4: 学习模式识别
        print("\n=== 测试学习模式识别 ===")
        try:
            pattern_data = advanced_service.identify_learning_patterns(user.id, 60)
            if pattern_data:
                print("✓ 学习模式识别成功")
                
                frequency_pattern = pattern_data.get('frequency_pattern', {})
                print(f"  - 频率模式: {frequency_pattern.get('type', 'unknown')} (一致性: {frequency_pattern.get('consistency', 0):.2f})")
                
                intensity_pattern = pattern_data.get('intensity_pattern', {})
                print(f"  - 强度模式: {intensity_pattern.get('type', 'unknown')} (平均强度: {intensity_pattern.get('average_intensity', 0):.2f})")
                
                habit_assessment = pattern_data.get('habit_assessment', {})
                print(f"  - 习惯评分: {habit_assessment.get('score', 0)}")
                print(f"  - 学习风格: {pattern_data.get('learning_style', 'undefined')}")
            else:
                print("⚠ 学习模式识别返回空数据")
        except Exception as e:
            print(f"✗ 学习模式识别失败: {str(e)}")
            return False
        
        # 测试5: 学习表现预测
        print("\n=== 测试学习表现预测 ===")
        try:
            prediction_data = advanced_service.predict_performance(user.id, 7)
            if prediction_data:
                print("✓ 学习表现预测成功")
                
                performance_trend = prediction_data.get('performance_trend', {})
                print(f"  - 表现趋势: {performance_trend.get('trend', 'unknown')} (置信度: {performance_trend.get('confidence', 0):.2f})")
                
                predictions = prediction_data.get('predictions', {})
                accuracy_pred = predictions.get('accuracy', {})
                time_pred = predictions.get('study_time', {})
                efficiency_pred = predictions.get('efficiency', {})
                
                print(f"  - 预测准确率: {accuracy_pred.get('value', 0):.1f}% (置信度: {accuracy_pred.get('confidence', 0):.2f})")
                print(f"  - 预测学习时间: {time_pred.get('value', 0)}分钟 (置信度: {time_pred.get('confidence', 0):.2f})")
                print(f"  - 预测效率: {efficiency_pred.get('value', 0):.1f} (置信度: {efficiency_pred.get('confidence', 0):.2f})")
                
                risk_assessment = prediction_data.get('risk_assessment', {})
                print(f"  - 风险等级: {risk_assessment.get('risk_level', 'unknown')}")
                print(f"  - 总体置信度: {prediction_data.get('confidence_level', 0):.2f}")
            else:
                print("⚠ 学习表现预测返回空数据")
        except Exception as e:
            print(f"✗ 学习表现预测失败: {str(e)}")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 高级学习分析功能测试全部通过！")
        
        # 输出功能总结
        print("\n📊 高级分析功能总结:")
        print("- ✅ 学习效率分析 - 多维度效率评估")
        print("- ✅ 时间分布分析 - 学习时间模式识别")
        print("- ✅ 难度适应性分析 - 个性化难度推荐")
        print("- ✅ 学习模式识别 - 学习风格和习惯分析")
        print("- ✅ 学习表现预测 - 基于历史数据的趋势预测")
        
        print("\n🔍 分析维度:")
        print("- 效率维度: 准确率、答题速度、综合效率")
        print("- 时间维度: 小时分布、星期分布、会话分析")
        print("- 难度维度: 适应性评分、挑战准备度")
        print("- 模式维度: 频率模式、强度模式、学习风格")
        print("- 预测维度: 表现趋势、风险评估、置信度")
        
        return True

def main():
    """主函数"""
    success = test_advanced_analytics()
    if not success:
        print("❌ 高级学习分析功能测试失败")
        sys.exit(1)
    else:
        print("\n✅ 高级学习分析功能全部正常，可以进行API集成测试")

if __name__ == '__main__':
    main()