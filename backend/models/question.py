# -*- coding: utf-8 -*-
"""
题目和试卷模型
"""

from datetime import datetime
from utils.database import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class QuestionType(db.Model):
    """题型模型"""
    
    __tablename__ = 'question_types'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tenants.id'), nullable=False)
    
    # 基本信息
    code = db.Column(db.String(20), nullable=False, comment='题型代码')
    name = db.Column(db.String(50), nullable=False, comment='题型名称')
    description = db.Column(db.Text, comment='题型描述')
    
    # 题型属性
    category = db.Column(db.String(20), comment='题型类别：choice/fill/essay/calculation')
    scoring_method = db.Column(db.String(20), default='standard', comment='评分方式')
    time_limit = db.Column(db.Integer, comment='建议答题时间(秒)')
    
    # 答题模板
    answer_template = db.Column(db.JSON, default={}, comment='答题模板')
    solution_steps = db.Column(db.JSON, default=[], comment='解题步骤模板')
    
    # 状态
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    questions = db.relationship('Question', backref='question_type', lazy='dynamic')
    
    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'code', name='uq_tenant_question_type_code'),
    )
    
    def __repr__(self):
        return f'<QuestionType {self.name}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'scoring_method': self.scoring_method,
            'time_limit': self.time_limit,
            'answer_template': self.answer_template,
            'solution_steps': self.solution_steps,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'question_count': self.questions.count()
        }

class Question(db.Model):
    """题目模型 - 支持三维分类（知识点×题型×分值）"""
    
    __tablename__ = 'questions'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tenants.id'), nullable=False)
    knowledge_point_id = db.Column(UUID(as_uuid=True), db.ForeignKey('knowledge_points.id'), nullable=False)
    question_type_id = db.Column(UUID(as_uuid=True), db.ForeignKey('question_types.id'), nullable=False)
    
    # 基本信息
    title = db.Column(db.Text, nullable=False, comment='题目标题')
    content = db.Column(db.Text, nullable=False, comment='题目内容')
    options = db.Column(db.JSON, default=[], comment='选项（选择题）')
    
    # 答案和解析
    answer = db.Column(db.Text, nullable=False, comment='标准答案')
    solution = db.Column(db.Text, comment='详细解析')
    solution_steps = db.Column(db.JSON, default=[], comment='解题步骤')
    key_points = db.Column(db.JSON, default=[], comment='关键要点')
    
    # 题目属性
    difficulty = db.Column(db.Integer, default=3, comment='难度等级1-5')
    score = db.Column(db.Integer, default=5, comment='分值')
    estimated_time = db.Column(db.Integer, comment='预估答题时间(秒)')
    
    # 来源信息
    source = db.Column(db.String(100), comment='题目来源')
    year = db.Column(db.Integer, comment='年份')
    region = db.Column(db.String(50), comment='地区')
    exam_type = db.Column(db.String(50), comment='考试类型：高考/模拟/练习')
    
    # 统计信息
    attempt_count = db.Column(db.Integer, default=0, comment='尝试次数')
    correct_count = db.Column(db.Integer, default=0, comment='正确次数')
    avg_time = db.Column(db.Float, comment='平均答题时间')
    
    # 标签和分类
    tags = db.Column(db.JSON, default=[], comment='标签')
    keywords = db.Column(db.JSON, default=[], comment='关键词')
    related_questions = db.Column(db.JSON, default=[], comment='相关题目ID')
    
    # 状态
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False, comment='是否已审核')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    study_records = db.relationship('StudyRecord', backref='question', lazy='dynamic')
    
    def __repr__(self):
        return f'<Question {self.id}>'
    
    def get_accuracy_rate(self):
        """计算正确率"""
        if self.attempt_count == 0:
            return 0
        return round(self.correct_count / self.attempt_count * 100, 2)
    
    def update_stats(self, is_correct, time_spent):
        """更新统计信息"""
        self.attempt_count += 1
        if is_correct:
            self.correct_count += 1
        
        # 更新平均时间
        if self.avg_time:
            self.avg_time = (self.avg_time * (self.attempt_count - 1) + time_spent) / self.attempt_count
        else:
            self.avg_time = time_spent
        
        db.session.commit()
    
    def get_related_questions(self):
        """获取相关题目"""
        if not self.related_questions:
            return []
        return Question.query.filter(Question.id.in_(self.related_questions)).all()
    
    def to_dict(self, include_answer=False):
        data = {
            'id': str(self.id),
            'knowledge_point_id': str(self.knowledge_point_id),
            'question_type_id': str(self.question_type_id),
            'title': self.title,
            'content': self.content,
            'options': self.options,
            'difficulty': self.difficulty,
            'score': self.score,
            'estimated_time': self.estimated_time,
            'source': self.source,
            'year': self.year,
            'region': self.region,
            'exam_type': self.exam_type,
            'attempt_count': self.attempt_count,
            'correct_count': self.correct_count,
            'accuracy_rate': self.get_accuracy_rate(),
            'avg_time': self.avg_time,
            'tags': self.tags,
            'keywords': self.keywords,
            'related_questions': self.related_questions,
            'is_active': self.is_active,
            'is_verified': self.is_verified
        }
        
        if include_answer:
            data.update({
                'answer': self.answer,
                'solution': self.solution,
                'solution_steps': self.solution_steps,
                'key_points': self.key_points
            })
        
        return data

