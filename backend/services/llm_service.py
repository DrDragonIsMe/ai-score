#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 业务服务 - llm_service.py

Description:
    LLM服务，提供大语言模型调用、内容生成等AI功能。

Author: Chang Xinglong
Date: 2025-08-30
Version: 1.0.0
License: Apache License 2.0
"""


import json
import requests
from typing import Dict, List, Any, Optional
from models.ai_model import AIModelConfig
from utils.logger import get_logger

logger = get_logger(__name__)

class LLMService:
    """
    大语言模型服务类
    """
    
    def __init__(self):
        self.default_model = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """
        确保服务已初始化
        """
        if not self._initialized:
            self._load_default_model()
            self._initialized = True
    
    def _load_default_model(self):
        """
        加载默认模型配置
        """
        try:
            from flask import current_app
            with current_app.app_context():
                self.default_model = AIModelConfig.query.filter_by(
                    is_active=True,
                    is_default=True
                ).first()
                
                if not self.default_model:
                    logger.warning("未找到默认AI模型，创建备用模型")
                    self.default_model = self._create_fallback_model()
                    
        except Exception as e:
            logger.error(f"加载默认模型失败: {str(e)}")
            self.default_model = self._create_fallback_model()
    
    def get_available_models(self) -> List[AIModelConfig]:
        """
        获取所有可用的AI模型
        """
        try:
            from flask import current_app
            with current_app.app_context():
                return AIModelConfig.query.filter_by(is_active=True).all()
        except Exception as e:
            logger.error(f"获取可用模型失败: {str(e)}")
            return []
    
    def get_model_by_id(self, model_id: str) -> Optional[AIModelConfig]:
        """
        根据ID获取AI模型配置
        """
        try:
            from flask import current_app
            with current_app.app_context():
                return AIModelConfig.query.filter_by(id=model_id, is_active=True).first()
        except Exception as e:
            logger.error(f"获取模型配置失败: {str(e)}")
            return None
    
    def refresh_default_model(self):
        """
        刷新默认模型配置
        """
        self._initialized = False
        self._ensure_initialized()
    
    def _create_fallback_model(self):
        """
        创建备用模型配置
        """
        class FallbackModel:
            def __init__(self):
                self.model_name = "gpt-3.5-turbo"
                self.api_key = "fallback-key"
                self.api_url = "https://api.openai.com/v1/chat/completions"
                self.model_type = "openai"
                self.max_tokens = 1000
                self.temperature = 0.7
        
        return FallbackModel()
    
    def generate_text(self, prompt: str, model_name: Optional[str] = None, **kwargs) -> str:
        """
        生成文本
        
        Args:
            prompt: 输入提示
            model_name: 模型名称
            **kwargs: 其他参数
            
        Returns:
            str: 生成的文本
        """
        try:
            # 确保服务已初始化
            self._ensure_initialized()
            
            # 获取模型配置
            model = self._get_model(model_name)
            if not model:
                return "模型配置不可用"
            
            # 构建请求参数
            request_data = {
                "model": model.model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": kwargs.get("temperature", getattr(model, 'temperature', 0.7)),
                "max_tokens": kwargs.get("max_tokens", getattr(model, 'max_tokens', 1000)),
                "top_p": kwargs.get("top_p", getattr(model, 'top_p', 1.0))
            }
            
            # 发送请求
            response = self._make_request(model, request_data)
            
            if response and "choices" in response:
                return response["choices"][0]["message"]["content"]
            
            return "生成失败"
            
        except Exception as e:
            logger.error(f"文本生成失败: {str(e)}")
            return f"生成错误: {str(e)}"
    
    def generate_questions(self, subject: str, difficulty: str, count: int = 5) -> List[Dict]:
        """
        生成题目
        
        Args:
            subject: 学科
            difficulty: 难度
            count: 题目数量
            
        Returns:
            List[Dict]: 题目列表
        """
        prompt = f"""
        请生成{count}道{subject}学科的{difficulty}难度题目。
        
        要求：
        1. 题目类型包括选择题、填空题、解答题
        2. 每道题目包含题干、选项（选择题）、答案、解析
        3. 返回JSON格式
        
        格式示例：
        [
            {
                "type": "choice",
                "question": "题干内容",
                "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
                "answer": "A",
                "explanation": "解析内容"
            }
        ]
        """
        
        try:
            response_text = self.generate_text(prompt)
            
            # 尝试解析JSON
            if response_text.startswith("["):
                questions = json.loads(response_text)
                return questions
            else:
                # 如果不是JSON格式，返回默认题目
                return self._generate_default_questions(subject, difficulty, count)
                
        except Exception as e:
            logger.error(f"题目生成失败: {str(e)}")
            return self._generate_default_questions(subject, difficulty, count)
    
    def generate_explanation(self, question: str, answer: str, student_answer: str) -> str:
        """
        生成解题解析
        
        Args:
            question: 题目
            answer: 正确答案
            student_answer: 学生答案
            
        Returns:
            str: 解析内容
        """
        prompt = f"""
        题目：{question}
        正确答案：{answer}
        学生答案：{student_answer}
        
        请分析学生的答题情况，提供详细的解题思路和错误分析。
        
        要求：
        1. 指出学生答案的对错
        2. 分析错误原因（如果有错误）
        3. 提供正确的解题步骤
        4. 给出学习建议
        """
        
        return self.generate_text(prompt)
    
    def generate_study_plan(self, weak_points: List[str], study_time: int) -> str:
        """
        生成学习计划
        
        Args:
            weak_points: 薄弱知识点
            study_time: 学习时间（分钟）
            
        Returns:
            str: 学习计划
        """
        weak_points_str = "、".join(weak_points)
        
        prompt = f"""
        学生的薄弱知识点：{weak_points_str}
        可用学习时间：{study_time}分钟
        
        请制定一个详细的学习计划，包括：
        1. 学习顺序和时间分配
        2. 每个知识点的学习方法
        3. 练习建议
        4. 复习安排
        """
        
        return self.generate_text(prompt)
    
    def _get_model(self, model_name: Optional[str] = None) -> Any:
        """
        获取模型配置
        
        Args:
            model_name: 模型名称
            
        Returns:
            AIModelConfig: 模型配置
        """
        self._ensure_initialized()
        
        if model_name:
            return AIModelConfig.query.filter_by(
                model_name=model_name,
                is_active=True
            ).first()
        
        return self.default_model
    
    def evaluate_answer(self, question_text: str, correct_answer: str, 
                       student_answer: str, question_type: str) -> Dict[str, Any]:
        """
        评估学生答案
        
        Args:
            question_text: 题目内容
            correct_answer: 正确答案
            student_answer: 学生答案
            question_type: 题目类型
            
        Returns:
            Dict: 评估结果
        """
        try:
            # 简单的评分逻辑，可以后续扩展为AI评分
            if question_type in ['short_answer', 'essay']:
                # 主观题评分
                correct_words = set(correct_answer.lower().split())
                student_words = set(student_answer.lower().split())
                
                if not correct_words:
                    return {'score_percentage': 0.0, 'feedback': '标准答案为空'}
                
                # 计算关键词匹配度
                intersection = correct_words.intersection(student_words)
                similarity = len(intersection) / len(correct_words)
                
                # 根据相似度给分
                if similarity >= 0.8:
                    score_percentage = 1.0
                    feedback = '答案很好，涵盖了主要要点'
                elif similarity >= 0.6:
                    score_percentage = 0.8
                    feedback = '答案较好，但可以更完善'
                elif similarity >= 0.4:
                    score_percentage = 0.6
                    feedback = '答案基本正确，但缺少一些要点'
                elif similarity >= 0.2:
                    score_percentage = 0.3
                    feedback = '答案部分正确，需要补充更多内容'
                else:
                    score_percentage = 0.1
                    feedback = '答案需要重新组织，请参考标准答案'
                
                return {
                    'score_percentage': score_percentage,
                    'feedback': feedback,
                    'similarity': similarity
                }
            else:
                # 客观题直接比较
                is_correct = student_answer.strip().upper() == correct_answer.strip().upper()
                return {
                    'score_percentage': 1.0 if is_correct else 0.0,
                    'feedback': '正确' if is_correct else '错误',
                    'similarity': 1.0 if is_correct else 0.0
                }
                
        except Exception as e:
            logger.error(f"评估答案失败: {str(e)}")
            return {
                'score_percentage': 0.5,
                'feedback': '评分系统暂时不可用，给予中等分数',
                'similarity': 0.5
            }
    
    def _make_request(self, model: AIModelConfig, data: Dict) -> Optional[Dict]:
        """
        发送API请求
        
        Args:
            model: 模型配置
            data: 请求数据
            
        Returns:
            Dict: 响应数据
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {getattr(model, 'api_key', '')}"
            }
            
            # 构建完整的API URL
            base_url = getattr(model, 'api_base_url', '')
            if not base_url:
                base_url = getattr(model, 'api_url', getattr(model, 'api_endpoint', ''))
            
            # 对于Azure OpenAI，需要添加特定的路径和参数
            if 'azure.com' in base_url:
                api_url = f"{base_url}/openai/deployments/{model.model_id}/chat/completions?api-version=2024-02-15-preview"
                headers["api-key"] = model.api_key
                del headers["Authorization"]  # Azure使用api-key而不是Authorization
            else:
                api_url = base_url if base_url.endswith('/chat/completions') else f"{base_url}/chat/completions"
            
            response = requests.post(
                api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API请求失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"API请求异常: {str(e)}")
            return None
    
    def _generate_default_questions(self, subject: str, difficulty: str, count: int) -> List[Dict]:
        """
        生成默认题目（当AI生成失败时使用）
        
        Args:
            subject: 学科
            difficulty: 难度
            count: 题目数量
            
        Returns:
            List[Dict]: 默认题目列表
        """
        questions = []
        
        for i in range(count):
            question = {
                "type": "choice",
                "question": f"{subject}示例题目{i+1}（{difficulty}难度）",
                "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
                "answer": "A",
                "explanation": "这是一道示例题目的解析"
            }
            questions.append(question)
        
        return questions

# 创建全局实例
llm_service = LLMService()