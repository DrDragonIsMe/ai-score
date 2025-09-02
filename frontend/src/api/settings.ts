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
  }
};