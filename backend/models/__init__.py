#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 数据模型 - __init__.py

Description:
    models模块初始化文件，定义模块导出接口和初始化逻辑。

Author: Chang Xinglong
Date: 2025-08-30
Version: 1.0.0
License: Apache License 2.0
"""


from .tenant import Tenant
from .user import User, UserProfile
from .knowledge import Subject, Chapter, KnowledgePoint, SubKnowledgePoint
from .question import Question, QuestionType, ExamPaper
from .learning import LearningPath, StudyRecord, MemoryCard
from .diagnosis import DiagnosisReport, WeaknessPoint, LearningProfile
from .ai_model import AIModelConfig
from .mistake import MistakeRecord, TutoringSession
from .exam import ExamSession, TimeAllocation, ScoringStrategy, ExamAnalytics
from .tracking import LearningMetric, PerformanceSnapshot, LearningReport, GoalTracking, FeedbackRecord

__all__ = [
    'Tenant', 'User', 'UserProfile',
    'Subject', 'Chapter', 'KnowledgePoint', 'SubKnowledgePoint',
    'Question', 'QuestionType', 'ExamPaper',
    'LearningPath', 'StudyRecord', 'MemoryCard',
    'DiagnosisReport', 'WeaknessPoint', 'LearningProfile',
    'AIModelConfig',
    'MistakeRecord', 'TutoringSession',
    'ExamSession', 'TimeAllocation', 'ScoringStrategy', 'ExamAnalytics',
    'LearningMetric', 'PerformanceSnapshot', 'LearningReport', 'GoalTracking', 'FeedbackRecord'
]