import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { settingsApi } from '../services/settings';
import { type SubjectInitProgress } from '../api/settings';

interface SubjectInitState {
  // 状态
  initProgress: SubjectInitProgress | null;
  isInitializing: boolean;
  progressInterval: NodeJS.Timeout | null;
  forceUpdate: boolean;
  taskId: string | null;
  
  // 状态设置函数
  setInitProgress: (progress: SubjectInitProgress | null) => void;
  setIsInitializing: (initializing: boolean) => void;
  setProgressInterval: (interval: NodeJS.Timeout | null) => void;
  setForceUpdate: (force: boolean) => void;
  setTaskId: (taskId: string | null) => void;
  
  // 业务方法
  startSubjectInitialization: (forceUpdate?: boolean, showSnackbar?: (message: string, severity: 'success' | 'error' | 'warning' | 'info') => void) => Promise<{ success: boolean; message: string; severity: 'success' | 'error' | 'warning' }>;
  stopSubjectInitialization: (showSnackbar?: (message: string, severity: 'success' | 'error' | 'warning' | 'info') => void) => { success: boolean; message: string; severity: 'success' | 'error' | 'warning' };
  clearInitializationProgress: (showSnackbar?: (message: string, severity: 'success' | 'error' | 'warning' | 'info') => void) => Promise<{ success: boolean; message: string; severity: 'success' | 'error' | 'warning' }>;
  checkAndRestoreInitializationState: (showSnackbar?: (message: string, severity: 'success' | 'error' | 'warning' | 'info') => void) => Promise<void>;
  
  // 清理函数
  cleanup: () => void;
}

