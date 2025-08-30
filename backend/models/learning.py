# -*- coding: utf-8 -*-
"""
学习路径和记忆强化模型
"""

from datetime import datetime, timedelta
from utils.database import db
from sqlalchemy.dialects.postgresql import UUID
import uuid
import math

class LearningPath(db.Model):
    """学习路径模型 - 智能学习路径规划"""
    
    __tablename__ = 'learning_paths'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(UUID(as_uuid=True), db.ForeignKey('subjects.id'), nullable=False)
    
    # 基本信息
    name = db.Column(db.String(100), nullable=False, comment='学习路径名称')
    description = db.Column(db.Text, comment='路径描述')
    target_score = db.Column(db.Integer, comment='目标分数')
    
    # 路径配置
    path_type = db.Column(db.String(20), default='adaptive', comment='路径类型：adaptive/custom/template')
    priority_strategy = db.Column(db.String(20), default='weakness_first', comment='优先级策略')
    
    # 学习计划
    knowledge_points = db.Column(db.JSON, default=[], comment='知识点学习顺序')
    weekly_goals = db.Column(db.JSON, default=[], comment='周目标')
    daily_tasks = db.Column(db.JSON, default=[], comment='每日任务')
    
    # 进度跟踪
    total_points = db.Column(db.Integer, default=0, comment='总知识点数')
    completed_points = db.Column(db.Integer, default=0, comment='已完成知识点数')
    mastered_points = db.Column(db.Integer, default=0, comment='已掌握知识点数')
    
    # 颜色分级（红黄绿系统）
    red_points = db.Column(db.JSON, default=[], comment='薄弱知识点(红色)')
    yellow_points = db.Column(db.JSON, default=[], comment='待巩固知识点(黄色)')
    green_points = db.Column(db.JSON, default=[], comment='已掌握知识点(绿色)')
    
    # 时间规划
    start_date = db.Column(db.Date, comment='开始日期')
    target_date = db.Column(db.Date, comment='目标完成日期')
    estimated_hours = db.Column(db.Integer, comment='预估学习时长(小时)')
    actual_hours = db.Column(db.Integer, default=0, comment='实际学习时长(小时)')
    
    # 状态
    status = db.Column(db.String(20), default='active', comment='状态：active/paused/completed')
    is_auto_adjust = db.Column(db.Boolean, default=True, comment='是否自动调整')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    study_records = db.relationship('StudyRecord', backref='learning_path', lazy='dynamic')
    
    def __repr__(self):
        return f'<LearningPath {self.name}>'
    
    def get_progress_rate(self):
        """计算完成进度"""
        if self.total_points == 0:
            return 0
        return round(self.completed_points / self.total_points * 100, 2)
    
    def get_mastery_rate(self):
        """计算掌握率"""
        if self.total_points == 0:
            return 0
        return round(self.mastered_points / self.total_points * 100, 2)
    
    def update_point_status(self, knowledge_point_id, status):
        """更新知识点状态"""
        point_id = str(knowledge_point_id)
        
        # 从所有列表中移除
        self.red_points = [p for p in self.red_points if p != point_id]
        self.yellow_points = [p for p in self.yellow_points if p != point_id]
        self.green_points = [p for p in self.green_points if p != point_id]
        
        # 添加到对应列表
        if status == 'red':
            self.red_points.append(point_id)
        elif status == 'yellow':
            self.yellow_points.append(point_id)
        elif status == 'green':
            self.green_points.append(point_id)
            self.mastered_points += 1
        
        db.session.commit()
    
    def get_next_tasks(self, limit=5):
        """获取下一批学习任务（先红后黄再绿）"""
        tasks = []
        
        # 优先处理红色（薄弱）知识点
        for point_id in self.red_points[:limit]:
            tasks.append({
                'knowledge_point_id': point_id,
                'priority': 'high',
                'color': 'red',
                'type': 'strengthen'
            })
        
        # 如果还有空位，处理黄色（待巩固）知识点
        remaining = limit - len(tasks)
        if remaining > 0:
            for point_id in self.yellow_points[:remaining]:
                tasks.append({
                    'knowledge_point_id': point_id,
                    'priority': 'medium',
                    'color': 'yellow',
                    'type': 'consolidate'
                })
        
        # 如果还有空位，处理绿色（已掌握）知识点进行拓展
        remaining = limit - len(tasks)
        if remaining > 0:
            for point_id in self.green_points[:remaining]:
                tasks.append({
                    'knowledge_point_id': point_id,
                    'priority': 'low',
                    'color': 'green',
                    'type': 'expand'
                })
        
        return tasks
    
    def auto_adjust_schedule(self):
        """自动调整学习计划"""
        if not self.is_auto_adjust:
            return
        
        # 检查是否需要延长目标日期
        progress_rate = self.get_progress_rate()
        days_passed = (datetime.now().date() - self.start_date).days if self.start_date else 0
        total_days = (self.target_date - self.start_date).days if self.target_date and self.start_date else 0
        
        if total_days > 0:
            expected_progress = (days_passed / total_days) * 100
            if progress_rate < expected_progress * 0.8:  # 进度落后20%以上
                # 自动延长目标日期
                extension_days = int((expected_progress - progress_rate) / 100 * total_days)
                self.target_date += timedelta(days=extension_days)
                db.session.commit()
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'subject_id': str(self.subject_id),
            'name': self.name,
            'description': self.description,
            'target_score': self.target_score,
            'path_type': self.path_type,
            'priority_strategy': self.priority_strategy,
            'knowledge_points': self.knowledge_points,
            'weekly_goals': self.weekly_goals,
            'daily_tasks': self.daily_tasks,
            'total_points': self.total_points,
            'completed_points': self.completed_points,
            'mastered_points': self.mastered_points,
            'progress_rate': self.get_progress_rate(),
            'mastery_rate': self.get_mastery_rate(),
            'red_points': self.red_points,
            'yellow_points': self.yellow_points,
            'green_points': self.green_points,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'estimated_hours': self.estimated_hours,
            'actual_hours': self.actual_hours,
            'status': self.status,
            'is_auto_adjust': self.is_auto_adjust
        }

