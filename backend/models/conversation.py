#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 数据模型 - conversation.py

Description:
    AI助理会话数据模型，用于存储和管理用户与AI的对话历史。

Author: Chang Xinglong
Date: 2025-01-11
Version: 1.0.0
License: Apache License 2.0
"""

from datetime import datetime
from utils.database import db
import json
import uuid


class Conversation(db.Model):
    """AI助理会话模型"""
    
    __tablename__ = 'conversations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    
    # 基本信息
    title = db.Column(db.String(200), nullable=False, default='新对话', comment='会话标题')
    
    # 会话状态
    starred = db.Column(db.Boolean, default=False, nullable=False, comment='是否收藏')
    archived = db.Column(db.Boolean, default=False, nullable=False, comment='是否归档')
    
    # 消息统计
    message_count = db.Column(db.Integer, default=0, nullable=False, comment='消息数量')
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow, comment='最后消息时间')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关联消息
    messages = db.relationship('ConversationMessage', backref='conversation', cascade='all, delete-orphan', lazy='dynamic')
    
    def __repr__(self):
        return f'<Conversation {self.title}>'
    
    def add_message(self, role, content, message_type='text', metadata=None):
        """添加消息到会话"""
        message = ConversationMessage(
            conversation_id=self.id,
            role=role,
            message_type=message_type,
            content=content,
            metadata=json.dumps(metadata or {})
        )
        
        db.session.add(message)
        self.message_count = self.messages.count() + 1
        self.last_message_at = datetime.utcnow()
        
        # 如果是第一条用户消息，自动生成标题
        if role == 'user' and self.message_count == 1:
            self.title = self._generate_title_from_content(content)
        
        return message
    
    def toggle_star(self):
        """切换收藏状态"""
        self.starred = not self.starred
        return self.starred
    
    def update_title(self, new_title):
        """更新会话标题"""
        if new_title and new_title.strip():
            self.title = new_title.strip()[:200]
            return True
        return False
    
    def archive(self):
        """归档会话"""
        self.archived = True
    
    def unarchive(self):
        """取消归档"""
        self.archived = False
    
    def get_messages(self):
        """获取会话的所有消息"""
        return [msg.to_dict() for msg in self.messages.order_by(ConversationMessage.created_at)]  # type: ignore
    
    def _generate_title_from_content(self, content):
        """从内容生成标题"""
        title = content.strip()[:50]
        if len(content) > 50:
            title += '...'
        return title or '新对话'
    
    @classmethod
    def get_user_conversations(cls, user_id, page=1, per_page=20, starred_only=False, include_archived=False):
        """获取用户的会话列表"""
        query = cls.query.filter_by(user_id=user_id)
        
        if not include_archived:
            query = query.filter_by(archived=False)
        
        if starred_only:
            query = query.filter_by(starred=True)
        
        query = query.order_by(cls.last_message_at.desc())  # type: ignore
        
        total = query.count()
        conversations = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return {
            'conversations': [conv.to_dict() for conv in conversations],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }
    
    @classmethod
    def search_conversations(cls, user_id, keyword, page=1, per_page=20):
        """搜索用户的会话"""
        query = cls.query.filter(
            cls.user_id == user_id,
            cls.archived == False,
            cls.title.like(f'%{keyword}%')  # type: ignore
        ).order_by(cls.last_message_at.desc())  # type: ignore
        
        total = query.count()
        conversations = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return {
            'conversations': [conv.to_dict() for conv in conversations],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page,
            'keyword': keyword
        }
    
    def to_dict(self, include_messages=False):
        """转换为字典"""
        result = {
            'id': str(self.id),
            'title': self.title,
            'user_id': str(self.user_id),
            'starred': self.starred,
            'archived': self.archived,
            'message_count': self.message_count,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_messages:
            result['messages'] = self.get_messages()
        
        return result


class ConversationMessage(db.Model):
    """会话消息模型"""
    
    __tablename__ = 'conversation_messages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = db.Column(db.String(36), db.ForeignKey('conversations.id'), nullable=False, index=True)
    
    # 消息信息
    role = db.Column(db.String(20), nullable=False, comment='消息角色：user/assistant/system')
    message_type = db.Column(db.String(20), default='text', comment='消息类型：text/image/file')
    content = db.Column(db.Text, nullable=False, comment='消息内容')
    
    # 消息元数据
    message_metadata = db.Column(db.Text, comment='JSON格式存储额外信息')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<ConversationMessage {self.role}: {self.content[:50]}>'
    
    def get_metadata(self):
        """获取元数据"""
        if self.message_metadata:
            try:
                return json.loads(self.message_metadata)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_metadata(self, metadata):
        """设置元数据"""
        self.message_metadata = json.dumps(metadata)
    
    def to_dict(self):
        """转换为字典"""
        result = {
            'id': str(self.id),
            'conversation_id': str(self.conversation_id),
            'role': self.role,
            'message_type': self.message_type,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        result['metadata'] = self.get_metadata()
        return result