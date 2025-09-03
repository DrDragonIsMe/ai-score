#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 业务服务 - ai_assistant_service.py

Description:
    AI助理"高小分"服务，提供智能对话、拍照识别试题、个性化学习建议等功能。

Author: Chang Xinglong
Date: 2025-01-21
Version: 1.0.0
License: Apache License 2.0
"""

import json
import base64
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from PIL import Image
import io
import pytesseract
from utils.database import db
from models.user import User
from models.diagnosis import DiagnosisReport, WeaknessPoint
from models.knowledge import KnowledgePoint, Subject
from models.exam import ExamSession, ExamAnalytics
from models.exam_papers import ExamPaper
from models.mistake import MistakeRecord, MistakeReviewSession, MistakePattern
from models.learning import StudyRecord, MemoryCard
from services.llm_service import llm_service
from services.diagnosis_service import DiagnosisService
from services.document_service import get_document_service
from services.vector_database_service import vector_db_service
from services.ppt_generation_service import ppt_generation_service
from utils.logger import get_logger

logger = get_logger(__name__)

class AIAssistantService:
    """
    AI助理"高小分"服务类
    """
    
    def __init__(self):
        self.assistant_name = "高小分"
        self.assistant_personality = {
            "role": "智能学习助手",
            "traits": ["友善", "耐心", "专业", "鼓励性"],
            "greeting": "你好！我是高小分，你的专属学习助手。我可以帮你分析试题、制定学习计划，还能通过拍照识别题目哦！"
        }
    
    def get_assistant_info(self) -> Dict[str, Any]:
        """
        获取AI助理基本信息
        """
        return {
            "name": self.assistant_name,
            "personality": self.assistant_personality,
            "capabilities": [
                "智能对话交流",
                "拍照识别试题",
                "试题分析解答",
                "个性化学习建议",
                "学习进度跟踪",
                "知识点推荐",
                "PDF文档分析",
                "文档内容问答"
            ]
        }
    
    def chat_with_user(self, user_id: str, message: str, context: Optional[Dict] = None, 
                      model_id: Optional[str] = None, template_id: Optional[str] = None) -> Dict[str, Any]:
        """
        与用户进行智能对话
        
        Args:
            user_id: 用户ID
            message: 用户消息
            context: 对话上下文
            model_id: 指定使用的AI模型ID
            template_id: PPT模板ID（用于PPT生成）
        
        Returns:
            AI助理回复
        """
        try:
            # 检测是否需要生成PPT
            if self._should_generate_ppt(message):
                return self._handle_ppt_generation(user_id, message, template_id)
            
            # 获取用户信息和学习情况
            user_profile = self._get_user_learning_profile(user_id)
            
            # 检索综合数据（文档、试卷、错题记录等）
            comprehensive_data = self._retrieve_comprehensive_data(user_id, message)
            
            # 构建对话提示词（包含综合数据信息）
            system_prompt = self._build_comprehensive_chat_prompt(user_profile, context, comprehensive_data)
            
            # 调用大模型生成回复
            full_prompt = f"{system_prompt}\n\n用户: {message}\n\n高小分:"
            
            response = llm_service.generate_text(
                prompt=full_prompt,
                max_tokens=500,
                temperature=0.7,
                model_name=model_id
            )
            
            return {
                "success": True,
                "response": response,
                "assistant_name": self.assistant_name,
                "model_used": model_id or "default",
                "timestamp": datetime.now().isoformat(),
                "suggestions": self._generate_contextual_suggestions(user_id, message),
                "referenced_data": comprehensive_data
            }
            
        except Exception as e:
            logger.error(f"AI助理对话失败: {str(e)}")
            return {
                "success": False,
                "response": "抱歉，我现在有点忙，请稍后再试。",
                "error": str(e)
            }
    
    def recognize_question_from_image(self, user_id: str, image_data: str) -> Dict[str, Any]:
        """
        从图片中识别试题或描述图片内容
        
        Args:
            user_id: 用户ID
            image_data: Base64编码的图片数据
        
        Returns:
            识别结果
        """
        try:
            # 解码图片
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # OCR识别文字
            extracted_text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            
            # 如果没有识别到文字，尝试描述图片内容
            if not extracted_text.strip():
                image_description = self._describe_image_content(image_data, user_id)
                return {
                    "success": True,
                    "content_type": "image_description",
                    "description": image_description,
                    "message": "这张图片没有文字内容，我来为你描述一下图片内容。",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 使用AI分析识别的文本，判断是否为题目
            content_analysis = self._analyze_extracted_text(extracted_text, user_id)
            
            logger.info(f"图片识别成功 - 提取文本: {extracted_text[:100]}...")
            logger.info(f"内容分析结果: {content_analysis}")
            
            # 根据分析结果决定处理方式
            if content_analysis.get('is_question', False):
                return {
                    "success": True,
                    "content_type": "question",
                    "extracted_text": extracted_text,
                    "question_analysis": content_analysis,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # 不是题目，描述图片内容
                image_description = self._describe_image_content(image_data, user_id, extracted_text)
                return {
                    "success": True,
                    "content_type": "image_description",
                    "extracted_text": extracted_text,
                    "description": image_description,
                    "message": "这张图片不是题目，我来为你介绍一下图片内容。",
                    "timestamp": datetime.now().isoformat()
                }
            
        except Exception as e:
            logger.error(f"图片识别失败: {str(e)}")
            return {
                "success": False,
                "message": "图片识别失败，请重试。",
                "error": str(e)
            }
    
    def analyze_and_solve_question(self, user_id: str, question_text: str, 
                                 user_answer: Optional[str] = None) -> Dict[str, Any]:
        """
        分析并解答试题
        
        Args:
            user_id: 用户ID
            question_text: 题目文本
            user_answer: 用户答案（可选）
        
        Returns:
            分析结果
        """
        try:
            # 获取用户学习情况
            user_profile = self._get_user_learning_profile(user_id)
            
            # 构建分析提示词
            analysis_prompt = self._build_question_analysis_prompt(
                question_text, user_answer, user_profile
            )
            
            # 调用大模型进行分析
            analysis_result = llm_service.generate_text(
                prompt=analysis_prompt,
                max_tokens=1000,
                temperature=0.3
            )
            
            # 解析分析结果
            parsed_result = self._parse_analysis_result(analysis_result)
            
            # 生成个性化建议
            personalized_suggestions = self._generate_personalized_suggestions(
                user_id, question_text, parsed_result
            )
            
            return {
                "success": True,
                "analysis": parsed_result,
                "suggestions": personalized_suggestions,
                "assistant_comment": self._generate_assistant_comment(parsed_result, user_answer),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"题目分析失败: {str(e)}")
            return {
                "success": False,
                "message": "题目分析失败，请重试。",
                "error": str(e)
            }
    
    def get_personalized_recommendations(self, user_id: str) -> Dict[str, Any]:
        """
        获取个性化学习建议
        
        Args:
            user_id: 用户ID
        
        Returns:
            个性化建议
        """
        try:
            # 获取用户学习诊断数据
            user_profile = self._get_user_learning_profile(user_id)
            diagnosis_data = self._get_user_diagnosis_data(user_id)
            
            # 生成个性化建议
            recommendations = {
                "daily_study_plan": self._generate_daily_study_plan(user_profile, diagnosis_data),
                "weak_points_focus": self._get_weak_points_recommendations(user_id),
                "practice_suggestions": self._generate_practice_suggestions(user_profile),
                "motivational_message": self._generate_motivational_message(user_profile)
            }
            
            return {
                "success": True,
                "recommendations": recommendations,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取个性化建议失败: {str(e)}")
            return {
                "success": False,
                "message": "获取建议失败，请重试。",
                "error": str(e)
            }
    
    def analyze_document_content(self, user_id: str, document_id: str, question: Optional[str] = None) -> Dict[str, Any]:
        """
        分析PDF文档内容并回答相关问题
        
        Args:
            user_id: 用户ID
            document_id: 文档ID
            question: 用户问题（可选）
        
        Returns:
            文档分析结果
        """
        try:
            document_service = get_document_service()
            
            # 获取文档信息
            document_info = document_service.get_document_info(document_id)
            if not document_info:
                return {
                    "success": False,
                    "message": "文档不存在或已被删除"
                }
            
            # 获取文档内容
            document_content = document_service.get_document_content(document_id)
            if not document_content:
                return {
                    "success": False,
                    "message": "无法获取文档内容"
                }
            
            # 获取用户学习档案
            user_profile = self._get_user_learning_profile(user_id)
            
            # 构建分析提示词
            if question:
                # 基于问题的文档问答
                analysis_prompt = self._build_document_qa_prompt(
                    document_info, document_content, question, user_profile
                )
            else:
                # 文档内容总结分析
                analysis_prompt = self._build_document_analysis_prompt(
                    document_info, document_content, user_profile
                )
            
            # 调用大模型进行分析
            analysis_result = llm_service.generate_text(
                prompt=analysis_prompt,
                max_tokens=1000,
                temperature=0.3
            )
            
            # 生成学习建议
            learning_suggestions = self._generate_document_learning_suggestions(
                user_id, document_info, document_content
            )
            
            return {
                "success": True,
                "document_info": {
                    "title": document_info.get('title', ''),
                    "category": document_info.get('category', ''),
                    "upload_time": document_info.get('upload_time', '')
                },
                "analysis": analysis_result,
                "learning_suggestions": learning_suggestions,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"文档分析失败: {str(e)}")
            return {
                "success": False,
                "message": "文档分析失败，请重试。",
                "error": str(e)
            }
    
    def search_documents_by_content(self, user_id: str, query: str) -> Dict[str, Any]:
        """
        根据内容搜索用户的PDF文档
        
        Args:
            user_id: 用户ID
            query: 搜索查询
        
        Returns:
            搜索结果
        """
        try:
            document_service = get_document_service()
            
            # 搜索文档
            search_results = document_service.search_documents(
                query=query,
                user_id=user_id,
                tenant_id="default"
            )
            
            if not search_results:
                return {
                    "success": True,
                    "results": [],
                    "message": "没有找到相关文档，建议上传更多学习资料。",
                    "suggestions": [
                        "尝试使用不同的关键词搜索",
                        "上传更多相关的PDF文档",
                        "检查搜索词的拼写"
                    ]
                }
            
            # 为每个结果生成简要说明
            enhanced_results = []
            for doc in search_results[:5]:  # 限制返回前5个结果
                doc_summary = self._generate_document_summary(doc)
                enhanced_results.append({
                    "document_id": doc.get('id'),
                    "title": doc.get('title', ''),
                    "category": doc.get('category', ''),
                    "relevance_score": doc.get('relevance_score', 0),
                    "summary": doc_summary,
                    "upload_time": doc.get('upload_time', '')
                })
            
            return {
                "success": True,
                "results": enhanced_results,
                "total_found": len(search_results),
                "message": f"找到 {len(search_results)} 个相关文档",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"文档搜索失败: {str(e)}")
            return {
                "success": False,
                "message": "文档搜索失败，请重试。",
                "error": str(e)
            }
    
    def _get_user_learning_profile(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户学习档案
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {}
            
            # 获取最近的诊断报告
            recent_reports = DiagnosisReport.query.filter_by(
                user_id=user_id
            ).order_by(DiagnosisReport.created_at.desc()).limit(3).all()
            
            profile = {
                "user_id": user_id,
                "username": user.username,
                "real_name": getattr(user, 'real_name', None),
                "nickname": getattr(user, 'nickname', None),
                "preferred_greeting": getattr(user, 'preferred_greeting', 'casual'),
                "grade_level": getattr(user, 'grade_level', '未知'),
                "recent_reports": len(recent_reports),
                "learning_style": self._infer_learning_style(recent_reports),
                "strong_subjects": self._get_strong_subjects(recent_reports),
                "weak_areas": self._get_weak_areas(user_id)
            }
            
            return profile
            
        except Exception as e:
            logger.error(f"获取用户学习档案失败: {str(e)}")
            return {}
    
    def _retrieve_relevant_documents(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        """
        检索与查询相关的文档
        
        Args:
            user_id: 用户ID
            query: 查询文本
        
        Returns:
            相关文档列表
        """
        try:
            # 使用向量数据库进行语义搜索
            similar_docs = vector_db_service.search_similar_documents(
                query=query,
                top_k=3,
                similarity_threshold=0.4
            )
            
            if not similar_docs:
                return []
            
            # 获取文档详细信息
            document_service = get_document_service()
            relevant_documents = []
            
            for doc in similar_docs:
                try:
                    # 根据文档类型获取详细信息
                    if doc['document_type'] == 'document':
                        doc_info = document_service.get_document_info(doc['document_id'])
                        if doc_info:
                            relevant_documents.append({
                                'id': doc['document_id'],
                                'type': 'document',
                                'title': doc_info.get('title', '未知文档'),
                                'content_snippet': doc['content'][:200] + '...' if len(doc['content']) > 200 else doc['content'],
                                'similarity': doc['similarity'],
                                'preview_url': f"/api/document/{doc['document_id']}/preview",
                                'metadata': doc.get('metadata', {})
                            })
                    elif doc['document_type'] == 'exam_paper':
                        # 处理试卷文档
                        relevant_documents.append({
                            'id': doc['document_id'],
                            'type': 'exam_paper',
                            'title': f"试卷 {doc['document_id']}",
                            'content_snippet': doc['content'][:200] + '...' if len(doc['content']) > 200 else doc['content'],
                            'similarity': doc['similarity'],
                            'preview_url': f"/api/exam_papers/{doc['document_id']}/preview",
                            'metadata': doc.get('metadata', {})
                        })
                except Exception as e:
                    logger.warning(f"获取文档 {doc['document_id']} 详细信息失败: {str(e)}")
                    continue
            
            logger.info(f"为查询 '{query}' 找到 {len(relevant_documents)} 个相关文档")
            return relevant_documents
            
        except Exception as e:
            logger.error(f"文档检索失败: {str(e)}")
            return []
    
    def _retrieve_comprehensive_data(self, user_id: str, query: str) -> Dict[str, Any]:
        """
        检索综合数据，包括文档、试卷、错题记录和学习情况
        
        Args:
            user_id: 用户ID
            query: 查询内容
        
        Returns:
            综合数据字典
        """
        try:
            # 检索相关文档
            documents = self._retrieve_relevant_documents(user_id, query)
            
            # 检索试卷数据
            exam_papers = self._get_exam_papers_data(user_id, query)
            
            # 检索错题记录
            mistake_records = self._get_mistake_records_data(user_id, query)
            
            # 检索考试会话
            exam_sessions = self._get_exam_sessions_data(user_id, query)
            
            # 检索学习记录
            study_records = self._get_study_records_data(user_id, query)
            
            # 获取学习分析数据
            learning_analytics = self._get_learning_analytics_data(user_id)
            
            return {
                'documents': documents,
                'exam_papers': exam_papers,
                'mistake_records': mistake_records,
                'exam_sessions': exam_sessions,
                'study_records': study_records,
                'learning_analytics': learning_analytics
            }
            
        except Exception as e:
            logger.error(f"检索综合数据失败: {str(e)}")
            return {}
    
    def _build_chat_prompt(self, user_profile: Dict, context: Optional[Dict] = None, 
                          relevant_documents: Optional[List[Dict]] = None) -> str:
        """
        构建对话提示词
        """
        # 确定用户称呼
        user_nickname = user_profile.get('nickname') or user_profile.get('real_name') or user_profile.get('username', '同学')
        preferred_greeting = user_profile.get('preferred_greeting', 'casual')
        
        # 根据问候偏好设置称呼方式
        greeting_styles = {
            'formal': f'您好，{user_nickname}',
            'casual': f'嗨，{user_nickname}',
            'friendly': f'{user_nickname}，你好',
            'professional': f'{user_nickname}同学'
        }
        
        greeting_style = greeting_styles.get(preferred_greeting, f'你好，{user_nickname}')
        
        base_prompt = f"""
