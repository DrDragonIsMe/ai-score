# -*- coding: utf-8 -*-
"""
大语言模型服务
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
        self._load_default_model()
    
    def _load_default_model(self):
        """
        加载默认模型配置
        """
        try:
            self.default_model = AIModelConfig.query.filter_by(
                is_active=True,
                is_default=True
            ).first()
            
            if not self.default_model:
                # 如果没有默认模型，使用第一个可用模型
                self.default_model = AIModelConfig.query.filter_by(
                    is_active=True
                ).first()
                
        except Exception as e:
            logger.error(f"加载默认模型失败: {str(e)}")
    
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
                "temperature": kwargs.get("temperature", model.temperature),
                "max_tokens": kwargs.get("max_tokens", model.max_tokens),
                "top_p": kwargs.get("top_p", model.top_p)
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
    
    def _get_model(self, model_name: Optional[str] = None) -> Optional[AIModelConfig]:
        """
        获取模型配置
        
        Args:
            model_name: 模型名称
            
        Returns:
            AIModelConfig: 模型配置
        """
        if model_name:
            return AIModelConfig.query.filter_by(
                model_name=model_name,
                is_active=True
            ).first()
        
        return self.default_model
    
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
                "Authorization": f"Bearer {model.api_key}"
            }
            
            response = requests.post(
                model.api_endpoint,
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