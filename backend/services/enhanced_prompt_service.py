# -*- coding: utf-8 -*-
"""
增强版提示词工程服务

根据用户年级设定调用不同的提示词工程，提供精准的学科指导，
减少废话，直接提供干货内容，并能关联用户材料或搜索网络资源。

作者: AI智能学习系统
创建时间: 2025-01-06
"""

from typing import Dict, List, Any, Optional
from models.knowledge import Subject, KnowledgePoint
from utils.logger import get_logger

logger = get_logger(__name__)

class EnhancedPromptService:
    """
    增强版提示词工程服务
    
    根据年级智能调用不同的提示词工程，提供精准的学科指导。
    """
    
    def __init__(self):
        """初始化增强版提示词服务"""
        
        # 年级对应的教材版本和难度
        self.grade_configs = {
            "小学": {
                "grades": ["一年级", "二年级", "三年级", "四年级", "五年级", "六年级"],
                "difficulty": "基础",
                "style": "生动有趣",
                "textbook": "人教版小学教材"
            },
            "初中": {
                "grades": ["初一", "初二", "初三", "七年级", "八年级", "九年级"],
                "difficulty": "中等",
                "style": "循序渐进",
                "textbook": "人教版初中教材"
            },
            "高中": {
                "grades": ["高一", "高二", "高三"],
                "difficulty": "较高",
                "style": "严谨专业",
                "textbook": "人教版高中教材"
            }
        }
        
        # 各学段核心要求
        self.stage_requirements = {
            "小学": {
                "语文": "识字写字、阅读理解、口语交际、习作表达",
                "数学": "数与代数、图形与几何、统计与概率、综合实践",
                "英语": "听说读写、语音语调、词汇积累、简单交流"
            },
            "初中": {
                "语文": "现代文阅读、古诗文阅读、写作表达、口语交际",
                "数学": "数与式、方程与不等式、函数、图形与几何、统计与概率",
                "英语": "听力理解、口语表达、阅读理解、写作能力",
                "物理": "力学、热学、光学、电学基础",
                "化学": "物质构成、化学反应、酸碱盐、金属非金属",
                "生物": "生物体结构、生命活动、遗传变异、生态环境",
                "历史": "中国古代史、中国近现代史、世界史",
                "地理": "地球地图、中国地理、世界地理",
                "政治": "道德品质、法律常识、国情教育"
            },
            "高中": {
                "语文": "现代文阅读、古诗文阅读、语言文字运用、写作表达",
                "数学": "函数、几何、代数、统计概率、数学建模",
                "英语": "阅读理解、完形填空、语法填空、写作翻译",
                "物理": "力学、电磁学、热学、光学、原子物理",
                "化学": "无机化学、有机化学、物理化学、化学实验",
                "生物": "分子细胞生物学、遗传进化、稳态调节、生态环境",
                "历史": "政治史、经济史、文化史、世界史",
                "地理": "自然地理、人文地理、区域地理、地理信息技术",
                "政治": "经济生活、政治生活、文化生活、生活哲学"
            }
        }
    
    def build_grade_specific_prompt(self, subject_name: str, grade_level: str, 
                                  question_type: str = "综合", context: Optional[Dict] = None) -> str:
        """
        根据年级构建专门的提示词
        
        Args:
            subject_name: 学科名称
            grade_level: 年级水平
            question_type: 题目类型
            context: 上下文信息
            
        Returns:
            构建的提示词
        """
        # 确定学段
        stage = self._determine_stage(grade_level)
        stage_config = self.grade_configs.get(stage, self.grade_configs["高中"])
        
        # 获取用户材料信息
        user_materials = self._get_user_materials(context)
        
        # 构建基础提示词
        base_prompt = f"""
你是专业的{stage_config['textbook']}{subject_name}学科助手。

**教学标准**：严格按照{stage_config['textbook']}课程标准
**年级水平**：{grade_level}（{stage_config['difficulty']}难度）
**回答风格**：{stage_config['style']}，直接干货，无废话

**学科要求**：
{self._get_subject_requirements(subject_name, stage)}

**答题标准**：
1. 直接回答问题，不要多余的问候和铺垫
2. 知识点总结要干练精辟，紧扣教材内容
3. 优先关联用户上传的材料和试卷
4. 如无相关材料，提供网络搜索的试题和网址
5. 答案要符合{grade_level}学生的认知水平
6. 使用规范的学科术语和解题方法
"""
        
        # 添加用户材料关联
        if user_materials:
            base_prompt += f"\n**用户材料关联**：\n{user_materials}\n"
        
        # 添加题目类型特定要求
        type_prompt = self._get_question_type_prompt(question_type, stage)
        if type_prompt:
            base_prompt += f"\n**{question_type}题型要求**：\n{type_prompt}\n"
        
        # 添加网络搜索指导
        base_prompt += f"""
**资源补充要求**：
- 当需要补充练习题时，说明"建议搜索：[具体关键词]"并提供相关网址
- 引用网络资源时，必须标注来源网址
- 优先推荐权威教育网站的内容
"""
        
        return base_prompt
    
    def _determine_stage(self, grade_level: str) -> str:
        """确定学段"""
        if not grade_level or grade_level.strip() == '':
            return "高中"  # 默认为高中
        for stage, config in self.grade_configs.items():
            if grade_level in config["grades"] or any(g in grade_level for g in config["grades"]):
                return stage
        return "高中"  # 默认高中
    
    def _get_subject_requirements(self, subject_name: str, stage: str) -> str:
        """获取学科要求"""
        requirements = self.stage_requirements.get(stage, {})
        return requirements.get(subject_name, f"{subject_name}学科基础知识和能力培养")
    
    def _get_user_materials(self, context: Optional[Dict]) -> str:
        """获取用户材料信息（包含个人描述与知识图谱标签/描述摘要）"""
        if not context:
            return ""
        
        lines: List[str] = []
        
        # 个人描述
        user_bio = context.get('user_bio') or context.get('bio')
        if isinstance(user_bio, str) and user_bio.strip():
            bio = user_bio.strip()
            short_bio = bio[:120] + ('…' if len(bio) > 120 else '')
            lines.append(f"个人描述：{short_bio}")
        
        # 资料概况（来自调用方预汇总的字符串）
        summarized_materials = context.get('user_materials')
        if isinstance(summarized_materials, str) and summarized_materials.strip():
            lines.append(f"资料概况：{summarized_materials.strip()}")
        
        # 综合数据细节
        comprehensive_data = context.get('comprehensive_data', {})
        if isinstance(comprehensive_data, dict) and comprehensive_data:
            # 文档/试卷/错题 统计
            documents = comprehensive_data.get('documents', [])
            if isinstance(documents, list) and documents:
                lines.append(f"相关文档：{len(documents)}份")
            exam_papers = comprehensive_data.get('exam_papers', [])
            if isinstance(exam_papers, list) and exam_papers:
                lines.append(f"相关试卷：{len(exam_papers)}份")
            mistake_records = comprehensive_data.get('mistake_records', [])
            if isinstance(mistake_records, list) and mistake_records:
                lines.append(f"错题记录：{len(mistake_records)}道")
            
            # 知识图谱摘要（名称+标签+描述）
            knowledge_graphs = comprehensive_data.get('knowledge_graphs', [])
            if isinstance(knowledge_graphs, list) and knowledge_graphs:
                lines.append(f"知识图谱：{len(knowledge_graphs)}个")
                # 取前2-3个做摘要，避免过长
                for kg in knowledge_graphs[:3]:
                    if not isinstance(kg, dict):
                        continue
                    name = str(kg.get('name', '未命名图谱'))
                    tags = [t for t in kg.get('tags', []) if isinstance(t, str)]
                    desc = kg.get('description') or ''
                    # 标签与描述裁剪
                    tags_str = ', '.join(tags[:5]) if tags else '无标签'
                    short_desc = (desc[:80] + '…') if isinstance(desc, str) and len(desc) > 80 else (desc if isinstance(desc, str) else '')
                    lines.append(f"- 知识图谱《{name}》：标签：{tags_str}；简介：{short_desc}")
        
        return "\n".join(lines) if lines else "暂无相关材料"
    
    def _get_question_type_prompt(self, question_type: str, stage: str) -> str:
        """获取题目类型特定提示词"""
        type_prompts = {
            "选择题": "提供准确答案和详细解析，说明每个选项的对错原因",
            "填空题": "给出准确答案，解释解题思路和关键步骤",
            "解答题": "按步骤详细解答，标注得分要点，提供规范答题格式",
            "证明题": "严格按照逻辑顺序证明，标注关键定理和推理步骤",
            "计算题": "列出完整计算过程，注意单位和有效数字",
            "实验题": "说明实验原理、步骤、注意事项和结果分析",
            "作文题": "提供写作思路、结构安排和优秀范例",
            "阅读理解": "分析文本结构，提供答题技巧和标准答案"
        }
        
        return type_prompts.get(question_type, "按照标准答题格式回答")
    
    def build_knowledge_summary_prompt(self, subject_name: str, grade_level: str, 
                                     knowledge_point: str, context: Optional[Dict] = None) -> str:
        """构建知识点总结提示词"""
        stage = self._determine_stage(grade_level)
        stage_config = self.grade_configs.get(stage, self.grade_configs["高中"])
        
        return f"""
你是{stage_config['textbook']}{subject_name}专家。请对"{knowledge_point}"进行精准总结。

**总结要求**：
1. 核心概念：用最简洁的语言说明本质
2. 关键公式/定理：列出重要公式并说明适用条件
3. 解题方法：总结常见题型和解题思路
4. 易错点：指出学生常犯错误和注意事项
5. 关联知识：说明与其他知识点的联系
6. 实际应用：举出生活中的应用实例

**格式要求**：
- 每部分用简洁的要点形式
- 避免冗长的解释和废话
- 突出重点和难点
- 适合{grade_level}学生理解

**补充资源**：
如需更多练习题，建议搜索："{subject_name} {knowledge_point} {grade_level} 练习题"
推荐网站：中学学科网、菁优网、组卷网
"""
    
    def build_exam_analysis_prompt(self, subject_name: str, grade_level: str, 
                                 exam_type: str = "期末考试") -> str:
        """构建考试分析提示词"""
        stage = self._determine_stage(grade_level)
        stage_config = self.grade_configs.get(stage, self.grade_configs["高中"])
        
        return f"""
你是{stage_config['textbook']}{subject_name}考试分析专家。

**分析任务**：对{exam_type}进行专业分析

**分析维度**：
1. 考点分布：各章节知识点的分值占比
2. 题型分析：各类题型的数量和难度
3. 能力要求：考查的核心能力和素养
4. 难度评估：整体难度和区分度分析
5. 答题策略：时间分配和答题顺序建议

**输出格式**：
- 用数据和图表形式展示分析结果
- 提供具体的备考建议
- 推荐针对性的复习资料

**资源推荐**：
相关真题搜索："{subject_name} {grade_level} {exam_type} 真题"
权威网站：教育部考试中心、各省教育考试院
"""
    
    def get_web_search_suggestions(self, subject_name: str, grade_level: str, 
                                 topic: str, question_type: str = "练习题") -> Dict[str, Any]:
        """获取网络搜索建议"""
        stage = self._determine_stage(grade_level)
        
        search_keywords = [
            f"{subject_name} {topic} {grade_level} {question_type}",
            f"{topic} {question_type} 解析",
            f"{subject_name} {topic} 知识点总结"
        ]
        
        recommended_sites = {
            "小学": [
                "https://www.zxxk.com/ - 中学学科网小学频道",
                "https://www.jyeoo.com/ - 菁优网小学题库",
                "https://www.21cnjy.com/ - 21世纪教育网"
            ],
            "初中": [
                "https://www.zxxk.com/ - 中学学科网",
                "https://www.jyeoo.com/ - 菁优网",
                "https://www.zzstep.com/ - 中华资源库"
            ],
            "高中": [
                "https://www.zxxk.com/ - 中学学科网",
                "https://www.jyeoo.com/ - 菁优网",
                "https://www.zujuan.com/ - 组卷网",
                "https://gaokao.chsi.com.cn/ - 阳光高考平台"
            ]
        }
        
        return {
            "search_keywords": search_keywords,
            "recommended_sites": recommended_sites.get(stage, recommended_sites["高中"]),
            "search_tips": [
                "使用具体的知识点名称搜索",
                "添加年级和题型关键词",
                "选择权威教育网站的内容",
                "注意题目的时效性和准确性"
            ]
        }
    
    def build_enhanced_prompt_with_search(self, subject_name: str, grade_level: str, 
                                         question_type: str = "综合", context: Optional[Dict] = None) -> str:
        """构建集成网络搜索功能的增强提示词"""
        if not context:
            context = {}
            
        # 获取基础提示词
        base_prompt = self.build_grade_specific_prompt(subject_name, grade_level, question_type, context)
        
        # 检查是否有用户材料
        user_materials = context.get('user_materials', '暂无相关材料')
        
        # 如果没有相关材料，添加网络搜索建议
        if '暂无相关' in user_materials:
            topic = context.get('topic', '基础知识')
            search_suggestions = self.get_web_search_suggestions(subject_name, grade_level, topic)
            
            # 安全地获取搜索查询
            search_keywords = search_suggestions.get('search_keywords', [])
            query1 = search_keywords[0] if search_keywords and len(search_keywords) > 0 else f'{grade_level} {subject_name} {topic}'
            query2 = search_keywords[1] if len(search_keywords) > 1 else f'{subject_name} {topic} 练习题'
            
            search_prompt = f"""

🔍 **网络搜索建议**：
由于暂无相关学习材料，建议搜索以下关键词获取更多资源：
- {query1}
- {query2}

📚 **推荐网站**：
- 学科网 (zxxk.com) - 专业教育资源
- 21世纪教育网 (21cnjy.com) - 试卷题库
- 菁优网 (jyeoo.com) - 在线题库

💡 **搜索提示**：
- 使用"年级+科目+知识点"的组合进行搜索
- 添加"练习题"、"试卷"等关键词获取更精准结果
- 关注官方教育网站和知名教育平台的内容
"""
            base_prompt += search_prompt
        
        return base_prompt
    
    def search_related_exercises(self, grade_level: str, subject_name: str, topic: str) -> Dict[str, Any]:
        """
        搜索相关练习题和试题
        """
        try:
            from services.web_search_service import web_search_service
        except ImportError:
            logger.warning("Web search service not available")
            return {
                'success': False,
                'error': 'Web search service not available',
                'query': '',
                'results': [],
                'total_results': 0
            }
        
        # 构建搜索查询
        search_query = f"{grade_level} {subject_name} {topic} 练习题 试卷"
        
        try:
            # 执行网络搜索
            search_results = web_search_service.search(search_query, num_results=5)
            
            # 格式化搜索结果
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'snippet': result.get('snippet', ''),
                    'source': result.get('source', '')
                })
            
            logger.info(f"Successfully searched for {topic} exercises, found {len(formatted_results)} results")
            
            return {
                'success': True,
                'query': search_query,
                'results': formatted_results,
                'total_results': len(formatted_results)
            }
        except Exception as e:
            logger.error(f"Error searching for exercises: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'query': search_query,
                'results': [],
                'total_results': 0
            }

# 创建全局服务实例
enhanced_prompt_service = EnhancedPromptService()