你是{self.assistant_name}，一个友善、耐心、专业的AI学习助手。你的任务是帮助学生提高学习效果。

用户信息：
- 称呼：{user_nickname}
- 问候方式：{greeting_style}
- 年级：{user_profile.get('grade_level', '未知')}
- 擅长科目：{', '.join(user_profile.get('strong_subjects', []))}
- 薄弱环节：{', '.join(user_profile.get('weak_areas', []))}

对话风格要求：
- 在回复开始时使用设定的问候方式称呼用户
- 在对话中适当使用用户的称呼
- 根据用户偏好调整语言风格（正式/亲切/友好/专业）
- 使用友善、鼓励性的语言
- 根据用户的学习情况提供针对性建议
- 适当使用表情符号增加亲和力
- 保持专业性，提供准确的学习指导
"""
        
        # 添加相关文档信息
        if relevant_documents:
            base_prompt += "\n\n相关参考资料："
            for i, doc in enumerate(relevant_documents, 1):
                doc_type_name = "文档" if doc['type'] == 'document' else "试卷"
                base_prompt += f"""
{i}. {doc_type_name}：{doc['title']}
   内容摘要：{doc['content_snippet']}
   预览链接：{doc['preview_url']}
   相关度：{doc['similarity']:.2f}"""
            
            base_prompt += "\n\n回答指导："
            base_prompt += "\n- 当回答涉及上述参考资料时，请引用相关内容并提供预览链接"
            base_prompt += "\n- 使用格式：[文档标题](预览链接) 来引用文档"
            base_prompt += "\n- 结合参考资料为用户提供更准确、详细的解答"
        
        if context:
            base_prompt += f"\n\n对话上下文：{json.dumps(context, ensure_ascii=False)}"
        
        return base_prompt
    
    def _build_comprehensive_chat_prompt(self, user_profile: Dict, context: Optional[Dict] = None, 
                                       comprehensive_data: Optional[Dict] = None) -> str:
        """
        构建包含综合数据的对话提示词
        """
        # 确定用户称呼
        user_nickname = user_profile.get('nickname') or user_profile.get('real_name') or user_profile.get('username', '同学')
        preferred_greeting = user_profile.get('preferred_greeting', 'casual')
        
        # 根据问候偏好设置称呼方式
        greeting_styles = {
            'formal': f'您好，{user_nickname}',
            'casual': f'嗨，{user_nickname}',
            'friendly': f'{user_nickname}，你好',
            'professional': f'{user_nickname}同学'
        }
        
        greeting_style = greeting_styles.get(preferred_greeting, f'你好，{user_nickname}')
        
        base_prompt = f"""
