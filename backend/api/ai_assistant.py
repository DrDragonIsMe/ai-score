#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - API接口 - ai_assistant.py

Description:
    AI助理"高小分"API接口，提供智能对话、拍照识别、学习建议等功能。

Author: Chang Xinglong
Date: 2025-08-31
Version: 1.0.0
License: Apache License 2.0
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from utils.response import success_response, error_response
from services.ai_assistant_service import ai_assistant_service
from models.conversation import Conversation, ConversationMessage
from utils.database import db
from utils.logger import get_logger

logger = get_logger(__name__)

# 创建蓝图
ai_assistant_bp = Blueprint('ai_assistant', __name__, url_prefix='/ai-assistant')

@ai_assistant_bp.route('/info', methods=['GET'])
def get_assistant_info():
    """
    获取AI助理基本信息
    """
    info = ai_assistant_service.get_assistant_info()
    return success_response(info, "获取AI助理信息成功")

@ai_assistant_bp.route('/chat', methods=['POST'])
@jwt_required()
def chat_with_assistant():
    """
    与AI助理对话
    
    请求参数:
    - message: 用户消息
    - context: 对话上下文（可选）
    - model_id: 指定使用的AI模型ID（可选）
    """
    data = request.get_json()
    
    if not data or 'message' not in data:
        return error_response("缺少必要参数：message", 400)
    
    message = data['message']
    context = data.get('context')
    model_id = data.get('model_id')
    template_id = data.get('template_id')
    
    if not message.strip():
        return error_response("消息内容不能为空", 400)
    
    try:
        # 从JWT token中获取用户ID
        current_user_data = get_jwt_identity()
        user_id = current_user_data['user_id']
        
        # 调用AI助理服务
        result = ai_assistant_service.chat_with_user(
            user_id=user_id,
            message=message,
            context=context,
            model_id=model_id,
            template_id=template_id
        )
        
        if result['success']:
            return success_response(result, "对话成功")
        else:
            logger.error(f"AI助理对话失败: {result.get('error', '未知错误')}")
            return error_response("AI助理暂时不可用，请检查模型配置", 503)
    except Exception as e:
        logger.error(f"AI助理API异常: {str(e)}")
        return error_response("AI助理服务异常，请稍后重试", 503)

@ai_assistant_bp.route('/recognize-image', methods=['POST'])
def recognize_question_image():
    """
    拍照识别试题
    
    请求参数:
    - image_data: Base64编码的图片数据
    """
    data = request.get_json()
    
    if not data or 'image_data' not in data:
        return error_response("缺少必要参数：image_data", 400)
    
    image_data = data['image_data']
    
    if not image_data:
        return error_response("图片数据不能为空", 400)
    
    # 移除data:image前缀（如果存在）
    if image_data.startswith('data:image'):
        image_data = image_data.split(',')[1]
    
    # 调用图片识别服务（暂时使用固定用户ID）
    result = ai_assistant_service.recognize_question_from_image(
        user_id="1",
        image_data=image_data
    )
    
    if result['success']:
        return success_response(result, "图片识别成功")
    else:
        return error_response(result.get('message', '图片识别失败'), 500)

@ai_assistant_bp.route('/analyze-question', methods=['POST'])
def analyze_question():
    """
    分析并解答试题
    
    请求参数:
    - question_text: 题目文本
    - user_answer: 用户答案（可选）
    """
    data = request.get_json()
    
    if not data or 'question_text' not in data:
        return error_response("缺少必要参数：question_text", 400)
    
    question_text = data['question_text']
    user_answer = data.get('user_answer')
    
    if not question_text.strip():
        return error_response("题目内容不能为空", 400)
    
    # 调用题目分析服务（暂时使用固定用户ID）
    result = ai_assistant_service.analyze_and_solve_question(
        user_id="1",
        question_text=question_text,
        user_answer=user_answer
    )
    
    if result['success']:
        return success_response(result, "题目分析成功")
    else:
        return error_response(result.get('message', '题目分析失败'), 500)

@ai_assistant_bp.route('/recommendations', methods=['GET'])
def get_personalized_recommendations():
    """
    获取个性化学习建议
    """
    result = ai_assistant_service.get_personalized_recommendations(
        user_id="1"
    )
    
    if result['success']:
        return success_response(result, "获取学习建议成功")
    else:
        return error_response(result.get('message', '获取建议失败'), 500)

