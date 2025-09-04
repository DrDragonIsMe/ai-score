import { api } from '../services/api';

export interface AIModelConfig {
  id?: string;
  name: string;
  model_type: string;
  model_id: string;
  api_key: string;
  api_base_url: string;
  max_tokens: number;
  temperature: number;
  top_p: number;
  frequency_penalty: number;
  presence_penalty: number;
  supports_streaming: boolean;
  supports_function_calling: boolean;
  supports_vision: boolean;
  max_requests_per_minute: number;
  max_tokens_per_minute: number;
  cost_per_1k_input_tokens: number;
  cost_per_1k_output_tokens: number;
  is_active: boolean;
  is_default?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface SystemInfo {
  version: string;
  environment: string;
  database_status: string;
  ai_service_status: string;
  total_models: number;
  active_models: number;
  default_model: string;
}

export interface SubjectInitProgress {
  task_id?: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'waiting_for_conflicts';
  progress_percent: number;
  message: string;
  current_subject?: string;
  current_stage?: string;
  stage_progress?: number;
  download_source?: string;
  completed_subjects: Array<{
    subject_code: string;
    name: string;
  }>;
  conflicts: Array<{
    subject_code: string;
    conflicts: string[];
  }>;
  errors: Array<{
    subject_code: string;
    error: string;
  }>;
  start_time: string;
  end_time?: string;
  created_count?: number;
  updated_count?: number;
  error?: string;
}

export interface SubjectPreview {
  code: string;
  name: string;
  name_en: string;
  description: string;
  category: string;
  grade_range: string;
}

export interface SubjectInitResult {
  created_count: number;
  updated_count: number;
  total_subjects: number;
  conflicts?: string[];
}



export const settingsApi = {
  // 获取AI模型列表
  getAIModels: () => {
    return api.get('/settings/ai-models');
  },

  // 获取单个AI模型详情
  getAIModel: (modelId: string) => {
    return api.get(`/settings/ai-models/${modelId}`);
  },

  // 创建AI模型
  createAIModel: (data: Omit<AIModelConfig, 'id' | 'is_default' | 'created_at' | 'updated_at'>) => {
    return api.post('/settings/ai-models', data);
  },

  // 更新AI模型
  updateAIModel: (modelId: string, data: Partial<AIModelConfig>) => {
    return api.put(`/settings/ai-models/${modelId}`, data);
  },

  // 删除AI模型
  deleteAIModel: (modelId: string) => {
    return api.delete(`/settings/ai-models/${modelId}`);
  },

  // 测试AI模型
  testAIModel: (modelId: string) => {
    return api.post(`/settings/ai-models/${modelId}/test`);
  },

  // 设置默认AI模型
  setDefaultAIModel: (modelId: string) => {
    return api.post(`/settings/ai-models/${modelId}/set-default`);
  },

  // 切换AI模型启用/禁用状态
  toggleAIModelActive: (modelId: string) => {
    return api.post(`/settings/ai-models/${modelId}/toggle-active`);
  },

  // 获取系统信息
  getSystemInfo: () => {
    return api.get('/settings/system-info');
  },

  // 九大学科初始化相关API
  // 获取初始化状态
  getSubjectInitStatus: () => {
    return api.get('/subjects/initialize/status');
  },

  // 预览将要初始化的学科
  previewSubjects: () => {
    return api.get('/subjects/initialize/preview');
  },

  // 初始化九大学科
  initializeSubjects: (forceUpdate: boolean = false) => {
    return api.post('/subjects/initialize', { force_update: forceUpdate });
  },

  // 获取初始化进度
  getInitializationProgress: (taskId?: string) => {
    const url = taskId ? `/subjects/initialize/progress?task_id=${taskId}` : '/subjects/initialize/progress';
    return api.get(url);
  },

  // 解决初始化冲突
  resolveConflicts: (action: 'skip' | 'overwrite', conflicts: string[]) => {
    return api.post('/subjects/initialize/conflicts/resolve', {
      action,
      conflicts
    });
  },

  // 清除初始化进度记录
  clearProgress: (taskId: string) => {
    return api.delete(`/subjects/initialize/progress/${taskId}`);
  },

};