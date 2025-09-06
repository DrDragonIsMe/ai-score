import { api } from '../services/api';

// 知识图谱相关API接口
export interface KnowledgeGraphRequest {
  subject_id: string;
  content: string;
  tags?: string[];
  difficulty_level?: string;
  target_audience?: string;
  title?: string;
  force_overwrite?: boolean;
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
  const response = await api.post('/ai-assistant/generate-knowledge-graph', data);
  return response.data;
};

// 获取知识图谱列表
export const getKnowledgeGraphs = async (params?: { subjectId?: string; graphType?: string; [key: string]: any }): Promise<KnowledgeGraphResponse[]> => {
  const queryParams: any = {};
  if (params?.subjectId) queryParams.subject_id = params.subjectId;
  if (params?.graphType) queryParams.type = params.graphType;
  const response = await api.get('/knowledge-graph', { params: queryParams });
  return response.data || [];
};

// 兼容旧的调用方式
export const getKnowledgeGraphsLegacy = async (subjectId?: string, graphType?: string): Promise<KnowledgeGraphResponse[]> => {
  const params: any = {};
  if (subjectId) params.subject_id = subjectId;
  if (graphType) params.type = graphType;
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
  const response = await api.put(`/knowledge-graph/nodes/${graphId}`, data);
  return response.data;
};

// 删除知识图谱
export const deleteKnowledgeGraph = async (graphId: string): Promise<void> => {
  await api.delete(`/knowledge-graph/nodes/${graphId}`);
};

// 搜索知识图谱内容
export interface KnowledgeGraphSearchRequest {
  query: string;
  subject_filter?: string;
}

export interface KnowledgeGraphSearchResult {
  id: string;
  name: string;
  description: string;
  content: string;
  subject_name: string;
  subject_id: string;
  tags: string[];
  graph_type: string;
  created_at: string;
  updated_at: string;
  relevance_score: number;
  data_type: string;
}

export interface KnowledgeGraphSearchResponse {
  results: KnowledgeGraphSearchResult[];
  total_found: number;
  message: string;
  timestamp: string;
}

export const searchKnowledgeGraphs = async (data: KnowledgeGraphSearchRequest): Promise<KnowledgeGraphSearchResponse> => {
  const response = await api.post('/ai-assistant/search-knowledge-graphs', data);
  return response.data;
};

export default {
  generateKnowledgeGraph,
  getKnowledgeGraphs,
  getKnowledgeGraph,
  updateKnowledgeGraph,
  deleteKnowledgeGraph,
  searchKnowledgeGraphs,
};