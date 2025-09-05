import axios from 'axios';

// API基础配置
const API_BASE_URL = 'http://localhost:5001/api';

// 创建axios实例
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加认证token
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    // 处理认证错误
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// 试卷管理API
export const examPaperApi = {
  // 获取试卷列表
  getExamPapers: (token: string, subjectId?: string) => {
    const params = subjectId ? { subject_id: subjectId } : {};
    return api.get('/exam-papers', {
      headers: { Authorization: `Bearer ${token}` },
      params
    });
  },

  // 获取科目列表
  getSubjects: (token: string) => {
    return api.get('/subjects', {
      headers: { Authorization: `Bearer ${token}` }
    });
  },

  // 上传试卷
  uploadExamPaper: (token: string, file: File, formData: any) => {
    const data = new FormData();
    data.append('file', file);
    Object.keys(formData).forEach(key => {
      if (key === 'file') {
        // 跳过file字段，已经单独处理
        return;
      }
      if (key === 'tags') {
        // 处理标签字段
        if (typeof formData[key] === 'string') {
          data.append(key, formData[key]);
        } else if (Array.isArray(formData[key])) {
          data.append(key, formData[key].join(','));
        }
      } else if (key === 'auto_generate_kg') {
        // 处理布尔值字段
        data.append(key, formData[key] ? 'true' : 'false');
      } else {
        data.append(key, formData[key]);
      }
    });
    
    return api.post('/exam-papers/upload', data, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  // 下载科目试卷
  downloadSubjectPapers: (token: string, subjectId: string, years: number) => {
    return api.post(`/subjects/${subjectId}/download-papers`, 
      { years },
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
  },

  // 删除试卷
  deleteExamPaper: (token: string, paperId: string) => {
    return api.delete(`/exam-papers/${paperId}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
  },

  // 获取试卷解析状态
  getParseStatus: (token: string, paperId: string) => {
    return api.get(`/exam-papers/${paperId}/parse-status`, {
      headers: { Authorization: `Bearer ${token}` }
    });
  }
};

export default api;