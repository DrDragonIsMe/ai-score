import { api } from '../services/api';

// 知识图谱相关API接口
export interface KnowledgeGraphRequest {
  subject_id: string;
  content: string;
  tags?: string[];
  difficulty_level?: string;
  target_audience?: string;
}

export interface KnowledgeGraphResponse {
  id: string;
  subject_id: string;
  content: string;
  tags: string[];
  knowledge_graph: {
    nodes: GraphNode[];
    edges: GraphEdge[];
    layout_config: LayoutConfig;
  };
  created_at: string;
  updated_at: string;
}

export interface GraphNode {
  id: string;
  name: string;
  type: 'subject' | 'chapter' | 'knowledge_point' | 'sub_knowledge_point';
  level: number;
  position?: {
    x: number;
    y: number;
  };
  difficulty_level?: string;
  keywords?: string[];
  original_id?: number;
  chapter_id?: number;
  section_id?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: 'hierarchy' | 'relation';
  strength?: number;
}

export interface LayoutConfig {
  layout: string;
  node_size_factor: number;
  link_strength_factor: number;
  color_scheme: string;
}

// 生成知识图谱
export const generateKnowledgeGraph = async (data: KnowledgeGraphRequest): Promise<KnowledgeGraphResponse> => {
  const response = await api.post('/knowledge-graph/generate', data);
  return response.data;
};

// 获取知识图谱列表
export const getKnowledgeGraphs = async (subjectId?: string): Promise<KnowledgeGraphResponse[]> => {
  const params = subjectId ? { subject_id: subjectId } : {};
  const response = await api.get('/knowledge-graph', { params });
  return response.data || [];
};

// 获取单个知识图谱
export const getKnowledgeGraph = async (graphId: string): Promise<KnowledgeGraphResponse> => {
  const response = await api.get(`/knowledge-graph/${graphId}`);
  return response.data;
};

// 更新知识图谱
export const updateKnowledgeGraph = async (graphId: string, data: Partial<KnowledgeGraphRequest>): Promise<KnowledgeGraphResponse> => {
  const response = await api.put(`/knowledge-graph/${graphId}`, data);
  return response.data;
};

// 删除知识图谱
export const deleteKnowledgeGraph = async (graphId: string): Promise<void> => {
  await api.delete(`/knowledge-graph/${graphId}`);
};

export default {
  generateKnowledgeGraph,
  getKnowledgeGraphs,
  getKnowledgeGraph,
  updateKnowledgeGraph,
  deleteKnowledgeGraph,
};