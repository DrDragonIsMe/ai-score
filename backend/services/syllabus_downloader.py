#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 人教版考试大纲下载服务

Description:
    提供人教版官方考试大纲下载功能，支持各学科大纲文件获取和解析。

Author: Chang Xinglong
Date: 2025-08-31
Version: 1.0.0
License: Apache License 2.0
"""

import os
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
from utils.logger import get_logger
import hashlib
import time

logger = get_logger(__name__)

class SyllabusDownloader:
    """人教版考试大纲下载器"""
    
    def __init__(self):
        self.base_url = "https://www.pep.com.cn"  # 人教版官网
        self.download_dir = "data/syllabus"
        self.subjects_config = {
            'chinese': {
                'name': '语文',
                'urls': [
                    'https://www.pep.com.cn/gzyw/jszx/tbjxzy/kbbiaozhun/',  # 课程标准
                    'https://www.pep.com.cn/gzyw/jszx/tbjxzy/jxdg/'  # 教学大纲
                ],
                'keywords': ['课程标准', '教学大纲', '考试说明']
            },
            'mathematics': {
                'name': '数学',
                'urls': [
                    'https://www.pep.com.cn/gzsx/jszx/tbjxzy/kbbiaozhun/',
                    'https://www.pep.com.cn/gzsx/jszx/tbjxzy/jxdg/'
                ],
                'keywords': ['课程标准', '教学大纲', '考试说明']
            },
            'english': {
                'name': '英语',
                'urls': [
                    'https://www.pep.com.cn/gzyy/jszx/tbjxzy/kbbiaozhun/',
                    'https://www.pep.com.cn/gzyy/jszx/tbjxzy/jxdg/'
                ],
                'keywords': ['课程标准', '教学大纲', '考试说明']
            },
            'physics': {
                'name': '物理',
                'urls': [
                    'https://www.pep.com.cn/gzwl/jszx/tbjxzy/kbbiaozhun/',
                    'https://www.pep.com.cn/gzwl/jszx/tbjxzy/jxdg/'
                ],
                'keywords': ['课程标准', '教学大纲', '考试说明']
            },
            'chemistry': {
                'name': '化学',
                'urls': [
                    'https://www.pep.com.cn/gzhx/jszx/tbjxzy/kbbiaozhun/',
                    'https://www.pep.com.cn/gzhx/jszx/tbjxzy/jxdg/'
                ],
                'keywords': ['课程标准', '教学大纲', '考试说明']
            },
            'biology': {
                'name': '生物',
                'urls': [
                    'https://www.pep.com.cn/gzsw/jszx/tbjxzy/kbbiaozhun/',
                    'https://www.pep.com.cn/gzsw/jszx/tbjxzy/jxdg/'
                ],
                'keywords': ['课程标准', '教学大纲', '考试说明']
            },
            'history': {
                'name': '历史',
                'urls': [
                    'https://www.pep.com.cn/gzls/jszx/tbjxzy/kbbiaozhun/',
                    'https://www.pep.com.cn/gzls/jszx/tbjxzy/jxdg/'
                ],
                'keywords': ['课程标准', '教学大纲', '考试说明']
            },
            'geography': {
                'name': '地理',
                'urls': [
                    'https://www.pep.com.cn/gzdl/jszx/tbjxzy/kbbiaozhun/',
                    'https://www.pep.com.cn/gzdl/jszx/tbjxzy/jxdg/'
                ],
                'keywords': ['课程标准', '教学大纲', '考试说明']
            },
            'politics': {
                'name': '政治',
                'urls': [
                    'https://www.pep.com.cn/gzzz/jszx/tbjxzy/kbbiaozhun/',
                    'https://www.pep.com.cn/gzzz/jszx/tbjxzy/jxdg/'
                ],
                'keywords': ['课程标准', '教学大纲', '考试说明']
            }
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # 确保下载目录存在
        os.makedirs(self.download_dir, exist_ok=True)
    
    def download_subject_syllabus(self, subject_code: str) -> Dict:
        """下载指定学科的考试大纲"""
        try:
            if subject_code not in self.subjects_config:
                return {
                    'success': False,
                    'message': f'不支持的学科代码: {subject_code}'
                }
            
            subject_info = self.subjects_config[subject_code]
            subject_name = subject_info['name']
            
            logger.info(f"开始下载 {subject_name} 考试大纲")
            
            downloaded_files = []
            
            # 创建学科专用目录
            subject_dir = os.path.join(self.download_dir, subject_code)
            os.makedirs(subject_dir, exist_ok=True)
            
            # 遍历每个URL尝试下载
            for url in subject_info['urls']:
                try:
                    result = self._download_from_url(url, subject_dir, subject_info['keywords'])
                    if result['success']:
                        downloaded_files.extend(result['files'])
                except Exception as e:
                    logger.warning(f"从 {url} 下载失败: {str(e)}")
                    continue
            
            # 如果没有成功下载任何文件，使用备用方案
            if not downloaded_files:
                logger.info(f"未能从官网下载 {subject_name} 大纲，使用内置模板")
                template_file = self._create_template_syllabus(subject_code, subject_dir)
                if template_file:
                    downloaded_files.append(template_file)
            
            return {
                'success': True,
                'subject_code': subject_code,
                'subject_name': subject_name,
                'downloaded_files': downloaded_files,
                'download_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"下载 {subject_code} 考试大纲失败: {str(e)}")
            return {
                'success': False,
                'message': f'下载失败: {str(e)}',
                'error': str(e)
            }
    
    def _download_from_url(self, url: str, save_dir: str, keywords: List[str]) -> Dict:
        """从指定URL下载文件"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # 解析页面内容，查找相关文档链接
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            downloaded_files = []
            
            # 查找包含关键词的链接
            for keyword in keywords:
                links = soup.find_all('a')
                for link in links:
                    link_text = link.get_text(strip=True)
                    if link_text and keyword in link_text:
                        href = link.get('href')
                        if href:
                            file_url = self._resolve_url(url, href)
                            if file_url.endswith(('.pdf', '.doc', '.docx', '.txt')):
                                file_result = self._download_file(file_url, save_dir)
                                if file_result['success']:
                                    downloaded_files.append(file_result['file_path'])
            
            return {
                'success': True,
                'files': downloaded_files
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _resolve_url(self, base_url: str, href: str) -> str:
        """解析相对URL为绝对URL"""
        if href.startswith('http'):
            return href
        elif href.startswith('//'):
            return 'https:' + href
        elif href.startswith('/'):
            return self.base_url + href
        else:
            return base_url.rsplit('/', 1)[0] + '/' + href
    
    def _download_file(self, url: str, save_dir: str) -> Dict:
        """下载单个文件"""
        try:
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            
            # 生成文件名
            filename = url.split('/')[-1]
            if not filename or '.' not in filename:
                filename = f"syllabus_{hashlib.md5(url.encode()).hexdigest()[:8]}.pdf"
            
            file_path = os.path.join(save_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"成功下载文件: {filename}")
            
            return {
                'success': True,
                'file_path': file_path,
                'filename': filename,
                'size': len(response.content)
            }
            
        except Exception as e:
            logger.error(f"下载文件失败 {url}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_template_syllabus(self, subject_code: str, save_dir: str) -> Optional[str]:
        """创建模板考试大纲（当无法从官网下载时使用）"""
        try:
            subject_info = self.subjects_config[subject_code]
            subject_name = subject_info['name']
            
            # 根据学科生成基础大纲模板
            template_content = self._generate_syllabus_template(subject_code, subject_name)
            
            filename = f"{subject_code}_syllabus_template.json"
            file_path = os.path.join(save_dir, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(template_content, f, ensure_ascii=False, indent=2)
            
            logger.info(f"创建 {subject_name} 大纲模板: {filename}")
            
            return file_path
            
        except Exception as e:
            logger.error(f"创建模板大纲失败: {str(e)}")
            return None
    
    def _generate_syllabus_template(self, subject_code: str, subject_name: str) -> Dict:
        """生成学科大纲模板"""
        # 基础模板结构
        template = {
            'subject_code': subject_code,
            'subject_name': subject_name,
            'version': '2023版',
            'source': '内置模板',
            'created_at': datetime.now().isoformat(),
            'curriculum_standards': {
                'core_competencies': [],
                'learning_objectives': [],
                'content_standards': []
            },
            'knowledge_structure': {
                'modules': [],
                'chapters': [],
                'knowledge_points': []
            },
            'assessment_standards': {
                'exam_format': '',
                'score_distribution': {},
                'difficulty_levels': []
            }
        }
        
        # 根据不同学科填充具体内容
        if subject_code == 'chinese':
            template['curriculum_standards']['core_competencies'] = [
                '语言建构与运用', '思维发展与提升', '审美鉴赏与创造', '文化传承与理解'
            ]
            template['knowledge_structure']['modules'] = [
                '现代文阅读', '古代诗文阅读', '语言文字运用', '写作'
            ]
            template['knowledge_structure']['chapters'] = [
                {'id': 1, 'title': '现代文阅读', 'sections': [1, 2, 3]},
                {'id': 2, 'title': '古代诗文阅读', 'sections': [4, 5, 6]},
                {'id': 3, 'title': '语言文字运用', 'sections': [7, 8]},
                {'id': 4, 'title': '写作', 'sections': [9, 10]}
            ]
            template['knowledge_structure']['knowledge_points'] = [
                {'id': 1, 'content': '论述类文本阅读', 'chapter_id': 1, 'section_id': 1, 'difficulty_level': '理解', 'keywords': ['论述', '文本', '阅读']},
                {'id': 2, 'content': '实用类文本阅读', 'chapter_id': 1, 'section_id': 2, 'difficulty_level': '理解', 'keywords': ['实用', '文本', '阅读']},
                {'id': 3, 'content': '文学类文本阅读', 'chapter_id': 1, 'section_id': 3, 'difficulty_level': '分析', 'keywords': ['文学', '文本', '阅读']},
                {'id': 4, 'content': '文言文阅读', 'chapter_id': 2, 'section_id': 4, 'difficulty_level': '掌握', 'keywords': ['文言文', '阅读', '翻译']},
                {'id': 5, 'content': '古代诗歌阅读', 'chapter_id': 2, 'section_id': 5, 'difficulty_level': '分析', 'keywords': ['古诗', '鉴赏', '意境']},
                {'id': 6, 'content': '名篇名句默写', 'chapter_id': 2, 'section_id': 6, 'difficulty_level': '掌握', 'keywords': ['默写', '名句', '背诵']},
                {'id': 7, 'content': '语言文字运用', 'chapter_id': 3, 'section_id': 7, 'difficulty_level': '运用', 'keywords': ['语言', '文字', '运用']},
                {'id': 8, 'content': '语言表达连贯', 'chapter_id': 3, 'section_id': 8, 'difficulty_level': '运用', 'keywords': ['表达', '连贯', '逻辑']},
                {'id': 9, 'content': '记叙文写作', 'chapter_id': 4, 'section_id': 9, 'difficulty_level': '综合', 'keywords': ['记叙文', '写作', '叙述']},
                {'id': 10, 'content': '议论文写作', 'chapter_id': 4, 'section_id': 10, 'difficulty_level': '综合', 'keywords': ['议论文', '写作', '论证']}
            ]
        elif subject_code == 'mathematics':
            template['curriculum_standards']['core_competencies'] = [
                '数学抽象', '逻辑推理', '数学建模', '直观想象', '数学运算', '数据分析'
            ]
            template['knowledge_structure']['modules'] = [
                '函数', '几何与代数', '概率与统计', '数学建模活动与数学探究活动'
            ]
            template['knowledge_structure']['chapters'] = [
                {'id': 1, 'title': '集合与常用逻辑用语', 'sections': [1, 2]},
                {'id': 2, 'title': '函数', 'sections': [3, 4, 5]},
                {'id': 3, 'title': '三角函数', 'sections': [6, 7, 8]},
                {'id': 4, 'title': '平面向量', 'sections': [9, 10]},
                {'id': 5, 'title': '数列', 'sections': [11, 12]},
                {'id': 6, 'title': '不等式', 'sections': [13, 14]},
                {'id': 7, 'title': '立体几何', 'sections': [15, 16, 17]},
                {'id': 8, 'title': '解析几何', 'sections': [18, 19, 20]},
                {'id': 9, 'title': '统计与概率', 'sections': [21, 22, 23]}
            ]
            template['knowledge_structure']['knowledge_points'] = [
                {'id': 1, 'content': '集合的概念与运算', 'chapter_id': 1, 'section_id': 1, 'difficulty_level': '理解', 'keywords': ['集合', '运算', '交并补']},
                {'id': 2, 'content': '常用逻辑用语', 'chapter_id': 1, 'section_id': 2, 'difficulty_level': '理解', 'keywords': ['逻辑', '命题', '量词']},
                {'id': 3, 'content': '函数的概念与性质', 'chapter_id': 2, 'section_id': 3, 'difficulty_level': '掌握', 'keywords': ['函数', '定义域', '值域']},
                {'id': 4, 'content': '基本初等函数', 'chapter_id': 2, 'section_id': 4, 'difficulty_level': '掌握', 'keywords': ['指数函数', '对数函数', '幂函数']},
                {'id': 5, 'content': '函数的应用', 'chapter_id': 2, 'section_id': 5, 'difficulty_level': '运用', 'keywords': ['函数', '应用', '建模']},
                {'id': 6, 'content': '三角函数的概念', 'chapter_id': 3, 'section_id': 6, 'difficulty_level': '理解', 'keywords': ['三角函数', '弧度制', '单位圆']},
                {'id': 7, 'content': '三角恒等变换', 'chapter_id': 3, 'section_id': 7, 'difficulty_level': '掌握', 'keywords': ['三角恒等式', '和差公式', '倍角公式']},
                {'id': 8, 'content': '三角函数的图像与性质', 'chapter_id': 3, 'section_id': 8, 'difficulty_level': '掌握', 'keywords': ['三角函数', '图像', '周期性']},
                {'id': 9, 'content': '平面向量的概念', 'chapter_id': 4, 'section_id': 9, 'difficulty_level': '理解', 'keywords': ['向量', '坐标', '模长']},
                {'id': 10, 'content': '平面向量的运算', 'chapter_id': 4, 'section_id': 10, 'difficulty_level': '掌握', 'keywords': ['向量', '数量积', '夹角']}
            ]
        elif subject_code == 'english':
            template['curriculum_standards']['core_competencies'] = [
                '语言能力', '文化意识', '思维品质', '学习能力'
            ]
            template['knowledge_structure']['modules'] = [
                '听力理解', '阅读理解', '语言运用', '书面表达'
            ]
            template['knowledge_structure']['chapters'] = [
                {'id': 1, 'title': '听力理解', 'sections': [1, 2]},
                {'id': 2, 'title': '阅读理解', 'sections': [3, 4, 5]},
                {'id': 3, 'title': '语言知识运用', 'sections': [6, 7]},
                {'id': 4, 'title': '写作', 'sections': [8, 9]}
            ]
            template['knowledge_structure']['knowledge_points'] = [
                {'id': 1, 'content': '短对话理解', 'chapter_id': 1, 'section_id': 1, 'difficulty_level': '理解', 'keywords': ['听力', '对话', '理解']},
                {'id': 2, 'content': '长对话和独白理解', 'chapter_id': 1, 'section_id': 2, 'difficulty_level': '理解', 'keywords': ['听力', '独白', '信息']},
                {'id': 3, 'content': '细节理解题', 'chapter_id': 2, 'section_id': 3, 'difficulty_level': '理解', 'keywords': ['阅读', '细节', '信息']},
                {'id': 4, 'content': '推理判断题', 'chapter_id': 2, 'section_id': 4, 'difficulty_level': '分析', 'keywords': ['阅读', '推理', '判断']},
                {'id': 5, 'content': '主旨大意题', 'chapter_id': 2, 'section_id': 5, 'difficulty_level': '分析', 'keywords': ['阅读', '主旨', '概括']},
                {'id': 6, 'content': '完形填空', 'chapter_id': 3, 'section_id': 6, 'difficulty_level': '运用', 'keywords': ['完形填空', '语境', '词汇']},
                {'id': 7, 'content': '语法填空', 'chapter_id': 3, 'section_id': 7, 'difficulty_level': '运用', 'keywords': ['语法', '填空', '语言知识']},
                {'id': 8, 'content': '短文改错', 'chapter_id': 4, 'section_id': 8, 'difficulty_level': '运用', 'keywords': ['改错', '语法', '表达']},
                {'id': 9, 'content': '书面表达', 'chapter_id': 4, 'section_id': 9, 'difficulty_level': '综合', 'keywords': ['写作', '表达', '应用文']}
            ]
        elif subject_code == 'physics':
            template['curriculum_standards']['core_competencies'] = [
                '物理观念', '科学思维', '科学探究', '科学态度与责任'
            ]
            template['knowledge_structure']['modules'] = [
                '力学', '热学', '电磁学', '光学', '原子物理'
            ]
            template['knowledge_structure']['chapters'] = [
                {'id': 1, 'title': '运动的描述', 'sections': [1, 2, 3]},
                {'id': 2, 'title': '相互作用', 'sections': [4, 5, 6]},
                {'id': 3, 'title': '牛顿运动定律', 'sections': [7, 8, 9]},
                {'id': 4, 'title': '曲线运动', 'sections': [10, 11, 12]},
                {'id': 5, 'title': '万有引力与宇宙航行', 'sections': [13, 14]},
                {'id': 6, 'title': '机械能', 'sections': [15, 16, 17]},
                {'id': 7, 'title': '电场', 'sections': [18, 19, 20]},
                {'id': 8, 'title': '恒定电流', 'sections': [21, 22, 23]},
                {'id': 9, 'title': '磁场', 'sections': [24, 25, 26]}
            ]
            template['knowledge_structure']['knowledge_points'] = [
                {'id': 1, 'content': '质点、参考系和坐标系', 'chapter_id': 1, 'section_id': 1, 'difficulty_level': '理解', 'keywords': ['质点', '参考系', '坐标系']},
                {'id': 2, 'content': '时间和位移', 'chapter_id': 1, 'section_id': 2, 'difficulty_level': '理解', 'keywords': ['时间', '位移', '路程']},
                {'id': 3, 'content': '运动快慢的描述——速度', 'chapter_id': 1, 'section_id': 3, 'difficulty_level': '掌握', 'keywords': ['速度', '平均速度', '瞬时速度']},
                {'id': 4, 'content': '重力基本相互作用', 'chapter_id': 2, 'section_id': 4, 'difficulty_level': '理解', 'keywords': ['重力', '基本相互作用', '引力']},
                {'id': 5, 'content': '弹力', 'chapter_id': 2, 'section_id': 5, 'difficulty_level': '掌握', 'keywords': ['弹力', '胡克定律', '弹性形变']},
                {'id': 6, 'content': '摩擦力', 'chapter_id': 2, 'section_id': 6, 'difficulty_level': '掌握', 'keywords': ['摩擦力', '静摩擦', '滑动摩擦']},
                {'id': 7, 'content': '牛顿第一定律', 'chapter_id': 3, 'section_id': 7, 'difficulty_level': '理解', 'keywords': ['牛顿第一定律', '惯性', '惯性定律']},
                {'id': 8, 'content': '牛顿第二定律', 'chapter_id': 3, 'section_id': 8, 'difficulty_level': '掌握', 'keywords': ['牛顿第二定律', '加速度', '力']},
                {'id': 9, 'content': '牛顿第三定律', 'chapter_id': 3, 'section_id': 9, 'difficulty_level': '理解', 'keywords': ['牛顿第三定律', '作用力', '反作用力']},
                {'id': 10, 'content': '抛物运动', 'chapter_id': 4, 'section_id': 10, 'difficulty_level': '运用', 'keywords': ['抛物运动', '平抛运动', '斜抛运动']}
            ]
        elif subject_code == 'chemistry':
            template['curriculum_standards']['core_competencies'] = [
                '宏观辨识与微观探析', '变化观念与平衡思想', '证据推理与模型认知', '科学探究与创新意识', '科学态度与社会责任'
            ]
            template['knowledge_structure']['modules'] = [
                '物质结构与性质', '化学反应原理', '有机化学基础', '化学与生活'
            ]
            template['knowledge_structure']['chapters'] = [
                {'id': 1, 'title': '原子结构与性质', 'sections': [1, 2, 3]},
                {'id': 2, 'title': '分子结构与性质', 'sections': [4, 5, 6]},
                {'id': 3, 'title': '晶体结构与性质', 'sections': [7, 8]},
                {'id': 4, 'title': '化学反应与能量', 'sections': [9, 10, 11]},
                {'id': 5, 'title': '化学反应速率和化学平衡', 'sections': [12, 13, 14]},
                {'id': 6, 'title': '水溶液中的离子平衡', 'sections': [15, 16, 17]},
                {'id': 7, 'title': '有机化合物的结构与性质', 'sections': [18, 19, 20]},
                {'id': 8, 'title': '有机化学反应与有机合成', 'sections': [21, 22]}
            ]
            template['knowledge_structure']['knowledge_points'] = [
                {'id': 1, 'content': '原子结构', 'chapter_id': 1, 'section_id': 1, 'difficulty_level': '理解', 'keywords': ['原子结构', '电子构型', '核外电子']},
                {'id': 2, 'content': '原子结构与元素的性质', 'chapter_id': 1, 'section_id': 2, 'difficulty_level': '掌握', 'keywords': ['元素性质', '周期律', '原子半径']},
                {'id': 3, 'content': '原子结构与元素周期表', 'chapter_id': 1, 'section_id': 3, 'difficulty_level': '掌握', 'keywords': ['周期表', '族', '周期']},
                {'id': 4, 'content': '共价键', 'chapter_id': 2, 'section_id': 4, 'difficulty_level': '理解', 'keywords': ['共价键', '价键理论', '杂化轨道']},
                {'id': 5, 'content': '分子的立体结构', 'chapter_id': 2, 'section_id': 5, 'difficulty_level': '掌握', 'keywords': ['分子构型', '价层电子对互斥理论', 'VSEPR']},
                {'id': 6, 'content': '分子的性质', 'chapter_id': 2, 'section_id': 6, 'difficulty_level': '掌握', 'keywords': ['分子性质', '极性', '氢键']},
                {'id': 7, 'content': '晶体的常识', 'chapter_id': 3, 'section_id': 7, 'difficulty_level': '理解', 'keywords': ['晶体', '晶格', '晶胞']},
                {'id': 8, 'content': '分子晶体与原子晶体', 'chapter_id': 3, 'section_id': 8, 'difficulty_level': '掌握', 'keywords': ['分子晶体', '原子晶体', '金属晶体']},
                {'id': 9, 'content': '反应热的计算', 'chapter_id': 4, 'section_id': 9, 'difficulty_level': '运用', 'keywords': ['反应热', '焓变', '热化学方程式']},
                {'id': 10, 'content': '化学反应速率', 'chapter_id': 5, 'section_id': 12, 'difficulty_level': '掌握', 'keywords': ['反应速率', '活化能', '催化剂']}
            ]
        elif subject_code == 'biology':
            template['curriculum_standards']['core_competencies'] = [
                '生命观念', '科学思维', '科学探究', '社会责任'
            ]
            template['knowledge_structure']['modules'] = [
                '分子与细胞', '遗传与进化', '稳态与环境', '生物技术实践'
            ]
            template['knowledge_structure']['chapters'] = [
                {'id': 1, 'title': '细胞的分子组成', 'sections': [1, 2, 3]},
                {'id': 2, 'title': '细胞的基本结构', 'sections': [4, 5, 6]},
                {'id': 3, 'title': '细胞的物质输入和输出', 'sections': [7, 8]},
                {'id': 4, 'title': '细胞的能量供应和利用', 'sections': [9, 10, 11]},
                {'id': 5, 'title': '细胞的生命历程', 'sections': [12, 13, 14]},
                {'id': 6, 'title': '遗传因子的发现', 'sections': [15, 16]},
                {'id': 7, 'title': '基因和染色体的关系', 'sections': [17, 18, 19]},
                {'id': 8, 'title': '基因的本质', 'sections': [20, 21, 22]},
                {'id': 9, 'title': '基因的表达', 'sections': [23, 24]}
            ]
            template['knowledge_structure']['knowledge_points'] = [
                {'id': 1, 'content': '细胞中的元素和化合物', 'chapter_id': 1, 'section_id': 1, 'difficulty_level': '理解', 'keywords': ['元素', '化合物', '生物大分子']},
                {'id': 2, 'content': '生命活动的主要承担者——蛋白质', 'chapter_id': 1, 'section_id': 2, 'difficulty_level': '掌握', 'keywords': ['蛋白质', '氨基酸', '肽键']},
                {'id': 3, 'content': '遗传信息的携带者——核酸', 'chapter_id': 1, 'section_id': 3, 'difficulty_level': '掌握', 'keywords': ['核酸', 'DNA', 'RNA']},
                {'id': 4, 'content': '细胞膜——系统的边界', 'chapter_id': 2, 'section_id': 4, 'difficulty_level': '理解', 'keywords': ['细胞膜', '磷脂双分子层', '流动镶嵌模型']},
                {'id': 5, 'content': '细胞器——系统内的分工合作', 'chapter_id': 2, 'section_id': 5, 'difficulty_level': '掌握', 'keywords': ['细胞器', '线粒体', '叶绿体']},
                {'id': 6, 'content': '细胞核——系统的控制中心', 'chapter_id': 2, 'section_id': 6, 'difficulty_level': '理解', 'keywords': ['细胞核', '核膜', '染色质']},
                {'id': 7, 'content': '物质跨膜运输的实例', 'chapter_id': 3, 'section_id': 7, 'difficulty_level': '掌握', 'keywords': ['跨膜运输', '渗透作用', '载体蛋白']},
                {'id': 8, 'content': '生物膜的流动镶嵌模型', 'chapter_id': 3, 'section_id': 8, 'difficulty_level': '理解', 'keywords': ['生物膜', '流动性', '选择透过性']},
                {'id': 9, 'content': '降低化学反应活化能的酶', 'chapter_id': 4, 'section_id': 9, 'difficulty_level': '掌握', 'keywords': ['酶', '活化能', '催化作用']},
                {'id': 10, 'content': '细胞的能量通货——ATP', 'chapter_id': 4, 'section_id': 10, 'difficulty_level': '掌握', 'keywords': ['ATP', '腺苷三磷酸', '能量转换']}
            ]
        elif subject_code == 'history':
            template['curriculum_standards']['core_competencies'] = [
                '唯物史观', '时空观念', '史料实证', '历史解释', '家国情怀'
            ]
            template['knowledge_structure']['modules'] = [
                '中国古代史', '中国近现代史', '世界古代史', '世界近现代史'
            ]
            template['knowledge_structure']['chapters'] = [
                {'id': 1, 'title': '中华文明的起源与早期国家', 'sections': [1, 2, 3]},
                {'id': 2, 'title': '中古时期的中华文明', 'sections': [4, 5, 6]},
                {'id': 3, 'title': '中华文明的辉煌与危机', 'sections': [7, 8, 9]},
                {'id': 4, 'title': '中华民族的抗争与求索', 'sections': [10, 11, 12]},
                {'id': 5, 'title': '中华人民共和国成立和社会主义革命与建设', 'sections': [13, 14, 15]},
                {'id': 6, 'title': '改革开放与社会主义现代化建设新时期', 'sections': [16, 17]},
                {'id': 7, 'title': '古代文明的产生与发展', 'sections': [18, 19, 20]},
                {'id': 8, 'title': '中古时期的世界', 'sections': [21, 22, 23]},
                {'id': 9, 'title': '走向整体的世界', 'sections': [24, 25, 26]}
            ]
            template['knowledge_structure']['knowledge_points'] = [
                {'id': 1, 'content': '中华文明的起源', 'chapter_id': 1, 'section_id': 1, 'difficulty_level': '理解', 'keywords': ['文明起源', '新石器时代', '农业革命']},
                {'id': 2, 'content': '夏商西周的政治制度', 'chapter_id': 1, 'section_id': 2, 'difficulty_level': '掌握', 'keywords': ['夏商西周', '政治制度', '分封制']},
                {'id': 3, 'content': '春秋战国的变革', 'chapter_id': 1, 'section_id': 3, 'difficulty_level': '掌握', 'keywords': ['春秋战国', '社会变革', '百家争鸣']},
                {'id': 4, 'content': '秦汉统一多民族国家的建立', 'chapter_id': 2, 'section_id': 4, 'difficulty_level': '掌握', 'keywords': ['秦汉', '统一', '多民族国家']},
                {'id': 5, 'content': '三国两晋南北朝的民族交融', 'chapter_id': 2, 'section_id': 5, 'difficulty_level': '理解', 'keywords': ['魏晋南北朝', '民族交融', '政权更替']},
                {'id': 6, 'content': '隋唐统一多民族国家的发展', 'chapter_id': 2, 'section_id': 6, 'difficulty_level': '掌握', 'keywords': ['隋唐', '盛世', '开放包容']},
                {'id': 7, 'content': '宋元时期的经济发展', 'chapter_id': 3, 'section_id': 7, 'difficulty_level': '掌握', 'keywords': ['宋元', '经济发展', '商品经济']},
                {'id': 8, 'content': '明清统一多民族国家的巩固与发展', 'chapter_id': 3, 'section_id': 8, 'difficulty_level': '掌握', 'keywords': ['明清', '统一', '专制主义']},
                {'id': 9, 'content': '明清时期的对外关系', 'chapter_id': 3, 'section_id': 9, 'difficulty_level': '理解', 'keywords': ['明清', '对外关系', '海禁政策']},
                {'id': 10, 'content': '鸦片战争与中国社会的变化', 'chapter_id': 4, 'section_id': 10, 'difficulty_level': '掌握', 'keywords': ['鸦片战争', '半殖民地', '社会变化']}
            ]
        elif subject_code == 'geography':
            template['curriculum_standards']['core_competencies'] = [
                '人地协调观', '综合思维', '区域认知', '地理实践力'
            ]
            template['knowledge_structure']['modules'] = [
                '自然地理', '人文地理', '区域地理', '地理信息技术'
            ]
            template['knowledge_structure']['chapters'] = [
                {'id': 1, 'title': '地球的宇宙环境', 'sections': [1, 2, 3]},
                {'id': 2, 'title': '地球的圈层结构', 'sections': [4, 5, 6]},
                {'id': 3, 'title': '大气的运动', 'sections': [7, 8, 9]},
                {'id': 4, 'title': '水的运动', 'sections': [10, 11, 12]},
                {'id': 5, 'title': '地表形态的塑造', 'sections': [13, 14, 15]},
                {'id': 6, 'title': '自然环境的整体性与差异性', 'sections': [16, 17]},
                {'id': 7, 'title': '人口', 'sections': [18, 19, 20]},
                {'id': 8, 'title': '城市与环境', 'sections': [21, 22, 23]},
                {'id': 9, 'title': '生产活动与地域联系', 'sections': [24, 25, 26]}
            ]
            template['knowledge_structure']['knowledge_points'] = [
                {'id': 1, 'content': '地球在宇宙中的位置', 'chapter_id': 1, 'section_id': 1, 'difficulty_level': '理解', 'keywords': ['宇宙', '太阳系', '地球位置']},
                {'id': 2, 'content': '太阳对地球的影响', 'chapter_id': 1, 'section_id': 2, 'difficulty_level': '掌握', 'keywords': ['太阳辐射', '太阳活动', '地球影响']},
                {'id': 3, 'content': '地球的运动', 'chapter_id': 1, 'section_id': 3, 'difficulty_level': '掌握', 'keywords': ['地球自转', '地球公转', '地理意义']},
                {'id': 4, 'content': '地球的内部圈层', 'chapter_id': 2, 'section_id': 4, 'difficulty_level': '理解', 'keywords': ['地壳', '地幔', '地核']},
                {'id': 5, 'content': '地球的外部圈层', 'chapter_id': 2, 'section_id': 5, 'difficulty_level': '理解', 'keywords': ['大气圈', '水圈', '生物圈']},
                {'id': 6, 'content': '岩石圈与地表形态', 'chapter_id': 2, 'section_id': 6, 'difficulty_level': '掌握', 'keywords': ['岩石圈', '地表形态', '地质作用']},
                {'id': 7, 'content': '大气的组成和垂直分层', 'chapter_id': 3, 'section_id': 7, 'difficulty_level': '理解', 'keywords': ['大气组成', '大气分层', '对流层']},
                {'id': 8, 'content': '大气的热状况与大气运动', 'chapter_id': 3, 'section_id': 8, 'difficulty_level': '掌握', 'keywords': ['大气热状况', '大气运动', '热力环流']},
                {'id': 9, 'content': '全球性大气环流', 'chapter_id': 3, 'section_id': 9, 'difficulty_level': '掌握', 'keywords': ['大气环流', '三圈环流', '季风环流']},
                {'id': 10, 'content': '水循环', 'chapter_id': 4, 'section_id': 10, 'difficulty_level': '掌握', 'keywords': ['水循环', '水循环过程', '水循环意义']}
            ]
        elif subject_code == 'politics':
            template['curriculum_standards']['core_competencies'] = [
                '政治认同', '科学精神', '法治意识', '公共参与'
            ]
            template['knowledge_structure']['modules'] = [
                '经济生活', '政治生活', '文化生活', '生活与哲学'
            ]
            template['knowledge_structure']['chapters'] = [
                {'id': 1, 'title': '生产资料所有制与经济体制', 'sections': [1, 2, 3]},
                {'id': 2, 'title': '生产、劳动与经营', 'sections': [4, 5, 6]},
                {'id': 3, 'title': '收入与分配', 'sections': [7, 8, 9]},
                {'id': 4, 'title': '发展社会主义市场经济', 'sections': [10, 11, 12]},
                {'id': 5, 'title': '人民当家作主', 'sections': [13, 14, 15]},
                {'id': 6, 'title': '人民代表大会制度', 'sections': [16, 17, 18]},
                {'id': 7, 'title': '中国共产党领导的多党合作和政治协商制度', 'sections': [19, 20]},
                {'id': 8, 'title': '民族区域自治制度和基层群众自治制度', 'sections': [21, 22]},
                {'id': 9, 'title': '全面依法治国', 'sections': [23, 24, 25]}
            ]
            template['knowledge_structure']['knowledge_points'] = [
                {'id': 1, 'content': '公有制为主体、多种所有制经济共同发展', 'chapter_id': 1, 'section_id': 1, 'difficulty_level': '掌握', 'keywords': ['公有制', '多种所有制', '基本经济制度']},
                {'id': 2, 'content': '社会主义市场经济体制', 'chapter_id': 1, 'section_id': 2, 'difficulty_level': '掌握', 'keywords': ['市场经济', '经济体制', '资源配置']},
                {'id': 3, 'content': '新发展理念和中国特色社会主义新时代的经济建设', 'chapter_id': 1, 'section_id': 3, 'difficulty_level': '理解', 'keywords': ['新发展理念', '经济建设', '高质量发展']},
                {'id': 4, 'content': '发展生产 满足消费', 'chapter_id': 2, 'section_id': 4, 'difficulty_level': '理解', 'keywords': ['生产', '消费', '生产力']},
                {'id': 5, 'content': '我国的个人收入分配', 'chapter_id': 3, 'section_id': 7, 'difficulty_level': '掌握', 'keywords': ['收入分配', '分配制度', '共同富裕']},
                {'id': 6, 'content': '国家财政', 'chapter_id': 3, 'section_id': 8, 'difficulty_level': '掌握', 'keywords': ['财政', '财政政策', '宏观调控']},
                {'id': 7, 'content': '征税和纳税', 'chapter_id': 3, 'section_id': 9, 'difficulty_level': '理解', 'keywords': ['税收', '纳税', '税收作用']},
                {'id': 8, 'content': '社会主义市场经济', 'chapter_id': 4, 'section_id': 10, 'difficulty_level': '掌握', 'keywords': ['市场经济', '宏观调控', '经济发展']},
                {'id': 9, 'content': '我国的人民民主', 'chapter_id': 5, 'section_id': 13, 'difficulty_level': '掌握', 'keywords': ['人民民主', '民主制度', '人民当家作主']},
                {'id': 10, 'content': '坚持党的领导', 'chapter_id': 5, 'section_id': 14, 'difficulty_level': '掌握', 'keywords': ['党的领导', '中国共产党', '政治领导']}
            ]
        # 可以继续添加其他学科的模板内容
        
        return template
    
    def download_all_subjects(self) -> Dict:
        """下载所有学科的考试大纲"""
        try:
            logger.info("开始下载所有学科考试大纲")
            
            results = {}
            success_count = 0
            total_count = len(self.subjects_config)
            
            for subject_code in self.subjects_config.keys():
                result = self.download_subject_syllabus(subject_code)
                results[subject_code] = result
                
                if result['success']:
                    success_count += 1
                
                # 添加延迟避免请求过于频繁
                time.sleep(2)
            
            return {
                'success': True,
                'total_subjects': total_count,
                'success_count': success_count,
                'failed_count': total_count - success_count,
                'results': results,
                'download_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"批量下载考试大纲失败: {str(e)}")
            return {
                'success': False,
                'message': f'批量下载失败: {str(e)}',
                'error': str(e)
            }
    
    def get_download_status(self) -> Dict:
        """获取下载状态"""
        try:
            status = {}
            
            for subject_code, subject_info in self.subjects_config.items():
                subject_dir = os.path.join(self.download_dir, subject_code)
                
                if os.path.exists(subject_dir):
                    files = os.listdir(subject_dir)
                    status[subject_code] = {
                        'name': subject_info['name'],
                        'downloaded': True,
                        'file_count': len(files),
                        'files': files
                    }
                else:
                    status[subject_code] = {
                        'name': subject_info['name'],
                        'downloaded': False,
                        'file_count': 0,
                        'files': []
                    }
            
            return {
                'success': True,
                'status': status
            }
            
        except Exception as e:
            logger.error(f"获取下载状态失败: {str(e)}")
            return {
                'success': False,
                'message': f'获取状态失败: {str(e)}',
                'error': str(e)
            }