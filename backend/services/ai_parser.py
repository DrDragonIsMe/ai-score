#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - AI解析服务 - ai_parser.py

Description:
    AI智能解析服务，用于解析试卷文件，识别题目并关联知识点。

Author: Chang Xinglong
Date: 2025-08-31
Version: 1.0.0
License: Apache License 2.0
"""

import os
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
from openai import OpenAI
from models import Question, KnowledgePoint, ExamPaper
from utils.database import db
from utils.logger import logger
from flask import current_app

class AIParser:
    """AI解析器类"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=current_app.config.get('OPENAI_API_KEY'),
            base_url=current_app.config.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        )
        
    def parse_exam_paper(self, exam_paper_id: str) -> Dict[str, Any]:
        """解析试卷文件"""
        try:
            # 获取试卷信息
            exam_paper = ExamPaper.query.get(exam_paper_id)
            if not exam_paper:
                raise ValueError(f"试卷不存在: {exam_paper_id}")
            
            # 根据文件类型选择解析方法
            if exam_paper.file_type.lower() == 'pdf':
                text_content = self._extract_text_from_pdf(exam_paper.file_path)
            else:
                text_content = self._extract_text_from_image(exam_paper.file_path)
            
            # 使用AI识别题目
            questions_data = self._identify_questions_with_ai(text_content, exam_paper.subject_id)
            
            # 保存题目到数据库
            questions = self._save_questions_to_db(questions_data, exam_paper)
            
            # 更新试卷状态
            exam_paper.parse_status = 'completed'
            exam_paper.question_count = len(questions)
            db.session.commit()
            
            return {
                'success': True,
                'questions_count': len(questions),
                'questions': [q.to_dict() for q in questions]
            }
            
        except Exception as e:
            logger.error(f"解析试卷失败: {str(e)}")
            # 更新试卷状态为失败
            if 'exam_paper' in locals():
                exam_paper.parse_status = 'failed'
                exam_paper.parse_error = str(e)
                db.session.commit()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """从PDF文件提取文本"""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                # 使用get_text()方法提取文本，忽略类型检查器警告
                text += page.get_text()  # type: ignore
            doc.close()
            return text
        except Exception as e:
            logger.error(f"PDF文本提取失败: {str(e)}")
            raise
    
    def _extract_text_from_image(self, file_path: str) -> str:
        """从图片文件提取文本"""
        try:
            image = Image.open(file_path)
            # 使用OCR提取文本
            text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            return text
        except Exception as e:
            logger.error(f"图片文本提取失败: {str(e)}")
            raise
    
    def _identify_questions_with_ai(self, text_content: str, subject_id: str) -> List[Dict[str, Any]]:
        """使用AI识别题目"""
        try:
            # 获取学科相关的知识点
            knowledge_points = KnowledgePoint.query.filter_by(subject_id=subject_id).all()
            knowledge_points_text = "\n".join([f"{kp.id}: {kp.name}" for kp in knowledge_points])
            
            prompt = f"""
你是一个专业的试卷解析AI助手。请分析以下试卷内容，识别出所有题目，并为每个题目关联相关的知识点。

试卷内容：
{text_content}

可用知识点列表：
{knowledge_points_text}

请按照以下JSON格式返回结果：
{{
  "questions": [
    {{
      "content": "题目内容",
      "type": "选择题/填空题/解答题/判断题",
      "options": ["A选项", "B选项", "C选项", "D选项"],  // 仅选择题需要
      "correct_answer": "正确答案",
      "analysis": "题目解析",
      "difficulty": 3,  // 1-5难度等级
      "score": 5,  // 题目分值
      "knowledge_points": ["知识点ID1", "知识点ID2"],  // 关联的知识点ID
      "tags": ["标签1", "标签2"]  // 题目标签
    }}
  ]
}}

注意事项：
1. 仔细识别题目边界，避免将多个题目合并
2. 准确判断题目类型
3. 为选择题提取所有选项
4. 根据题目内容合理关联知识点
5. 设置合适的难度等级和分值
6. 如果无法确定正确答案，可以留空
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "你是一个专业的试卷解析AI助手，擅长识别和分析各种类型的题目。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            
            if not result_text:
                raise ValueError("AI返回的结果为空")
            
            # 尝试解析JSON
            try:
                result = json.loads(result_text)
                return result.get('questions', [])
            except json.JSONDecodeError:
                # 如果直接解析失败，尝试提取JSON部分
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return result.get('questions', [])
                else:
                    raise ValueError("AI返回的结果不是有效的JSON格式")
                    
        except Exception as e:
            logger.error(f"AI题目识别失败: {str(e)}")
            raise
    
    def _save_questions_to_db(self, questions_data: List[Dict[str, Any]], exam_paper: ExamPaper) -> List[Question]:
        """保存题目到数据库"""
        questions = []
        
        for i, q_data in enumerate(questions_data):
            try:
                # 创建题目对象
                question = Question(
                    tenant_id=exam_paper.tenant_id,
                    exam_paper_id=exam_paper.id,
                    subject_id=exam_paper.subject_id,
                    content=q_data.get('content', ''),
                    type=q_data.get('type', '选择题'),
                    options=q_data.get('options', []),
                    correct_answer=q_data.get('correct_answer', ''),
                    analysis=q_data.get('analysis', ''),
                    difficulty=q_data.get('difficulty', 3),
                    score=q_data.get('score', 5),
                    tags=q_data.get('tags', []),
                    order_index=i + 1
                )
                
                db.session.add(question)
                db.session.flush()  # 获取question.id
                
                # 关联知识点
                knowledge_point_ids = q_data.get('knowledge_points', [])
                for kp_id in knowledge_point_ids:
                    kp = KnowledgePoint.query.get(kp_id)
                    if kp:
                        question.knowledge_points.append(kp)
                
                questions.append(question)
                
            except Exception as e:
                logger.error(f"保存题目失败: {str(e)}")
                continue
        
        db.session.commit()
        return questions
    
    def enhance_question_analysis(self, question_id: str) -> Dict[str, Any]:
        """增强题目分析"""
        try:
            question = Question.query.get(question_id)
            if not question:
                raise ValueError(f"题目不存在: {question_id}")
            
            prompt = f"""
请对以下题目进行深度分析：

题目内容：{question.content}
题目类型：{question.type}
当前难度：{question.difficulty}

请提供：
1. 详细的解题思路和步骤
2. 涉及的核心知识点和概念
3. 常见错误和易错点
4. 解题技巧和方法
5. 相关的拓展知识

请以JSON格式返回：
{{
  "detailed_analysis": "详细解析",
  "solution_steps": ["步骤1", "步骤2", "步骤3"],
  "key_concepts": ["概念1", "概念2"],
  "common_mistakes": ["错误1", "错误2"],
  "solving_tips": ["技巧1", "技巧2"],
  "related_knowledge": ["相关知识1", "相关知识2"]
}}
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "你是一个专业的教育分析师，擅长深度分析题目和提供学习指导。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            
            if not result_text:
                raise ValueError("AI返回的结果为空")
                
            result = json.loads(result_text)
            
            # 更新题目的分析信息
            question.detailed_analysis = result.get('detailed_analysis', '')
            question.solution_steps = result.get('solution_steps', [])
            question.key_concepts = result.get('key_concepts', [])
            question.common_mistakes = result.get('common_mistakes', [])
            question.solving_tips = result.get('solving_tips', [])
            question.related_knowledge = result.get('related_knowledge', [])
            
            db.session.commit()
            
            return {
                'success': True,
                'analysis': result
            }
            
        except Exception as e:
            logger.error(f"增强题目分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# AI解析器实例将在需要时创建