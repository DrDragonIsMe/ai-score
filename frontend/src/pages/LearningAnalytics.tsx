import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Table,
  Tag,
  Divider,
  Space,
  Typography,
  Spin,
  message,
  Button,
  DatePicker,
  Select,
  Tabs,
  List,
  Avatar,
  Alert
} from 'antd';
import {
  BarChartOutlined,
  TrophyOutlined,
  BookOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LineChartOutlined,
  PieChartOutlined,
  ReloadOutlined,
  BulbOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import dayjs, { Dayjs } from 'dayjs';
import api from '../services/api';

const { Title, Text, Paragraph } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;
const { TabPane } = Tabs;

// 数据接口定义
interface DashboardSummary {
  total_study_time: number;
  total_questions: number;
  accuracy_rate: number;
  knowledge_points_mastered: number;
  weak_points_count: number;
  recent_performance: {
    trend: 'improving' | 'stable' | 'declining';
    change_rate: number;
  };
}

interface LearningProgress {
  subject_progress: Array<{
    subject_name: string;
    progress: number;
    total_time: number;
    mastery_rate: number;
  }>;
  weekly_progress: Array<{
    week: string;
    study_time: number;
    questions_count: number;
    accuracy: number;
  }>;
  overall_trend: 'improving' | 'stable' | 'declining';
}

interface KnowledgeMastery {
  mastered_points: Array<{
    knowledge_point: string;
    mastery_level: number;
    practice_count: number;
    last_practiced: string;
  }>;
  weak_points: Array<{
    knowledge_point: string;
    mastery_level: number;
    error_count: number;
    suggestions: string[];
  }>;
  mastery_distribution: {
    excellent: number;
    good: number;
    average: number;
    poor: number;
  };
}

interface PerformanceTrends {
  accuracy_trend: Array<{
    date: string;
    accuracy: number;
    questions_count: number;
  }>;
  efficiency_trend: Array<{
    date: string;
    avg_time_per_question: number;
    total_questions: number;
  }>;
  subject_performance: Array<{
    subject_name: string;
    accuracy_trend: number;
    efficiency_trend: number;
    recent_accuracy: number;
  }>;
}

interface StudyStatistics {
  daily_stats: Array<{
    date: string;
    study_time: number;
    questions_count: number;
    accuracy: number;
  }>;
  subject_distribution: Array<{
    subject_name: string;
    time_spent: number;
    percentage: number;
  }>;
  peak_hours: Array<{
    hour: number;
    activity_level: number;
  }>;
}

interface LearningRecommendations {
  priority_topics: Array<{
    topic: string;
    priority_score: number;
    reason: string;
    estimated_time: number;
  }>;
  study_plan: Array<{
    date: string;
    recommended_topics: string[];
    estimated_duration: number;
  }>;
  learning_resources: Array<{
    topic: string;
    resource_type: string;
    resource_name: string;
    difficulty_level: number;
  }>;
}

const LearningAnalytics: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [dashboardData, setDashboardData] = useState<DashboardSummary | null>(null);
  const [progressData, setProgressData] = useState<LearningProgress | null>(null);
  const [masteryData, setMasteryData] = useState<KnowledgeMastery | null>(null);
  const [trendsData, setTrendsData] = useState<PerformanceTrends | null>(null);
  const [statisticsData, setStatisticsData] = useState<StudyStatistics | null>(null);
  const [recommendationsData, setRecommendationsData] = useState<LearningRecommendations | null>(null);

  // 获取仪表板摘要数据
  const fetchDashboardSummary = async () => {
    try {
      const response: any = await api.get('/learning-analytics/dashboard-summary');
      if (response.success) {
        setDashboardData(response.data);
      }
    } catch (error) {
      console.error('获取仪表板数据失败:', error);
      message.error('获取仪表板数据失败');
    }
  };

  // 获取学习进度数据
  const fetchLearningProgress = async () => {
    try {
      const response: any = await api.get('/learning-analytics/progress');
      if (response.success) {
        setProgressData(response.data);
      }
    } catch (error) {
      console.error('获取学习进度数据失败:', error);
      message.error('获取学习进度数据失败');
    }
  };

  // 获取知识点掌握情况
  const fetchKnowledgeMastery = async () => {
    try {
      const response: any = await api.get('/learning-analytics/knowledge-mastery');
      if (response.success) {
        setMasteryData(response.data);
      }
    } catch (error) {
      console.error('获取知识点掌握数据失败:', error);
      message.error('获取知识点掌握数据失败');
    }
  };

  // 获取学习建议
  const fetchRecommendations = async () => {
    try {
      const response: any = await api.get('/learning-analytics/learning-recommendations');
      if (response.success) {
        setRecommendationsData(response.data);
      }
    } catch (error) {
      console.error('获取学习建议失败:', error);
      message.error('获取学习建议失败');
    }
  };

  // 获取学习统计
  const fetchStudyStatistics = async () => {
    try {
      const response: any = await api.get('/learning-analytics/study-statistics');
      if (response.success) {
        setStatisticsData(response.data);
      }
    } catch (error) {
      console.error('获取学习统计失败:', error);
      message.error('获取学习统计失败');
    }
  };

  // 初始化数据
  useEffect(() => {
    fetchDashboardSummary();
  }, []);

  // 根据活跃标签页加载对应数据
  useEffect(() => {
    switch (activeTab) {
      case 'progress':
        if (!progressData) fetchLearningProgress();
        break;
      case 'mastery':
        if (!masteryData) fetchKnowledgeMastery();
        break;
      case 'statistics':
        if (!statisticsData) fetchStudyStatistics();
        break;
      case 'recommendations':
        if (!recommendationsData) fetchRecommendations();
        break;
    }
  }, [activeTab]);

  // 格式化时间
  const formatTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}小时${mins}分钟` : `${mins}分钟`;
  };

  // 获取趋势颜色和图标
  const getTrendDisplay = (trend: string, changeRate?: number) => {
    const rate = changeRate || 0;
    switch (trend) {
      case 'improving':
        return { color: '#52c41a', text: '上升', icon: '↗️' };
      case 'declining':
        return { color: '#ff4d4f', text: '下降', icon: '↘️' };
      default:
        return { color: '#1890ff', text: '稳定', icon: '→' };
    }
  };

  // 获取掌握程度颜色
  const getMasteryColor = (level: number) => {
    if (level >= 0.8) return '#52c41a';
    if (level >= 0.6) return '#faad14';
    if (level >= 0.4) return '#fa8c16';
    return '#ff4d4f';
  };

  // 获取掌握程度文本
  const getMasteryText = (level: number) => {
    if (level >= 0.8) return '优秀';
    if (level >= 0.6) return '良好';
    if (level >= 0.4) return '一般';
    return '待提高';
  };

  // 渲染仪表板概览
  const renderDashboard = () => {
    if (!dashboardData) {
      return <Spin size="large" style={{ display: 'block', textAlign: 'center', padding: '50px' }} />;
    }

    const trendDisplay = getTrendDisplay(dashboardData.recent_performance.trend, dashboardData.recent_performance.change_rate);

    return (
      <div>
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总学习时长"
                value={formatTime(dashboardData.total_study_time)}
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="答题总数"
                value={dashboardData.total_questions}
                prefix={<BookOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="正确率"
                value={dashboardData.accuracy_rate}
                suffix="%"
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#faad14' }}
                precision={1}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="掌握知识点"
                value={dashboardData.knowledge_points_mastered}
                prefix={<TrophyOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Card title="学习趋势" extra={<Tag color={trendDisplay.color}>{trendDisplay.icon} {trendDisplay.text}</Tag>}>
              <div style={{ textAlign: 'center', padding: '20px' }}>
                <div style={{ fontSize: '24px', marginBottom: '8px' }}>
                  {trendDisplay.icon}
                </div>
                <Text style={{ color: trendDisplay.color, fontSize: '16px' }}>
                  {trendDisplay.text} {Math.abs(dashboardData.recent_performance.change_rate).toFixed(1)}%
                </Text>
                <div style={{ marginTop: '12px' }}>
                  <Text type="secondary">相比上周学习表现</Text>
                </div>
              </div>
            </Card>
          </Col>
          <Col span={12}>
            <Card title="薄弱环节" extra={<Tag color="orange">{dashboardData.weak_points_count} 个</Tag>}>
              <div style={{ textAlign: 'center', padding: '20px' }}>
                <ExclamationCircleOutlined style={{ fontSize: '32px', color: '#fa8c16', marginBottom: '12px' }} />
                <div>
                  <Text>发现 {dashboardData.weak_points_count} 个需要重点关注的知识点</Text>
                </div>
                <div style={{ marginTop: '12px' }}>
                  <Button type="primary" size="small" onClick={() => setActiveTab('mastery')}>查看详情</Button>
                </div>
              </div>
            </Card>
          </Col>
        </Row>
      </div>
    );
  };

  // 渲染学习进度
  const renderProgress = () => {
    if (!progressData) {
      return <Spin size="large" style={{ display: 'block', textAlign: 'center', padding: '50px' }} />;
    }

    const subjectColumns = [
      {
        title: '学科',
        dataIndex: 'subject_name',
        key: 'subject_name',
      },
      {
        title: '学习进度',
        dataIndex: 'progress',
        key: 'progress',
        render: (progress: number) => (
          <Progress percent={Math.round(progress * 100)} size="small" />
        ),
      },
      {
        title: '学习时长',
        dataIndex: 'total_time',
        key: 'total_time',
        render: (time: number) => formatTime(time),
      },
      {
        title: '掌握率',
        dataIndex: 'mastery_rate',
        key: 'mastery_rate',
        render: (rate: number) => (
          <Tag color={getMasteryColor(rate)}>
            {(rate * 100).toFixed(1)}%
          </Tag>
        ),
      },
    ];

    return (
      <div>
        <Card title="学科学习进度" style={{ marginBottom: 24 }}>
          <Table
            columns={subjectColumns}
            dataSource={progressData.subject_progress}
            rowKey="subject_name"
            pagination={false}
            size="small"
          />
        </Card>

        <Card title="周学习统计">
          <Table
            columns={[
              { title: '周期', dataIndex: 'week', key: 'week' },
              { title: '学习时长', dataIndex: 'study_time', key: 'study_time', render: (time: number) => formatTime(time) },
              { title: '答题数量', dataIndex: 'questions_count', key: 'questions_count' },
              { title: '正确率', dataIndex: 'accuracy', key: 'accuracy', render: (acc: number) => `${(acc * 100).toFixed(1)}%` },
            ]}
            dataSource={progressData.weekly_progress}
            rowKey="week"
            pagination={false}
            size="small"
          />
        </Card>
      </div>
    );
  };

  // 渲染知识点掌握情况
  const renderMastery = () => {
    if (!masteryData) {
      return <Spin size="large" style={{ display: 'block', textAlign: 'center', padding: '50px' }} />;
    }

    return (
      <div>
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="优秀"
                value={masteryData.mastery_distribution.excellent}
                valueStyle={{ color: '#52c41a' }}
                suffix="个"
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="良好"
                value={masteryData.mastery_distribution.good}
                valueStyle={{ color: '#faad14' }}
                suffix="个"
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="一般"
                value={masteryData.mastery_distribution.average}
                valueStyle={{ color: '#fa8c16' }}
                suffix="个"
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="待提高"
                value={masteryData.mastery_distribution.poor}
                valueStyle={{ color: '#ff4d4f' }}
                suffix="个"
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Card title="已掌握知识点" extra={<Tag color="green">{masteryData.mastered_points.length} 个</Tag>}>
              <List
                size="small"
                dataSource={masteryData.mastered_points.slice(0, 5)}
                renderItem={(item) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<Avatar style={{ backgroundColor: getMasteryColor(item.mastery_level) }}>{getMasteryText(item.mastery_level)[0]}</Avatar>}
                      title={item.knowledge_point}
                      description={`练习 ${item.practice_count} 次 · 掌握度 ${(item.mastery_level * 100).toFixed(0)}%`}
                    />
                  </List.Item>
                )}
              />
            </Card>
          </Col>
          <Col span={12}>
            <Card title="薄弱知识点" extra={<Tag color="orange">{masteryData.weak_points.length} 个</Tag>}>
              <List
                size="small"
                dataSource={masteryData.weak_points.slice(0, 5)}
                renderItem={(item) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<Avatar style={{ backgroundColor: getMasteryColor(item.mastery_level) }}>{getMasteryText(item.mastery_level)[0]}</Avatar>}
                      title={item.knowledge_point}
                      description={`错误 ${item.error_count} 次 · 掌握度 ${(item.mastery_level * 100).toFixed(0)}%`}
                    />
                    <div>
                      {item.suggestions.slice(0, 2).map((suggestion, index) => (
                        <Tag key={index}>{suggestion}</Tag>
                      ))}
                    </div>
                  </List.Item>
                )}
              />
            </Card>
          </Col>
        </Row>
      </div>
    );
  };

  // 渲染学习建议
  const renderRecommendations = () => {
    if (!recommendationsData) {
      return <Spin size="large" style={{ display: 'block', textAlign: 'center', padding: '50px' }} />;
    }

    return (
      <div>
        <Card title="优先学习主题" style={{ marginBottom: 24 }}>
          <List
            dataSource={recommendationsData.priority_topics}
            renderItem={(item) => (
              <List.Item
                actions={[
                  <Text type="secondary">{item.estimated_time}分钟</Text>,
                  <Button type="primary" size="small">开始学习</Button>
                ]}
              >
                <List.Item.Meta
                  avatar={<Avatar style={{ backgroundColor: '#1890ff' }}><BulbOutlined /></Avatar>}
                  title={item.topic}
                  description={item.reason}
                />
                <div>
                  <Progress percent={item.priority_score * 20} size="small" showInfo={false} />
                  <Text type="secondary" style={{ fontSize: '12px' }}>优先级: {item.priority_score}/5</Text>
                </div>
              </List.Item>
            )}
          />
        </Card>

        <Card title="学习计划建议">
          <List
            dataSource={recommendationsData.study_plan.slice(0, 7)}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta
                  avatar={<Avatar style={{ backgroundColor: '#52c41a' }}><CalendarOutlined /></Avatar>}
                  title={dayjs(item.date).format('MM月DD日')}
                  description={
                    <div>
                      <div>推荐主题: {item.recommended_topics.join(', ')}</div>
                      <Text type="secondary">预计时长: {item.estimated_duration}分钟</Text>
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        </Card>
      </div>
    );
  };

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <BarChartOutlined style={{ marginRight: 12 }} />
          学习分析
        </Title>
        <Text type="secondary">
          基于AI分析您的学习数据，提供个性化的学习洞察和建议
        </Text>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'dashboard',
            label: (
              <span>
                <BarChartOutlined />
                概览
              </span>
            ),
            children: renderDashboard()
          },
          {
            key: 'progress',
            label: (
              <span>
                <LineChartOutlined />
                学习进度
              </span>
            ),
            children: renderProgress()
          },
          {
            key: 'mastery',
            label: (
              <span>
                <TrophyOutlined />
                知识掌握
              </span>
            ),
            children: renderMastery()
          },
          {
            key: 'recommendations',
            label: (
              <span>
                <BulbOutlined />
                学习建议
              </span>
            ),
            children: renderRecommendations()
          }
        ]}
      />
    </div>
  );
};

export default LearningAnalytics;