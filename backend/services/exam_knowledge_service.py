#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 服务层 - exam_knowledge_service.py

Description:
    试卷知识点映射服务，提供试卷与知识点关联分析、统计计算等功能。

Author: Chang Xinglong
Date: 2025-01-21
Version: 1.0.0
License: Apache License 2.0
"""

from typing import List, Dict, Any, Optional
from sqlalchemy import func, and_, or_
from models import (
    ExamPaper, Question, KnowledgePoint, Chapter, Subject,
    ExamKnowledgeMapping, ExamKnowledgeStatistics
)
from utils.database import db
import logging

logger = logging.getLogger(__name__)

class ExamKnowledgeService:
    """试卷知识点映射服务"""
    
    @staticmethod
    def create_mapping_for_paper(exam_paper_id: str) -> List[ExamKnowledgeMapping]:
        """为试卷创建知识点映射关系"""
        try:
            # 获取试卷信息
            exam_paper = ExamPaper.query.get(exam_paper_id)
            if not exam_paper:
                raise ValueError(f"试卷不存在: {exam_paper_id}")
            
            # 获取试卷中的所有题目
            questions = Question.query.filter_by(
                exam_paper_id=exam_paper_id,
                is_active=True
            ).all()
            
            if not questions:
                logger.warning(f"试卷 {exam_paper_id} 中没有题目")
                return []
            
            # 按知识点分组统计
            knowledge_point_stats = {}
            for question in questions:
                kp_id = question.knowledge_point_id
                if kp_id not in knowledge_point_stats:
                    knowledge_point_stats[kp_id] = {
                        'questions': [],
                        'total_score': 0,
                        'difficulties': [],
                        'choice_count': 0,
                        'fill_count': 0,
                        'essay_count': 0,
                        'other_count': 0,
                        'choice_score': 0,
                        'fill_score': 0,
                        'essay_score': 0,
                        'other_score': 0
                    }
                
                stats = knowledge_point_stats[kp_id]
                stats['questions'].append(question)
                stats['total_score'] += question.score or 0
                stats['difficulties'].append(question.difficulty or 3)
                
                # 统计题型
                if hasattr(question, 'question_type') and question.question_type:
                    category = question.question_type.category
                    if category == 'choice':
                        stats['choice_count'] += 1
                        stats['choice_score'] += question.score or 0
                    elif category == 'fill':
                        stats['fill_count'] += 1
                        stats['fill_score'] += question.score or 0
                    elif category == 'essay':
                        stats['essay_count'] += 1
                        stats['essay_score'] += question.score or 0
                    else:
                        stats['other_count'] += 1
                        stats['other_score'] += question.score or 0
            
            # 创建或更新映射关系
            mappings = []
            for kp_id, stats in knowledge_point_stats.items():
                # 检查是否已存在映射关系
                existing_mapping = ExamKnowledgeMapping.query.filter_by(
                    exam_paper_id=exam_paper_id,
                    knowledge_point_id=kp_id
                ).first()
                
                if existing_mapping:
                    mapping = existing_mapping
                else:
                    mapping = ExamKnowledgeMapping(
                        exam_paper_id=exam_paper_id,
                        knowledge_point_id=kp_id
                    )
                    db.session.add(mapping)
                
                # 更新统计信息
                mapping.question_count = len(stats['questions'])
                mapping.total_score = stats['total_score']
                mapping.avg_difficulty = sum(stats['difficulties']) / len(stats['difficulties'])
                
                mapping.choice_count = stats['choice_count']
                mapping.fill_count = stats['fill_count']
                mapping.essay_count = stats['essay_count']
                mapping.other_count = stats['other_count']
                
                mapping.choice_score = stats['choice_score']
                mapping.fill_score = stats['fill_score']
                mapping.essay_score = stats['essay_score']
                mapping.other_score = stats['other_score']
                
                # 计算重要程度权重和覆盖率
                mapping.importance_weight = mapping.calculate_importance_weight()
                if exam_paper.total_score and exam_paper.total_score > 0:
                    mapping.coverage_rate = mapping.total_score / exam_paper.total_score
                
                mappings.append(mapping)
            
            db.session.commit()
            logger.info(f"为试卷 {exam_paper_id} 创建了 {len(mappings)} 个知识点映射")
            return mappings
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建试卷知识点映射失败: {str(e)}")
            raise
    
    @staticmethod
    def update_knowledge_statistics(subject_id: str, year: Optional[int] = None, 
                                  exam_type: Optional[str] = None, 
                                  region: Optional[str] = None) -> List[ExamKnowledgeStatistics]:
        """更新知识点统计信息"""
        try:
            # 获取学科下的所有知识点
            knowledge_points = db.session.query(KnowledgePoint).join(Chapter).filter(
                Chapter.subject_id == subject_id,
                KnowledgePoint.is_active == True
            ).all()
            
            if not knowledge_points:
                logger.warning(f"学科 {subject_id} 下没有知识点")
                return []
            
            # 构建试卷查询条件
            paper_filters = {'subject_id': subject_id}
            if year:
                paper_filters['year'] = year
            if exam_type:
                paper_filters['exam_type'] = exam_type
            if region:
                paper_filters['region'] = region
            
            # 获取符合条件的试卷
            exam_papers = ExamPaper.query.filter_by(**paper_filters).all()
            total_papers = len(exam_papers)
            
            if total_papers == 0:
                logger.warning(f"没有找到符合条件的试卷")
                return []
            
            statistics_list = []
            
            for kp in knowledge_points:
                # 检查是否已存在统计记录
                existing_stats = ExamKnowledgeStatistics.query.filter_by(
                    subject_id=subject_id,
                    knowledge_point_id=kp.id,
                    year=year,
                    exam_type=exam_type,
                    region=region
                ).first()
                
                if existing_stats:
                    stats = existing_stats
                else:
                    stats = ExamKnowledgeStatistics(
                        subject_id=subject_id,
                        knowledge_point_id=kp.id,
                        year=year,
                        exam_type=exam_type,
                        region=region
                    )
                    db.session.add(stats)
                
                # 获取该知识点的所有映射关系
                exam_paper_ids = [ep.id for ep in exam_papers]
                mappings = ExamKnowledgeMapping.query.filter(
                    ExamKnowledgeMapping.knowledge_point_id == kp.id,
                    ExamKnowledgeMapping.exam_paper_id.in_(exam_paper_ids)
                ).all()
                
                # 更新统计信息
                stats.total_papers = total_papers
                stats.appeared_papers = len(mappings)
                stats.appearance_rate = stats.appeared_papers / total_papers if total_papers > 0 else 0
                
                if mappings:
                    stats.total_questions = sum(m.question_count for m in mappings)
                    stats.total_score = sum(m.total_score for m in mappings)
                    stats.avg_questions_per_paper = stats.total_questions / stats.appeared_papers
                    stats.avg_score_per_paper = stats.total_score / stats.appeared_papers
                    stats.max_score_per_paper = max(m.total_score for m in mappings)
                    
                    # 计算平均难度
                    difficulties = [m.avg_difficulty for m in mappings if m.avg_difficulty]
                    if difficulties:
                        stats.avg_difficulty = sum(difficulties) / len(difficulties)
                    
                    # 统计难度分布
                    difficulty_dist = {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0}
                    for m in mappings:
                        if m.avg_difficulty:
                            level = round(m.avg_difficulty)
                            if 1 <= level <= 5:
                                difficulty_dist[str(level)] += 1
                    stats.difficulty_distribution = difficulty_dist
                    
                    # 统计题型分布
                    type_dist = {
                        'choice': sum(m.choice_count for m in mappings),
                        'fill': sum(m.fill_count for m in mappings),
                        'essay': sum(m.essay_count for m in mappings),
                        'other': sum(m.other_count for m in mappings)
                    }
                    stats.question_type_distribution = type_dist
                    
                    # 统计分值分布
                    score_dist = {
                        'choice': sum(m.choice_score for m in mappings),
                        'fill': sum(m.fill_score for m in mappings),
                        'essay': sum(m.essay_score for m in mappings),
                        'other': sum(m.other_score for m in mappings)
                    }
                    stats.score_type_distribution = score_dist
                else:
                    # 重置统计信息
                    stats.total_questions = 0
                    stats.total_score = 0
                    stats.avg_questions_per_paper = 0
                    stats.avg_score_per_paper = 0
                    stats.max_score_per_paper = 0
                    stats.avg_difficulty = None
                    stats.difficulty_distribution = {}
                    stats.question_type_distribution = {}
                    stats.score_type_distribution = {}
                
                # 计算重要程度评分
                stats.importance_score = stats.calculate_importance_score()
                
                statistics_list.append(stats)
            
            db.session.commit()
            logger.info(f"更新了 {len(statistics_list)} 个知识点的统计信息")
            return statistics_list
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"更新知识点统计信息失败: {str(e)}")
            raise
    
    @staticmethod
    def get_star_map_data(subject_id: str, year: Optional[int] = None, 
                         exam_type: Optional[str] = None) -> Dict[str, Any]:
        """获取星图展示数据"""
        try:
            # 获取知识点统计数据
            query = ExamKnowledgeStatistics.query.filter_by(subject_id=subject_id)
            if year:
                query = query.filter_by(year=year)
            if exam_type:
                query = query.filter_by(exam_type=exam_type)
            
            statistics = query.all()
            
            # 获取学科结构
            subject = Subject.query.get(subject_id)
            if not subject:
                raise ValueError(f"学科不存在: {subject_id}")
            
            chapters = Chapter.query.filter_by(subject_id=subject_id, is_active=True).all()
            
            # 构建节点数据
            nodes = []
            edges = []
            
            # 添加学科节点
            nodes.append({
                'id': f'subject_{subject.id}',
                'name': subject.name,
                'type': 'subject',
                'level': 0,
                'importance': 5,
                'difficulty': 3,
                'examFrequency': 1.0,
                'mastery_level': 0.8,
                'question_count': 0
            })
            
            # 添加章节节点
            for chapter in chapters:
                nodes.append({
                    'id': f'chapter_{chapter.id}',
                    'name': chapter.name,
                    'type': 'chapter',
                    'level': 1,
                    'importance': chapter.importance or 3,
                    'difficulty': chapter.difficulty or 3,
                    'examFrequency': chapter.exam_frequency / 100.0 if chapter.exam_frequency else 0.0,
                    'mastery_level': 0.7,
                    'question_count': 0
                })
                
                # 添加学科到章节的边
                edges.append({
                    'source': f'subject_{subject.id}',
                    'target': f'chapter_{chapter.id}',
                    'type': 'contains',
                    'weight': 1
                })
                
                # 获取章节下的知识点
                knowledge_points = KnowledgePoint.query.filter_by(
                    chapter_id=chapter.id,
                    is_active=True
                ).all()
                
                for kp in knowledge_points:
                    # 查找对应的统计数据
                    kp_stats = next((s for s in statistics if s.knowledge_point_id == kp.id), None)
                    
                    # 计算节点属性
                    exam_frequency = kp_stats.appearance_rate if kp_stats else 0.0
                    question_count = kp_stats.total_questions if kp_stats else 0
                    importance_score = kp_stats.importance_score if kp_stats else kp.importance or 3
                    
                    nodes.append({
                        'id': f'kp_{kp.id}',
                        'name': kp.name,
                        'type': 'knowledge_point',
                        'level': 2,
                        'importance': min(5, max(1, importance_score / 20)),  # 转换为1-5范围
                        'difficulty': kp.difficulty or 3,
                        'examFrequency': exam_frequency,
                        'mastery_level': 0.6,
                        'question_count': question_count,
                        'chapter_id': chapter.id,
                        'chapter_name': chapter.name
                    })
                    
                    # 添加章节到知识点的边
                    edges.append({
                        'source': f'chapter_{chapter.id}',
                        'target': f'kp_{kp.id}',
                        'type': 'contains',
                        'weight': 1
                    })
                    
                    # 添加知识点之间的关联边
                    if kp.related_points:
                        for related_id in kp.related_points:
                            if any(rp.id == related_id for rp in knowledge_points):
                                edges.append({
                                    'source': f'kp_{kp.id}',
                                    'target': f'kp_{related_id}',
                                    'type': 'related',
                                    'weight': 0.5
                                })
            
            return {
                'nodes': nodes,
                'edges': edges,
                'metadata': {
                    'subject_id': subject_id,
                    'subject_name': subject.name,
                    'year': year,
                    'exam_type': exam_type,
                    'total_nodes': len(nodes),
                    'total_edges': len(edges),
                    'chapters_count': len(chapters),
                    'knowledge_points_count': len([n for n in nodes if n['type'] == 'knowledge_point'])
                }
            }
            
        except Exception as e:
            logger.error(f"获取星图数据失败: {str(e)}")
            raise
    
    @staticmethod
    def get_knowledge_point_questions(knowledge_point_id: str, 
                                    year: Optional[int] = None,
                                    exam_type: Optional[str] = None,
                                    limit: int = 20) -> List[Dict[str, Any]]:
        """获取知识点相关的题目"""
        try:
            # 构建查询条件
            query = Question.query.filter_by(
                knowledge_point_id=knowledge_point_id,
                is_active=True
            )
            
            # 如果指定了年份或考试类型，需要通过试卷进行过滤
            if year or exam_type:
                paper_filters = {}
                if year:
                    paper_filters['year'] = year
                if exam_type:
                    paper_filters['exam_type'] = exam_type
                
                exam_paper_ids = [ep.id for ep in ExamPaper.query.filter_by(**paper_filters).all()]
                query = query.filter(Question.exam_paper_id.in_(exam_paper_ids))
            
            questions = query.limit(limit).all()
            
            result = []
            for question in questions:
                question_data = question.to_dict(include_answer=True)
                
                # 添加试卷信息
                if question.exam_paper:
                    question_data['exam_paper'] = {
                        'id': question.exam_paper.id,
                        'title': question.exam_paper.title,
                        'year': question.exam_paper.year,
                        'exam_type': question.exam_paper.exam_type,
                        'region': question.exam_paper.region
                    }
                
                result.append(question_data)
            
            return result
            
        except Exception as e:
            logger.error(f"获取知识点题目失败: {str(e)}")
            raise
    
    @staticmethod
    def batch_update_mappings(subject_id: str) -> Dict[str, int]:
        """批量更新学科下所有试卷的映射关系"""
        try:
            # 获取学科下的所有试卷
            exam_papers = ExamPaper.query.filter_by(
                subject_id=subject_id,
                is_active=True
            ).all()
            
            updated_count = 0
            failed_count = 0
            
            for paper in exam_papers:
                try:
                    ExamKnowledgeService.create_mapping_for_paper(paper.id)
                    updated_count += 1
                except Exception as e:
                    logger.error(f"更新试卷 {paper.id} 映射失败: {str(e)}")
                    failed_count += 1
            
            # 更新统计信息
            ExamKnowledgeService.update_knowledge_statistics(subject_id)
            
            return {
                'total_papers': len(exam_papers),
                'updated_count': updated_count,
                'failed_count': failed_count
            }
            
        except Exception as e:
            logger.error(f"批量更新映射关系失败: {str(e)}")
            raise