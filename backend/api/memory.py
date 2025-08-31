#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - API接口 - memory.py

Description:
    记忆数据模型，定义记忆强化相关数据结构。

Author: Chang Xinglong
Date: 2025-01-20
Version: 1.0.0
License: Apache License 2.0
"""


from datetime import datetime, timedelta
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import joinedload

from . import api_bp
from models.learning import MemoryCard
from models.knowledge import KnowledgePoint
from models.question import Question
from services.memory_service import MemoryService
from utils.database import db
from utils.response import success_response, error_response
from utils.validators import validate_required_fields
import uuid

# 临时模型定义（应该移到models目录下）
class MemorySession(db.Model):
    """记忆会话模型"""
    __tablename__ = 'memory_sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    session_type = db.Column(db.String(20), default='regular')
    target_count = db.Column(db.Integer, default=10)
    completed_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    total_duration = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'session_type': self.session_type,
            'target_count': self.target_count,
            'completed_count': self.completed_count,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_duration': self.total_duration,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class MemoryReminder(db.Model):
    """记忆提醒模型"""
    __tablename__ = 'memory_reminders'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    card_id = db.Column(db.String(36), db.ForeignKey('memory_cards.id'))
    reminder_type = db.Column(db.String(20), default='daily')
    reminder_time = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'card_id': str(self.card_id) if self.card_id else None,
            'reminder_type': self.reminder_type,
            'reminder_time': self.reminder_time.isoformat() if self.reminder_time else None,
            'is_active': self.is_active,
            'message': self.message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# 初始化记忆服务
memory_service = MemoryService()

@api_bp.route('/memory/cards', methods=['POST'])
@jwt_required()
def create_memory_card():
    """
    创建记忆卡片
    
    请求参数:
    - knowledge_point_id: 知识点ID
    - content_type: 内容类型 (concept/question/formula/example)
    - question_id: 题目ID (可选，当content_type为question时必需)
    - tags: 标签列表 (可选)
    - difficulty_level: 难度等级 1-5 (可选，默认3)
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['knowledge_point_id', 'content_type']
        if not validate_required_fields(data, required_fields):
            return error_response('缺少必需字段', 400)
        
        # 验证内容类型
        valid_types = ['concept', 'question', 'formula', 'example']
        if data['content_type'] not in valid_types:
            return error_response('无效的内容类型', 400)
        
        # 如果是题目类型，验证question_id
        if data['content_type'] == 'question' and not data.get('question_id'):
            return error_response('题目类型卡片需要提供question_id', 400)
        
        # 创建记忆卡片
        card = memory_service.create_memory_card(
            user_id=user_id,
            knowledge_point_id=data['knowledge_point_id'],
            question_id=data.get('question_id'),
            content_type=data['content_type'],
            custom_content=data.get('custom_content')
        )
        
        if not card:
            return error_response('创建记忆卡片失败', 500)
        
        return success_response(card.to_dict(), '记忆卡片创建成功')
        
    except Exception as e:
        current_app.logger.error(f"创建记忆卡片失败: {str(e)}")
        return error_response('创建记忆卡片失败', 500)

