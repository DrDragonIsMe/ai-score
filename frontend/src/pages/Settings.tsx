import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  Chip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  Divider,
  IconButton,
  Tooltip,
  CircularProgress,
  Snackbar,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Grid,
  Paper
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Science as TestIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  School as SchoolIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { type SubjectInitProgress } from '../api/settings';
import { useAuthStore } from '../stores/authStore';
import { useSubjectInitStore } from '../stores/subjectInitStore';
import settingsApi from '../services/settings';

interface AIModel {
  id: string;
  name: string;
  model_type: string;
  model_id: string;
  api_key: string;
  api_base_url: string;
  max_tokens: number;
  temperature: number;
  top_p: number;
  frequency_penalty: number;
  presence_penalty: number;
  supports_streaming: boolean;
  supports_function_calling: boolean;
  supports_vision: boolean;
  max_requests_per_minute: number;
  max_tokens_per_minute: number;
  cost_per_1k_input_tokens: number;
  cost_per_1k_output_tokens: number;
  is_active: boolean;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

interface SystemInfo {
  version: string;
  environment: string;
  database_status: string;
  ai_service_status: string;
  total_models: number;
  active_models: number;
  default_model: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const Settings: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated, logout, user } = useAuthStore();
  const [tabValue, setTabValue] = useState(0);
  const [models, setModels] = useState<AIModel[]>([]);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingModel, setEditingModel] = useState<AIModel | null>(null);
  const [testingModel, setTestingModel] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' | 'warning' | 'info' });

  // 格式化时长显示
  const formatDuration = (startTime: string, endTime?: string) => {
    try {
      // 确保时间字符串格式正确
      const start = new Date(startTime);
      const end = endTime ? new Date(endTime) : new Date();
      
      // 检查时间是否有效
      if (isNaN(start.getTime()) || isNaN(end.getTime())) {
        return '时间格式错误';
      }
      
      const durationMs = end.getTime() - start.getTime();
      
      // 如果时间差为负数，说明数据有问题
      if (durationMs < 0) {
        return '时间数据异常';
      }
      
      const totalSeconds = Math.floor(durationMs / 1000);
      const hours = Math.floor(totalSeconds / 3600);
      const minutes = Math.floor((totalSeconds % 3600) / 60);
      const seconds = totalSeconds % 60;
      
      if (hours > 0) {
        return `${hours}小时${minutes}分钟${seconds}秒`;
      } else if (minutes > 0) {
        return `${minutes}分钟${seconds}秒`;
      } else {
        return `${seconds}秒`;
      }
    } catch (error) {
      console.error('时间格式化错误:', error, { startTime, endTime });
      return '时间计算错误';
    }
  };

  // 计算预计完成时间
  const getEstimatedCompletionTime = (startTime: string, progressPercent: number) => {
    try {
      if (progressPercent <= 0) return '计算中...';
      if (progressPercent >= 100) return '即将完成';
      
      const start = new Date(startTime);
      const now = new Date();
      
      // 检查时间是否有效
      if (isNaN(start.getTime())) {
        return '开始时间无效';
      }
      
      const elapsed = now.getTime() - start.getTime();
      
      // 如果已用时间为负数或过小，说明数据有问题
      if (elapsed <= 0) {
        return '计算中...';
      }
      
      // 根据当前进度估算总时间
      const totalEstimated = (elapsed / progressPercent) * 100;
      const remaining = totalEstimated - elapsed;
      
      if (remaining <= 0) return '即将完成';
      
      const estimatedEnd = new Date(now.getTime() + remaining);
      return estimatedEnd.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch (error) {
      console.error('预计完成时间计算错误:', error, { startTime, progressPercent });
      return '计算错误';
    }
  };
  
  // 使用全局状态管理学科初始化
  const {
    initProgress,
    isInitializing,
    forceUpdate,
    setForceUpdate,
    startSubjectInitialization,
    stopSubjectInitialization,
    clearInitializationProgress,
    checkAndRestoreInitializationState,
    cleanup
  } = useSubjectInitStore();
  
  // 检查是否为管理员
  const isAdmin = user?.role === 'admin';



  const [formData, setFormData] = useState({
    name: '',
    model_type: 'openai',
    model_id: '',
    api_key: '',
    api_base_url: '',
    max_tokens: 4000,
    temperature: 0.7,
    top_p: 1.0,
    frequency_penalty: 0.0,
    presence_penalty: 0.0,
    supports_streaming: true,
    supports_function_calling: false,
    supports_vision: false,
    max_requests_per_minute: 60,
    max_tokens_per_minute: 60000,
    cost_per_1k_input_tokens: 0.001,
    cost_per_1k_output_tokens: 0.002,
    is_active: true
  });

  useEffect(() => {
    // 检查用户是否已登录
    if (!isAuthenticated) {
      showSnackbar('请先登录', 'error');
      navigate('/login');
      return;
    }
    
    fetchModels();
    fetchSystemInfo();
    if (isAdmin) {
      checkAndRestoreInitializationState(showSnackbar);
    }
  }, [isAuthenticated, navigate, isAdmin, checkAndRestoreInitializationState]);

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  const fetchModels = async () => {
    try {
      setLoading(true);
      const response = await settingsApi.getAIModels();
      setModels(response.data.models || []);
    } catch (error: any) {
      if (error.response?.status === 401) {
        showSnackbar('登录已过期，请重新登录', 'error');
        logout();
        setTimeout(() => {
          navigate('/login');
        }, 1500);
      } else {
        showSnackbar('获取AI模型列表失败', 'error');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchSystemInfo = async () => {
    try {
      const response = await settingsApi.getSystemInfo();
      setSystemInfo(response.data);
    } catch (error: any) {
      if (error.response?.status === 401) {
        showSnackbar('登录已过期，请重新登录', 'error');
        logout();
        setTimeout(() => {
          navigate('/login');
        }, 1500);
      } else {
        console.error('获取系统信息失败:', error);
      }
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'warning' | 'info') => {
    setSnackbar({ open: true, message, severity });
  };





  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleOpenDialog = async (model?: AIModel) => {
    if (model) {
      try {
        // 获取完整的模型信息（包含API密钥）
        const response = await settingsApi.getAIModel(model.id);
        const fullModel = response.data;
        
        setEditingModel(model);
        setFormData({
          name: fullModel.model_name || '',
          model_type: fullModel.model_type || 'openai',
          model_id: fullModel.model_id || '',
          api_key: fullModel.api_key || '',
          api_base_url: fullModel.api_base_url || '',
          max_tokens: fullModel.max_tokens || 4000,
          temperature: fullModel.temperature || 0.7,
          top_p: fullModel.top_p || 1.0,
          frequency_penalty: fullModel.frequency_penalty || 0.0,
          presence_penalty: fullModel.presence_penalty || 0.0,
          supports_streaming: fullModel.supports_streaming ?? true,
          supports_function_calling: fullModel.supports_function_calling ?? false,
          supports_vision: fullModel.supports_vision ?? false,
          max_requests_per_minute: fullModel.max_requests_per_minute || 60,
          max_tokens_per_minute: fullModel.max_tokens_per_minute || 60000,
          cost_per_1k_input_tokens: fullModel.cost_per_1k_input_tokens || 0.001,
          cost_per_1k_output_tokens: fullModel.cost_per_1k_output_tokens || 0.002,
          is_active: fullModel.is_active ?? true
        });
      } catch (error) {
        showSnackbar('获取模型详情失败', 'error');
        return;
      }
    } else {
      setEditingModel(null);
      setFormData({
        name: '',
        model_type: 'openai',
        model_id: '',
        api_key: '',
        api_base_url: '',
        max_tokens: 4000,
        temperature: 0.7,
        top_p: 1.0,
        frequency_penalty: 0.0,
        presence_penalty: 0.0,
        supports_streaming: true,
        supports_function_calling: false,
        supports_vision: false,
        max_requests_per_minute: 60,
        max_tokens_per_minute: 60000,
        cost_per_1k_input_tokens: 0.001,
        cost_per_1k_output_tokens: 0.002,
        is_active: true
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingModel(null);
  };

  const handleSaveModel = async () => {
    try {
      if (editingModel) {
        await settingsApi.updateAIModel(editingModel.id, formData);
        showSnackbar('AI模型更新成功', 'success');
      } else {
        await settingsApi.createAIModel(formData);
        showSnackbar('AI模型创建成功', 'success');
      }
      handleCloseDialog();
      fetchModels();
      fetchSystemInfo();
    } catch (error: any) {
      console.error('AI模型操作失败:', error);
      const errorMessage = error.response?.data?.message || error.message || (editingModel ? 'AI模型更新失败' : 'AI模型创建失败');
      showSnackbar(errorMessage, 'error');
    }
  };

  const handleDeleteModel = async (modelId: string) => {
    if (window.confirm('确定要删除这个AI模型吗？')) {
      try {
        await settingsApi.deleteAIModel(modelId);
        showSnackbar('AI模型删除成功', 'success');
        fetchModels();
        fetchSystemInfo();
      } catch (error) {
        showSnackbar('AI模型删除失败', 'error');
      }
    }
  };

  const handleTestModel = async (modelId: string) => {
    try {
      setTestingModel(modelId);
      const response = await settingsApi.testAIModel(modelId);
      showSnackbar('AI模型测试成功', 'success');
    } catch (error) {
      showSnackbar('AI模型测试失败', 'error');
    } finally {
      setTestingModel(null);
    }
  };

  const handleSetDefault = async (modelId: string) => {
    try {
      await settingsApi.setDefaultAIModel(modelId);
      showSnackbar('默认模型设置成功', 'success');
      fetchModels();
      fetchSystemInfo();
    } catch (error) {
      showSnackbar('默认模型设置失败', 'error');
    }
  };

  const handleToggleActive = async (modelId: string) => {
    try {
      await settingsApi.toggleAIModelActive(modelId);
      showSnackbar('模型状态切换成功', 'success');
      fetchModels();
      fetchSystemInfo();
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || '模型状态切换失败';
      showSnackbar(errorMessage, 'error');
    }
  };

  const handleFormChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h4" gutterBottom>
        系统设置
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="AI模型管理" />
          <Tab label="系统信息" />
          {isAdmin && <Tab label="学科初始化" />}
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">AI模型配置</Typography>
          <Box>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchModels}
              sx={{ mr: 2 }}
            >
              刷新
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => handleOpenDialog()}
            >
              添加模型
            </Button>
          </Box>
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' }, gap: 3 }}>
            {models.map((model) => (
              <Box key={model.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Typography variant="h6" component="div">
                        {model.name}
                        {model.is_default && (
                          <Chip
                            label="默认"
                            color="primary"
                            size="small"
                            sx={{ ml: 1 }}
                          />
                        )}
                      </Typography>
                      <Box>
                        <Tooltip title={model.is_default ? '已是默认模型' : '设为默认模型'}>
                          <IconButton
                            size="small"
                            onClick={() => handleSetDefault(model.id)}
                            disabled={model.is_default}
                          >
                            {model.is_default ? <StarIcon color="primary" /> : <StarBorderIcon />}
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </Box>

                    <Typography color="text.secondary" gutterBottom>
                      {model.model_type} - {model.model_id}
                    </Typography>

                    <Box sx={{ mb: 2 }}>
                      <Chip
                        label={model.is_active ? '活跃' : '停用'}
                        color={model.is_active ? 'success' : 'default'}
                        size="small"
                      />
                      {model.supports_streaming && (
                        <Chip label="流式" size="small" sx={{ ml: 1 }} />
                      )}
                      {model.supports_function_calling && (
                        <Chip label="函数调用" size="small" sx={{ ml: 1 }} />
                      )}
                      {model.supports_vision && (
                        <Chip label="视觉" size="small" sx={{ ml: 1 }} />
                      )}
                    </Box>

                    <Typography variant="body2" color="text.secondary">
                      最大令牌: {model.max_tokens}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      温度: {model.temperature}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      成本: ${model.cost_per_1k_input_tokens}/${model.cost_per_1k_output_tokens} per 1K tokens
                    </Typography>

                    <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      <Button
                        size="small"
                        startIcon={testingModel === model.id ? <CircularProgress size={16} /> : <TestIcon />}
                        onClick={() => handleTestModel(model.id)}
                        disabled={testingModel === model.id || !model.is_active}
                      >
                        测试
                      </Button>
                      <Button
                        size="small"
                        startIcon={<EditIcon />}
                        onClick={() => handleOpenDialog(model)}
                      >
                        编辑
                      </Button>
                      <Button
                        size="small"
                        color={model.is_active ? 'warning' : 'success'}
                        onClick={() => handleToggleActive(model.id)}
                      >
                        {model.is_active ? '禁用' : '启用'}
                      </Button>
                      <Button
                        size="small"
                        color="error"
                        startIcon={<DeleteIcon />}
                        onClick={() => handleDeleteModel(model.id)}
                        disabled={model.is_default}
                      >
                        删除
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Box>
            ))}
          </Box>
        )}
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Typography variant="h6" gutterBottom>
          系统信息
        </Typography>
        {systemInfo && (
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 3 }}>
            <Box>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    基本信息
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    版本: {systemInfo.version}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    环境: {systemInfo.environment}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    数据库状态: {systemInfo.database_status}
                  </Typography>
                  <Typography variant="body2">
                    AI服务状态: {systemInfo.ai_service_status}
                  </Typography>
                </CardContent>
              </Card>
            </Box>
            <Box>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    AI模型统计
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    总模型数: {systemInfo.total_models}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    活跃模型数: {systemInfo.active_models}
                  </Typography>
                  <Typography variant="body2">
                    默认模型: {systemInfo.default_model}
                  </Typography>
                </CardContent>
              </Card>
            </Box>
          </Box>
        )}
      </TabPanel>

      {/* 学科初始化标签页 */}
        {isAdmin && tabValue === 2 && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              <SchoolIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              学科初始化
            </Typography>
          
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="body1" color="text.secondary" gutterBottom>
                初始化九大学科的基础数据，包括学科结构、知识点和题目等。此操作将从外部数据源抓取最新的学科信息。
              </Typography>
              
              <Box sx={{ mt: 2, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={isInitializing ? <StopIcon /> : <PlayIcon />}
                  onClick={isInitializing ? () => stopSubjectInitialization(showSnackbar) : () => startSubjectInitialization(forceUpdate, showSnackbar)}
                  disabled={loading}
                >
                  {isInitializing ? '停止初始化' : '开始初始化'}
                </Button>
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={forceUpdate}
                      onChange={(e) => setForceUpdate(e.target.checked)}
                      disabled={isInitializing}
                    />
                  }
                  label="强制更新现有学科"
                />
                
                {initProgress && (
                  <Button
                    variant="outlined"
                    onClick={() => clearInitializationProgress(showSnackbar)}
                    disabled={isInitializing}
                  >
                    清除进度记录
                  </Button>
                )}
              </Box>
            </CardContent>
          </Card>

          {/* 初始化进度显示 */}
          {initProgress && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {isInitializing ? <CircularProgress size={20} /> : 
                   initProgress.status === 'completed' ? <CheckCircleIcon color="success" /> :
                   initProgress.status === 'failed' ? <ErrorIcon color="error" /> :
                   <WarningIcon color="warning" />}
                  学科初始化进度
                </Typography>
                
                {/* 状态概览 */}
                <Box sx={{ mb: 3, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      状态: {initProgress.status === 'running' ? '🔄 进行中' : 
                             initProgress.status === 'completed' ? '✅ 已完成' : 
                             initProgress.status === 'failed' ? '❌ 失败' : 
                             initProgress.status === 'waiting_for_conflicts' ? '⚠️ 等待处理冲突' :
                             initProgress.status}
                    </Typography>
                    <Typography variant="h6" color="primary">
                      {initProgress.progress_percent ? initProgress.progress_percent.toFixed(1) : '0.0'}%
                    </Typography>
                  </Box>
                  
                  <LinearProgress 
                    variant="determinate" 
                    value={initProgress.progress_percent || 0} 
                    sx={{ height: 10, borderRadius: 5, mb: 2 }}
                  />
                  
                  <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' }, gap: 2, mb: 2 }}>
                    <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'success.light', borderRadius: 1 }}>
                      <Typography variant="h6" color="success.contrastText">
                        {initProgress.created_count || 0}
                      </Typography>
                      <Typography variant="body2" color="success.contrastText">
                        已创建
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'info.light', borderRadius: 1 }}>
                      <Typography variant="h6" color="info.contrastText">
                        {initProgress.updated_count || 0}
                      </Typography>
                      <Typography variant="body2" color="info.contrastText">
                        已更新
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'warning.light', borderRadius: 1 }}>
                      <Typography variant="h6" color="warning.contrastText">
                        {initProgress.conflicts ? initProgress.conflicts.length : 0}
                      </Typography>
                      <Typography variant="body2" color="warning.contrastText">
                        冲突数
                      </Typography>
                    </Box>
                  </Box>
                  
                  {initProgress.message && (
                    <Typography variant="body2" color="text.secondary" sx={{ 
                      p: 1, 
                      bgcolor: 'action.hover', 
                      borderRadius: 1,
                      fontFamily: 'monospace',
                      fontSize: '0.875rem'
                    }}>
                      💬 {initProgress.message}
                    </Typography>
                  )}
                  
                  {initProgress.current_subject && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="body2" color="primary" sx={{ fontWeight: 'bold' }}>
                        🎯 当前学科: {initProgress.current_subject}
                      </Typography>
                      {initProgress.current_stage && (
                        <Typography variant="body2" color="text.secondary" sx={{ ml: 2 }}>
                          📋 处理阶段: {initProgress.current_stage}
                        </Typography>
                      )}
                      {initProgress.stage_progress !== undefined && (
                        <Box sx={{ ml: 2, mt: 0.5 }}>
                          <Typography variant="caption" color="text.secondary">
                            阶段进度: {initProgress.stage_progress}%
                          </Typography>
                          <LinearProgress 
                            variant="determinate" 
                            value={initProgress.stage_progress} 
                            sx={{ height: 4, borderRadius: 2, mt: 0.5 }}
                          />
                        </Box>
                      )}
                      {initProgress.download_source && (
                        <Typography variant="body2" color="text.secondary" sx={{ ml: 2 }}>
                          📥 数据来源: {initProgress.download_source}
                        </Typography>
                      )}
                    </Box>
                  )}
                </Box>

                {/* 已完成的学科 */}
                {initProgress.completed_subjects && initProgress.completed_subjects.length > 0 && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <CheckCircleIcon color="success" />
                      已完成学科 ({initProgress.completed_subjects.length})
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, maxHeight: 200, overflow: 'auto', p: 1, bgcolor: 'success.light', borderRadius: 1 }}>
                      {initProgress.completed_subjects.map((subject, index) => (
                        <Chip
                          key={index}
                          label={`${subject.subject_code} - ${subject.name || ''}`}
                          color="success"
                          size="small"
                          variant="outlined"
                          sx={{ bgcolor: 'success.main', color: 'success.contrastText' }}
                        />
                      ))}
                    </Box>
                  </Box>
                )}

                {/* 冲突信息 */}
                {initProgress.conflicts && initProgress.conflicts.length > 0 && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <WarningIcon color="warning" />
                      发现冲突 ({initProgress.conflicts.length})
                    </Typography>
                    <Box sx={{ maxHeight: 200, overflow: 'auto', p: 2, bgcolor: 'warning.light', borderRadius: 1 }}>
                      {initProgress.conflicts.map((conflict, index) => (
                        <Box key={index} sx={{ mb: 1, p: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
                          <Typography variant="body2" fontWeight="bold">
                            {conflict.subject_code}
                          </Typography>
                          {conflict.conflicts && conflict.conflicts.length > 0 && (
                            <Typography variant="body2" color="text.secondary" sx={{ ml: 2 }}>
                              冲突项: {conflict.conflicts.join(', ')}
                            </Typography>
                          )}
                        </Box>
                      ))}
                    </Box>
                  </Box>
                )}

                {/* 错误信息 */}
                {initProgress.errors && initProgress.errors.length > 0 && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <ErrorIcon color="error" />
                      处理错误 ({initProgress.errors.length})
                    </Typography>
                    <Box sx={{ maxHeight: 200, overflow: 'auto', p: 2, bgcolor: 'error.light', borderRadius: 1 }}>
                      {initProgress.errors.map((error, index) => (
                        <Box key={index} sx={{ mb: 1, p: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
                          <Typography variant="body2" fontWeight="bold" color="error">
                            {error.subject_code}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ ml: 2, fontFamily: 'monospace' }}>
                            {error.error || '未知错误'}
                          </Typography>
                        </Box>
                      ))}
                    </Box>
                  </Box>
                )}



                {/* 时间信息 */}
                <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                  <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' }, gap: 2 }}>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        🕐 开始时间: {initProgress.start_time ? new Date(initProgress.start_time).toLocaleString() : '等待开始...'}
                      </Typography>
                      {initProgress.end_time && (
                        <Typography variant="body2" color="text.secondary">
                          🏁 结束时间: {new Date(initProgress.end_time).toLocaleString()}
                        </Typography>
                      )}
                    </Box>
                    <Box>
                      {initProgress.task_id && (
                        <Typography variant="body2" color="text.secondary">
                          🆔 任务ID: {initProgress.task_id.substring(0, 8)}...
                        </Typography>
                      )}
                      {initProgress.start_time && (
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            ⏱️ 运行时长: {formatDuration(initProgress.start_time, initProgress.end_time)}
                          </Typography>
                          {initProgress.status === 'running' && initProgress.progress_percent > 0 && (
                            <Typography variant="body2" color="text.secondary">
                              ⏰ 预计完成时间: {getEstimatedCompletionTime(initProgress.start_time, initProgress.progress_percent)}
                            </Typography>
                          )}
                        </Box>
                      )}
                    </Box>
                  </Box>
                </Box>
               </CardContent>
             </Card>
           )}
          </Box>
        )}

      {/* AI模型编辑对话框 */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingModel ? '编辑AI模型' : '添加AI模型'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' }, gap: 2, mt: 1 }}>
            <Box>
              <TextField
                fullWidth
                label="模型名称"
                value={formData.name}
                onChange={(e) => handleFormChange('name', e.target.value)}
              />
            </Box>
            <Box>
              <FormControl fullWidth>
                <InputLabel>模型类型</InputLabel>
                <Select
                  value={formData.model_type}
                  label="模型类型"
                  onChange={(e) => handleFormChange('model_type', e.target.value)}
                >
                  <MenuItem value="openai">OpenAI</MenuItem>
                  <MenuItem value="anthropic">Anthropic</MenuItem>
                  <MenuItem value="google">Google</MenuItem>
                  <MenuItem value="azure">Azure OpenAI</MenuItem>
                  <MenuItem value="custom">自定义</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box sx={{ gridColumn: '1 / -1' }}>
              <TextField
                fullWidth
                label="模型ID"
                value={formData.model_id}
                onChange={(e) => handleFormChange('model_id', e.target.value)}
                helperText="例如: gpt-4, claude-3-sonnet, gemini-pro"
              />
            </Box>
            <Box sx={{ gridColumn: '1 / -1' }}>
              <TextField
                fullWidth
                label="API密钥"
                type="password"
                value={formData.api_key}
                onChange={(e) => handleFormChange('api_key', e.target.value)}
              />
            </Box>
            <Box sx={{ gridColumn: '1 / -1' }}>
              <TextField
                fullWidth
                label="API基础URL"
                value={formData.api_base_url}
                onChange={(e) => handleFormChange('api_base_url', e.target.value)}
                helperText="留空使用默认URL"
              />
            </Box>
            
            <Box sx={{ gridColumn: '1 / -1' }}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                模型参数
              </Typography>
            </Box>
            
            <Box>
              <TextField
                fullWidth
                label="最大令牌数"
                type="number"
                value={formData.max_tokens}
                onChange={(e) => handleFormChange('max_tokens', parseInt(e.target.value))}
              />
            </Box>
            <Box>
              <TextField
                fullWidth
                label="温度"
                type="number"
                inputProps={{ step: 0.1, min: 0, max: 2 }}
                value={formData.temperature}
                onChange={(e) => handleFormChange('temperature', parseFloat(e.target.value))}
              />
            </Box>
            <Box>
              <TextField
                fullWidth
                label="Top P"
                type="number"
                inputProps={{ step: 0.1, min: 0, max: 1 }}
                value={formData.top_p}
                onChange={(e) => handleFormChange('top_p', parseFloat(e.target.value))}
              />
            </Box>
            <Box>
              <TextField
                fullWidth
                label="频率惩罚"
                type="number"
                inputProps={{ step: 0.1, min: -2, max: 2 }}
                value={formData.frequency_penalty}
                onChange={(e) => handleFormChange('frequency_penalty', parseFloat(e.target.value))}
              />
            </Box>
            
            <Box sx={{ gridColumn: '1 / -1' }}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                功能支持
              </Typography>
            </Box>
          </Box>
          
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' }, gap: 2, mt: 2 }}>
            <Box>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.supports_streaming}
                    onChange={(e) => handleFormChange('supports_streaming', e.target.checked)}
                  />
                }
                label="支持流式输出"
              />
            </Box>
            <Box>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.supports_function_calling}
                    onChange={(e) => handleFormChange('supports_function_calling', e.target.checked)}
                  />
                }
                label="支持函数调用"
              />
            </Box>
            <Box>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.supports_vision}
                    onChange={(e) => handleFormChange('supports_vision', e.target.checked)}
                  />
                }
                label="支持视觉理解"
              />
            </Box>
          </Box>
          
          <Box sx={{ mt: 2 }}>
            <Divider sx={{ my: 2 }} />
            <Typography variant="h6" gutterBottom>
              性能与成本
            </Typography>
          </Box>
          
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' }, gap: 2, mt: 2 }}>
            <Box>
              <TextField
                fullWidth
                label="每分钟最大请求数"
                type="number"
                value={formData.max_requests_per_minute}
                onChange={(e) => handleFormChange('max_requests_per_minute', parseInt(e.target.value))}
              />
            </Box>
            <Box>
              <TextField
                fullWidth
                label="每分钟最大令牌数"
                type="number"
                value={formData.max_tokens_per_minute}
                onChange={(e) => handleFormChange('max_tokens_per_minute', parseInt(e.target.value))}
              />
            </Box>
            <Box>
              <TextField
                fullWidth
                label="输入成本 (每1K令牌)"
                type="number"
                inputProps={{ step: 0.001 }}
                value={formData.cost_per_1k_input_tokens}
                onChange={(e) => handleFormChange('cost_per_1k_input_tokens', parseFloat(e.target.value))}
              />
            </Box>
            <Box>
              <TextField
                fullWidth
                label="输出成本 (每1K令牌)"
                type="number"
                inputProps={{ step: 0.001 }}
                value={formData.cost_per_1k_output_tokens}
                onChange={(e) => handleFormChange('cost_per_1k_output_tokens', parseFloat(e.target.value))}
              />
            </Box>
            
            <Box sx={{ gridColumn: '1 / -1', mt: 2 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_active}
                    onChange={(e) => handleFormChange('is_active', e.target.checked)}
                  />
                }
                label="启用此模型"
              />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>取消</Button>
          <Button onClick={handleSaveModel} variant="contained">
            {editingModel ? '更新' : '创建'}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
      >
        <Alert
          onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Settings;