你是{self.assistant_name}，一个友善、耐心、专业的AI学习助手。你的任务是帮助学生提高学习效果。

用户信息：
- 称呼：{user_nickname}
- 问候方式：{greeting_style}
- 年级：{user_profile.get('grade_level', '未知')}
- 擅长科目：{', '.join(user_profile.get('strong_subjects', []))}
- 薄弱环节：{', '.join(user_profile.get('weak_areas', []))}

对话风格要求：
- 在回复开始时使用设定的问候方式称呼用户
- 在对话中适当使用用户的称呼
- 根据用户偏好调整语言风格（正式/亲切/友好/专业）
- 使用友善、鼓励性的语言
- 根据用户的学习情况提供针对性建议
- 适当使用表情符号增加亲和力
- 保持专业性，提供准确的学习指导
"""
        
        if comprehensive_data:
            # 添加文档信息
            documents = comprehensive_data.get('documents', [])
            if documents:
                base_prompt += "\n\n相关文档资料："
                for i, doc in enumerate(documents[:3], 1):
                    base_prompt += f"\n{i}. {doc['title']} - {doc['content_snippet'][:100]}..."
            
            # 添加试卷信息
            exam_papers = comprehensive_data.get('exam_papers', [])
            if exam_papers:
                base_prompt += "\n\n相关试卷："
                for i, paper in enumerate(exam_papers[:3], 1):
                    base_prompt += f"\n{i}. {paper['title']} ({paper['year']}年 {paper['exam_type']})"
            
            # 添加错题记录信息
            mistake_records = comprehensive_data.get('mistake_records', [])
            if mistake_records:
                base_prompt += f"\n\n用户错题情况：共有{len(mistake_records)}道错题记录"
                resolved_count = sum(1 for m in mistake_records if m.get('is_resolved'))
                base_prompt += f"，已解决{resolved_count}道"
            
            # 添加学习分析数据
            learning_analytics = comprehensive_data.get('learning_analytics', {})
            if learning_analytics:
                mistake_analysis = learning_analytics.get('mistake_analysis', {})
                exam_performance = learning_analytics.get('exam_performance', {})
                if mistake_analysis.get('total_mistakes', 0) > 0:
                    base_prompt += f"\n\n学习分析：最近30天错题{mistake_analysis['total_mistakes']}道，解决率{mistake_analysis.get('resolution_rate', 0):.1f}%"
                if exam_performance.get('total_exams', 0) > 0:
                    base_prompt += f"，平均考试成绩{exam_performance.get('average_score', 0):.1f}分"
            
            base_prompt += "\n\n回答指导："
            base_prompt += "\n- 结合用户的学习数据提供个性化建议"
            base_prompt += "\n- 针对错题记录和薄弱环节给出具体改进方案"
            base_prompt += "\n- 推荐相关的学习资料和练习题目"
            base_prompt += "\n- 鼓励用户并提供学习动力"
        
        if context:
            base_prompt += f"\n\n对话上下文：{json.dumps(context, ensure_ascii=False)}"
        
        return base_prompt
    
    def _analyze_extracted_text(self, text: str, user_id: str) -> Dict[str, Any]:
        """
        分析OCR提取的文本
        """
        prompt = f"""
