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

// 预定义主题样式 - 淡雅和谐配色版本
export const themeStyles = {
  default: {
    name: '淡雅扁平',
    colors: {
      primary: '#6b7c95', // 温和的蓝灰色
      secondary: '#9bb0c7', // 柔和的次要色
      accent: '#d4dde8', // 淡雅的强调色
    }
  },
  blue: {
    name: '海洋蓝',
    colors: {
      primary: '#4a90e2', // 柔和的蓝色
      secondary: '#7bb3f0', // 淡雅的天蓝色
      accent: '#b8d4f1', // 浅蓝色强调
    }
  },
  green: {
    name: '自然绿',
    colors: {
      primary: '#5cb85c', // 温和的绿色
      secondary: '#7cc77c', // 柔和的浅绿
      accent: '#a8d8a8', // 淡绿色强调
    }
  },
  purple: {
    name: '优雅紫',
    colors: {
      primary: '#8e7cc3', // 温和的紫色
      secondary: '#a695d1', // 柔和的浅紫
      accent: '#c4b5e0', // 淡紫色强调
    }
  },
  orange: {
    name: '活力橙',
    colors: {
      primary: '#f0ad4e', // 温和的橙色
      secondary: '#f4c171', // 柔和的浅橙
      accent: '#f8d7a3', // 淡橙色强调
    }
  },
  tencent: {
    name: '腾讯会议',
    colors: {
      primary: '#4a7ba7', // 温和的企业蓝
      secondary: '#6fa8d3', // 柔和的浅蓝
      accent: '#9bc5e4', // 淡蓝色强调
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

// 将十六进制颜色转换为RGB
const hexToRgb = (hex: string): { r: number; g: number; b: number } | null => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null;
};

// 获取仪表盘颜色配置
const getDashboardColors = (themeName: string, mode: 'light' | 'dark') => {
  const baseColors = {
    light: {
      success: '#52c41a',
      warning: '#faad14', 
      orange: '#fa541c',
      purple: '#722ed1',
      cyan: '#13c2c2'
    },
    dark: {
      success: '#73d13d',
      warning: '#ffc53d',
      orange: '#ff7a45', 
      purple: '#b37feb',
      cyan: '#36cfc9'
    }
  };

  // 根据主题调整颜色
  const colors = baseColors[mode];
  
  switch (themeName) {
    case '海洋蓝':
      return {
        ...colors,
        success: mode === 'dark' ? '#5cdbd3' : '#13c2c2',
        cyan: mode === 'dark' ? '#87e8de' : '#36cfc9'
      };
    case '自然绿':
      return {
        ...colors,
        success: mode === 'dark' ? '#95de64' : '#73d13d',
        orange: mode === 'dark' ? '#ffa940' : '#fa8c16'
      };
    case '活力橙':
      return {
        ...colors,
        orange: mode === 'dark' ? '#ffb366' : '#ff7a45',
        warning: mode === 'dark' ? '#ffd666' : '#ffc53d'
      };
    case '优雅紫':
      return {
        ...colors,
        purple: mode === 'dark' ? '#d3adf7' : '#b37feb',
        success: mode === 'dark' ? '#b7eb8f' : '#95de64'
      };
    default:
      return colors;
  }
};

// 应用CSS变量到文档根元素
const applyCSSVariables = (config: ThemeConfig, actualMode: 'light' | 'dark') => {
  if (typeof document === 'undefined') return;
  
  const root = document.documentElement;
  const style = themeStyles[config.style];
  const colors = config.customColors || style.colors;
  
  // 应用主色调
  const primaryColor = colors.primary || style.colors.primary;
  const secondaryColor = colors.secondary || style.colors.secondary;
  const accentColor = colors.accent || style.colors.accent;
  
  root.style.setProperty('--primary-color', primaryColor);
  root.style.setProperty('--secondary-color', secondaryColor);
  root.style.setProperty('--accent-color', accentColor);
  
  // 设置主色调的RGB值（用于透明度计算）
  const primaryRgb = hexToRgb(primaryColor);
  const secondaryRgb = hexToRgb(secondaryColor);
  const accentRgb = hexToRgb(accentColor);
  
  if (primaryRgb) {
    root.style.setProperty('--primary-color-rgb', `${primaryRgb.r}, ${primaryRgb.g}, ${primaryRgb.b}`);
  }
  if (secondaryRgb) {
    root.style.setProperty('--secondary-color-rgb', `${secondaryRgb.r}, ${secondaryRgb.g}, ${secondaryRgb.b}`);
  }
  if (accentRgb) {
    root.style.setProperty('--accent-color-rgb', `${accentRgb.r}, ${accentRgb.g}, ${accentRgb.b}`);
  }
  
  // 设置仪表盘专用颜色变量 - 根据主题和模式调整
    const dashboardColors = getDashboardColors(style.name, actualMode);
    root.style.setProperty('--success-color', dashboardColors.success);
    root.style.setProperty('--warning-color', dashboardColors.warning);
    root.style.setProperty('--orange-color', dashboardColors.orange);
    root.style.setProperty('--purple-color', dashboardColors.purple);
    root.style.setProperty('--cyan-color', dashboardColors.cyan);
  
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
    
    // 统一按钮样式 - 暗色主题，淡雅和谐配色
    const primaryColor = colors.primary || style.colors.primary;
    const secondaryColor = colors.secondary || style.colors.secondary;
    const accentColor = colors.accent || style.colors.accent;
    
    root.style.setProperty('--button-primary-bg', primaryColor);
    root.style.setProperty('--button-primary-hover', `color-mix(in srgb, ${primaryColor} 85%, white)`);
    root.style.setProperty('--button-primary-active', `color-mix(in srgb, ${primaryColor} 90%, white)`);
    
    root.style.setProperty('--button-secondary-bg', 'rgba(255, 255, 255, 0.06)');
    root.style.setProperty('--button-secondary-hover', 'rgba(255, 255, 255, 0.10)');
    root.style.setProperty('--button-secondary-border', 'rgba(255, 255, 255, 0.15)');
    root.style.setProperty('--button-secondary-color', secondaryColor);
    
    root.style.setProperty('--button-text-bg', 'transparent');
    root.style.setProperty('--button-text-hover', `color-mix(in srgb, ${primaryColor} 10%, transparent)`);
    root.style.setProperty('--button-text-color', primaryColor);
    
    root.style.setProperty('--button-ghost-border', `color-mix(in srgb, ${primaryColor} 40%, transparent)`);
    root.style.setProperty('--button-ghost-hover', `color-mix(in srgb, ${primaryColor} 8%, transparent)`);
    root.style.setProperty('--button-ghost-color', primaryColor);
    
    root.style.setProperty('--button-link-color', primaryColor);
    root.style.setProperty('--button-link-hover', `color-mix(in srgb, ${primaryColor} 85%, white)`);
    
    root.style.setProperty('--button-danger-bg', '#ff4d4f');
    root.style.setProperty('--button-danger-hover', '#ff7875');
    
    root.style.setProperty('--button-success-bg', accentColor);
    root.style.setProperty('--button-success-hover', `color-mix(in srgb, ${accentColor} 85%, white)`);
    
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
    
    // 统一按钮样式 - 亮色主题，淡雅和谐配色
    const primaryColor = colors.primary || style.colors.primary;
    const secondaryColor = colors.secondary || style.colors.secondary;
    const accentColor = colors.accent || style.colors.accent;
    
    root.style.setProperty('--button-primary-bg', primaryColor);
    root.style.setProperty('--button-primary-hover', `color-mix(in srgb, ${primaryColor} 85%, black)`);
    root.style.setProperty('--button-primary-active', `color-mix(in srgb, ${primaryColor} 90%, black)`);
    
    root.style.setProperty('--button-secondary-bg', 'rgba(0, 0, 0, 0.03)');
    root.style.setProperty('--button-secondary-hover', 'rgba(0, 0, 0, 0.06)');
    root.style.setProperty('--button-secondary-border', 'rgba(0, 0, 0, 0.08)');
    root.style.setProperty('--button-secondary-color', secondaryColor);
    
    root.style.setProperty('--button-text-bg', 'transparent');
    root.style.setProperty('--button-text-hover', `color-mix(in srgb, ${primaryColor} 8%, transparent)`);
    root.style.setProperty('--button-text-color', primaryColor);
    
    root.style.setProperty('--button-ghost-border', `color-mix(in srgb, ${primaryColor} 30%, transparent)`);
    root.style.setProperty('--button-ghost-hover', `color-mix(in srgb, ${primaryColor} 5%, transparent)`);
    root.style.setProperty('--button-ghost-color', primaryColor);
    
    root.style.setProperty('--button-link-color', primaryColor);
    root.style.setProperty('--button-link-hover', `color-mix(in srgb, ${primaryColor} 85%, black)`);
    
    root.style.setProperty('--button-danger-bg', '#ff4d4f');
    root.style.setProperty('--button-danger-hover', '#ff7875');
    
    root.style.setProperty('--button-success-bg', accentColor);
    root.style.setProperty('--button-success-hover', `color-mix(in srgb, ${accentColor} 85%, black)`);
    
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