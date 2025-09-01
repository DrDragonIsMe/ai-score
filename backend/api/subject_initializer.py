#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学科初始化API接口
提供学科数据抓取和初始化功能
"""

from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
import asyncio
import json
from datetime import datetime
from typing import Dict, List

from services.subject_initializer import SubjectInitializer
from models.base import db
from models.knowledge import Subject
from utils.decorators import role_required
from utils.response import success_response, error_response
from utils.logger import get_logger

logger = get_logger(__name__)

# 创建蓝图
subject_initializer_bp = Blueprint('subject_initializer', __name__, url_prefix='/api/subjects')

# 存储初始化进度的全局字典
initialization_progress = {}

class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.progress = {
            'task_id': task_id,
            'status': 'running',
            'current_subject': '',
            'progress_percent': 0,
            'message': '初始化开始...',
            'completed_subjects': [],
            'conflicts': [],
            'errors': [],
            'start_time': datetime.now().isoformat(),
            'end_time': None
        }
        initialization_progress[task_id] = self.progress
    
    def update(self, message: str, percent: int, subject: str = ''):
        """更新进度"""
        self.progress.update({
            'message': message,
            'progress_percent': percent,
            'current_subject': subject
        })
        initialization_progress[self.task_id] = self.progress
    
    def add_conflict(self, subject_code: str, conflicts: List[Dict]):
        """添加冲突信息"""
        self.progress['conflicts'].extend([{
            'subject_code': subject_code,
            'conflicts': conflicts
        }])
    
    def add_error(self, subject_code: str, error: str):
        """添加错误信息"""
        self.progress['errors'].append({
            'subject_code': subject_code,
            'error': error
        })
    
    def complete_subject(self, subject_code: str, result: Dict):
        """完成学科处理"""
        self.progress['completed_subjects'].append({
            'subject_code': subject_code,
            'result': result
        })
    
    def finish(self, status: str = 'completed'):
        """完成任务"""
        self.progress.update({
            'status': status,
            'progress_percent': 100,
            'end_time': datetime.now().isoformat()
        })
        initialization_progress[self.task_id] = self.progress

@subject_initializer_bp.route('/initialize-with-crawling', methods=['POST'])
@jwt_required()
@role_required('admin')
def initialize_subjects_with_crawling():
    """初始化学科并抓取数据"""
    try:
        # 获取请求参数
        data = request.get_json() or {}
        subject_codes = data.get('subject_codes', [])
        overwrite_conflicts = data.get('overwrite_conflicts', False)
        
        # 获取租户信息
        identity = get_jwt_identity()
        tenant_id = identity.get('tenant_id')
        
        if not tenant_id:
            return error_response('租户信息缺失', 400)
        
        # 如果没有指定学科，默认初始化所有九大学科
        if not subject_codes:
            subject_codes = ['chinese', 'math', 'english', 'physics', 'chemistry', 
                           'biology', 'history', 'geography', 'politics']
        
        # 生成任务ID
        task_id = f"init_{tenant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 启动初始化任务
        import threading
        
        def run_initialization():
            try:
                _initialize_subjects_sync(task_id, tenant_id, subject_codes, overwrite_conflicts)
            except Exception as e:
                logger.error(f"初始化任务执行失败: {str(e)}")
        
        thread = threading.Thread(target=run_initialization)
        thread.daemon = True
        thread.start()
        
        return success_response({
            'task_id': task_id,
            'message': '学科初始化任务已启动',
            'subject_count': len(subject_codes)
        })
        
    except Exception as e:
        logger.error(f"启动学科初始化失败: {str(e)}")
        return error_response(f'启动初始化失败: {str(e)}', 500)

@subject_initializer_bp.route('/initialization-progress/<task_id>', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_initialization_progress(task_id: str):
    """获取初始化进度"""
    try:
        if task_id not in initialization_progress:
            return error_response('任务不存在', 404)
        
        progress = initialization_progress[task_id]
        return success_response(progress)
        
    except Exception as e:
        logger.error(f"获取初始化进度失败: {str(e)}")
        return error_response(f'获取进度失败: {str(e)}', 500)

@subject_initializer_bp.route('/resolve-conflicts', methods=['POST'])
@jwt_required()
@role_required('admin')
def resolve_conflicts():
    """解决数据冲突"""
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        resolutions = data.get('resolutions', [])  # [{'subject_code': 'math', 'action': 'overwrite'/'skip'}]
        
        if task_id not in initialization_progress:
            return error_response('任务不存在', 404)
        
        # 获取租户信息
        identity = get_jwt_identity()
        tenant_id = identity.get('tenant_id')
        
        # 启动冲突解决任务
        import threading
        
        def run_conflict_resolution():
            try:
                _resolve_conflicts_sync(task_id, tenant_id, resolutions)
            except Exception as e:
                logger.error(f"冲突解决任务执行失败: {str(e)}")
        
        thread = threading.Thread(target=run_conflict_resolution)
        thread.daemon = True
        thread.start()
        
        return success_response({'message': '冲突解决任务已启动'})
        
    except Exception as e:
        logger.error(f"解决冲突失败: {str(e)}")
        return error_response(f'解决冲突失败: {str(e)}', 500)

@subject_initializer_bp.route('/clear-progress/<task_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def clear_progress(task_id: str):
    """清除进度记录"""
    try:
        if task_id in initialization_progress:
            del initialization_progress[task_id]
        
        return success_response({'message': '进度记录已清除'})
        
    except Exception as e:
        logger.error(f"清除进度记录失败: {str(e)}")
        return error_response(f'清除失败: {str(e)}', 500)

def _initialize_subjects_sync(task_id: str, tenant_id: str, 
                                   subject_codes: List[str], overwrite_conflicts: bool):
    """同步初始化学科数据"""
    from app import create_app
    
    # 创建应用上下文
    app = create_app()
    
    with app.app_context():
        tracker = ProgressTracker(task_id)
        initializer = None
        
        try:
            # 创建初始化器实例
            initializer = SubjectInitializer(tenant_id)
            
            total_subjects = len(subject_codes)
            for i, subject_code in enumerate(subject_codes):
                try:
                    # 获取学科信息
                    subject = db.session.query(Subject).filter_by(
                        code=subject_code,
                        tenant_id=tenant_id
                    ).first()
                    
                    if not subject:
                        tracker.add_error(subject_code, f'学科 {subject_code} 不存在')
                        continue
                    
                    # 更新进度
                    base_progress = int((i / total_subjects) * 100)
                    subject_name = subject.name if subject else subject_code
                    tracker.update(
                        f'正在初始化 {subject_name}...',
                        base_progress,
                        subject_name
                    )
                    
                    # 初始化学科
                    def progress_callback(message, percent):
                        actual_progress = base_progress + int((percent / 100) * (100 / total_subjects))
                        tracker.update(message, actual_progress, subject_name)
                    
                    result = initializer.initialize_subject(
                        subject_code, subject.id, progress_callback
                    )
                    
                    # 检查冲突
                    if result['conflicts'] and not overwrite_conflicts:
                        tracker.add_conflict(subject_code, result['conflicts'])
                        tracker.update(
                            f'{subject_name} 存在数据冲突，等待用户处理',
                            base_progress + int(100 / total_subjects),
                            subject_name
                        )
                    else:
                        # 保存数据
                        save_result = initializer.save_data(
                            subject.id, result, overwrite_conflicts
                        )
                        result['save_result'] = save_result
                        
                        tracker.update(
                            f'{subject_name} 初始化完成',
                            base_progress + int(100 / total_subjects),
                            subject_name
                        )
                    
                    tracker.complete_subject(subject_code, result)
                    
                except Exception as e:
                    logger.error(f"初始化学科 {subject_code} 失败: {str(e)}")
                    tracker.add_error(subject_code, str(e))
            
            # 检查是否有冲突需要处理
            if tracker.progress['conflicts']:
                tracker.progress['status'] = 'conflicts_pending'
                tracker.update('存在数据冲突，请处理后继续', 100)
            else:
                tracker.finish('completed')
                tracker.update('所有学科初始化完成', 100)
                
        except Exception as e:
            logger.error(f"初始化任务失败: {str(e)}")
            tracker.add_error('system', str(e))
            tracker.finish('failed')
            tracker.update(f'初始化失败: {str(e)}', 100)
        
        finally:
            if initializer:
                initializer.close()

def _resolve_conflicts_sync(task_id: str, tenant_id: str, resolutions: List[Dict]):
    """同步解决冲突"""
    if task_id not in initialization_progress:
        return
    
    tracker = ProgressTracker(task_id)
    tracker.progress = initialization_progress[task_id]  # 继承现有进度
    tracker.progress['status'] = 'resolving_conflicts'
    
    initializer = None
    
    try:
        initializer = SubjectInitializer(tenant_id)
        
        for resolution in resolutions:
            subject_code = resolution['subject_code']
            action = resolution['action']  # 'overwrite' or 'skip'
            
            if action == 'skip':
                continue
            
            # 找到对应的学科结果
            subject_result = None
            for completed in tracker.progress['completed_subjects']:
                if completed['subject_code'] == subject_code:
                    subject_result = completed['result']
                    break
            
            if not subject_result:
                continue
            
            # 获取学科信息
            subject = db.session.query(Subject).filter_by(
                code=subject_code,
                tenant_id=tenant_id
            ).first()
            
            if subject:
                # 保存数据（覆盖冲突）
                save_result = initializer.save_data(
                    subject.id, subject_result, overwrite_conflicts=True
                )
                
                subject_name = subject.name if subject else resolution['subject_code']
                tracker.update(
                    f'{subject_name} 冲突已解决',
                    tracker.progress['progress_percent'],
                    subject_name
                )
        
        # 清除冲突记录
        tracker.progress['conflicts'] = []
        tracker.finish('completed')
        tracker.update('所有冲突已解决，初始化完成', 100)
        
    except Exception as e:
        logger.error(f"解决冲突失败: {str(e)}")
        tracker.add_error('conflict_resolution', str(e))
        tracker.finish('failed')
        tracker.update(f'解决冲突失败: {str(e)}', 100)
    
    finally:
        if initializer:
            initializer.close()