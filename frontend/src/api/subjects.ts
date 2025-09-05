import { api } from '../services/api';

// 学科相关API接口
export interface Subject {
  id: string;
  name: string;
  description?: string;
  grade_level?: string;
  chapters?: Chapter[];
}

export interface Chapter {
  id: string;
  name: string;
  order: number;
  knowledge_points_count?: number;
}

// 获取学科列表
export const getSubjects = async (): Promise<Subject[]> => {
  const response = await api.get('/subjects');
  return response.data || [];
};

// 获取单个学科详情
export const getSubject = async (subjectId: string): Promise<Subject> => {
  const response = await api.get(`/subjects/${subjectId}`);
  return response.data;
};

// 创建学科
export const createSubject = async (subjectData: Omit<Subject, 'id'>): Promise<Subject> => {
  const response = await api.post('/subjects', subjectData);
  return response.data;
};

// 更新学科
export const updateSubject = async (subjectId: string, subjectData: Partial<Subject>): Promise<Subject> => {
  const response = await api.put(`/subjects/${subjectId}`, subjectData);
  return response.data;
};

// 删除学科
export const deleteSubject = async (subjectId: string): Promise<void> => {
  await api.delete(`/subjects/${subjectId}`);
};

export default {
  getSubjects,
  getSubject,
  createSubject,
  updateSubject,
  deleteSubject,
};