请分析以下从图片中提取的文本，判断是否为试题，并提取关键信息：

提取的文本：
{text}

请以JSON格式返回分析结果，包含：
1. is_question: 是否为试题（true/false）
2. subject: 科目（如：数学、物理、化学等）
3. question_type: 题型（如：选择题、填空题、解答题等）
4. difficulty_level: 难度等级（1-5）
5. key_concepts: 涉及的关键概念
6. cleaned_question: 清理后的题目文本
"""
        
        try:
            result = llm_service.generate_text(prompt, max_tokens=500)
            return json.loads(result)
        except:
            return {
                "is_question": True,
                "subject": "未知",
                "question_type": "未知",
                "difficulty_level": 3,
                "key_concepts": [],
                "cleaned_question": text
            }
    
    def _describe_image_content(self, image_data: str, user_id: str, extracted_text: Optional[str] = None) -> str:
        """
        描述图片内容
        
        Args:
            image_data: Base64编码的图片数据
            user_id: 用户ID
            extracted_text: OCR提取的文本（可选）
        
        Returns:
            图片内容描述
        """
        try:
            # 构建描述提示
            if extracted_text:
                prompt = f"""
请根据以下信息描述这张图片的内容：

图片中的文字内容：
{extracted_text}

请用友好、详细的语言描述这张图片，包括：
1. 图片的主要内容和主题
2. 图片中的文字信息
3. 可能的用途或背景
4. 其他值得注意的细节

请以自然、易懂的方式描述，就像在和朋友聊天一样。
"""
            else:
                prompt = """
这是一张没有文字内容的图片。请描述这张图片可能包含的内容，比如：
1. 可能是什么类型的图片（照片、图表、插画等）
2. 可能的主题或内容
3. 建议用户如何更好地使用图片识别功能

请用友好、鼓励的语气回复。
"""
            
            result = llm_service.generate_text(prompt, max_tokens=300)
            return result.strip()
            
        except Exception as e:
            logger.error(f"图片内容描述失败: {str(e)}")
            if extracted_text:
                return f"我看到这张图片包含以下文字内容：{extracted_text[:200]}...\n\n这看起来不是一道题目，而是包含文字信息的图片。如果你需要我帮助分析特定内容，请告诉我你想了解什么！"
            else:
                return "这张图片没有包含文字内容。如果你想让我识别题目，请确保图片清晰且包含题目文字。我也可以帮你分析其他包含文字的学习材料！"
    
    def _build_question_analysis_prompt(self, question: str, user_answer: Optional[str], 
                                      user_profile: Dict) -> str:
        """
        构建题目分析提示词
        """
        # 确定用户称呼
        user_nickname = user_profile.get('nickname') or user_profile.get('real_name') or user_profile.get('username', '同学')
        preferred_greeting = user_profile.get('preferred_greeting', 'casual')
        
        # 根据问候偏好设置称呼方式
        greeting_styles = {
            'formal': f'您好，{user_nickname}',
            'casual': f'嗨，{user_nickname}',
            'friendly': f'{user_nickname}，你好',
            'professional': f'{user_nickname}同学'
        }
        
        greeting_style = greeting_styles.get(preferred_greeting, f'你好，{user_nickname}')
        
        prompt = f"""
