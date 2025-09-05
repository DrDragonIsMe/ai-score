#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 服务模块 - classification_service.py

Description:
    文档智能分类服务，提供基于规则和AI的文档分类功能。

Author: Chang Xinglong
Date: 2025-08-31
Version: 1.0.0
License: Apache License 2.0
"""

from typing import Dict, List, Optional, Tuple, Any
import json
import re
from datetime import datetime
from sqlalchemy.orm import Session
from models.document import Document, DocumentCategory, DocumentAnalysis
# 移除循环导入，改为延迟导入
from utils.database import db
from utils.logger import get_logger

logger = get_logger(__name__)

class ClassificationService:
    """文档智能分类服务"""
    
    def __init__(self):
        self.ai_assistant_service = None  # 延迟初始化以避免循环导入
        
        # 预定义分类规则
        self.classification_rules = {
            '数学': {
                'keywords': ['数学', '算术', '代数', '几何', '微积分', '统计', '概率', '函数', '方程', '公式'],
                'patterns': [r'\d+[+\-*/]\d+', r'[xy]=', r'∫', r'∑', r'√', r'π']
            },
            '语文': {
                'keywords': ['语文', '文学', '作文', '阅读', '诗歌', '散文', '小说', '古诗', '文言文', '现代文'],
                'patterns': [r'[。，；：！？]', r'第[一二三四五六七八九十]章', r'诗经', r'论语']
            },
            '英语': {
                'keywords': ['英语', '英文', 'English', '语法', '词汇', '阅读理解', '写作', '听力'],
                'patterns': [r'\b[A-Za-z]+\b', r'\bthe\b', r'\band\b', r'\bof\b']
            },
            '物理': {
                'keywords': ['物理', '力学', '电学', '光学', '热学', '原子', '分子', '能量', '速度', '加速度'],
                'patterns': [r'F=ma', r'E=mc²', r'牛顿', r'爱因斯坦']
            },
            '化学': {
                'keywords': ['化学', '元素', '化合物', '反应', '有机', '无机', '分析', '实验', '分子式'],
                'patterns': [r'H₂O', r'CO₂', r'NaCl', r'化学方程式']
            },
            '生物': {
                'keywords': ['生物', '细胞', '遗传', '进化', '生态', '分子生物学', 'DNA', 'RNA', '蛋白质'],
                'patterns': [r'DNA', r'RNA', r'ATP', r'细胞膜']
            },
            '历史': {
                'keywords': ['历史', '朝代', '战争', '文化', '政治', '经济', '社会', '古代', '近代', '现代'],
                'patterns': [r'\d+年', r'朝代', r'皇帝', r'革命']
            },
            '地理': {
                'keywords': ['地理', '地形', '气候', '人口', '城市', '资源', '环境', '地图', '经纬度'],
                'patterns': [r'北纬', r'南纬', r'东经', r'西经', r'°']
            },
            '政治': {
                'keywords': ['政治', '马克思', '哲学', '经济学', '法律', '国际关系', '政府', '制度'],
                'patterns': [r'马克思主义', r'社会主义', r'资本主义']
            }
        }
    
    def classify_document(self, document: Document, content: str) -> Dict[str, Any]:
        """对文档进行智能分类
        
        Args:
            document: 文档对象
            content: 文档内容
            
        Returns:
            Dict: 分类结果
        """
        try:
            # 基于规则的分类
            rule_result = self._classify_by_rules(content)
            
            # 基于AI的分类
            ai_result = self._classify_by_ai(content)
            
            # 综合分类结果
            final_result = self._combine_classification_results(rule_result, ai_result)
            
            # 保存分类结果
            self._save_classification_result(document, final_result)
            
            return final_result
            
        except Exception as e:
            logger.error(f"文档分类失败: {str(e)}")
            return {
                'category': '未分类',
                'confidence': 0.0,
                'method': 'error',
                'error': str(e)
            }
    
    def _classify_by_rules(self, content: str) -> Dict[str, Any]:
        """基于预定义规则进行分类"""
        scores = {}
        
        for category, rules in self.classification_rules.items():
            score = 0
            
            # 关键词匹配
            for keyword in rules['keywords']:
                if keyword in content:
                    score += 1
            
            # 模式匹配
            for pattern in rules['patterns']:
                matches = re.findall(pattern, content, re.IGNORECASE)
                score += len(matches) * 0.5
            
            scores[category] = score
        
        # 找到最高分的分类
        if scores:
            best_category = max(scores.keys(), key=lambda k: scores[k])
            max_score = scores[best_category]
            
            if max_score > 0:
                confidence = min(max_score / 10, 1.0)  # 归一化到0-1
                return {
                    'category': best_category,
                    'confidence': confidence,
                    'method': 'rule_based',
                    'scores': scores
                }
        
        return {
            'category': '未分类',
            'confidence': 0.0,
            'method': 'rule_based',
            'scores': scores
        }
    
    def _classify_by_ai(self, content: str) -> Dict[str, Any]:
        """基于AI进行分类"""
        try:
            # 构建AI分类提示
            prompt = f"""
            请对以下文档内容进行学科分类，从以下类别中选择最合适的一个：
            数学、语文、英语、物理、化学、生物、历史、地理、政治
            
            文档内容：
            {content[:2000]}  # 限制内容长度
            
            请返回JSON格式的结果，包含：
            - category: 分类名称
            - confidence: 置信度(0-1)
            - reason: 分类理由
            """
            
            # 延迟导入AI助手服务以避免循环导入
            if self.ai_assistant_service is None:
                try:
                    from services.ai_assistant_service import AIAssistantService
                    self.ai_assistant_service = AIAssistantService()
                except ImportError:
                    logger.warning("AIAssistantService不可用，跳过AI分类")
                    return {
                        'category': '未分类',
                        'confidence': 0.0,
                        'method': 'ai_based',
                        'error': 'AIAssistantService不可用'
                    }
            
            # 调用AI助手
            response = self.ai_assistant_service.chat_with_user(
                user_id="system",
                message=prompt,
                context={"task": "document_classification"}
            )
            
            if response and 'response' in response:
                response_text = response['response']
                
                # 尝试解析JSON响应
                try:
                    result = json.loads(response_text)
                    result['method'] = 'ai_based'
                    return result
                except json.JSONDecodeError:
                    # 如果不是JSON格式，尝试提取分类信息
                    for category in self.classification_rules.keys():
                        if category in response_text:
                            return {
                                'category': category,
                                'confidence': 0.7,
                                'method': 'ai_based',
                                'reason': '基于AI文本分析'
                            }
            
            return {
                'category': '未分类',
                'confidence': 0.0,
                'method': 'ai_based',
                'error': 'AI分类失败'
            }
            
        except Exception as e:
            logger.error(f"AI分类失败: {str(e)}")
            return {
                'category': '未分类',
                'confidence': 0.0,
                'method': 'ai_based',
                'error': str(e)
            }
    
    def _combine_classification_results(self, rule_result: Dict, ai_result: Dict) -> Dict:
        """综合规则和AI的分类结果"""
        # 如果两种方法得出相同结果，提高置信度
        if rule_result['category'] == ai_result['category'] and rule_result['category'] != '未分类':
            return {
                'category': rule_result['category'],
                'confidence': min((rule_result['confidence'] + ai_result['confidence']) / 2 + 0.2, 1.0),
                'method': 'combined',
                'rule_result': rule_result,
                'ai_result': ai_result
            }
        
        # 选择置信度更高的结果
        if rule_result['confidence'] > ai_result['confidence']:
            return {
                **rule_result,
                'method': 'combined_rule_preferred',
                'ai_result': ai_result
            }
        else:
            return {
                **ai_result,
                'method': 'combined_ai_preferred',
                'rule_result': rule_result
            }
    
    def _save_classification_result(self, document: Document, result: Dict):
        """保存分类结果到数据库"""
        try:
            # 查找或创建分类
            category = DocumentCategory.query.filter_by(
                name=result['category'],
                tenant_id=document.tenant_id
            ).first()
            
            if not category and result['category'] != '未分类':
                category = DocumentCategory(
                    name=result['category'],
                    description=f"自动分类：{result['category']}",
                    tenant_id=document.tenant_id
                )
                db.session.add(category)
                db.session.flush()
            
            # 更新文档分类
            if category:
                document.category_id = category.id
            
            # 保存分析结果
            analysis = DocumentAnalysis(
                document_id=document.id,
                analysis_type='classification',
                result=result,
                confidence_score=result.get('confidence', 0.0)
            )
            
            db.session.add(analysis)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"保存分类结果失败: {str(e)}")
            db.session.rollback()
    
    def batch_classify_documents(self, document_ids: List[str]) -> Dict[str, Any]:
        """批量分类文档"""
        results = []
        
        for doc_id in document_ids:
            try:
                document = Document.query.get(doc_id)
                if not document:
                    continue
                
                # 获取文档内容（这里需要实现获取解析后内容的逻辑）
                content = self._get_document_content(document)
                if content:
                    result = self.classify_document(document, content)
                    results.append({
                        'document_id': doc_id,
                        'result': result
                    })
                    
            except Exception as e:
                logger.error(f"批量分类文档 {doc_id} 失败: {str(e)}")
                results.append({
                    'document_id': doc_id,
                    'error': str(e)
                })
        
        return {
            'total': len(document_ids),
            'processed': len(results),
            'results': results
        }
    
    def _get_document_content(self, document: Document) -> Optional[str]:
        """获取文档内容"""
        try:
            # 从文档页面中获取文本内容
            pages = document.pages.all()
            content_parts = []
            
            for page in pages:
                if page.text_content:
                    content_parts.append(page.text_content)
            
            return '\n'.join(content_parts) if content_parts else None
            
        except Exception as e:
            logger.error(f"获取文档内容失败: {str(e)}")
            return None
    
    def get_classification_suggestions(self, content: str) -> List[Dict]:
        """获取分类建议"""
        rule_result = self._classify_by_rules(content)
        
        suggestions = []
        if 'scores' in rule_result:
            # 按分数排序，返回前3个建议
            sorted_scores = sorted(rule_result['scores'].items(), key=lambda x: x[1], reverse=True)
            
            for category, score in sorted_scores[:3]:
                if score > 0:
                    suggestions.append({
                        'category': category,
                        'score': score,
                        'confidence': min(score / 10, 1.0)
                    })
        
        return suggestions
    
    def update_classification_rules(self, category: str, keywords: List[str], patterns: List[str]):
        """更新分类规则"""
        if category in self.classification_rules:
            self.classification_rules[category]['keywords'].extend(keywords)
            self.classification_rules[category]['patterns'].extend(patterns)
        else:
            self.classification_rules[category] = {
                'keywords': keywords,
                'patterns': patterns
            }
        
        logger.info(f"更新分类规则: {category}")

# 创建全局实例
classification_service = ClassificationService()