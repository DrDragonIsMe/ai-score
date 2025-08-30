# -*- coding: utf-8 -*-
"""
数据库模型
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