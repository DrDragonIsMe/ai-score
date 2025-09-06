#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 数据库迁移 - create_conversations_tables.py

Description:
    创建会话管理相关的数据库表

Author: Chang Xinglong
Date: 2025-01-11
Version: 1.0.0
License: Apache License 2.0
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import db
from models.conversation import Conversation, ConversationMessage
from app import create_app

def create_conversations_tables():
    """创建会话相关表"""
    app = create_app()
    with app.app_context():
        try:
            # 创建conversations表
            db.create_all()
            print("✅ 会话管理表创建成功")
            print("- conversations 表")
            print("- conversation_messages 表")
            
        except Exception as e:
            print(f"❌ 创建表失败: {e}")
            return False
    
    return True

if __name__ == '__main__':
    print("开始创建会话管理相关表...")
    success = create_conversations_tables()
    if success:
        print("\n🎉 数据库迁移完成！")
    else:
        print("\n💥 数据库迁移失败！")
        sys.exit(1)