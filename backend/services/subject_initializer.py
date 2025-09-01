#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学科初始化服务
负责从互联网抓取真题、知识点和考试范围数据
"""

import requests
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
import time
import threading
from sqlalchemy.orm import Session
from models.exam_papers import ExamPaper
from models.question import Question
from models.knowledge import KnowledgePoint, Chapter, Subject
from models.base import db
from utils.logger import get_logger
from api.knowledge_graph import generate_exam_scope

logger = get_logger(__name__)

class SubjectInitializer:
    """学科初始化器"""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.timeout = 30
        
        # 各学科的数据源配置
        self.subject_sources = {
            'chinese': {
                'name': '语文',
                'exam_sites': [
                    'http://www.gaokao.com/yuwen/',
                    'http://www.zhongkao.com/yuwen/',
                ],
                'knowledge_sites': [
                    'http://www.12999.com/yuwen/',
                ]
            },
            'math': {
                'name': '数学', 
                'exam_sites': [
                    'http://www.gaokao.com/shuxue/',
                    'http://www.zhongkao.com/shuxue/',
                ],
                'knowledge_sites': [
                    'http://www.12999.com/math/',
                ]
            },
            'english': {
                'name': '英语',
                'exam_sites': [
                    'http://www.gaokao.com/yingyu/',
                    'http://www.zhongkao.com/yingyu/',
                ],
                'knowledge_sites': [
                    'http://www.12999.com/english/',
                ]
            },
            'physics': {
                'name': '物理',
                'exam_sites': [
                    'http://www.gaokao.com/wuli/',
                    'http://www.zhongkao.com/wuli/',
                ],
                'knowledge_sites': [
                    'http://www.12999.com/physics/',
                ]
            },
            'chemistry': {
                'name': '化学',
                'exam_sites': [
                    'http://www.gaokao.com/huaxue/',
                    'http://www.zhongkao.com/huaxue/',
                ],
                'knowledge_sites': [
                    'http://www.12999.com/chemistry/',
                ]
            },
            'biology': {
                'name': '生物',
                'exam_sites': [
                    'http://www.gaokao.com/shengwu/',
                    'http://www.zhongkao.com/shengwu/',
                ],
                'knowledge_sites': [
                    'http://www.12999.com/biology/',
                ]
            },
            'history': {
                'name': '历史',
                'exam_sites': [
                    'http://www.gaokao.com/lishi/',
                    'http://www.zhongkao.com/lishi/',
                ],
                'knowledge_sites': [
                    'http://www.12999.com/history/',
                ]
            },
            'geography': {
                'name': '地理',
                'exam_sites': [
                    'http://www.gaokao.com/dili/',
                    'http://www.zhongkao.com/dili/',
                ],
                'knowledge_sites': [
                    'http://www.12999.com/geography/',
                ]
            },
            'politics': {
                'name': '政治',
                'exam_sites': [
                    'http://www.gaokao.com/zhengzhi/',
                    'http://www.zhongkao.com/zhengzhi/',
                ],
                'knowledge_sites': [
                    'http://www.12999.com/politics/',
                ]
            }
        }
    
    def initialize_subject(self, subject_code: str, subject_id: str, 
                               progress_callback=None) -> Dict:
        """初始化单个学科"""
        if subject_code not in self.subject_sources:
            raise ValueError(f"不支持的学科代码: {subject_code}")
        
        subject_config = self.subject_sources[subject_code]
        result = {
            'subject_code': subject_code,
            'subject_name': subject_config['name'],
            'exam_papers': [],
            'knowledge_points': [],
            'conflicts': [],
            'errors': []
        }
        
        try:
            # 1. 抓取真题数据
            if progress_callback:
                progress_callback(f"正在抓取{subject_config['name']}真题数据...", 10)
            
            exam_papers = self._crawl_exam_papers(
                subject_code, subject_config['exam_sites']
            )
            
            # 2. 检测重复和冲突
            if progress_callback:
                progress_callback(f"正在检测{subject_config['name']}数据冲突...", 30)
            
            conflicts = self._detect_conflicts(subject_id, exam_papers)
            result['conflicts'] = conflicts
            
            # 3. 抓取知识点数据
            if progress_callback:
                progress_callback(f"正在抓取{subject_config['name']}知识点数据...", 50)
            
            knowledge_points = self._crawl_knowledge_points(
                subject_code, subject_config['knowledge_sites']
            )
            
            # 4. 保存数据（如果没有冲突或用户选择覆盖）
            if progress_callback:
                progress_callback(f"正在保存{subject_config['name']}数据...", 80)
            
            result['exam_papers'] = exam_papers
            result['knowledge_points'] = knowledge_points
            
            if progress_callback:
                progress_callback(f"{subject_config['name']}初始化完成", 100)
            
        except Exception as e:
            logger.error(f"初始化学科 {subject_code} 失败: {str(e)}")
            result['errors'].append(str(e))
        
        return result
    
    def _crawl_exam_papers(self, subject_code: str, sites: List[str]) -> List[Dict]:
        """抓取真题数据"""
        papers = []
        
        for site in sites:
            try:
                # 获取近10年的真题链接
                paper_links = self._get_paper_links(site)
                
                for link_info in paper_links:
                    paper_data = self._extract_paper_data(link_info)
                    if paper_data:
                        papers.append(paper_data)
                    time.sleep(0.5)  # 添加延时避免请求过快
                        
            except Exception as e:
                logger.error(f"抓取网站 {site} 失败: {str(e)}")
                continue
        
        return papers
    
    def _get_paper_links(self, base_url: str) -> List[Dict]:
        """获取试卷链接"""
        links = []
        current_year = datetime.now().year
        
        try:
            response = self.session.get(base_url, timeout=self.timeout)
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                # 查找试卷链接（根据不同网站的结构调整）
                paper_links = soup.find_all('a', href=True)
                
                for link in paper_links:
                    href = link.get('href')
                    text = link.get_text().strip()
                    
                    # 提取年份信息
                    year_match = re.search(r'(20\d{2})', text)
                    if year_match:
                        year = int(year_match.group(1))
                        # 只获取近10年的数据
                        if current_year - year <= 10:
                            links.append({
                                'url': urljoin(base_url, href),
                                'title': text,
                                'year': year
                            })
        
        except Exception as e:
            logger.error(f"获取链接失败 {base_url}: {str(e)}")
        
        return links[:50]  # 限制数量
    
    def _extract_paper_data(self, link_info: Dict) -> Optional[Dict]:
        """提取试卷数据"""
        try:
            response = self.session.get(link_info['url'], timeout=self.timeout)
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                # 提取试卷内容
                content = self._extract_content(soup)
                questions = self._extract_questions(soup)
                
                return {
                    'title': link_info['title'],
                    'year': link_info['year'],
                    'source_url': link_info['url'],
                    'content': content,
                    'questions': questions,
                    'hash': self._generate_content_hash(content)
                }
        
        except Exception as e:
            logger.error(f"提取试卷数据失败 {link_info['url']}: {str(e)}")
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取试卷内容"""
        # 移除脚本和样式
        for script in soup(["script", "style"]):
            script.decompose()
        
        # 获取主要内容
        content_selectors = [
            '.content', '.main-content', '.paper-content',
            '#content', '#main', '.article-content'
        ]
        
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                return content_div.get_text().strip()
        
        # 如果没有找到特定容器，返回body内容
        body = soup.find('body')
        if body:
            return body.get_text().strip()
        
        return soup.get_text().strip()
    
    def _extract_questions(self, soup: BeautifulSoup) -> List[Dict]:
        """提取题目信息"""
        questions = []
        
        # 查找题目模式
        question_patterns = [
            r'(\d+)[.、]\s*(.+?)(?=\d+[.、]|$)',  # 数字题号
            r'([一二三四五六七八九十]+)[.、]\s*(.+?)(?=[一二三四五六七八九十]+[.、]|$)',  # 中文题号
        ]
        
        text = soup.get_text()
        
        for pattern in question_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                if len(match) >= 2 and len(match[1].strip()) > 10:
                    questions.append({
                        'number': match[0],
                        'content': match[1].strip()[:500],  # 限制长度
                        'type': self._detect_question_type(match[1])
                    })
        
        return questions[:20]  # 限制题目数量
    
    def _detect_question_type(self, content: str) -> str:
        """检测题目类型"""
        content_lower = content.lower()
        
        if '选择' in content or 'A.' in content or 'A、' in content:
            return 'choice'
        elif '填空' in content or '______' in content or '（）' in content:
            return 'fill_blank'
        elif '判断' in content or '正确' in content or '错误' in content:
            return 'judge'
        elif '简答' in content or '回答' in content:
            return 'short_answer'
        elif '作文' in content or '写作' in content:
            return 'essay'
        else:
            return 'other'
    
    def _generate_content_hash(self, content: str) -> str:
        """生成内容哈希"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _detect_conflicts(self, subject_id: str, new_papers: List[Dict]) -> List[Dict]:
        """检测数据冲突"""
        conflicts = []
        
        # 查询现有试卷
        existing_papers = db.session.query(ExamPaper).filter_by(
            subject_id=subject_id,
            tenant_id=self.tenant_id,
            is_active=True
        ).all()
        
        existing_hashes = {paper.content_hash: paper for paper in existing_papers if paper.content_hash}
        existing_years = {paper.exam_year: paper for paper in existing_papers if paper.exam_year}
        
        for new_paper in new_papers:
            conflict_info = {
                'new_paper': new_paper,
                'conflict_type': [],
                'existing_papers': []
            }
            
            # 检查内容哈希冲突
            if new_paper['hash'] in existing_hashes:
                conflict_info['conflict_type'].append('content_duplicate')
                conflict_info['existing_papers'].append(existing_hashes[new_paper['hash']])
            
            # 检查年份冲突
            if new_paper['year'] in existing_years:
                conflict_info['conflict_type'].append('year_duplicate')
                if existing_years[new_paper['year']] not in conflict_info['existing_papers']:
                    conflict_info['existing_papers'].append(existing_years[new_paper['year']])
            
            if conflict_info['conflict_type']:
                conflicts.append(conflict_info)
        
        return conflicts
    
    def _crawl_knowledge_points(self, subject_code: str, sites: List[str]) -> List[Dict]:
        """抓取知识点数据"""
        knowledge_points = []
        
        # 预定义的知识点结构（作为备用）
        default_knowledge = self._get_default_knowledge_structure(subject_code)
        
        for site in sites:
            try:
                crawled_knowledge = self._extract_knowledge_from_site(site)
                knowledge_points.extend(crawled_knowledge)
                time.sleep(0.5)  # 添加延时
            except Exception as e:
                logger.error(f"抓取知识点失败 {site}: {str(e)}")
                continue
        
        # 如果抓取失败，使用默认结构
        if not knowledge_points:
            knowledge_points = default_knowledge
        
        return knowledge_points
    
    def _get_default_knowledge_structure(self, subject_code: str) -> List[Dict]:
        """获取默认知识点结构"""
        structures = {
            'math': [
                {'name': '代数', 'children': ['方程与不等式', '函数', '数列']},
                {'name': '几何', 'children': ['平面几何', '立体几何', '解析几何']},
                {'name': '概率统计', 'children': ['概率', '统计', '随机变量']}
            ],
            'chinese': [
                {'name': '现代文阅读', 'children': ['记叙文', '说明文', '议论文']},
                {'name': '古诗文阅读', 'children': ['文言文', '古诗词', '名句默写']},
                {'name': '写作', 'children': ['记叙文写作', '议论文写作', '应用文写作']}
            ],
            'english': [
                {'name': '语法', 'children': ['时态', '语态', '从句']},
                {'name': '词汇', 'children': ['词汇运用', '短语搭配', '词义辨析']},
                {'name': '阅读理解', 'children': ['细节理解', '推理判断', '主旨大意']}
            ]
        }
        
        return structures.get(subject_code, [])
    
    def _extract_knowledge_from_site(self, site: str) -> List[Dict]:
        """从网站提取知识点"""
        knowledge_points = []
        
        try:
            response = self.session.get(site, timeout=self.timeout)
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                # 查找知识点结构
                nav_elements = soup.find_all(['nav', 'ul', 'ol'], class_=re.compile(r'menu|nav|catalog'))
                
                for nav in nav_elements:
                    points = self._parse_knowledge_structure(nav)
                    knowledge_points.extend(points)
        
        except Exception as e:
            logger.error(f"提取知识点失败 {site}: {str(e)}")
        
        return knowledge_points
    
    def _parse_knowledge_structure(self, element) -> List[Dict]:
        """解析知识点结构"""
        points = []
        
        # 查找章节标题
        chapters = element.find_all(['h1', 'h2', 'h3', 'li'], recursive=True)
        
        for chapter in chapters:
            text = chapter.get_text().strip()
            if len(text) > 2 and len(text) < 50:
                # 查找子知识点
                children = []
                next_elements = chapter.find_next_siblings()
                
                for next_elem in next_elements[:5]:  # 限制子元素数量
                    child_text = next_elem.get_text().strip()
                    if len(child_text) > 2 and len(child_text) < 30:
                        children.append(child_text)
                
                points.append({
                    'name': text,
                    'children': children
                })
        
        return points[:10]  # 限制章节数量
    
    def save_data(self, subject_id: str, data: Dict, overwrite_conflicts: bool = False) -> Dict:
        """保存抓取的数据"""
        result = {
            'saved_papers': 0,
            'saved_knowledge_points': 0,
            'skipped_conflicts': 0,
            'errors': []
        }
        
        try:
            # 保存试卷数据
            for paper_data in data['exam_papers']:
                # 检查是否有冲突
                has_conflict = any(
                    conflict['new_paper']['hash'] == paper_data['hash']
                    for conflict in data['conflicts']
                )
                
                if has_conflict and not overwrite_conflicts:
                    result['skipped_conflicts'] += 1
                    continue
                
                # 保存试卷
                exam_paper = ExamPaper(
                    tenant_id=self.tenant_id,
                    subject_id=subject_id,
                    title=paper_data['title'],
                    exam_year=paper_data['year'],
                    source_url=paper_data['source_url'],
                    content_hash=paper_data['hash'],
                    is_active=True
                )
                
                db.session.add(exam_paper)
                db.session.flush()  # 获取ID
                
                # 保存题目
                for q_data in paper_data['questions']:
                    question = Question(
                        tenant_id=self.tenant_id,
                        exam_paper_id=exam_paper.id,
                        content=q_data['content'],
                        question_type=q_data['type'],
                        question_number=q_data['number']
                    )
                    db.session.add(question)
                
                result['saved_papers'] += 1
            
            # 保存知识点数据
            for kp_data in data['knowledge_points']:
                # 创建章节
                chapter = Chapter(
                    subject_id=subject_id,
                    code=f"ch_{len(data['knowledge_points'])}",
                    name=kp_data['name'],
                    sort_order=len(data['knowledge_points'])
                )
                db.session.add(chapter)
                db.session.flush()
                
                # 创建知识点
                for child_name in kp_data['children']:
                    knowledge_point = KnowledgePoint(
                        chapter_id=chapter.id,
                        code=f"kp_{len(kp_data['children'])}",
                        name=child_name,
                        difficulty=1
                    )
                    db.session.add(knowledge_point)
                    result['saved_knowledge_points'] += 1
            
            db.session.commit()
            
            # 生成知识图谱考试范围数据
            try:
                from datetime import datetime
                current_year = datetime.now().year
                exam_scope = generate_exam_scope(subject_id, current_year)
                
                # 更新学科的考试范围配置
                subject = Subject.query.get(subject_id)
                if subject:
                    subject.exam_scope = exam_scope
                    db.session.commit()
                    logger.info(f"已为学科 {subject_id} 生成知识图谱考试范围数据")
                    
            except Exception as e:
                logger.warning(f"生成知识图谱考试范围失败: {str(e)}")
                # 不影响主流程，继续执行
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"保存数据失败: {str(e)}")
            result['errors'].append(str(e))
        
        return result
    
    def close(self):
        """关闭会话"""
        self.session.close()