@api_bp.route('/memory/cards/batch', methods=['POST'])
@jwt_required()
def batch_create_memory_cards():
    """
    批量创建记忆卡片
    
    请求参数:
    - cards: 卡片列表，每个卡片包含knowledge_point_id, content_type等字段
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('cards') or not isinstance(data['cards'], list):
            return error_response('请提供有效的卡片列表', 400)
        
        # 批量创建卡片
        knowledge_point_ids = [card['knowledge_point_id'] for card in data['cards']]
        content_types = [card.get('content_type', 'concept') for card in data['cards']]
        
        results = memory_service.batch_create_cards(
            user_id=user_id,
            knowledge_point_ids=knowledge_point_ids,
            content_types=content_types
        )
        
        return success_response({
            'total_requested': len(data['cards']),
            'created_count': len(results) if results else 0,
            'created_cards': [card.to_dict() for card in results] if results else []
        }, '批量创建记忆卡片完成')
        
    except Exception as e:
        current_app.logger.error(f"批量创建记忆卡片失败: {str(e)}")
        return error_response('批量创建记忆卡片失败', 500)

@api_bp.route('/memory/cards/due', methods=['GET'])
@jwt_required()
def get_due_cards():
    """
    获取需要复习的卡片
    
    查询参数:
    - limit: 返回数量限制 (默认10)
    - subject_id: 学科ID (可选)
    - difficulty_range: 难度范围 "min,max" (可选)
    - content_types: 内容类型列表，逗号分隔 (可选)
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取查询参数
        limit = request.args.get('limit', 10, type=int)
        subject_id = request.args.get('subject_id', type=int)
        difficulty_range = request.args.get('difficulty_range')
        content_types = request.args.get('content_types')
        
        # 解析难度范围
        min_difficulty, max_difficulty = None, None
        if difficulty_range:
            try:
                min_diff, max_diff = map(int, difficulty_range.split(','))
                min_difficulty, max_difficulty = min_diff, max_diff
            except ValueError:
                return error_response('无效的难度范围格式', 400)
        
        # 解析内容类型
        content_type_list = None
        if content_types:
            content_type_list = [t.strip() for t in content_types.split(',')]
        
        # 获取到期卡片
        cards = memory_service.get_due_cards(
            user_id=user_id,
            limit=limit
        )
        
        return success_response({
            'cards': [card.to_dict() for card in cards],
            'total_count': len(cards)
        }, '获取到期卡片成功')
        
    except Exception as e:
        current_app.logger.error(f"获取到期卡片失败: {str(e)}")
        return error_response('获取到期卡片失败', 500)

@api_bp.route('/memory/cards/<int:card_id>/review', methods=['POST'])
@jwt_required()
def review_card(card_id):
    """
    复习卡片
    
    请求参数:
    - performance: 表现评级 (again/poor/fair/good/excellent)
    - response_time: 响应时间（秒，可选）
    - user_feedback: 用户反馈（可选）
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证必需字段
        if not data.get('performance'):
            return error_response('缺少表现评级', 400)
        
        # 验证表现评级
        valid_performances = ['again', 'poor', 'fair', 'good', 'excellent']
        if data['performance'] not in valid_performances:
            return error_response('无效的表现评级', 400)
        
        # 复习卡片
        success = memory_service.review_card(
            card_id=card_id,
            user_id=user_id,
            performance=data['performance'],
            response_time=data.get('response_time'),
            user_feedback=data.get('user_feedback')
        )
        
        if not success:
            return error_response('复习卡片失败，卡片不存在或无权限', 404)
        
        # 获取更新后的卡片信息
        updated_card = MemoryCard.query.get(card_id)
        if not updated_card:
            return error_response('卡片不存在', 404)
        
        return success_response({
            'card': updated_card.to_dict(),
            'performance': data['performance'],
            'response_time': data.get('response_time')
        }, '复习完成')
        
    except Exception as e:
        current_app.logger.error(f"复习卡片失败: {str(e)}")
        return error_response('复习卡片失败', 500)

@api_bp.route('/memory/cards', methods=['GET'])
@jwt_required()
def get_memory_cards():
    """
    获取用户的记忆卡片列表
    
    查询参数:
    - page: 页码 (默认1)
    - per_page: 每页数量 (默认20)
    - subject_id: 学科ID (可选)
    - content_type: 内容类型 (可选)
    - status: 状态筛选 (active/inactive/mastered/due/due_soon/scheduled)
    - search: 搜索关键词 (可选)
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        subject_id = request.args.get('subject_id', type=int)
        content_type = request.args.get('content_type')
        status = request.args.get('status')
        search = request.args.get('search')
        
        # 构建查询
        query = MemoryCard.query.filter_by(user_id=user_id)
        
        # 添加关联查询以优化性能
        query = query.options(
            joinedload(MemoryCard.knowledge_point),
            joinedload(MemoryCard.question)
        )
        
        # 学科筛选
        if subject_id:
            query = query.join(KnowledgePoint).filter(
                KnowledgePoint.subject_id == subject_id
            )
        
        # 内容类型筛选
        if content_type:
            query = query.filter(MemoryCard.content_type == content_type)
        
        # 状态筛选
        now = datetime.utcnow()
        if status == 'active':
            query = query.filter(MemoryCard.is_active == True)
        elif status == 'inactive':
            query = query.filter(MemoryCard.is_active == False)
        elif status == 'mastered':
            query = query.filter(MemoryCard.is_mastered == True)
        elif status == 'due':
            query = query.filter(
                and_(
                    MemoryCard.is_active == True,
                    MemoryCard.is_mastered == False,
                    MemoryCard.next_review_time <= now
                )
            )
        elif status == 'due_soon':
            tomorrow = now + timedelta(days=1)
            query = query.filter(
                and_(
                    MemoryCard.is_active == True,
                    MemoryCard.is_mastered == False,
                    MemoryCard.next_review_time <= tomorrow,
                    MemoryCard.next_review_time > now
                )
            )
        elif status == 'scheduled':
            query = query.filter(
                and_(
                    MemoryCard.is_active == True,
                    MemoryCard.is_mastered == False,
                    MemoryCard.next_review_time > now
                )
            )
        
        # 搜索功能
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    MemoryCard.front_content.ilike(search_pattern),
                    MemoryCard.back_content.ilike(search_pattern)
                )
            )
        
        # 排序
        query = query.order_by(
            MemoryCard.next_review_time.asc(),
            MemoryCard.memory_strength.asc()
        )
        
        # 分页
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        cards = pagination.items
        
        return success_response({
            'cards': [card.to_dict() for card in cards],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        }, '获取记忆卡片成功')
        
    except Exception as e:
        current_app.logger.error(f"获取记忆卡片失败: {str(e)}")
        return error_response('获取记忆卡片失败', 500)