作为专业的学习助手{self.assistant_name}，请分析以下题目：

题目：
{question}
"""
        
        if user_answer:
            prompt += f"\n\n学生答案：\n{user_answer}"
        
        prompt += f"""

用户信息：
- 称呼：{user_nickname}
- 问候方式：{greeting_style}
- 擅长领域：{', '.join(user_profile.get('strong_subjects', []))}
- 薄弱环节：{', '.join(user_profile.get('weak_areas', []))}

请提供：
1. 题目解析和标准答案
2. 解题思路和方法
3. 相关知识点
4. 常见错误分析
5. 针对该用户的个性化建议

回答要求：
- 在回复开始时使用设定的问候方式称呼用户
- 在分析过程中适当使用用户的称呼
- 根据用户偏好调整语言风格（正式/亲切/友好/专业）
- 用友善、鼓励的语调回答
"""
        
        return prompt
    
    def _parse_analysis_result(self, result: str) -> Dict[str, Any]:
        """
        解析分析结果
        """
        # 简单的结果解析，实际可以更复杂
        return {
            "solution": result,
            "confidence": 0.85,
            "key_points": [],
            "difficulty": "中等"
        }
    
    def _generate_personalized_suggestions(self, user_id: str, question: str, 
                                         analysis: Dict) -> List[str]:
        """
        生成个性化建议
        """
        suggestions = [
            "建议多练习类似题型，加强理解",
            "可以复习相关的基础知识点",
            "尝试用不同方法解决同一问题"
        ]
        
        # 根据用户薄弱环节添加针对性建议
        weak_areas = self._get_weak_areas(user_id)
        for area in weak_areas:
            suggestions.append(f"针对{area}，建议加强专项练习")
        
        return suggestions[:5]  # 限制建议数量
    
    def _generate_assistant_comment(self, analysis: Dict, user_answer: Optional[str]) -> str:
        """
        生成助理评论
        """
        if user_answer:
            return f"我看了你的答案，{self._get_encouraging_comment()}！让我来帮你分析一下这道题。"
        else:
            return f"这是一道很有意思的题目！{self._get_encouraging_comment()}，我来为你详细解析。"
    
    def _get_encouraging_comment(self) -> str:
        """
        获取鼓励性评论
        """
        comments = [
            "你很用心在思考",
            "继续保持这种学习态度",
            "你的思路很不错",
            "学习就是要这样积极主动",
            "我相信你能掌握这个知识点"
        ]
        import random
        return random.choice(comments)
    
    def _get_weak_areas(self, user_id: str) -> List[str]:
        """
        获取用户薄弱领域
        """
        try:
            weak_points = WeaknessPoint.query.filter_by(
                user_id=user_id
            ).order_by(WeaknessPoint.severity.desc()).limit(5).all()
            
            return [point.knowledge_point.name for point in weak_points 
                   if point.knowledge_point]
        except:
            return []
    
    def _generate_contextual_suggestions(self, user_id: str, message: str) -> List[str]:
        """
        生成上下文相关建议
        """
        suggestions = []
        
        # 根据消息内容生成建议
        if "题目" in message or "题" in message:
            suggestions.append("📸 可以拍照上传题目，我来帮你分析")
        
        if "不会" in message or "难" in message:
            suggestions.append("💪 别担心，我们一步步来解决")
            suggestions.append("📚 我可以推荐一些相关的练习")
        
        if "考试" in message:
            suggestions.append("📋 我可以帮你制定复习计划")
            suggestions.append("🎯 让我分析一下你的薄弱环节")
        
        return suggestions
    
    def _get_user_diagnosis_data(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户诊断数据
        """
        try:
            return DiagnosisService.get_diagnosis_statistics(user_id)
        except:
            return {}
    
    def _generate_daily_study_plan(self, user_profile: Dict, diagnosis_data: Dict) -> Dict[str, Any]:
        """
        生成每日学习计划
        """
        return {
            "morning": "复习昨日错题，巩固薄弱知识点",
            "afternoon": "新知识学习和理解",
            "evening": "练习题目，检验学习效果",
            "duration": "建议每个时段30-45分钟"
        }
    
    def _get_weak_points_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取薄弱点建议
        """
        weak_areas = self._get_weak_areas(user_id)
        recommendations = []
        
        for area in weak_areas[:3]:  # 只取前3个
            recommendations.append({
                "knowledge_point": area,
                "suggestion": f"建议加强{area}的基础练习",
                "priority": "高"
            })
        
        return recommendations
    
    def _generate_practice_suggestions(self, user_profile: Dict) -> List[str]:
        """
        生成练习建议
        """
        return [
            "每天坚持做3-5道相关题目",
            "定期回顾错题本",
            "尝试不同难度的题目挑战自己",
            "与同学讨论交流学习心得"
        ]
    
    def _generate_motivational_message(self, user_profile: Dict) -> str:
        """
        生成激励消息
        """
        messages = [
            "学习是一个持续的过程，你已经在进步的路上了！💪",
            "每一次练习都是向目标迈进的一步，加油！🌟",
            "相信自己，你有能力克服学习中的困难！🚀",
            "今天的努力就是明天的收获，继续保持！📈"
        ]
        import random
        return random.choice(messages)
    
    def _infer_learning_style(self, reports: List) -> str:
        """
        推断学习风格
        """
        if not reports:
            return "探索型"
        
        # 简单的学习风格推断逻辑
        styles = ["视觉型", "听觉型", "动手型", "逻辑型"]
        import random
        return random.choice(styles)
    
    def _get_strong_subjects(self, reports: List) -> List[str]:
        """
        获取擅长科目
        """
        # 简单实现，实际应该基于诊断数据分析
        return ["数学", "物理"] if reports else []
    
    def _build_document_qa_prompt(self, document_info: Dict, document_content: str, 
                                question: str, user_profile: Dict) -> str:
        """
        构建文档问答提示词
        """
        # 确定用户称呼
        user_nickname = user_profile.get('nickname') or user_profile.get('real_name') or user_profile.get('username', '同学')
        preferred_greeting = user_profile.get('preferred_greeting', 'casual')
        
        # 根据问候偏好设置称呼方式
        greeting_styles = {
            'formal': f'您好，{user_nickname}',
            'casual': f'嗨，{user_nickname}',
            'friendly': f'{user_nickname}，你好',
            'professional': f'{user_nickname}同学'
        }
        
        greeting_style = greeting_styles.get(preferred_greeting, f'你好，{user_nickname}')
        
        return f"""
