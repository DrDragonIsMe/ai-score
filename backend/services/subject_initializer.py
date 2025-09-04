#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 九大学科初始化服务

Description:
    提供九大学科的初始化功能，包括学科基本信息、章节结构等。

Author: Chang Xinglong
Date: 2025-01-21
Version: 1.0.0
License: Apache License 2.0
"""

from datetime import datetime
from utils.database import db
from models.knowledge import Subject
from utils.logger import get_logger
from services.syllabus_downloader import SyllabusDownloader
from services.syllabus_parser import SyllabusParser
from services.knowledge_graph_generator import KnowledgeGraphGenerator
from services.star_map_generator import StarMapGenerator
import uuid
import os
import json

logger = get_logger(__name__)

class SubjectInitializer:
    """九大学科初始化器"""
    
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.initialized_subjects = []
        
        # 初始化相关服务
        self.syllabus_downloader = SyllabusDownloader()
        self.syllabus_parser = SyllabusParser()
        self.knowledge_graph_generator = KnowledgeGraphGenerator()
        self.star_map_generator = StarMapGenerator()
        
        # 创建输出目录
        self.output_dir = os.path.join('data', 'subjects', str(tenant_id))
        os.makedirs(self.output_dir, exist_ok=True)
        
    def get_default_subjects(self):
        """获取九大学科的默认数据"""
        return [
            {
                'code': 'chinese',
                'name': '语文',
                'name_en': 'Chinese',
                'description': '中华文化的载体，培养语言文字运用能力、文学鉴赏能力和文化传承意识。',
                'category': 'language',
                'grade_range': ['高一', '高二', '高三'],
                'total_score': 150,
                'sort_order': 1,
                'star_map_config': {
                    'color': '#e74c3c',
                    'icon': 'book',
                    'position': {'x': 100, 'y': 100}
                },
                'exam_scope': {
                    'reading_comprehension': 40,
                    'classical_chinese': 20,
                    'poetry_appreciation': 15,
                    'language_application': 25,
                    'composition': 50
                }
            },
            {
                'code': 'mathematics',
                'name': '数学',
                'name_en': 'Mathematics',
                'description': '培养逻辑思维、抽象思维和创新思维，掌握数学基本概念、方法和应用。',
                'category': 'science',
                'grade_range': ['高一', '高二', '高三'],
                'total_score': 150,
                'sort_order': 2,
                'star_map_config': {
                    'color': '#3498db',
                    'icon': 'calculator',
                    'position': {'x': 200, 'y': 100}
                },
                'exam_scope': {
                    'algebra': 35,
                    'geometry': 30,
                    'probability_statistics': 25,
                    'calculus': 35,
                    'applied_mathematics': 25
                }
            },
            {
                'code': 'english',
                'name': '英语',
                'name_en': 'English',
                'description': '培养英语语言综合运用能力，提高跨文化交际意识和能力。',
                'category': 'language',
                'grade_range': ['高一', '高二', '高三'],
                'total_score': 150,
                'sort_order': 3,
                'star_map_config': {
                    'color': '#2ecc71',
                    'icon': 'global',
                    'position': {'x': 300, 'y': 100}
                },
                'exam_scope': {
                    'listening': 30,
                    'reading_comprehension': 40,
                    'language_knowledge': 30,
                    'writing': 25,
                    'oral_expression': 25
                }
            },
            {
                'code': 'physics',
                'name': '物理',
                'name_en': 'Physics',
                'description': '探索自然界的基本规律，培养科学思维和实验探究能力。',
                'category': 'science',
                'grade_range': ['高一', '高二', '高三'],
                'total_score': 100,
                'sort_order': 4,
                'star_map_config': {
                    'color': '#9b59b6',
                    'icon': 'experiment',
                    'position': {'x': 100, 'y': 200}
                },
                'exam_scope': {
                    'mechanics': 35,
                    'thermodynamics': 15,
                    'electromagnetism': 30,
                    'optics': 10,
                    'modern_physics': 10
                }
            },
            {
                'code': 'chemistry',
                'name': '化学',
                'name_en': 'Chemistry',
                'description': '认识物质的组成、结构、性质和变化规律，培养化学核心素养。',
                'category': 'science',
                'grade_range': ['高一', '高二', '高三'],
                'total_score': 100,
                'sort_order': 5,
                'star_map_config': {
                    'color': '#f39c12',
                    'icon': 'flask',
                    'position': {'x': 200, 'y': 200}
                },
                'exam_scope': {
                    'basic_concepts': 20,
                    'inorganic_chemistry': 25,
                    'organic_chemistry': 25,
                    'chemical_reactions': 20,
                    'experimental_chemistry': 10
                }
            },
            {
                'code': 'biology',
                'name': '生物',
                'name_en': 'Biology',
                'description': '探索生命现象和生命活动规律，培养生命观念和科学思维。',
                'category': 'science',
                'grade_range': ['高一', '高二', '高三'],
                'total_score': 100,
                'sort_order': 6,
                'star_map_config': {
                    'color': '#27ae60',
                    'icon': 'leaf',
                    'position': {'x': 300, 'y': 200}
                },
                'exam_scope': {
                    'cell_biology': 25,
                    'genetics': 25,
                    'evolution': 15,
                    'ecology': 20,
                    'biotechnology': 15
                }
            },
            {
                'code': 'history',
                'name': '历史',
                'name_en': 'History',
                'description': '了解人类社会发展历程，培养历史思维和文化认同感。',
                'category': 'liberal_arts',
                'grade_range': ['高一', '高二', '高三'],
                'total_score': 100,
                'sort_order': 7,
                'star_map_config': {
                    'color': '#8e44ad',
                    'icon': 'history',
                    'position': {'x': 100, 'y': 300}
                },
                'exam_scope': {
                    'ancient_history': 30,
                    'modern_history': 35,
                    'contemporary_history': 25,
                    'historical_thinking': 10
                }
            },
            {
                'code': 'geography',
                'name': '地理',
                'name_en': 'Geography',
                'description': '认识地理环境与人类活动的关系，培养地理实践力和可持续发展观念。',
                'category': 'liberal_arts',
                'grade_range': ['高一', '高二', '高三'],
                'total_score': 100,
                'sort_order': 8,
                'star_map_config': {
                    'color': '#16a085',
                    'icon': 'globe',
                    'position': {'x': 200, 'y': 300}
                },
                'exam_scope': {
                    'physical_geography': 40,
                    'human_geography': 35,
                    'regional_geography': 15,
                    'geographic_skills': 10
                }
            },
            {
                'code': 'politics',
                'name': '政治',
                'name_en': 'Politics',
                'description': '培养政治认同、科学精神、法治意识和公共参与的核心素养。',
                'category': 'liberal_arts',
                'grade_range': ['高一', '高二', '高三'],
                'total_score': 100,
                'sort_order': 9,
                'star_map_config': {
                    'color': '#c0392b',
                    'icon': 'flag',
                    'position': {'x': 300, 'y': 300}
                },
                'exam_scope': {
                    'economic_life': 25,
                    'political_life': 25,
                    'cultural_life': 25,
                    'philosophy': 25
                }
            }
        ]
    
    def check_existing_subjects(self):
        """检查已存在的学科"""
        existing_subjects = Subject.query.filter_by(tenant_id=self.tenant_id).all()
        existing_codes = [subject.code for subject in existing_subjects]
        return existing_codes
    
    def initialize_subjects(self, force_update=False):
        """初始化九大学科"""
        try:
            logger.info(f"开始初始化九大学科，租户ID: {self.tenant_id}")
            
            default_subjects = self.get_default_subjects()
            existing_codes = self.check_existing_subjects()
            
            conflicts = []
            created_count = 0
            updated_count = 0
            
            for subject_data in default_subjects:
                subject_code = subject_data['code']
                
                # 检查是否已存在
                existing_subject = Subject.query.filter_by(
                    tenant_id=self.tenant_id,
                    code=subject_code
                ).first()
                
                if existing_subject:
                    if force_update:
                        # 更新现有学科
                        for key, value in subject_data.items():
                            if key != 'code':  # 不更新code
                                setattr(existing_subject, key, value)
                        existing_subject.updated_at = datetime.utcnow()
                        updated_count += 1
                        self.initialized_subjects.append(existing_subject)
                        logger.info(f"更新学科: {subject_data['name']}")
                    else:
                        # 只有在非强制更新时才记录冲突
                        conflicts.append({
                            'code': subject_code,
                            'name': subject_data['name'],
                            'existing_name': existing_subject.name
                        })
                else:
                    # 创建新学科
                    new_subject = Subject(
                        id=str(uuid.uuid4()),
                        tenant_id=self.tenant_id,
                        **subject_data
                    )
                    db.session.add(new_subject)
                    created_count += 1
                    self.initialized_subjects.append(new_subject)
                    logger.info(f"创建学科: {subject_data['name']}")
            
            if conflicts and not force_update:
                return {
                    'success': False,
                    'message': '发现冲突的学科',
                    'conflicts': conflicts,
                    'created_count': created_count,
                    'updated_count': updated_count
                }
            
            # 提交数据库更改
            db.session.commit()
            
            logger.info(f"九大学科初始化完成，创建: {created_count}个，更新: {updated_count}个")
            
            # 为每个学科生成大纲、知识图谱和星图
            enhanced_results = self._enhance_subjects_with_syllabus_and_maps()
            
            return {
                'success': True,
                'message': '九大学科初始化成功',
                'created_count': created_count,
                'updated_count': updated_count,
                'total_subjects': len(self.initialized_subjects),
                'enhancement_results': enhanced_results
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"九大学科初始化失败: {str(e)}")
            return {
                'success': False,
                'message': f'初始化失败: {str(e)}',
                'error': str(e)
            }
    
    def get_initialization_progress(self):
        """获取初始化进度"""
        total_subjects = 9
        initialized_count = len(self.initialized_subjects)
        progress = int((initialized_count / total_subjects) * 100)
        
        return {
            'progress': progress,
            'initialized_count': initialized_count,
            'total_subjects': total_subjects,
            'status': 'completed' if progress == 100 else 'in_progress'
        }
    
    def _enhance_subjects_with_syllabus_and_maps(self):
        """为学科生成大纲、知识图谱和星图"""
        enhancement_results = {
            'syllabus_downloads': [],
            'knowledge_graphs': [],
            'star_maps': [],
            'errors': [],
            'skipped_subjects': []
        }
        
        try:
            logger.info("开始为学科生成增强内容")
            
            for subject in self.initialized_subjects:
                subject_code = subject.code
                subject_name = subject.name
                
                logger.info(f"处理学科: {subject_name} ({subject_code})")
                print(f"正在处理学科: {subject_name} ({subject_code})")
                
                try:
                    # 1. 下载考试大纲
                    syllabus_result = self._download_subject_syllabus(subject_code, subject_name)
                    enhancement_results['syllabus_downloads'].append(syllabus_result)
                    
                    # 检查文件下载是否成功
                    if not syllabus_result.get('success', False):
                        # 记录INFO日志并向屏幕输出
                        error_msg = f"学科 {subject_name} ({subject_code}) 文件下载失败: {syllabus_result.get('message', '未知错误')}"
                        logger.info(error_msg)
                        print(f"⚠️  {error_msg}")
                        print(f"跳过学科 {subject_name} 的后续处理，继续下一个学科")
                        
                        # 记录跳过的学科
                        enhancement_results['skipped_subjects'].append({
                            'subject_code': subject_code,
                            'subject_name': subject_name,
                            'reason': '文件下载失败',
                            'message': syllabus_result.get('message', '未知错误')
                        })
                        
                        # 中止该学科的后续处理，继续下一个学科
                        continue
                    
                    # 2. 生成知识图谱（只有在下载成功时才执行）
                    print(f"✅ {subject_name} 文件下载成功，开始生成知识图谱")
                    kg_result = self._generate_subject_knowledge_graph(subject_code, syllabus_result)
                    enhancement_results['knowledge_graphs'].append(kg_result)
                    
                    # 3. 生成星图
                    if kg_result.get('success', False):
                        print(f"✅ {subject_name} 知识图谱生成成功，开始生成星图")
                        star_map_result = self._generate_subject_star_map(subject_code, kg_result)
                        enhancement_results['star_maps'].append(star_map_result)
                        print(f"✅ {subject_name} 星图生成完成")
                    else:
                        error_msg = f"学科 {subject_name} 知识图谱生成失败，跳过星图生成"
                        logger.info(error_msg)
                        print(f"⚠️  {error_msg}")
                        enhancement_results['errors'].append({
                            'subject': subject_code,
                            'step': 'star_map',
                            'message': '知识图谱生成失败，跳过星图生成'
                        })
                        
                except Exception as e:
                    error_msg = f"处理学科 {subject_code} 时出错: {str(e)}"
                    logger.error(error_msg)
                    print(f"❌ {error_msg}")
                    enhancement_results['errors'].append({
                        'subject': subject_code,
                        'step': 'general',
                        'message': error_msg
                    })
                    # 发生异常时也继续处理下一个学科
                    continue
            
            # 输出处理结果摘要
            total_subjects = len(self.initialized_subjects)
            successful_subjects = len([r for r in enhancement_results['syllabus_downloads'] if r.get('success', False)])
            skipped_subjects = len(enhancement_results['skipped_subjects'])
            
            logger.info(f"学科增强内容生成完成 - 总计: {total_subjects}, 成功: {successful_subjects}, 跳过: {skipped_subjects}")
            print(f"\n📊 学科处理结果摘要:")
            print(f"   总计学科: {total_subjects}")
            print(f"   成功处理: {successful_subjects}")
            print(f"   跳过学科: {skipped_subjects}")
            
            if enhancement_results['skipped_subjects']:
                print(f"\n⚠️  跳过的学科:")
                for skipped in enhancement_results['skipped_subjects']:
                    print(f"   - {skipped['subject_name']} ({skipped['subject_code']}): {skipped['reason']}")
            
            return enhancement_results
            
        except Exception as e:
            logger.error(f"学科增强处理失败: {str(e)}")
            print(f"❌ 学科增强处理失败: {str(e)}")
            enhancement_results['errors'].append({
                'subject': 'all',
                'step': 'general',
                'message': f'整体处理失败: {str(e)}'
            })
            return enhancement_results
    
    def _download_subject_syllabus(self, subject_code: str, subject_name: str):
        """下载学科考试大纲"""
        try:
            logger.info(f"开始下载 {subject_name} 考试大纲")
            
            # 创建学科专用目录
            subject_dir = os.path.join(self.output_dir, subject_code)
            os.makedirs(subject_dir, exist_ok=True)
            
            # 下载大纲
            download_result = self.syllabus_downloader.download_subject_syllabus(subject_code)
            
            if download_result.get('success', False):
                logger.info(f"{subject_name} 大纲下载成功")
            else:
                logger.warning(f"{subject_name} 大纲下载失败: {download_result.get('message', '未知错误')}")
            
            return {
                'subject_code': subject_code,
                'subject_name': subject_name,
                'success': download_result.get('success', False),
                'message': download_result.get('message', ''),
                'files': download_result.get('downloaded_files', []),
                'output_dir': subject_dir
            }
            
        except Exception as e:
            error_msg = f"下载 {subject_name} 大纲时出错: {str(e)}"
            logger.error(error_msg)
            return {
                'subject_code': subject_code,
                'subject_name': subject_name,
                'success': False,
                'message': error_msg,
                'files': []
            }
    
    def _generate_subject_knowledge_graph(self, subject_code: str, syllabus_result: dict):
        """生成学科知识图谱"""
        try:
            logger.info(f"开始生成 {subject_code} 知识图谱")
            
            if not syllabus_result.get('success', False):
                return {
                    'subject_code': subject_code,
                    'success': False,
                    'message': '大纲数据不可用'
                }
            
            # 解析大纲文件
            syllabus_files = syllabus_result.get('files', [])
            parsed_content = []
            
            for file_path in syllabus_files:
                if os.path.exists(file_path):
                    parse_result = self.syllabus_parser.parse_syllabus_file(file_path)
                    if parse_result and parse_result.get('success', False):
                        # 从解析结果中提取结构数据
                        structure_data = parse_result.get('structure', {})
                        if 'knowledge_structure' in structure_data:
                            # JSON模板文件的结构
                            knowledge_structure = structure_data['knowledge_structure']
                            content = {
                                'subject': subject_code,
                                'chapters': knowledge_structure.get('chapters', []),
                                'sections': knowledge_structure.get('sections', []),
                                'knowledge_points': knowledge_structure.get('knowledge_points', [])
                            }
                        else:
                            # 其他格式文件的结构
                            content = structure_data
                        parsed_content.append(content)
            
            if not parsed_content:
                # 如果没有实际文件，创建基础结构
                parsed_content = [{
                    'subject': subject_code,
                    'chapters': [],
                    'sections': [],
                    'knowledge_points': []
                }]
            
            # 使用第一个解析内容作为主要结构
            main_structure = parsed_content[0] if parsed_content else {}
            
            # 生成知识图谱
            kg_result = self.knowledge_graph_generator.generate_knowledge_graph(main_structure, subject_code)
            
            if kg_result.get('success', False):
                # 保存章节和知识点到数据库
                self._save_chapters_and_knowledge_points_to_db(subject_code, main_structure)
                
                # 保存知识图谱
                kg_file = os.path.join(syllabus_result['output_dir'], 'knowledge_graph.json')
                with open(kg_file, 'w', encoding='utf-8') as f:
                    json.dump(kg_result['graph_data'], f, ensure_ascii=False, indent=2)
                
                logger.info(f"{subject_code} 知识图谱生成成功")
                
                return {
                    'subject_code': subject_code,
                    'success': True,
                    'message': '知识图谱生成成功',
                    'knowledge_graph': kg_result['graph_data'],
                    'file_path': kg_file
                }
            else:
                return {
                    'subject_code': subject_code,
                    'success': False,
                    'message': kg_result.get('message', '知识图谱生成失败')
                }
                
        except Exception as e:
            error_msg = f"生成 {subject_code} 知识图谱时出错: {str(e)}"
            logger.error(error_msg)
            return {
                'subject_code': subject_code,
                'success': False,
                'message': error_msg
            }
    
    def _save_chapters_and_knowledge_points_to_db(self, subject_code: str, main_structure: dict):
        """将章节和知识点数据保存到数据库"""
        try:
            from models.knowledge import Subject, Chapter, KnowledgePoint, db
            
            # 获取学科
            subject = Subject.query.filter_by(
                tenant_id=self.tenant_id,
                code=subject_code
            ).first()
            
            if not subject:
                logger.error(f"未找到学科: {subject_code}")
                return
            
            # 保存章节
            chapters_data = main_structure.get('chapters', [])
            chapter_map = {}
            
            for chapter_data in chapters_data:
                chapter_id = chapter_data.get('id')
                chapter_title = chapter_data.get('title', f'Chapter {chapter_id}')
                
                # 检查章节是否已存在
                existing_chapter = Chapter.query.filter_by(
                    subject_id=subject.id,
                    code=f"CH{chapter_id:03d}"
                ).first()
                
                if not existing_chapter:
                    new_chapter = Chapter(
                        id=str(uuid.uuid4()),
                        subject_id=subject.id,
                        code=f"CH{chapter_id:03d}",
                        name=chapter_title,
                        description=chapter_data.get('description', ''),
                        difficulty=chapter_data.get('difficulty', 3),
                        importance=chapter_data.get('importance', 3)
                    )
                    db.session.add(new_chapter)
                    db.session.flush()  # 获取ID
                    chapter_map[chapter_id] = new_chapter
                    logger.info(f"创建章节: {chapter_title}")
                else:
                    chapter_map[chapter_id] = existing_chapter
                    logger.info(f"使用现有章节: {chapter_title}")
            
            # 保存知识点
            knowledge_points_data = main_structure.get('knowledge_points', [])
            
            for kp_data in knowledge_points_data:
                kp_id = kp_data.get('id')
                kp_content = kp_data.get('content', f'Knowledge Point {kp_id}')
                chapter_id = kp_data.get('chapter_id')
                
                # 获取对应的章节
                chapter = chapter_map.get(chapter_id)
                if not chapter:
                    logger.warning(f"知识点 {kp_content} 没有对应的章节，跳过")
                    continue
                
                # 检查知识点是否已存在
                existing_kp = KnowledgePoint.query.filter_by(
                    chapter_id=chapter.id,
                    code=f"KP{kp_id:03d}"
                ).first()
                
                if not existing_kp:
                    new_kp = KnowledgePoint(
                        id=str(uuid.uuid4()),
                        chapter_id=chapter.id,
                        code=f"KP{kp_id:03d}",
                        name=kp_content,
                        description=kp_data.get('description', ''),
                        content=kp_content,
                        difficulty=kp_data.get('difficulty_level', 3),
                        importance=kp_data.get('importance', 3),
                        keywords=kp_data.get('keywords', [])
                    )
                    db.session.add(new_kp)
                    logger.info(f"创建知识点: {kp_content}")
                else:
                    logger.info(f"使用现有知识点: {kp_content}")
            
            # 提交事务
            db.session.commit()
            logger.info(f"成功保存 {subject_code} 的章节和知识点到数据库")
            
        except Exception as e:
            logger.error(f"保存章节和知识点到数据库失败: {str(e)}")
            db.session.rollback()
    
    def _generate_subject_star_map(self, subject_code: str, kg_result: dict):
        """生成学科星图"""
        try:
            logger.info(f"开始生成 {subject_code} 星图")
            
            if not kg_result.get('success', False):
                return {
                    'subject_code': subject_code,
                    'success': False,
                    'message': '知识图谱数据不可用'
                }
            
            knowledge_graph = kg_result.get('knowledge_graph', {})
            
            # 生成星图
            star_map_result = self.star_map_generator.generate_star_map(knowledge_graph, subject_code)
            
            if star_map_result.get('success', False):
                # 保存星图
                star_map_file = os.path.join(
                    os.path.dirname(kg_result.get('file_path', '')), 
                    'star_map.json'
                )
                
                if star_map_file:
                    self.star_map_generator.save_star_map(star_map_result, star_map_file)
                
                logger.info(f"{subject_code} 星图生成成功")
                
                return {
                    'subject_code': subject_code,
                    'success': True,
                    'message': '星图生成成功',
                    'star_map': star_map_result.get('star_map', {}),
                    'file_path': star_map_file
                }
            else:
                return {
                    'subject_code': subject_code,
                    'success': False,
                    'message': star_map_result.get('message', '星图生成失败')
                }
                
        except Exception as e:
            error_msg = f"生成 {subject_code} 星图时出错: {str(e)}"
            logger.error(error_msg)
            return {
                'subject_code': subject_code,
                'success': False,
                'message': error_msg
            }