@api_bp.route('/memory/cards/<int:card_id>', methods=['GET'])
@jwt_required()
def get_memory_card(card_id):
    """
    获取单个记忆卡片详情
    """
    try:
        user_id = get_jwt_identity()
        
        card = MemoryCard.query.filter_by(
            id=card_id, user_id=user_id
        ).options(
            joinedload(MemoryCard.knowledge_point),
            joinedload(MemoryCard.question),
            joinedload(MemoryCard.review_records)
        ).first()
        
        if not card:
            return error_response('记忆卡片不存在', 404)
        
        # 获取复习记录（暂时返回空列表，等待ReviewRecord模型实现）
        review_records = []
        
        card_data = card.to_dict()
        card_data['recent_reviews'] = [record.to_dict() for record in review_records]
        card_data['review_status'] = card.get_review_status()
        card_data['memory_level'] = card.get_memory_level()
        
        return success_response(card_data, '获取记忆卡片详情成功')
        
    except Exception as e:
        current_app.logger.error(f"获取记忆卡片详情失败: {str(e)}")
        return error_response('获取记忆卡片详情失败', 500)

@api_bp.route('/memory/cards/<int:card_id>', methods=['PUT'])
@jwt_required()
def update_memory_card(card_id):
    """
    更新记忆卡片
    
    请求参数:
    - front_content: 正面内容 (可选)
    - back_content: 背面内容 (可选)
    - tags: 标签列表 (可选)
    - difficulty_level: 难度等级 (可选)
    - is_active: 是否活跃 (可选)
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        card = MemoryCard.query.filter_by(
            id=card_id, user_id=user_id
        ).first()
        
        if not card:
            return error_response('记忆卡片不存在', 404)
        
        # 更新字段
        if 'front_content' in data:
            card.front_content = data['front_content']
        if 'back_content' in data:
            card.back_content = data['back_content']
        if 'tags' in data:
            card.tags = data['tags']
        if 'difficulty_level' in data:
            if 1 <= data['difficulty_level'] <= 5:
                card.difficulty_level = data['difficulty_level']
            else:
                return error_response('难度等级必须在1-5之间', 400)
        if 'is_active' in data:
            card.is_active = bool(data['is_active'])
        
        card.updated_time = datetime.utcnow()
        db.session.commit()
        
        return success_response(card.to_dict(), '记忆卡片更新成功')
        
    except Exception as e:
        current_app.logger.error(f"更新记忆卡片失败: {str(e)}")
        db.session.rollback()
        return error_response('更新记忆卡片失败', 500)

@api_bp.route('/memory/cards/<int:card_id>', methods=['DELETE'])
@jwt_required()
def delete_memory_card(card_id):
    """
    删除记忆卡片
    """
    try:
        user_id = get_jwt_identity()
        
        card = MemoryCard.query.filter_by(
            id=card_id, user_id=user_id
        ).first()
        
        if not card:
            return error_response('记忆卡片不存在', 404)
        
        db.session.delete(card)
        db.session.commit()
        
        return success_response(None, '记忆卡片删除成功')
        
    except Exception as e:
        current_app.logger.error(f"删除记忆卡片失败: {str(e)}")
        db.session.rollback()
        return error_response('删除记忆卡片失败', 500)

@api_bp.route('/memory/statistics', methods=['GET'])
@jwt_required()
def get_memory_statistics():
    """
    获取记忆统计信息
    
    查询参数:
    - days: 统计天数 (默认30)
    - subject_id: 学科ID (可选)
    """
    try:
        user_id = get_jwt_identity()
        days = request.args.get('days', 30, type=int)
        subject_id = request.args.get('subject_id', type=int)
        
        # 获取统计信息
        stats = memory_service.get_review_statistics(
            user_id=user_id,
            days=days
        )
        
        return success_response(stats, '获取记忆统计成功')
        
    except Exception as e:
        current_app.logger.error(f"获取记忆统计失败: {str(e)}")
        return error_response('获取记忆统计失败', 500)

@api_bp.route('/memory/recommendations', methods=['GET'])
@jwt_required()
def get_memory_recommendations():
    """
    获取个性化记忆建议
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取个性化建议
        recommendations = memory_service.get_personalized_recommendations(user_id)
        
        return success_response(recommendations, '获取记忆建议成功')
        
    except Exception as e:
        current_app.logger.error(f"获取记忆建议失败: {str(e)}")
        return error_response('获取记忆建议失败', 500)