你是高小分，一个专业的学习助手。用户上传了一个PDF文档，现在想要询问相关问题。

文档信息：
- 标题：{document_info.get('title', '未知')}
- 分类：{document_info.get('category', '未知')}

文档内容（前2000字符）：
{document_content[:2000]}...

用户问题：{question}

用户信息：
- 称呼：{user_nickname}
- 问候方式：{greeting_style}
- 年级：{user_profile.get('grade_level', '未知')}
- 强势学科：{', '.join(user_profile.get('strong_subjects', []))}
- 薄弱环节：{', '.join(user_profile.get('weak_areas', []))}

请基于文档内容回答用户的问题，并结合用户的学习情况给出个性化的学习建议。
回答要求：
1. 在回复开始时使用设定的问候方式称呼用户
2. 直接回答用户问题
3. 引用文档中的相关内容
4. 提供学习建议
5. 根据用户偏好调整语言风格（正式/亲切/友好/专业）
6. 语言要友善、鼓励性
"""
    
    def _build_document_analysis_prompt(self, document_info: Dict, document_content: str, 
                                      user_profile: Dict) -> str:
        """
        构建文档分析提示词
        """
        # 确定用户称呼
        user_nickname = user_profile.get('nickname') or user_profile.get('real_name') or user_profile.get('username', '同学')
        preferred_greeting = user_profile.get('preferred_greeting', 'casual')
        
        # 根据问候偏好设置称呼方式
        greeting_styles = {
            'formal': f'您好，{user_nickname}',
            'casual': f'嗨，{user_nickname}',
            'friendly': f'{user_nickname}，你好',
            'professional': f'{user_nickname}同学'
        }
        
        greeting_style = greeting_styles.get(preferred_greeting, f'你好，{user_nickname}')
        
        return f"""
你是高小分，一个专业的学习助手。用户上传了一个PDF文档，请帮助分析文档内容。

文档信息：
- 标题：{document_info.get('title', '未知')}
- 分类：{document_info.get('category', '未知')}

文档内容（前2000字符）：
{document_content[:2000]}...

用户信息：
- 称呼：{user_nickname}
- 问候方式：{greeting_style}
- 年级：{user_profile.get('grade_level', '未知')}
- 强势学科：{', '.join(user_profile.get('strong_subjects', []))}
- 薄弱环节：{', '.join(user_profile.get('weak_areas', []))}

请分析这个文档的内容，包括：
1. 文档主要内容概述
2. 涉及的知识点
3. 难度等级评估
4. 对用户的学习价值
5. 个性化学习建议

