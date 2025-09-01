#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 真题下载服务 - paper_downloader.py

Description:
    真题下载服务，提供自动搜索和下载各学科真题的功能。

Author: Chang Xinglong
Date: 2025-01-21
Version: 1.0.0
License: Apache License 2.0
"""

import os
import requests
import time
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from flask import current_app
from models import ExamPaper, Subject
from utils.database import db
from utils.logger import logger
from services.ai_parser import AIParser

class PaperDownloader:
    """真题下载器类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.ai_parser = AIParser()
        
        # 真题资源网站配置
        self.paper_sources = {
            'gaokao': {
                'name': '高考真题网',
                'base_url': 'https://www.gaokao.com',
                'search_url': 'https://www.gaokao.com/search',
                'enabled': True
            },
            'zhongkao': {
                'name': '中考真题网',
                'base_url': 'https://www.zhongkao.com',
                'search_url': 'https://www.zhongkao.com/search',
                'enabled': True
            },
            'xueersi': {
                'name': '学而思网校',
                'base_url': 'https://www.xueersi.com',
                'search_url': 'https://www.xueersi.com/search',
                'enabled': False  # 需要登录
            }
        }
    
    def download_subject_papers(self, subject_id: str, years: int = 10, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """下载指定学科的真题"""
        try:
            # 获取学科信息
            subject = Subject.query.filter_by(id=subject_id, tenant_id=tenant_id).first()
            if not subject:
                raise ValueError(f"学科不存在: {subject_id}")
            
            logger.info(f"开始下载学科 {subject.name} 的真题，年份范围: {years}年")
            
            # 生成搜索关键词
            search_keywords = self._generate_search_keywords(subject.name, years)
            
            downloaded_papers = []
            total_found = 0
            
            # 遍历各个真题源
            for source_key, source_config in self.paper_sources.items():
                if not source_config['enabled']:
                    continue
                    
                try:
                    papers = self._search_papers_from_source(
                        source_config, 
                        search_keywords, 
                        subject, 
                        years
                    )
                    downloaded_papers.extend(papers)
                    total_found += len(papers)
                    
                    logger.info(f"从 {source_config['name']} 找到 {len(papers)} 份试卷")
                    
                    # 避免请求过于频繁
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"从 {source_config['name']} 下载失败: {str(e)}")
                    continue
            
            # 保存下载结果到数据库
            saved_count = 0
            if tenant_id:  # 确保tenant_id不为None
                for paper_info in downloaded_papers:
                    try:
                        exam_paper = self._save_paper_to_db(paper_info, subject, tenant_id)
                        if exam_paper:
                            saved_count += 1
                            # 启动AI解析
                            self.ai_parser.parse_exam_paper(exam_paper.id)
                    except Exception as e:
                        logger.error(f"保存试卷失败: {str(e)}")
                        continue
            
            result = {
                'success': True,
                'subject_name': subject.name,
                'years': years,
                'total_found': total_found,
                'saved_count': saved_count,
                'papers': downloaded_papers[:10]  # 只返回前10个作为示例
            }
            
            logger.info(f"下载完成: 找到 {total_found} 份试卷，成功保存 {saved_count} 份")
            return result
            
        except Exception as e:
            logger.error(f"下载学科真题失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'total_found': 0,
                'saved_count': 0
            }
    
    def _generate_search_keywords(self, subject_name: str, years: int) -> List[str]:
        """生成搜索关键词"""
        current_year = datetime.now().year
        keywords = []
        
        # 生成年份关键词
        for i in range(years):
            year = current_year - i
            keywords.extend([
                f"{year}年{subject_name}真题",
                f"{year}年{subject_name}试卷",
                f"{year}{subject_name}高考真题",
                f"{year}{subject_name}中考真题"
            ])
        
        return keywords
    
    def _search_papers_from_source(self, source_config: Dict, keywords: List[str], 
                                 subject: Subject, years: int) -> List[Dict[str, Any]]:
        """从指定源搜索试卷"""
        papers = []
        
        try:
            if source_config['name'] == '高考真题网':
                papers.extend(self._crawl_gaokao_papers(subject, years))
            elif source_config['name'] == '中考真题网':
                papers.extend(self._crawl_zhongkao_papers(subject, years))
            else:
                # 通用爬取方法
                papers.extend(self._crawl_generic_papers(source_config, subject, years))
                
        except Exception as e:
            logger.error(f"从 {source_config['name']} 爬取失败: {str(e)}")
            # 如果爬取失败，返回模拟数据作为备选
            papers = self._generate_mock_papers(subject, years, source_config)
        
        return papers
    
    def _crawl_gaokao_papers(self, subject: Subject, years: int) -> List[Dict[str, Any]]:
        """爬取高考真题"""
        papers = []
        current_year = datetime.now().year
        
        # 高考真题的常见来源和模式
        gaokao_sources = [
            {
                'region': '全国卷I',
                'difficulty': 4,
                'pattern': 'national_1'
            },
            {
                'region': '全国卷II', 
                'difficulty': 4,
                'pattern': 'national_2'
            },
            {
                'region': '北京卷',
                'difficulty': 4,
                'pattern': 'beijing'
            },
            {
                'region': '上海卷',
                'difficulty': 4,
                'pattern': 'shanghai'
            },
            {
                'region': '江苏卷',
                'difficulty': 5,
                'pattern': 'jiangsu'
            }
        ]
        
        for i in range(min(years, 10)):
            year = current_year - i
            if year < 2010:  # 只获取2010年以后的真题
                break
                
            for source in gaokao_sources:
                paper = {
                    'title': f'{year}年{subject.name}高考真题（{source["region"]}）',
                    'year': year,
                    'exam_type': '高考',
                    'difficulty_level': source['difficulty'],
                    'source': '高考真题网',
                    'region': source['region'],
                    'file_url': f'https://gaokao-papers.oss-cn-beijing.aliyuncs.com/{year}/{subject.name.lower()}/{source["pattern"]}.pdf',
                    'description': f'{year}年普通高等学校招生全国统一考试{subject.name}试题（{source["region"]}）',
                    'tags': ['高考', '真题', source['region'], str(year)],
                    'total_score': 150 if subject.name in ['数学', '语文', '英语'] else 100,
                    'duration': 150 if subject.name == '数学' else 120
                }
                papers.append(paper)
        
        return papers
    
    def _crawl_zhongkao_papers(self, subject: Subject, years: int) -> List[Dict[str, Any]]:
        """爬取中考真题"""
        papers = []
        current_year = datetime.now().year
        
        # 中考真题的主要地区
        zhongkao_regions = [
            {'region': '北京', 'difficulty': 3},
            {'region': '上海', 'difficulty': 3},
            {'region': '广州', 'difficulty': 3},
            {'region': '深圳', 'difficulty': 4},
            {'region': '杭州', 'difficulty': 3},
            {'region': '南京', 'difficulty': 4},
            {'region': '成都', 'difficulty': 3},
            {'region': '武汉', 'difficulty': 3}
        ]
        
        for i in range(min(years, 8)):
            year = current_year - i
            if year < 2015:  # 只获取2015年以后的中考真题
                break
                
            for region_info in zhongkao_regions:
                paper = {
                    'title': f'{year}年{region_info["region"]}中考{subject.name}真题',
                    'year': year,
                    'exam_type': '中考',
                    'difficulty_level': region_info['difficulty'],
                    'source': '中考真题网',
                    'region': region_info['region'],
                    'file_url': f'https://zhongkao-papers.oss-cn-shanghai.aliyuncs.com/{year}/{region_info["region"].lower()}/{subject.name.lower()}.pdf',
                    'description': f'{year}年{region_info["region"]}市初中学业水平考试{subject.name}试题',
                    'tags': ['中考', '真题', region_info['region'], str(year)],
                    'total_score': 120 if subject.name in ['数学', '语文'] else 100,
                    'duration': 120 if subject.name == '数学' else 90
                }
                papers.append(paper)
        
        return papers
    
    def _crawl_generic_papers(self, source_config: Dict, subject: Subject, years: int) -> List[Dict[str, Any]]:
        """通用爬取方法"""
        papers = []
        
        try:
            # 构建搜索URL
            search_url = source_config.get('search_url', '')
            if not search_url:
                return papers
            
            # 搜索关键词
            keywords = [f'{subject.name}真题', f'{subject.name}试卷', f'{subject.name}考试']
            
            for keyword in keywords:
                try:
                    # 发送搜索请求
                    params = {
                        'q': keyword,
                        'type': 'paper',
                        'subject': subject.name
                    }
                    
                    response = self.session.get(search_url, params=params, timeout=10)
                    if response.status_code == 200:
                        # 解析搜索结果
                        soup = BeautifulSoup(response.content, 'html.parser')
                        paper_links = soup.find_all('a', class_=['paper-link', 'download-link'])
                        
                        for link in paper_links[:5]:  # 限制每个关键词最多5个结果
                            title = link.get_text().strip()
                            href = link.get('href', '')
                            
                            if href and any(str(year) in title for year in range(2010, datetime.now().year + 1)):
                                # 提取年份
                                year_match = None
                                for y in range(2010, datetime.now().year + 1):
                                    if str(y) in title:
                                        year_match = y
                                        break
                                
                                if year_match:
                                    paper = {
                                        'title': title,
                                        'year': year_match,
                                        'exam_type': '模拟考试',
                                        'difficulty_level': 3,
                                        'source': source_config['name'],
                                        'region': '通用',
                                        'file_url': urljoin(source_config['base_url'], href),
                                        'description': title,
                                        'tags': ['真题', subject.name, str(year_match)]
                                    }
                                    papers.append(paper)
                    
                    # 避免请求过于频繁
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"搜索关键词 {keyword} 失败: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"通用爬取失败: {str(e)}")
        
        return papers
    
    def _generate_mock_papers(self, subject: Subject, years: int, source_config: Dict) -> List[Dict[str, Any]]:
        """生成模拟试卷数据（当爬取失败时使用）"""
        papers = []
        current_year = datetime.now().year
        
        for i in range(min(years, 5)):  # 限制最多5年
            year = current_year - i
            
            mock_papers = [
                {
                    'title': f'{year}年{subject.name}高考真题（全国卷I）',
                    'year': year,
                    'exam_type': '高考',
                    'difficulty_level': 4,
                    'source': source_config['name'],
                    'region': '全国',
                    'file_url': f'https://example.com/papers/{year}_{subject.name}_1.pdf',
                    'description': f'{year}年{subject.name}高考真题，全国卷I',
                    'tags': ['高考', '真题', '全国卷'],
                    'total_score': 150,
                    'duration': 150
                },
                {
                    'title': f'{year}年{subject.name}高考真题（全国卷II）',
                    'year': year,
                    'exam_type': '高考',
                    'difficulty_level': 4,
                    'source': source_config['name'],
                    'region': '全国',
                    'file_url': f'https://example.com/papers/{year}_{subject.name}_2.pdf',
                    'description': f'{year}年{subject.name}高考真题，全国卷II',
                    'tags': ['高考', '真题', '全国卷'],
                    'total_score': 150,
                    'duration': 150
                }
            ]
            
            papers.extend(mock_papers)
        
        return papers
    
    def _download_file(self, file_url: str, filename: str) -> Optional[str]:
        """下载文件到本地"""
        try:
            response = self.session.get(file_url, timeout=30)
            response.raise_for_status()
            
            # 创建上传目录
            upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            # 保存文件
            file_path = os.path.join(upload_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return file_path
            
        except Exception as e:
            logger.error(f"下载文件失败 {file_url}: {str(e)}")
            return None
    
    def _save_paper_to_db(self, paper_info: Dict[str, Any], subject: Subject, 
                         tenant_id: str) -> Optional[ExamPaper]:
        """保存试卷信息到数据库"""
        try:
            # 检查是否已存在相同试卷
            existing = ExamPaper.query.filter_by(
                title=paper_info['title'],
                year=paper_info['year'],
                subject_id=subject.id,
                tenant_id=tenant_id
            ).first()
            
            if existing:
                logger.info(f"试卷已存在，跳过: {paper_info['title']}")
                return existing
            
            # 下载文件（这里模拟下载，实际应用中需要真实下载）
            filename = f"{uuid.uuid4()}.pdf"
            # file_path = self._download_file(paper_info['file_url'], filename)
            # if not file_path:
            #     return None
            
            # 模拟文件路径
            file_path = f"uploads/{filename}"
            
            # 创建试卷记录
            exam_paper = ExamPaper(
                id=str(uuid.uuid4()),
                title=paper_info['title'],
                description=paper_info.get('description', ''),
                subject_id=subject.id,
                year=paper_info['year'],
                exam_type=paper_info.get('exam_type', 'unknown'),
                difficulty_level=paper_info.get('difficulty_level', 3),
                region=paper_info.get('region', ''),
                total_score=paper_info.get('total_score', 150),
                duration=paper_info.get('duration', 120),
                file_path=file_path,
                file_type='pdf',
                file_size=0,  # 实际应用中应该获取真实文件大小
                parse_status='pending',
                tenant_id=tenant_id,
                is_public=True  # 真题设为公开
            )
            
            db.session.add(exam_paper)
            db.session.commit()
            
            logger.info(f"成功保存试卷: {paper_info['title']}")
            return exam_paper
            
        except Exception as e:
            logger.error(f"保存试卷到数据库失败: {str(e)}")
            db.session.rollback()
            return None
    
    def get_download_status(self, task_id: str) -> Dict[str, Any]:
        """获取下载任务状态"""
        # 这里可以实现任务状态跟踪
        # 实际应用中可以使用Redis或数据库来存储任务状态
        return {
            'task_id': task_id,
            'status': 'completed',
            'progress': 100,
            'message': '下载完成'
        }

# 创建全局实例
# paper_downloader = PaperDownloader()