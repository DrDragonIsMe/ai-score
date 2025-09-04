#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - 九大学科初始化API

Description:
    提供九大学科初始化的REST API接口。

Author: Chang Xinglong
Date: 2025-01-21
Version: 1.0.0
License: Apache License 2.0
"""

from flask import Blueprint, request, g, current_app
from flask_jwt_extended import jwt_required
from utils.decorators import admin_required
from utils.response import success_response, error_response
from services.subject_initializer import SubjectInitializer
from utils.logger import get_logger
import uuid
import threading
from datetime import datetime

logger = get_logger(__name__)

# 全局任务状态存储
task_status = {}

# 创建蓝图
subject_initializer_bp = Blueprint('subject_initializer', __name__, url_prefix='/api/subjects')

def _run_initialization_task(task_id, tenant_id, force_update, user_id, app_context):
    """
    异步执行初始化任务
    """
    logger.info(f"异步任务开始执行，任务ID: {task_id}, 租户ID: {tenant_id}, 强制更新: {force_update}")
    try:
        with app_context():
            # 更新任务状态为运行中
            task_status[task_id].update({
                'status': 'running',
                'message': '正在初始化学科...',
                'current_subject': None,
                'progress_percent': 0
            })
            
            # 创建初始化器
            initializer = SubjectInitializer(tenant_id)
            
            # 获取学科数据并显示进度
            subjects = initializer.get_default_subjects()
            total_subjects = len(subjects)
            
            # 显示准备阶段进度
            task_status[task_id].update({
                'message': f'准备初始化 {total_subjects} 个学科...',
                'progress_percent': 5
            })
            
            import time
            time.sleep(0.5)
            
            # 详细进度更新
            for i, subject_data in enumerate(subjects):
                subject_name = subject_data['name']
                base_progress = 5 + (i / total_subjects) * 85
                
                # 阶段1: 下载大纲
                task_status[task_id].update({
                    'current_subject': subject_name,
                    'progress_percent': base_progress + (0.2 / total_subjects) * 85,
                    'message': f'正在下载学科大纲: {subject_name}',
                    'current_stage': '下载大纲',
                    'download_source': '教育部官方网站',
                    'stage_progress': 20
                })
                time.sleep(0.1)
                
                # 阶段2: 解析内容
                task_status[task_id].update({
                    'progress_percent': base_progress + (0.4 / total_subjects) * 85,
                    'message': f'正在解析学科内容: {subject_name}',
                    'current_stage': '解析内容',
                    'stage_progress': 40
                })
                time.sleep(0.1)
                
                # 阶段3: 生成知识图谱
                task_status[task_id].update({
                    'progress_percent': base_progress + (0.7 / total_subjects) * 85,
                    'message': f'正在生成知识图谱: {subject_name}',
                    'current_stage': '生成知识图谱',
                    'stage_progress': 70
                })
                time.sleep(0.1)
                
                # 阶段4: 创建星图
                task_status[task_id].update({
                    'progress_percent': base_progress + (0.9 / total_subjects) * 85,
                    'message': f'正在创建学科星图: {subject_name}',
                    'current_stage': '创建星图',
                    'stage_progress': 90
                })
                time.sleep(0.1)
                
                # 完成当前学科
                task_status[task_id].update({
                    'progress_percent': base_progress + (1.0 / total_subjects) * 85,
                    'message': f'学科 {subject_name} 处理完成 ({i+1}/{total_subjects})',
                    'current_stage': '完成',
                    'stage_progress': 100
                })
                time.sleep(0.1)
            
            # 显示执行阶段
            task_status[task_id].update({
                'message': '正在执行数据库操作...',
                'progress_percent': 90,
                'current_subject': None
            })
            time.sleep(0.5)
            
            # 执行实际初始化
            result = initializer.initialize_subjects(force_update=force_update)
            
            if result['success']:
                task_status[task_id].update({
                    'status': 'completed',
                    'message': result['message'],
                    'progress_percent': 100,
                    'created_count': result['created_count'],
                    'updated_count': result['updated_count'],
                    'total_subjects': result['total_subjects'],
                    'end_time': datetime.utcnow().isoformat() + 'Z',
                    'completed_subjects': [{'subject_code': s['code']} for s in subjects[:result['created_count'] + result['updated_count']]],
                    'conflicts': [],
                    'errors': []
                })
                logger.info(f"用户 {user_id} 成功初始化九大学科")
            else:
                if 'conflicts' in result:
                    task_status[task_id].update({
                        'status': 'waiting_for_conflicts',
                        'message': result['message'],
                        'conflicts': [{'subject_code': c['code'], 'conflicts': [c]} for c in result['conflicts']],
                        'created_count': result['created_count'],
                        'updated_count': result['updated_count'],
                        'errors': []
                    })
                else:
                    task_status[task_id].update({
                        'status': 'failed',
                        'message': result['message'],
                        'error': result.get('error', '未知错误'),
                        'end_time': datetime.utcnow().isoformat() + 'Z',
                        'errors': [{'subject_code': 'unknown', 'error': result.get('error', '未知错误')}]
                    })
                    
    except Exception as e:
        logger.error(f"初始化任务执行失败: {str(e)}")
        with app_context():
            task_status[task_id].update({
                'status': 'failed',
                'message': f'初始化失败: {str(e)}',
                'error': str(e),
                'end_time': datetime.utcnow().isoformat() + 'Z',
                'errors': [{'subject_code': 'unknown', 'error': str(e)}]
            })

@subject_initializer_bp.route('/initialize', methods=['POST'])
@jwt_required()
@admin_required
def initialize_subjects():
    """
    初始化九大学科（异步任务）
    
    请求参数:
    - force_update: bool, 是否强制更新已存在的学科
    
    返回:
    - success: bool, 是否成功
    - message: str, 消息
    - data: dict, 包含task_id的任务信息
    """
    try:
        data = request.get_json() or {}
        force_update = data.get('force_update', False)
        
        # 获取当前租户ID和用户ID
        tenant_id = g.current_user.tenant_id
        user_id = g.current_user.id
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 初始化任务状态
        task_status[task_id] = {
            'task_id': task_id,
            'status': 'pending',
            'message': '任务已创建，等待执行...',
            'progress_percent': 0,
            'start_time': datetime.utcnow().isoformat() + 'Z',  # 设置任务创建时间作为开始时间，添加UTC时区标识
            'end_time': None,
            'current_subject': None,
            'completed_subjects': [],
            'conflicts': [],
            'errors': [],
            'created_count': 0,
            'updated_count': 0
        }
        
        # 启动异步任务 - 传递应用上下文
        app_context = current_app.app_context
        thread = threading.Thread(
            target=_run_initialization_task,
            args=(task_id, tenant_id, force_update, user_id, app_context)
        )
        thread.daemon = True
        thread.start()
        
        return success_response(
            message='初始化任务已启动',
            data={'task_id': task_id}
        )
                
    except Exception as e:
        logger.error(f"启动初始化任务失败: {str(e)}")
        return error_response(f"启动任务失败: {str(e)}", 500)

@subject_initializer_bp.route('/initialize/progress', methods=['GET'])
@subject_initializer_bp.route('/initialize/progress/<task_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_initialization_progress(task_id=None):
    """
    获取初始化进度
    
    参数:
    - task_id: str, 任务ID（可选）
    
    返回:
    - success: bool, 是否成功
    - data: dict, 进度信息
    """
    try:
        if task_id:
            # 获取指定任务的进度
            if task_id not in task_status:
                return error_response("任务不存在", 404)
            
            progress = task_status[task_id]
            return success_response(
                message="获取进度成功",
                data=progress
            )
        else:
            # 兼容旧版本，返回默认进度
            tenant_id = g.current_user.tenant_id
            initializer = SubjectInitializer(tenant_id)
            progress = initializer.get_initialization_progress()
            
            return success_response(
                message="获取进度成功",
                data=progress
            )
        
    except Exception as e:
        logger.error(f"获取初始化进度失败: {str(e)}")
        return error_response(f"获取进度失败: {str(e)}", 500)

@subject_initializer_bp.route('/initialize/conflicts/resolve', methods=['POST'])
@jwt_required()
@admin_required
def resolve_conflicts():
    """
    解决初始化冲突
    
    请求参数:
    - action: str, 处理方式 ('skip' | 'overwrite')
    - conflicts: list, 冲突的学科代码列表
    
    返回:
    - success: bool, 是否成功
    - message: str, 消息
    - data: dict, 处理结果
    """
    try:
        data = request.get_json()
        action = data.get('action')
        conflicts = data.get('conflicts', [])
        
        if action not in ['skip', 'overwrite']:
            return error_response("无效的处理方式", 400)
        
        # 获取当前租户ID
        tenant_id = g.current_user.tenant_id
        
        # 创建初始化器
        initializer = SubjectInitializer(tenant_id)
        
        if action == 'overwrite':
            # 强制更新冲突的学科
            result = initializer.initialize_subjects(force_update=True)
        else:
            # 跳过冲突，只创建新的学科
            result = initializer.initialize_subjects(force_update=False)
        
        if result['success']:
            logger.info(f"用户 {g.current_user.username} 解决初始化冲突: {action}")
            return success_response(
                message=f"冲突处理成功 ({action})",
                data={
                    'created_count': result['created_count'],
                    'updated_count': result['updated_count'],
                    'total_subjects': result['total_subjects']
                }
            )
        else:
            return error_response(result['message'], 500)
            
    except Exception as e:
        logger.error(f"解决初始化冲突失败: {str(e)}")
        return error_response(f"处理冲突失败: {str(e)}", 500)

@subject_initializer_bp.route('/initialize/preview', methods=['GET'])
@jwt_required()
@admin_required
def preview_subjects():
    """
    预览将要初始化的九大学科
    
    返回:
    - success: bool, 是否成功
    - data: dict, 学科预览信息
    """
    try:
        # 获取当前租户ID
        tenant_id = g.current_user.tenant_id
        
        # 创建初始化器
        initializer = SubjectInitializer(tenant_id)
        
        # 获取默认学科数据
        default_subjects = initializer.get_default_subjects()
        
        # 检查现有学科
        existing_codes = initializer.check_existing_subjects()
        
        # 分类学科
        new_subjects = []
        existing_subjects = []
        
        for subject in default_subjects:
            if subject['code'] in existing_codes:
                existing_subjects.append(subject)
            else:
                new_subjects.append(subject)
        
        return success_response(
            message="获取预览成功",
            data={
                'new_subjects': new_subjects,
                'existing_subjects': existing_subjects,
                'total_count': len(default_subjects),
                'new_count': len(new_subjects),
                'existing_count': len(existing_subjects)
            }
        )
        
    except Exception as e:
        logger.error(f"获取学科预览失败: {str(e)}")
        return error_response(f"获取预览失败: {str(e)}", 500)

@subject_initializer_bp.route('/initialize/status', methods=['GET'])
@jwt_required()
@admin_required
def get_initialization_status():
    """
    获取初始化状态
    
    返回:
    - success: bool, 是否成功
    - data: dict, 状态信息
    """
    try:
        # 获取当前租户ID
        tenant_id = g.current_user.tenant_id
        
        # 创建初始化器
        initializer = SubjectInitializer(tenant_id)
        
        # 检查现有学科
        existing_codes = initializer.check_existing_subjects()
        default_subjects = initializer.get_default_subjects()
        default_codes = [subject['code'] for subject in default_subjects]
        
        # 计算状态
        initialized_codes = [code for code in default_codes if code in existing_codes]
        missing_codes = [code for code in default_codes if code not in existing_codes]
        
        is_initialized = len(missing_codes) == 0
        progress = int((len(initialized_codes) / len(default_codes)) * 100)
        
        return success_response(
            message="获取状态成功",
            data={
                'is_initialized': is_initialized,
                'progress': progress,
                'total_subjects': len(default_codes),
                'initialized_subjects': len(initialized_codes),
                'missing_subjects': len(missing_codes),
                'initialized_codes': initialized_codes,
                'missing_codes': missing_codes
            }
        )
        
    except Exception as e:
        logger.error(f"获取初始化状态失败: {str(e)}")
        return error_response(f"获取状态失败: {str(e)}", 500)