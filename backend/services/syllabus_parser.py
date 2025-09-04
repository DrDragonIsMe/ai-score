#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 考试大纲解析服务

Description:
    解析下载的考试大纲内容，提取知识点结构和层次关系。

Author: Chang Xinglong
Date: 2025-01-21
Version: 1.0.0
License: Apache License 2.0
"""

import os
import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from utils.logger import get_logger

# 可选依赖
try:
    import PyPDF2
    HAS_PDF_SUPPORT = True
except ImportError:
    HAS_PDF_SUPPORT = False

try:
    import docx
    HAS_DOCX_SUPPORT = True
except ImportError:
    HAS_DOCX_SUPPORT = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4_SUPPORT = True
except ImportError:
    HAS_BS4_SUPPORT = False

logger = get_logger(__name__)

class SyllabusParser:
    """考试大纲解析器"""
    
    def __init__(self):
        self.knowledge_patterns = {
            # 章节标题模式
            'chapter': [
                r'第[一二三四五六七八九十\d]+章[\s]*([^\n]+)',
                r'第[一二三四五六七八九十\d]+部分[\s]*([^\n]+)',
                r'[一二三四五六七八九十\d]+、[\s]*([^\n]+)',
                r'Chapter\s+\d+[\s]*([^\n]+)'
            ],
            # 节标题模式
            'section': [
                r'第[一二三四五六七八九十\d]+节[\s]*([^\n]+)',
                r'\d+\.[\d\.]*[\s]*([^\n]+)',
                r'[一二三四五六七八九十\d]+\.[一二三四五六七八九十\d]+[\s]*([^\n]+)'
            ],
            # 知识点模式
            'knowledge_point': [
                r'[（(]\d+[）)][\s]*([^\n]+)',
                r'[①②③④⑤⑥⑦⑧⑨⑩][\s]*([^\n]+)',
                r'\([一二三四五六七八九十\d]+\)[\s]*([^\n]+)',
                r'[a-z]\.[\s]*([^\n]+)'
            ],
            # 能力要求模式
            'ability': [
                r'(了解|理解|掌握|运用|分析|综合|评价)[：:][\s]*([^\n]+)',
                r'能力要求[：:][\s]*([^\n]+)',
                r'学习目标[：:][\s]*([^\n]+)'
            ]
        }
        
        self.difficulty_levels = {
            '了解': 1,
            '理解': 2,
            '掌握': 3,
            '运用': 4,
            '分析': 5,
            '综合': 6,
            '评价': 7
        }
    
    def parse_syllabus_file(self, file_path: str) -> Dict:
        """解析考试大纲文件"""
        try:
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'message': f'文件不存在: {file_path}'
                }
            
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # 根据文件类型选择解析方法
            if file_ext == '.pdf':
                if not HAS_PDF_SUPPORT:
                    return {
                        'success': False,
                        'message': 'PDF解析需要安装PyPDF2库: pip install PyPDF2'
                    }
                content = self._extract_pdf_content(file_path)
            elif file_ext in ['.doc', '.docx']:
                if not HAS_DOCX_SUPPORT:
                    return {
                        'success': False,
                        'message': 'Word文档解析需要安装python-docx库: pip install python-docx'
                    }
                content = self._extract_docx_content(file_path)
            elif file_ext == '.txt':
                content = self._extract_txt_content(file_path)
            elif file_ext == '.json':
                return self._parse_json_syllabus(file_path)
            else:
                return {
                    'success': False,
                    'message': f'不支持的文件格式: {file_ext}'
                }
            
            if not content:
                return {
                    'success': False,
                    'message': '无法提取文件内容'
                }
            
            # 解析内容结构
            parsed_structure = self._parse_content_structure(content)
            
            return {
                'success': True,
                'file_path': file_path,
                'content_length': len(content),
                'structure': parsed_structure,
                'parsed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"解析大纲文件失败 {file_path}: {str(e)}")
            return {
                'success': False,
                'message': f'解析失败: {str(e)}',
                'error': str(e)
            }
    
    def _extract_pdf_content(self, file_path: str) -> str:
        """提取PDF文件内容"""
        if not HAS_PDF_SUPPORT:
            logger.error("PDF解析需要安装PyPDF2库")
            return ""
        
        try:
            content = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    content += page.extract_text() + "\n"
            return content
        except Exception as e:
            logger.error(f"提取PDF内容失败: {str(e)}")
            return ""
    
    def _extract_docx_content(self, file_path: str) -> str:
        """提取Word文档内容"""
        if not HAS_DOCX_SUPPORT:
            logger.error("Word文档解析需要安装python-docx库")
            return ""
        
        try:
            doc = docx.Document(file_path)
            content = ""
            for paragraph in doc.paragraphs:
                content += paragraph.text + "\n"
            return content
        except Exception as e:
            logger.error(f"提取Word内容失败: {str(e)}")
            return ""
    
    def _extract_txt_content(self, file_path: str) -> str:
        """提取文本文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"提取文本内容失败: {str(e)}")
            return ""
    
    def _parse_json_syllabus(self, file_path: str) -> Dict:
        """解析JSON格式的大纲文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            return {
                'success': True,
                'file_path': file_path,
                'structure': data,
                'parsed_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"解析JSON大纲失败: {str(e)}")
            return {
                'success': False,
                'message': f'JSON解析失败: {str(e)}',
                'error': str(e)
            }
    
    def _parse_content_structure(self, content: str) -> Dict:
        """解析内容结构"""
        try:
            structure = {
                'chapters': [],
                'sections': [],
                'knowledge_points': [],
                'abilities': [],
                'metadata': {
                    'total_chapters': 0,
                    'total_sections': 0,
                    'total_knowledge_points': 0,
                    'difficulty_distribution': {}
                }
            }
            
            lines = content.split('\n')
            current_chapter = None
            current_section = None
            
            for line_num, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # 检查章节
                chapter_match = self._match_patterns(line, self.knowledge_patterns['chapter'])
                if chapter_match:
                    current_chapter = {
                        'id': len(structure['chapters']) + 1,
                        'title': chapter_match,
                        'line_number': line_num + 1,
                        'sections': [],
                        'knowledge_points': []
                    }
                    structure['chapters'].append(current_chapter)
                    continue
                
                # 检查节
                section_match = self._match_patterns(line, self.knowledge_patterns['section'])
                if section_match:
                    current_section = {
                        'id': len(structure['sections']) + 1,
                        'title': section_match,
                        'line_number': line_num + 1,
                        'chapter_id': current_chapter['id'] if current_chapter else None,
                        'knowledge_points': []
                    }
                    structure['sections'].append(current_section)
                    if current_chapter:
                        current_chapter['sections'].append(current_section['id'])
                    continue
                
                # 检查知识点
                kp_match = self._match_patterns(line, self.knowledge_patterns['knowledge_point'])
                if kp_match:
                    knowledge_point = {
                        'id': len(structure['knowledge_points']) + 1,
                        'content': kp_match,
                        'line_number': line_num + 1,
                        'chapter_id': current_chapter['id'] if current_chapter else None,
                        'section_id': current_section['id'] if current_section else None,
                        'difficulty_level': self._extract_difficulty_level(line),
                        'keywords': self._extract_keywords(kp_match)
                    }
                    structure['knowledge_points'].append(knowledge_point)
                    
                    if current_section:
                        current_section['knowledge_points'].append(knowledge_point['id'])
                    if current_chapter:
                        current_chapter['knowledge_points'].append(knowledge_point['id'])
                    continue
                
                # 检查能力要求
                ability_match = self._match_patterns(line, self.knowledge_patterns['ability'])
                if ability_match:
                    ability = {
                        'id': len(structure['abilities']) + 1,
                        'description': ability_match,
                        'line_number': line_num + 1,
                        'level': self._extract_difficulty_level(line)
                    }
                    structure['abilities'].append(ability)
            
            # 更新元数据
            structure['metadata']['total_chapters'] = len(structure['chapters'])
            structure['metadata']['total_sections'] = len(structure['sections'])
            structure['metadata']['total_knowledge_points'] = len(structure['knowledge_points'])
            
            # 统计难度分布
            difficulty_count = {}
            for kp in structure['knowledge_points']:
                level = kp.get('difficulty_level', 'unknown')
                difficulty_count[level] = difficulty_count.get(level, 0) + 1
            structure['metadata']['difficulty_distribution'] = difficulty_count
            
            return structure
            
        except Exception as e:
            logger.error(f"解析内容结构失败: {str(e)}")
            return {}
    
    def _match_patterns(self, text: str, patterns: List[str]) -> Optional[str]:
        """匹配文本模式"""
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        return None
    
    def _extract_difficulty_level(self, text: str) -> str:
        """提取难度等级"""
        for level, score in self.difficulty_levels.items():
            if level in text:
                return level
        return 'unknown'
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取，可以后续优化
        keywords = []
        
        # 移除标点符号
        clean_text = re.sub(r'[，。；：！？、（）()\[\]【】""''《》]', ' ', text)
        
        # 分词（简单按空格分割）
        words = clean_text.split()
        
        # 过滤长度大于1的词
        keywords = [word for word in words if len(word) > 1]
        
        return keywords[:5]  # 最多返回5个关键词
    
    def parse_subject_syllabus(self, subject_code: str, syllabus_dir: str) -> Dict:
        """解析指定学科的所有大纲文件"""
        try:
            if not os.path.exists(syllabus_dir):
                return {
                    'success': False,
                    'message': f'大纲目录不存在: {syllabus_dir}'
                }
            
            files = os.listdir(syllabus_dir)
            if not files:
                return {
                    'success': False,
                    'message': f'大纲目录为空: {syllabus_dir}'
                }
            
            parsed_results = []
            merged_structure = {
                'chapters': [],
                'sections': [],
                'knowledge_points': [],
                'abilities': [],
                'metadata': {
                    'total_files': len(files),
                    'total_chapters': 0,
                    'total_sections': 0,
                    'total_knowledge_points': 0,
                    'difficulty_distribution': {}
                }
            }
            
            for filename in files:
                file_path = os.path.join(syllabus_dir, filename)
                if os.path.isfile(file_path):
                    result = self.parse_syllabus_file(file_path)
                    if result['success']:
                        parsed_results.append(result)
                        
                        # 合并结构
                        structure = result['structure']
                        if isinstance(structure, dict):
                            self._merge_structure(merged_structure, structure)
            
            # 更新合并后的元数据
            merged_structure['metadata']['total_chapters'] = len(merged_structure['chapters'])
            merged_structure['metadata']['total_sections'] = len(merged_structure['sections'])
            merged_structure['metadata']['total_knowledge_points'] = len(merged_structure['knowledge_points'])
            
            # 重新计算难度分布
            difficulty_count = {}
            for kp in merged_structure['knowledge_points']:
                level = kp.get('difficulty_level', 'unknown')
                difficulty_count[level] = difficulty_count.get(level, 0) + 1
            merged_structure['metadata']['difficulty_distribution'] = difficulty_count
            
            return {
                'success': True,
                'subject_code': subject_code,
                'parsed_files': len(parsed_results),
                'file_results': parsed_results,
                'merged_structure': merged_structure,
                'parsed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"解析学科大纲失败 {subject_code}: {str(e)}")
            return {
                'success': False,
                'message': f'解析失败: {str(e)}',
                'error': str(e)
            }
    
    def _merge_structure(self, target: Dict, source: Dict):
        """合并结构数据"""
        try:
            # 合并章节
            if 'chapters' in source:
                for chapter in source['chapters']:
                    chapter['id'] = len(target['chapters']) + 1
                    target['chapters'].append(chapter)
            
            # 合并节
            if 'sections' in source:
                for section in source['sections']:
                    section['id'] = len(target['sections']) + 1
                    target['sections'].append(section)
            
            # 合并知识点
            if 'knowledge_points' in source:
                for kp in source['knowledge_points']:
                    kp['id'] = len(target['knowledge_points']) + 1
                    target['knowledge_points'].append(kp)
            
            # 合并能力要求
            if 'abilities' in source:
                for ability in source['abilities']:
                    ability['id'] = len(target['abilities']) + 1
                    target['abilities'].append(ability)
                    
        except Exception as e:
            logger.error(f"合并结构数据失败: {str(e)}")
    
    def export_parsed_structure(self, structure: Dict, output_path: str) -> bool:
        """导出解析后的结构"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(structure, f, ensure_ascii=False, indent=2)
            
            logger.info(f"导出解析结构到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出解析结构失败: {str(e)}")
            return False