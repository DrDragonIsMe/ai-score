#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 业务服务 - content_generation_service.py

Description:
    内容生成服务，提供AI驱动的教学内容生成。

Author: Chang Xinglong
Date: 2025-08-30
Version: 1.0.0
License: Apache License 2.0
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from models.knowledge import KnowledgePoint, Subject
from models.question import Question, QuestionType
from models.user import User
from models.diagnosis import LearningProfile
from services.llm_service import LLMService
from utils.logger import get_logger
import json
import re

logger = get_logger(__name__)

class ContentGenerationService:
    """
    AI内容生成服务
    基于知识点和学习画像生成个性化学习内容
    """
    
    @staticmethod
    def generate_learning_content(knowledge_point_id: str, 
                                user_id: str = None,
                                content_type: str = 'explanation',
                                difficulty_level: float = None,
                                learning_style: str = None) -> Dict[str, Any]:
        """
        生成学习内容
        
        Args:
            knowledge_point_id: 知识点ID
            user_id: 用户ID（可选，用于个性化）
            content_type: 内容类型（explanation, example, summary, etc.）
            difficulty_level: 难度级别
            learning_style: 学习风格
            
        Returns:
            生成的学习内容
        """
        try:
            # 获取知识点信息
            knowledge_point = KnowledgePoint.query.get(knowledge_point_id)
            if not knowledge_point:
                raise ValueError('知识点不存在')
            
            # 获取用户学习画像（如果提供了用户ID）
            learning_profile = None
            if user_id:
                learning_profile = LearningProfile.query.filter_by(
                    user_id=user_id,
                    subject_id=knowledge_point.subject_id
                ).first()
            
            # 确定内容参数
            params = ContentGenerationService._determine_content_params(
                knowledge_point, learning_profile, difficulty_level, learning_style
            )
            
            # 根据内容类型生成内容
            if content_type == 'explanation':
                content = ContentGenerationService._generate_explanation(
                    knowledge_point, params
                )
            elif content_type == 'example':
                content = ContentGenerationService._generate_examples(
                    knowledge_point, params
                )
            elif content_type == 'summary':
                content = ContentGenerationService._generate_summary(
                    knowledge_point, params
                )
            elif content_type == 'analogy':
                content = ContentGenerationService._generate_analogy(
                    knowledge_point, params
                )
            elif content_type == 'step_by_step':
                content = ContentGenerationService._generate_step_by_step(
                    knowledge_point, params
                )
            else:
                raise ValueError(f'不支持的内容类型: {content_type}')
            
            return {
                'knowledge_point_id': knowledge_point_id,
                'content_type': content_type,
                'content': content,
                'difficulty_level': params['difficulty_level'],
                'learning_style': params['learning_style'],
                'generated_at': datetime.utcnow().isoformat(),
                'personalized': user_id is not None
            }
            
        except Exception as e:
            logger.error(f"生成学习内容失败: {e}")
            raise
    
    @staticmethod
    def generate_practice_questions(knowledge_point_id: str,
                                  user_id: str = None,
                                  question_count: int = 5,
                                  difficulty_range: tuple = None,
                                  question_types: List[str] = None) -> List[Dict[str, Any]]:
        """
        生成练习题
        
        Args:
            knowledge_point_id: 知识点ID
            user_id: 用户ID（可选）
            question_count: 题目数量
            difficulty_range: 难度范围 (min, max)
            question_types: 题目类型列表
            
        Returns:
            生成的练习题列表
        """
        try:
            # 获取知识点信息
            knowledge_point = KnowledgePoint.query.get(knowledge_point_id)
            if not knowledge_point:
                raise ValueError('知识点不存在')
            
            # 获取用户学习画像
            learning_profile = None
            if user_id:
                learning_profile = LearningProfile.query.filter_by(
                    user_id=user_id,
                    subject_id=knowledge_point.subject_id
                ).first()
            
            # 确定题目参数
            params = ContentGenerationService._determine_question_params(
                knowledge_point, learning_profile, difficulty_range, question_types
            )
            
            questions = []
            
            # 生成不同类型的题目
            for i in range(question_count):
                question_type = params['question_types'][i % len(params['question_types'])]
                difficulty = ContentGenerationService._calculate_question_difficulty(
                    i, question_count, params['difficulty_range']
                )
                
                question = ContentGenerationService._generate_single_question(
                    knowledge_point, question_type, difficulty, params
                )
                
                if question:
                    questions.append({
                        'knowledge_point_id': knowledge_point_id,
                        'question_type': question_type,
                        'difficulty': difficulty,
                        'question': question,
                        'generated_at': datetime.utcnow().isoformat()
                    })
            
            return questions
            
        except Exception as e:
            logger.error(f"生成练习题失败: {e}")
            raise
    
    @staticmethod
    def generate_personalized_explanation(question_id: str, 
                                        user_answer: str,
                                        correct_answer: str,
                                        user_id: str = None) -> Dict[str, Any]:
        """
        生成个性化解释
        
        Args:
            question_id: 题目ID
            user_answer: 用户答案
            correct_answer: 正确答案
            user_id: 用户ID
            
        Returns:
            个性化解释
        """
        try:
            # 获取题目信息
            question = Question.query.get(question_id)
            if not question:
                raise ValueError('题目不存在')
            
            # 获取知识点信息
            knowledge_point = KnowledgePoint.query.get(question.knowledge_point_id)
            
            # 获取用户学习画像
            learning_profile = None
            if user_id:
                learning_profile = LearningProfile.query.filter_by(
                    user_id=user_id,
                    subject_id=knowledge_point.subject_id if knowledge_point else None
                ).first()
            
            # 分析答题情况
            is_correct = ContentGenerationService._compare_answers(
                user_answer, correct_answer, question.question_type
            )
            
            # 生成解释
            if is_correct:
                explanation = ContentGenerationService._generate_correct_explanation(
                    question, knowledge_point, learning_profile
                )
            else:
                explanation = ContentGenerationService._generate_incorrect_explanation(
                    question, user_answer, correct_answer, knowledge_point, learning_profile
                )
            
            return {
                'question_id': question_id,
                'is_correct': is_correct,
                'explanation': explanation,
                'learning_tips': ContentGenerationService._generate_learning_tips(
                    question, knowledge_point, is_correct, learning_profile
                ),
                'related_concepts': ContentGenerationService._get_related_concepts(
                    knowledge_point
                ),
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"生成个性化解释失败: {e}")
            raise
    
    @staticmethod
    def _determine_content_params(knowledge_point: KnowledgePoint,
                                learning_profile: LearningProfile = None,
                                difficulty_level: float = None,
                                learning_style: str = None) -> Dict[str, Any]:
        """
        确定内容生成参数
        
        Args:
            knowledge_point: 知识点
            learning_profile: 学习画像
            difficulty_level: 指定难度级别
            learning_style: 指定学习风格
            
        Returns:
            内容参数
        """
        params = {
            'difficulty_level': difficulty_level or knowledge_point.difficulty_level,
            'learning_style': learning_style or 'balanced',
            'language_level': 'standard',
            'include_examples': True,
            'include_analogies': False
        }
        
        # 基于学习画像调整参数
        if learning_profile and learning_profile.learning_preferences:
            preferences = learning_profile.learning_preferences
            
            # 学习风格
            if not learning_style:
                params['learning_style'] = preferences.get('learning_style', 'balanced')
            
            # 难度偏好
            if not difficulty_level:
                difficulty_pref = preferences.get('difficulty_preference', 'medium')
                if difficulty_pref == 'easy':
                    params['difficulty_level'] = max(1, params['difficulty_level'] - 0.5)
                elif difficulty_pref == 'hard':
                    params['difficulty_level'] = min(5, params['difficulty_level'] + 0.5)
            
            # 语言水平
            if preferences.get('language_level'):
                params['language_level'] = preferences['language_level']
            
            # 内容偏好
            if preferences.get('prefer_analogies'):
                params['include_analogies'] = True
        
        return params
    
    @staticmethod
    def _generate_explanation(knowledge_point: KnowledgePoint, 
                            params: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成概念解释
        
        Args:
            knowledge_point: 知识点
            params: 生成参数
            
        Returns:
            概念解释内容
        """
        try:
            # 构建提示词
            prompt = f"""
            请为以下知识点生成详细的概念解释：
            
            知识点：{knowledge_point.name}
            学科：{knowledge_point.subject.name if knowledge_point.subject else '未知'}
            难度级别：{params['difficulty_level']}
            学习风格：{params['learning_style']}
            
            要求：
            1. 解释要清晰易懂，适合难度级别{params['difficulty_level']}
            2. 根据学习风格'{params['learning_style']}'调整表达方式
            3. 包含核心概念、重要特征和应用场景
            4. 语言要{params['language_level']}
            {'5. 适当使用类比和比喻' if params['include_analogies'] else ''}
            {'6. 包含具体例子' if params['include_examples'] else ''}
            
            请按以下格式输出：
            ## 核心概念
            [概念的核心定义]
            
            ## 重要特征
            [列出2-3个重要特征]
            
            ## 应用场景
            [说明在什么情况下使用]
            
            {'## 类比理解\n[用生活中的例子类比]\n' if params['include_analogies'] else ''}
            {'## 具体例子\n[提供1-2个具体例子]\n' if params['include_examples'] else ''}
            """
            
            # 调用LLM生成内容
            response = LLMService.generate_content(
                prompt=prompt,
                max_tokens=800,
                temperature=0.7
            )
            
            if response and response.get('content'):
                content = response['content']
                
                # 解析结构化内容
                parsed_content = ContentGenerationService._parse_structured_content(content)
                
                return {
                    'type': 'explanation',
                    'raw_content': content,
                    'structured_content': parsed_content,
                    'word_count': len(content.split()),
                    'estimated_reading_time': len(content.split()) // 200 + 1  # 分钟
                }
            
        except Exception as e:
            logger.error(f"生成概念解释失败: {e}")
        
        # 返回默认内容
        return {
            'type': 'explanation',
            'raw_content': f'{knowledge_point.name}是一个重要的概念，需要深入理解其核心要点。',
            'structured_content': {
                '核心概念': f'{knowledge_point.name}的基本定义和含义',
                '重要特征': ['特征1', '特征2'],
                '应用场景': '相关的应用场景'
            },
            'word_count': 20,
            'estimated_reading_time': 1
        }
    
    @staticmethod
    def _generate_examples(knowledge_point: KnowledgePoint, 
                         params: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成例子
        
        Args:
            knowledge_point: 知识点
            params: 生成参数
            
        Returns:
            例子内容
        """
        try:
            prompt = f"""
            请为知识点"{knowledge_point.name}"生成3-5个具体例子。
            
            要求：
            1. 例子要贴近生活，容易理解
            2. 难度适合级别{params['difficulty_level']}
            3. 每个例子都要有简短的解释说明
            4. 例子之间要有一定的层次性
            
            请按以下格式输出：
            例子1：[例子描述]
            解释：[为什么这是一个好例子]
            
            例子2：[例子描述]
            解释：[为什么这是一个好例子]
            
            ...
            """
            
            response = LLMService.generate_content(
                prompt=prompt,
                max_tokens=600,
                temperature=0.8
            )
            
            if response and response.get('content'):
                content = response['content']
                examples = ContentGenerationService._parse_examples(content)
                
                return {
                    'type': 'examples',
                    'examples': examples,
                    'count': len(examples)
                }
            
        except Exception as e:
            logger.error(f"生成例子失败: {e}")
        
        return {
            'type': 'examples',
            'examples': [{
                'description': f'{knowledge_point.name}的基本例子',
                'explanation': '这是一个基础的应用示例'
            }],
            'count': 1
        }
    
    @staticmethod
    def _generate_summary(knowledge_point: KnowledgePoint, 
                        params: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成总结
        
        Args:
            knowledge_point: 知识点
            params: 生成参数
            
        Returns:
            总结内容
        """
        try:
            prompt = f"""
            请为知识点"{knowledge_point.name}"生成一个简洁的总结。
            
            要求：
            1. 总结要包含最核心的要点
            2. 语言要简洁明了
            3. 适合作为复习材料
            4. 控制在100-200字以内
            
            请按以下格式输出：
            ## 核心要点
            - 要点1
            - 要点2
            - 要点3
            
            ## 记忆口诀
            [如果适用，提供记忆口诀]
            
            ## 注意事项
            [需要特别注意的地方]
            """
            
            response = LLMService.generate_content(
                prompt=prompt,
                max_tokens=400,
                temperature=0.6
            )
            
            if response and response.get('content'):
                content = response['content']
                
                return {
                    'type': 'summary',
                    'content': content,
                    'word_count': len(content.split())
                }
            
        except Exception as e:
            logger.error(f"生成总结失败: {e}")
        
        return {
            'type': 'summary',
            'content': f'{knowledge_point.name}的核心要点总结',
            'word_count': 10
        }
    
    @staticmethod
    def _generate_analogy(knowledge_point: KnowledgePoint, 
                        params: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成类比
        
        Args:
            knowledge_point: 知识点
            params: 生成参数
            
        Returns:
            类比内容
        """
        try:
            prompt = f"""
            请为知识点"{knowledge_point.name}"创造一个生动的类比。
            
            要求：
            1. 类比要贴近日常生活
            2. 能够帮助理解抽象概念
            3. 类比要准确，不能误导
            4. 语言要生动有趣
            
            请按以下格式输出：
            ## 类比对象
            [选择的类比对象]
            
            ## 相似之处
            [详细说明相似的地方]
            
            ## 类比解释
            [用类比来解释原概念]
            
            ## 注意限制
            [类比的局限性]
            """
            
            response = LLMService.generate_content(
                prompt=prompt,
                max_tokens=500,
                temperature=0.8
            )
            
            if response and response.get('content'):
                content = response['content']
                
                return {
                    'type': 'analogy',
                    'content': content
                }
            
        except Exception as e:
            logger.error(f"生成类比失败: {e}")
        
        return {
            'type': 'analogy',
            'content': f'可以把{knowledge_point.name}想象成日常生活中的相似概念'
        }
    
    @staticmethod
    def _generate_step_by_step(knowledge_point: KnowledgePoint, 
                             params: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成步骤式教学
        
        Args:
            knowledge_point: 知识点
            params: 生成参数
            
        Returns:
            步骤式内容
        """
        try:
            prompt = f"""
            请为知识点"{knowledge_point.name}"设计一个步骤式的学习过程。
            
            要求：
            1. 将学习过程分解为清晰的步骤
            2. 每个步骤都要有具体的学习目标
            3. 步骤之间要有逻辑关系
            4. 适合自学使用
            
            请按以下格式输出：
            ## 学习目标
            [整体学习目标]
            
            ## 学习步骤
            ### 步骤1：[步骤名称]
            目标：[这一步要达到什么目标]
            内容：[具体学习内容]
            检验：[如何检验是否掌握]
            
            ### 步骤2：[步骤名称]
            目标：[这一步要达到什么目标]
            内容：[具体学习内容]
            检验：[如何检验是否掌握]
            
            ...
            
            ## 总结检验
            [整体掌握情况的检验方法]
            """
            
            response = LLMService.generate_content(
                prompt=prompt,
                max_tokens=700,
                temperature=0.7
            )
            
            if response and response.get('content'):
                content = response['content']
                steps = ContentGenerationService._parse_steps(content)
                
                return {
                    'type': 'step_by_step',
                    'content': content,
                    'steps': steps,
                    'step_count': len(steps)
                }
            
        except Exception as e:
            logger.error(f"生成步骤式教学失败: {e}")
        
        return {
            'type': 'step_by_step',
            'content': f'{knowledge_point.name}的分步学习指南',
            'steps': [{
                'name': '基础理解',
                'goal': '理解基本概念',
                'content': '学习基础知识',
                'verification': '能够解释基本概念'
            }],
            'step_count': 1
        }
    
    @staticmethod
    def _determine_question_params(knowledge_point: KnowledgePoint,
                                 learning_profile: LearningProfile = None,
                                 difficulty_range: tuple = None,
                                 question_types: List[str] = None) -> Dict[str, Any]:
        """
        确定题目生成参数
        
        Args:
            knowledge_point: 知识点
            learning_profile: 学习画像
            difficulty_range: 难度范围
            question_types: 题目类型
            
        Returns:
            题目参数
        """
        # 默认参数
        params = {
            'difficulty_range': difficulty_range or (knowledge_point.difficulty_level - 0.5, 
                                                    knowledge_point.difficulty_level + 0.5),
            'question_types': question_types or ['single_choice', 'multiple_choice', 'true_false', 'fill_blank'],
            'include_explanation': True,
            'language_level': 'standard'
        }
        
        # 基于学习画像调整
        if learning_profile and learning_profile.learning_preferences:
            preferences = learning_profile.learning_preferences
            
            # 题型偏好
            if preferences.get('preferred_question_types'):
                params['question_types'] = preferences['preferred_question_types']
            
            # 难度偏好
            if preferences.get('difficulty_preference') and not difficulty_range:
                base_difficulty = knowledge_point.difficulty_level
                if preferences['difficulty_preference'] == 'easy':
                    params['difficulty_range'] = (base_difficulty - 1, base_difficulty)
                elif preferences['difficulty_preference'] == 'hard':
                    params['difficulty_range'] = (base_difficulty, base_difficulty + 1)
        
        # 确保难度范围合理
        min_diff, max_diff = params['difficulty_range']
        params['difficulty_range'] = (max(1, min_diff), min(5, max_diff))
        
        return params
    
    @staticmethod
    def _calculate_question_difficulty(question_index: int, 
                                     total_questions: int,
                                     difficulty_range: tuple) -> float:
        """
        计算题目难度
        
        Args:
            question_index: 题目索引
            total_questions: 总题目数
            difficulty_range: 难度范围
            
        Returns:
            题目难度
        """
        min_diff, max_diff = difficulty_range
        
        if total_questions == 1:
            return (min_diff + max_diff) / 2
        
        # 线性分布
        progress = question_index / (total_questions - 1)
        difficulty = min_diff + progress * (max_diff - min_diff)
        
        return round(difficulty, 1)
    
    @staticmethod
    def _generate_single_question(knowledge_point: KnowledgePoint,
                                question_type: str,
                                difficulty: float,
                                params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        生成单个题目
        
        Args:
            knowledge_point: 知识点
            question_type: 题目类型
            difficulty: 难度
            params: 生成参数
            
        Returns:
            生成的题目
        """
        try:
            # 根据题目类型构建不同的提示词
            if question_type == 'single_choice':
                prompt = ContentGenerationService._build_single_choice_prompt(
                    knowledge_point, difficulty
                )
            elif question_type == 'multiple_choice':
                prompt = ContentGenerationService._build_multiple_choice_prompt(
                    knowledge_point, difficulty
                )
            elif question_type == 'true_false':
                prompt = ContentGenerationService._build_true_false_prompt(
                    knowledge_point, difficulty
                )
            elif question_type == 'fill_blank':
                prompt = ContentGenerationService._build_fill_blank_prompt(
                    knowledge_point, difficulty
                )
            else:
                return None
            
            # 调用LLM生成题目
            response = LLMService.generate_content(
                prompt=prompt,
                max_tokens=500,
                temperature=0.8
            )
            
            if response and response.get('content'):
                content = response['content']
                
                # 解析题目内容
                parsed_question = ContentGenerationService._parse_question_content(
                    content, question_type
                )
                
                if parsed_question:
                    return {
                        'question_text': parsed_question['question'],
                        'options': parsed_question.get('options', []),
                        'correct_answer': parsed_question['answer'],
                        'explanation': parsed_question.get('explanation', ''),
                        'difficulty': difficulty,
                        'question_type': question_type
                    }
            
        except Exception as e:
            logger.error(f"生成单个题目失败: {e}")
        
        return None
    
    @staticmethod
    def _build_single_choice_prompt(knowledge_point: KnowledgePoint, 
                                  difficulty: float) -> str:
        """
        构建单选题提示词
        
        Args:
            knowledge_point: 知识点
            difficulty: 难度
            
        Returns:
            提示词
        """
        return f"""
        请为知识点"{knowledge_point.name}"生成一道单选题。
        
        要求：
        1. 难度级别：{difficulty}
        2. 题目要准确测试对该知识点的理解
        3. 提供4个选项（A、B、C、D）
        4. 只有一个正确答案
        5. 错误选项要有一定的迷惑性
        6. 提供详细的解释
        
        请按以下格式输出：
        题目：[题目内容]
        
        A. [选项A]
        B. [选项B]
        C. [选项C]
        D. [选项D]
        
        正确答案：[A/B/C/D]
        
        解释：[为什么这个答案是正确的，其他选项为什么错误]
        """
    
    @staticmethod
    def _build_multiple_choice_prompt(knowledge_point: KnowledgePoint, 
                                    difficulty: float) -> str:
        """
        构建多选题提示词
        
        Args:
            knowledge_point: 知识点
            difficulty: 难度
            
        Returns:
            提示词
        """
        return f"""
        请为知识点"{knowledge_point.name}"生成一道多选题。
        
        要求：
        1. 难度级别：{difficulty}
        2. 提供4-5个选项
        3. 有2-3个正确答案
        4. 错误选项要有迷惑性
        5. 提供详细解释
        
        请按以下格式输出：
        题目：[题目内容]
        
        A. [选项A]
        B. [选项B]
        C. [选项C]
        D. [选项D]
        E. [选项E]（如果有）
        
        正确答案：[如：A,C,D]
        
        解释：[解释每个选项的正确性]
        """
    
    @staticmethod
    def _build_true_false_prompt(knowledge_point: KnowledgePoint, 
                               difficulty: float) -> str:
        """
        构建判断题提示词
        
        Args:
            knowledge_point: 知识点
            difficulty: 难度
            
        Returns:
            提示词
        """
        return f"""
        请为知识点"{knowledge_point.name}"生成一道判断题。
        
        要求：
        1. 难度级别：{difficulty}
        2. 陈述要明确，不能模糊
        3. 要么明确正确，要么明确错误
        4. 提供详细解释
        
        请按以下格式输出：
        题目：[陈述内容]
        
        正确答案：[正确/错误]
        
        解释：[详细解释为什么正确或错误]
        """
    
    @staticmethod
    def _build_fill_blank_prompt(knowledge_point: KnowledgePoint, 
                               difficulty: float) -> str:
        """
        构建填空题提示词
        
        Args:
            knowledge_point: 知识点
            difficulty: 难度
            
        Returns:
            提示词
        """
        return f"""
        请为知识点"{knowledge_point.name}"生成一道填空题。
        
        要求：
        1. 难度级别：{difficulty}
        2. 空格处应该是关键概念或重要信息
        3. 可以有1-3个空格
        4. 答案要明确唯一
        5. 提供详细解释
        
        请按以下格式输出：
        题目：[题目内容，用______表示空格]
        
        正确答案：[答案1, 答案2, ...]（按空格顺序）
        
        解释：[解释答案和相关知识点]
        """
    
    @staticmethod
    def _parse_question_content(content: str, question_type: str) -> Optional[Dict[str, Any]]:
        """
        解析题目内容
        
        Args:
            content: LLM生成的内容
            question_type: 题目类型
            
        Returns:
            解析后的题目数据
        """
        try:
            lines = content.strip().split('\n')
            result = {}
            
            # 查找题目
            question_line = None
            for line in lines:
                if line.startswith('题目：'):
                    question_line = line[3:].strip()
                    break
            
            if not question_line:
                return None
            
            result['question'] = question_line
            
            if question_type in ['single_choice', 'multiple_choice']:
                # 解析选择题选项
                options = []
                for line in lines:
                    line = line.strip()
                    if re.match(r'^[A-E]\. ', line):
                        options.append(line[3:].strip())
                
                result['options'] = options
            
            # 查找答案
            for line in lines:
                if line.startswith('正确答案：'):
                    answer = line[5:].strip()
                    result['answer'] = answer
                    break
            
            # 查找解释
            for line in lines:
                if line.startswith('解释：'):
                    explanation = line[3:].strip()
                    result['explanation'] = explanation
                    break
            
            return result if 'answer' in result else None
            
        except Exception as e:
            logger.error(f"解析题目内容失败: {e}")
            return None
    
    @staticmethod
    def _parse_structured_content(content: str) -> Dict[str, str]:
        """
        解析结构化内容
        
        Args:
            content: 原始内容
            
        Returns:
            结构化的内容字典
        """
        structured = {}
        current_section = None
        current_content = []
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            
            # 检查是否是新的章节
            if line.startswith('## '):
                # 保存前一个章节
                if current_section and current_content:
                    structured[current_section] = '\n'.join(current_content).strip()
                
                # 开始新章节
                current_section = line[3:].strip()
                current_content = []
            elif current_section and line:
                current_content.append(line)
        
        # 保存最后一个章节
        if current_section and current_content:
            structured[current_section] = '\n'.join(current_content).strip()
        
        return structured
    
    @staticmethod
    def _parse_examples(content: str) -> List[Dict[str, str]]:
        """
        解析例子内容
        
        Args:
            content: 原始内容
            
        Returns:
            例子列表
        """
        examples = []
        lines = content.split('\n')
        
        current_example = None
        current_explanation = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('例子'):
                # 保存前一个例子
                if current_example:
                    examples.append({
                        'description': current_example,
                        'explanation': current_explanation or ''
                    })
                
                # 开始新例子
                current_example = line.split('：', 1)[1] if '：' in line else line
                current_explanation = None
            
            elif line.startswith('解释：'):
                current_explanation = line[3:].strip()
        
        # 保存最后一个例子
        if current_example:
            examples.append({
                'description': current_example,
                'explanation': current_explanation or ''
            })
        
        return examples
    
    @staticmethod
    def _parse_steps(content: str) -> List[Dict[str, str]]:
        """
        解析步骤内容
        
        Args:
            content: 原始内容
            
        Returns:
            步骤列表
        """
        steps = []
        lines = content.split('\n')
        
        current_step = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('### 步骤'):
                if current_step:
                    steps.append(current_step)
                
                step_name = line.split('：', 1)[1] if '：' in line else line[3:].strip()
                current_step = {'name': step_name, 'goal': '', 'content': '', 'verification': ''}
            
            elif current_step:
                if line.startswith('目标：'):
                    current_step['goal'] = line[3:].strip()
                elif line.startswith('内容：'):
                    current_step['content'] = line[3:].strip()
                elif line.startswith('检验：'):
                    current_step['verification'] = line[3:].strip()
        
        if current_step:
            steps.append(current_step)
        
        return steps
    
    @staticmethod
    def _compare_answers(user_answer: str, correct_answer: str, 
                       question_type: str) -> bool:
        """
        比较答案是否正确
        
        Args:
            user_answer: 用户答案
            correct_answer: 正确答案
            question_type: 题目类型
            
        Returns:
            是否正确
        """
        user_answer = user_answer.strip().upper()
        correct_answer = correct_answer.strip().upper()
        
        if question_type == 'multiple_choice':
            # 多选题需要处理逗号分隔的答案
            user_set = set(user_answer.replace(' ', '').split(','))
            correct_set = set(correct_answer.replace(' ', '').split(','))
            return user_set == correct_set
        
        return user_answer == correct_answer
    
    @staticmethod
    def _generate_correct_explanation(question: Question,
                                    knowledge_point: KnowledgePoint = None,
                                    learning_profile: LearningProfile = None) -> str:
        """
        生成答对时的解释
        
        Args:
            question: 题目
            knowledge_point: 知识点
            learning_profile: 学习画像
            
        Returns:
            解释内容
        """
        try:
            prompt = f"""
            学生答对了以下题目，请生成鼓励性的解释：
            
            题目：{question.question_text}
            正确答案：{question.correct_answer}
            
            要求：
            1. 首先肯定学生的正确答案
            2. 简要解释为什么这个答案是正确的
            3. 可以拓展相关知识点
            4. 语言要鼓励和积极
            5. 控制在100字以内
            """
            
            response = LLMService.generate_content(
                prompt=prompt,
                max_tokens=200,
                temperature=0.7
            )
            
            if response and response.get('content'):
                return response['content'].strip()
            
        except Exception as e:
            logger.error(f"生成正确解释失败: {e}")
        
        return "回答正确！你很好地掌握了这个知识点。"
    
    @staticmethod
    def _generate_incorrect_explanation(question: Question,
                                      user_answer: str,
                                      correct_answer: str,
                                      knowledge_point: KnowledgePoint = None,
                                      learning_profile: LearningProfile = None) -> str:
        """
        生成答错时的解释
        
        Args:
            question: 题目
            user_answer: 用户答案
            correct_answer: 正确答案
            knowledge_point: 知识点
            learning_profile: 学习画像
            
        Returns:
            解释内容
        """
        try:
            prompt = f"""
            学生答错了以下题目，请生成有帮助的解释：
            
            题目：{question.question_text}
            学生答案：{user_answer}
            正确答案：{correct_answer}
            
            要求：
            1. 不要批评学生，要鼓励
            2. 解释为什么正确答案是对的
            3. 分析学生答案可能的错误原因
            4. 提供记忆或理解的技巧
            5. 语言要温和有帮助
            6. 控制在150字以内
            """
            
            response = LLMService.generate_content(
                prompt=prompt,
                max_tokens=300,
                temperature=0.7
            )
            
            if response and response.get('content'):
                return response['content'].strip()
            
        except Exception as e:
            logger.error(f"生成错误解释失败: {e}")
        
        return f"正确答案是{correct_answer}。让我们一起分析一下这道题的解题思路。"
    
    @staticmethod
    def _generate_learning_tips(question: Question,
                              knowledge_point: KnowledgePoint = None,
                              is_correct: bool = True,
                              learning_profile: LearningProfile = None) -> List[str]:
        """
        生成学习提示
        
        Args:
            question: 题目
            knowledge_point: 知识点
            is_correct: 是否答对
            learning_profile: 学习画像
            
        Returns:
            学习提示列表
        """
        tips = []
        
        if is_correct:
            tips.extend([
                "继续保持这种学习状态",
                "可以尝试更有挑战性的题目",
                "复习相关知识点以巩固理解"
            ])
        else:
            tips.extend([
                "重新阅读相关概念和定义",
                "多做类似的练习题",
                "寻找知识点之间的联系",
                "不要气馁，错误是学习的一部分"
            ])
        
        # 基于学习画像个性化提示
        if learning_profile and learning_profile.learning_preferences:
            preferences = learning_profile.learning_preferences
            learning_style = preferences.get('learning_style', '')
            
            if learning_style == 'visual':
                tips.append("尝试画图或制作思维导图来理解概念")
            elif learning_style == 'hands_on':
                tips.append("通过实际操作和实验来加深理解")
            elif learning_style == 'auditory':
                tips.append("可以大声朗读或听相关的音频材料")
        
        return tips[:4]  # 最多4个提示
    
    @staticmethod
    def _get_related_concepts(knowledge_point: KnowledgePoint = None) -> List[str]:
        """
        获取相关概念
        
        Args:
            knowledge_point: 知识点
            
        Returns:
            相关概念列表
        """
        if not knowledge_point:
            return []
        
        related_concepts = []
        
        # 获取前置知识点
        if knowledge_point.prerequisites:
            for prereq_id in knowledge_point.prerequisites:
                prereq_kp = KnowledgePoint.query.get(prereq_id)
                if prereq_kp:
                    related_concepts.append(prereq_kp.name)
        
        # 获取同级知识点（简化实现）
        same_level_kps = KnowledgePoint.query.filter_by(
            subject_id=knowledge_point.subject_id,
            level=knowledge_point.level
        ).limit(3).all()
        
        for kp in same_level_kps:
            if kp.id != knowledge_point.id:
                related_concepts.append(kp.name)
        
        return related_concepts[:5]  # 最多5个相关概念