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
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  Slider,
  message,
  Tabs,
  Steps,
  Timeline,
  Tooltip,
  Empty,
  Divider,
  Badge
} from 'antd';
import {
  RocketOutlined,
  BookOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  CheckCircleOutlined,
  StarOutlined,
  AimOutlined,
  BulbOutlined
} from '@ant-design/icons';
import type { LearningPath, StudyRecord } from '../types';

const { Title, Text, Paragraph } = Typography;
// const { TabPane } = Tabs; // 已弃用，改用items属性
const { Option } = Select;
const { Step } = Steps;
const { TextArea } = Input;

// 扩展的学习路径类型
interface ExtendedLearningPath extends LearningPath {
  subjectName: string;
  completedSteps: number;
  totalSteps: number;
  nextMilestone: string;
  estimatedCompletion: string;
}

// 学习步骤类型
interface LearningStep {
  id: number;
  title: string;
  description: string;
  type: 'theory' | 'practice' | 'assessment' | 'review';
  duration: number;
  isCompleted: boolean;
  resources: string[];
}

// 模拟数据
const mockLearningPaths: ExtendedLearningPath[] = [
  {
    id: 1,
    user_id: 1,
    subject_id: 1,
    name: '高中数学函数专项突破',
    description: '系统学习函数的概念、性质和应用，包括一次函数、二次函数、指数函数、对数函数等',
    target_knowledge_points: [1, 2, 3, 4, 5],
    estimated_duration: 30,
    difficulty_progression: [2, 3, 4, 4, 5],
    status: 'active',
    progress: 0.65,
    created_at: '2024-01-10',
    subjectName: '数学',
    completedSteps: 13,
    totalSteps: 20,
    nextMilestone: '二次函数综合应用',
    estimatedCompletion: '2024-02-15'
  },
  {
    id: 2,
    user_id: 1,
    subject_id: 2,
    name: '物理力学基础强化',
    description: '掌握力学基本概念和定律，包括运动学、动力学、功能关系等核心内容',
    target_knowledge_points: [6, 7, 8, 9],
    estimated_duration: 25,
    difficulty_progression: [3, 4, 4, 5],
    status: 'active',
    progress: 0.4,
    created_at: '2024-01-12',
    subjectName: '物理',
    completedSteps: 6,
    totalSteps: 15,
    nextMilestone: '牛顿定律应用',
    estimatedCompletion: '2024-02-20'
  },
  {
    id: 3,
    user_id: 1,
    subject_id: 3,
    name: '化学有机化合物入门',
    description: '学习有机化合物的结构、命名、性质和反应，为高考化学打下坚实基础',
    target_knowledge_points: [10, 11, 12],
    estimated_duration: 20,
    difficulty_progression: [3, 4, 5],
    status: 'completed',
    progress: 1.0,
    created_at: '2024-01-05',
    subjectName: '化学',
    completedSteps: 12,
    totalSteps: 12,
    nextMilestone: '已完成',
    estimatedCompletion: '已完成'
  }
];

const mockLearningSteps: LearningStep[] = [
  {
    id: 1,
    title: '函数的基本概念',
    description: '理解函数的定义、定义域、值域等基本概念',
    type: 'theory',
    duration: 45,
    isCompleted: true,
    resources: ['视频讲解', '练习题', '知识点总结']
  },
  {
    id: 2,
    title: '一次函数性质',
    description: '掌握一次函数的图像和性质',
    type: 'theory',
    duration: 60,
    isCompleted: true,
    resources: ['互动课件', '图像绘制工具']
  },
  {
    id: 3,
    title: '一次函数应用练习',
    description: '通过实际问题练习一次函数的应用',
    type: 'practice',
    duration: 90,
    isCompleted: true,
    resources: ['练习题库', '解题视频']
  },
  {
    id: 4,
    title: '二次函数概念',
    description: '学习二次函数的定义和基本形式',
    type: 'theory',
    duration: 50,
    isCompleted: false,
    resources: ['视频讲解', '动画演示']
  },
  {
    id: 5,
    title: '二次函数图像',
    description: '理解二次函数的图像特征和变换',
    type: 'theory',
    duration: 70,
    isCompleted: false,
    resources: ['图像工具', '变换动画']
  }
];