class StudyRecord(db.Model):
    """学习记录模型"""
    
    __tablename__ = 'study_records'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    learning_path_id = db.Column(UUID(as_uuid=True), db.ForeignKey('learning_paths.id'))
    knowledge_point_id = db.Column(UUID(as_uuid=True), db.ForeignKey('knowledge_points.id'))
    question_id = db.Column(UUID(as_uuid=True), db.ForeignKey('questions.id'))
    
    # 学习内容
    study_type = db.Column(db.String(20), nullable=False, comment='学习类型：lecture/practice/review/exam')
    content_type = db.Column(db.String(20), comment='内容类型：video/text/audio/interactive')
    
    # 学习结果
    is_correct = db.Column(db.Boolean, comment='是否正确（题目）')
    score = db.Column(db.Integer, comment='得分')
    max_score = db.Column(db.Integer, comment='满分')
    
    # 时间统计
    start_time = db.Column(db.DateTime, nullable=False, comment='开始时间')
    end_time = db.Column(db.DateTime, comment='结束时间')
    duration = db.Column(db.Integer, comment='学习时长(秒)')
    
    # 学习状态
    mastery_level = db.Column(db.Integer, default=1, comment='掌握程度1-5')
    difficulty_rating = db.Column(db.Integer, comment='难度评价1-5')
    confidence_level = db.Column(db.Integer, comment='信心程度1-5')
    
    # 错误分析
    error_type = db.Column(db.String(20), comment='错误类型：knowledge/careless/method')
    error_reason = db.Column(db.Text, comment='错误原因')
    
    # 备注
    notes = db.Column(db.Text, comment='学习笔记')
    tags = db.Column(db.JSON, default=[], comment='标签')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StudyRecord {self.id}>'
    
    def calculate_duration(self):
        """计算学习时长"""
        if self.end_time and self.start_time:
            self.duration = int((self.end_time - self.start_time).total_seconds())
        return self.duration
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'learning_path_id': str(self.learning_path_id) if self.learning_path_id else None,
            'knowledge_point_id': str(self.knowledge_point_id) if self.knowledge_point_id else None,
            'question_id': str(self.question_id) if self.question_id else None,
            'study_type': self.study_type,
            'content_type': self.content_type,
            'is_correct': self.is_correct,
            'score': self.score,
            'max_score': self.max_score,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'mastery_level': self.mastery_level,
            'difficulty_rating': self.difficulty_rating,
            'confidence_level': self.confidence_level,
            'error_type': self.error_type,
            'error_reason': self.error_reason,
            'notes': self.notes,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class MemoryCard(db.Model):
    """记忆卡片模型 - 艾宾浩斯遗忘曲线实战"""
    
    __tablename__ = 'memory_cards'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    knowledge_point_id = db.Column(UUID(as_uuid=True), db.ForeignKey('knowledge_points.id'), nullable=False)
    
    # 卡片内容
    front_content = db.Column(db.Text, nullable=False, comment='正面内容（记忆任务）')
    back_content = db.Column(db.Text, nullable=False, comment='背面内容（解析+易错提示）')
    card_type = db.Column(db.String(20), default='formula', comment='卡片类型：formula/concept/method')
    
    # 记忆状态
    mastery_level = db.Column(db.Integer, default=1, comment='掌握程度1-4')
    difficulty = db.Column(db.Integer, default=3, comment='难度等级1-5')
    
    # 复习计划（艾宾浩斯曲线）
    review_count = db.Column(db.Integer, default=0, comment='复习次数')
    correct_count = db.Column(db.Integer, default=0, comment='正确次数')
    last_review_at = db.Column(db.DateTime, comment='最后复习时间')
    next_review_at = db.Column(db.DateTime, comment='下次复习时间')
    
    # 记忆强度参数
    memory_strength = db.Column(db.Float, default=1.0, comment='记忆强度')
    forgetting_rate = db.Column(db.Float, default=0.5, comment='遗忘率')
    interval_days = db.Column(db.Integer, default=1, comment='当前复习间隔(天)')
    
    # 学习统计
    total_time = db.Column(db.Integer, default=0, comment='总学习时间(秒)')
    avg_response_time = db.Column(db.Float, comment='平均反应时间(秒)')
    
    # 状态
    is_active = db.Column(db.Boolean, default=True, comment='是否激活')
    is_due = db.Column(db.Boolean, default=True, comment='是否到期复习')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<MemoryCard {self.id}>'
    
    def calculate_next_review(self, is_correct, response_time):
        """根据艾宾浩斯曲线计算下次复习时间"""
        from config import Config
        
        self.review_count += 1
        self.last_review_at = datetime.utcnow()
        
        if is_correct:
            self.correct_count += 1
            # 正确时增加记忆强度，延长复习间隔
            self.memory_strength = min(self.memory_strength * 1.3, 3.0)
            
            # 根据掌握程度调整间隔
            if self.mastery_level < 4:
                self.mastery_level += 1
        else:
            # 错误时降低记忆强度，缩短复习间隔
            self.memory_strength = max(self.memory_strength * 0.6, 0.3)
            # 降低掌握程度
            if self.mastery_level > 1:
                self.mastery_level -= 1
        
        # 计算下次复习间隔
        base_intervals = Config.MEMORY_INTERVALS  # [1, 2, 4, 7, 15, 30, 60]
        interval_index = min(self.review_count - 1, len(base_intervals) - 1)
        base_interval = base_intervals[interval_index]
        
        # 根据记忆强度和掌握程度调整间隔
        adjusted_interval = base_interval * self.memory_strength * (self.mastery_level / 2)
        self.interval_days = max(int(adjusted_interval), 1)
        
        # 设置下次复习时间
        self.next_review_at = datetime.utcnow() + timedelta(days=self.interval_days)
        
        # 更新平均反应时间
        if self.avg_response_time:
            self.avg_response_time = (self.avg_response_time * (self.review_count - 1) + response_time) / self.review_count
        else:
            self.avg_response_time = response_time
        
        # 更新总学习时间
        self.total_time += int(response_time)
        
        # 更新是否到期标志
        self.is_due = False
        
        db.session.commit()
    
    def check_if_due(self):
        """检查是否到期复习"""
        if self.next_review_at and datetime.utcnow() >= self.next_review_at:
            self.is_due = True
            db.session.commit()
        return self.is_due
    
    def get_mastery_description(self):
        """获取掌握程度描述"""
        descriptions = {
            1: '初学',
            2: '熟悉', 
            3: '熟练',
            4: '精通'
        }
        return descriptions.get(self.mastery_level, '未知')
    
    def get_accuracy_rate(self):
        """计算正确率"""
        if self.review_count == 0:
            return 0
        return round(self.correct_count / self.review_count * 100, 2)
    
    def to_dict(self, include_back=False):
        data = {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'knowledge_point_id': str(self.knowledge_point_id),
            'front_content': self.front_content,
            'card_type': self.card_type,
            'mastery_level': self.mastery_level,
            'mastery_description': self.get_mastery_description(),
            'difficulty': self.difficulty,
            'review_count': self.review_count,
            'correct_count': self.correct_count,
            'accuracy_rate': self.get_accuracy_rate(),
            'last_review_at': self.last_review_at.isoformat() if self.last_review_at else None,
            'next_review_at': self.next_review_at.isoformat() if self.next_review_at else None,
            'memory_strength': self.memory_strength,
            'forgetting_rate': self.forgetting_rate,
            'interval_days': self.interval_days,
            'total_time': self.total_time,
            'avg_response_time': self.avg_response_time,
            'is_active': self.is_active,
            'is_due': self.is_due
        }
        
        if include_back:
            data['back_content'] = self.back_content
        
        return data
    
    @classmethod
    def get_due_cards(cls, user_id, limit=10):
        """获取到期复习的卡片"""
        return cls.query.filter_by(
            user_id=user_id,
            is_active=True,
            is_due=True
        ).order_by(cls.next_review_at.asc()).limit(limit).all()
    
    @classmethod
    def update_due_status(cls):
        """批量更新到期状态"""
        due_cards = cls.query.filter(
            cls.next_review_at <= datetime.utcnow(),
            cls.is_active == True,
            cls.is_due == False
        ).all()
        
        for card in due_cards:
            card.is_due = True
        
        db.session.commit()
        return len(due_cards)