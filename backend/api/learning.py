from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.learning_path_service import LearningPathService
from services.content_generation_service import ContentGenerationService
from services.learning_profile_service import LearningProfileService
from models.user import User
from models.knowledge import Subject, KnowledgePoint
from models.question import Question
from utils.logger import get_logger
from utils.response import success_response, error_response
from utils.validation import validate_required_fields
from typing import List, Dict, Any

logger = get_logger(__name__)

@jwt_required()
def generate_learning_path():
    """
    生成个性化学习路径
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['subject_id']
        if not validate_required_fields(data, required_fields):
            return error_response('缺少必需字段', 400)
        
        subject_id = data['subject_id']
        diagnosis_report_id = data.get('diagnosis_report_id')
        target_level = data.get('target_level', 'intermediate')
        time_budget = data.get('time_budget', 30)  # 默认30分钟/天
        
        # 验证学科是否存在
        subject = Subject.query.get(subject_id)
        if not subject:
            return error_response('学科不存在', 404)
        
        # 生成学习路径
        learning_path = LearningPathService.generate_learning_path(
            user_id=user_id,
            subject_id=subject_id,
            diagnosis_report_id=diagnosis_report_id,
            target_level=target_level,
            time_budget=time_budget
        )
        
        return success_response(learning_path, '学习路径生成成功')
        
    except ValueError as e:
        logger.error(f"生成学习路径参数错误: {e}")
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"生成学习路径失败: {e}")
        return error_response('生成学习路径失败', 500)

@jwt_required()
def update_learning_progress():
    """
    更新学习进度
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['subject_id', 'knowledge_point_id', 'progress_data']
        if not validate_required_fields(data, required_fields):
            return error_response('缺少必需字段', 400)
        
        subject_id = data['subject_id']
        knowledge_point_id = data['knowledge_point_id']
        progress_data = data['progress_data']
        
        # 更新进度
        success = LearningPathService.update_learning_progress(
            user_id=user_id,
            subject_id=subject_id,
            knowledge_point_id=knowledge_point_id,
            progress_data=progress_data
        )
        
        if success:
            return success_response({}, '学习进度更新成功')
        else:
            return error_response('学习进度更新失败', 500)
        
    except Exception as e:
        logger.error(f"更新学习进度失败: {e}")
        return error_response('更新学习进度失败', 500)

@jwt_required()
def get_learning_progress(subject_id):
    """
    获取学习进度
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取学习进度
        progress = LearningPathService.get_learning_progress(
            user_id=user_id,
            subject_id=subject_id
        )
        
        return success_response(progress, '获取学习进度成功')
        
    except Exception as e:
        logger.error(f"获取学习进度失败: {e}")
        return error_response('获取学习进度失败', 500)

@jwt_required()
def generate_learning_content():
    """
    生成学习内容
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['knowledge_point_id']
        if not validate_required_fields(data, required_fields):
            return error_response('缺少必需字段', 400)
        
        knowledge_point_id = data['knowledge_point_id']
        content_type = data.get('content_type', 'explanation')
        difficulty_level = data.get('difficulty_level')
        learning_style = data.get('learning_style')
        
        # 验证知识点是否存在
        knowledge_point = KnowledgePoint.query.get(knowledge_point_id)
        if not knowledge_point:
            return error_response('知识点不存在', 404)
        
        # 验证内容类型
        valid_content_types = ['explanation', 'example', 'summary', 'analogy', 'step_by_step']
        if content_type not in valid_content_types:
            return error_response(f'不支持的内容类型，支持的类型: {", ".join(valid_content_types)}', 400)
        
        # 生成学习内容
        content = ContentGenerationService.generate_learning_content(
            knowledge_point_id=knowledge_point_id,
            user_id=user_id,
            content_type=content_type,
            difficulty_level=difficulty_level,
            learning_style=learning_style
        )
        
        return success_response(content, '学习内容生成成功')
        
    except ValueError as e:
        logger.error(f"生成学习内容参数错误: {e}")
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"生成学习内容失败: {e}")
        return error_response('生成学习内容失败', 500)

@jwt_required()
def generate_practice_questions():
    """
    生成练习题
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['knowledge_point_id']
        if not validate_required_fields(data, required_fields):
            return error_response('缺少必需字段', 400)
        
        knowledge_point_id = data['knowledge_point_id']
        question_count = data.get('question_count', 5)
        difficulty_range = data.get('difficulty_range')
        question_types = data.get('question_types')
        
        # 验证参数
        if question_count < 1 or question_count > 20:
            return error_response('题目数量必须在1-20之间', 400)
        
        if difficulty_range:
            if len(difficulty_range) != 2 or difficulty_range[0] > difficulty_range[1]:
                return error_response('难度范围格式错误', 400)
            if difficulty_range[0] < 1 or difficulty_range[1] > 5:
                return error_response('难度范围必须在1-5之间', 400)
        
        # 验证知识点是否存在
        knowledge_point = KnowledgePoint.query.get(knowledge_point_id)
        if not knowledge_point:
            return error_response('知识点不存在', 404)
        
        # 验证题目类型
        valid_question_types = ['single_choice', 'multiple_choice', 'true_false', 'fill_blank']
        if question_types:
            for qt in question_types:
                if qt not in valid_question_types:
                    return error_response(f'不支持的题目类型: {qt}', 400)
        
        # 生成练习题
        questions = ContentGenerationService.generate_practice_questions(
            knowledge_point_id=knowledge_point_id,
            user_id=user_id,
            question_count=question_count,
            difficulty_range=tuple(difficulty_range) if difficulty_range else None,
            question_types=question_types
        )
        
        return success_response({
            'questions': questions,
            'total_count': len(questions),
            'knowledge_point_id': knowledge_point_id
        }, '练习题生成成功')
        
    except ValueError as e:
        logger.error(f"生成练习题参数错误: {e}")
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"生成练习题失败: {e}")
        return error_response('生成练习题失败', 500)

@jwt_required()
def generate_question_explanation():
    """
    生成题目解释
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['question_id', 'user_answer', 'correct_answer']
        if not validate_required_fields(data, required_fields):
            return error_response('缺少必需字段', 400)
        
        question_id = data['question_id']
        user_answer = data['user_answer']
        correct_answer = data['correct_answer']
        
        # 验证题目是否存在
        question = Question.query.get(question_id)
        if not question:
            return error_response('题目不存在', 404)
        
        # 生成个性化解释
        explanation = ContentGenerationService.generate_personalized_explanation(
            question_id=question_id,
            user_answer=user_answer,
            correct_answer=correct_answer,
            user_id=user_id
        )
        
        return success_response(explanation, '题目解释生成成功')
        
    except ValueError as e:
        logger.error(f"生成题目解释参数错误: {e}")
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"生成题目解释失败: {e}")
        return error_response('生成题目解释失败', 500)