@api_bp.route('/memory/sessions', methods=['POST'])
@jwt_required()
def start_memory_session():
    """
    开始记忆会话
    
    请求参数:
    - session_type: 会话类型 (regular/intensive/review)
    - target_count: 目标复习数量 (默认10)
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        session_type = data.get('session_type', 'regular')
        target_count = data.get('target_count', 10)
        
        # 验证会话类型
        valid_types = ['regular', 'intensive', 'review']
        if session_type not in valid_types:
            return error_response('无效的会话类型', 400)
        
        # 创建记忆会话
        session = MemorySession(
            user_id=user_id,
            session_type=session_type,
            target_count=target_count
        )
        
        db.session.add(session)
        db.session.commit()
        
        return success_response(session.to_dict(), '记忆会话开始成功')
        
    except Exception as e:
        current_app.logger.error(f"开始记忆会话失败: {str(e)}")
        db.session.rollback()
        return error_response('开始记忆会话失败', 500)

@api_bp.route('/memory/sessions/<int:session_id>/complete', methods=['POST'])
@jwt_required()
def complete_memory_session(session_id):
    """
    完成记忆会话
    """
    try:
        user_id = get_jwt_identity()
        
        session = MemorySession.query.filter_by(
            id=session_id, user_id=user_id
        ).first()
        
        if not session:
            return error_response('记忆会话不存在', 404)
        
        if session.status != 'active':
            return error_response('会话已结束', 400)
        
        # 更新会话状态
        session.status = 'completed'
        session.end_time = datetime.utcnow()
        
        if session.start_time:
            duration = session.end_time - session.start_time
            session.total_duration = int(duration.total_seconds())
        
        db.session.commit()
        
        return success_response(session.to_dict(), '记忆会话完成')
        
    except Exception as e:
        current_app.logger.error(f"完成记忆会话失败: {str(e)}")
        db.session.rollback()
        return error_response('完成记忆会话失败', 500)

@api_bp.route('/memory/reminders', methods=['GET'])
@jwt_required()
def get_memory_reminders():
    """
    获取记忆提醒设置
    """
    try:
        user_id = get_jwt_identity()
        
        reminders = MemoryReminder.query.filter_by(user_id=user_id).all()
        
        return success_response({
            'reminders': [reminder.to_dict() for reminder in reminders]
        }, '获取记忆提醒设置成功')
        
    except Exception as e:
        current_app.logger.error(f"获取记忆提醒设置失败: {str(e)}")
        return error_response('获取记忆提醒设置失败', 500)

@api_bp.route('/memory/reminders', methods=['POST'])
@jwt_required()
def create_memory_reminder():
    """
    创建记忆提醒
    
    请求参数:
    - reminder_type: 提醒类型 (daily/due_cards/weekly_summary)
    - reminder_time: 提醒时间 HH:MM
    - timezone: 时区 (可选，默认UTC)
    - delivery_channels: 发送渠道设置
    - content_settings: 内容设置
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证必需字段
        if not data.get('reminder_type'):
            return error_response('缺少提醒类型', 400)
        
        # 验证提醒类型
        valid_types = ['daily', 'due_cards', 'weekly_summary']
        if data['reminder_type'] not in valid_types:
            return error_response('无效的提醒类型', 400)
        
        # 创建提醒
        reminder = MemoryReminder(
            user_id=user_id,
            reminder_type=data['reminder_type'],
            reminder_time=data.get('reminder_time'),
            timezone=data.get('timezone', 'UTC')
        )
        
        # 设置发送渠道
        channels = data.get('delivery_channels', {})
        reminder.send_email = channels.get('email', False)
        reminder.send_push = channels.get('push', True)
        reminder.send_sms = channels.get('sms', False)
        
        # 设置内容选项
        content = data.get('content_settings', {})
        reminder.include_due_count = content.get('include_due_count', True)
        reminder.include_weak_areas = content.get('include_weak_areas', True)
        reminder.include_progress_summary = content.get('include_progress_summary', False)
        
        db.session.add(reminder)
        db.session.commit()
        
        return success_response(reminder.to_dict(), '记忆提醒创建成功')
        
    except Exception as e:
        current_app.logger.error(f"创建记忆提醒失败: {str(e)}")
        db.session.rollback()
        return error_response('创建记忆提醒失败', 500)