@ai_assistant_bp.route('/quick-help', methods=['POST'])
def quick_help():
    """
    快速帮助功能
    
    请求参数:
    - help_type: 帮助类型（study_plan, weak_points, motivation等）
    - subject: 科目（可选）
    """
    data = request.get_json()
    
    if not data or 'help_type' not in data:
        return error_response("缺少必要参数：help_type", 400)
    
    help_type = data['help_type']
    subject = data.get('subject')
    
    # 根据帮助类型提供不同的快速帮助
    if help_type == 'study_plan':
        result = ai_assistant_service.get_personalized_recommendations("1")
        if result['success']:
            return success_response({
                'help_content': result['recommendations']['daily_study_plan'],
                'type': 'study_plan'
            }, "获取学习计划成功")
    
    elif help_type == 'weak_points':
        result = ai_assistant_service.get_personalized_recommendations("1")
        if result['success']:
            return success_response({
                'help_content': result['recommendations']['weak_points_focus'],
                'type': 'weak_points'
            }, "获取薄弱点分析成功")
    
    elif help_type == 'motivation':
        result = ai_assistant_service.get_personalized_recommendations("1")
        if result['success']:
            return success_response({
                'help_content': result['recommendations']['motivational_message'],
                'type': 'motivation'
            }, "获取激励消息成功")
    
    else:
        return error_response("不支持的帮助类型", 400)
    
    return error_response("获取帮助失败", 500)

@ai_assistant_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """
    提交用户反馈
    
    请求参数:
    - feedback_type: 反馈类型（helpful, not_helpful, suggestion等）
    - content: 反馈内容
    - rating: 评分（1-5）
    """
    data = request.get_json()
    
    if not data:
        return error_response("缺少反馈数据", 400)
    
    feedback_type = data.get('feedback_type', 'general')
    content = data.get('content', '')
    rating = data.get('rating')
    
    # 记录用户反馈（这里可以保存到数据库）
    logger.info(f"用户反馈 - 用户ID: 1, 类型: {feedback_type}, 评分: {rating}, 内容: {content}")
    
    return success_response({
        'message': '感谢您的反馈！我会继续努力为您提供更好的服务。',
        'feedback_id': f"fb_1_{int(datetime.now().timestamp())}"
    }, "反馈提交成功")

# ==================== 会话管理API ====================

@ai_assistant_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    """
    获取用户的会话列表
    
    查询参数:
    - page: 页码（默认1）
    - per_page: 每页数量（默认20）
    - starred_only: 只显示收藏的（默认false）
    - include_archived: 包含已归档的（默认false）
    """
    try:
        current_user_data = get_jwt_identity()
        user_id = current_user_data['user_id']
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        starred_only = request.args.get('starred_only', 'false').lower() == 'true'
        include_archived = request.args.get('include_archived', 'false').lower() == 'true'
        
        result = Conversation.get_user_conversations(
            user_id=user_id,
            page=page,
            per_page=per_page,
            starred_only=starred_only,
            include_archived=include_archived
        )
        
        return success_response(result, "获取会话列表成功")
    except Exception as e:
        logger.error(f"获取会话列表失败: {str(e)}")
        return error_response("获取会话列表失败", 500)

@ai_assistant_bp.route('/conversations', methods=['POST'])
@jwt_required()
def create_conversation():
    """
    创建新会话
    
    请求参数:
    - title: 会话标题（可选）
    """
    try:
        current_user_data = get_jwt_identity()
        user_id = current_user_data['user_id']
        
        data = request.get_json() or {}
        title = data.get('title', '新对话')
        
        conversation = Conversation(
            user_id=user_id,
            title=title
        )
        
        db.session.add(conversation)
        db.session.commit()
        
        return success_response(conversation.to_dict(), "创建会话成功")
    except Exception as e:
        logger.error(f"创建会话失败: {str(e)}")
        db.session.rollback()
        return error_response("创建会话失败", 500)

