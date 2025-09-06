# -*- coding: utf-8 -*-
"""
人教版高中提示词工程服务

该服务专门为人教版高中教材设计，提供专业的学科答题提示词，
确保AI回答符合人教版教材标准和高中学习要求。

作者: AI智能学习系统
创建时间: 2025-01-06
"""

from typing import Dict, List, Any, Optional
from models.knowledge import Subject, KnowledgePoint
from utils.logger import get_logger

logger = get_logger(__name__)

class PEPHighSchoolPromptService:
    """
    人教版高中提示词工程服务
    
    专门针对人教版高中教材的提示词构建服务，
    提供各学科专业化的答题指导和知识解析。
    """
    
    def __init__(self):
        """初始化人教版高中提示词服务"""
        self.curriculum_standard = "人教版高中课程标准"
        self.grade_levels = ["高一", "高二", "高三"]
        
        # 人教版高中各学科核心素养
        self.core_competencies = {
            "语文": ["语言建构与运用", "思维发展与提升", "审美鉴赏与创造", "文化传承与理解"],
            "数学": ["数学抽象", "逻辑推理", "数学建模", "直观想象", "数学运算", "数据分析"],
            "英语": ["语言能力", "文化意识", "思维品质", "学习能力"],
            "物理": ["物理观念", "科学思维", "科学探究", "科学态度与责任"],
            "化学": ["宏观辨识与微观探析", "变化观念与平衡思想", "证据推理与模型认知", "科学探究与创新意识", "科学态度与社会责任"],
            "生物": ["生命观念", "科学思维", "科学探究", "社会责任"],
            "历史": ["唯物史观", "时空观念", "史料实证", "历史解释", "家国情怀"],
            "地理": ["人地协调观", "综合思维", "区域认知", "地理实践力"],
            "政治": ["政治认同", "科学精神", "法治意识", "公共参与"]
        }
        
        # 人教版教材版本信息
        self.textbook_versions = {
            "语文": "人教版普通高中教科书·语文（2019年版）",
            "数学": "人教A版普通高中教科书·数学（2019年版）",
            "英语": "人教版普通高中教科书·英语（2019年版）",
            "物理": "人教版普通高中教科书·物理（2019年版）",
            "化学": "人教版普通高中教科书·化学（2019年版）",
            "生物": "人教版普通高中教科书·生物学（2019年版）",
            "历史": "人教版普通高中教科书·历史（2019年版）",
            "地理": "人教版普通高中教科书·地理（2019年版）",
            "政治": "人教版普通高中教科书·思想政治（2019年版）"
        }
    
    def build_subject_specific_prompt(self, subject_name: str, question_type: str = "综合", 
                                    grade_level: str = "高中", context: Optional[Dict] = None) -> str:
        """
        构建学科专业提示词
        
        Args:
            subject_name: 学科名称
            question_type: 题目类型（选择题、填空题、解答题、综合题等）
            grade_level: 年级水平
            context: 上下文信息
            
        Returns:
            专业化的学科提示词
        """
        try:
            # 获取学科基础信息
            base_prompt = self._get_subject_base_prompt(subject_name, grade_level)
            
            # 添加题目类型特定要求
            type_specific_prompt = self._get_question_type_prompt(subject_name, question_type)
            
            # 添加人教版教材标准
            textbook_standard = self._get_textbook_standard_prompt(subject_name)
            
            # 添加核心素养要求
            competency_prompt = self._get_core_competency_prompt(subject_name)
            
            # 组合完整提示词
            full_prompt = f"""{base_prompt}

{textbook_standard}

{competency_prompt}

{type_specific_prompt}

答题标准要求：
1. 严格按照人教版教材内容和标准进行回答
2. 使用规范的学科术语和表达方式
3. 体现相应的学科核心素养
4. 答案层次清晰，逻辑严密
5. 适合{grade_level}学生的认知水平
6. 符合高考评分标准和要求
"""
            
            # 添加上下文信息
            if context:
                full_prompt += f"\n\n上下文信息：\n{self._format_context(context)}"
            
            return full_prompt
            
        except Exception as e:
            logger.error(f"构建学科提示词失败: {e}")
            return self._get_fallback_prompt(subject_name, grade_level)
    
    def _get_subject_base_prompt(self, subject_name: str, grade_level: str) -> str:
        """
        获取学科基础提示词
        """
        subject_prompts = {
            "语文": f"""
你是一位资深的{grade_level}语文教师，精通人教版语文教材体系。
请严格按照人教版语文课程标准和教学要求进行专业回答。

专业要求：
- 准确运用语文学科术语和概念
- 体现语文学科的人文性和工具性特点
- 注重文本解读和语言文字运用
- 培养学生的语文核心素养
- 结合课文内容和文学常识
""",
            "数学": f"""
你是一位资深的{grade_level}数学教师，精通人教A版数学教材体系。
请严格按照人教版数学课程标准和教学要求进行专业回答。

专业要求：
- 使用标准的数学符号和术语
- 解题过程逻辑清晰，步骤完整
- 注重数学思想方法的渗透
- 培养学生的数学核心素养
- 结合教材例题和习题特点
""",
            "英语": f"""
你是一位资深的{grade_level}英语教师，精通人教版英语教材体系。
请严格按照人教版英语课程标准和教学要求进行专业回答。

专业要求：
- 使用准确的英语语法和词汇知识
- 注重语言的实际运用和交际功能
- 培养学生的英语核心素养
- 结合教材话题和语言点
- 体现英语学科的工具性和人文性
""",
            "物理": f"""
你是一位资深的{grade_level}物理教师，精通人教版物理教材体系。
请严格按照人教版物理课程标准和教学要求进行专业回答。

专业要求：
- 使用准确的物理概念和定律
- 注重物理现象的本质分析
- 培养学生的物理核心素养
- 结合实验和生活实际
- 体现物理学科的科学性和实践性
""",
            "化学": f"""
你是一位资深的{grade_level}化学教师，精通人教版化学教材体系。
请严格按照人教版化学课程标准和教学要求进行专业回答。

专业要求：
- 使用准确的化学概念和原理
- 注重宏观现象与微观本质的联系
- 培养学生的化学核心素养
- 结合化学实验和生产生活
- 体现化学学科的实验性和应用性
""",
            "生物": f"""
你是一位资深的{grade_level}生物教师，精通人教版生物学教材体系。
请严格按照人教版生物课程标准和教学要求进行专业回答。

专业要求：
- 使用准确的生物学概念和原理
- 注重结构与功能的统一性
- 培养学生的生物学核心素养
- 结合生物实验和生活实际
- 体现生物学科的实验性和探究性
""",
            "历史": f"""
你是一位资深的{grade_level}历史教师，精通人教版历史教材体系。
请严格按照人教版历史课程标准和教学要求进行专业回答。

专业要求：
- 使用准确的历史概念和史实
- 注重史论结合和史料实证
- 培养学生的历史核心素养
- 结合教材内容和史学观点
- 体现历史学科的人文性和思辨性
""",
            "地理": f"""
你是一位资深的{grade_level}地理教师，精通人教版地理教材体系。
请严格按照人教版地理课程标准和教学要求进行专业回答。

专业要求：
- 使用准确的地理概念和原理
- 注重人地关系和区域特征
- 培养学生的地理核心素养
- 结合地图和地理实践
- 体现地理学科的综合性和实践性
""",
            "政治": f"""
你是一位资深的{grade_level}思想政治教师，精通人教版思想政治教材体系。
请严格按照人教版思想政治课程标准和教学要求进行专业回答。

专业要求：
- 使用准确的政治概念和理论
- 注重理论联系实际
- 培养学生的思想政治核心素养
- 结合时事和社会热点
- 体现思想政治学科的思想性和实践性
"""
        }
        
        return subject_prompts.get(subject_name, f"""
你是一位资深的{grade_level}{subject_name}教师，请按照人教版教材标准进行专业回答。
""")
    
    def _get_question_type_prompt(self, subject_name: str, question_type: str) -> str:
        """
        获取题目类型特定提示词
        """
        type_prompts = {
            "选择题": """
选择题答题要求：
1. 仔细分析题干，明确考查的知识点
2. 逐一分析各个选项，排除干扰项
3. 选择最符合题意的正确答案
4. 说明选择理由和排除其他选项的原因
5. 答案格式：正确答案是X，理由是...
""",
            "填空题": """
填空题答题要求：
1. 准确理解题意，确定填空内容的性质
2. 使用规范的学科术语和表达
3. 答案要简洁准确，符合题目要求
4. 注意单位、符号等细节要求
5. 必要时提供解题思路说明
""",
            "解答题": """
解答题答题要求：
1. 审题仔细，明确题目要求和考查内容
2. 解答过程完整，步骤清晰
3. 使用规范的学科语言和符号
4. 结论明确，符合题意
5. 适当说明解题思路和方法
""",
            "综合题": """
综合题答题要求：
1. 全面分析题目，把握各部分之间的联系
2. 运用多个知识点进行综合分析
3. 答案要有层次性和逻辑性
4. 注重知识的迁移和应用
5. 体现学科核心素养的综合运用
""",
            "实验题": """
实验题答题要求：
1. 明确实验目的和原理
2. 分析实验步骤和操作要点
3. 处理实验数据，得出结论
4. 分析可能的误差和改进措施
5. 体现科学探究的思维过程
"""
        }
        
        return type_prompts.get(question_type, "")
    
    def _get_textbook_standard_prompt(self, subject_name: str) -> str:
        """
        获取教材标准提示词
        """
        textbook_version = self.textbook_versions.get(subject_name, f"人教版{subject_name}教材")
        
        return f"""
教材标准要求：
- 严格依据{textbook_version}的内容体系
- 遵循课程标准的学习目标和要求
- 体现教材的知识结构和逻辑体系
- 使用教材中的标准术语和表达方式
- 结合教材中的典型例题和案例
"""
    
    def _get_core_competency_prompt(self, subject_name: str) -> str:
        """
        获取核心素养提示词
        """
        competencies = self.core_competencies.get(subject_name, [])
        
        if not competencies:
            return ""
        
        competency_text = "、".join(competencies)
        
        return f"""
学科核心素养要求：
本学科核心素养包括：{competency_text}

在回答中应该：
1. 体现相应的核心素养要求
2. 培养学生的学科思维能力
3. 注重知识与能力的有机结合
4. 促进学生全面发展
"""
    
    def _format_context(self, context: Dict) -> str:
        """
        格式化上下文信息
        """
        formatted_context = []
        
        if context.get('knowledge_points'):
            formatted_context.append(f"相关知识点：{', '.join(context['knowledge_points'])}")
        
        if context.get('difficulty_level'):
            formatted_context.append(f"难度等级：{context['difficulty_level']}")
        
        if context.get('exam_type'):
            formatted_context.append(f"考试类型：{context['exam_type']}")
        
        if context.get('chapter'):
            formatted_context.append(f"所属章节：{context['chapter']}")
        
        return "\n".join(formatted_context)
    
    def _get_fallback_prompt(self, subject_name: str, grade_level: str) -> str:
        """
        获取备用提示词
        """
        return f"""
你是一位专业的{grade_level}{subject_name}教师，请按照人教版教材标准和课程要求进行回答。

基本要求：
1. 使用准确的学科术语和概念
2. 答案符合{grade_level}学生的认知水平
3. 体现学科的核心素养要求
4. 遵循人教版教材的知识体系
5. 注重理论联系实际
"""
    
    def get_exam_oriented_prompt(self, subject_name: str, exam_type: str = "高考") -> str:
        """
        获取考试导向的提示词
        
        Args:
            subject_name: 学科名称
            exam_type: 考试类型（高考、期中、期末等）
            
        Returns:
            考试导向的提示词
        """
        base_prompt = self.build_subject_specific_prompt(subject_name, "综合", "高中")
        
        exam_specific = f"""

{exam_type}答题要求：
1. 严格按照{exam_type}评分标准进行回答
2. 注重答题的规范性和完整性
3. 体现学科核心素养的考查要求
4. 答案要有层次性和逻辑性
5. 使用标准的学科术语和表达
6. 适当展示解题思路和方法

评分关注点：
- 知识点掌握的准确性
- 解题方法的合理性
- 表达的规范性和完整性
- 学科思维的体现程度
"""
        
        return base_prompt + exam_specific
    
    def get_knowledge_point_prompt(self, knowledge_point: KnowledgePoint) -> str:
        """
        获取知识点专项提示词
        
        Args:
            knowledge_point: 知识点对象
            
        Returns:
            知识点专项提示词
        """
        subject_name = knowledge_point.subject.name if knowledge_point.subject else "未知学科"
        
        base_prompt = self.build_subject_specific_prompt(subject_name)
        
        knowledge_specific = f"""

知识点专项要求：
- 知识点名称：{knowledge_point.name}
- 难度等级：{knowledge_point.difficulty_level or '中等'}
- 重要程度：{knowledge_point.importance_level or '重要'}

教学要求：
1. 准确阐述该知识点的核心内容
2. 说明其在学科体系中的地位和作用
3. 提供典型的应用实例和练习
4. 指出学习中的重点和难点
5. 建议相应的学习方法和策略
"""
        
        return base_prompt + knowledge_specific

# 创建全局服务实例
pep_prompt_service = PEPHighSchoolPromptService()