import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// 支持的语言类型
export type Language = 'zh-CN' | 'en-US';

// 翻译文本接口
export interface TranslationTexts {
  // 通用
  common: {
    confirm: string;
    cancel: string;
    save: string;
    delete: string;
    edit: string;
    add: string;
    search: string;
    filter: string;
    reset: string;
    submit: string;
    loading: string;
    success: string;
    error: string;
    warning: string;
    info: string;
    yes: string;
    no: string;
    ok: string;
    close: string;
    back: string;
    next: string;
    previous: string;
    refresh: string;
    export: string;
    import: string;
    download: string;
    upload: string;
    view: string;
    settings: string;
    logout: string;
    login: string;
    register: string;
    profile: string;
    help: string;
    about: string;
  };
  
  // 导航菜单
  menu: {
    dashboard: string;
    subjects: string;
    examPapers: string;
    documents: string;
    diagnosis: string;
    learningPath: string;
    memoryCards: string;
    mistakeBook: string;
    exam: string;
    analytics: string;
    aiAssistant: string;
  };
  
  // 设置页面
  settings: {
    title: string;
    theme: string;
    language: string;
    themeMode: string;
    themeStyle: string;
    lightMode: string;
    darkMode: string;
    autoMode: string;
    defaultTheme: string;
    blueTheme: string;
    greenTheme: string;
    purpleTheme: string;
    orangeTheme: string;
    aiModels: string;
    systemInfo: string;
    subjectInit: string;
  };
  
  // 主题相关
  theme: {
    light: string;
    dark: string;
    auto: string;
    followSystem: string;
    customColors: string;
    primaryColor: string;
    secondaryColor: string;
    accentColor: string;
    resetTheme: string;
    applyTheme: string;
  };
  
  // 语言相关
  language: {
    chinese: string;
    english: string;
    selectLanguage: string;
    languageChanged: string;
  };
  
  // 试卷管理
  examPaper: {
    title: string;
    upload: string;
    download: string;
    parse: string;
    status: string;
    tags: string;
    subject: string;
    createTime: string;
    actions: string;
    parsing: string;
    completed: string;
    failed: string;
    pending: string;
    autoGenerateKG: string;
    autoGenerateKGTooltip: string;
    searchByTag: string;
    noTags: string;
  };
  
  // 文档管理
  document: {
    title: string;
    upload: string;
    category: string;
    size: string;
    uploadTime: string;
    status: string;
    actions: string;
    preview: string;
    vectorize: string;
  };
  
  // AI助手
  aiAssistant: {
    title: string;
    inputPlaceholder: string;
    send: string;
    clear: string;
    thinking: string;
    error: string;
    retry: string;
    copy: string;
    copied: string;
  };
}