@ai_assistant_bp.route('/conversations/<conversation_id>', methods=['GET'])
@jwt_required()
def get_conversation(conversation_id):
    """
    获取指定会话详情
    
    路径参数:
    - conversation_id: 会话ID
    """
    try:
        current_user_data = get_jwt_identity()
        user_id = current_user_data['user_id']
        
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=user_id
        ).first()
        
        if not conversation:
            return error_response("会话不存在", 404)
        
        return success_response(conversation.to_dict(include_messages=True), "获取会话详情成功")
    except Exception as e:
        logger.error(f"获取会话详情失败: {str(e)}")
        return error_response("获取会话详情失败", 500)

@ai_assistant_bp.route('/conversations/<conversation_id>', methods=['PUT'])
@jwt_required()
def update_conversation(conversation_id):
    """
    更新会话信息
    
    路径参数:
    - conversation_id: 会话ID
    
    请求参数:
    - title: 新标题（可选）
    - starred: 收藏状态（可选）
    - archived: 归档状态（可选）
    """
    try:
        current_user_data = get_jwt_identity()
        user_id = current_user_data['user_id']
        
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=user_id
        ).first()
        
        if not conversation:
            return error_response("会话不存在", 404)
        
        data = request.get_json() or {}
        
        # 更新标题
        if 'title' in data:
            if not conversation.update_title(data['title']):
                return error_response("标题不能为空", 400)
        
        # 更新收藏状态
        if 'starred' in data:
            conversation.starred = bool(data['starred'])
        
        # 更新归档状态
        if 'archived' in data:
            if data['archived']:
                conversation.archive()
            else:
                conversation.unarchive()
        
        db.session.commit()
        
        return success_response(conversation.to_dict(), "更新会话成功")
    except Exception as e:
        logger.error(f"更新会话失败: {str(e)}")
        db.session.rollback()
        return error_response("更新会话失败", 500)

@ai_assistant_bp.route('/conversations/<conversation_id>', methods=['DELETE'])
@jwt_required()
def delete_conversation(conversation_id):
    """
    删除会话
    
    路径参数:
    - conversation_id: 会话ID
    """
    try:
        current_user_data = get_jwt_identity()
        user_id = current_user_data['user_id']
        
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=user_id
        ).first()
        
        if not conversation:
            return error_response("会话不存在", 404)
        
        db.session.delete(conversation)
        db.session.commit()
        
        return success_response({"id": conversation_id}, "删除会话成功")
    except Exception as e:
        logger.error(f"删除会话失败: {str(e)}")
        db.session.rollback()
        return error_response("删除会话失败", 500)

@ai_assistant_bp.route('/conversations/<conversation_id>/star', methods=['POST'])
@jwt_required()
def toggle_conversation_star(conversation_id):
    """
    切换会话收藏状态
    
    路径参数:
    - conversation_id: 会话ID
    """
    try:
        current_user_data = get_jwt_identity()
        user_id = current_user_data['user_id']
        
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=user_id
        ).first()
        
        if not conversation:
            return error_response("会话不存在", 404)
        
        starred = conversation.toggle_star()
        db.session.commit()
        
        return success_response({
            "id": conversation_id,
            "starred": starred
        }, f"会话{'收藏' if starred else '取消收藏'}成功")
    except Exception as e:
        logger.error(f"切换收藏状态失败: {str(e)}")
        db.session.rollback()
        return error_response("操作失败", 500)

@ai_assistant_bp.route('/conversations/search', methods=['GET'])
@jwt_required()
def search_conversations():
    """
    搜索会话
    
    查询参数:
    - keyword: 搜索关键词
    - page: 页码（默认1）
    - per_page: 每页数量（默认20）
    """
    try:
        current_user_data = get_jwt_identity()
        user_id = current_user_data['user_id']
        
        keyword = request.args.get('keyword', '').strip()
        if not keyword:
            return error_response("搜索关键词不能为空", 400)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        result = Conversation.search_conversations(
            user_id=user_id,
            keyword=keyword,
            page=page,
            per_page=per_page
        )
        
        return success_response(result, "搜索会话成功")
    except Exception as e:
        logger.error(f"搜索会话失败: {str(e)}")
        return error_response("搜索会话失败", 500)

