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

export interface ConversationItem {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  starred: boolean;
  archived?: boolean;
  messageCount?: number;
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
  
  // 会话管理相关
  conversations: ConversationItem[];
  currentConversationId: string | null;
  conversationsLoading: boolean;
  
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
  
  // 会话管理操作
  setConversations: (conversations: ConversationItem[]) => void;
  setCurrentConversationId: (id: string | null) => void;
  setConversationsLoading: (loading: boolean) => void;
  loadConversations: () => Promise<void>;
  createConversation: (title?: string) => Promise<string | null>;
  updateConversation: (id: string, updates: Partial<ConversationItem>) => Promise<boolean>;
  deleteConversation: (id: string) => Promise<boolean>;
  toggleConversationStar: (id: string) => Promise<boolean>;
  searchConversations: (keyword: string) => Promise<ConversationItem[]>;
  
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
      
      // 会话管理初始状态
      conversations: [],
      currentConversationId: null,
      conversationsLoading: false,
      
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
      
      // 会话管理方法
      setConversations: (conversations: ConversationItem[]) => set({ conversations }),
      setCurrentConversationId: (id: string | null) => set({ currentConversationId: id }),
      setConversationsLoading: (loading: boolean) => set({ conversationsLoading: loading }),
      
      loadConversations: async () => {
        try {
          set({ conversationsLoading: true });
          const token = localStorage.getItem('token');
          if (!token) {
            console.warn('未找到认证token');
            return;
          }
          
          const response = await fetch('/api/ai-assistant/conversations', {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          });
          
          if (response.ok) {
            const result = await response.json();
            if (result.success && result.data) {
              const conversations = result.data.conversations.map((conv: any) => ({
                id: conv.id.toString(),
                title: conv.title,
                lastMessage: conv.last_message || '',
                timestamp: new Date(conv.updated_at),
                starred: conv.starred,
                archived: conv.archived,
                messageCount: conv.message_count || 0,
              }));
              set({ conversations });
            }
          }
        } catch (error) {
          console.error('加载会话列表失败:', error);
        } finally {
          set({ conversationsLoading: false });
        }
      },
      
      createConversation: async (title = '新对话') => {
        try {
          const token = localStorage.getItem('token');
          if (!token) {
            console.warn('未找到认证token');
            return null;
          }
          
          const response = await fetch('/api/ai-assistant/conversations', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ title }),
          });
          
          if (response.ok) {
            const result = await response.json();
            if (result.success && result.data) {
              const newConversation: ConversationItem = {
                id: result.data.id.toString(),
                title: result.data.title,
                lastMessage: '',
                timestamp: new Date(result.data.created_at),
                starred: false,
                archived: false,
                messageCount: 0,
              };
              
              set((state) => ({
                conversations: [newConversation, ...state.conversations],
                currentConversationId: newConversation.id,
              }));
              
              return newConversation.id;
            }
          }
        } catch (error) {
          console.error('创建会话失败:', error);
        }
        return null;
      },
      
      updateConversation: async (id: string, updates: Partial<ConversationItem>) => {
        try {
          const token = localStorage.getItem('token');
          if (!token) {
            console.warn('未找到认证token');
            return false;
          }
          
          const response = await fetch(`/api/ai-assistant/conversations/${id}`, {
            method: 'PUT',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(updates),
          });
          
          if (response.ok) {
            set((state) => ({
              conversations: state.conversations.map((conv) =>
                conv.id === id ? { ...conv, ...updates } : conv
              ),
            }));
            return true;
          }
        } catch (error) {
          console.error('更新会话失败:', error);
        }
        return false;
      },
      
      deleteConversation: async (id: string) => {
        try {
          const token = localStorage.getItem('token');
          if (!token) {
            console.warn('未找到认证token');
            return false;
          }
          
          const response = await fetch(`/api/ai-assistant/conversations/${id}`, {
            method: 'DELETE',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          });
          
          if (response.ok) {
            set((state) => ({
              conversations: state.conversations.filter((conv) => conv.id !== id),
              currentConversationId: state.currentConversationId === id ? null : state.currentConversationId,
            }));
            return true;
          }
        } catch (error) {
          console.error('删除会话失败:', error);
        }
        return false;
      },
      
      toggleConversationStar: async (id: string) => {
        try {
          const token = localStorage.getItem('token');
          if (!token) {
            console.warn('未找到认证token');
            return false;
          }
          
          const response = await fetch(`/api/ai-assistant/conversations/${id}/star`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          });
          
          if (response.ok) {
            const result = await response.json();
            if (result.success && result.data) {
              const starred = result.data.starred;
              set((state) => ({
                conversations: state.conversations.map((conv) =>
                  conv.id === id ? { ...conv, starred } : conv
                ),
              }));
              return true;
            }
          }
        } catch (error) {
          console.error('切换收藏状态失败:', error);
        }
        return false;
      },
      
      searchConversations: async (keyword: string) => {
        try {
          const token = localStorage.getItem('token');
          if (!token) {
            console.warn('未找到认证token');
            return [];
          }
          
          const response = await fetch(`/api/ai-assistant/conversations/search?keyword=${encodeURIComponent(keyword)}`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          });
          
          if (response.ok) {
            const result = await response.json();
            if (result.success && result.data) {
              return result.data.conversations.map((conv: any) => ({
                id: conv.id.toString(),
                title: conv.title,
                lastMessage: conv.last_message || '',
                timestamp: new Date(conv.updated_at),
                starred: conv.starred,
                archived: conv.archived,
                messageCount: conv.message_count || 0,
              }));
            }
          }
        } catch (error) {
          console.error('搜索会话失败:', error);
        }
        return [];
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
          currentConversationId: null,
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
        conversations: state.conversations,
        currentConversationId: state.currentConversationId,
      }),
    }
  )
);