回答要求：
- 在回复开始时使用设定的问候方式称呼用户
- 根据用户偏好调整语言风格（正式/亲切/友好/专业）
- 回答要友善、专业，并具有鼓励性
"""
    
    def _generate_document_learning_suggestions(self, user_id: str, document_info: Dict, 
                                             document_content: str) -> List[str]:
        """
        生成基于文档的学习建议
        """
        suggestions = []
        
        # 基于文档类别的建议
        category = document_info.get('category', '')
        if '数学' in category:
            suggestions.extend([
                "建议先理解基本概念，再练习相关题目",
                "可以制作思维导图整理知识点"
            ])
        elif '语文' in category:
            suggestions.extend([
                "建议多读几遍，理解文章结构和主旨",
                "可以摘抄好词好句，积累写作素材"
            ])
        elif '英语' in category:
            suggestions.extend([
                "建议先掌握生词，再理解文章内容",
                "可以朗读文章，提高语感"
            ])
        
        # 通用建议
        suggestions.extend([
            "建议制定学习计划，分阶段掌握内容",
            "遇到不懂的地方可以随时问我",
            "学习后可以做相关练习巩固知识"
        ])
        
        return suggestions[:5]  # 返回前5个建议
    
    def _generate_document_summary(self, document: Dict) -> str:
        """
        生成文档摘要
        """
        title = document.get('title', '未知文档')
        category = document.get('category', '未分类')
        content_preview = document.get('content', '')[:100] + '...' if document.get('content') else '暂无内容预览'
        
        return f"《{title}》- {category}类文档。{content_preview}"
    
    def _get_exam_papers_data(self, user_id: str, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取试卷数据
        
        Args:
            user_id: 用户ID
            query: 查询关键词（可选）
        
        Returns:
            试卷数据列表
        """
        try:
            # 构建查询
            exam_query = db.session.query(ExamPaper)
            
            if query:
                filters = []
                if hasattr(ExamPaper, 'title'):
                    filters.append(ExamPaper.title.contains(query))
                if hasattr(ExamPaper, 'description'):
                    filters.append(ExamPaper.description.contains(query))
                if hasattr(ExamPaper, 'exam_type'):
                    filters.append(ExamPaper.exam_type.contains(query))
                if hasattr(ExamPaper, 'region'):
                    filters.append(ExamPaper.region.contains(query))
                if filters:
                    exam_query = exam_query.filter(db.or_(*filters))
            
            # 限制返回数量
            exam_papers = exam_query.limit(10).all()
            
            papers_data = []
            for paper in exam_papers:
                papers_data.append({
                    'id': paper.id,
                    'title': paper.title,
                    'description': paper.description,
                    'year': paper.year,
                    'exam_type': paper.exam_type,
                    'region': paper.region,
                    'total_score': paper.total_score,
                    'duration': paper.duration,
                    'difficulty_level': paper.difficulty_level,
                    'question_count': paper.question_count,
                    'download_count': paper.download_count
                })
            
            return papers_data
            
        except Exception as e:
            logger.error(f"获取试卷数据失败: {str(e)}")
            return []
    
    def _get_mistake_records_data(self, user_id: str, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取错题记录数据
        
        Args:
            user_id: 用户ID
            query: 查询关键词（可选）
        
        Returns:
            错题记录数据列表
        """
        try:
            # 构建查询
            mistake_query = db.session.query(MistakeRecord).filter(
                MistakeRecord.user_id == user_id,
                MistakeRecord.is_archived == False
            )
            
            if query:
                # 关联查询题目内容
                from models.question import Question
                mistake_query = mistake_query.join(Question).filter(
                    db.or_(
                        Question.content.contains(query),
                        MistakeRecord.error_analysis.contains(query)
                    )
                )
            
            # 按时间排序，限制返回数量
            mistakes = mistake_query.order_by(
                MistakeRecord.created_time.desc()
            ).limit(20).all()
            
            mistakes_data = []
            for mistake in mistakes:
                mistakes_data.append({
                    'id': mistake.id,
                    'question_id': mistake.question_id,
                    'user_answer': mistake.user_answer,
                    'correct_answer': mistake.correct_answer,
                    'mistake_type': mistake.mistake_type.value if hasattr(mistake, 'mistake_type') and mistake.mistake_type is not None else None,
                    'mistake_level': mistake.mistake_level.value if hasattr(mistake, 'mistake_level') and mistake.mistake_level is not None else None,
                    'error_analysis': mistake.error_analysis,
                    'solution_steps': mistake.solution_steps,
                    'key_concepts': mistake.key_concepts,
                    'improvement_suggestions': mistake.improvement_suggestions,
                    'review_count': mistake.review_count,
                    'mastery_level': mistake.mastery_level,
                    'is_resolved': mistake.is_resolved,
                    'priority_score': getattr(mistake, 'priority_score', 0),
                    'created_time': mistake.created_time.isoformat() if hasattr(mistake, 'created_time') and mistake.created_time is not None else None,
                    'next_review_time': mistake.next_review_time.isoformat() if hasattr(mistake, 'next_review_time') and mistake.next_review_time is not None and hasattr(mistake.next_review_time, 'isoformat') else None
                })
            
            return mistakes_data
            
        except Exception as e:
            logger.error(f"获取错题记录失败: {str(e)}")
            return []
    
    def _get_exam_sessions_data(self, user_id: str, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取考试会话数据
        
        Args:
            user_id: 用户ID
            query: 查询关键词（可选）
        
        Returns:
            考试会话数据列表
        """
        try:
            # 构建查询
            exam_query = db.session.query(ExamSession).filter(
                ExamSession.user_id == user_id
            )
            
            if query:
                filters = []
                if hasattr(ExamSession, 'title'):
                    filters.append(ExamSession.title.contains(query))
                if hasattr(ExamSession, 'description'):
                    filters.append(ExamSession.description.contains(query))
                if hasattr(ExamSession, 'exam_type'):
                    filters.append(ExamSession.exam_type.contains(query))
                if filters:
                    exam_query = exam_query.filter(db.or_(*filters))
            
            # 按时间排序，限制返回数量
            exams = exam_query.order_by(
                ExamSession.created_time.desc()
            ).limit(15).all()
            
            exams_data = []
            for exam in exams:
                exams_data.append({
                    'id': exam.id,
                    'title': exam.title,
                    'description': exam.description,
                    'exam_type': exam.exam_type,
                    'status': exam.status,
                    'total_questions': exam.total_questions,
                    'completed_questions': exam.completed_questions,
                    'total_score': exam.total_score,
                    'score_percentage': exam.score_percentage,
                    'correct_answers': exam.correct_answers,
                    'wrong_answers': exam.wrong_answers,
                    'time_efficiency': exam.time_efficiency,
                    'average_time_per_question': exam.average_time_per_question,
                    'created_time': exam.created_time.isoformat() if hasattr(exam, 'created_time') and exam.created_time is not None else None,
                    'actual_start_time': exam.actual_start_time.isoformat() if hasattr(exam, 'actual_start_time') and exam.actual_start_time is not None else None,
                    'end_time': exam.end_time.isoformat() if hasattr(exam, 'end_time') and exam.end_time is not None else None
                })
            
            return exams_data
            
        except Exception as e:
            logger.error(f"获取考试会话数据失败: {str(e)}")
            return []
    
    def _get_study_records_data(self, user_id: str, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取学习记录数据
        
        Args:
            user_id: 用户ID
            query: 查询关键词（可选）
        
        Returns:
            学习记录数据列表
        """
        try:
            # 构建查询
            study_query = db.session.query(StudyRecord).filter(
                StudyRecord.user_id == user_id
            )
            
            if query:
                filters = []
                if hasattr(StudyRecord, 'study_type') and hasattr(StudyRecord.study_type.property, 'columns'):
                    filters.append(StudyRecord.study_type.contains(query))
                if hasattr(StudyRecord, 'content_type') and hasattr(StudyRecord.content_type.property, 'columns'):
                    filters.append(StudyRecord.content_type.contains(query))
                if hasattr(StudyRecord, 'notes') and hasattr(StudyRecord.notes.property, 'columns'):
                    filters.append(StudyRecord.notes.contains(query))
                if filters:
                    study_query = study_query.filter(db.or_(*filters))
            
            # 按时间排序，限制返回数量
            records = study_query.order_by(
                StudyRecord.start_time.desc()
            ).limit(20).all()
            
            records_data = []
            for record in records:
                records_data.append({
                    'id': record.id,
                    'study_type': record.study_type,
                    'content_type': record.content_type,
                    'is_correct': record.is_correct,
                    'score': record.score,
                    'max_score': record.max_score,
                    'duration': record.duration,
                    'mastery_level': record.mastery_level,
                    'difficulty_rating': record.difficulty_rating,
                    'confidence_level': record.confidence_level,
                    'error_types': record.error_types,
                    'improvement_areas': record.improvement_areas,
                    'notes': record.notes,
                    'start_time': record.start_time.isoformat() if record.start_time else None,
                    'end_time': record.end_time.isoformat() if record.end_time else None
                })
            
            return records_data
            
        except Exception as e:
            logger.error(f"获取学习记录失败: {str(e)}")
            return []
    
    def _get_learning_analytics_data(self, user_id: str) -> Dict[str, Any]:
        """
        获取学习分析数据
        
        Args:
            user_id: 用户ID
        
        Returns:
            学习分析数据
        """
        try:
            from datetime import datetime, timedelta
            from sqlalchemy import func
            
            # 获取最近30天的数据
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            # 错题统计
            mistake_stats = db.session.query(
                func.count(MistakeRecord.id).label('total_mistakes'),
                func.count(func.case((MistakeRecord.is_resolved == True, 1))).label('resolved_mistakes'),
                func.avg(MistakeRecord.mastery_level).label('avg_mastery')
            ).filter(
                MistakeRecord.user_id == user_id
            ).first()
            
            # 考试统计
            exam_stats = db.session.query(
                func.count(ExamSession.id).label('total_exams'),
                func.avg(ExamSession.score_percentage).label('avg_score'),
                func.avg(ExamSession.time_efficiency).label('avg_efficiency')
            ).filter(
                ExamSession.user_id == user_id
            ).filter(
                ExamSession.created_time >= thirty_days_ago
            ).filter(
                ExamSession.status == 'completed' # type: ignore
            ).first()
            
            # 学习时长统计
            study_stats = db.session.query(
                func.sum(StudyRecord.duration).label('total_duration'),
                func.count(StudyRecord.id).label('total_sessions'),
                func.avg(StudyRecord.mastery_level).label('avg_mastery')
            ).filter(
                StudyRecord.user_id == user_id,
                StudyRecord.start_time >= thirty_days_ago
            ).first()
            
            return {
                'mistake_analysis': {
                    'total_mistakes': getattr(mistake_stats, 'total_mistakes', 0) or 0,
                    'resolved_mistakes': getattr(mistake_stats, 'resolved_mistakes', 0) or 0,
                    'average_mastery': float(getattr(mistake_stats, 'avg_mastery', 0) or 0),
                    'resolution_rate': (getattr(mistake_stats, 'resolved_mistakes', 0) or 0) / max(getattr(mistake_stats, 'total_mistakes', 1) or 1, 1) * 100
                },
                'exam_performance': {
                    'total_exams': getattr(exam_stats, 'total_exams', 0) or 0,
                    'average_score': float(getattr(exam_stats, 'avg_score', 0) or 0),
                    'average_efficiency': float(getattr(exam_stats, 'avg_efficiency', 0) or 0)
                },
                'study_habits': {
                    'total_duration': getattr(study_stats, 'total_duration', 0) or 0,
                    'total_sessions': getattr(study_stats, 'total_sessions', 0) or 0,
                    'average_mastery': float(getattr(study_stats, 'avg_mastery', 0) or 0),
                    'average_session_duration': (getattr(study_stats, 'total_duration', 0) or 0) / max(getattr(study_stats, 'total_sessions', 1) or 1, 1)
                }
            }
            
        except Exception as e:
            logger.error(f"获取学习分析数据失败: {str(e)}")
            return {}
    
    def _should_generate_ppt(self, message: str) -> bool:
        """
        检测用户消息是否包含生成PPT的请求
        """
        ppt_keywords = [
            'ppt', 'PPT', 'powerpoint', 'PowerPoint', 
            '幻灯片', '演示文稿', '课件', '生成ppt', 
            '制作ppt', '创建ppt', '做个ppt', '做一个ppt'
        ]
        
        message_lower = message.lower()
        return any(keyword.lower() in message_lower for keyword in ppt_keywords)
    
    def _handle_ppt_generation(self, user_id: str, message: str, template_id: Optional[str] = None) -> Dict[str, Any]:
        """
        处理PPT生成请求
        """
        try:
            # 调用PPT生成服务
            result = ppt_generation_service.generate_ppt_from_text(
                user_id=user_id,
                tenant_id="default",
                content=message,
                title="AI生成的演示文稿",
                template_id=template_id
            )
            
            if result['success']:
                data = result['data']
                filename = data['title'] + '.pptx'
                return {
                    "success": True,
                    "response": f"我已经为您生成了PPT！\n\n📄 文件名: {filename}\n🔗 下载链接: {data['download_url']}\n\n该PPT已自动保存到您的文档管理中，您可以随时查看和下载。",
                    "assistant_name": self.assistant_name,
                    "timestamp": datetime.now().isoformat(),
                    "ppt_info": {
                        "filename": filename,
                        "download_url": data['download_url'],
                        "document_id": data.get('document_id'),
                        "slides_count": data.get('slides_count')
                    },
                    "suggestions": [
                        "您可以点击下载链接获取PPT文件",
                        "PPT已保存在文档管理中，可随时查看",
                        "如需修改PPT内容，请告诉我具体要求"
                    ]
                }
            else:
                return {
                    "success": False,
                    "response": f"抱歉，PPT生成失败：{result.get('error', '未知错误')}。请稍后重试或提供更详细的内容要求。",
                    "assistant_name": self.assistant_name,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"PPT生成处理失败: {str(e)}")
            return {
                "success": False,
                "response": "抱歉，PPT生成功能暂时不可用，请稍后重试。",
                "error": str(e),
                "assistant_name": self.assistant_name,
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_ppt(self, content: str, template_id: Optional[str] = None, 
                    user_id: str = "1", tenant_id: str = "default") -> Dict[str, Any]:
        """
        生成PPT
        
        Args:
            content: PPT内容描述
            template_id: 模板ID（可选）
            user_id: 用户ID
            tenant_id: 租户ID
            
        Returns:
            Dict: 包含生成结果的字典
        """
        try:
            logger.info(f"开始生成PPT，用户ID: {user_id}, 模板ID: {template_id}")
            
            # 调用PPT生成服务
            result = ppt_generation_service.generate_ppt_from_text(
                content=content,
                user_id=user_id,
                tenant_id=tenant_id,
                template_id=template_id
            )
            
            if result.get('success'):
                logger.info(f"PPT生成成功: {result.get('filename')}")
                return {
                    "success": True,
                    "filename": result.get('filename'),
                    "download_url": result.get('download_url'),
                    "file_path": result.get('file_path'),
                    "message": "PPT生成成功"
                }
            else:
                logger.error(f"PPT生成失败: {result.get('error')}")
                return {
                    "success": False,
                    "message": result.get('error', 'PPT生成失败'),
                    "error": result.get('error')
                }
                
        except Exception as e:
            logger.error(f"PPT生成异常: {str(e)}")
            return {
                "success": False,
                "message": f"PPT生成失败: {str(e)}",
                "error": str(e)
            }

# 创建全局实例
ai_assistant_service = AIAssistantService()