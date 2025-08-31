#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 业务服务 - learning_path_service.py

Description:
    学习路径服务，提供个性化学习路径生成和优化。

Author: Chang Xinglong
Date: 2025-08-31
Version: 1.0.0
License: Apache License 2.0
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from models.diagnosis import DiagnosisReport, LearningProfile
from models.knowledge import KnowledgePoint, Subject
from models.user import User
from utils.database import db
from services.llm_service import LLMService
from utils.logger import get_logger
import json
import math

logger = get_logger(__name__)

class LearningPathService:
    """
    智能学习路径规划服务
    基于诊断结果、学习画像和知识图谱生成个性化学习路径
    """
    
    @staticmethod
    def generate_learning_path(user_id: str, subject_id: str, 
                             diagnosis_report_id: str = None,
                             target_level: str = 'intermediate',
                             time_budget: int = 30) -> Dict[str, Any]:
        """
        生成个性化学习路径
        
        Args:
            user_id: 用户ID
            subject_id: 学科ID
            diagnosis_report_id: 诊断报告ID（可选）
            target_level: 目标水平
            time_budget: 每日学习时间预算（分钟）
            
        Returns:
            学习路径规划
        """
        try:
            # 获取用户信息
            user = User.query.get(user_id)
            if not user:
                raise ValueError('用户不存在')
            
            # 获取学科信息
            subject = Subject.query.get(subject_id)
            if not subject:
                raise ValueError('学科不存在')
            
            # 获取诊断报告（如果有）
            diagnosis_report = None
            if diagnosis_report_id:
                diagnosis_report = DiagnosisReport.query.get(diagnosis_report_id)
            
            # 获取学习画像
            learning_profile = LearningProfile.query.filter_by(
                user_id=user_id,
                subject_id=subject_id
            ).first()
            
            # 分析当前水平和薄弱点
            current_analysis = LearningPathService._analyze_current_level(
                user_id, subject_id, diagnosis_report, learning_profile
            )
            
            # 获取知识点依赖关系
            knowledge_graph = LearningPathService._build_knowledge_graph(subject_id)
            
            # 生成学习路径
            learning_path = LearningPathService._generate_path_structure(
                current_analysis, knowledge_graph, target_level, time_budget
            )
            
            # 优化路径顺序
            optimized_path = LearningPathService._optimize_path_sequence(
                learning_path, learning_profile
            )
            
            # 生成学习计划
            study_plan = LearningPathService._generate_study_plan(
                optimized_path, time_budget
            )
            
            # 生成AI建议
            ai_recommendations = LearningPathService._generate_ai_recommendations(
                user, subject, current_analysis, optimized_path
            )
            
            return {
                'user_id': user_id,
                'subject_id': subject_id,
                'target_level': target_level,
                'current_analysis': current_analysis,
                'learning_path': optimized_path,
                'study_plan': study_plan,
                'ai_recommendations': ai_recommendations,
                'estimated_completion_time': LearningPathService._estimate_completion_time(
                    optimized_path, time_budget
                ),
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"生成学习路径失败: {e}")
            raise
    
    @staticmethod
    def _analyze_current_level(user_id: str, subject_id: str, 
                             diagnosis_report: DiagnosisReport = None,
                             learning_profile: LearningProfile = None) -> Dict[str, Any]:
        """
        分析用户当前水平
        
        Args:
            user_id: 用户ID
            subject_id: 学科ID
            diagnosis_report: 诊断报告
            learning_profile: 学习画像
            
        Returns:
            当前水平分析结果
        """
        analysis = {
            'overall_level': 'beginner',
            'mastered_knowledge_points': [],
            'weak_knowledge_points': [],
            'learning_preferences': {},
            'estimated_ability': 0.0
        }
        
        # 从诊断报告获取信息
        if diagnosis_report:
            analysis['overall_level'] = diagnosis_report.target_level or 'intermediate'
            analysis['estimated_ability'] = diagnosis_report.ability_estimate or 0.0
            
            # 分析掌握情况
            if diagnosis_report.mastery_levels:
                for kp_id, mastery_score in diagnosis_report.mastery_levels.items():
                    if mastery_score >= 0.8:
                        analysis['mastered_knowledge_points'].append(kp_id)
                    elif mastery_score <= 0.4:
                        analysis['weak_knowledge_points'].append(kp_id)
        
        # 从学习画像获取信息
        if learning_profile:
            analysis['learning_preferences'] = learning_profile.learning_preferences or {}
            
            # 更新整体水平评估
            if learning_profile.overall_level:
                analysis['overall_level'] = learning_profile.overall_level
        
        # 如果没有诊断数据，基于历史学习记录估算
        if not diagnosis_report and not learning_profile:
            analysis = LearningPathService._estimate_level_from_history(
                user_id, subject_id
            )
        
        return analysis
    
    @staticmethod
    def _estimate_level_from_history(user_id: str, subject_id: str) -> Dict[str, Any]:
        """
        基于历史学习记录估算水平
        
        Args:
            user_id: 用户ID
            subject_id: 学科ID
            
        Returns:
            估算的水平信息
        """
        # 这里可以基于用户的历史答题记录、学习时长等进行估算
        # 暂时返回默认值
        return {
            'overall_level': 'beginner',
            'mastered_knowledge_points': [],
            'weak_knowledge_points': [],
            'learning_preferences': {
                'difficulty_preference': 'medium',
                'learning_style': 'visual',
                'preferred_session_duration': 30
            },
            'estimated_ability': 0.0
        }
    
    @staticmethod
    def _build_knowledge_graph(subject_id: str) -> Dict[str, Any]:
        """
        构建知识图谱
        
        Args:
            subject_id: 学科ID
            
        Returns:
            知识图谱结构
        """
        try:
            # 获取学科下的所有知识点
            knowledge_points = KnowledgePoint.query.filter_by(
                subject_id=subject_id
            ).all()
            
            # 构建图谱结构
            graph = {
                'nodes': {},
                'edges': [],
                'levels': {}
            }
            
            # 添加节点
            for kp in knowledge_points:
                graph['nodes'][str(kp.id)] = {
                    'id': str(kp.id),
                    'name': kp.name,
                    'level': kp.level,
                    'difficulty': kp.difficulty_level,
                    'importance': kp.importance_score,
                    'prerequisites': kp.prerequisites or [],
                    'estimated_study_time': kp.estimated_study_time or 60
                }
                
                # 按层级分组
                level = kp.level
                if level not in graph['levels']:
                    graph['levels'][level] = []
                graph['levels'][level].append(str(kp.id))
            
            # 添加边（依赖关系）
            for kp in knowledge_points:
                if kp.prerequisites:
                    for prereq_id in kp.prerequisites:
                        graph['edges'].append({
                            'from': str(prereq_id),
                            'to': str(kp.id),
                            'type': 'prerequisite'
                        })
            
            return graph
            
        except Exception as e:
            logger.error(f"构建知识图谱失败: {e}")
            return {'nodes': {}, 'edges': [], 'levels': {}}
    
    @staticmethod
    def _generate_path_structure(current_analysis: Dict[str, Any],
                               knowledge_graph: Dict[str, Any],
                               target_level: str,
                               time_budget: int) -> List[Dict[str, Any]]:
        """
        生成学习路径结构
        
        Args:
            current_analysis: 当前水平分析
            knowledge_graph: 知识图谱
            target_level: 目标水平
            time_budget: 时间预算
            
        Returns:
            学习路径结构
        """
        path_structure = []
        
        # 确定需要学习的知识点
        mastered_kps = set(current_analysis['mastered_knowledge_points'])
        weak_kps = set(current_analysis['weak_knowledge_points'])
        
        # 根据目标水平确定需要覆盖的层级
        target_levels = LearningPathService._get_target_levels(target_level)
        
        # 收集需要学习的知识点
        to_learn = []
        for level in sorted(target_levels):
            if str(level) in knowledge_graph['levels']:
                for kp_id in knowledge_graph['levels'][str(level)]:
                    if kp_id not in mastered_kps:
                        kp_info = knowledge_graph['nodes'][kp_id]
                        priority = LearningPathService._calculate_priority(
                            kp_id, kp_info, weak_kps, current_analysis
                        )
                        to_learn.append({
                            'knowledge_point_id': kp_id,
                            'knowledge_point_info': kp_info,
                            'priority': priority,
                            'is_weak': kp_id in weak_kps
                        })
        
        # 按优先级和依赖关系排序
        sorted_kps = LearningPathService._sort_by_dependencies(
            to_learn, knowledge_graph
        )
        
        # 生成学习阶段
        current_stage = 1
        current_stage_time = 0
        stage_time_limit = time_budget * 7  # 每周时间限制
        
        current_stage_kps = []
        
        for kp_item in sorted_kps:
            kp_info = kp_item['knowledge_point_info']
            estimated_time = kp_info['estimated_study_time']
            
            # 检查是否需要开始新阶段
            if (current_stage_time + estimated_time > stage_time_limit and 
                current_stage_kps):
                
                # 完成当前阶段
                path_structure.append({
                    'stage': current_stage,
                    'stage_name': f'第{current_stage}阶段',
                    'knowledge_points': current_stage_kps,
                    'estimated_time': current_stage_time,
                    'learning_objectives': LearningPathService._generate_stage_objectives(
                        current_stage_kps
                    )
                })
                
                # 开始新阶段
                current_stage += 1
                current_stage_kps = []
                current_stage_time = 0
            
            # 添加到当前阶段
            current_stage_kps.append({
                'knowledge_point_id': kp_item['knowledge_point_id'],
                'name': kp_info['name'],
                'difficulty': kp_info['difficulty'],
                'estimated_time': estimated_time,
                'priority': kp_item['priority'],
                'is_weak': kp_item['is_weak'],
                'learning_resources': LearningPathService._recommend_resources(
                    kp_info, current_analysis['learning_preferences']
                ),
                'practice_strategy': LearningPathService._recommend_practice_strategy(
                    kp_info, kp_item['is_weak']
                )
            })
            current_stage_time += estimated_time
        
        # 添加最后一个阶段
        if current_stage_kps:
            path_structure.append({
                'stage': current_stage,
                'stage_name': f'第{current_stage}阶段',
                'knowledge_points': current_stage_kps,
                'estimated_time': current_stage_time,
                'learning_objectives': LearningPathService._generate_stage_objectives(
                    current_stage_kps
                )
            })
        
        return path_structure
    
    @staticmethod
    def _get_target_levels(target_level: str) -> List[int]:
        """
        根据目标水平确定需要覆盖的层级
        
        Args:
            target_level: 目标水平
            
        Returns:
            需要覆盖的层级列表
        """
        level_mapping = {
            'beginner': [1, 2],
            'intermediate': [1, 2, 3],
            'advanced': [1, 2, 3, 4],
            'expert': [1, 2, 3, 4, 5]
        }
        
        return level_mapping.get(target_level, [1, 2, 3])
    
    @staticmethod
    def _calculate_priority(kp_id: str, kp_info: Dict[str, Any], 
                          weak_kps: set, current_analysis: Dict[str, Any]) -> float:
        """
        计算知识点学习优先级
        
        Args:
            kp_id: 知识点ID
            kp_info: 知识点信息
            weak_kps: 薄弱知识点集合
            current_analysis: 当前水平分析
            
        Returns:
            优先级分数（越高越优先）
        """
        priority = 0.0
        
        # 基础优先级（重要性）
        priority += kp_info['importance'] * 0.3
        
        # 薄弱点加权
        if kp_id in weak_kps:
            priority += 0.4
        
        # 难度适配性
        user_ability = current_analysis['estimated_ability']
        difficulty_gap = abs(kp_info['difficulty'] - user_ability)
        if difficulty_gap <= 1.0:  # 难度适中
            priority += 0.2
        elif difficulty_gap > 2.0:  # 难度过高或过低
            priority -= 0.1
        
        # 前置知识点完成度
        prereq_completion = LearningPathService._calculate_prereq_completion(
            kp_info['prerequisites'], current_analysis['mastered_knowledge_points']
        )
        priority += prereq_completion * 0.1
        
        return priority
    
    @staticmethod
    def _calculate_prereq_completion(prerequisites: List[str], 
                                   mastered_kps: List[str]) -> float:
        """
        计算前置知识点完成度
        
        Args:
            prerequisites: 前置知识点列表
            mastered_kps: 已掌握知识点列表
            
        Returns:
            完成度（0-1）
        """
        if not prerequisites:
            return 1.0
        
        mastered_set = set(mastered_kps)
        completed = sum(1 for prereq in prerequisites if prereq in mastered_set)
        
        return completed / len(prerequisites)
    
    @staticmethod
    def _sort_by_dependencies(to_learn: List[Dict[str, Any]], 
                            knowledge_graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        按依赖关系和优先级排序
        
        Args:
            to_learn: 待学习知识点列表
            knowledge_graph: 知识图谱
            
        Returns:
            排序后的知识点列表
        """
        # 简化的拓扑排序
        sorted_kps = []
        remaining = to_learn.copy()
        
        while remaining:
            # 找到没有未满足依赖的知识点
            available = []
            for kp_item in remaining:
                kp_id = kp_item['knowledge_point_id']
                kp_info = knowledge_graph['nodes'][kp_id]
                prerequisites = kp_info['prerequisites']
                
                # 检查前置条件是否满足
                can_learn = True
                if prerequisites:
                    learned_ids = {item['knowledge_point_id'] for item in sorted_kps}
                    for prereq in prerequisites:
                        if prereq not in learned_ids:
                            can_learn = False
                            break
                
                if can_learn:
                    available.append(kp_item)
            
            if not available:
                # 如果没有可学习的，按优先级选择
                available = sorted(remaining, key=lambda x: x['priority'], reverse=True)[:1]
            
            # 按优先级排序可学习的知识点
            available.sort(key=lambda x: x['priority'], reverse=True)
            
            # 添加到结果中
            for kp_item in available:
                sorted_kps.append(kp_item)
                remaining.remove(kp_item)
        
        return sorted_kps
    
    @staticmethod
    def _generate_stage_objectives(stage_kps: List[Dict[str, Any]]) -> List[str]:
        """
        生成阶段学习目标
        
        Args:
            stage_kps: 阶段知识点列表
            
        Returns:
            学习目标列表
        """
        objectives = []
        
        # 按难度分组
        difficulty_groups = {}
        for kp in stage_kps:
            difficulty = kp['difficulty']
            if difficulty not in difficulty_groups:
                difficulty_groups[difficulty] = []
            difficulty_groups[difficulty].append(kp['name'])
        
        # 生成目标
        for difficulty, kp_names in difficulty_groups.items():
            if len(kp_names) == 1:
                objectives.append(f"掌握{kp_names[0]}的基本概念和应用")
            else:
                objectives.append(f"掌握{', '.join(kp_names[:3])}等{len(kp_names)}个知识点")
        
        # 添加综合目标
        if len(stage_kps) > 1:
            objectives.append("能够综合运用本阶段所学知识解决相关问题")
        
        return objectives
    
    @staticmethod
    def _recommend_resources(kp_info: Dict[str, Any], 
                           learning_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        推荐学习资源
        
        Args:
            kp_info: 知识点信息
            learning_preferences: 学习偏好
            
        Returns:
            推荐资源列表
        """
        resources = []
        
        # 基础资源
        resources.append({
            'type': 'concept',
            'title': f'{kp_info["name"]}概念讲解',
            'description': f'详细介绍{kp_info["name"]}的基本概念和原理',
            'estimated_time': 15,
            'difficulty': kp_info['difficulty']
        })
        
        # 根据学习偏好推荐
        learning_style = learning_preferences.get('learning_style', 'visual')
        
        if learning_style == 'visual':
            resources.append({
                'type': 'video',
                'title': f'{kp_info["name"]}视频教程',
                'description': '通过动画和图表直观理解概念',
                'estimated_time': 20,
                'difficulty': kp_info['difficulty']
            })
        
        if learning_style == 'hands_on':
            resources.append({
                'type': 'interactive',
                'title': f'{kp_info["name"]}互动练习',
                'description': '通过实际操作加深理解',
                'estimated_time': 25,
                'difficulty': kp_info['difficulty']
            })
        
        # 练习资源
        resources.append({
            'type': 'practice',
            'title': f'{kp_info["name"]}练习题',
            'description': '巩固知识点的基础练习',
            'estimated_time': 20,
            'difficulty': kp_info['difficulty']
        })
        
        return resources
    
    @staticmethod
    def _recommend_practice_strategy(kp_info: Dict[str, Any], 
                                   is_weak: bool) -> Dict[str, Any]:
        """
        推荐练习策略
        
        Args:
            kp_info: 知识点信息
            is_weak: 是否为薄弱点
            
        Returns:
            练习策略
        """
        strategy = {
            'practice_frequency': 'daily',
            'practice_duration': 15,
            'difficulty_progression': 'gradual',
            'review_schedule': [1, 3, 7, 14]  # 复习间隔（天）
        }
        
        if is_weak:
            # 薄弱点需要更多练习
            strategy['practice_frequency'] = 'twice_daily'
            strategy['practice_duration'] = 20
            strategy['difficulty_progression'] = 'slow'
            strategy['review_schedule'] = [1, 2, 4, 7, 14]
        
        if kp_info['difficulty'] >= 4:
            # 高难度知识点
            strategy['practice_duration'] = 25
            strategy['difficulty_progression'] = 'very_slow'
        
        return strategy
    
    @staticmethod
    def _optimize_path_sequence(learning_path: List[Dict[str, Any]], 
                              learning_profile: LearningProfile = None) -> List[Dict[str, Any]]:
        """
        优化学习路径顺序
        
        Args:
            learning_path: 原始学习路径
            learning_profile: 学习画像
            
        Returns:
            优化后的学习路径
        """
        # 基于学习画像调整顺序
        if learning_profile and learning_profile.learning_preferences:
            preferences = learning_profile.learning_preferences
            
            # 如果用户偏好从易到难
            if preferences.get('difficulty_preference') == 'easy_first':
                for stage in learning_path:
                    stage['knowledge_points'].sort(key=lambda x: x['difficulty'])
            
            # 如果用户偏好先解决薄弱点
            elif preferences.get('priority_preference') == 'weakness_first':
                for stage in learning_path:
                    stage['knowledge_points'].sort(
                        key=lambda x: (not x['is_weak'], x['difficulty'])
                    )
        
        return learning_path
    
    @staticmethod
    def _generate_study_plan(learning_path: List[Dict[str, Any]], 
                           time_budget: int) -> Dict[str, Any]:
        """
        生成学习计划
        
        Args:
            learning_path: 学习路径
            time_budget: 每日时间预算
            
        Returns:
            学习计划
        """
        total_time = sum(stage['estimated_time'] for stage in learning_path)
        total_days = math.ceil(total_time / time_budget)
        
        # 生成每日计划
        daily_plans = []
        current_day = 1
        remaining_time = time_budget
        current_stage_idx = 0
        current_kp_idx = 0
        
        while current_stage_idx < len(learning_path):
            stage = learning_path[current_stage_idx]
            
            if current_kp_idx >= len(stage['knowledge_points']):
                current_stage_idx += 1
                current_kp_idx = 0
                continue
            
            kp = stage['knowledge_points'][current_kp_idx]
            kp_time = kp['estimated_time']
            
            if remaining_time >= kp_time:
                # 当天可以完成这个知识点
                if current_day > len(daily_plans):
                    daily_plans.append({
                        'day': current_day,
                        'date': (datetime.now() + timedelta(days=current_day-1)).strftime('%Y-%m-%d'),
                        'knowledge_points': [],
                        'total_time': 0
                    })
                
                daily_plans[current_day-1]['knowledge_points'].append(kp)
                daily_plans[current_day-1]['total_time'] += kp_time
                remaining_time -= kp_time
                current_kp_idx += 1
            else:
                # 当天时间不够，开始新的一天
                current_day += 1
                remaining_time = time_budget
        
        return {
            'total_stages': len(learning_path),
            'total_days': len(daily_plans),
            'estimated_completion_date': (datetime.now() + timedelta(days=len(daily_plans))).strftime('%Y-%m-%d'),
            'daily_time_budget': time_budget,
            'total_study_time': total_time,
            'daily_plans': daily_plans
        }
    
    @staticmethod
    def _estimate_completion_time(learning_path: List[Dict[str, Any]], 
                                time_budget: int) -> Dict[str, Any]:
        """
        估算完成时间
        
        Args:
            learning_path: 学习路径
            time_budget: 每日时间预算
            
        Returns:
            完成时间估算
        """
        total_time = sum(stage['estimated_time'] for stage in learning_path)
        total_days = math.ceil(total_time / time_budget)
        total_weeks = math.ceil(total_days / 7)
        
        return {
            'total_study_time_minutes': total_time,
            'total_study_time_hours': round(total_time / 60, 1),
            'estimated_days': total_days,
            'estimated_weeks': total_weeks,
            'completion_date': (datetime.now() + timedelta(days=total_days)).strftime('%Y-%m-%d')
        }
    
    @staticmethod
    def _generate_ai_recommendations(user: User, subject: Subject, 
                                   current_analysis: Dict[str, Any],
                                   learning_path: List[Dict[str, Any]]) -> List[str]:
        """
        生成AI学习建议
        
        Args:
            user: 用户对象
            subject: 学科对象
            current_analysis: 当前水平分析
            learning_path: 学习路径
            
        Returns:
            AI建议列表
        """
        try:
            # 构建提示词
            prompt = f"""
            请为学生生成个性化学习建议。
            
            学生信息：
            - 学科：{subject.name}
            - 当前水平：{current_analysis['overall_level']}
            - 能力估计：{current_analysis['estimated_ability']}
            - 已掌握知识点数：{len(current_analysis['mastered_knowledge_points'])}
            - 薄弱知识点数：{len(current_analysis['weak_knowledge_points'])}
            
            学习路径信息：
            - 总阶段数：{len(learning_path)}
            - 预计学习时间：{sum(stage['estimated_time'] for stage in learning_path)}分钟
            
            请生成5-8条具体的学习建议，包括：
            1. 学习方法建议
            2. 时间安排建议
            3. 重点关注建议
            4. 复习策略建议
            5. 心态调整建议
            
            要求：
            - 建议要具体可操作
            - 考虑学生的当前水平
            - 语言要鼓励和积极
            """
            
            # 调用LLM生成建议
            response = LLMService.generate_content(
                prompt=prompt,
                max_tokens=500,
                temperature=0.7
            )
            
            if response and response.get('content'):
                # 解析建议
                content = response['content']
                recommendations = []
                
                # 简单的文本分割
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and (line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.')) or 
                               line.startswith(('-', '•'))):
                        # 清理格式
                        clean_line = line.lstrip('12345678.-• ').strip()
                        if clean_line:
                            recommendations.append(clean_line)
                
                return recommendations[:8]  # 最多8条建议
            
        except Exception as e:
            logger.error(f"生成AI建议失败: {e}")
        
        # 返回默认建议
        return [
            "建议每天坚持学习，保持学习的连续性和规律性",
            "重点关注薄弱知识点，通过反复练习加强理解",
            "学习新知识点时，先理解概念再进行练习",
            "定期复习已学内容，巩固记忆效果",
            "遇到困难时不要气馁，可以寻求帮助或换个角度思考",
            "保持积极的学习态度，相信自己能够不断进步"
        ]
    
    @staticmethod
    def update_learning_progress(user_id: str, subject_id: str, 
                               knowledge_point_id: str, 
                               progress_data: Dict[str, Any]) -> bool:
        """
        更新学习进度
        
        Args:
            user_id: 用户ID
            subject_id: 学科ID
            knowledge_point_id: 知识点ID
            progress_data: 进度数据
            
        Returns:
            是否更新成功
        """
        try:
            # 这里可以记录学习进度到数据库
            # 暂时只记录日志
            logger.info(f"用户 {user_id} 在学科 {subject_id} 的知识点 {knowledge_point_id} 学习进度更新: {progress_data}")
            return True
            
        except Exception as e:
            logger.error(f"更新学习进度失败: {e}")
            return False
    
    @staticmethod
    def get_learning_progress(user_id: str, subject_id: str) -> Dict[str, Any]:
        """
        获取学习进度
        
        Args:
            user_id: 用户ID
            subject_id: 学科ID
            
        Returns:
            学习进度信息
        """
        try:
            # 这里应该从数据库获取实际进度
            # 暂时返回模拟数据
            return {
                'user_id': user_id,
                'subject_id': subject_id,
                'overall_progress': 0.0,
                'completed_knowledge_points': [],
                'current_stage': 1,
                'days_studied': 0,
                'total_study_time': 0,
                'last_study_date': None
            }
            
        except Exception as e:
            logger.error(f"获取学习进度失败: {e}")
            return {}