// 中文翻译
const zhCNTexts: TranslationTexts = {
  common: {
    confirm: '确认',
    cancel: '取消',
    save: '保存',
    delete: '删除',
    edit: '编辑',
    add: '添加',
    search: '搜索',
    filter: '筛选',
    reset: '重置',
    submit: '提交',
    loading: '加载中...',
    success: '成功',
    error: '错误',
    warning: '警告',
    info: '信息',
    yes: '是',
    no: '否',
    ok: '确定',
    close: '关闭',
    back: '返回',
    next: '下一步',
    previous: '上一步',
    refresh: '刷新',
    export: '导出',
    import: '导入',
    download: '下载',
    upload: '上传',
    view: '查看',
    settings: '设置',
    logout: '退出登录',
    login: '登录',
    register: '注册',
    profile: '个人资料',
    help: '帮助',
    about: '关于',
  },
  
  menu: {
    dashboard: '仪表盘',
    subjects: '学科管理',
    examPapers: '试卷管理',
    documents: '文档管理',
    diagnosis: '学习诊断',
    learningPath: '学习路径',
    memoryCards: '记忆强化',
    mistakeBook: '错题本',
    exam: '考试测评',
    analytics: '数据分析',
    aiAssistant: 'AI助手',
  },
  
  settings: {
    title: '系统设置',
    theme: '主题设置',
    language: '语言设置',
    themeMode: '主题模式',
    themeStyle: '主题风格',
    lightMode: '亮色模式',
    darkMode: '暗色模式',
    autoMode: '跟随系统',
    defaultTheme: '默认蓝色',
    blueTheme: '海洋蓝',
    greenTheme: '自然绿',
    purpleTheme: '优雅紫',
    orangeTheme: '活力橙',
    aiModels: 'AI模型管理',
    systemInfo: '系统信息',
    subjectInit: '学科初始化',
  },
  
  theme: {
    light: '亮色',
    dark: '暗色',
    auto: '自动',
    followSystem: '跟随系统',
    customColors: '自定义颜色',
    primaryColor: '主色调',
    secondaryColor: '辅助色',
    accentColor: '强调色',
    resetTheme: '重置主题',
    applyTheme: '应用主题',
  },
  
  language: {
    chinese: '中文',
    english: 'English',
    selectLanguage: '选择语言',
    languageChanged: '语言已切换',
  },
  
  examPaper: {
    title: '试卷管理',
    upload: '上传试卷',
    download: '下载',
    parse: '解析',
    status: '状态',
    tags: '标签',
    subject: '学科',
    createTime: '创建时间',
    actions: '操作',
    parsing: '解析中',
    completed: '已解析',
    failed: '解析失败',
    pending: '待解析',
    autoGenerateKG: '自动生成知识图谱',
    autoGenerateKGTooltip: '上传后自动为试卷内容生成知识图谱和向量化存储',
    searchByTag: '按标签搜索',
    noTags: '无标签',
  },
  
  document: {
    title: '文档管理',
    upload: '上传文档',
    category: '分类',
    size: '大小',
    uploadTime: '上传时间',
    status: '状态',
    actions: '操作',
    preview: '预览',
    vectorize: '向量化',
  },
  
  aiAssistant: {
    title: 'AI智能助手',
    inputPlaceholder: '请输入您的问题...',
    send: '发送',
    clear: '清空对话',
    thinking: '思考中...',
    error: '出现错误，请重试',
    retry: '重试',
    copy: '复制',
    copied: '已复制',
  },
};

// 英文翻译
const enUSTexts: TranslationTexts = {
  common: {
    confirm: 'Confirm',
    cancel: 'Cancel',
    save: 'Save',
    delete: 'Delete',
    edit: 'Edit',
    add: 'Add',
    search: 'Search',
    filter: 'Filter',
    reset: 'Reset',
    submit: 'Submit',
    loading: 'Loading...',
    success: 'Success',
    error: 'Error',
    warning: 'Warning',
    info: 'Info',
    yes: 'Yes',
    no: 'No',
    ok: 'OK',
    close: 'Close',
    back: 'Back',
    next: 'Next',
    previous: 'Previous',
    refresh: 'Refresh',
    export: 'Export',
    import: 'Import',
    download: 'Download',
    upload: 'Upload',
    view: 'View',
    settings: 'Settings',
    logout: 'Logout',
    login: 'Login',
    register: 'Register',
    profile: 'Profile',
    help: 'Help',
    about: 'About',
  },
  
  menu: {
    dashboard: 'Dashboard',
    subjects: 'Subjects',
    examPapers: 'Exam Papers',
    documents: 'Documents',
    diagnosis: 'Diagnosis',
    learningPath: 'Learning Path',
    memoryCards: 'Memory Cards',
    mistakeBook: 'Mistake Book',
    exam: 'Exam',
    analytics: 'Analytics',
    aiAssistant: 'AI Assistant',
  },
  
  settings: {
    title: 'System Settings',
    theme: 'Theme Settings',
    language: 'Language Settings',
    themeMode: 'Theme Mode',
    themeStyle: 'Theme Style',
    lightMode: 'Light Mode',
    darkMode: 'Dark Mode',
    autoMode: 'Follow System',
    defaultTheme: 'Default Blue',
    blueTheme: 'Ocean Blue',
    greenTheme: 'Nature Green',
    purpleTheme: 'Elegant Purple',
    orangeTheme: 'Vibrant Orange',
    aiModels: 'AI Models',
    systemInfo: 'System Info',
    subjectInit: 'Subject Initialization',
  },
  
  theme: {
    light: 'Light',
    dark: 'Dark',
    auto: 'Auto',
    followSystem: 'Follow System',
    customColors: 'Custom Colors',
    primaryColor: 'Primary Color',
    secondaryColor: 'Secondary Color',
    accentColor: 'Accent Color',
    resetTheme: 'Reset Theme',
    applyTheme: 'Apply Theme',
  },
  
  language: {
    chinese: '中文',
    english: 'English',
    selectLanguage: 'Select Language',
    languageChanged: 'Language Changed',
  },
  
  examPaper: {
    title: 'Exam Papers',
    upload: 'Upload Paper',
    download: 'Download',
    parse: 'Parse',
    status: 'Status',
    tags: 'Tags',
    subject: 'Subject',
    createTime: 'Create Time',
    actions: 'Actions',
    parsing: 'Parsing',
    completed: 'Completed',
    failed: 'Failed',
    pending: 'Pending',
    autoGenerateKG: 'Auto Generate KG',
    autoGenerateKGTooltip: 'Automatically generate knowledge graph and vectorization after upload',
    searchByTag: 'Search by Tag',
    noTags: 'No Tags',
  },
  
  document: {
    title: 'Documents',
    upload: 'Upload Document',
    category: 'Category',
    size: 'Size',
    uploadTime: 'Upload Time',
    status: 'Status',
    actions: 'Actions',
    preview: 'Preview',
    vectorize: 'Vectorize',
  },
  
  aiAssistant: {
    title: 'AI Assistant',
    inputPlaceholder: 'Please enter your question...',
    send: 'Send',
    clear: 'Clear Chat',
    thinking: 'Thinking...',
    error: 'An error occurred, please try again',
    retry: 'Retry',
    copy: 'Copy',
    copied: 'Copied',
  },
};

// 翻译字典
const translations: Record<Language, TranslationTexts> = {
  'zh-CN': zhCNTexts,
  'en-US': enUSTexts,
};

// 国际化状态接口
interface I18nState {
  // 当前语言
  language: Language;
  
  // 当前翻译文本
  texts: TranslationTexts;
  
  // Actions
  setLanguage: (language: Language) => void;
  t: (key: string) => string;
  
  // 内部方法
  updateTexts: () => void;
}

// 默认语言
const defaultLanguage: Language = 'zh-CN';

// 获取嵌套对象的值
const getNestedValue = (obj: any, path: string): string => {
  return path.split('.').reduce((current, key) => current?.[key], obj) || path;
};

// 创建国际化store
export const useI18nStore = create<I18nState>()(
  persist(
    (set, get) => ({
      language: defaultLanguage,
      texts: translations[defaultLanguage],
      
      setLanguage: (language: Language) => {
        set({
          language,
          texts: translations[language],
        });
      },
      
      t: (key: string): string => {
        const { texts } = get();
        return getNestedValue(texts, key);
      },
      
      updateTexts: () => {
        const { language } = get();
        set({ texts: translations[language] });
      },
    }),
    {
      name: 'i18n-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ language: state.language }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.texts = translations[state.language];
        }
      },
    }
  )
);

// 导出翻译函数
export const useTranslation = () => {
  const { t, language, setLanguage } = useI18nStore();
  return { t, language, setLanguage };
};

// 导出支持的语言列表
export const supportedLanguages = [
  { code: 'zh-CN' as Language, name: '中文', nativeName: '中文' },
  { code: 'en-US' as Language, name: 'English', nativeName: 'English' },
];