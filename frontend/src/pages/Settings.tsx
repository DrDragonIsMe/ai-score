import React, { useState, useEffect } from 'react';
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
  Snackbar
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Science as TestIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { settingsApi } from '../api/settings';

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
  const [tabValue, setTabValue] = useState(0);
  const [models, setModels] = useState<AIModel[]>([]);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingModel, setEditingModel] = useState<AIModel | null>(null);
  const [testingModel, setTestingModel] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

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
    fetchModels();
    fetchSystemInfo();
  }, []);

  const fetchModels = async () => {
    try {
      setLoading(true);
      const response = await settingsApi.getAIModels();
      setModels(response.data.models || []);
    } catch (error) {
      showSnackbar('获取AI模型列表失败', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchSystemInfo = async () => {
    try {
      const response = await settingsApi.getSystemInfo();
      setSystemInfo(response.data);
    } catch (error) {
      console.error('获取系统信息失败:', error);
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error') => {
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
    } catch (error) {
      showSnackbar(editingModel ? 'AI模型更新失败' : 'AI模型创建失败', 'error');
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

                    <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                      <Button
                        size="small"
                        startIcon={testingModel === model.id ? <CircularProgress size={16} /> : <TestIcon />}
                        onClick={() => handleTestModel(model.id)}
                        disabled={testingModel === model.id}
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