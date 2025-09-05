import React, { useEffect, useState } from 'react';
import {
  Row,
  Col,
  Card,
  Statistic,
  Progress,
  Typography,
  Space,
  Button,
  List,
  Avatar,
  Tag,
  Divider,
} from 'antd';
import {
  BookOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  FireOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  RobotOutlined,
  BulbOutlined,
  MessageOutlined,
  StarOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

const { Title, Text } = Typography;

interface DashboardStats {
  totalSubjects: number;
  completedLessons: number;
  studyStreak: number;
  totalStudyTime: number;
  weeklyProgress: number;
  accuracy: number;
}

interface AIStats {
  totalInteractions: number;
  questionsAnswered: number;
  aiAccuracy: number;
  personalizedRecommendations: number;
  aiStudyTime: number;
  intelligentAnalysis: number;
}

interface RecentActivity {
  id: number;
  type: 'study' | 'quiz' | 'review';
  title: string;
  subject: string;
  score?: number;
  duration: number;
  timestamp: string;
}

interface UpcomingTask {
  id: number;
  type: 'review' | 'quiz' | 'lesson';
  title: string;
  subject: string;
  dueDate: string;
  priority: 'high' | 'medium' | 'low';
}

const Dashboard: React.FC = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats>({
    totalSubjects: 5,
    completedLessons: 23,
    studyStreak: 7,
    totalStudyTime: 1250,
    weeklyProgress: 75,
    accuracy: 85,
  });

  const [aiStats, setAiStats] = useState<AIStats>({
    totalInteractions: 156,
    questionsAnswered: 89,
    aiAccuracy: 94,
    personalizedRecommendations: 23,
    aiStudyTime: 420,
    intelligentAnalysis: 15,
  });

  const [recentActivities] = useState<RecentActivity[]>([
    {
      id: 1,
      type: 'study',
      title: '线性代数基础',
      subject: '数学',
      duration: 45,
      timestamp: '2小时前',
    },
    {
      id: 2,
      type: 'quiz',
      title: '英语语法测试',
      subject: '英语',
      score: 92,
      duration: 30,
      timestamp: '4小时前',
    },
    {
      id: 3,
      type: 'review',
      title: '物理公式复习',
      subject: '物理',
      duration: 20,
      timestamp: '昨天',
    },
  ]);

  const [upcomingTasks] = useState<UpcomingTask[]>([
    {
      id: 1,
      type: 'review',
      title: '化学方程式复习',
      subject: '化学',
      dueDate: '今天 18:00',
      priority: 'high',
    },
    {
      id: 2,
      type: 'quiz',
      title: '历史知识测试',
      subject: '历史',
      dueDate: '明天 14:00',
      priority: 'medium',
    },
    {
      id: 3,
      type: 'lesson',
      title: '生物细胞结构',
      subject: '生物',
      dueDate: '后天 10:00',
      priority: 'low',
    },
  ]);

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'study':
        return <BookOutlined style={{ color: '#1890ff' }} />;
      case 'quiz':
        return <TrophyOutlined style={{ color: '#52c41a' }} />;
      case 'review':
        return <ClockCircleOutlined style={{ color: '#faad14' }} />;
      default:
        return <BookOutlined />;
    }
  };

  const getTaskIcon = (type: string) => {
    switch (type) {
      case 'review':
        return <ClockCircleOutlined />;
      case 'quiz':
        return <TrophyOutlined />;
      case 'lesson':
        return <PlayCircleOutlined />;
      default:
        return <BookOutlined />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'red';
      case 'medium':
        return 'orange';
      case 'low':
        return 'green';
      default:
        return 'default';
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ 
          fontFamily: 'var(--font-family-primary)', 
          fontWeight: 'var(--font-weight-bold)', 
          color: 'var(--heading-color)',
          lineHeight: 'var(--line-height-heading)'
        }}>
          <RobotOutlined style={{ color: 'var(--primary-color)', marginRight: 8 }} />
          AI智能学习仪表盘
        </Title>
        <Text type="secondary" style={{
          fontFamily: 'var(--font-family-primary)',
          fontSize: 'var(--font-size-base)',
          color: 'var(--text-secondary)',
          lineHeight: 'var(--line-height-normal)'
        }}>
          欢迎回来，{user?.full_name || user?.username}！AI助手已为您准备了个性化学习方案。
        </Text>
      </div>

      {/* AI功能统计卡片 */}
      <Card 
        title={
          <Space>
            <RobotOutlined style={{ color: 'var(--primary-color)' }} />
            <span>AI学习助手统计</span>
          </Space>
        }
        style={{ marginBottom: 24 }}
        extra={<Button type="primary" ghost>查看AI详情</Button>}
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={4}>
            <Statistic
              title="AI互动次数"
              value={aiStats.totalInteractions}
              prefix={<MessageOutlined style={{ color: 'var(--primary-color)' }} />}
              valueStyle={{ color: 'var(--primary-color)' }}
            />
          </Col>
          <Col xs={24} sm={12} lg={4}>
            <Statistic
              title="AI解答问题"
              value={aiStats.questionsAnswered}
              prefix={<BulbOutlined style={{ color: 'var(--success-color)' }} />}
              valueStyle={{ color: 'var(--success-color)' }}
            />
          </Col>
          <Col xs={24} sm={12} lg={4}>
            <Statistic
              title="AI准确率"
              value={aiStats.aiAccuracy}
              suffix="%"
              prefix={<StarOutlined style={{ color: 'var(--warning-color)' }} />}
              valueStyle={{ color: 'var(--warning-color)' }}
            />
          </Col>
          <Col xs={24} sm={12} lg={4}>
            <Statistic
              title="个性化推荐"
              value={aiStats.personalizedRecommendations}
              prefix={<TrophyOutlined style={{ color: 'var(--purple-color)' }} />}
              valueStyle={{ color: 'var(--purple-color)' }}
            />
          </Col>
          <Col xs={24} sm={12} lg={4}>
            <Statistic
              title="AI辅助学习"
              value={aiStats.aiStudyTime}
              suffix="分钟"
              prefix={<ClockCircleOutlined style={{ color: 'var(--orange-color)' }} />}
              valueStyle={{ color: 'var(--orange-color)' }}
            />
          </Col>
          <Col xs={24} sm={12} lg={4}>
            <Statistic
              title="智能分析"
              value={aiStats.intelligentAnalysis}
              suffix="次"
              prefix={<BookOutlined style={{ color: 'var(--cyan-color)' }} />}
              valueStyle={{ color: 'var(--cyan-color)' }}
            />
          </Col>
        </Row>
      </Card>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="学习科目"
              value={stats.totalSubjects}
              prefix={<BookOutlined />}
              valueStyle={{ color: 'var(--primary-color)' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="完成课程"
              value={stats.completedLessons}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: 'var(--success-color)' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="连续学习"
              value={stats.studyStreak}
              suffix="天"
              prefix={<FireOutlined />}
              valueStyle={{ color: 'var(--orange-color)' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="学习时长"
              value={stats.totalStudyTime}
              suffix="分钟"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: 'var(--purple-color)' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 学习进度 */}
        <Col xs={24} lg={12}>
          <Card title="本周学习进度" extra={<Button type="link">查看详情</Button>}>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <Text style={{
                    fontFamily: 'var(--font-family-primary)',
                    fontSize: 'var(--font-size-base)',
                    color: 'var(--text-primary)'
                  }}>整体进度</Text>
                  <Text strong style={{
                    fontFamily: 'var(--font-family-primary)',
                    fontWeight: 'var(--font-weight-semibold)',
                    color: 'var(--text-primary)'
                  }}>{stats.weeklyProgress}%</Text>
                </div>
                <Progress percent={stats.weeklyProgress} strokeColor="var(--primary-color)" />
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <Text style={{
                    fontFamily: 'var(--font-family-primary)',
                    fontSize: 'var(--font-size-base)',
                    color: 'var(--text-primary)'
                  }}>答题准确率</Text>
                  <Text strong style={{
                    fontFamily: 'var(--font-family-primary)',
                    fontWeight: 'var(--font-weight-semibold)',
                    color: 'var(--text-primary)'
                  }}>{stats.accuracy}%</Text>
                </div>
                <Progress percent={stats.accuracy} strokeColor="var(--success-color)" />
              </div>
              <Row gutter={16}>
                <Col span={12}>
                  <Card size="small">
                    <Statistic
                      title="本周学习"
                      value={320}
                      suffix="分钟"
                      valueStyle={{ fontSize: 16 }}
                      prefix={<ArrowUpOutlined style={{ color: 'var(--success-color)' }} />}
                    />
                  </Card>
                </Col>
                <Col span={12}>
                  <Card size="small">
                    <Statistic
                      title="完成任务"
                      value={12}
                      suffix="个"
                      valueStyle={{ fontSize: 16 }}
                      prefix={<ArrowUpOutlined style={{ color: 'var(--success-color)' }} />}
                    />
                  </Card>
                </Col>
              </Row>
            </Space>
          </Card>
        </Col>

        {/* 最近活动 */}
        <Col xs={24} lg={12}>
          <Card title="最近活动" extra={<Button type="link">查看全部</Button>}>
            <List
              itemLayout="horizontal"
              dataSource={recentActivities}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={<Avatar icon={getActivityIcon(item.type)} />}
                    title={
                      <Space>
                        <span>{item.title}</span>
                        <Tag color="blue">{item.subject}</Tag>
                      </Space>
                    }
                    description={
                      <Space>
                        <Text type="secondary" style={{
                          fontFamily: 'var(--font-family-primary)',
                          fontSize: 'var(--font-size-small)',
                          color: 'var(--text-secondary)'
                        }}>{item.timestamp}</Text>
                        <Text type="secondary" style={{
                          fontFamily: 'var(--font-family-primary)',
                          color: 'var(--text-secondary)'
                        }}>•</Text>
                        <Text type="secondary" style={{
                          fontFamily: 'var(--font-family-primary)',
                          fontSize: 'var(--font-size-small)',
                          color: 'var(--text-secondary)'
                        }}>{item.duration}分钟</Text>
                        {item.score && (
                          <>
                            <Text type="secondary" style={{
                              fontFamily: 'var(--font-family-primary)',
                              color: 'var(--text-secondary)'
                            }}>•</Text>
                            <Text type="secondary" style={{
                              fontFamily: 'var(--font-family-primary)',
                              fontSize: 'var(--font-size-small)',
                              color: 'var(--text-secondary)'
                            }}>得分: {item.score}%</Text>
                          </>
                        )}
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      {/* 待办任务 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="待办任务" extra={<Button type="link">管理任务</Button>}>
            <List
              itemLayout="horizontal"
              dataSource={upcomingTasks}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    <Button type="primary" size="small" onClick={() => {
                      // 根据任务类型导航到相应页面
                      if (item.type === 'review') {
                        navigate('/memory-cards');
                      } else if (item.type === 'quiz') {
                        navigate('/diagnosis');
                      } else {
                        navigate('/learning-path');
                      }
                    }}>
                      开始
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    avatar={<Avatar icon={getTaskIcon(item.type)} />}
                    title={
                      <Space>
                        <span>{item.title}</span>
                        <Tag color="blue">{item.subject}</Tag>
                        <Tag color={getPriorityColor(item.priority)}>
                          {item.priority === 'high' ? '高优先级' : 
                           item.priority === 'medium' ? '中优先级' : '低优先级'}
                        </Tag>
                      </Space>
                    }
                    description={
                      <Text type="secondary" style={{
                        fontFamily: 'var(--font-family-primary)',
                        fontSize: 'var(--font-size-small)',
                        color: 'var(--text-secondary)'
                      }}>截止时间: {item.dueDate}</Text>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;