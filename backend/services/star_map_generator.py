#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 星图可视化生成服务

Description:
    创建星图可视化展示，将知识点以星座形式呈现。

Author: Chang Xinglong
Date: 2025-08-31
Version: 1.0.0
License: Apache License 2.0
"""

import os
import json
import math
import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

class StarMapGenerator:
    """星图生成器"""
    
    def __init__(self):
        self.canvas_width = 1200
        self.canvas_height = 800
        self.star_sizes = {
            'subject': 20,
            'chapter': 15,
            'section': 12,
            'knowledge_point': 8,
            'concept': 6
        }
        
        self.star_colors = {
            'subject': '#FFD700',      # 金色 - 太阳
            'chapter': '#FF6B6B',      # 红色 - 红巨星
            'section': '#4ECDC4',      # 青色 - 蓝巨星
            'knowledge_point': '#45B7D1',  # 蓝色 - 主序星
            'concept': '#96CEB4',      # 绿色 - 白矮星
            'default': '#FFFFFF'       # 白色 - 默认
        }
        
        self.constellation_patterns = {
            'mathematics': {
                'name': '数学座',
                'main_stars': ['函数', '几何', '代数', '统计'],
                'pattern': 'square'  # 正方形排列
            },
            'chinese': {
                'name': '文学座',
                'main_stars': ['阅读', '写作', '语法', '文学'],
                'pattern': 'circle'  # 圆形排列
            },
            'english': {
                'name': '英语座',
                'main_stars': ['听力', '口语', '阅读', '写作'],
                'pattern': 'diamond'  # 菱形排列
            },
            'physics': {
                'name': '物理座',
                'main_stars': ['力学', '热学', '电学', '光学'],
                'pattern': 'line'  # 直线排列
            },
            'chemistry': {
                'name': '化学座',
                'main_stars': ['无机', '有机', '物化', '分析'],
                'pattern': 'triangle'  # 三角形排列
            }
        }
        
        # 星座连线样式
        self.constellation_lines = {
            'color': '#4A90E2',
            'width': 2,
            'opacity': 0.6
        }
        
        # 知识路径样式
        self.learning_paths = {
            'prerequisite': {
                'color': '#FF9500',
                'width': 3,
                'style': 'solid',
                'arrow': True
            },
            'related': {
                'color': '#50E3C2',
                'width': 2,
                'style': 'dashed',
                'arrow': False
            },
            'similar': {
                'color': '#B8E986',
                'width': 1,
                'style': 'dotted',
                'arrow': False
            }
        }
    
    def generate_star_map(self, knowledge_graph: Dict, subject_code: str) -> Dict:
        """生成星图"""
        try:
            logger.info(f"开始生成 {subject_code} 星图")
            
            nodes = knowledge_graph.get('nodes', [])
            edges = knowledge_graph.get('edges', [])
            
            if not nodes:
                return {
                    'success': False,
                    'message': '知识图谱为空，无法生成星图'
                }
            
            # 生成星座布局
            star_positions = self._generate_constellation_layout(nodes, subject_code)
            
            # 创建星星数据
            stars = self._create_stars(nodes, star_positions)
            
            # 创建星座连线
            constellation_lines = self._create_constellation_lines(stars, subject_code)
            
            # 创建学习路径
            learning_paths = self._create_learning_paths(edges, star_positions)
            
            # 生成星图元数据
            metadata = self._generate_star_map_metadata(stars, constellation_lines, learning_paths, subject_code)
            
            star_map_data = {
                'canvas': {
                    'width': self.canvas_width,
                    'height': self.canvas_height,
                    'background': '#0B1426'  # 深蓝色夜空
                },
                'stars': stars,
                'constellation_lines': constellation_lines,
                'learning_paths': learning_paths,
                'metadata': metadata
            }
            
            return {
                'success': True,
                'subject_code': subject_code,
                'star_map': star_map_data,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"生成星图失败: {str(e)}")
            return {
                'success': False,
                'message': f'生成失败: {str(e)}',
                'error': str(e)
            }
    
    def _generate_constellation_layout(self, nodes: List[Dict], subject_code: str) -> Dict[str, Tuple[float, float]]:
        """生成星座布局"""
        try:
            positions = {}
            
            # 按类型分组节点
            node_groups = {
                'subject': [],
                'chapter': [],
                'section': [],
                'knowledge_point': []
            }
            
            for node in nodes:
                node_type = node.get('type', 'knowledge_point')
                if node_type in node_groups:
                    node_groups[node_type].append(node)
                else:
                    node_groups['knowledge_point'].append(node)
            
            # 学科节点放在中心
            if node_groups['subject']:
                subject_node = node_groups['subject'][0]
                positions[subject_node['id']] = (self.canvas_width / 2, self.canvas_height / 2)
            
            # 章节节点按星座模式排列
            chapter_positions = self._arrange_constellation_pattern(
                node_groups['chapter'], 
                subject_code,
                center=(self.canvas_width / 2, self.canvas_height / 2),
                radius=200
            )
            positions.update(chapter_positions)
            
            # 小节节点围绕章节排列
            section_positions = self._arrange_sections_around_chapters(
                node_groups['section'], 
                chapter_positions,
                radius=80
            )
            positions.update(section_positions)
            
            # 知识点围绕小节排列
            kp_positions = self._arrange_knowledge_points(
                node_groups['knowledge_point'],
                section_positions,
                chapter_positions,
                radius=40
            )
            positions.update(kp_positions)
            
            return positions
            
        except Exception as e:
            logger.error(f"生成星座布局失败: {str(e)}")
            return {}
    
    def _arrange_constellation_pattern(self, nodes: List[Dict], subject_code: str, 
                                     center: Tuple[float, float], radius: float) -> Dict[str, Tuple[float, float]]:
        """按星座模式排列节点"""
        positions = {}
        
        if not nodes:
            return positions
        
        constellation = self.constellation_patterns.get(subject_code, {
            'pattern': 'circle'
        })
        
        pattern = constellation.get('pattern', 'circle')
        cx, cy = center
        
        if pattern == 'circle':
            # 圆形排列
            angle_step = 2 * math.pi / len(nodes)
            for i, node in enumerate(nodes):
                angle = i * angle_step
                x = cx + radius * math.cos(angle)
                y = cy + radius * math.sin(angle)
                positions[node['id']] = (x, y)
        
        elif pattern == 'square':
            # 正方形排列
            side_length = len(nodes) // 4 + (1 if len(nodes) % 4 > 0 else 0)
            for i, node in enumerate(nodes):
                side = i // side_length
                pos_in_side = i % side_length
                
                if side == 0:  # 上边
                    x = cx - radius + (2 * radius * pos_in_side / max(1, side_length - 1))
                    y = cy - radius
                elif side == 1:  # 右边
                    x = cx + radius
                    y = cy - radius + (2 * radius * pos_in_side / max(1, side_length - 1))
                elif side == 2:  # 下边
                    x = cx + radius - (2 * radius * pos_in_side / max(1, side_length - 1))
                    y = cy + radius
                else:  # 左边
                    x = cx - radius
                    y = cy + radius - (2 * radius * pos_in_side / max(1, side_length - 1))
                
                positions[node['id']] = (x, y)
        
        elif pattern == 'diamond':
            # 菱形排列
            angle_step = 2 * math.pi / len(nodes)
            for i, node in enumerate(nodes):
                angle = i * angle_step + math.pi / 4  # 旋转45度
                x = cx + radius * math.cos(angle)
                y = cy + radius * math.sin(angle)
                positions[node['id']] = (x, y)
        
        elif pattern == 'line':
            # 直线排列
            if len(nodes) == 1:
                positions[nodes[0]['id']] = (cx, cy - radius)
            else:
                for i, node in enumerate(nodes):
                    x = cx - radius + (2 * radius * i / (len(nodes) - 1))
                    y = cy - radius
                    positions[node['id']] = (x, y)
        
        elif pattern == 'triangle':
            # 三角形排列
            if len(nodes) <= 3:
                angles = [0, 2 * math.pi / 3, 4 * math.pi / 3]
                for i, node in enumerate(nodes):
                    angle = angles[i] if i < len(angles) else 0
                    x = cx + radius * math.cos(angle)
                    y = cy + radius * math.sin(angle)
                    positions[node['id']] = (x, y)
            else:
                # 多个节点时，内外两层三角形
                for i, node in enumerate(nodes):
                    if i < 3:
                        angle = i * 2 * math.pi / 3
                        r = radius
                    else:
                        angle = (i - 3) * 2 * math.pi / max(1, len(nodes) - 3)
                        r = radius * 0.6
                    
                    x = cx + r * math.cos(angle)
                    y = cy + r * math.sin(angle)
                    positions[node['id']] = (x, y)
        
        else:
            # 默认圆形排列
            angle_step = 2 * math.pi / len(nodes)
            for i, node in enumerate(nodes):
                angle = i * angle_step
                x = cx + radius * math.cos(angle)
                y = cy + radius * math.sin(angle)
                positions[node['id']] = (x, y)
        
        return positions
    
    def _arrange_sections_around_chapters(self, sections: List[Dict], 
                                        chapter_positions: Dict[str, Tuple[float, float]], 
                                        radius: float) -> Dict[str, Tuple[float, float]]:
        """围绕章节排列小节"""
        positions = {}
        
        # 按章节分组小节
        chapter_sections = {}
        for section in sections:
            chapter_id = section.get('chapter_id')
            if chapter_id:
                chapter_node_id = f"chapter_{chapter_id}"
                if chapter_node_id not in chapter_sections:
                    chapter_sections[chapter_node_id] = []
                chapter_sections[chapter_node_id].append(section)
        
        # 为每个章节的小节安排位置
        for chapter_id, chapter_sections_list in chapter_sections.items():
            if chapter_id in chapter_positions:
                cx, cy = chapter_positions[chapter_id]
                
                if len(chapter_sections_list) == 1:
                    # 只有一个小节，放在章节下方
                    positions[chapter_sections_list[0]['id']] = (cx, cy + radius)
                else:
                    # 多个小节，围绕章节圆形排列
                    angle_step = 2 * math.pi / len(chapter_sections_list)
                    for i, section in enumerate(chapter_sections_list):
                        angle = i * angle_step
                        x = cx + radius * math.cos(angle)
                        y = cy + radius * math.sin(angle)
                        positions[section['id']] = (x, y)
        
        return positions
    
    def _arrange_knowledge_points(self, knowledge_points: List[Dict],
                                section_positions: Dict[str, Tuple[float, float]],
                                chapter_positions: Dict[str, Tuple[float, float]],
                                radius: float) -> Dict[str, Tuple[float, float]]:
        """排列知识点"""
        positions = {}
        
        # 按小节分组知识点
        section_kps = {}
        chapter_kps = {}
        
        for kp in knowledge_points:
            section_id = kp.get('section_id')
            chapter_id = kp.get('chapter_id')
            
            if section_id:
                section_node_id = f"section_{section_id}"
                if section_node_id not in section_kps:
                    section_kps[section_node_id] = []
                section_kps[section_node_id].append(kp)
            elif chapter_id:
                chapter_node_id = f"chapter_{chapter_id}"
                if chapter_node_id not in chapter_kps:
                    chapter_kps[chapter_node_id] = []
                chapter_kps[chapter_node_id].append(kp)
        
        # 围绕小节排列知识点
        for section_id, kps in section_kps.items():
            if section_id in section_positions:
                cx, cy = section_positions[section_id]
                self._arrange_points_around_center(kps, positions, cx, cy, radius)
        
        # 围绕章节排列知识点（没有小节的）
        for chapter_id, kps in chapter_kps.items():
            if chapter_id in chapter_positions:
                cx, cy = chapter_positions[chapter_id]
                # 使用更大的半径避免与小节重叠
                self._arrange_points_around_center(kps, positions, cx, cy, radius * 2)
        
        return positions
    
    def _arrange_points_around_center(self, points: List[Dict], positions: Dict, 
                                    cx: float, cy: float, radius: float):
        """围绕中心点排列点"""
        if len(points) == 1:
            # 随机角度避免重叠
            angle = random.uniform(0, 2 * math.pi)
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            positions[points[0]['id']] = (x, y)
        else:
            angle_step = 2 * math.pi / len(points)
            for i, point in enumerate(points):
                angle = i * angle_step + random.uniform(-0.2, 0.2)  # 添加小的随机偏移
                x = cx + radius * math.cos(angle)
                y = cy + radius * math.sin(angle)
                positions[point['id']] = (x, y)
    
    def _create_stars(self, nodes: List[Dict], positions: Dict[str, Tuple[float, float]]) -> List[Dict]:
        """创建星星数据"""
        stars = []
        
        for node in nodes:
            node_id = node['id']
            if node_id in positions:
                x, y = positions[node_id]
                
                node_type = node.get('type', 'knowledge_point')
                
                star = {
                    'id': node_id,
                    'name': node.get('name', node_id),
                    'type': node_type,
                    'position': {'x': x, 'y': y},
                    'size': self.star_sizes.get(node_type, 8),
                    'color': self.star_colors.get(node_type, self.star_colors['default']),
                    'brightness': self._calculate_star_brightness(node),
                    'twinkle': node_type in ['subject', 'chapter'],  # 重要星星会闪烁
                    'metadata': {
                        'difficulty_level': node.get('difficulty_level'),
                        'keywords': node.get('keywords', []),
                        'original_id': node.get('original_id')
                    }
                }
                
                stars.append(star)
        
        return stars
    
    def _calculate_star_brightness(self, node: Dict) -> float:
        """计算星星亮度"""
        node_type = node.get('type', 'knowledge_point')
        
        # 基础亮度
        base_brightness = {
            'subject': 1.0,
            'chapter': 0.8,
            'section': 0.6,
            'knowledge_point': 0.4,
            'concept': 0.3
        }.get(node_type, 0.4)
        
        # 根据难度调整亮度
        difficulty_level = node.get('difficulty_level', 'unknown')
        difficulty_multiplier = {
            '了解': 0.7,
            '理解': 0.8,
            '掌握': 0.9,
            '运用': 1.0,
            '分析': 1.1,
            '综合': 1.2,
            '评价': 1.3,
            'unknown': 0.8
        }.get(difficulty_level, 0.8)
        
        return min(1.0, base_brightness * difficulty_multiplier)
    
    def _create_constellation_lines(self, stars: List[Dict], subject_code: str) -> List[Dict]:
        """创建星座连线"""
        lines = []
        
        # 按类型分组星星
        star_groups = {
            'subject': [],
            'chapter': [],
            'section': [],
            'knowledge_point': []
        }
        
        for star in stars:
            star_type = star.get('type', 'knowledge_point')
            if star_type in star_groups:
                star_groups[star_type].append(star)
        
        # 连接学科到章节
        if star_groups['subject'] and star_groups['chapter']:
            subject_star = star_groups['subject'][0]
            for chapter_star in star_groups['chapter']:
                line = {
                    'id': f"line_{subject_star['id']}_{chapter_star['id']}",
                    'start': subject_star['position'],
                    'end': chapter_star['position'],
                    'color': self.constellation_lines['color'],
                    'width': self.constellation_lines['width'],
                    'opacity': self.constellation_lines['opacity'],
                    'type': 'constellation'
                }
                lines.append(line)
        
        # 连接章节形成星座图案
        if len(star_groups['chapter']) > 1:
            constellation = self.constellation_patterns.get(subject_code, {})
            pattern = constellation.get('pattern', 'circle')
            
            chapter_stars = star_groups['chapter']
            
            if pattern in ['circle', 'square', 'diamond']:
                # 连接相邻的章节
                for i in range(len(chapter_stars)):
                    start_star = chapter_stars[i]
                    end_star = chapter_stars[(i + 1) % len(chapter_stars)]
                    
                    line = {
                        'id': f"constellation_{start_star['id']}_{end_star['id']}",
                        'start': start_star['position'],
                        'end': end_star['position'],
                        'color': self.constellation_lines['color'],
                        'width': self.constellation_lines['width'],
                        'opacity': self.constellation_lines['opacity'],
                        'type': 'constellation'
                    }
                    lines.append(line)
            
            elif pattern == 'line':
                # 连接成直线
                for i in range(len(chapter_stars) - 1):
                    start_star = chapter_stars[i]
                    end_star = chapter_stars[i + 1]
                    
                    line = {
                        'id': f"constellation_{start_star['id']}_{end_star['id']}",
                        'start': start_star['position'],
                        'end': end_star['position'],
                        'color': self.constellation_lines['color'],
                        'width': self.constellation_lines['width'],
                        'opacity': self.constellation_lines['opacity'],
                        'type': 'constellation'
                    }
                    lines.append(line)
        
        return lines
    
    def _create_learning_paths(self, edges: List[Dict], positions: Dict[str, Tuple[float, float]]) -> List[Dict]:
        """创建学习路径"""
        paths = []
        
        for edge in edges:
            source_id = edge.get('source')
            target_id = edge.get('target')
            relation = edge.get('relation', 'related')
            
            if source_id in positions and target_id in positions:
                source_pos = positions[source_id]
                target_pos = positions[target_id]
                
                path_style = self.learning_paths.get(relation, self.learning_paths['related'])
                
                path = {
                    'id': f"path_{source_id}_{target_id}",
                    'source': source_id,
                    'target': target_id,
                    'start': {'x': source_pos[0], 'y': source_pos[1]},
                    'end': {'x': target_pos[0], 'y': target_pos[1]},
                    'relation': relation,
                    'color': path_style['color'],
                    'width': path_style['width'],
                    'style': path_style['style'],
                    'arrow': path_style['arrow'],
                    'weight': edge.get('weight', 1.0)
                }
                
                paths.append(path)
        
        return paths
    
    def _generate_star_map_metadata(self, stars: List[Dict], constellation_lines: List[Dict], 
                                  learning_paths: List[Dict], subject_code: str) -> Dict:
        """生成星图元数据"""
        try:
            constellation = self.constellation_patterns.get(subject_code, {})
            
            # 统计星星类型
            star_type_count = {}
            for star in stars:
                star_type = star.get('type', 'unknown')
                star_type_count[star_type] = star_type_count.get(star_type, 0) + 1
            
            # 统计学习路径类型
            path_type_count = {}
            for path in learning_paths:
                relation = path.get('relation', 'unknown')
                path_type_count[relation] = path_type_count.get(relation, 0) + 1
            
            metadata = {
                'constellation_name': constellation.get('name', f'{subject_code}座'),
                'constellation_pattern': constellation.get('pattern', 'circle'),
                'total_stars': len(stars),
                'total_constellation_lines': len(constellation_lines),
                'total_learning_paths': len(learning_paths),
                'star_type_distribution': star_type_count,
                'learning_path_distribution': path_type_count,
                'brightness_range': {
                    'min': min([star.get('brightness', 0.4) for star in stars]) if stars else 0,
                    'max': max([star.get('brightness', 0.4) for star in stars]) if stars else 0
                },
                'generated_at': datetime.now().isoformat()
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"生成星图元数据失败: {str(e)}")
            return {}
    
    def save_star_map(self, star_map_data: Dict, output_path: str) -> bool:
        """保存星图"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(star_map_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"星图已保存到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存星图失败: {str(e)}")
            return False
    
    def load_star_map(self, file_path: str) -> Optional[Dict]:
        """加载星图"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                star_map_data = json.load(f)
            
            logger.info(f"星图已从 {file_path} 加载")
            return star_map_data
            
        except Exception as e:
            logger.error(f"加载星图失败: {str(e)}")
            return None