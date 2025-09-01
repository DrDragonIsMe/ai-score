import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Progress,
  Tag,
  List,
  Avatar,
  Typography,
  Space,
  Statistic,
  Badge,
  Modal,
  Form,
  Select,
  DatePicker,
  Switch,
  message,
  Tabs,
  Timeline,
  Rate,
  Tooltip,
  Empty
} from 'antd';
import {
  ExperimentOutlined,
  ClockCircleOutlined,
  BookOutlined,
  RiseOutlined,
  CalendarOutlined,
  BellOutlined,
  StarOutlined,
  ReloadOutlined,
  AimOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import type { MemoryCard, ReviewReminder, MemoryStats } from '../types';

const { Title, Text } = Typography;
// const { TabPane } = Tabs; // 已弃用，改用items属性
const { Option } = Select;

// 扩展的记忆卡片类型，包含计算属性
interface ExtendedMemoryCard extends MemoryCard {
  masteryLevel: number;
  subjectName: string;
}

// 模拟数据
const mockMemoryCards: ExtendedMemoryCard[] = [
  {
    id: 1,
    user_id: 1,
    knowledge_point_id: 1,
    front_content: '二次函数的顶点公式',
    back_content: 'y = a(x-h)² + k，其中(h,k)为顶点坐标',
    difficulty: 3,
    next_review_date: '2024-01-18',
    review_count: 5,
    success_count: 4,
    created_at: '2024-01-10',
    masteryLevel: 0.8,
    subjectName: '数学'
  },
  {
    id: 2,
    user_id: 1,
    knowledge_point_id: 2,
    front_content: '牛顿第二定律',
    back_content: 'F = ma，力等于质量乘以加速度',
    difficulty: 4,
    next_review_date: '2024-01-17',
    review_count: 3,
    success_count: 2,
    created_at: '2024-01-12',
    masteryLevel: 0.6,
    subjectName: '物理'
  },
  {
    id: 3,
    user_id: 1,
    knowledge_point_id: 3,
    front_content: '化学平衡常数',
    back_content: 'Kc = [C]^c[D]^d / [A]^a[B]^b',
    difficulty: 5,
    next_review_date: '2024-01-16',
    review_count: 2,
    success_count: 1,
    created_at: '2024-01-11',
    masteryLevel: 0.4,
    subjectName: '化学'
  }
];

const mockReminders: ReviewReminder[] = [
  {
    id: '1',
    userId: '1',
    cardId: '1',
    reminderTime: new Date('2024-01-18T09:00:00'),
    isCompleted: false,
    createdAt: new Date('2024-01-15'),
    updatedAt: new Date('2024-01-15')
  },
  {
    id: '2',
    userId: '1',
    cardId: '2',
    reminderTime: new Date('2024-01-17T14:00:00'),
    isCompleted: false,
    createdAt: new Date('2024-01-14'),
    updatedAt: new Date('2024-01-14')
  }
];

const mockStats: MemoryStats = {
  totalCards: 25,
  reviewedToday: 8,
  averageMastery: 0.72,
  streakDays: 12,
  totalReviews: 156,
  accuracy: 0.78
};

const Memory: React.FC = () => {
  const [memoryCards, setMemoryCards] = useState<ExtendedMemoryCard[]>(mockMemoryCards);
  const [reminders, setReminders] = useState<ReviewReminder[]>(mockReminders);
  const [stats, setStats] = useState<MemoryStats>(mockStats);
  const [selectedCard, setSelectedCard] = useState<ExtendedMemoryCard | null>(null);
  const [reviewModalVisible, setReviewModalVisible] = useState(false);
  const [reminderModalVisible, setReminderModalVisible] = useState(false);
  const [activeTab, setActiveTab] = useState('cards');
  const [form] = Form.useForm();

  useEffect(() => {
    // 模拟数据加载
    console.log('加载记忆卡片数据');
  }, []);

  const handleReviewCard = (card: ExtendedMemoryCard, isCorrect: boolean) => {
    const updatedCard = {
      ...card,
      review_count: card.review_count + 1,
      success_count: card.success_count + (isCorrect ? 1 : 0),
      masteryLevel: isCorrect 
        ? Math.min(1, card.masteryLevel + 0.1)
        : Math.max(0, card.masteryLevel - 0.1),
      next_review_date: new Date(Date.now() + (isCorrect ? 3 : 1) * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    };

    setMemoryCards(prev => 
      prev.map(c => c.id === card.id ? updatedCard : c)
    );

    setReviewModalVisible(false);
    setSelectedCard(null);
    message.success(isCorrect ? '回答正确！' : '继续加油！');
  };

  const handleSetReminder = (values: any) => {
    const newReminder: ReviewReminder = {
      id: Date.now().toString(),
      userId: '1',
      cardId: selectedCard?.id.toString() || '',
      reminderTime: values.reminderTime.toDate(),
      isCompleted: false,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    setReminders(prev => [...prev, newReminder]);
    setReminderModalVisible(false);
    form.resetFields();
    message.success('复习提醒设置成功！');
  };

  const getDifficultyColor = (difficulty: number) => {
    if (difficulty <= 2) return 'green';
    if (difficulty <= 3) return 'blue';
    if (difficulty <= 4) return 'orange';
    return 'red';
  };

  const getMasteryColor = (mastery: number) => {
    if (mastery >= 0.8) return 'green';
    if (mastery >= 0.6) return 'blue';
    if (mastery >= 0.4) return 'orange';
    return 'red';
  };

  const renderMemoryCards = () => (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总卡片数"
              value={stats.totalCards}
              prefix={<BookOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="今日复习"
              value={stats.reviewedToday}
              prefix={<ReloadOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="平均掌握度"
              value={stats.averageMastery}
              precision={1}
              suffix="%"
              formatter={(value) => `${((value as number) * 100).toFixed(1)}%`}
              prefix={<RiseOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="连续天数"
              value={stats.streakDays}
              prefix={<AimOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card title="记忆卡片" extra={
        <Button type="primary" icon={<ExperimentOutlined />}>
          开始复习
        </Button>
      }>
        <List
          dataSource={memoryCards}
          renderItem={(card) => (
            <List.Item
              actions={[
                <Button
                  type="link"
                  onClick={() => {
                    setSelectedCard(card);
                    setReviewModalVisible(true);
                  }}
                >
                  复习
                </Button>,
                <Button
                  type="link"
                  onClick={() => {
                    setSelectedCard(card);
                    setReminderModalVisible(true);
                  }}
                >
                  设置提醒
                </Button>
              ]}
            >
              <List.Item.Meta
                avatar={
                  <Avatar style={{ backgroundColor: getDifficultyColor(card.difficulty) }}>
                    {card.subjectName[0]}
                  </Avatar>
                }
                title={
                  <Space>
                    <Text strong>{card.front_content}</Text>
                    <Tag color={getDifficultyColor(card.difficulty)}>
                      难度 {card.difficulty}
                    </Tag>
                    <Tag color={getMasteryColor(card.masteryLevel)}>
                      掌握度 {(card.masteryLevel * 100).toFixed(0)}%
                    </Tag>
                  </Space>
                }
                description={
                  <Space direction="vertical" size={4}>
                    <Text type="secondary">
                      科目：{card.subjectName}
                    </Text>
                    <Text type="secondary">
                      复习次数：{card.review_count} | 正确次数：{card.success_count}
                    </Text>
                    <Text type="secondary">
                      下次复习：{new Date(card.next_review_date).toLocaleDateString()}
                    </Text>
                  </Space>
                }
              />
              <div>
                <Progress
                  percent={card.masteryLevel * 100}
                  size="small"
                  strokeColor={getMasteryColor(card.masteryLevel)}
                  showInfo={false}
                />
              </div>
            </List.Item>
          )}
        />
      </Card>
    </div>
  );

  const renderReminders = () => (
    <Card title="复习提醒" extra={
      <Button type="primary" icon={<BellOutlined />}>
        新建提醒
      </Button>
    }>
      {reminders.length > 0 ? (
        <Timeline>
          {reminders.map((reminder) => {
            const card = memoryCards.find(c => c.id.toString() === reminder.cardId);
            return (
              <Timeline.Item
                key={reminder.id}
                color={reminder.isCompleted ? 'green' : 'blue'}
                dot={reminder.isCompleted ? <CheckCircleOutlined /> : <ClockCircleOutlined />}
              >
                <div>
                  <Text strong>{card?.front_content}</Text>
                  <br />
                  <Text type="secondary">
                    提醒时间：{reminder.reminderTime.toLocaleString()}
                  </Text>
                  <br />
                  <Badge
                    status={reminder.isCompleted ? 'success' : 'processing'}
                    text={reminder.isCompleted ? '已完成' : '待复习'}
                  />
                </div>
              </Timeline.Item>
            );
          })}
        </Timeline>
      ) : (
        <Empty description="暂无复习提醒" />
      )}
    </Card>
  );

  const renderStats = () => (
    <Row gutter={[16, 16]}>
      <Col xs={24} md={12}>
        <Card title="学习统计">
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <div>
              <Text>总复习次数</Text>
              <div>
                <Text strong style={{ fontSize: 24 }}>{stats.totalReviews}</Text>
              </div>
            </div>
            <div>
              <Text>复习准确率</Text>
              <div>
                <Progress
                  percent={stats.accuracy * 100}
                  strokeColor="#52c41a"
                  format={(percent) => `${percent?.toFixed(1)}%`}
                />
              </div>
            </div>
            <div>
              <Text>学习连续天数</Text>
              <div>
                <Text strong style={{ fontSize: 24, color: '#1890ff' }}>
                  {stats.streakDays} 天
                </Text>
              </div>
            </div>
          </Space>
        </Card>
      </Col>
      <Col xs={24} md={12}>
        <Card title="掌握度分布">
          <Space direction="vertical" size={12} style={{ width: '100%' }}>
            <div>
              <Text>优秀 (80%+)</Text>
              <Progress
                percent={40}
                strokeColor="#52c41a"
                showInfo={false}
              />
              <Text type="secondary">10 个知识点</Text>
            </div>
            <div>
              <Text>良好 (60-80%)</Text>
              <Progress
                percent={30}
                strokeColor="#1890ff"
                showInfo={false}
              />
              <Text type="secondary">8 个知识点</Text>
            </div>
            <div>
              <Text>一般 (40-60%)</Text>
              <Progress
                percent={20}
                strokeColor="#faad14"
                showInfo={false}
              />
              <Text type="secondary">5 个知识点</Text>
            </div>
            <div>
              <Text>需加强 (&lt;40%)</Text>
              <Progress
                percent={10}
                strokeColor="#ff4d4f"
                showInfo={false}
              />
              <Text type="secondary">2 个知识点</Text>
            </div>
          </Space>
        </Card>
      </Col>
    </Row>
  );

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <ExperimentOutlined style={{ marginRight: 12 }} />
          记忆强化
        </Title>
        <Text type="secondary">
          通过科学的复习算法，帮助您更好地记忆和掌握知识点
        </Text>
      </div>

      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        items={[
          {
            key: 'cards',
            label: '记忆卡片',
            children: renderMemoryCards()
          },
          {
            key: 'reminders',
            label: '复习提醒',
            children: renderReminders()
          },
          {
            key: 'stats',
            label: '学习统计',
            children: renderStats()
          }
        ]}
      />

      {/* 复习模态框 */}
      <Modal
        title="复习卡片"
        open={reviewModalVisible}
        onCancel={() => {
          setReviewModalVisible(false);
          setSelectedCard(null);
        }}
        footer={[
          <Button
            key="incorrect"
            onClick={() => selectedCard && handleReviewCard(selectedCard, false)}
          >
            答错了
          </Button>,
          <Button
            key="correct"
            type="primary"
            onClick={() => selectedCard && handleReviewCard(selectedCard, true)}
          >
            答对了
          </Button>
        ]}
      >
        {selectedCard && (
          <div>
            <Card>
              <Title level={4}>{selectedCard.front_content}</Title>
              <div style={{ marginTop: 16, padding: 16, backgroundColor: '#f5f5f5', borderRadius: 8 }}>
                <Text strong>答案：</Text>
                <div style={{ marginTop: 8 }}>
                  <Text>{selectedCard.back_content}</Text>
                </div>
              </div>
              <Space direction="vertical" size={12} style={{ marginTop: 16 }}>
                <div>
                  <Text strong>科目：</Text>
                  <Text>{selectedCard.subjectName}</Text>
                </div>
                <div>
                  <Text strong>难度：</Text>
                  <Rate disabled value={selectedCard.difficulty} />
                </div>
                <div>
                  <Text strong>当前掌握度：</Text>
                  <Progress
                    percent={selectedCard.masteryLevel * 100}
                    size="small"
                    strokeColor={getMasteryColor(selectedCard.masteryLevel)}
                  />
                </div>
                <div>
                  <Text strong>复习历史：</Text>
                  <Text>
                    {selectedCard.review_count} 次复习，{selectedCard.success_count} 次正确
                  </Text>
                </div>
              </Space>
            </Card>
            <div style={{ marginTop: 16, textAlign: 'center' }}>
              <Text>请回忆这个知识点的内容，然后选择您的掌握情况</Text>
            </div>
          </div>
        )}
      </Modal>

      {/* 提醒设置模态框 */}
      <Modal
        title="设置复习提醒"
        open={reminderModalVisible}
        onCancel={() => {
          setReminderModalVisible(false);
          setSelectedCard(null);
          form.resetFields();
        }}
        onOk={() => form.submit()}
      >
        <Form form={form} onFinish={handleSetReminder} layout="vertical">
          <Form.Item label="卡片内容">
            <Text>{selectedCard?.front_content}</Text>
          </Form.Item>
          <Form.Item
            name="reminderTime"
            label="提醒时间"
            rules={[{ required: true, message: '请选择提醒时间' }]}
          >
            <DatePicker
              showTime
              style={{ width: '100%' }}
              placeholder="选择提醒时间"
            />
          </Form.Item>
          <Form.Item name="repeatEnabled" label="重复提醒" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item
            name="repeatInterval"
            label="重复间隔"
            dependencies={['repeatEnabled']}
          >
            <Select placeholder="选择重复间隔" disabled={!form.getFieldValue('repeatEnabled')}>
              <Option value="daily">每天</Option>
              <Option value="weekly">每周</Option>
              <Option value="monthly">每月</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Memory;