class ExamPaper(db.Model):
    """试卷模型"""
    
    __tablename__ = 'exam_papers'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tenants.id'), nullable=False)
    
    # 基本信息
    name = db.Column(db.String(100), nullable=False, comment='试卷名称')
    description = db.Column(db.Text, comment='试卷描述')
    subject_id = db.Column(UUID(as_uuid=True), db.ForeignKey('subjects.id'), nullable=False)
    
    # 试卷属性
    total_score = db.Column(db.Integer, default=150, comment='总分')
    time_limit = db.Column(db.Integer, comment='考试时间(分钟)')
    difficulty = db.Column(db.Integer, default=3, comment='整体难度1-5')
    
    # 题目配置
    question_config = db.Column(db.JSON, default={}, comment='题目配置')
    questions = db.Column(db.JSON, default=[], comment='题目ID列表')
    
    # 来源信息
    source = db.Column(db.String(100), comment='试卷来源')
    year = db.Column(db.Integer, comment='年份')
    region = db.Column(db.String(50), comment='地区')
    exam_type = db.Column(db.String(50), comment='考试类型')
    
    # 统计信息
    attempt_count = db.Column(db.Integer, default=0, comment='尝试次数')
    avg_score = db.Column(db.Float, comment='平均分')
    avg_time = db.Column(db.Float, comment='平均用时')
    
    # 状态
    is_active = db.Column(db.Boolean, default=True)
    is_public = db.Column(db.Boolean, default=False, comment='是否公开')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    subject = db.relationship('Subject', backref='exam_papers')
    
    def __repr__(self):
        return f'<ExamPaper {self.name}>'
    
    def get_questions(self):
        """获取试卷题目"""
        if not self.questions:
            return []
        return Question.query.filter(Question.id.in_(self.questions)).all()
    
    def calculate_total_score(self):
        """计算试卷总分"""
        questions = self.get_questions()
        return sum(q.score for q in questions)
    
    def update_stats(self, score, time_spent):
        """更新统计信息"""
        self.attempt_count += 1
        
        # 更新平均分
        if self.avg_score:
            self.avg_score = (self.avg_score * (self.attempt_count - 1) + score) / self.attempt_count
        else:
            self.avg_score = score
        
        # 更新平均时间
        if self.avg_time:
            self.avg_time = (self.avg_time * (self.attempt_count - 1) + time_spent) / self.attempt_count
        else:
            self.avg_time = time_spent
        
        db.session.commit()
    
    def to_dict(self, include_questions=False):
        data = {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'subject_id': str(self.subject_id),
            'total_score': self.total_score,
            'time_limit': self.time_limit,
            'difficulty': self.difficulty,
            'question_config': self.question_config,
            'source': self.source,
            'year': self.year,
            'region': self.region,
            'exam_type': self.exam_type,
            'attempt_count': self.attempt_count,
            'avg_score': self.avg_score,
            'avg_time': self.avg_time,
            'is_active': self.is_active,
            'is_public': self.is_public,
            'question_count': len(self.questions) if self.questions else 0
        }
        
        if include_questions:
            questions = self.get_questions()
            data['questions'] = [q.to_dict() for q in questions]
        
        return data