@jwt_required()
def get_learning_recommendations(subject_id):
    """
    获取学习建议
    """
    try:
        user_id = get_jwt_identity()
        
        # 验证学科是否存在
        subject = Subject.query.get(subject_id)
        if not subject:
            return error_response('学科不存在', 404)
        
        # 获取用户学习画像
        learning_profile = LearningProfileService.get_or_create_profile(
            user_id=user_id,
            subject_id=subject_id
        )
        
        if not learning_profile:
            return error_response('无法获取学习画像', 500)
        
        # 获取学习画像摘要
        profile_summary = LearningProfileService.get_profile_summary(learning_profile)
        
        # 构建学习建议
        recommendations = {
            'user_id': user_id,
            'subject_id': subject_id,
            'subject_name': subject.name,
            'profile_summary': profile_summary,
            'personalized_suggestions': profile_summary.get('recommendations', []),
            'learning_style_tips': _get_learning_style_tips(
                profile_summary.get('learning_style', 'balanced')
            ),
            'difficulty_recommendations': _get_difficulty_recommendations(
                profile_summary.get('difficulty_preference', 'medium')
            ),
            'time_management_tips': _get_time_management_tips(
                profile_summary.get('time_preferences', {})
            ),
            'generated_at': profile_summary.get('last_updated')
        }
        
        return success_response(recommendations, '获取学习建议成功')
        
    except Exception as e:
        logger.error(f"获取学习建议失败: {e}")
        return error_response('获取学习建议失败', 500)

# 辅助函数
def _get_learning_style_tips(learning_style: str) -> List[str]:
    """
    获取学习风格提示
    
    Args:
        learning_style: 学习风格
        
    Returns:
        提示列表
    """
    tips_map = {
        'visual': [
            '使用图表、思维导图和视觉辅助工具',
            '观看教学视频和动画演示',
            '用不同颜色标记重点内容',
            '创建视觉化的笔记和总结'
        ],
        'auditory': [
            '大声朗读学习材料',
            '参与讨论和口头解释',
            '听录音和播客',
            '用音乐或韵律帮助记忆'
        ],
        'hands_on': [
            '通过实际操作和实验学习',
            '制作模型和实物演示',
            '参与互动练习和游戏',
            '边学边做，理论结合实践'
        ],
        'reading': [
            '阅读详细的文字材料',
            '做大量的笔记和摘要',
            '查阅参考书籍和资料',
            '通过写作来整理思路'
        ],
        'balanced': [
            '结合多种学习方式',
            '根据内容特点选择合适的方法',
            '保持学习方式的多样性',
            '定期调整学习策略'
        ]
    }
    
    return tips_map.get(learning_style, tips_map['balanced'])

def _get_difficulty_recommendations(difficulty_preference: str) -> List[str]:
    """
    获取难度建议
    
    Args:
        difficulty_preference: 难度偏好
        
    Returns:
        建议列表
    """
    recommendations_map = {
        'easy': [
            '从基础概念开始，循序渐进',
            '多做简单题目建立信心',
            '确保基础牢固再进阶',
            '不要急于求成，稳扎稳打'
        ],
        'medium': [
            '保持适中的挑战性',
            '基础和进阶题目相结合',
            '根据掌握情况调整难度',
            '保持学习的持续性'
        ],
        'hard': [
            '挑战更高难度的题目',
            '深入理解概念的本质',
            '尝试解决复杂问题',
            '培养独立思考能力'
        ]
    }
    
    return recommendations_map.get(difficulty_preference, recommendations_map['medium'])

def _get_time_management_tips(time_preferences: Dict[str, Any]) -> List[str]:
    """
    获取时间管理建议
    
    Args:
        time_preferences: 时间偏好
        
    Returns:
        建议列表
    """
    tips = [
        '制定合理的学习计划',
        '保持规律的学习时间',
        '适当休息，避免疲劳学习',
        '根据注意力状态安排学习内容'
    ]
    
    # 根据偏好的学习时长调整建议
    preferred_duration = time_preferences.get('preferred_session_duration', 30)
    
    if preferred_duration <= 15:
        tips.extend([
            '利用碎片时间进行复习',
            '采用番茄工作法，短时高效',
            '重点关注核心概念'
        ])
    elif preferred_duration >= 60:
        tips.extend([
            '进行深度学习和思考',
            '安排完整的学习块时间',
            '结合理论学习和实践练习'
        ])
    else:
        tips.extend([
            '保持适中的学习节奏',
            '合理分配不同类型的学习任务',
            '定期评估学习效果'
        ])
    
    return tips