@ai_assistant_bp.route('/conversations/<conversation_id>/messages', methods=['POST'])
@jwt_required()
def add_message_to_conversation(conversation_id):
    """
    向会话添加消息
    
    路径参数:
    - conversation_id: 会话ID
    
    请求参数:
    - role: 消息角色（user/assistant/system）
    - content: 消息内容
    - message_type: 消息类型（默认text）
    - metadata: 元数据（可选）
    """
    try:
        current_user_data = get_jwt_identity()
        user_id = current_user_data['user_id']
        
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=user_id
        ).first()
        
        if not conversation:
            return error_response("会话不存在", 404)
        
        data = request.get_json()
        if not data or 'role' not in data or 'content' not in data:
            return error_response("缺少必要参数：role, content", 400)
        
        role = data['role']
        content = data['content']
        message_type = data.get('message_type', 'text')
        metadata = data.get('metadata')
        
        if role not in ['user', 'assistant', 'system']:
            return error_response("无效的消息角色", 400)
        
        if not content.strip():
            return error_response("消息内容不能为空", 400)
        
        message = conversation.add_message(
            role=role,
            content=content,
            message_type=message_type,
            metadata=metadata
        )
        
        db.session.commit()
        
        return success_response(message.to_dict(), "添加消息成功")
    except Exception as e:
        logger.error(f"添加消息失败: {str(e)}")
        db.session.rollback()
        return error_response("添加消息失败", 500)

# ==================== 兼容性接口 ====================

@ai_assistant_bp.route('/conversation-history', methods=['GET'])
def get_conversation_history():
    """
    获取对话历史（兼容性接口）
    
    查询参数:
    - limit: 限制数量（默认20）
    - offset: 偏移量（默认0）
    """
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # 这里应该从数据库获取对话历史
    # 暂时返回模拟数据
    history = {
        'conversations': [
            {
                'id': 1,
                'user_message': '这道数学题怎么做？',
                'assistant_response': '让我来帮你分析这道题...',
                'timestamp': '2025-01-21T10:30:00Z',
                'type': 'question_analysis'
            }
        ],
        'total': 1,
        'limit': limit,
        'offset': offset
    }
    
    return success_response(history, "获取对话历史成功")

@ai_assistant_bp.route('/analyze-document', methods=['POST'])
def analyze_document():
    """
    分析PDF文档内容
    
    请求参数:
    - document_id: 文档ID
    - question: 用户问题（可选）
    """
    data = request.get_json()
    
    if not data or 'document_id' not in data:
        return error_response("缺少必要参数：document_id", 400)
    
    document_id = data['document_id']
    question = data.get('question')
    
    # 调用文档分析服务（暂时使用固定用户ID）
    result = ai_assistant_service.analyze_document_content(
        user_id="1",
        document_id=document_id,
        question=question
    )
    
    if result['success']:
        return success_response(result, "文档分析成功")
    else:
        return error_response(result.get('message', '文档分析失败'), 500)

@ai_assistant_bp.route('/search-documents', methods=['POST'])
@jwt_required()
def search_documents():
    """
    搜索PDF文档，支持红黄绿掌握度过滤
    
    请求参数:
    - query: 搜索查询
    - subject_filter: 学科过滤（可选）
    - search_tags: 是否搜索标签（可选，默认true）
    - mastery_filter: 掌握度过滤（可选：red/yellow/green）
    """
    data = request.get_json()
    
    if not data or 'query' not in data:
        return error_response("缺少必要参数：query", 400)
    
    query = data['query']
    subject_filter = data.get('subject_filter')
    search_tags = data.get('search_tags', True)
    mastery_filter = data.get('mastery_filter')
    
    if not query.strip():
        return error_response("搜索内容不能为空", 400)
    
    try:
        # 从JWT token中获取用户ID
        current_user_data = get_jwt_identity()
        user_id = current_user_data['user_id']
        
        # 调用文档搜索服务
        result = ai_assistant_service.search_documents_by_content(
            user_id=user_id,
            query=query,
            subject_filter=subject_filter,
            search_tags=search_tags,
            mastery_filter=mastery_filter
        )
        
        if result['success']:
            return success_response(result, "文档搜索成功")
        else:
            return error_response(result.get('message', '文档搜索失败'), 500)
            
    except Exception as e:
        logger.error(f"文档搜索API异常: {str(e)}")
        return error_response("文档搜索服务异常，请稍后重试", 503)

