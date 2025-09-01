import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  DatePicker,
  Select,
  Button,
  Spin,
  message,
  Progress,
  Table,
  Tag,
  Divider,
  Space,
  Typography
} from 'antd';
import {
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  BookOutlined,
  CheckCircleOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import dayjs, { Dayjs } from 'dayjs';
import api from '../services/api';

const { RangePicker } = DatePicker;
const { Option } = Select;
const { Title, Text } = Typography;

// 统计数据接口
interface LearningStatistics {
  total_study_time: number;
  questions_answered: number;
  accuracy_rate: number;
  knowledge_points_mastered: number;
  daily_stats: Array<{
    date: string;
    study_time: number;
    questions_count: number;
    accuracy: number;
  }>;
  subject_breakdown: Array<{
    subject_id: string;
    subject_name: string;
    study_time: number;
    progress: number;
    accuracy: number;
  }>;
  weekly_progress: Array<{
    week: string;
    study_time: number;
    questions_count: number;
    accuracy: number;
  }>;
  performance_trends: {
    overall_trend: 'improving' | 'stable' | 'declining';
    accuracy_trend: number;
    efficiency_trend: number;
  };
}

interface StatisticsAnalysisProps {
  subjectId?: string;
}

const StatisticsAnalysis: React.FC<StatisticsAnalysisProps> = ({ subjectId }) => {
  const [loading, setLoading] = useState(false);
  const [statistics, setStatistics] = useState<LearningStatistics | null>(null);
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs]>([
    dayjs().subtract(30, 'day'),
    dayjs()
  ]);
  const [periodType, setPeriodType] = useState<'day' | 'week' | 'month'>('day');

  // 获取统计数据
  const fetchStatistics = async () => {
    if (!dateRange) return;
    
    setLoading(true);
    try {
      const params = {
        period_start: dateRange[0].toISOString(),
        period_end: dateRange[1].toISOString(),
        ...(subjectId && { subject_id: subjectId })
      };
      
      const response = await api.get('/tracking/statistics', { params });
      if (response.data.success) {
        setStatistics(response.data.data.statistics);
      } else {
        message.error('获取统计数据失败');
      }
    } catch (error) {
      console.error('获取统计数据失败:', error);
      message.error('获取统计数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatistics();
  }, [dateRange, subjectId]);

  // 格式化时间
  const formatTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}小时${mins}分钟` : `${mins}分钟`;
  };

  // 获取趋势颜色
  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'improving': return '#52c41a';
      case 'declining': return '#ff4d4f';
      default: return '#1890ff';
    }
  };

  // 获取趋势文本
  const getTrendText = (trend: string) => {
    switch (trend) {
      case 'improving': return '上升';
      case 'declining': return '下降';
      default: return '稳定';
    }
  };

  // 渲染概览统计
  const renderOverviewStats = () => {
    if (!statistics) return null;

    return (
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总学习时长"
              value={formatTime(statistics.total_study_time)}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="答题总数"
              value={statistics.questions_answered}
              prefix={<BookOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="正确率"
              value={statistics.accuracy_rate}
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
              value={statistics.knowledge_points_mastered}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>
    );
  };

  // 渲染学科分布
  const renderSubjectBreakdown = () => {
    if (!statistics?.subject_breakdown?.length) return null;

    const columns = [
      {
        title: '学科',
        dataIndex: 'subject_name',
        key: 'subject_name',
      },
      {
        title: '学习时长',
        dataIndex: 'study_time',
        key: 'study_time',
        render: (time: number) => formatTime(time),
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
        title: '正确率',
        dataIndex: 'accuracy',
        key: 'accuracy',
        render: (accuracy: number) => (
          <Tag color={accuracy >= 0.8 ? 'green' : accuracy >= 0.6 ? 'orange' : 'red'}>
            {(accuracy * 100).toFixed(1)}%
          </Tag>
        ),
      },
    ];

    return (
      <Card title="学科学习分布" style={{ marginBottom: 24 }}>
        <Table
          columns={columns}
          dataSource={statistics.subject_breakdown}
          rowKey="subject_id"
          pagination={false}
          size="small"
        />
      </Card>
    );
  };

  // 渲染每日学习统计
  const renderDailyStats = () => {
    if (!statistics?.daily_stats?.length) return null;

    const recentStats = statistics.daily_stats.slice(-7); // 最近7天

    return (
      <Card title="最近7天学习统计" style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          {recentStats.map((stat, index) => (
            <Col span={24 / Math.min(recentStats.length, 7)} key={stat.date}>
              <div style={{ textAlign: 'center', padding: '16px 0' }}>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: 8 }}>
                  {dayjs(stat.date).format('MM/DD')}
                </div>
                <div style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: 4 }}>
                  {formatTime(stat.study_time)}
                </div>
                <div style={{ fontSize: '12px', color: '#999' }}>
                  {stat.questions_count}题 · {(stat.accuracy * 100).toFixed(0)}%
                </div>
              </div>
            </Col>
          ))}
        </Row>
      </Card>
    );
  };

  // 渲染性能趋势
  const renderPerformanceTrends = () => {
    if (!statistics?.performance_trends) return null;

    const { performance_trends } = statistics;

    return (
      <Card title="学习趋势分析" style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col span={8}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '14px', color: '#666', marginBottom: 8 }}>
                整体趋势
              </div>
              <div 
                style={{ 
                  fontSize: '18px', 
                  fontWeight: 'bold',
                  color: getTrendColor(performance_trends.overall_trend)
                }}
              >
                {getTrendText(performance_trends.overall_trend)}
              </div>
            </div>
          </Col>
          <Col span={8}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '14px', color: '#666', marginBottom: 8 }}>
                正确率变化
              </div>
              <div 
                style={{ 
                  fontSize: '18px', 
                  fontWeight: 'bold',
                  color: performance_trends.accuracy_trend >= 0 ? '#52c41a' : '#ff4d4f'
                }}
              >
                {performance_trends.accuracy_trend >= 0 ? '+' : ''}
                {(performance_trends.accuracy_trend * 100).toFixed(1)}%
              </div>
            </div>
          </Col>
          <Col span={8}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '14px', color: '#666', marginBottom: 8 }}>
                效率变化
              </div>
              <div 
                style={{ 
                  fontSize: '18px', 
                  fontWeight: 'bold',
                  color: performance_trends.efficiency_trend >= 0 ? '#52c41a' : '#ff4d4f'
                }}
              >
                {performance_trends.efficiency_trend >= 0 ? '+' : ''}
                {(performance_trends.efficiency_trend * 100).toFixed(1)}%
              </div>
            </div>
          </Col>
        </Row>
      </Card>
    );
  };

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={3}>学习统计分析</Title>
        <Space>
          <RangePicker
            value={dateRange}
            onChange={(dates) => setDateRange(dates as [Dayjs, Dayjs])}
            format="YYYY-MM-DD"
          />
          <Select
            value={periodType}
            onChange={setPeriodType}
            style={{ width: 120 }}
          >
            <Option value="day">按天</Option>
            <Option value="week">按周</Option>
            <Option value="month">按月</Option>
          </Select>
          <Button 
            type="primary" 
            icon={<ReloadOutlined />}
            onClick={fetchStatistics}
            loading={loading}
          >
            刷新数据
          </Button>
        </Space>
      </div>

      <Spin spinning={loading}>
        {statistics ? (
          <>
            {renderOverviewStats()}
            {renderPerformanceTrends()}
            {renderDailyStats()}
            {renderSubjectBreakdown()}
          </>
        ) : (
          <Card>
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <Text type="secondary">暂无统计数据</Text>
            </div>
          </Card>
        )}
      </Spin>
    </div>
  );
};

export default StatisticsAnalysis;