@api_bp.route('/memory/reminders/<int:reminder_id>', methods=['PUT'])
@jwt_required()
def update_memory_reminder(reminder_id):
    """
    更新记忆提醒设置
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        reminder = MemoryReminder.query.filter_by(
            id=reminder_id, user_id=user_id
        ).first()
        
        if not reminder:
            return error_response('记忆提醒不存在', 404)
        
        # 更新字段
        if 'is_enabled' in data:
            reminder.is_enabled = bool(data['is_enabled'])
        if 'reminder_time' in data:
            reminder.reminder_time = data['reminder_time']
        if 'timezone' in data:
            reminder.timezone = data['timezone']
        
        # 更新发送渠道
        if 'delivery_channels' in data:
            channels = data['delivery_channels']
            reminder.send_email = channels.get('email', reminder.send_email)
            reminder.send_push = channels.get('push', reminder.send_push)
            reminder.send_sms = channels.get('sms', reminder.send_sms)
        
        # 更新内容设置
        if 'content_settings' in data:
            content = data['content_settings']
            reminder.include_due_count = content.get('include_due_count', reminder.include_due_count)
            reminder.include_weak_areas = content.get('include_weak_areas', reminder.include_weak_areas)
            reminder.include_progress_summary = content.get('include_progress_summary', reminder.include_progress_summary)
        
        reminder.updated_time = datetime.utcnow()
        db.session.commit()
        
        return success_response(reminder.to_dict(), '记忆提醒更新成功')
        
    except Exception as e:
        current_app.logger.error(f"更新记忆提醒失败: {str(e)}")
        db.session.rollback()
        return error_response('更新记忆提醒失败', 500)

@api_bp.route('/memory/reminders/<int:reminder_id>', methods=['DELETE'])
@jwt_required()
def delete_memory_reminder(reminder_id):
    """
    删除记忆提醒
    """
    try:
        user_id = get_jwt_identity()
        
        reminder = MemoryReminder.query.filter_by(
            id=reminder_id, user_id=user_id
        ).first()
        
        if not reminder:
            return error_response('记忆提醒不存在', 404)
        
        db.session.delete(reminder)
        db.session.commit()
        
        return success_response(None, '记忆提醒删除成功')
        
    except Exception as e:
        current_app.logger.error(f"删除记忆提醒失败: {str(e)}")
        db.session.rollback()
        return error_response('删除记忆提醒失败', 500)