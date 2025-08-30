// 用户相关类型
export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface AuthResponse {
  access_token: string;
  user: User;
}

// 学科和知识点类型
export interface Subject {
  id: number;
  name: string;
  description?: string;
  icon?: string;
  color?: string;
  created_at: string;
}

export interface KnowledgePoint {
  id: number;
  subject_id: number;
  name: string;
  description?: string;
  difficulty_level: number;
  parent_id?: number;
  prerequisites: number[];
  created_at: string;
}

// 题目相关类型
export interface Question {
  id: number;
  subject_id: number;
  knowledge_point_ids: number[];
  question_type: 'single_choice' | 'multiple_choice' | 'fill_blank' | 'essay' | 'true_false';
  difficulty_level: number;
  content: string;
  options?: string[];
  correct_answer: string | string[];
  explanation?: string;
  created_at: string;
}

export interface UserAnswer {
  question_id: number;
  user_answer: string | string[];
  is_correct: boolean;
  time_spent: number;
  created_at: string;
}

// 诊断相关类型
export interface DiagnosisSession {
  id: number;
  user_id: number;
  subject_id: number;
  status: 'pending' | 'in_progress' | 'completed';
  total_questions: number;
  answered_questions: number;
  accuracy_rate?: number;
  created_at: string;
  completed_at?: string;
}

export interface DiagnosisResult {
  id: number;
  session_id: number;
  overall_score: number;
  knowledge_mastery: Record<number, number>;
  weak_points: number[];
  strong_points: number[];
  recommendations: string[];
  created_at: string;
}

// 学习路径类型
export interface LearningPath {
  id: number;
  user_id: number;
  subject_id: number;
  name: string;
  description?: string;
  target_knowledge_points: number[];
  estimated_duration: number;
  difficulty_progression: number[];
  status: 'active' | 'completed' | 'paused';
  progress: number;
  created_at: string;
}

export interface StudyRecord {
  id: number;
  user_id: number;
  knowledge_point_id: number;
  study_duration: number;
  mastery_level: number;
  notes?: string;
  created_at: string;
}

// 记忆卡片类型
export interface MemoryCard {
  id: number;
  user_id: number;
  knowledge_point_id: number;
  front_content: string;
  back_content: string;
  difficulty: number;
  next_review_date: string;
  review_count: number;
  success_count: number;
  created_at: string;
}

export interface ReviewRecord {
  id: number;
  card_id: number;
  user_id: number;
  review_result: 'easy' | 'good' | 'hard' | 'again';
  response_time: number;
  next_interval: number;
  created_at: string;
}

export interface ReviewReminder {
  id: string;
  userId: string;
  cardId: string;
  reminderTime: Date;
  isCompleted: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface MemoryStats {
  totalCards: number;
  reviewedToday: number;
  averageMastery: number;
  streakDays: number;
  totalReviews: number;
  accuracy: number;
}

// 考试相关类型
export interface ExamSession {
  id: number;
  user_id: number;
  subject_id: number;
  exam_type: 'practice' | 'formal';
  total_questions: number;
  correct_answers: number;
  score: number;
  time_spent: number;
  started_at: string;
  completed_at?: string;
}

// 错题相关类型
export interface MistakeRecord {
  id: number;
  user_id: number;
  question_id: number;
  subject_id: number;
  user_answer: string | string[];
  correct_answer: string | string[];
  mistake_type: string;
  analysis?: string;
  is_resolved: boolean;
  review_count: number;
  is_mastered: boolean;
  question_content: string;
  notes?: string;
  difficulty_level: number;
  created_at: string;
}

// 学习统计类型
export interface LearningMetric {
  id: number;
  user_id: number;
  metric_type: string;
  metric_value: number;
  period_start: string;
  period_end: string;
  subject_id?: number;
  created_at: string;
}

export interface PerformanceSnapshot {
  id: number;
  user_id: number;
  snapshot_type: string;
  overall_score: number;
  metrics_summary: Record<string, any>;
  period_start: string;
  period_end: string;
  created_at: string;
}

// API响应类型
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// 通用类型
export interface SelectOption {
  label: string;
  value: string | number;
}

export interface ChartData {
  name: string;
  value: number;
  [key: string]: any;
}