@ai_assistant_bp.route('/generate-knowledge-graph', methods=['POST'])
@jwt_required()
def generate_knowledge_graph():
    """
    生成知识图谱
    
    请求参数:
    - subject_id: 学科ID
    - content: 要保存的内容（可选）
    - tags: 标签列表（可选）
    - title: 自定义标题（可选）
    - force_overwrite: 是否强制覆盖（可选）
    """
    data = request.get_json()
    
    if not data or 'subject_id' not in data:
        return error_response("缺少必要参数：subject_id", 400)
    
    subject_id = data['subject_id']
    content = data.get('content')
    tags = data.get('tags', [])
    title = data.get('title')
    force_overwrite = data.get('force_overwrite', False)
    
    try:
        # 从JWT token中获取用户ID
        current_user_data = get_jwt_identity()
        user_id = current_user_data['user_id']
        
        # 如果有自定义内容，保存到知识图谱
        if content:
            result = ai_assistant_service.save_content_to_knowledge_graph(
                user_id=user_id,
                subject_id=subject_id,
                content=content,
                tags=tags,
                title=title,
                force_overwrite=force_overwrite
            )
        else:
            # 调用知识图谱生成服务
            result = ai_assistant_service.generate_knowledge_graph_for_user(
                user_id=user_id,
                subject_id=subject_id
            )
        
        if result['success']:
            return success_response(result, "知识图谱操作成功")
        elif result.get('duplicate_found'):
            # 返回重复检测结果，让前端处理
            return jsonify(result), 409  # 409 Conflict
        else:
            return error_response(result.get('message', '知识图谱操作失败'), 500)
            
    except Exception as e:
        logger.error(f"知识图谱API异常: {str(e)}")
        return error_response("知识图谱服务异常，请稍后重试", 503)

@ai_assistant_bp.route('/search-knowledge-graphs', methods=['POST'])
@jwt_required()
def search_knowledge_graphs():
    """
    搜索知识图谱内容
    
    请求参数:
    - query: 搜索查询
    - subject_filter: 学科过滤（可选）
    """
    data = request.get_json()
    
    if not data or 'query' not in data:
        return error_response("缺少必要参数：query", 400)
    
    query = data['query']
    subject_filter = data.get('subject_filter')
    
    try:
        # 从JWT token中获取用户ID
        current_user_data = get_jwt_identity()
        user_id = current_user_data['user_id']
        
        # 搜索知识图谱
        knowledge_graphs = ai_assistant_service._get_knowledge_graphs_data(user_id, query)
        
        # 如果有学科过滤，进一步过滤结果
        if subject_filter:
            knowledge_graphs = [
                kg for kg in knowledge_graphs 
                if kg['subject_id'] == subject_filter
            ]
        
        return success_response({
            'results': knowledge_graphs,
            'total_found': len(knowledge_graphs),
            'message': f'找到 {len(knowledge_graphs)} 个相关知识图谱',
            'timestamp': datetime.now().isoformat()
        }, "知识图谱搜索成功")
        
    except Exception as e:
        logger.error(f"知识图谱搜索失败: {str(e)}")
        return error_response("知识图谱搜索失败，请重试", 500)

@ai_assistant_bp.route('/generate-ppt', methods=['POST'])
def generate_ppt():
    """
    生成PPT
    
    请求参数:
    - content: PPT内容描述
    - template_id: 模板ID（可选）
    - user_id: 用户ID
    - tenant_id: 租户ID
    """
    data = request.get_json()
    
    if not data or 'content' not in data:
        return error_response("缺少必要参数：content", 400)
    
    try:
        content = data['content']
        template_id = data.get('template_id')
        user_id = data.get('user_id', '1')  # 默认用户ID
        tenant_id = data.get('tenant_id', 'default')  # 默认租户ID
        
        # 调用AI助理服务生成PPT
        result = ai_assistant_service.generate_ppt(
            content=content,
            template_id=template_id,
            user_id=user_id,
            tenant_id=tenant_id
        )
        
        return success_response(result, "PPT生成成功")
        
    except Exception as e:
        logger.error(f"PPT生成失败: {str(e)}")
        return error_response(f"PPT生成失败: {str(e)}", 500)

# 错误处理
@ai_assistant_bp.errorhandler(400)
def bad_request(error):
    return error_response("请求参数错误", 400)

@ai_assistant_bp.errorhandler(500)
def internal_error(error):
    return error_response("服务器内部错误", 500)