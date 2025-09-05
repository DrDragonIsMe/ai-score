from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from models.knowledge import KnowledgePoint, Subject
from models.document import Document
from models.user import User
from services.mastery_classification_service import mastery_classification_service
from services.document_service import document_service
from utils.database import db
from utils.logger import get_logger
import json
import re
from collections import defaultdict

logger = get_logger(__name__)

class KnowledgeGraphService:
    """
    知识图谱服务
    负责自动生成知识图谱，管理考点星图，支持红黄绿分类显示
    """
    
    @staticmethod
    def generate_knowledge_graph(subject_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        生成知识图谱
        
        Args:
            subject_id: 学科ID
            user_id: 用户ID（可选，用于个性化显示）
            
        Returns:
            知识图谱数据
        """
        try:
            # 获取学科信息
            subject = Subject.query.get(subject_id)
            if not subject:
                raise ValueError(f"Subject {subject_id} not found")
            
            # 获取该学科的所有知识点
            knowledge_points = KnowledgePoint.query.filter_by(
                subject_id=subject_id
            ).all()
            
            # 构建知识点节点
            nodes = {}
            edges = []
            
            for kp in knowledge_points:
                # 获取掌握程度颜色分类
                mastery_color = 'gray'  # 默认未学习
                mastery_score = 0.0
                
                if user_id:
                    mastery_level = mastery_classification_service.classify_knowledge_point(
                        user_id, str(kp.id)
                    )
                    mastery_color = mastery_level
                    # 暂时使用默认分数，后续可以从实际数据计算
                    mastery_score = 0.7 if mastery_level == 'green' else (
                        0.5 if mastery_level == 'yellow' else 0.3
                    )
                
                nodes[str(kp.id)] = {
                    'id': str(kp.id),
                    'name': kp.name,
                    'description': kp.description or '',
                    'difficulty': kp.difficulty or 'medium',
                    'importance': kp.importance or 0.5,
                    'mastery_color': mastery_color,
                    'mastery_score': mastery_score,
                    'category': kp.category or 'general',
                    'tags': kp.tags or [],
                    'estimated_study_time': kp.estimated_study_time or 30,
                    'prerequisites': kp.prerequisites or [],
                    'related_documents': KnowledgeGraphService._get_related_documents(
                        str(kp.id), subject_id
                    )
                }
                
                # 构建依赖关系边
                if kp.prerequisites:
                    for prereq_id in kp.prerequisites:
                        edges.append({
                            'source': str(prereq_id),
                            'target': str(kp.id),
                            'type': 'prerequisite',
                            'weight': 1.0
                        })
            
            # 按层级组织知识点
            levels = KnowledgeGraphService._organize_by_levels(nodes, edges)
            
            # 生成星图布局
            star_map = KnowledgeGraphService._generate_star_map_layout(
                nodes, levels, user_id
            )
            
            return {
                'subject_id': subject_id,
                'subject_name': subject.name,
                'nodes': nodes,
                'edges': edges,
                'levels': levels,
                'star_map': star_map,
                'statistics': KnowledgeGraphService._calculate_statistics(
                    nodes, user_id
                ),
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating knowledge graph: {str(e)}")
            raise
    
    @staticmethod
    def _get_related_documents(knowledge_point_id: str, subject_id: str) -> List[Dict[str, Any]]:
        """
        获取与知识点相关的文档
        
        Args:
            knowledge_point_id: 知识点ID
            subject_id: 学科ID
            
        Returns:
            相关文档列表
        """
        try:
            # 通过标签和内容搜索相关文档
            from services.document_service import DocumentService
            doc_service = DocumentService()
            documents = doc_service.search_documents(
                query=f"knowledge_point_{knowledge_point_id}",
                user_id="system",  # 系统查询
                tenant_id="default",
                subject_filter=subject_id,
                limit=10
            )
            
            related_docs = []
            for doc in documents:
                related_docs.append({
                    'id': str(doc.get('id', '')),
                    'title': doc.get('title', ''),
                    'type': doc.get('document_type', 'document'),
                    'tags': doc.get('tags', []),
                    'upload_date': doc.get('created_at')
                })
            
            return related_docs
            
        except Exception as e:
            logger.error(f"Error getting related documents: {str(e)}")
            return []
    
    @staticmethod
    def _organize_by_levels(nodes: Dict[str, Any], edges: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        按层级组织知识点
        
        Args:
            nodes: 知识点节点
            edges: 依赖关系边
            
        Returns:
            按层级组织的知识点
        """
        # 构建依赖图
        dependencies = defaultdict(set)
        dependents = defaultdict(set)
        
        for edge in edges:
            if edge['type'] == 'prerequisite':
                dependencies[edge['target']].add(edge['source'])
                dependents[edge['source']].add(edge['target'])
        
        # 拓扑排序确定层级
        levels = defaultdict(list)
        visited = set()
        
        def calculate_level(node_id: str) -> int:
            if node_id in visited:
                return 0
            
            visited.add(node_id)
            
            if node_id not in dependencies or not dependencies[node_id]:
                return 0
            
            max_prereq_level = 0
            for prereq_id in dependencies[node_id]:
                prereq_level = calculate_level(prereq_id)
                max_prereq_level = max(max_prereq_level, prereq_level)
            
            return max_prereq_level + 1
        
        # 计算每个节点的层级
        for node_id in nodes:
            level = calculate_level(node_id)
            levels[str(level)].append(node_id)
        
        return dict(levels)
    
    @staticmethod
    def _generate_star_map_layout(nodes: Dict[str, Any], levels: Dict[str, List[str]], 
                                user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        生成星图布局
        
        Args:
            nodes: 知识点节点
            levels: 层级信息
            user_id: 用户ID
            
        Returns:
            星图布局数据
        """
        import math
        
        star_map = {
            'center': {'x': 0, 'y': 0},
            'nodes': {},
            'clusters': {}
        }
        
        # 按颜色分类节点
        color_clusters = {
            'red': [],    # 薄弱
            'yellow': [], # 待巩固
            'green': [],  # 已掌握
            'gray': []    # 未学习
        }
        
        for node_id, node_data in nodes.items():
            color = node_data.get('mastery_color', 'gray')
            color_clusters[color].append(node_id)
        
        # 为每个颜色分类生成圆形布局
        radius_base = 100
        angle_offset = 0
        
        for color, node_ids in color_clusters.items():
            if not node_ids:
                continue
            
            cluster_radius = radius_base + len(color_clusters[color]) * 10
            angle_step = 2 * math.pi / max(len(node_ids), 1)
            
            cluster_center_x = cluster_radius * math.cos(angle_offset)
            cluster_center_y = cluster_radius * math.sin(angle_offset)
            
            star_map['clusters'][color] = {
                'center': {'x': cluster_center_x, 'y': cluster_center_y},
                'radius': 50,
                'color': color,
                'count': len(node_ids)
            }
            
            # 在集群内部排列节点
            for i, node_id in enumerate(node_ids):
                angle = i * angle_step
                node_x = cluster_center_x + 30 * math.cos(angle)
                node_y = cluster_center_y + 30 * math.sin(angle)
                
                star_map['nodes'][node_id] = {
                    'x': node_x,
                    'y': node_y,
                    'color': color,
                    'size': 10 + nodes[node_id].get('importance', 0.5) * 10
                }
            
            angle_offset += math.pi / 2  # 每个集群间隔90度
        
        return star_map
    
    @staticmethod
    def _calculate_statistics(nodes: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        计算知识图谱统计信息
        
        Args:
            nodes: 知识点节点
            user_id: 用户ID
            
        Returns:
            统计信息
        """
        total_count = len(nodes)
        color_counts = {
            'red': 0,
            'yellow': 0,
            'green': 0,
            'gray': 0
        }
        
        total_mastery_score = 0.0
        
        for node_data in nodes.values():
            color = node_data.get('mastery_color', 'gray')
            if color in color_counts:
                color_counts[color] += 1
            
            total_mastery_score += node_data.get('mastery_score', 0.0)
        
        average_mastery = total_mastery_score / max(total_count, 1)
        
        return {
            'total_knowledge_points': total_count,
            'mastery_distribution': color_counts,
            'mastery_percentages': {
                color: (count / max(total_count, 1)) * 100
                for color, count in color_counts.items()
            },
            'average_mastery_score': round(average_mastery, 2),
            'completion_rate': round(
                (color_counts['green'] / max(total_count, 1)) * 100, 2
            )
        }
    
    @staticmethod
    def update_knowledge_point_from_document(document_id: str) -> bool:
        """
        从文档中提取并更新知识点
        
        Args:
            document_id: 文档ID
            
        Returns:
            是否成功更新
        """
        try:
            document = Document.query.get(document_id)
            if not document:
                return False
            
            # 从文档标签中提取知识点
            if document.tags:
                for tag in document.tags:
                    if tag.startswith('knowledge_point_'):
                        kp_id = tag.replace('knowledge_point_', '')
                        # 这里可以添加更新知识点信息的逻辑
                        pass
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating knowledge point from document: {str(e)}")
            return False
    
    @staticmethod
    def get_exam_tested_points(subject_id: str, user_id: str) -> List[Dict[str, Any]]:
        """
        获取考试考过的考点
        
        Args:
            subject_id: 学科ID
            user_id: 用户ID
            
        Returns:
            考试考过的考点列表
        """
        try:
            # 这里应该从考试记录中获取考过的考点
            # 暂时返回示例数据
            tested_points = []
            
            # 获取该学科的知识点
            knowledge_points = KnowledgePoint.query.filter_by(
                subject_id=subject_id
            ).all()
            
            for kp in knowledge_points:
                # 检查是否在考试中出现过
                # 这里需要根据实际的考试记录表来查询
                mastery_level = mastery_classification_service.classify_knowledge_point(
                    user_id, str(kp.id)
                )
                
                tested_points.append({
                    'knowledge_point_id': str(kp.id),
                    'name': kp.name,
                    'mastery_color': mastery_level,
                    'last_tested': None,  # 最后考试时间
                    'test_frequency': 0,  # 考试频次
                    'average_score': 0.0  # 平均得分
                })
            
            return tested_points
            
        except Exception as e:
            logger.error(f"Error getting exam tested points: {str(e)}")
            return []

# 创建服务实例
knowledge_graph_service = KnowledgeGraphService()