const LearningPathPage: React.FC = () => {
  const [learningPaths, setLearningPaths] = useState<ExtendedLearningPath[]>(mockLearningPaths);
  const [learningSteps, setLearningSteps] = useState<LearningStep[]>(mockLearningSteps);
  const [selectedPath, setSelectedPath] = useState<ExtendedLearningPath | null>(null);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [activeTab, setActiveTab] = useState('paths');
  const [form] = Form.useForm();

  useEffect(() => {
    // 模拟数据加载
    console.log('加载学习路径数据');
  }, []);

  const handleCreatePath = (values: any) => {
    const newPath: ExtendedLearningPath = {
      id: Date.now(),
      user_id: 1,
      subject_id: values.subject,
      name: values.name,
      description: values.description,
      target_knowledge_points: values.knowledgePoints || [],
      estimated_duration: values.duration,
      difficulty_progression: [values.difficulty],
      status: 'active',
      progress: 0,
      created_at: new Date().toISOString().split('T')[0],
      subjectName: getSubjectName(values.subject),
      completedSteps: 0,
      totalSteps: values.totalSteps || 10,
      nextMilestone: '开始学习',
      estimatedCompletion: new Date(Date.now() + values.duration * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    };

    setLearningPaths(prev => [...prev, newPath]);
    setCreateModalVisible(false);
    form.resetFields();
    message.success('学习路径创建成功！');
  };

  const handleStartPath = (path: ExtendedLearningPath) => {
    setLearningPaths(prev =>
      prev.map(p => p.id === path.id ? { ...p, status: 'active' as const } : p)
    );
    message.success('学习路径已开始！');
  };

  const handlePausePath = (path: ExtendedLearningPath) => {
    setLearningPaths(prev =>
      prev.map(p => p.id === path.id ? { ...p, status: 'paused' as const } : p)
    );
    message.success('学习路径已暂停！');
  };

  const handleDeletePath = (path: ExtendedLearningPath) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除学习路径「${path.name}」吗？`,
      onOk: () => {
        setLearningPaths(prev => prev.filter(p => p.id !== path.id));
        message.success('学习路径已删除！');
      }
    });
  };

  const getSubjectName = (subjectId: number) => {
    const subjects: Record<number, string> = {
      1: '数学',
      2: '物理',
      3: '化学',
      4: '生物'
    };
    return subjects[subjectId] || '未知科目';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'processing';
      case 'completed': return 'success';
      case 'paused': return 'warning';
      default: return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active': return '进行中';
      case 'completed': return '已完成';
      case 'paused': return '已暂停';
      default: return '未知状态';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'theory': return <BookOutlined />;
      case 'practice': return <EditOutlined />;
      case 'assessment': return <TrophyOutlined />;
      case 'review': return <StarOutlined />;
      default: return <BulbOutlined />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'theory': return 'blue';
      case 'practice': return 'green';
      case 'assessment': return 'orange';
      case 'review': return 'purple';
      default: return 'default';
    }
  };

  const renderPathList = () => (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总路径数"
              value={learningPaths.length}
              prefix={<RocketOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="进行中"
              value={learningPaths.filter(p => p.status === 'active').length}
              prefix={<PlayCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="已完成"
              value={learningPaths.filter(p => p.status === 'completed').length}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
               title="平均进度"
               value={Math.round(learningPaths.reduce((acc, p) => acc + p.progress, 0) / learningPaths.length * 100)}
               suffix="%"
               prefix={<AimOutlined />}
             />
          </Card>
        </Col>
      </Row>

      <Card title="我的学习路径" extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>
          创建路径
        </Button>
      }>
        <Row gutter={[16, 16]}>
          {learningPaths.map((path) => (
            <Col xs={24} md={12} lg={8} key={path.id}>
              <Card
                hoverable
                actions={[
                  <Tooltip title="查看详情">
                    <Button
                      type="text"
                      icon={<BookOutlined />}
                      onClick={() => {
                        setSelectedPath(path);
                        setDetailModalVisible(true);
                      }}
                    />
                  </Tooltip>,
                  path.status === 'active' ? (
                    <Tooltip title="暂停">
                      <Button
                        type="text"
                        icon={<PauseCircleOutlined />}
                        onClick={() => handlePausePath(path)}
                      />
                    </Tooltip>
                  ) : path.status === 'paused' ? (
                    <Tooltip title="继续">
                      <Button
                        type="text"
                        icon={<PlayCircleOutlined />}
                        onClick={() => handleStartPath(path)}
                      />
                    </Tooltip>
                  ) : null,
                  <Tooltip title="删除">
                    <Button
                      type="text"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => handleDeletePath(path)}
                    />
                  </Tooltip>
                ]}
              >
                <Card.Meta
                  avatar={
                    <Avatar style={{ backgroundColor: '#1890ff' }}>
                      {path.subjectName[0]}
                    </Avatar>
                  }
                  title={
                    <Space>
                      <Text strong>{path.name}</Text>
                      <Badge status={getStatusColor(path.status)} text={getStatusText(path.status)} />
                    </Space>
                  }
                  description={
                    <div>
                      <Paragraph ellipsis={{ rows: 2 }}>
                        {path.description}
                      </Paragraph>
                      <Space direction="vertical" size={8} style={{ width: '100%' }}>
                        <div>
                          <Text type="secondary">进度：</Text>
                          <Progress
                            percent={Math.round(path.progress * 100)}
                            size="small"
                            status={path.status === 'completed' ? 'success' : 'active'}
                          />
                        </div>
                        <div>
                          <Space>
                            <Text type="secondary">
                              <ClockCircleOutlined /> {path.estimated_duration}天
                            </Text>
                            <Text type="secondary">
                              {path.completedSteps}/{path.totalSteps}步骤
                            </Text>
                          </Space>
                        </div>
                        <div>
                          <Text type="secondary">下个里程碑：</Text>
                          <Text>{path.nextMilestone}</Text>
                        </div>
                      </Space>
                    </div>
                  }
                />
              </Card>
            </Col>
          ))}
        </Row>
      </Card>
    </div>
  );

  const renderRecommendations = () => (
    <Card title="智能推荐">
      <Row gutter={[16, 16]}>
        <Col xs={24} md={12}>
          <Card size="small" title="基于薄弱点推荐">
            <List
              size="small"
              dataSource={[
                { title: '三角函数专项训练', reason: '诊断发现三角函数掌握度较低' },
                { title: '立体几何强化', reason: '空间想象能力需要提升' },
                { title: '概率统计入门', reason: '该知识点尚未学习' }
              ]}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    <Button type="link" size="small">创建路径</Button>
                  ]}
                >
                  <List.Item.Meta
                    title={item.title}
                    description={item.reason}
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card size="small" title="热门学习路径">
            <List
              size="small"
              dataSource={[
                { title: '高考数学冲刺', users: 1250 },
                { title: '物理竞赛准备', users: 890 },
                { title: '化学实验技能', users: 670 }
              ]}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    <Button type="link" size="small">查看详情</Button>
                  ]}
                >
                  <List.Item.Meta
                    title={item.title}
                    description={`${item.users} 人正在学习`}
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </Card>
  );

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <RocketOutlined style={{ marginRight: 12 }} />
          智能学习路径
        </Title>
        <Text type="secondary">
          基于AI分析为您定制个性化学习路径，科学规划学习进度
        </Text>
      </div>

      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        items={[
          {
            key: 'paths',
            label: '我的路径',
            children: renderPathList()
          },
          {
            key: 'recommendations',
            label: '智能推荐',
            children: renderRecommendations()
          }
        ]}
      />

      {/* 创建路径模态框 */}
      <Modal
        title="创建学习路径"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        width={600}
      >
        <Form form={form} onFinish={handleCreatePath} layout="vertical">
          <Form.Item
            name="name"
            label="路径名称"
            rules={[{ required: true, message: '请输入路径名称' }]}
          >
            <Input placeholder="例如：高中数学函数专项突破" />
          </Form.Item>
          <Form.Item
            name="description"
            label="路径描述"
            rules={[{ required: true, message: '请输入路径描述' }]}
          >
            <TextArea rows={3} placeholder="描述学习路径的目标和内容" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="subject"
                label="学科"
                rules={[{ required: true, message: '请选择学科' }]}
              >
                <Select placeholder="选择学科">
                  <Option value={1}>数学</Option>
                  <Option value={2}>物理</Option>
                  <Option value={3}>化学</Option>
                  <Option value={4}>生物</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="duration"
                label="预计天数"
                rules={[{ required: true, message: '请输入预计天数' }]}
              >
                <Input type="number" placeholder="30" suffix="天" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="difficulty" label="难度等级">
            <Slider
              min={1}
              max={5}
              marks={{
                1: '入门',
                2: '基础',
                3: '中等',
                4: '困难',
                5: '专家'
              }}
              defaultValue={3}
            />
          </Form.Item>
          <Form.Item name="totalSteps" label="总步骤数">
            <Input type="number" placeholder="10" suffix="步" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 路径详情模态框 */}
      <Modal
        title={selectedPath?.name}
        open={detailModalVisible}
        onCancel={() => {
          setDetailModalVisible(false);
          setSelectedPath(null);
        }}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>,
          selectedPath?.status === 'active' && (
            <Button key="continue" type="primary">
              继续学习
            </Button>
          )
        ]}
        width={800}
      >
        {selectedPath && (
          <div>
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
              <Col span={8}>
                <Statistic title="总进度" value={Math.round(selectedPath.progress * 100)} suffix="%" />
              </Col>
              <Col span={8}>
                <Statistic title="已完成步骤" value={selectedPath.completedSteps} suffix={`/${selectedPath.totalSteps}`} />
              </Col>
              <Col span={8}>
                <Statistic title="预计完成" value={selectedPath.estimatedCompletion} />
              </Col>
            </Row>
            
            <Divider>学习步骤</Divider>
            <Steps direction="vertical" size="small" current={learningSteps.findIndex(step => !step.isCompleted)}>
              {learningSteps.map((step) => (
                <Step
                  key={step.id}
                  title={
                    <Space>
                      {step.title}
                      <Tag color={getTypeColor(step.type)} icon={getTypeIcon(step.type)}>
                        {step.type === 'theory' ? '理论' : 
                         step.type === 'practice' ? '练习' :
                         step.type === 'assessment' ? '测评' : '复习'}
                      </Tag>
                    </Space>
                  }
                  description={
                    <div>
                      <Text>{step.description}</Text>
                      <br />
                      <Text type="secondary">
                        <ClockCircleOutlined /> {step.duration}分钟
                      </Text>
                      <div style={{ marginTop: 8 }}>
                        <Text type="secondary">资源：</Text>
                         {step.resources.map((resource, index) => (
                           <Tag key={index}>{resource}</Tag>
                         ))}
                      </div>
                    </div>
                  }
                  status={step.isCompleted ? 'finish' : 'wait'}
                />
              ))}
            </Steps>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default LearningPathPage;