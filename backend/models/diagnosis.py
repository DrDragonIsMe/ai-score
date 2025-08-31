#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 数据模型 - diagnosis.py

Description:
    诊断数据模型，定义学习诊断结果和分析数据。

Author: Chang Xinglong
Date: 2025-08-31
Version: 1.0.0
License: Apache License 2.0
"""


from datetime import datetime
from enum import Enum
from utils.database import db
from .base import BaseModel
import uuid

class DiagnosisType(Enum):
    """诊断类型"""
    BASIC = 'basic'  # 基础诊断
    COMPREHENSIVE = 'comprehensive'  # 综合诊断
    ADAPTIVE = 'adaptive'  # 自适应诊断
    TARGETED = 'targeted'  # 针对性诊断

class DiagnosisStatus(Enum):
    """诊断状态"""
    PENDING = 'pending'  # 待开始
    IN_PROGRESS = 'in_progress'  # 进行中
    COMPLETED = 'completed'  # 已完成
    CANCELLED = 'cancelled'  # 已取消

class DiagnosisLevel(Enum):
    """诊断层级"""
    MEMORY = 'memory'  # 记忆层
    APPLICATION = 'application'  # 应用层
    TRANSFER = 'transfer'  # 迁移层

class DiagnosisReport(BaseModel):
    """诊断报告模型 - 三层诊断体系 + AI自适应出题"""
    
    __tablename__ = 'diagnosis_reports'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.String(36), db.ForeignKey('subjects.id'), nullable=False)
    knowledge_point_ids = db.Column(db.JSON, default=[], comment='涉及的知识点ID列表')
    
    # 基本信息
    name = db.Column(db.String(100), nullable=False, comment='诊断名称')
    description = db.Column(db.Text, comment='诊断描述')
    diagnosis_type = db.Column(db.Enum(DiagnosisType), default=DiagnosisType.COMPREHENSIVE, comment='诊断类型')
    target_level = db.Column(db.Enum(DiagnosisLevel), comment='目标诊断层级')
    
    # 诊断配置
    total_questions_planned = db.Column(db.Integer, default=30, comment='计划题目总数')
    time_limit = db.Column(db.Integer, comment='时间限制(分钟)')
    difficulty_range = db.Column(db.JSON, default={'min': 1, 'max': 5}, comment='难度范围')
    adaptive_enabled = db.Column(db.Boolean, default=True, comment='是否启用自适应出题')
    
    # 诊断层级
    basic_level = db.Column(db.JSON, default={}, comment='基础层(记忆)诊断结果')
    advanced_level = db.Column(db.JSON, default={}, comment='进阶层(应用)诊断结果')
    comprehensive_level = db.Column(db.JSON, default={}, comment='综合层(迁移)诊断结果')
    
    # 整体评估
    overall_score = db.Column(db.Integer, comment='总体得分')
    max_score = db.Column(db.Integer, comment='满分')
    accuracy_rate = db.Column(db.Float, comment='正确率')
    ability_estimate = db.Column(db.Float, comment='能力估计值(-3到3)')
    confidence_interval = db.Column(db.JSON, default={}, comment='能力估计置信区间')
    
    # 知识热力图数据
    heatmap_data = db.Column(db.JSON, default={}, comment='知识热力图数据')
    mastery_levels = db.Column(db.JSON, default={}, comment='各知识点掌握程度')
    weakness_points = db.Column(db.JSON, default=[], comment='薄弱点TOP5')
    strength_points = db.Column(db.JSON, default=[], comment='优势点TOP5')
    
    # AI分析结果
    ai_analysis = db.Column(db.JSON, default={}, comment='AI分析结果')
    learning_path = db.Column(db.JSON, default=[], comment='推荐学习路径')
    next_topics = db.Column(db.JSON, default=[], comment='下一步学习主题')
    recommendations = db.Column(db.JSON, default=[], comment='学习建议')
    
    # 自适应出题统计
    adaptive_adjustments = db.Column(db.Integer, default=0, comment='自适应调整次数')
    difficulty_progression = db.Column(db.JSON, default=[], comment='难度变化轨迹')
    question_selection_log = db.Column(db.JSON, default=[], comment='题目选择日志')
    
    # 诊断统计
    total_questions = db.Column(db.Integer, default=0, comment='总题目数')
    correct_questions = db.Column(db.Integer, default=0, comment='正确题目数')
    total_time = db.Column(db.Integer, comment='总用时(秒)')
    avg_time_per_question = db.Column(db.Float, comment='平均每题用时')
    
    # 状态
    status = db.Column(db.Enum(DiagnosisStatus), default=DiagnosisStatus.COMPLETED, comment='诊断状态')
    
    # 关系
    user = db.relationship('User', backref='diagnosis_reports')
    subject = db.relationship('Subject', backref='diagnosis_reports')
    weakness_points_rel = db.relationship('WeaknessPoint', backref='diagnosis_report', lazy='dynamic', cascade='all, delete-orphan')
    diagnosis_sessions = db.relationship('DiagnosisSession', backref='diagnosis_report', lazy='dynamic', cascade='all, delete-orphan')
    
    # 索引
    __table_args__ = (
        db.Index('idx_diagnosis_user_subject', 'user_id', 'subject_id'),
        db.Index('idx_diagnosis_type_status', 'diagnosis_type', 'status'),
        db.Index('idx_diagnosis_created', 'created_at'),
    )
    
    def __repr__(self):
        return f'<DiagnosisReport {self.name}>'
    
    def calculate_accuracy_rate(self):
        """计算正确率"""
        if self.total_questions == 0:
            return 0
        accuracy = round(self.correct_questions / self.total_questions * 100, 2)
        self.accuracy_rate = accuracy
        return accuracy
    
    def generate_heatmap_data(self):
        """生成知识热力图数据"""
        from models.knowledge import KnowledgePoint
        
        heatmap = {
            'knowledge_points': [],
            'mastery_scores': [],
            'difficulty_levels': [],
            'time_spent': [],
            'error_rates': []
        }
        
        # 根据mastery_levels生成热力图
        if self.mastery_levels:
            for kp_id, mastery_data in self.mastery_levels.items():
                kp = KnowledgePoint.query.get(kp_id)
                if kp:
                    heatmap['knowledge_points'].append(kp.name)
                    heatmap['mastery_scores'].append(mastery_data.get('score', 0))
                    heatmap['difficulty_levels'].append(mastery_data.get('difficulty', 3))
                    heatmap['time_spent'].append(mastery_data.get('time_spent', 0))
                    heatmap['error_rates'].append(mastery_data.get('error_rate', 0))
        
        self.heatmap_data = heatmap
        return heatmap
    
    def get_weakness_analysis(self):
        """获取薄弱点分析"""
        weakness_analysis = {
            'knowledge_gaps': [],  # 知识盲区
            'skill_deficits': [],  # 技能不足
            'common_mistakes': [], # 常见错误
            'time_management': {},  # 时间管理问题
            'difficulty_adaptation': {},  # 难度适应性
            'learning_efficiency': {}  # 学习效率
        }
        
        # 分析薄弱知识点
        if self.mastery_levels:
            for kp_id, mastery_data in self.mastery_levels.items():
                score = mastery_data.get('score', 0)
                if score < 60:  # 掌握度低于60%
                    weakness_analysis['knowledge_gaps'].append({
                        'knowledge_point_id': kp_id,
                        'mastery_score': score,
                        'error_types': mastery_data.get('error_types', []),
                        'improvement_priority': mastery_data.get('priority', 3)
                    })
        
        return weakness_analysis
    
    def update_ability_estimate(self, responses):
        """更新能力估计值（基于IRT模型）"""
        import math
        
        # 简化的IRT能力估计算法
        correct_count = sum(1 for r in responses if r.get('is_correct', False))
        total_count = len(responses)
        
        if total_count == 0:
            self.ability_estimate = 0.0
            return
        
        # 基础正确率
        accuracy = correct_count / total_count
        
        # 考虑题目难度的加权计算
        weighted_score = 0
        total_weight = 0
        
        for response in responses:
            difficulty = response.get('difficulty', 3)  # 1-5难度
            is_correct = response.get('is_correct', False)
            weight = difficulty  # 难题权重更高
            
            if is_correct:
                weighted_score += weight * difficulty
            total_weight += weight
        
        if total_weight > 0:
            # 转换为-3到3的能力值
            raw_ability = (weighted_score / total_weight - 2.5) * 1.2
            self.ability_estimate = max(-3, min(3, raw_ability))
        else:
            self.ability_estimate = 0.0
        
        # 计算置信区间
        std_error = 1.0 / math.sqrt(max(1, total_count))
        self.confidence_interval = {
            'lower': max(-3, self.ability_estimate - 1.96 * std_error),
            'upper': min(3, self.ability_estimate + 1.96 * std_error),
            'confidence_level': 0.95
        }
    
    def generate_learning_path(self):
        """生成个性化学习路径"""
        from models.knowledge import KnowledgePoint, KnowledgeRelation
        
        learning_path = []
        
        # 基于薄弱点生成学习路径
        weakness_analysis = self.get_weakness_analysis()
        knowledge_gaps = weakness_analysis.get('knowledge_gaps', [])
        
        # 按优先级排序薄弱点
        sorted_gaps = sorted(knowledge_gaps, 
                           key=lambda x: (x.get('improvement_priority', 3), -x.get('mastery_score', 0)))
        
        for gap in sorted_gaps[:5]:  # 取前5个最需要改进的知识点
            kp_id = gap['knowledge_point_id']
            kp = KnowledgePoint.query.get(kp_id)
            
            if kp:
                # 查找前置知识点
                prerequisites = KnowledgeRelation.query.filter_by(
                    target_id=kp_id,
                    relation_type='prerequisite'
                ).all()
                
                path_item = {
                    'knowledge_point_id': kp_id,
                    'knowledge_point_name': kp.name,
                    'current_mastery': gap.get('mastery_score', 0),
                    'target_mastery': 80,  # 目标掌握度
                    'estimated_time': self._estimate_learning_time(gap),
                    'prerequisites': [p.source_id for p in prerequisites],
                    'recommended_resources': self._get_recommended_resources(kp),
                    'practice_strategy': self._get_practice_strategy(gap)
                }
                learning_path.append(path_item)
        
        self.learning_path = learning_path
        return learning_path
    
    def _estimate_learning_time(self, knowledge_gap):
        """估计学习时间（小时）"""
        mastery_score = knowledge_gap.get('mastery_score', 0)
        priority = knowledge_gap.get('improvement_priority', 3)
        
        # 基础时间：根据掌握度差距
        base_time = (80 - mastery_score) * 0.1  # 每提升1%掌握度需要0.1小时
        
        # 优先级调整
        priority_multiplier = {1: 1.5, 2: 1.3, 3: 1.0, 4: 0.8, 5: 0.6}.get(priority, 1.0)
        
        return round(base_time * priority_multiplier, 1)
    
    def _get_recommended_resources(self, knowledge_point):
        """获取推荐学习资源"""
        return {
            'videos': [],  # 视频资源
            'articles': [],  # 文章资源
            'exercises': [],  # 练习题
            'examples': []  # 例题
        }
    
    def _get_practice_strategy(self, knowledge_gap):
        """获取练习策略"""
        mastery_score = knowledge_gap.get('mastery_score', 0)
        error_types = knowledge_gap.get('error_types', [])
        
        if mastery_score < 30:
            return 'foundation_building'  # 基础建设
        elif mastery_score < 60:
            return 'skill_development'  # 技能发展
        else:
            return 'mastery_refinement'  # 精熟提升
    
    def to_dict(self, include_details=False):
        data = {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'subject_id': str(self.subject_id),
            'name': self.name,
            'description': self.description,
            'diagnosis_type': self.diagnosis_type,
            'overall_score': self.overall_score,
            'max_score': self.max_score,
            'accuracy_rate': self.accuracy_rate,
            'weakness_points': self.weakness_points,
            'strength_points': self.strength_points,
            'total_questions': self.total_questions,
            'correct_questions': self.correct_questions,
            'total_time': self.total_time,
            'avg_time_per_question': self.avg_time_per_question,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_details:
            data.update({
                'basic_level': self.basic_level,
                'advanced_level': self.advanced_level,
                'comprehensive_level': self.comprehensive_level,
                'heatmap_data': self.heatmap_data,
                'ai_analysis': self.ai_analysis,
                'recommendations': self.recommendations
            })
        
        return data

class DiagnosisSession(BaseModel):
    """诊断会话模型 - 支持AI自适应出题过程"""
    
    __tablename__ = 'diagnosis_sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    diagnosis_report_id = db.Column(db.String(36), db.ForeignKey('diagnosis_reports.id'), nullable=False)
    
    # 会话信息
    session_name = db.Column(db.String(100), comment='会话名称')
    session_type = db.Column(db.Enum(DiagnosisLevel), comment='会话类型（诊断层级）')
    current_question_index = db.Column(db.Integer, default=0, comment='当前题目索引')
    total_questions = db.Column(db.Integer, default=0, comment='总题目数')
    
    # 自适应参数
    current_ability_estimate = db.Column(db.Float, default=0.0, comment='当前能力估计')
    target_precision = db.Column(db.Float, default=0.3, comment='目标精度')
    max_questions = db.Column(db.Integer, default=30, comment='最大题目数')
    min_questions = db.Column(db.Integer, default=10, comment='最小题目数')
    
    # 会话状态
    status = db.Column(db.Enum(DiagnosisStatus), default=DiagnosisStatus.PENDING, comment='会话状态')
    start_time = db.Column(db.DateTime, comment='开始时间')
    end_time = db.Column(db.DateTime, comment='结束时间')
    
    # 统计数据
    questions_answered = db.Column(db.Integer, default=0, comment='已答题数')
    correct_answers = db.Column(db.Integer, default=0, comment='正确答案数')
    total_time_spent = db.Column(db.Integer, default=0, comment='总用时（秒）')
    
    # 自适应调整记录
    difficulty_adjustments = db.Column(db.JSON, default=[], comment='难度调整记录')
    question_selection_history = db.Column(db.JSON, default=[], comment='题目选择历史')
    ability_progression = db.Column(db.JSON, default=[], comment='能力值变化轨迹')
    
    # 关系
    question_responses = db.relationship('QuestionResponse', backref='diagnosis_session', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<DiagnosisSession {self.session_name}>'
    
    def start_session(self):
        """开始诊断会话"""
        self.status = DiagnosisStatus.IN_PROGRESS
        self.start_time = datetime.utcnow()
        db.session.commit()
    
    def end_session(self):
        """结束诊断会话"""
        self.status = DiagnosisStatus.COMPLETED
        self.end_time = datetime.utcnow()
        db.session.commit()
    
    def update_ability_estimate(self, new_response):
        """基于新回答更新能力估计"""
        # 记录能力值变化
        self.ability_progression.append({
            'question_index': self.current_question_index,
            'previous_estimate': self.current_ability_estimate,
            'response_correct': new_response.get('is_correct', False),
            'question_difficulty': new_response.get('difficulty', 3),
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # 简化的能力估计更新
        if new_response.get('is_correct', False):
            self.current_ability_estimate += 0.1
            self.correct_answers += 1
        else:
            self.current_ability_estimate -= 0.1
        
        # 限制能力值范围
        self.current_ability_estimate = max(-3, min(3, self.current_ability_estimate))
        self.questions_answered += 1
        self.current_question_index += 1
    
    def should_continue(self):
        """判断是否应该继续出题"""
        # 达到最大题目数
        if self.questions_answered >= self.max_questions:
            return False
        
        # 未达到最小题目数
        if self.questions_answered < self.min_questions:
            return True
        
        # 检查精度是否满足要求
        if len(self.ability_progression) >= 5:
            recent_estimates = [p['previous_estimate'] for p in self.ability_progression[-5:]]
            variance = sum((x - self.current_ability_estimate) ** 2 for x in recent_estimates) / len(recent_estimates)
            if variance < self.target_precision:
                return False
        
        return True
    
    def get_next_difficulty(self):
        """获取下一题的建议难度"""
        # 基于当前能力估计调整难度
        base_difficulty = 3  # 中等难度
        ability_adjustment = self.current_ability_estimate * 0.5
        
        suggested_difficulty = base_difficulty + ability_adjustment
        return max(1, min(5, round(suggested_difficulty)))
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'diagnosis_report_id': str(self.diagnosis_report_id),
            'session_name': self.session_name,
            'session_type': self.session_type.value if self.session_type else None,
            'current_question_index': self.current_question_index,
            'total_questions': self.total_questions,
            'current_ability_estimate': self.current_ability_estimate,
            'status': self.status.value if self.status else None,
            'questions_answered': self.questions_answered,
            'correct_answers': self.correct_answers,
            'accuracy_rate': round(self.correct_answers / max(1, self.questions_answered) * 100, 2),
            'total_time_spent': self.total_time_spent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class QuestionResponse(BaseModel):
    """题目回答记录模型"""
    
    __tablename__ = 'question_responses'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    diagnosis_session_id = db.Column(db.String(36), db.ForeignKey('diagnosis_sessions.id'), nullable=False)
    question_id = db.Column(db.String(36), comment='题目ID')
    knowledge_point_id = db.Column(db.String(36), db.ForeignKey('knowledge_points.id'), comment='知识点ID')
    
    # 题目信息
    question_content = db.Column(db.Text, comment='题目内容')
    question_type = db.Column(db.String(20), comment='题目类型')
    difficulty_level = db.Column(db.Integer, comment='难度等级1-5')
    
    # 回答信息
    user_answer = db.Column(db.Text, comment='用户答案')
    correct_answer = db.Column(db.Text, comment='正确答案')
    is_correct = db.Column(db.Boolean, comment='是否正确')
    
    # 时间统计
    time_spent = db.Column(db.Integer, comment='答题用时（秒）')
    start_time = db.Column(db.DateTime, comment='开始答题时间')
    submit_time = db.Column(db.DateTime, comment='提交时间')
    
    # 分析数据
    confidence_level = db.Column(db.Integer, comment='答题信心1-5')
    error_type = db.Column(db.String(50), comment='错误类型')
    solution_steps = db.Column(db.JSON, default=[], comment='解题步骤')
    
    def __repr__(self):
        return f'<QuestionResponse {self.id}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'diagnosis_session_id': str(self.diagnosis_session_id),
            'question_id': str(self.question_id) if self.question_id else None,
            'knowledge_point_id': str(self.knowledge_point_id) if self.knowledge_point_id else None,
            'question_content': self.question_content,
            'question_type': self.question_type,
            'difficulty_level': self.difficulty_level,
            'user_answer': self.user_answer,
            'correct_answer': self.correct_answer,
            'is_correct': self.is_correct,
            'time_spent': self.time_spent,
            'confidence_level': self.confidence_level,
            'error_type': self.error_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class WeaknessPoint(BaseModel):
    """薄弱点模型"""
    
    __tablename__ = 'weakness_points'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    diagnosis_report_id = db.Column(db.String(36), db.ForeignKey('diagnosis_reports.id'), nullable=False)
    knowledge_point_id = db.Column(db.String(36), db.ForeignKey('knowledge_points.id'), nullable=False)
    
    # 薄弱程度
    weakness_level = db.Column(db.Integer, default=1, comment='薄弱程度1-5')
    accuracy_rate = db.Column(db.Float, comment='正确率')
    avg_time = db.Column(db.Float, comment='平均用时')
    
    # 错误分析
    error_types = db.Column(db.JSON, default=[], comment='错误类型统计')
    common_mistakes = db.Column(db.JSON, default=[], comment='常见错误')
    
    # 改进建议
    improvement_suggestions = db.Column(db.JSON, default=[], comment='改进建议')
    recommended_exercises = db.Column(db.JSON, default=[], comment='推荐练习')
    
    # 优先级
    priority = db.Column(db.Integer, default=3, comment='优先级1-5')
    estimated_improvement_time = db.Column(db.Integer, comment='预估改进时间(小时)')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<WeaknessPoint {self.knowledge_point_id}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'diagnosis_report_id': str(self.diagnosis_report_id),
            'knowledge_point_id': str(self.knowledge_point_id),
            'weakness_level': self.weakness_level,
            'accuracy_rate': self.accuracy_rate,
            'avg_time': self.avg_time,
            'error_types': self.error_types,
            'common_mistakes': self.common_mistakes,
            'improvement_suggestions': self.improvement_suggestions,
            'recommended_exercises': self.recommended_exercises,
            'priority': self.priority,
            'estimated_improvement_time': self.estimated_improvement_time
        }

class LearningProfile(BaseModel):
    """学习画像模型 - 个性化学习特征分析"""
    
    __tablename__ = 'learning_profiles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # 思维特征
    thinking_style = db.Column(db.String(20), comment='思维风格：logical/creative/analytical/intuitive')
    problem_solving_approach = db.Column(db.String(20), comment='解题方法：systematic/trial_error/pattern_recognition')
    learning_pace = db.Column(db.String(20), comment='学习节奏：fast/moderate/slow')
    
    # 答题习惯
    answer_patterns = db.Column(db.JSON, default={}, comment='答题模式分析')
    time_distribution = db.Column(db.JSON, default={}, comment='时间分配习惯')
    mistake_patterns = db.Column(db.JSON, default={}, comment='错误模式')
    
    # 遗忘周期
    forgetting_curve_params = db.Column(db.JSON, default={}, comment='遗忘曲线参数')
    memory_retention_rate = db.Column(db.Float, comment='记忆保持率')
    optimal_review_intervals = db.Column(db.JSON, default=[], comment='最佳复习间隔')
    
    # 学习偏好
    preferred_difficulty = db.Column(db.Integer, default=3, comment='偏好难度1-5')
    preferred_question_types = db.Column(db.JSON, default=[], comment='偏好题型')
    study_time_preferences = db.Column(db.JSON, default={}, comment='学习时间偏好')
    
    # 认知能力评估
    attention_span = db.Column(db.Integer, comment='注意力持续时间(分钟)')
    working_memory_capacity = db.Column(db.Integer, comment='工作记忆容量')
    processing_speed = db.Column(db.Float, comment='信息处理速度')
    
    # 情绪和动机
    motivation_level = db.Column(db.Integer, default=3, comment='学习动机1-5')
    anxiety_level = db.Column(db.Integer, default=3, comment='考试焦虑1-5')
    confidence_level = db.Column(db.Integer, default=3, comment='学习信心1-5')
    
    # 社交学习特征
    collaboration_preference = db.Column(db.Boolean, default=False, comment='是否偏好协作学习')
    peer_comparison_sensitivity = db.Column(db.Integer, default=3, comment='同伴比较敏感度1-5')
    
    # 数据统计
    total_study_sessions = db.Column(db.Integer, default=0, comment='总学习次数')
    avg_session_duration = db.Column(db.Float, comment='平均学习时长')
    consistency_score = db.Column(db.Float, comment='学习一致性得分')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<LearningProfile {self.user_id}>'
    
    def update_forgetting_curve(self, retention_data):
        """更新遗忘曲线参数"""
        # 根据用户的记忆保持数据更新遗忘曲线参数
        # 这里应该实现具体的算法
        pass
    
    def get_personalized_strategy(self):
        """获取个性化学习策略"""
        strategy = {
            'study_schedule': {},  # 学习计划
            'content_delivery': {},  # 内容呈现方式
            'assessment_approach': {},  # 评估方法
            'motivation_techniques': []  # 激励技巧
        }
        
        # 根据学习画像生成个性化策略
        if self.thinking_style == 'logical':
            strategy['content_delivery']['structure'] = 'step_by_step'
        elif self.thinking_style == 'creative':
            strategy['content_delivery']['structure'] = 'mind_map'
        
        return strategy
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'thinking_style': self.thinking_style,
            'problem_solving_approach': self.problem_solving_approach,
            'learning_pace': self.learning_pace,
            'answer_patterns': self.answer_patterns,
            'time_distribution': self.time_distribution,
            'mistake_patterns': self.mistake_patterns,
            'forgetting_curve_params': self.forgetting_curve_params,
            'memory_retention_rate': self.memory_retention_rate,
            'optimal_review_intervals': self.optimal_review_intervals,
            'preferred_difficulty': self.preferred_difficulty,
            'preferred_question_types': self.preferred_question_types,
            'study_time_preferences': self.study_time_preferences,
            'attention_span': self.attention_span,
            'working_memory_capacity': self.working_memory_capacity,
            'processing_speed': self.processing_speed,
            'motivation_level': self.motivation_level,
            'anxiety_level': self.anxiety_level,
            'confidence_level': self.confidence_level,
            'collaboration_preference': self.collaboration_preference,
            'peer_comparison_sensitivity': self.peer_comparison_sensitivity,
            'total_study_sessions': self.total_study_sessions,
            'avg_session_duration': self.avg_session_duration,
            'consistency_score': self.consistency_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }