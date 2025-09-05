import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// 主题类型定义
export type ThemeMode = 'light' | 'dark' | 'auto';
export type ThemeStyle = 'default' | 'blue' | 'green' | 'purple' | 'orange' | 'tencent';

// 主题配置接口
export interface ThemeConfig {
  mode: ThemeMode;
  style: ThemeStyle;
  customColors?: {
    primary?: string;
    secondary?: string;
    accent?: string;
  };
}

// 预定义主题样式 - 优化对比度版本
export const themeStyles = {
  default: {
    name: '淡雅扁平',
    colors: {
      primary: '#5a6b85', // 加深主色调，提升对比度
      secondary: '#8fa2b8', // 适度加深次要色
      accent: '#c2cdd8', // 保持淡雅但增强可见性
    }
  },
  blue: {
    name: '海洋蓝',
    colors: {
      primary: '#1677ff', // 稍微加深蓝色
      secondary: '#0fb5b5', // 增强青色对比度
      accent: '#2db7b7', // 优化强调色
    }
  },
  green: {
    name: '自然绿',
    colors: {
      primary: '#47b317', // 加深绿色主色调
      secondary: '#65c932', // 保持活力但增强对比
      accent: '#7ed957', // 优化强调色可读性
    }
  },
  purple: {
    name: '优雅紫',
    colors: {
      primary: '#6b2bc7', // 加深紫色主色调
      secondary: '#8347d4', // 增强次要色对比度
      accent: '#a66ee8', // 保持优雅但更清晰
    }
  },
  orange: {
    name: '活力橙',
    colors: {
      primary: '#e67e14', // 加深橙色主色调
      secondary: '#f29c3a', // 增强次要色对比度
      accent: '#ffab7a', // 优化强调色可读性
    }
  },
  tencent: {
    name: '腾讯会议',
    colors: {
      primary: '#1a4472', // 稍微加深蓝色
      secondary: '#00c49a', // 增强青绿色对比度
      accent: '#4285d4', // 优化强调色
    }
  }
};

// 主题状态接口
interface ThemeState {
  // 当前主题配置
  config: ThemeConfig;
  
  // 系统是否支持暗色模式
  systemSupportsDark: boolean;
  
  // 当前实际应用的主题模式（考虑auto模式）
  actualMode: 'light' | 'dark';
  
  // Actions
  setThemeMode: (mode: ThemeMode) => void;
  setThemeStyle: (style: ThemeStyle) => void;
  setCustomColors: (colors: ThemeConfig['customColors']) => void;
  resetTheme: () => void;
  
  // 内部方法
  updateActualMode: () => void;
  applyTheme: () => void;
}

// 默认主题配置
const defaultThemeConfig: ThemeConfig = {
  mode: 'light',
  style: 'default',
};

// 检测系统是否支持暗色模式
const checkSystemDarkMode = (): boolean => {
  if (typeof window === 'undefined') return false;
  return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
};

// 应用CSS变量到文档根元素
const applyCSSVariables = (config: ThemeConfig, actualMode: 'light' | 'dark') => {
  if (typeof document === 'undefined') return;
  
  const root = document.documentElement;
  const style = themeStyles[config.style];
  const colors = config.customColors || style.colors;
  
  // 应用主色调
  root.style.setProperty('--primary-color', colors.primary || style.colors.primary);
  root.style.setProperty('--secondary-color', colors.secondary || style.colors.secondary);
  root.style.setProperty('--accent-color', colors.accent || style.colors.accent);
  
  // 根据模式应用背景和文字颜色 - 优化对比度版本
  if (actualMode === 'dark') {
    // 暗色主题 - 增强对比度
    root.style.setProperty('--background-primary', '#0f0f0f'); // 更深的主背景
    root.style.setProperty('--background-secondary', '#1a1a1a'); // 增强层次感
    root.style.setProperty('--background-tertiary', '#242424'); // 优化三级背景
    root.style.setProperty('--background-soft', '#2d2d2d'); // 柔和背景更清晰
    root.style.setProperty('--background-card', 'rgba(26, 26, 26, 0.98)'); // 提升卡片对比度
    
    root.style.setProperty('--text-primary', '#ffffff'); // 保持纯白主文字
    root.style.setProperty('--text-secondary', '#e0e0e0'); // 增强次要文字对比度
    root.style.setProperty('--text-tertiary', '#a0a0a0'); // 提升三级文字可读性
    root.style.setProperty('--text-disabled', '#666666'); // 优化禁用文字对比度
    
    root.style.setProperty('--border-color', 'rgba(255, 255, 255, 0.15)'); // 增强边框可见性
    root.style.setProperty('--shadow-light', '0 2px 8px rgba(0, 0, 0, 0.2)');
    root.style.setProperty('--shadow-medium', '0 4px 12px rgba(0, 0, 0, 0.3)');
    root.style.setProperty('--shadow-elegant', '0 6px 24px rgba(0, 0, 0, 0.4)');
    
    // 统一色块样式 - 暗色主题
    root.style.setProperty('--block-success-bg', 'rgba(76, 175, 80, 0.15)');
    root.style.setProperty('--block-success-border', 'rgba(76, 175, 80, 0.3)');
    root.style.setProperty('--block-success-text', '#81c784');
    root.style.setProperty('--block-info-bg', 'rgba(33, 150, 243, 0.15)');
    root.style.setProperty('--block-info-border', 'rgba(33, 150, 243, 0.3)');
    root.style.setProperty('--block-info-text', '#64b5f6');
    root.style.setProperty('--block-warning-bg', 'rgba(255, 152, 0, 0.15)');
    root.style.setProperty('--block-warning-border', 'rgba(255, 152, 0, 0.3)');
    root.style.setProperty('--block-warning-text', '#ffb74d');
    root.style.setProperty('--block-error-bg', 'rgba(244, 67, 54, 0.15)');
    root.style.setProperty('--block-error-border', 'rgba(244, 67, 54, 0.3)');
    root.style.setProperty('--block-error-text', '#e57373');
    
    // 统一按钮样式 - 暗色主题
    root.style.setProperty('--button-primary-bg', colors.primary || style.colors.primary);
    root.style.setProperty('--button-primary-hover', `color-mix(in srgb, ${colors.primary || style.colors.primary} 85%, white)`);
    root.style.setProperty('--button-secondary-bg', 'rgba(255, 255, 255, 0.08)');
    root.style.setProperty('--button-secondary-hover', 'rgba(255, 255, 255, 0.12)');
    root.style.setProperty('--button-secondary-border', 'rgba(255, 255, 255, 0.2)');
    
    // 设置Ant Design暗色主题
    root.setAttribute('data-theme', 'dark');
  } else {
    // 亮色主题 - 淡雅扁平化风格，优化对比度
    root.style.setProperty('--background-primary', 'linear-gradient(135deg, #ffffff 0%, #f6f8fa 100%)');
    root.style.setProperty('--background-secondary', 'linear-gradient(180deg, #f6f8fa 0%, #e8ecf0 100%)');
    root.style.setProperty('--background-tertiary', '#f0f2f5'); // 稍微加深三级背景
    root.style.setProperty('--background-soft', '#e6e9ed'); // 优化柔和背景
    root.style.setProperty('--background-card', 'rgba(255, 255, 255, 0.95)'); // 提升卡片对比度
    root.style.setProperty('--background-gradient', 'linear-gradient(180deg, #f6f8fa 0%, #e8ecf0 100%)');
    
    // 优化文字对比度 - 保持淡雅但更清晰
    root.style.setProperty('--text-primary', '#2c3338'); // 加深主文字颜色
    root.style.setProperty('--text-secondary', '#4a5258'); // 增强次要文字对比度
    root.style.setProperty('--text-tertiary', '#6c757d'); // 提升三级文字可读性
    root.style.setProperty('--text-disabled', '#adb5bd'); // 优化禁用文字对比度
    
    // 优化边框和阴影
    root.style.setProperty('--border-color', '#d6dce5'); // 增强边框可见性
    root.style.setProperty('--shadow-light', '0 2px 8px rgba(0, 0, 0, 0.08)');
    root.style.setProperty('--shadow-medium', '0 4px 20px rgba(0, 0, 0, 0.12)');
    root.style.setProperty('--shadow-elegant', '0 6px 32px rgba(0, 0, 0, 0.15)');
    root.style.setProperty('--shadow-soft', '0 1px 3px rgba(0, 0, 0, 0.06)');
    
    // 设置边框圆角
    root.style.setProperty('--border-radius', '8px');
    root.style.setProperty('--border-radius-large', '12px');
    
    // 统一色块样式 - 亮色主题
    root.style.setProperty('--block-success-bg', 'rgba(76, 175, 80, 0.08)');
    root.style.setProperty('--block-success-border', 'rgba(76, 175, 80, 0.2)');
    root.style.setProperty('--block-success-text', '#2e7d32');
    root.style.setProperty('--block-info-bg', 'rgba(33, 150, 243, 0.08)');
    root.style.setProperty('--block-info-border', 'rgba(33, 150, 243, 0.2)');
    root.style.setProperty('--block-info-text', '#1565c0');
    root.style.setProperty('--block-warning-bg', 'rgba(255, 152, 0, 0.08)');
    root.style.setProperty('--block-warning-border', 'rgba(255, 152, 0, 0.2)');
    root.style.setProperty('--block-warning-text', '#e65100');
    root.style.setProperty('--block-error-bg', 'rgba(244, 67, 54, 0.08)');
    root.style.setProperty('--block-error-border', 'rgba(244, 67, 54, 0.2)');
    root.style.setProperty('--block-error-text', '#c62828');
    
    // 统一按钮样式 - 亮色主题
    root.style.setProperty('--button-primary-bg', colors.primary || style.colors.primary);
    root.style.setProperty('--button-primary-hover', `color-mix(in srgb, ${colors.primary || style.colors.primary} 85%, black)`);
    root.style.setProperty('--button-secondary-bg', 'rgba(0, 0, 0, 0.04)');
    root.style.setProperty('--button-secondary-hover', 'rgba(0, 0, 0, 0.08)');
    root.style.setProperty('--button-secondary-border', 'rgba(0, 0, 0, 0.12)');
    
    // 设置Ant Design亮色主题
    root.setAttribute('data-theme', 'light');
  }
  
  // 统一字体规范
  root.style.setProperty('--font-family-primary', '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif');
  root.style.setProperty('--font-family-mono', 'SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace');
  
  // 字体大小规范
  root.style.setProperty('--font-size-xs', '12px');
  root.style.setProperty('--font-size-sm', '14px');
  root.style.setProperty('--font-size-base', '16px');
  root.style.setProperty('--font-size-lg', '18px');
  root.style.setProperty('--font-size-xl', '20px');
  root.style.setProperty('--font-size-2xl', '24px');
  root.style.setProperty('--font-size-3xl', '30px');
  
  // 字重规范
  root.style.setProperty('--font-weight-light', '300');
  root.style.setProperty('--font-weight-normal', '400');
  root.style.setProperty('--font-weight-medium', '500');
  root.style.setProperty('--font-weight-semibold', '600');
  root.style.setProperty('--font-weight-bold', '700');
  
  // 行高规范
  root.style.setProperty('--line-height-tight', '1.25');
  root.style.setProperty('--line-height-normal', '1.5');
  root.style.setProperty('--line-height-relaxed', '1.75');
  
  // 标题样式规范
  root.style.setProperty('--heading-color', actualMode === 'dark' ? '#ffffff' : '#1a1a1a');
  root.style.setProperty('--heading-font-weight', '600');
  root.style.setProperty('--subheading-color', actualMode === 'dark' ? '#e0e0e0' : '#4a5258');
  root.style.setProperty('--subheading-font-weight', '500');
  
  // 列表样式规范
  root.style.setProperty('--list-item-padding', '12px 16px');
  root.style.setProperty('--list-item-hover-bg', actualMode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)');
  root.style.setProperty('--list-item-active-bg', actualMode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.04)');
  root.style.setProperty('--list-divider-color', actualMode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)');
};

// 创建主题store
export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      config: defaultThemeConfig,
      systemSupportsDark: checkSystemDarkMode(),
      actualMode: 'light',
      
      setThemeMode: (mode: ThemeMode) => {
        set((state) => {
          const newConfig = { ...state.config, mode };
          const newState = { ...state, config: newConfig };
          
          // 更新实际模式
          const actualMode = mode === 'auto' 
            ? (state.systemSupportsDark ? 'dark' : 'light')
            : mode as 'light' | 'dark';
          
          newState.actualMode = actualMode;
          
          // 应用主题
          applyCSSVariables(newConfig, actualMode);
          
          return newState;
        });
      },
      
      setThemeStyle: (style: ThemeStyle) => {
        set((state) => {
          const newConfig = { ...state.config, style };
          const newState = { ...state, config: newConfig };
          
          // 应用主题
          applyCSSVariables(newConfig, state.actualMode);
          
          return newState;
        });
      },
      
      setCustomColors: (customColors: ThemeConfig['customColors']) => {
        set((state) => {
          const newConfig = { ...state.config, customColors };
          const newState = { ...state, config: newConfig };
          
          // 应用主题
          applyCSSVariables(newConfig, state.actualMode);
          
          return newState;
        });
      },
      
      resetTheme: () => {
        set((state) => {
          const newState = {
            ...state,
            config: defaultThemeConfig,
            actualMode: 'light' as const
          };
          
          // 应用默认主题
          applyCSSVariables(defaultThemeConfig, 'light');
          
          return newState;
        });
      },
      
      updateActualMode: () => {
        set((state) => {
          if (state.config.mode !== 'auto') return state;
          
          const systemSupportsDark = checkSystemDarkMode();
          const actualMode = systemSupportsDark ? 'dark' : 'light';
          
          if (actualMode !== state.actualMode) {
            applyCSSVariables(state.config, actualMode);
            return {
              ...state,
              systemSupportsDark,
              actualMode
            };
          }
          
          return { ...state, systemSupportsDark };
        });
      },
      
      applyTheme: () => {
        const state = get();
        applyCSSVariables(state.config, state.actualMode);
      },
    }),
    {
      name: 'theme-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ config: state.config }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          // 重新计算实际模式
          const systemSupportsDark = checkSystemDarkMode();
          const actualMode = state.config.mode === 'auto'
            ? (systemSupportsDark ? 'dark' : 'light')
            : state.config.mode as 'light' | 'dark';
          
          state.systemSupportsDark = systemSupportsDark;
          state.actualMode = actualMode;
          
          // 应用主题
          applyCSSVariables(state.config, actualMode);
        }
      },
    }
  )
);

// 监听系统主题变化
if (typeof window !== 'undefined') {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  mediaQuery.addEventListener('change', () => {
    useThemeStore.getState().updateActualMode();
  });
}

// 导出主题工具函数
export const getThemeColors = (style: ThemeStyle, customColors?: ThemeConfig['customColors']) => {
  return customColors || themeStyles[style].colors;
};

export const getCurrentTheme = () => {
  return useThemeStore.getState();
};