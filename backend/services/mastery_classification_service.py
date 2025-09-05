#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 知识点掌握度分类服务

Description:
    实现知识点的红黄绿颜色分类系统，根据学习数据自动分类知识点掌握程度。

Author: Chang Xinglong
Date: 2025-01-21
Version: 1.0.0
License: Apache License 2.0
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from utils.database import db
from models.learning import StudyRecord, LearningPath
from models.knowledge import KnowledgePoint
from models.exam import ExamSession
from models.diagnosis import DiagnosisReport, WeaknessPoint
from utils.logger import get_logger

logger = get_logger(__name__)

class MasteryClassificationService:
    """
    知识点掌握度分类服务
    
    实现红黄绿三色分类系统：
    - 红色（薄弱）：掌握度 < 60%，需要重点学习
    - 黄色（待巩固）：掌握度 60-80%，需要巩固练习
    - 绿色（已掌握）：掌握度 >= 80%，已经掌握
    """
    
    # 掌握度阈值配置
    RED_THRESHOLD = 0.6      # 红色阈值：60%
    YELLOW_THRESHOLD = 0.8   # 黄色阈值：80%
    
    # 权重配置
    ACCURACY_WEIGHT = 0.4    # 正确率权重
    FREQUENCY_WEIGHT = 0.2   # 练习频率权重
    RECENT_WEIGHT = 0.3      # 近期表现权重
    CONFIDENCE_WEIGHT = 0.1  # 信心度权重
    
    def __init__(self):
        self.logger = logger
    
    def classify_knowledge_point(self, user_id: str, knowledge_point_id: str) -> Dict[str, Any]:
        """
        分类单个知识点的掌握程度
        
        Args:
            user_id: 用户ID
            knowledge_point_id: 知识点ID
            
        Returns:
            分类结果
        """
        try:
            # 获取知识点信息
            knowledge_point = KnowledgePoint.query.get(knowledge_point_id)
            if not knowledge_point:
                return self._create_default_classification(knowledge_point_id, "知识点不存在")
            
            # 计算掌握度分数
            mastery_score = self._calculate_mastery_score(user_id, knowledge_point_id)
            
            # 确定颜色分类
            color_class = self._determine_color_class(mastery_score)
            
            # 获取详细统计信息
            stats = self._get_knowledge_point_stats(user_id, knowledge_point_id)
            
            return {
                "knowledge_point_id": knowledge_point_id,
                "knowledge_point_name": knowledge_point.name,
                "mastery_score": mastery_score,
                "color_class": color_class,
                "color_name": self._get_color_name(color_class),
                "stats": stats,
                "recommendations": self._get_recommendations(color_class, stats),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"知识点分类失败 {knowledge_point_id}: {str(e)}")
            return self._create_default_classification(knowledge_point_id, str(e))
    
    def classify_user_knowledge_points(self, user_id: str, subject_id: Optional[str] = None) -> Dict[str, Any]:
        """
        分类用户的所有知识点
        
        Args:
            user_id: 用户ID
            subject_id: 学科ID（可选）
            
        Returns:
            分类结果汇总
        """
        try:
            # 获取用户相关的知识点
            knowledge_points = self._get_user_knowledge_points(user_id, subject_id)
            
            red_points = []
            yellow_points = []
            green_points = []
            
            # 分类每个知识点
            for kp in knowledge_points:
                classification = self.classify_knowledge_point(user_id, kp.id)
                
                if classification["color_class"] == "red":
                    red_points.append(classification)
                elif classification["color_class"] == "yellow":
                    yellow_points.append(classification)
                else:
                    green_points.append(classification)
            
            # 按掌握度排序
            red_points.sort(key=lambda x: x["mastery_score"])
            yellow_points.sort(key=lambda x: x["mastery_score"])
            green_points.sort(key=lambda x: x["mastery_score"], reverse=True)
            
            return {
                "user_id": user_id,
                "subject_id": subject_id,
                "total_points": len(knowledge_points),
                "red_points": red_points,
                "yellow_points": yellow_points,
                "green_points": green_points,
                "distribution": {
                    "red_count": len(red_points),
                    "yellow_count": len(yellow_points),
                    "green_count": len(green_points),
                    "red_percentage": len(red_points) / len(knowledge_points) * 100 if knowledge_points else 0,
                    "yellow_percentage": len(yellow_points) / len(knowledge_points) * 100 if knowledge_points else 0,
                    "green_percentage": len(green_points) / len(knowledge_points) * 100 if knowledge_points else 0
                },
                "overall_mastery": sum(kp["mastery_score"] for kp in red_points + yellow_points + green_points) / len(knowledge_points) if knowledge_points else 0,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"用户知识点分类失败 {user_id}: {str(e)}")
            return {
                "user_id": user_id,
                "error": str(e),
                "red_points": [],
                "yellow_points": [],
                "green_points": []
            }
    
    def update_learning_path_colors(self, user_id: str) -> bool:
        """
        更新学习路径中的颜色分类
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否更新成功
        """
        try:
            # 获取用户的学习路径
            learning_path = LearningPath.query.filter_by(user_id=user_id).first()
            if not learning_path:
                return False
            
            # 获取分类结果
            classification = self.classify_user_knowledge_points(user_id)
            
            # 更新学习路径
            learning_path.red_points = [kp["knowledge_point_id"] for kp in classification["red_points"]]
            learning_path.yellow_points = [kp["knowledge_point_id"] for kp in classification["yellow_points"]]
            learning_path.green_points = [kp["knowledge_point_id"] for kp in classification["green_points"]]
            learning_path.updated_at = datetime.now()
            
            db.session.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"更新学习路径颜色失败 {user_id}: {str(e)}")
            db.session.rollback()
            return False
    
    def _calculate_mastery_score(self, user_id: str, knowledge_point_id: str) -> float:
        """
        计算知识点掌握度分数
        
        Args:
            user_id: 用户ID
            knowledge_point_id: 知识点ID
            
        Returns:
            掌握度分数 (0-1)
        """
        try:
            # 获取学习记录
            study_records = StudyRecord.query.filter_by(
                user_id=user_id,
                knowledge_point_id=knowledge_point_id
            ).order_by(StudyRecord.created_at.desc()).limit(20).all()
            
            if not study_records:
                return 0.0
            
            # 计算正确率
            accuracy_score = sum(record.mastery_level for record in study_records) / (len(study_records) * 5)
            
            # 计算练习频率分数
            frequency_score = min(len(study_records) / 10, 1.0)  # 10次练习为满分
            
            # 计算近期表现分数
            recent_records = [r for r in study_records if r.created_at > datetime.now() - timedelta(days=7)]
            recent_score = sum(record.mastery_level for record in recent_records) / (len(recent_records) * 5) if recent_records else accuracy_score
            
            # 计算信心度分数
            confidence_score = sum(record.confidence_level for record in study_records) / (len(study_records) * 5) if study_records else 0.5
            
            # 加权计算总分
            total_score = (
                accuracy_score * self.ACCURACY_WEIGHT +
                frequency_score * self.FREQUENCY_WEIGHT +
                recent_score * self.RECENT_WEIGHT +
                confidence_score * self.CONFIDENCE_WEIGHT
            )
            
            return min(max(total_score, 0.0), 1.0)
            
        except Exception as e:
            self.logger.error(f"计算掌握度分数失败 {knowledge_point_id}: {str(e)}")
            return 0.0
    
    def _determine_color_class(self, mastery_score: float) -> str:
        """
        根据掌握度分数确定颜色分类
        
        Args:
            mastery_score: 掌握度分数
            
        Returns:
            颜色分类
        """
        if mastery_score >= self.YELLOW_THRESHOLD:
            return "green"
        elif mastery_score >= self.RED_THRESHOLD:
            return "yellow"
        else:
            return "red"
    
    def _get_color_name(self, color_class: str) -> str:
        """
        获取颜色中文名称
        
        Args:
            color_class: 颜色分类
            
        Returns:
            中文名称
        """
        color_names = {
            "red": "薄弱",
            "yellow": "待巩固",
            "green": "已掌握"
        }
        return color_names.get(color_class, "未知")
    
    def _get_knowledge_point_stats(self, user_id: str, knowledge_point_id: str) -> Dict[str, Any]:
        """
        获取知识点统计信息
        
        Args:
            user_id: 用户ID
            knowledge_point_id: 知识点ID
            
        Returns:
            统计信息
        """
        try:
            study_records = StudyRecord.query.filter_by(
                user_id=user_id,
                knowledge_point_id=knowledge_point_id
            ).all()
            
            if not study_records:
                return {
                    "total_attempts": 0,
                    "average_mastery": 0,
                    "last_study_date": None,
                    "study_frequency": 0
                }
            
            return {
                "total_attempts": len(study_records),
                "average_mastery": sum(r.mastery_level for r in study_records) / len(study_records),
                "last_study_date": max(r.created_at for r in study_records).isoformat(),
                "study_frequency": len([r for r in study_records if r.created_at > datetime.now() - timedelta(days=30)])
            }
            
        except Exception as e:
            self.logger.error(f"获取知识点统计失败 {knowledge_point_id}: {str(e)}")
            return {}
    
    def _get_recommendations(self, color_class: str, stats: Dict[str, Any]) -> List[str]:
        """
        根据颜色分类获取学习建议
        
        Args:
            color_class: 颜色分类
            stats: 统计信息
            
        Returns:
            学习建议列表
        """
        recommendations = []
        
        if color_class == "red":
            recommendations.extend([
                "建议重点学习该知识点的基础概念",
                "多做相关的基础练习题",
                "寻求老师或同学的帮助",
                "观看相关的教学视频"
            ])
        elif color_class == "yellow":
            recommendations.extend([
                "继续巩固练习，提高熟练度",
                "尝试更有挑战性的题目",
                "总结解题方法和技巧",
                "定期复习以保持掌握程度"
            ])
        else:  # green
            recommendations.extend([
                "保持定期复习以维持掌握水平",
                "可以尝试帮助其他同学学习",
                "探索该知识点的深层应用",
                "关注相关的拓展知识"
            ])
        
        # 根据统计信息添加个性化建议
        if stats.get("study_frequency", 0) < 3:
            recommendations.append("建议增加学习频率，每周至少练习3次")
        
        return recommendations
    
    def _get_user_knowledge_points(self, user_id: str, subject_id: Optional[str] = None) -> List[KnowledgePoint]:
        """
        获取用户相关的知识点
        
        Args:
            user_id: 用户ID
            subject_id: 学科ID
            
        Returns:
            知识点列表
        """
        try:
            # 从学习记录中获取用户接触过的知识点
            study_records = StudyRecord.query.filter_by(user_id=user_id).all()
            knowledge_point_ids = list(set(record.knowledge_point_id for record in study_records if record.knowledge_point_id))
            
            query = KnowledgePoint.query.filter(KnowledgePoint.id.in_(knowledge_point_ids))
            
            if subject_id:
                query = query.filter_by(subject_id=subject_id)
            
            return query.all()
            
        except Exception as e:
            self.logger.error(f"获取用户知识点失败 {user_id}: {str(e)}")
            return []
    
    def _create_default_classification(self, knowledge_point_id: str, error_msg: str) -> Dict[str, Any]:
        """
        创建默认分类结果
        
        Args:
            knowledge_point_id: 知识点ID
            error_msg: 错误信息
            
        Returns:
            默认分类结果
        """
        return {
            "knowledge_point_id": knowledge_point_id,
            "knowledge_point_name": "未知知识点",
            "mastery_score": 0.0,
            "color_class": "red",
            "color_name": "薄弱",
            "stats": {},
            "recommendations": ["暂无数据，建议开始学习"],
            "error": error_msg,
            "last_updated": datetime.now().isoformat()
        }

# 创建服务实例
mastery_classification_service = MasteryClassificationService()