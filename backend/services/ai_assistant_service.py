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
from services.llm_service import llm_service
from services.diagnosis_service import DiagnosisService
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
                "知识点推荐"
            ]
        }
    
    def chat_with_user(self, user_id: str, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        与用户进行智能对话
        
        Args:
            user_id: 用户ID
            message: 用户消息
            context: 对话上下文
        
        Returns:
            AI助理回复
        """
        try:
            # 获取用户信息和学习情况
            user_profile = self._get_user_learning_profile(user_id)
            
            # 构建对话提示词
            system_prompt = self._build_chat_prompt(user_profile, context)
            
            # 调用大模型生成回复
            full_prompt = f"{system_prompt}\n\n用户: {message}\n\n高小分:"
            
            response = llm_service.generate_text(
                prompt=full_prompt,
                max_tokens=500,
                temperature=0.7
            )
            
            return {
                "success": True,
                "response": response,
                "assistant_name": self.assistant_name,
                "timestamp": datetime.now().isoformat(),
                "suggestions": self._generate_contextual_suggestions(user_id, message)
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
        从图片中识别试题
        
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
            
            if not extracted_text.strip():
                return {
                    "success": False,
                    "message": "未能识别到文字内容，请确保图片清晰且包含文字。"
                }
            
            # 使用AI分析识别的文本，提取题目信息
            question_analysis = self._analyze_extracted_text(extracted_text, user_id)
            
            return {
                "success": True,
                "extracted_text": extracted_text,
                "question_analysis": question_analysis,
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
    
    def _build_chat_prompt(self, user_profile: Dict, context: Optional[Dict] = None) -> str:
        """
        构建对话提示词
        """
        base_prompt = f"""
你是{self.assistant_name}，一个友善、耐心、专业的AI学习助手。你的任务是帮助学生提高学习效果。

用户信息：
- 用户名：{user_profile.get('username', '同学')}
- 年级：{user_profile.get('grade_level', '未知')}
- 擅长科目：{', '.join(user_profile.get('strong_subjects', []))}
- 薄弱环节：{', '.join(user_profile.get('weak_areas', []))}

对话风格：
- 使用友善、鼓励性的语言
- 根据用户的学习情况提供针对性建议
- 适当使用表情符号增加亲和力
- 保持专业性，提供准确的学习指导
"""
        
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
    
    def _build_question_analysis_prompt(self, question: str, user_answer: Optional[str], 
                                      user_profile: Dict) -> str:
        """
        构建题目分析提示词
        """
        prompt = f"""
作为专业的学习助手{self.assistant_name}，请分析以下题目：

题目：
{question}
"""
        
        if user_answer:
            prompt += f"\n\n学生答案：\n{user_answer}"
        
        prompt += f"""

用户学习情况：
- 擅长领域：{', '.join(user_profile.get('strong_subjects', []))}
- 薄弱环节：{', '.join(user_profile.get('weak_areas', []))}

请提供：
1. 题目解析和标准答案
2. 解题思路和方法
3. 相关知识点
4. 常见错误分析
5. 针对该用户的个性化建议

请用友善、鼓励的语调回答。
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

# 创建全局实例
ai_assistant_service = AIAssistantService()