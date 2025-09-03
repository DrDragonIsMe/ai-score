import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isImage?: boolean;
  imageUrl?: string;
  isPdf?: boolean;
  pdfName?: string;
  documentId?: string;
  questionAnalysis?: {
    difficulty: string;
    keyPoints: string[];
  };
  referencedDocuments?: Array<{
    id: string;
    title: string;
    content_snippet: string;
    relevance_score: number;
  }>;
}

export interface PPTTemplate {
  id: number;
  name: string;
  category: string;
  description: string;
  preview_image?: string;
}

export interface AIStats {
  totalInteractions: number;
  questionsAnswered: number;
  aiAccuracy: number;
  personalizedRecommendations: number;
  aiStudyTime: number;
  intelligentAnalysis: number;
  todayInteractions: number;
}

interface AIAssistantState {
  // 消息相关
  messages: Message[];
  inputValue: string;
  loading: boolean;
  
  // PPT模板相关
  selectedTemplateId: number | null;
  selectedTemplateName: string;
  showPPTTemplateSelector: boolean;
  pptTemplates: PPTTemplate[];
  
  // 统计信息
  aiStats: AIStats;
  
  // 搜索相关
  searchQuery: string;
  searchResults: any[];
  searchLoading: boolean;
  
  // UI状态
  showCamera: boolean;
  uploading: boolean;
  
  // Actions
  setMessages: (messages: Message[] | ((prev: Message[]) => Message[])) => void;
  addMessage: (message: Message) => void;
  setInputValue: (value: string) => void;
  setLoading: (loading: boolean) => void;
  
  setSelectedTemplate: (id: number | null, name: string) => void;
  setShowPPTTemplateSelector: (show: boolean) => void;
  setPptTemplates: (templates: PPTTemplate[]) => void;
  loadPptTemplates: () => Promise<void>;
  addPptTemplate: (template: PPTTemplate) => void;
  
  updateAIStats: (stats: Partial<AIStats>) => void;
  incrementTodayInteractions: () => void;
  
  setSearchQuery: (query: string) => void;
  setSearchResults: (results: any[]) => void;
  setSearchLoading: (loading: boolean) => void;
  
  setShowCamera: (show: boolean) => void;
  setUploading: (uploading: boolean) => void;
  
  // 重置状态
  resetConversation: () => void;
}

const initialAIStats: AIStats = {
  totalInteractions: 0,
  questionsAnswered: 0,
  aiAccuracy: 94,
  personalizedRecommendations: 0,
  aiStudyTime: 0,
  intelligentAnalysis: 0,
  todayInteractions: 0,
};

const initialMessage: Message = {
  id: '1',
  type: 'assistant',
  content: '你好！我是高小分AI学习助手 🤖\n\n我可以帮助你：\n• 📚 解答学习问题\n• 🔍 分析上传的图片和文档\n• 📊 生成PPT演示文稿\n• 💡 提供个性化学习建议\n\n有什么可以帮助你的吗？',
  timestamp: new Date(),
};

export const useAIAssistantStore = create<AIAssistantState>()(
  persist(
    (set, get) => ({
      // 初始状态
      messages: [initialMessage],
      inputValue: '',
      loading: false,
      
      selectedTemplateId: null,
      selectedTemplateName: '',
      showPPTTemplateSelector: false,
      pptTemplates: [],
      
      aiStats: initialAIStats,
      
      searchQuery: '',
      searchResults: [],
      searchLoading: false,
      
      showCamera: false,
      uploading: false,
      
      // Actions
      setMessages: (messages: Message[] | ((prev: Message[]) => Message[])) => {
        set((state) => ({
          messages: typeof messages === 'function' ? messages(state.messages) : messages
        }));
      },
      
      addMessage: (message: Message) => {
        set((state) => ({
          messages: [...state.messages, message]
        }));
      },
      
      setInputValue: (value: string) => set({ inputValue: value }),
      setLoading: (loading: boolean) => set({ loading }),
      
      setSelectedTemplate: (id: number | null, name: string) => {
        set({ selectedTemplateId: id, selectedTemplateName: name });
      },
      
      setShowPPTTemplateSelector: (show: boolean) => set({ showPPTTemplateSelector: show }),
      setPptTemplates: (templates: PPTTemplate[]) => set({ pptTemplates: templates }),
      
      loadPptTemplates: async () => {
        try {
          const response = await fetch('http://localhost:5001/api/ppt-templates/list');
          const result = await response.json();
          if (result.success) {
            set({ pptTemplates: result.data.templates || [] });
          } else {
            // 如果API返回失败，使用默认模板
            set({ pptTemplates: [
              { id: 1, name: '学术报告模板', category: '学术类', description: '适用于学术研究和论文展示' },
              { id: 2, name: '商务汇报模板', category: '商务类', description: '适用于商务会议和项目汇报' },
              { id: 3, name: '教育培训模板', category: '教育类', description: '适用于课程教学和培训展示' },
            ]});
          }
        } catch (error) {
          console.error('加载PPT模板失败:', error);
          // 如果网络请求失败，使用默认模板
          set({ pptTemplates: [
            { id: 1, name: '学术报告模板', category: '学术类', description: '适用于学术研究和论文展示' },
            { id: 2, name: '商务汇报模板', category: '商务类', description: '适用于商务会议和项目汇报' },
            { id: 3, name: '教育培训模板', category: '教育类', description: '适用于课程教学和培训展示' },
          ]});
        }
      },
      
      addPptTemplate: (template: PPTTemplate) => {
        set((state) => ({
          pptTemplates: [...state.pptTemplates, template]
        }));
      },
      
      updateAIStats: (stats: Partial<AIStats>) => {
        set((state) => ({
          aiStats: { ...state.aiStats, ...stats }
        }));
      },
      
      incrementTodayInteractions: () => {
        set((state) => ({
          aiStats: {
            ...state.aiStats,
            todayInteractions: state.aiStats.todayInteractions + 1,
            totalInteractions: state.aiStats.totalInteractions + 1,
          }
        }));
      },
      
      setSearchQuery: (query: string) => set({ searchQuery: query }),
      setSearchResults: (results: any[]) => set({ searchResults: results }),
      setSearchLoading: (loading: boolean) => set({ searchLoading: loading }),
      
      setShowCamera: (show: boolean) => set({ showCamera: show }),
      setUploading: (uploading: boolean) => set({ uploading }),
      
      resetConversation: () => {
        set({
          messages: [initialMessage],
          inputValue: '',
          loading: false,
          selectedTemplateId: null,
          selectedTemplateName: '',
          searchQuery: '',
          searchResults: [],
        });
      },
    }),
    {
      name: 'ai-assistant-storage',
      partialize: (state) => ({
        aiStats: state.aiStats,
        selectedTemplateId: state.selectedTemplateId,
        selectedTemplateName: state.selectedTemplateName,
        pptTemplates: state.pptTemplates,
      }),
    }
  )
);