#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 知识图谱生成服务

Description:
    基于大纲内容生成结构化的知识图谱，建立知识点间的关联关系。

Author: Chang Xinglong
Date: 2025-01-21
Version: 1.0.0
License: Apache License 2.0
"""

import os
import json
import math
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime
from utils.logger import get_logger
from collections import defaultdict
import networkx as nx

logger = get_logger(__name__)

class KnowledgeGraphGenerator:
    """知识图谱生成器"""
    
    def __init__(self):
        self.graph = nx.DiGraph()  # 有向图
        self.node_types = {
            'subject': '学科',
            'chapter': '章节',
            'section': '小节',
            'knowledge_point': '知识点',
            'concept': '概念',
            'skill': '技能'
        }
        
        self.relation_types = {
            'contains': '包含',
            'prerequisite': '前置依赖',
            'related': '相关',
            'applies_to': '应用于',
            'extends': '扩展',
            'similar': '相似'
        }
        
        # 关键词相似度阈值
        self.similarity_threshold = 0.3
        
        # 学科特定的关联规则
        self.subject_rules = {
            'mathematics': {
                'prerequisite_keywords': ['基础', '定义', '概念', '公式'],
                'application_keywords': ['应用', '解题', '计算', '证明'],
                'concept_patterns': ['定理', '公式', '法则', '性质']
            },
            'chinese': {
                'prerequisite_keywords': ['字词', '语法', '基础'],
                'application_keywords': ['写作', '阅读', '理解', '分析'],
                'concept_patterns': ['修辞', '文体', '语法', '句式']
            },
            'english': {
                'prerequisite_keywords': ['词汇', '语法', '基础'],
                'application_keywords': ['听说', '读写', '交际', '应用'],
                'concept_patterns': ['时态', '语态', '句型', '语法']
            }
        }
    
    def generate_knowledge_graph(self, parsed_structure: Dict, subject_code: str) -> Dict:
        """生成知识图谱"""
        try:
            logger.info(f"开始生成 {subject_code} 知识图谱")
            
            # 清空之前的图
            self.graph.clear()
            
            # 添加学科根节点
            subject_node = f"subject_{subject_code}"
            self.graph.add_node(subject_node, 
                              type='subject',
                              name=subject_code,
                              level=0)
            
            # 添加章节节点
            chapter_nodes = self._add_chapter_nodes(parsed_structure.get('chapters', []), subject_node)
            
            # 添加小节节点
            section_nodes = self._add_section_nodes(parsed_structure.get('sections', []), chapter_nodes)
            
            # 添加知识点节点
            kp_nodes = self._add_knowledge_point_nodes(parsed_structure.get('knowledge_points', []), 
                                                     chapter_nodes, section_nodes)
            
            # 建立层次关系
            self._build_hierarchical_relations(subject_node, chapter_nodes, section_nodes, kp_nodes)
            
            # 建立知识点间的关联关系
            self._build_knowledge_relations(parsed_structure.get('knowledge_points', []), subject_code)
            
            # 计算图的统计信息
            graph_stats = self._calculate_graph_statistics()
            
            # 生成图的布局坐标
            layout = self._generate_layout()
            
            # 导出图数据
            graph_data = self._export_graph_data(layout)
            
            return {
                'success': True,
                'subject_code': subject_code,
                'graph_data': graph_data,
                'statistics': graph_stats,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"生成知识图谱失败: {str(e)}")
            return {
                'success': False,
                'message': f'生成失败: {str(e)}',
                'error': str(e)
            }
    
    def _add_chapter_nodes(self, chapters: List[Dict], subject_node: str) -> Dict[int, str]:
        """添加章节节点"""
        chapter_nodes = {}
        
        for chapter in chapters:
            chapter_id = chapter.get('id')
            chapter_title = chapter.get('title', f'Chapter {chapter_id}')
            
            node_id = f"chapter_{chapter_id}"
            self.graph.add_node(node_id,
                              type='chapter',
                              name=chapter_title,
                              level=1,
                              original_id=chapter_id)
            
            # 添加与学科的包含关系
            self.graph.add_edge(subject_node, node_id, relation='contains')
            
            chapter_nodes[chapter_id] = node_id
        
        return chapter_nodes
    
    def _add_section_nodes(self, sections: List[Dict], chapter_nodes: Dict[int, str]) -> Dict[int, str]:
        """添加小节节点"""
        section_nodes = {}
        
        for section in sections:
            section_id = section.get('id')
            section_title = section.get('title', f'Section {section_id}')
            chapter_id = section.get('chapter_id')
            
            node_id = f"section_{section_id}"
            self.graph.add_node(node_id,
                              type='section',
                              name=section_title,
                              level=2,
                              original_id=section_id,
                              chapter_id=chapter_id)
            
            # 添加与章节的包含关系
            if chapter_id and chapter_id in chapter_nodes:
                self.graph.add_edge(chapter_nodes[chapter_id], node_id, relation='contains')
            
            section_nodes[section_id] = node_id
        
        return section_nodes
    
    def _add_knowledge_point_nodes(self, knowledge_points: List[Dict], 
                                 chapter_nodes: Dict[int, str], 
                                 section_nodes: Dict[int, str]) -> Dict[int, str]:
        """添加知识点节点"""
        kp_nodes = {}
        
        for kp in knowledge_points:
            kp_id = kp.get('id')
            kp_content = kp.get('content', f'Knowledge Point {kp_id}')
            chapter_id = kp.get('chapter_id')
            section_id = kp.get('section_id')
            difficulty_level = kp.get('difficulty_level', 'unknown')
            keywords = kp.get('keywords', [])
            
            node_id = f"kp_{kp_id}"
            self.graph.add_node(node_id,
                              type='knowledge_point',
                              name=kp_content,
                              level=3,
                              original_id=kp_id,
                              chapter_id=chapter_id,
                              section_id=section_id,
                              difficulty_level=difficulty_level,
                              keywords=keywords)
            
            # 添加与章节或小节的包含关系
            if section_id and section_id in section_nodes:
                self.graph.add_edge(section_nodes[section_id], node_id, relation='contains')
            elif chapter_id and chapter_id in chapter_nodes:
                self.graph.add_edge(chapter_nodes[chapter_id], node_id, relation='contains')
            
            kp_nodes[kp_id] = node_id
        
        return kp_nodes
    
    def _build_hierarchical_relations(self, subject_node: str, chapter_nodes: Dict, 
                                    section_nodes: Dict, kp_nodes: Dict):
        """建立层次关系"""
        # 层次关系已在添加节点时建立，这里可以添加额外的层次逻辑
        pass
    
    def _build_knowledge_relations(self, knowledge_points: List[Dict], subject_code: str):
        """建立知识点间的关联关系"""
        try:
            # 获取学科特定规则
            rules = self.subject_rules.get(subject_code, {})
            
            # 建立前置依赖关系
            self._build_prerequisite_relations(knowledge_points, rules)
            
            # 建立相似关系
            self._build_similarity_relations(knowledge_points)
            
            # 建立应用关系
            self._build_application_relations(knowledge_points, rules)
            
        except Exception as e:
            logger.error(f"建立知识关联关系失败: {str(e)}")
    
    def _build_prerequisite_relations(self, knowledge_points: List[Dict], rules: Dict):
        """建立前置依赖关系"""
        prerequisite_keywords = rules.get('prerequisite_keywords', [])
        
        for i, kp1 in enumerate(knowledge_points):
            for j, kp2 in enumerate(knowledge_points):
                if i == j:
                    continue
                
                kp1_content = kp1.get('content', '').lower()
                kp2_content = kp2.get('content', '').lower()
                
                # 检查是否存在前置依赖关系
                is_prerequisite = False
                
                # 基于关键词判断
                for keyword in prerequisite_keywords:
                    if keyword in kp1_content and keyword not in kp2_content:
                        is_prerequisite = True
                        break
                
                # 基于难度等级判断
                kp1_difficulty = self._get_difficulty_score(kp1.get('difficulty_level', 'unknown'))
                kp2_difficulty = self._get_difficulty_score(kp2.get('difficulty_level', 'unknown'))
                
                if kp1_difficulty < kp2_difficulty and kp1_difficulty > 0:
                    # 检查内容相关性
                    similarity = self._calculate_content_similarity(kp1_content, kp2_content)
                    if similarity > self.similarity_threshold:
                        is_prerequisite = True
                
                if is_prerequisite:
                    kp1_node = f"kp_{kp1.get('id')}"
                    kp2_node = f"kp_{kp2.get('id')}"
                    if self.graph.has_node(kp1_node) and self.graph.has_node(kp2_node):
                        self.graph.add_edge(kp1_node, kp2_node, relation='prerequisite')
    
    def _build_similarity_relations(self, knowledge_points: List[Dict]):
        """建立相似关系"""
        for i, kp1 in enumerate(knowledge_points):
            for j, kp2 in enumerate(knowledge_points):
                if i >= j:  # 避免重复和自环
                    continue
                
                # 计算内容相似度
                similarity = self._calculate_content_similarity(
                    kp1.get('content', ''), kp2.get('content', '')
                )
                
                # 计算关键词相似度
                keyword_similarity = self._calculate_keyword_similarity(
                    kp1.get('keywords', []), kp2.get('keywords', [])
                )
                
                # 综合相似度
                total_similarity = (similarity + keyword_similarity) / 2
                
                if total_similarity > self.similarity_threshold:
                    kp1_node = f"kp_{kp1.get('id')}"
                    kp2_node = f"kp_{kp2.get('id')}"
                    if self.graph.has_node(kp1_node) and self.graph.has_node(kp2_node):
                        self.graph.add_edge(kp1_node, kp2_node, 
                                          relation='similar', 
                                          weight=total_similarity)
    
    def _build_application_relations(self, knowledge_points: List[Dict], rules: Dict):
        """建立应用关系"""
        application_keywords = rules.get('application_keywords', [])
        
        for i, kp1 in enumerate(knowledge_points):
            for j, kp2 in enumerate(knowledge_points):
                if i == j:
                    continue
                
                kp1_content = kp1.get('content', '').lower()
                kp2_content = kp2.get('content', '').lower()
                
                # 检查应用关系
                is_application = False
                
                for keyword in application_keywords:
                    if keyword in kp2_content and keyword not in kp1_content:
                        # kp1是基础概念，kp2是应用
                        similarity = self._calculate_content_similarity(kp1_content, kp2_content)
                        if similarity > self.similarity_threshold:
                            is_application = True
                            break
                
                if is_application:
                    kp1_node = f"kp_{kp1.get('id')}"
                    kp2_node = f"kp_{kp2.get('id')}"
                    if self.graph.has_node(kp1_node) and self.graph.has_node(kp2_node):
                        self.graph.add_edge(kp1_node, kp2_node, relation='applies_to')
    
    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """计算内容相似度"""
        try:
            # 简单的基于共同词汇的相似度计算
            words1 = set(content1.lower().split())
            words2 = set(content2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
            
        except Exception as e:
            logger.error(f"计算内容相似度失败: {str(e)}")
            return 0.0
    
    def _calculate_keyword_similarity(self, keywords1: List[str], keywords2: List[str]) -> float:
        """计算关键词相似度"""
        try:
            if not keywords1 or not keywords2:
                return 0.0
            
            set1 = set(keywords1)
            set2 = set(keywords2)
            
            intersection = set1.intersection(set2)
            union = set1.union(set2)
            
            return len(intersection) / len(union) if union else 0.0
            
        except Exception as e:
            logger.error(f"计算关键词相似度失败: {str(e)}")
            return 0.0
    
    def _get_difficulty_score(self, difficulty_level: str) -> int:
        """获取难度分数"""
        difficulty_scores = {
            '了解': 1,
            '理解': 2,
            '掌握': 3,
            '运用': 4,
            '分析': 5,
            '综合': 6,
            '评价': 7,
            'unknown': 0
        }
        return difficulty_scores.get(difficulty_level, 0)
    
    def _calculate_graph_statistics(self) -> Dict:
        """计算图的统计信息"""
        try:
            stats = {
                'total_nodes': self.graph.number_of_nodes(),
                'total_edges': self.graph.number_of_edges(),
                'node_types': {},
                'relation_types': {},
                'avg_degree': 0,
                'density': 0,
                'connected_components': 0
            }
            
            # 统计节点类型
            node_type_counts = defaultdict(int)
            for node, data in self.graph.nodes(data=True):
                node_type = data.get('type', 'unknown')
                node_type_counts[node_type] += 1
            stats['node_types'] = dict(node_type_counts)
            
            # 统计关系类型
            relation_type_counts = defaultdict(int)
            for u, v, data in self.graph.edges(data=True):
                relation = data.get('relation', 'unknown')
                relation_type_counts[relation] += 1
            stats['relation_types'] = dict(relation_type_counts)
            
            # 计算平均度数 (使用边数估算)
            if stats['total_nodes'] > 0:
                # 对于有向图，每条边贡献2个度数（入度+出度）
                stats['avg_degree'] = (2 * stats['total_edges']) / stats['total_nodes']
            
            # 计算密度
            if stats['total_nodes'] > 1:
                max_edges = stats['total_nodes'] * (stats['total_nodes'] - 1)
                stats['density'] = stats['total_edges'] / max_edges
            
            # 计算连通分量数（转为无向图）
            undirected_graph = self.graph.to_undirected()
            stats['connected_components'] = nx.number_connected_components(undirected_graph)
            
            return stats
            
        except Exception as e:
            logger.error(f"计算图统计信息失败: {str(e)}")
            return {}
    
    def _generate_layout(self) -> Dict:
        """生成图的布局坐标"""
        try:
            # 使用层次布局
            pos = self._hierarchical_layout()
            
            # 转换为字典格式
            layout = {}
            for node, (x, y) in pos.items():
                layout[node] = {'x': float(x), 'y': float(y)}
            
            return layout
            
        except Exception as e:
            logger.error(f"生成布局失败: {str(e)}")
            return {}
    
    def _hierarchical_layout(self) -> Dict:
        """层次布局算法"""
        try:
            pos = {}
            
            # 按层级分组节点
            levels = defaultdict(list)
            for node, data in self.graph.nodes(data=True):
                level = data.get('level', 0)
                levels[level].append(node)
            
            # 为每层分配坐标
            y_spacing = 200  # 层间距
            x_spacing = 150  # 节点间距
            
            for level, nodes in levels.items():
                y = -level * y_spacing  # 从上到下
                
                # 计算x坐标，使节点居中分布
                total_width = (len(nodes) - 1) * x_spacing
                start_x = -total_width / 2
                
                for i, node in enumerate(nodes):
                    x = start_x + i * x_spacing
                    pos[node] = (x, y)
            
            return pos
            
        except Exception as e:
            logger.error(f"层次布局失败: {str(e)}")
            return dict(nx.spring_layout(self.graph))
    
    def _export_graph_data(self, layout: Dict) -> Dict:
        """导出图数据"""
        try:
            # 导出节点数据
            nodes = []
            for node, data in self.graph.nodes(data=True):
                node_data = {
                    'id': node,
                    'name': data.get('name', node),
                    'type': data.get('type', 'unknown'),
                    'level': data.get('level', 0),
                    'position': layout.get(node, {'x': 0, 'y': 0})
                }
                
                # 添加其他属性
                for key, value in data.items():
                    if key not in ['name', 'type', 'level']:
                        node_data[key] = value
                
                nodes.append(node_data)
            
            # 导出边数据
            edges = []
            for u, v, data in self.graph.edges(data=True):
                edge_data = {
                    'source': u,
                    'target': v,
                    'relation': data.get('relation', 'unknown'),
                    'weight': data.get('weight', 1.0)
                }
                
                # 添加其他属性
                for key, value in data.items():
                    if key not in ['relation', 'weight']:
                        edge_data[key] = value
                
                edges.append(edge_data)
            
            return {
                'nodes': nodes,
                'edges': edges,
                'metadata': {
                    'node_count': len(nodes),
                    'edge_count': len(edges),
                    'generated_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"导出图数据失败: {str(e)}")
            return {'nodes': [], 'edges': [], 'metadata': {}}
    
    def save_knowledge_graph(self, graph_data: Dict, output_path: str) -> bool:
        """保存知识图谱"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(graph_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"知识图谱已保存到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存知识图谱失败: {str(e)}")
            return False
    
    def load_knowledge_graph(self, file_path: str) -> Optional[Dict]:
        """加载知识图谱"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                graph_data = json.load(f)
            
            logger.info(f"知识图谱已从 {file_path} 加载")
            return graph_data
            
        except Exception as e:
            logger.error(f"加载知识图谱失败: {str(e)}")
            return None