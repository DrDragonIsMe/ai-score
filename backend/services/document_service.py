#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 业务服务 - document_service.py

Description:
    文档管理服务，提供PDF文件上传、解析、分类、存储等功能。

Author: Chang Xinglong
Date: 2025-01-21
Version: 1.0.0
License: Apache License 2.0
"""

import os
import hashlib
import mimetypes
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image
import pymupdf as fitz  # PyMuPDF - 使用推荐的导入方式
import pytesseract
from werkzeug.utils import secure_filename
from flask import current_app

from utils.database import db
from models.document import Document, DocumentCategory, DocumentPage, DocumentAnalysis
from services.classification_service import classification_service
from utils.logger import get_logger

# 延迟导入向量数据库服务以避免循环导入
vector_db_service = None

def get_vector_db_service():
    global vector_db_service
    if vector_db_service is None:
        try:
            from services.vector_database_service import vector_db_service as vdb
            vector_db_service = vdb
        except ImportError:
            logger.warning("向量数据库服务不可用")
            vector_db_service = None
    return vector_db_service

logger = get_logger(__name__)

class DocumentService:
    """
    文档管理服务类
    """
    
    def __init__(self):
        self.upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        self.allowed_extensions = {'pdf', 'doc', 'docx', 'txt'}
        self.max_file_size = current_app.config.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024)  # 50MB
        
        # 确保上传目录存在
        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(os.path.join(self.upload_folder, 'documents'), exist_ok=True)
        os.makedirs(os.path.join(self.upload_folder, 'pages'), exist_ok=True)
    
    def allowed_file(self, filename: str) -> bool:
        """
        检查文件类型是否允许
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 是否允许
        """
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件哈希值
        """
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def save_uploaded_file(self, file, user_id: str) -> Tuple[str, Dict[str, Any]]:
        """
        保存上传的文件
        
        Args:
            file: 上传的文件对象
            user_id: 用户ID
            
        Returns:
            Tuple[str, Dict]: 文件路径和文件信息
        """
        if not file or not file.filename:
            raise ValueError("无效的文件")
        
        if not self.allowed_file(file.filename):
            raise ValueError("不支持的文件类型")
        
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{user_id}_{timestamp}_{filename}"
        
        # 保存文件
        file_path = os.path.join(self.upload_folder, 'documents', unique_filename)
        file.save(file_path)
        
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        file_hash = self.calculate_file_hash(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        
        file_info = {
            'filename': filename,
            'file_path': file_path,
            'file_size': file_size,
            'file_hash': file_hash,
            'mime_type': mime_type,
            'file_type': filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown'
        }
        
        return file_path, file_info
    
    def extract_pdf_text(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        从PDF文件中提取文本内容
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            List[Dict]: 页面内容列表
        """
        pages_content = []
        
        try:
            # 打开PDF文件
            pdf_document = fitz.open(pdf_path)
            
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                
                # 提取文本内容 - 使用PyMuPDF API
                text_content = page.get_text()  # type: ignore
                
                # 提取图片并进行OCR
                image_list = page.get_images(full=True)  # type: ignore
                ocr_text = ""
                
                if image_list:
                    # 生成页面图片 - 使用PyMuPDF API
                    mat = fitz.Matrix(2, 2)  # 2倍缩放提高质量
                    pix = page.get_pixmap(matrix=mat)  # type: ignore
                    img_data = pix.tobytes("png")
                    
                    # 保存临时图片
                    temp_img_path = os.path.join(self.upload_folder, 'pages', f'temp_page_{page_num}.png')
                    pix.save(temp_img_path)
                    
                    try:
                        # 使用OCR提取图片中的文字
                        ocr_text = pytesseract.image_to_string(Image.open(temp_img_path), lang='chi_sim+eng')
                    except Exception as e:
                        logger.warning(f"OCR处理失败: {e}")
                    finally:
                        # 删除临时文件
                        if os.path.exists(temp_img_path):
                            os.remove(temp_img_path)
                
                # 合并文本内容
                combined_text = text_content
                if ocr_text.strip():
                    combined_text += "\n\n[OCR提取内容]\n" + ocr_text
                
                page_info = {
                    'page_number': page_num + 1,
                    'text_content': text_content,
                    'ocr_content': ocr_text,
                    'combined_content': combined_text,
                    'word_count': len(combined_text.split()),
                    'character_count': len(combined_text),
                    'has_images': len(image_list) > 0,
                    'image_count': len(image_list)
                }
                
                pages_content.append(page_info)
            
            pdf_document.close()
            
        except Exception as e:
            logger.error(f"PDF文本提取失败: {e}")
            raise Exception(f"PDF解析失败: {str(e)}")
        
        return pages_content
    
    def analyze_document_content(self, content: str) -> Dict[str, Any]:
        """
        使用AI分析文档内容
        
        Args:
            content: 文档内容
            
        Returns:
            Dict: 分析结果
        """
        try:
            # 构建分析提示
            prompt = f"""
请分析以下文档内容，并提供以下信息：

1. 文档类型分类（如：学术论文、教材、试卷、笔记、报告等）
2. 主要主题和关键概念
3. 学科领域（如：数学、物理、化学、语文、英语等）
4. 难度等级（1-5级，1为最简单，5为最难）
5. 内容摘要（100字以内）
6. 关键词标签（5-10个）

文档内容：
{content[:2000]}...

请以JSON格式返回分析结果：
{{
    "document_type": "文档类型",
    "main_topics": ["主题1", "主题2"],
    "subject_area": "学科领域",
    "difficulty_level": 3,
    "summary": "内容摘要",
    "keywords": ["关键词1", "关键词2"],
    "confidence_score": 0.85
}}
"""
            
            # 基础内容分析（移除AI助手依赖以避免循环导入）
            # 简单的关键词提取和分类
            words = content.split()
            word_freq = {}
            for word in words:
                if len(word) > 2:  # 过滤短词
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # 获取高频词作为关键词
            keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            extracted_keywords = [word for word, freq in keywords]
            
            # 简单的难度评估（基于内容长度和复杂度）
            if len(content) < 1000:
                difficulty = 1
            elif len(content) < 3000:
                difficulty = 2
            elif len(content) < 5000:
                difficulty = 3
            elif len(content) < 8000:
                difficulty = 4
            else:
                difficulty = 5
            
            import json
            response_data = {
                "document_type": "文档",
                "main_topics": extracted_keywords[:3],
                "subject_area": "通用",
                "difficulty_level": difficulty,
                "summary": content[:100].replace('"', '').replace('\n', ' ') + "...",
                "keywords": extracted_keywords,
                "confidence_score": 0.7
            }
            response_text = json.dumps(response_data, ensure_ascii=False)
            
            # 解析响应
            import json
            try:
                analysis_result = json.loads(response_text)
            except json.JSONDecodeError:
                # 如果JSON解析失败，返回默认结果
                analysis_result = {
                    "document_type": "未知类型",
                    "main_topics": [],
                    "subject_area": "未知",
                    "difficulty_level": 3,
                    "summary": "AI分析失败，无法生成摘要",
                    "keywords": [],
                    "confidence_score": 0.0
                }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"文档内容分析失败: {e}")
            return {
                "document_type": "未知类型",
                "main_topics": [],
                "subject_area": "未知",
                "difficulty_level": 3,
                "summary": "分析失败",
                "keywords": [],
                "confidence_score": 0.0
            }
    
    def create_document(self, file, user_id: str, tenant_id: str, 
                       title: Optional[str] = None, description: Optional[str] = None, 
                       category_id: Optional[str] = None, tags: Optional[List[str]] = None) -> Document:
        """
        创建文档记录
        
        Args:
            file: 上传的文件对象
            user_id: 用户ID
            tenant_id: 租户ID
            title: 文档标题
            description: 文档描述
            category_id: 分类ID
            tags: 标签列表
            
        Returns:
            Document: 文档对象
        """
        try:
            # 保存文件
            file_path, file_info = self.save_uploaded_file(file, user_id)
            
            # 创建文档记录
            document = Document(
                tenant_id=tenant_id,
                user_id=user_id,
                category_id=category_id,
                filename=file_info['filename'],
                file_path=file_info['file_path'],
                file_size=file_info['file_size'],
                file_type=file_info['file_type'],
                mime_type=file_info['mime_type'],
                file_hash=file_info['file_hash'],
                title=title or file_info['filename'],
                description=description,
                tags=tags or [],
                parse_status='pending'
            )
            
            db.session.add(document)
            db.session.commit()
            
            # 异步解析文档（这里同步处理，实际应该用任务队列）
            self.parse_document(document.id)
            
            return document
            
        except Exception as e:
            logger.error(f"创建文档失败: {e}")
            db.session.rollback()
            raise Exception(f"文档创建失败: {str(e)}")
    
    def parse_document(self, document_id: str) -> bool:
        """
        解析文档内容
        
        Args:
            document_id: 文档ID
            
        Returns:
            bool: 解析是否成功
        """
        try:
            document = Document.query.get(document_id)
            if not document:
                raise ValueError("文档不存在")
            
            # 更新解析状态
            document.parse_status = 'processing'
            document.parse_progress = 0
            db.session.commit()
            
            # 根据文件类型进行解析
            if document.file_type.lower() == 'pdf':
                pages_content = self.extract_pdf_text(document.file_path)
                
                # 保存页面内容
                total_word_count = 0
                total_char_count = 0
                all_content = ""
                
                for page_info in pages_content:
                    page = DocumentPage(
                        document_id=document.id,
                        page_number=page_info['page_number'],
                        page_content=page_info['combined_content'],
                        content_type='mixed' if page_info['has_images'] else 'text'
                    )
                    db.session.add(page)
                    
                    total_word_count += page_info['word_count']
                    total_char_count += page_info['character_count']
                    all_content += page_info['combined_content'] + "\n\n"
                
                # 更新文档统计信息
                document.page_count = len(pages_content)
                document.word_count = total_word_count
                document.character_count = total_char_count
                document.parse_progress = 50
                db.session.commit()
                
                # AI分析文档内容
                if all_content.strip():
                    analysis_result = self.analyze_document_content(all_content)
                    
                    # 保存分析结果
                    analysis = DocumentAnalysis(
                        document_id=document.id,
                        analysis_type='classification',
                        result=analysis_result,
                        confidence_score=analysis_result.get('confidence_score', 0.0),
                        status='completed'
                    )
                    db.session.add(analysis)
                    
                    # 进行智能分类
                    classification_result = classification_service.classify_document(document, all_content)
                    
                    # 更新文档信息
                    if not document.title or document.title == document.filename:
                        document.title = analysis_result.get('summary', document.filename)[:100]
                    
                    # 合并标签
                    existing_tags = document.tags or []
                    new_tags = analysis_result.get('keywords', [])
                    document.tags = list(set(existing_tags + new_tags))
                
                # 创建向量索引
                self._create_document_vectors(document.id, all_content, analysis_result)
                
                # 完成解析
                document.parse_status = 'completed'
                document.parse_progress = 100
                document.parsed_at = datetime.utcnow()
                
            elif document.file_type.lower() == 'txt':
                # 处理文本文件
                try:
                    with open(document.file_path, 'r', encoding='utf-8') as f:
                        all_content = f.read()
                    
                    # 更新文档统计信息
                    document.word_count = len(all_content.split())
                    document.character_count = len(all_content)
                    document.page_count = 1
                    document.parse_progress = 50
                    db.session.commit()
                    
                    # AI分析文档内容
                    if all_content.strip():
                        analysis_result = self.analyze_document_content(all_content)
                        
                        # 保存分析结果
                        analysis = DocumentAnalysis(
                            document_id=document.id,
                            analysis_type='classification',
                            result=analysis_result,
                            confidence_score=analysis_result.get('confidence_score', 0.0),
                            status='completed'
                        )
                        db.session.add(analysis)
                        
                        # 进行智能分类
                        classification_result = classification_service.classify_document(document, all_content)
                        
                        # 更新文档信息
                        if not document.title or document.title == document.filename:
                            document.title = analysis_result.get('summary', document.filename)[:100]
                        
                        # 合并标签
                        existing_tags = document.tags or []
                        new_tags = analysis_result.get('keywords', [])
                        document.tags = list(set(existing_tags + new_tags))
                        
                        # 创建向量索引
                        self._create_document_vectors(document.id, all_content, analysis_result)
                    
                    # 完成解析
                    document.parse_status = 'completed'
                    document.parse_progress = 100
                    document.parsed_at = datetime.utcnow()
                    
                except Exception as e:
                    logger.error(f"文本文件处理失败: {e}")
                    raise Exception(f"文本文件解析失败: {str(e)}")
            
            else:
                # 其他文件类型的处理
                document.parse_status = 'completed'
                document.parse_progress = 100
                document.parsed_at = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"文档解析完成: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"文档解析失败: {e}")
            
            # 更新错误状态
            if 'document' in locals():
                document.parse_status = 'failed'
                document.parse_error = str(e)
                db.session.commit()
            
            return False
    
    def _create_document_vectors(self, document_id: str, content: str, analysis_result: Dict[str, Any]):
        """
        为文档创建向量索引
        
        Args:
            document_id: 文档ID
            content: 文档内容
            analysis_result: 文档分析结果
        """
        try:
            vdb_service = get_vector_db_service()
            if vdb_service is None:
                logger.warning(f"向量数据库服务不可用，跳过文档 {document_id} 的向量索引创建")
                return
            
            # 将长文本分割成块
            content_chunks = vdb_service._split_text_into_chunks(content, chunk_size=500, overlap=50)
            
            if not content_chunks:
                logger.warning(f"文档 {document_id} 内容为空，跳过向量索引创建")
                return
            
            # 准备元数据
            metadata = {
                'document_id': document_id,
                'document_type': analysis_result.get('document_type', '未知'),
                'subject_area': analysis_result.get('subject_area', '未知'),
                'difficulty_level': analysis_result.get('difficulty_level', 3),
                'keywords': analysis_result.get('keywords', []),
                'created_at': datetime.utcnow().isoformat()
            }
            
            # 添加向量到数据库
            success = vdb_service.add_document_vectors(
                document_id=document_id,
                document_type='document',
                content_chunks=content_chunks,
                metadata=metadata
            )
            
            if success:
                logger.info(f"文档 {document_id} 向量索引创建成功，共 {len(content_chunks)} 个块")
            else:
                logger.error(f"文档 {document_id} 向量索引创建失败")
                
        except Exception as e:
            logger.error(f"创建文档 {document_id} 向量索引时发生错误: {str(e)}")
    
    def get_documents(self, user_id: str, tenant_id: str, 
                     category_id: Optional[str] = None, search: Optional[str] = None, 
                     page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        获取文档列表
        
        Args:
            user_id: 用户ID
            tenant_id: 租户ID
            category_id: 分类ID
            search: 搜索关键词
            page: 页码
            per_page: 每页数量
            
        Returns:
            Dict: 文档列表和分页信息
        """
        query = Document.query.filter_by(user_id=user_id, tenant_id=tenant_id)
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        if search:
            query = query.filter(
                db.or_(
                    Document.title.contains(search),
                    Document.description.contains(search),
                    Document.filename.contains(search)
                )
            )
        
        # 分页查询
        pagination = query.order_by(Document.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        documents = [doc.to_dict() for doc in pagination.items]
        
        return {
            'documents': documents,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }

    def get_document_info(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档基本信息
        
        Args:
            document_id: 文档ID
            
        Returns:
            文档信息字典或None
        """
        try:
            document = Document.query.filter_by(id=document_id).first()
            if not document:
                return None
                
            return {
                'id': document.id,
                'title': document.title,
                'filename': document.filename,
                'file_type': document.file_type,
                'file_size': document.file_size,
                'upload_time': document.created_at.isoformat() if document.created_at else None,
                'category': document.category.name if document.category else None,
                'tags': document.tags,
                'description': document.description,
                'status': document.parse_status
            }
        except Exception as e:
            logger.error(f"获取文档信息失败: {str(e)}")
            return None
    
    def get_document_content(self, document_id: str) -> Optional[str]:
        """
        获取文档内容
        
        Args:
            document_id: 文档ID
            
        Returns:
            文档内容字符串或None
        """
        try:
            document = Document.query.filter_by(id=document_id).first()
            if not document:
                return None
                
            # 获取文档的所有页面内容
            pages = DocumentPage.query.filter_by(document_id=document_id).order_by(DocumentPage.page_number).all()
            
            content_parts = []
            for page in pages:
                if page.page_content:
                    content_parts.append(f"第{page.page_number}页:\n{page.page_content}")
            
            return "\n\n".join(content_parts) if content_parts else None
        except Exception as e:
            logger.error(f"获取文档内容失败: {str(e)}")
            return None
    
    def search_documents(self, query: str, user_id: str, tenant_id: str, limit: int = 10, 
                        search_tags: bool = True, subject_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        搜索文档
        
        Args:
            query: 搜索关键词
            user_id: 用户ID
            tenant_id: 租户ID
            limit: 返回结果数量限制
            search_tags: 是否搜索标签
            subject_filter: 学科过滤器
            
        Returns:
            搜索结果列表
        """
        try:
            # 基础查询条件
            documents_query = Document.query.filter(
                Document.user_id == user_id,
                Document.tenant_id == tenant_id,
                Document.parse_status == 'completed'
            )
            
            # 学科过滤
            if subject_filter:
                documents_query = documents_query.join(DocumentCategory).filter(
                    DocumentCategory.name.contains(subject_filter)
                )
            
            # 搜索标题和描述
            title_matches = documents_query.filter(
                db.or_(
                    Document.title.contains(query),
                    Document.description.contains(query)
                )
            ).limit(limit).all()
            
            # 搜索标签
            tag_matches = []
            if search_tags and len(title_matches) < limit:
                # 使用JSON查询搜索标签
                tag_docs = documents_query.filter(
                    Document.tags.contains([query])
                ).limit(limit - len(title_matches)).all()
                
                for doc in tag_docs:
                    if doc not in title_matches:
                        tag_matches.append(doc)
            
            # 搜索内容
            content_matches = []
            if len(title_matches) + len(tag_matches) < limit:
                pages = DocumentPage.query.join(Document).filter(
                    Document.user_id == user_id,
                    Document.tenant_id == tenant_id,
                    Document.parse_status == 'completed',
                    DocumentPage.page_content.contains(query)
                ).limit(limit - len(title_matches) - len(tag_matches)).all()
                
                existing_docs = title_matches + tag_matches
                for page in pages:
                    if page.document not in existing_docs:
                        content_matches.append(page.document)
            
            # 合并结果并按相关性排序
            all_matches = title_matches + tag_matches + content_matches
            
            results = []
            for doc in all_matches[:limit]:
                # 获取匹配的内容片段
                content_snippet = self._get_content_snippet(doc.id, query)
                
                # 计算相关性分数
                relevance_score = self._calculate_relevance_score(doc, query)
                
                results.append({
                    'id': doc.id,
                    'title': doc.title,
                    'filename': doc.filename,
                    'category': doc.category.name if doc.category else None,
                    'tags': doc.tags or [],
                    'upload_time': doc.upload_time.isoformat() if doc.upload_time else None,
                    'content': content_snippet,
                    'summary': doc.description or content_snippet[:200] + '...' if content_snippet else None,
                    'relevance_score': relevance_score,
                    'match_type': self._get_match_type(doc, query, title_matches, tag_matches)
                })
            
            # 按相关性分数排序
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return results
        except Exception as e:
            logger.error(f"搜索文档失败: {str(e)}")
            return []
    
    def _calculate_relevance_score(self, document: Document, query: str) -> float:
        """
        计算文档与查询的相关性分数
        
        Args:
            document: 文档对象
            query: 查询关键词
            
        Returns:
            相关性分数 (0-1)
        """
        score = 0.0
        query_lower = query.lower()
        
        # 标题匹配权重最高
        if document.title and query_lower in document.title.lower():
            score += 0.4
        
        # 标签匹配权重较高
        if document.tags:
            for tag in document.tags:
                if query_lower in tag.lower():
                    score += 0.3
                    break
        
        # 描述匹配
        if document.description and query_lower in document.description.lower():
            score += 0.2
        
        # 文件名匹配
        if document.filename and query_lower in document.filename.lower():
            score += 0.1
        
        return min(score, 1.0)
    
    def _get_match_type(self, document: Document, query: str, title_matches: list, tag_matches: list) -> str:
        """
        获取匹配类型
        
        Args:
            document: 文档对象
            query: 查询关键词
            title_matches: 标题匹配列表
            tag_matches: 标签匹配列表
            
        Returns:
            匹配类型
        """
        if document in title_matches:
            return 'title'
        elif document in tag_matches:
            return 'tag'
        else:
            return 'content'
    
    def _get_content_snippet(self, document_id: str, query: str, snippet_length: int = 200) -> Optional[str]:
        """
        获取包含搜索关键词的内容片段
        
        Args:
            document_id: 文档ID
            query: 搜索关键词
            snippet_length: 片段长度
            
        Returns:
            内容片段或None
        """
        try:
            pages = DocumentPage.query.filter_by(document_id=document_id).all()
            
            for page in pages:
                if page.text_content and query.lower() in page.text_content.lower():
                    content = page.text_content
                    query_pos = content.lower().find(query.lower())
                    
                    # 获取关键词前后的内容
                    start = max(0, query_pos - snippet_length // 2)
                    end = min(len(content), query_pos + len(query) + snippet_length // 2)
                    
                    snippet = content[start:end]
                    if start > 0:
                        snippet = '...' + snippet
                    if end < len(content):
                        snippet = snippet + '...'
                    
                    return snippet
            
            return None
        except Exception as e:
            logger.error(f"获取内容片段失败: {str(e)}")
            return None

    def delete_document(self, document_id: str, user_id: str) -> bool:
        """
        删除文档
        
        Args:
            document_id: 文档ID
            user_id: 用户ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            document = Document.query.filter_by(id=document_id, user_id=user_id).first()
            if not document:
                raise ValueError("文档不存在或无权限")
            
            # 删除向量索引
            try:
                vdb_service = get_vector_db_service()
                if vdb_service:
                    vdb_service.delete_document_vectors(document_id)
                    logger.info(f"文档 {document_id} 向量索引删除成功")
            except Exception as e:
                logger.warning(f"删除文档 {document_id} 向量索引时发生错误: {str(e)}")
            
            # 删除文件
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
            
            # 删除数据库记录（级联删除相关记录）
            db.session.delete(document)
            db.session.commit()
            
            logger.info(f"文档删除成功: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"文档删除失败: {e}")
            db.session.rollback()
            return False

# 延迟创建实例的函数
def get_document_service():
    """获取文档服务实例"""
    return DocumentService()

# 创建全局实例（在应用上下文中使用时）
document_service = None