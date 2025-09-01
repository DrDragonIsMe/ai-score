import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Table,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  message,
  Tabs,
  Statistic,
  Progress,
  Tooltip,
  Badge
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  DownloadOutlined,
  NodeIndexOutlined,
  FileTextOutlined,
  BarChartOutlined,
  StarOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import KnowledgeGraphViewer from '../components/KnowledgeGraphViewer.tsx';
import ExamPaperManager from '../components/ExamPaperManager.tsx';
import StarMapViewer from '../components/StarMapViewer.tsx';
import { useAuthStore } from '../stores/authStore';

// const { TabPane } = Tabs; // 已弃用，改用items属性
const { Option } = Select;

interface Subject {
  id: string;
  code: string;
  name: string;
  name_en: string;
  description: string;
  category: string;
  grade_range: string[];
  total_score: number;
  paper_count: number;
  last_paper_year: number;
  is_active: boolean;
  sort_order: number;
  chapter_count: number;
  stats?: {
    knowledge_point_count: number;
    exam_paper_count: number;
    knowledge_graph_count: number;
  };
}

interface Statistics {
  basic_stats: {
    chapter_count: number;
    knowledge_point_count: number;
    paper_count: number;
    graph_count: number;
  };
  paper_by_year: Array<{ year: number; count: number }>;
  knowledge_point_by_difficulty: Array<{ difficulty: number; count: number }>;
}

