import { api } from './api';

// 系统设置相关API
export const settingsApi = {
  // AI模型管理
  getAIModels: () => {
    return api.get('/settings/ai-models');
  },

  createAIModel: (data: any) => {
    return api.post('/settings/ai-models', data);
  },

  updateAIModel: (modelId: string, data: any) => {
    return api.put(`/settings/ai-models/${modelId}`, data);
  },

  deleteAIModel: (modelId: string) => {
    return api.delete(`/settings/ai-models/${modelId}`);
  },

  testAIModel: (modelId: string) => {
    return api.post(`/settings/ai-models/${modelId}/test`);
  },

  setDefaultAIModel: (modelId: string) => {
    return api.post(`/settings/ai-models/${modelId}/set-default`);
  },

  toggleAIModelActive: (modelId: string) => {
    return api.post(`/settings/ai-models/${modelId}/toggle-active`);
  },

  getAIModel: (modelId: string) => {
    return api.get(`/settings/ai-models/${modelId}`);
  },

  // 学科管理
  getSubjects: () => {
    return api.get('/subjects');
  },

  createSubject: (data: any) => {
    return api.post('/subjects', data);
  },

  updateSubject: (subjectId: string, data: any) => {
    return api.put(`/subjects/${subjectId}`, data);
  },

  deleteSubject: (subjectId: string) => {
    return api.delete(`/subjects/${subjectId}`);
  },

  // 学科初始化
  previewSubjectInitialization: () => {
    return api.get('/subjects/initialize/preview');
  },

  initializeSubjects: (options: { force_update?: boolean } = {}) => {
    return api.post('/subjects/initialize', options);
  },

  startSubjectInitialization: (options: { force_update?: boolean } = {}) => {
    return api.post('/subjects/initialize', options);
  },

  getInitializationProgress: (taskId?: string) => {
    const url = taskId ? `/subjects/initialize/progress/${taskId}` : '/subjects/initialize/progress';
    return api.get(url);
  },

  clearProgress: (taskId: string) => {
    return api.delete(`/subjects/initialize/progress/${taskId}`);
  },

  stopSubjectInitialization: () => {
    return api.post('/subjects/initialize/stop');
  },

  getInitializationStatus: () => {
    return api.get('/subjects/initialize/status');
  },

  // 系统信息
  getSystemInfo: () => {
    return api.get('/settings/system-info');
  }
};

export default settingsApi;