export const useSubjectInitStore = create<SubjectInitState>()(
  persist(
    (set, get) => ({
      // 初始状态
      initProgress: null,
      isInitializing: false,
      progressInterval: null,
      forceUpdate: false,
      taskId: null,
      
      // 基础Actions
      setInitProgress: (progress: SubjectInitProgress | null) => set({ initProgress: progress }),
      setIsInitializing: (initializing: boolean) => set({ isInitializing: initializing }),
      setProgressInterval: (interval: NodeJS.Timeout | null) => {
        const currentInterval = get().progressInterval;
        if (currentInterval) {
          clearInterval(currentInterval);
        }
        set({ progressInterval: interval });
      },
      setForceUpdate: (force: boolean) => set({ forceUpdate: force }),
      setTaskId: (taskId: string | null) => set({ taskId }),
      
      // 启动学科初始化
      startSubjectInitialization: async (forceUpdate = false, showSnackbar?: (message: string, severity: 'success' | 'error' | 'warning' | 'info') => void) => {
        const state = get();
        const { setIsInitializing, setInitProgress, setProgressInterval, setTaskId } = state;
        
        try {
          setIsInitializing(true);
          setInitProgress(null); // 清空之前的进度
          
          const response = await settingsApi.initializeSubjects({ force_update: forceUpdate });
          
          // 检查响应是否包含task_id
          if (response.data && response.data.task_id) {
            const taskId = response.data.task_id;
            setTaskId(taskId);
            
            // 开始轮询进度
            const interval = setInterval(async () => {
              try {
                const progressResponse = await settingsApi.getInitializationProgress(taskId);
                const progress = progressResponse.data;
                setInitProgress(progress);
                
                if (progress.status === 'completed' || progress.status === 'failed' || progress.status === 'waiting_for_conflicts') {
                  const currentState = get();
                  const currentInterval = currentState.progressInterval;
                  if (currentInterval) {
                    clearInterval(currentInterval);
                  }
                  setProgressInterval(null);
                  setIsInitializing(false);
                  setTaskId(null);
                  
                  if (progress.status === 'waiting_for_conflicts') {
                    // 处理冲突情况 - 这里只更新状态，UI组件负责处理用户交互
                    return;
                  }
                }
              } catch (error: any) {
                console.error('获取初始化进度失败:', error);
                const currentState = get();
                const currentInterval = currentState.progressInterval;
                if (currentInterval) {
                  clearInterval(currentInterval);
                }
                setProgressInterval(null);
                setIsInitializing(false);
                setTaskId(null);
              }
            }, 2000); // 每2秒轮询一次
            
            setProgressInterval(interval);
            return { success: true, message: '学科初始化已启动', severity: 'success' as const };
          } else {
            // 如果没有task_id，说明是同步执行，直接显示结果
            setIsInitializing(false);
            if (response.data && response.data.success) {
              return {
                success: true,
                message: `学科初始化完成！创建了 ${response.data.created_count || 0} 个学科，更新了 ${response.data.updated_count || 0} 个学科`,
                severity: 'success' as const
              };
            } else {
              return {
                success: false,
                message: response.data?.message || '学科初始化失败',
                severity: 'error' as const
              };
            }
          }
        } catch (error: any) {
          setIsInitializing(false);
          console.error('启动学科初始化失败:', error);
          
          // 检查是否是冲突错误（409状态码）
          if (error.response?.status === 409 && error.response?.data?.conflicts) {
            // 返回冲突信息，让UI组件处理
            return {
              success: false,
              message: 'conflicts_detected',
              severity: 'warning' as const,
              conflicts: error.response.data.conflicts
            } as any;
          }
          
          let errorMessage = '启动学科初始化失败';
          if (error.response?.data?.message) {
            errorMessage = error.response.data.message;
          } else if (error.message) {
            errorMessage = error.message;
          }
          
          return { success: false, message: errorMessage, severity: 'error' as const };
        }
      },
      
      // 停止学科初始化
      stopSubjectInitialization: (showSnackbar?: (message: string, severity: 'success' | 'error' | 'warning' | 'info') => void) => {
        const state = get();
        const { progressInterval, setProgressInterval, setIsInitializing, setInitProgress, setTaskId } = state;
        
        if (progressInterval) {
          clearInterval(progressInterval);
          setProgressInterval(null);
        }
        setIsInitializing(false);
        setInitProgress(null);
        setTaskId(null);
        
        return { success: true, message: '已停止监控初始化进度', severity: 'success' as const };
      },
      
      // 清除初始化进度记录
      clearInitializationProgress: async (showSnackbar?: (message: string, severity: 'success' | 'error' | 'warning' | 'info') => void) => {
        const state = get();
        const { initProgress, setInitProgress, setTaskId } = state;
        
        if (initProgress?.task_id) {
          try {
            await settingsApi.clearProgress(initProgress.task_id);
            setInitProgress(null);
            setTaskId(null);
            return { success: true, message: '进度记录已清除', severity: 'success' as const };
          } catch (error: any) {
            return {
              success: false,
              message: error.response?.data?.message || '清除进度记录失败',
              severity: 'error' as const
            };
          }
        }
        
        return { success: false, message: '没有可清除的进度记录', severity: 'warning' as const };
      },
      
      // 检查并恢复初始化状态
      checkAndRestoreInitializationState: async (showSnackbar?: (message: string, severity: 'success' | 'error' | 'warning' | 'info') => void) => {
        const state = get();
        const { setInitProgress, setIsInitializing, setProgressInterval, setTaskId } = state;
        
        try {
          const savedTaskId = state.taskId;
          if (savedTaskId) {
            const progressResponse = await settingsApi.getInitializationProgress(savedTaskId);
            const progress = progressResponse.data;
            
            if (progress && (progress.status === 'running' || progress.status === 'pending')) {
              setInitProgress(progress);
              setIsInitializing(true);
              
              // 重新开始轮询
              const interval = setInterval(async () => {
                try {
                  const progressResponse = await settingsApi.getInitializationProgress(savedTaskId);
                  const progress = progressResponse.data;
                  setInitProgress(progress);
                  
                  if (progress.status === 'completed' || progress.status === 'failed' || progress.status === 'waiting_for_conflicts') {
                    const currentState = get();
                    const currentInterval = currentState.progressInterval;
                    if (currentInterval) {
                      clearInterval(currentInterval);
                    }
                    setProgressInterval(null);
                    setIsInitializing(false);
                    setTaskId(null);
                    
                    // 显示完成或失败消息
                    if (showSnackbar) {
                      if (progress.status === 'completed') {
                        showSnackbar(`学科初始化完成！创建了 ${progress.created_count || 0} 个学科，更新了 ${progress.updated_count || 0} 个学科`, 'success');
                      } else if (progress.status === 'failed') {
                        showSnackbar(progress.message || '学科初始化失败', 'error');
                      }
                    }
                  }
                } catch (error) {
                  console.error('恢复进度轮询失败:', error);
                  const currentState = get();
                  const currentInterval = currentState.progressInterval;
                  if (currentInterval) {
                    clearInterval(currentInterval);
                  }
                  setProgressInterval(null);
                  setIsInitializing(false);
                  setTaskId(null);
                }
              }, 2000);
              
              setProgressInterval(interval);
            } else {
              // 任务已完成或失败，清除本地存储
              setTaskId(null);
            }
          }
        } catch (error) {
          console.error('检查初始化状态失败:', error);
          setTaskId(null);
        }
      },
      
      // 清理方法
      cleanup: () => {
        const state = get();
        const { progressInterval, setProgressInterval } = state;
        if (progressInterval) {
          clearInterval(progressInterval);
          setProgressInterval(null);
        }
      }
    }),
    {
      name: 'subject-init-store',
      storage: createJSONStorage(() => localStorage),
      // 只持久化必要的状态
      partialize: (state) => ({
        taskId: state.taskId,
        forceUpdate: state.forceUpdate,
        initProgress: state.initProgress,
        isInitializing: state.isInitializing
      }),
      // 恢复时重新检查状态
      onRehydrateStorage: () => (state) => {
        if (state) {
          // 页面刷新后重新检查初始化状态
          setTimeout(() => {
            state.checkAndRestoreInitializationState();
          }, 100);
        }
      }
    }
  )
);

// 导出清理函数，用于应用卸载时清理
export const cleanupSubjectInitStore = () => {
  const store = useSubjectInitStore.getState();
  store.cleanup();
};