const SubjectManagement: React.FC = () => {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingSubject, setEditingSubject] = useState<Subject | null>(null);
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [initializationProgress, setInitializationProgress] = useState<any>(null);
  const [initializationTaskId, setInitializationTaskId] = useState<string | null>(null);
  const [conflictModalVisible, setConflictModalVisible] = useState(false);
  const [conflicts, setConflicts] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState('list');
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  
  // 检查是否为管理员
  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    fetchSubjects();
  }, []);

  const fetchSubjects = async () => {
    setLoading(true);
    try {
      const response = await api.get('/subjects?include_stats=true');
      setSubjects(response.data);
    } catch (error) {
      message.error('获取学科列表失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async (subjectId: string) => {
    try {
      const response = await api.get(`/subjects/${subjectId}/statistics`);
      setStatistics(response.data);
    } catch (error) {
      message.error('获取统计信息失败');
    }
  };

  const initializeDefaultSubjects = async () => {
    Modal.confirm({
      title: '初始化九大学科',
      content: '此操作将从互联网抓取真题、知识点和考试范围数据，可能需要较长时间。确定要继续吗？',
      onOk: async () => {
        try {
          const response = await api.post('/subjects/initialize-with-crawling', {
            subject_codes: [],
            overwrite_conflicts: false
          });
          const taskId = response.data.task_id;
          setInitializationTaskId(taskId);
          message.success('初始化任务已启动，正在抓取数据...');
          
          // 开始轮询进度
          pollInitializationProgress(taskId);
        } catch (error) {
          console.error('初始化失败:', error);
          message.error('启动初始化失败');
        }
      }
    });
  };

  const pollInitializationProgress = async (taskId: string) => {
    let retryCount = 0;
    const maxRetries = 3;
    
    const poll = async () => {
      try {
        const response = await api.get(`/subjects/initialization-progress/${taskId}`);
        const progress = response.data;
        setInitializationProgress(progress);
        retryCount = 0; // 重置重试计数
        
        if (progress.status === 'completed') {
          message.success('学科初始化完成！');
          fetchSubjects();
          // 保持进度显示3秒后清除
          setTimeout(() => {
            setInitializationProgress(null);
            setInitializationTaskId(null);
          }, 3000);
        } else if (progress.status === 'conflicts_pending') {
          setConflicts(progress.conflicts);
          setConflictModalVisible(true);
        } else if (progress.status === 'failed') {
          message.error(`初始化失败: ${progress.message}`);
          // 保持错误状态显示，不自动清除
        } else if (progress.status === 'running') {
          // 继续轮询
          setTimeout(poll, 2000);
        }
      } catch (error) {
        console.error('获取进度失败:', error);
        retryCount++;
        
        if (retryCount <= maxRetries) {
          // 重试，延长轮询间隔
          setTimeout(poll, 5000);
        } else {
          // 超过最大重试次数，显示错误并停止轮询
          message.error('获取初始化进度失败，请刷新页面重试');
          setInitializationProgress({
            status: 'failed',
            message: '网络连接超时，无法获取进度信息'
          });
        }
      }
    };
    
    poll();
  };

  const clearInitializationProgress = () => {
    setInitializationProgress(null);
    setInitializationTaskId(null);
  };

  const handleSubmit = async (values: any) => {
    try {
      if (editingSubject) {
        await api.put(`/subjects/${editingSubject.id}`, values);
        message.success('更新成功');
      } else {
        await api.post('/subjects', values);
        message.success('创建成功');
      }
      setModalVisible(false);
      setEditingSubject(null);
      form.resetFields();
      fetchSubjects();
    } catch (error) {
      message.error(editingSubject ? '更新失败' : '创建失败');
    }
  };

  const handleEdit = (subject: Subject) => {
    setEditingSubject(subject);
    form.setFieldsValue(subject);
    setModalVisible(true);
  };

  const handleDelete = async (subjectId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个学科吗？此操作不可恢复。',
      onOk: async () => {
        try {
          await api.delete(`/subjects/${subjectId}`);
          message.success('删除成功');
          fetchSubjects();
        } catch (error) {
          message.error('删除失败');
        }
      }
    });
  };

  const handleViewKnowledgeGraph = (subject: Subject) => {
    setSelectedSubject(subject);
    setActiveTab('knowledge-graph');
  };

  const handleViewExamPapers = (subject: Subject) => {
    setSelectedSubject(subject);
    setActiveTab('exam-papers');
  };

  const handleViewStatistics = (subject: Subject) => {
    setSelectedSubject(subject);
    fetchStatistics(subject.id);
    setActiveTab('statistics');
  };

  const handleViewStarMap = (subject: Subject) => {
    setSelectedSubject(subject);
    setActiveTab('star-map');
  };

  const getCategoryColor = (category: string) => {
    const colors = {
      science: 'blue',
      liberal_arts: 'green',
      language: 'orange'
    };
    return colors[category as keyof typeof colors] || 'default';
  };

  const columns = [
    {
      title: '学科名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Subject) => (
        <div>
          <div style={{ fontWeight: 500 }}>{text}</div>
          <div style={{ fontSize: 12, color: '#666' }}>{record.name_en}</div>
        </div>
      )
    },
    {
      title: '学科代码',
      dataIndex: 'code',
      key: 'code',
      render: (text: string) => <Tag color="blue">{text}</Tag>
    },
    {
      title: '类别',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => {
        const categoryNames = {
          science: '理科',
          liberal_arts: '文科',
          language: '语言'
        };
        return (
          <Tag color={getCategoryColor(category)}>
            {categoryNames[category as keyof typeof categoryNames] || category}
          </Tag>
        );
      }
    },
    {
      title: '总分',
      dataIndex: 'total_score',
      key: 'total_score'
    },
    {
      title: '章节数',
      dataIndex: 'chapter_count',
      key: 'chapter_count',
      render: (count: number) => count || 0
    },
    {
      title: '试卷数',
      dataIndex: 'paper_count',
      key: 'paper_count',
      render: (count: number) => count || 0
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Badge
          status={isActive ? 'success' : 'default'}
          text={isActive ? '启用' : '禁用'}
        />
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: Subject) => (
        <Space>
          <Tooltip title="查看知识图谱">
            <Button
              type="text"
              icon={<NodeIndexOutlined />}
              onClick={() => handleViewKnowledgeGraph(record)}
            />
          </Tooltip>
          <Tooltip title="查看试卷">
            <Button
              type="text"
              icon={<FileTextOutlined />}
              onClick={() => handleViewExamPapers(record)}
            />
          </Tooltip>
          <Tooltip title="统计分析">
            <Button
              type="text"
              icon={<BarChartOutlined />}
              onClick={() => handleViewStatistics(record)}
            />
          </Tooltip>
          <Tooltip title="星图视图">
            <Button
              type="text"
              icon={<StarOutlined />}
              onClick={() => handleViewStarMap(record)}
            />
          </Tooltip>
          {isAdmin && (
            <>
              <Button
                type="text"
                icon={<EditOutlined />}
                onClick={() => handleEdit(record)}
              />
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
                onClick={() => handleDelete(record.id)}
              />
            </>
          )}
        </Space>
      )
    }
  ];

  const renderStatistics = () => {
    if (!statistics || !selectedSubject) return null;

    return (
      <div>
        <Card title={`${selectedSubject.name} - 统计信息`} style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={6}>
              <Statistic title="章节数" value={statistics.basic_stats.chapter_count} />
            </Col>
            <Col span={6}>
              <Statistic title="知识点数" value={statistics.basic_stats.knowledge_point_count} />
            </Col>
            <Col span={6}>
              <Statistic title="试卷数" value={statistics.basic_stats.paper_count} />
            </Col>
            <Col span={6}>
              <Statistic title="知识图谱数" value={statistics.basic_stats.graph_count} />
            </Col>
          </Row>
        </Card>

        <Row gutter={16}>
          <Col span={12}>
            <Card title="按年份统计试卷">
              {statistics.paper_by_year.map(item => (
                <div key={item.year} style={{ marginBottom: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>{item.year}年</span>
                    <span>{item.count}份</span>
                  </div>
                  <Progress
                    percent={(item.count / Math.max(...statistics.paper_by_year.map(p => p.count))) * 100}
                    showInfo={false}
                    size="small"
                  />
                </div>
              ))}
            </Card>
          </Col>
          <Col span={12}>
            <Card title="按难度统计知识点">
              {statistics.knowledge_point_by_difficulty.map(item => (
                <div key={item.difficulty} style={{ marginBottom: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>难度 {item.difficulty}</span>
                    <span>{item.count}个</span>
                  </div>
                  <Progress
                    percent={(item.count / Math.max(...statistics.knowledge_point_by_difficulty.map(p => p.count))) * 100}
                    showInfo={false}
                    size="small"
                  />
                </div>
              ))}
            </Card>
          </Col>
        </Row>
      </div>
    );
  };

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          items={[
            {
              key: 'list',
              label: '学科管理',
              children: (
                <>
                  {isAdmin && (
                    <div style={{ marginBottom: 16 }}>
                      <Space>
                        <Button
                          type="primary"
                          icon={<PlusOutlined />}
                          onClick={() => {
                            setEditingSubject(null);
                            form.resetFields();
                            setModalVisible(true);
                          }}
                        >
                          添加学科
                        </Button>
                        <Button
                          icon={<StarOutlined />}
                          onClick={initializeDefaultSubjects}
                          loading={!!initializationProgress && initializationProgress.status === 'running'}
                          disabled={!!initializationProgress && initializationProgress.status === 'running'}
                          type={initializationProgress ? 'default' : 'primary'}
                        >
                          {initializationProgress 
                            ? (initializationProgress.status === 'running' ? '正在初始化...' : '初始化完成') 
                            : '初始化九大学科'
                          }
                        </Button>
                        {initializationProgress && (
                          <div style={{ marginTop: 16, minWidth: 400 }}>
                            <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span style={{ fontWeight: 500 }}>初始化进度</span>
                              <span style={{ fontSize: 14, color: '#666' }}>
                                {initializationProgress.progress_percent}%
                              </span>
                            </div>
                            <Progress 
                              percent={initializationProgress.progress_percent} 
                              status={
                                initializationProgress.status === 'failed' ? 'exception' : 
                                initializationProgress.status === 'completed' ? 'success' : 'active'
                              }
                              strokeColor={
                                initializationProgress.status === 'completed' ? '#52c41a' : 
                                initializationProgress.status === 'failed' ? '#ff4d4f' : '#1890ff'
                              }
                              showInfo={false}
                            />
                            <div style={{ 
                              fontSize: 13, 
                              color: initializationProgress.status === 'failed' ? '#ff4d4f' : '#666', 
                              marginTop: 8,
                              minHeight: 20
                            }}>
                              {initializationProgress.message}
                              {initializationProgress.current_subject && (
                                <span style={{ fontWeight: 500, marginLeft: 8 }}>
                                  当前学科: {initializationProgress.current_subject}
                                </span>
                              )}
                            </div>
                            {initializationProgress.status === 'completed' && (
                               <div style={{ 
                                 marginTop: 12, 
                                 padding: 8, 
                                 backgroundColor: '#f6ffed', 
                                 border: '1px solid #b7eb8f',
                                 borderRadius: 4,
                                 fontSize: 13,
                                 color: '#389e0d',
                                 display: 'flex',
                                 justifyContent: 'space-between',
                                 alignItems: 'center'
                               }}>
                                 <span>✅ 九大学科初始化完成！数据已成功导入系统。</span>
                                 <Button 
                                   size="small" 
                                   type="text" 
                                   onClick={clearInitializationProgress}
                                   style={{ color: '#389e0d' }}
                                 >
                                   清除
                                 </Button>
                               </div>
                             )}
                             {initializationProgress.status === 'failed' && (
                               <div style={{ 
                                 marginTop: 12, 
                                 padding: 8, 
                                 backgroundColor: '#fff2f0', 
                                 border: '1px solid #ffccc7',
                                 borderRadius: 4,
                                 fontSize: 13,
                                 color: '#cf1322',
                                 display: 'flex',
                                 justifyContent: 'space-between',
                                 alignItems: 'center'
                               }}>
                                 <span>❌ 初始化失败，请检查网络连接或联系管理员。</span>
                                 <Button 
                                   size="small" 
                                   type="text" 
                                   onClick={clearInitializationProgress}
                                   style={{ color: '#cf1322' }}
                                 >
                                   清除
                                 </Button>
                               </div>
                             )}
                          </div>
                        )}
                      </Space>
                    </div>
                  )}

                  <Table
                    columns={columns}
                    dataSource={subjects}
                    rowKey="id"
                    loading={loading}
                    pagination={{
                      pageSize: 10,
                      showSizeChanger: true,
                      showQuickJumper: true,
                      showTotal: (total) => `共 ${total} 个学科`
                    }}
                  />
                </>
              )
            },
            {
              key: 'knowledge-graph',
              label: '知识图谱',
              disabled: !selectedSubject,
              children: selectedSubject && (
                <KnowledgeGraphViewer subjectId={selectedSubject.id} />
              )
            },
            {
              key: 'exam-papers',
              label: '试卷管理',
              disabled: !selectedSubject,
              children: selectedSubject && (
                <ExamPaperManager subjectId={selectedSubject.id} />
              )
            },
            {
              key: 'statistics',
              label: '统计分析',
              disabled: !selectedSubject,
              children: renderStatistics()
            },
            {
              key: 'star-map',
              label: '星图视图',
              disabled: !selectedSubject,
              children: selectedSubject && (
                <StarMapViewer subjectId={selectedSubject.id} />
              )
            }
          ]}
        />
      </Card>

      <Modal
        title={editingSubject ? '编辑学科' : '添加学科'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingSubject(null);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="学科名称"
                rules={[{ required: true, message: '请输入学科名称' }]}
              >
                <Input placeholder="如：数学" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="name_en"
                label="英文名称"
              >
                <Input placeholder="如：Mathematics" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="code"
                label="学科代码"
                rules={[{ required: true, message: '请输入学科代码' }]}
              >
                <Input placeholder="如：math" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="category"
                label="学科类别"
                rules={[{ required: true, message: '请选择学科类别' }]}
              >
                <Select placeholder="请选择">
                  <Option value="science">理科</Option>
                  <Option value="liberal_arts">文科</Option>
                  <Option value="language">语言</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="total_score"
                label="总分"
                rules={[{ required: true, message: '请输入总分' }]}
              >
                <InputNumber
                  min={1}
                  max={1000}
                  placeholder="150"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="sort_order"
                label="排序"
              >
                <InputNumber
                  min={0}
                  placeholder="0"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="description"
            label="学科描述"
          >
            <Input.TextArea
              rows={3}
              placeholder="请输入学科描述"
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                {editingSubject ? '更新' : '创建'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="数据冲突处理"
        open={conflictModalVisible}
        onCancel={() => setConflictModalVisible(false)}
        width={800}
        footer={[
          <Button key="cancel" onClick={() => setConflictModalVisible(false)}>
            取消
          </Button>,
          <Button key="skip" onClick={() => setConflictModalVisible(false)}>
            跳过冲突
          </Button>,
          <Button key="overwrite" type="primary" onClick={() => setConflictModalVisible(false)}>
            覆盖数据
          </Button>
        ]}
      >
        <div>
          <p>检测到以下数据冲突，请选择处理方式：</p>
          {conflicts.map((conflict, index) => (
            <Card key={index} title={`学科: ${conflict.subject}`} style={{ marginBottom: 16 }}>
              <div>
                {conflict.conflicts.map((item: any, itemIndex: number) => (
                  <div key={itemIndex} style={{ marginBottom: 8, padding: 8, background: '#f5f5f5', borderRadius: 4 }}>
                    <div><strong>类型：</strong>{item.type}</div>
                    <div><strong>标题：</strong>{item.title}</div>
                    <div><strong>年份：</strong>{item.year}</div>
                    <div><strong>冲突原因：</strong>{item.reason}</div>
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>
      </Modal>
    </div>
  );
};

export default SubjectManagement;