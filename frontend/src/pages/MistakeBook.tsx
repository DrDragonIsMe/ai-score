import React, { useState } from 'react';
import {
  Card,
  Table,
  Button,
  Tag,
  Space,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  Progress,
  Statistic,
  Row,
  Col,
  Tabs,
  List,
  Avatar,
  Typography,
  message,
  Tooltip,
  Badge,
  Popconfirm,
  Divider
} from 'antd';
import {
  BookOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import type { MistakeRecord, Subject } from '../types';

const { TextArea } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { Title, Text } = Typography;
const { TabPane } = Tabs;

// 学习分析数据类型
interface AnalysisData {
  totalMistakes: number;
  resolvedMistakes: number;
  averageReviewCount: number;
  masteryRate: number;
  subjectDistribution: { subject: string; count: number; color: string }[];
  weeklyProgress: { date: string; resolved: number; added: number }[];
}

// 模拟学科数据
const mockSubjects: Subject[] = [
  { id: 1, name: '数学', description: '数学学科', created_at: '2024-01-01' },
  { id: 2, name: '物理', description: '物理学科', created_at: '2024-01-01' },
  { id: 3, name: '化学', description: '化学学科', created_at: '2024-01-01' }
];

// 模拟数据
const mockMistakeRecords: MistakeRecord[] = [
  {
    id: 1,
    user_id: 1,
    question_id: 101,
    subject_id: 1,
    user_answer: 'B',
    correct_answer: 'A',
    mistake_type: '概念理解错误',
    analysis: '对函数单调性的概念理解不够深入，需要加强基础概念的学习。',
    is_resolved: false,
    review_count: 2,
    is_mastered: false,
    question_content: '函数f(x)=x²-2x+1在区间[0,2]上的单调性是？',
    notes: '需要重点复习函数单调性判断方法',
    difficulty_level: 3,
    created_at: '2024-01-15T10:30:00Z'
  },
  {
    id: 2,
    user_id: 1,
    question_id: 102,
    subject_id: 2,
    user_answer: '15N',
    correct_answer: '20N',
    mistake_type: '计算错误',
    analysis: '在计算合力时忘记考虑摩擦力的影响。',
    is_resolved: true,
    review_count: 4,
    is_mastered: true,
    question_content: '质量为2kg的物体在水平面上受到10N的水平推力，摩擦系数为0.2，求物体的加速度。',
    notes: '已掌握，注意力的完整性分析',
    difficulty_level: 4,
    created_at: '2024-01-14T14:20:00Z'
  },
  {
    id: 3,
    user_id: 1,
    question_id: 103,
    subject_id: 3,
    user_answer: '直线型',
    correct_answer: '三角锥型',
    mistake_type: '知识点混淆',
    analysis: '对分子空间构型的判断方法掌握不够熟练。',
    is_resolved: false,
    review_count: 1,
    is_mastered: false,
    question_content: 'NH3分子的空间构型是？',
    notes: '需要加强VSEPR理论的学习',
    difficulty_level: 2,
    created_at: '2024-01-13T09:15:00Z'
  }
];

const mockAnalysisData: AnalysisData = {
  totalMistakes: 15,
  resolvedMistakes: 8,
  averageReviewCount: 2.3,
  masteryRate: 53.3,
  subjectDistribution: [
    { subject: '数学', count: 6, color: '#1890ff' },
    { subject: '物理', count: 5, color: '#52c41a' },
    { subject: '化学', count: 4, color: '#faad14' }
  ],
  weeklyProgress: [
    { date: '2024-01-08', resolved: 2, added: 3 },
    { date: '2024-01-09', resolved: 1, added: 2 },
    { date: '2024-01-10', resolved: 3, added: 1 },
    { date: '2024-01-11', resolved: 2, added: 4 },
    { date: '2024-01-12', resolved: 4, added: 2 },
    { date: '2024-01-13', resolved: 1, added: 3 },
    { date: '2024-01-14', resolved: 3, added: 1 }
  ]
};

const MistakeBookPage: React.FC = () => {
  const [mistakeRecords, setMistakeRecords] = useState<MistakeRecord[]>(mockMistakeRecords);
  const [analysisData, setAnalysisData] = useState<AnalysisData>(mockAnalysisData);
  const [selectedRecord, setSelectedRecord] = useState<MistakeRecord | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [selectedSubject, setSelectedSubject] = useState<number | null>(null);
  const [mistakeType, setMistakeType] = useState<string | null>(null);
  const [resolvedFilter, setResolvedFilter] = useState<boolean | null>(null);
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();

  // 获取学科名称
  const getSubjectName = (subjectId: number) => {
    const subject = mockSubjects.find(s => s.id === subjectId);
    return subject ? subject.name : '未知学科';
  };

  // 获取难度文本
  const getDifficultyText = (level: number) => {
    const difficultyMap: { [key: number]: string } = {
      1: '基础',
      2: '基础',
      3: '中等',
      4: '困难',
      5: '困难'
    };
    return difficultyMap[level] || '未知';
  };

  // 获取复习状态
  const getReviewStatus = (record: MistakeRecord) => {
    if (record.is_mastered) return 'mastered';
    if (record.review_count > 0) return 'reviewing';
    return 'pending';
  };

  const handleAddMistake = (values: any) => {
    const newRecord: MistakeRecord = {
      id: Date.now(),
      user_id: 1,
      question_id: Date.now(),
      subject_id: values.subject_id,
      user_answer: values.user_answer,
      correct_answer: values.correct_answer,
      mistake_type: values.mistake_type,
      analysis: values.analysis,
      is_resolved: false,
      review_count: 0,
      is_mastered: false,
      question_content: values.question_content,
      notes: values.notes,
      difficulty_level: values.difficulty_level,
      created_at: new Date().toISOString()
    };
    
    setMistakeRecords(prev => [newRecord, ...prev]);
    setAddModalVisible(false);
    form.resetFields();
    message.success('错题添加成功！');
  };

  const handleEditMistake = (values: any) => {
    if (!selectedRecord) return;
    
    setMistakeRecords(prev =>
      prev.map(r => r.id === selectedRecord.id ? {
        ...r,
        ...values
      } : r)
    );
    setEditModalVisible(false);
    editForm.resetFields();
    message.success('错题更新成功！');
  };

  const handleMarkMastered = (record: MistakeRecord) => {
    setMistakeRecords(prev =>
      prev.map(r => r.id === record.id ? {
        ...r,
        is_mastered: true,
        is_resolved: true,
        review_count: r.review_count + 1
      } : r)
    );
    message.success('已标记为掌握！');
  };

  const handleStartReview = (record: MistakeRecord) => {
    setMistakeRecords(prev =>
      prev.map(r => r.id === record.id ? {
        ...r,
        review_count: r.review_count + 1
      } : r)
    );
    message.success('开始复习！');
  };

  const handleDeleteMistake = (record: MistakeRecord) => {
    setMistakeRecords(prev => prev.filter(r => r.id !== record.id));
    message.success('错题已删除！');
  };

  // 过滤数据
  const filteredRecords = mistakeRecords.filter(record => {
    if (selectedSubject && record.subject_id !== selectedSubject) return false;
    if (mistakeType && record.mistake_type !== mistakeType) return false;
    if (resolvedFilter !== null && record.is_resolved !== resolvedFilter) return false;
    return true;
  });

  // 表格列定义
  const columns = [
    {
      title: '题目内容',
      dataIndex: 'question_content',
      key: 'question_content',
      width: 300,
      render: (text: string) => (
        <Tooltip title={text}>
          <Text ellipsis style={{ maxWidth: 280 }}>{text}</Text>
        </Tooltip>
      )
    },
    {
      title: '学科',
      dataIndex: 'subject_id',
      key: 'subject_id',
      render: (subjectId: number) => (
        <Tag color="blue">{getSubjectName(subjectId)}</Tag>
      )
    },
    {
      title: '错误类型',
      dataIndex: 'mistake_type',
      key: 'mistake_type',
      render: (type: string) => <Tag color="orange">{type}</Tag>
    },
    {
      title: '难度',
      dataIndex: 'difficulty_level',
      key: 'difficulty_level',
      render: (level: number) => (
        <Tag color={level <= 2 ? 'green' : level <= 3 ? 'orange' : 'red'}>
          {getDifficultyText(level)}
        </Tag>
      )
    },
    {
      title: '复习次数',
      dataIndex: 'review_count',
      key: 'review_count',
      render: (count: number) => (
        <Badge count={count} style={{ backgroundColor: '#52c41a' }} />
      )
    },
    {
      title: '掌握程度',
      key: 'mastery',
      render: (record: MistakeRecord) => {
        const masteryLevel = Math.min(record.review_count * 20, 100);
        const status = getReviewStatus(record);
        return (
          <Progress
            percent={masteryLevel}
            size="small"
            status={status === 'mastered' ? 'success' : 'active'}
            format={() => `${masteryLevel}%`}
          />
        );
      }
    },
    {
      title: '状态',
      key: 'status',
      render: (record: MistakeRecord) => {
        const status = getReviewStatus(record);
        const statusConfig = {
          pending: { color: 'default', text: '待复习' },
          reviewing: { color: 'processing', text: '复习中' },
          mastered: { color: 'success', text: '已掌握' }
        };
        const config = statusConfig[status as keyof typeof statusConfig];
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: MistakeRecord) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => {
              setSelectedRecord(record);
              setDetailModalVisible(true);
            }}
          >
            查看
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => {
              setSelectedRecord(record);
              editForm.setFieldsValue(record);
              setEditModalVisible(true);
            }}
          >
            编辑
          </Button>
          {!record.is_mastered && (
            <Button
              type="link"
              icon={<CheckCircleOutlined />}
              onClick={() => handleMarkMastered(record)}
            >
              标记掌握
            </Button>
          )}
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteMistake(record)}
          >
            删除
          </Button>
        </Space>
      )
    }
  ];

  // 图表数据处理
  const subjectChartData = analysisData.subjectDistribution.map(item => ({
    ...item,
    percentage: Math.round((item.count / analysisData.totalMistakes) * 100)
  }));

  const weeklyChartData = analysisData.weeklyProgress.slice(-7);

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>
        <BookOutlined /> 错题本与学习分析
      </Title>

      <Tabs defaultActiveKey="mistakes">
        <TabPane tab="错题管理" key="mistakes">
          {/* 统计卡片 */}
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="总错题数"
                  value={analysisData.totalMistakes}
                  prefix={<ExclamationCircleOutlined />}
                  valueStyle={{ color: '#cf1322' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="已解决"
                  value={analysisData.resolvedMistakes}
                  prefix={<CheckCircleOutlined />}
                  valueStyle={{ color: '#3f8600' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="平均复习次数"
                  value={analysisData.averageReviewCount}
                  precision={1}
                  prefix={<ClockCircleOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="掌握率"
                  value={analysisData.masteryRate}
                  precision={1}
                  suffix="%"
                  prefix={<TrophyOutlined />}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
          </Row>

          {/* 筛选器 */}
          <Card style={{ marginBottom: 24 }}>
            <Space wrap>
              <Select
                placeholder="选择学科"
                style={{ width: 120 }}
                allowClear
                onChange={setSelectedSubject}
              >
                {mockSubjects.map(subject => (
                  <Option key={subject.id} value={subject.id}>
                    {subject.name}
                  </Option>
                ))}
              </Select>
              <Select
                placeholder="错误类型"
                style={{ width: 120 }}
                allowClear
                onChange={setMistakeType}
              >
                <Option value="概念理解错误">概念理解错误</Option>
                <Option value="计算错误">计算错误</Option>
                <Option value="知识点混淆">知识点混淆</Option>
                <Option value="审题不仔细">审题不仔细</Option>
              </Select>
              <Select
                placeholder="解决状态"
                style={{ width: 120 }}
                allowClear
                onChange={setResolvedFilter}
              >
                <Option value={true}>已解决</Option>
                <Option value={false}>未解决</Option>
              </Select>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setAddModalVisible(true)}
              >
                添加错题
              </Button>
            </Space>
          </Card>

          {/* 错题表格 */}
          <Card>
            <Table
              columns={columns}
              dataSource={filteredRecords}
              rowKey="id"
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条记录`
              }}
            />
          </Card>
        </TabPane>

        <TabPane tab="学习分析" key="analysis">
           <Row gutter={16}>
             <Col span={12}>
               <Card title="学科错题分布" extra={<BarChartOutlined />}>
                 <List
                   dataSource={subjectChartData}
                   renderItem={item => (
                     <List.Item>
                       <List.Item.Meta
                         avatar={<Avatar style={{ backgroundColor: item.color }}>{item.count}</Avatar>}
                         title={item.subject}
                         description={`${item.count}题 (${item.percentage}%)`}
                       />
                       <Progress percent={item.percentage} size="small" strokeColor={item.color} />
                     </List.Item>
                   )}
                 />
               </Card>
             </Col>
             <Col span={12}>
               <Card title="每周解决进度">
                 <List
                   dataSource={weeklyChartData}
                   renderItem={item => (
                     <List.Item>
                       <List.Item.Meta
                         title={new Date(item.date).toLocaleDateString()}
                         description={`解决 ${item.resolved}题，新增 ${item.added}题`}
                       />
                       <div>
                         <Text type="success">+{item.resolved}</Text>
                         <Text type="secondary" style={{ marginLeft: 8 }}>-{item.added}</Text>
                       </div>
                     </List.Item>
                   )}
                 />
               </Card>
             </Col>
           </Row>

          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col span={24}>
              <Card title="错题类型分析">
                <List
                  dataSource={[
                    { type: '概念理解错误', count: 6, percentage: 40 },
                    { type: '计算错误', count: 4, percentage: 27 },
                    { type: '知识点混淆', count: 3, percentage: 20 },
                    { type: '审题不仔细', count: 2, percentage: 13 }
                  ]}
                  renderItem={item => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={<Avatar style={{ backgroundColor: '#1890ff' }}>{item.count}</Avatar>}
                        title={item.type}
                        description={`占比 ${item.percentage}%`}
                      />
                      <Progress percent={item.percentage} size="small" />
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>

      {/* 错题详情模态框 */}
      <Modal
        title="错题详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>,
          selectedRecord && !selectedRecord.is_mastered && (
            <Button
              key="review"
              type="primary"
              onClick={() => {
                handleStartReview(selectedRecord);
                setDetailModalVisible(false);
              }}
            >
              开始复习
            </Button>
          )
        ]}
        width={800}
      >
        {selectedRecord && (
          <div>
            <Card size="small" title="题目信息" style={{ marginBottom: 16 }}>
              <p><strong>题目内容：</strong> {selectedRecord.question_content}</p>
              <p><strong>学科：</strong> {getSubjectName(selectedRecord.subject_id)}</p>
              <p><strong>难度：</strong> {getDifficultyText(selectedRecord.difficulty_level)}</p>
            </Card>
            
            <Card size="small" title="答题情况" style={{ marginBottom: 16 }}>
              <p><strong>我的答案：</strong> <Text type="danger">{selectedRecord.user_answer}</Text></p>
              <p><strong>正确答案：</strong> <Text type="success">{selectedRecord.correct_answer}</Text></p>
              <p><strong>错误类型：</strong> <Tag color="orange">{selectedRecord.mistake_type}</Tag></p>
            </Card>
            
            <Card size="small" title="分析与笔记" style={{ marginBottom: 16 }}>
              <p><strong>错误分析：</strong> {selectedRecord.analysis}</p>
              {selectedRecord.notes && (
                <p><strong>学习笔记：</strong> {selectedRecord.notes}</p>
              )}
            </Card>
            
            <Card size="small" title="复习记录">
              <p><strong>复习次数：</strong> {selectedRecord.review_count}</p>
              <p><strong>掌握状态：</strong> <Tag color={selectedRecord.is_mastered ? 'success' : 'processing'}>
                  {selectedRecord.is_mastered ? '已掌握' : '学习中'}
                </Tag>
              </p>
              <p><strong>创建时间：</strong> {new Date(selectedRecord.created_at).toLocaleString()}</p>
            </Card>
          </div>
        )}
      </Modal>

      {/* 添加错题模态框 */}
      <Modal
        title="添加错题"
        open={addModalVisible}
        onCancel={() => {
          setAddModalVisible(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleAddMistake}
        >
          <Form.Item
            name="question_content"
            label="题目内容"
            rules={[{ required: true, message: '请输入题目内容' }]}
          >
            <TextArea rows={3} placeholder="请输入题目内容" />
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="subject_id"
                label="学科"
                rules={[{ required: true, message: '请选择学科' }]}
              >
                <Select placeholder="选择学科">
                  {mockSubjects.map(subject => (
                    <Option key={subject.id} value={subject.id}>
                      {subject.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="difficulty_level"
                label="难度等级"
                rules={[{ required: true, message: '请选择难度等级' }]}
              >
                <Select placeholder="选择难度">
                  <Option value={1}>基础</Option>
                  <Option value={2}>基础</Option>
                  <Option value={3}>中等</Option>
                  <Option value={4}>困难</Option>
                  <Option value={5}>困难</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="user_answer"
                label="我的答案"
                rules={[{ required: true, message: '请输入你的答案' }]}
              >
                <Input placeholder="请输入你的答案" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="correct_answer"
                label="正确答案"
                rules={[{ required: true, message: '请输入正确答案' }]}
              >
                <Input placeholder="请输入正确答案" />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item
            name="mistake_type"
            label="错误类型"
            rules={[{ required: true, message: '请选择错误类型' }]}
          >
            <Select placeholder="选择错误类型">
              <Option value="概念理解错误">概念理解错误</Option>
              <Option value="计算错误">计算错误</Option>
              <Option value="知识点混淆">知识点混淆</Option>
              <Option value="审题不仔细">审题不仔细</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="analysis"
            label="错误分析"
          >
            <TextArea rows={3} placeholder="分析错误原因和改进方法" />
          </Form.Item>
          
          <Form.Item
            name="notes"
            label="学习笔记"
          >
            <TextArea rows={2} placeholder="记录学习心得和注意事项" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑错题模态框 */}
      <Modal
        title="编辑错题"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          editForm.resetFields();
        }}
        onOk={() => editForm.submit()}
        width={600}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleEditMistake}
        >
          <Form.Item
            name="question_content"
            label="题目内容"
            rules={[{ required: true, message: '请输入题目内容' }]}
          >
            <TextArea rows={3} placeholder="请输入题目内容" />
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="subject_id"
                label="学科"
                rules={[{ required: true, message: '请选择学科' }]}
              >
                <Select placeholder="选择学科">
                  {mockSubjects.map(subject => (
                    <Option key={subject.id} value={subject.id}>
                      {subject.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="difficulty_level"
                label="难度等级"
                rules={[{ required: true, message: '请选择难度等级' }]}
              >
                <Select placeholder="选择难度">
                  <Option value={1}>基础</Option>
                  <Option value={2}>基础</Option>
                  <Option value={3}>中等</Option>
                  <Option value={4}>困难</Option>
                  <Option value={5}>困难</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="user_answer"
                label="我的答案"
                rules={[{ required: true, message: '请输入你的答案' }]}
              >
                <Input placeholder="请输入你的答案" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="correct_answer"
                label="正确答案"
                rules={[{ required: true, message: '请输入正确答案' }]}
              >
                <Input placeholder="请输入正确答案" />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item
            name="mistake_type"
            label="错误类型"
            rules={[{ required: true, message: '请选择错误类型' }]}
          >
            <Select placeholder="选择错误类型">
              <Option value="概念理解错误">概念理解错误</Option>
              <Option value="计算错误">计算错误</Option>
              <Option value="知识点混淆">知识点混淆</Option>
              <Option value="审题不仔细">审题不仔细</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="analysis"
            label="错误分析"
          >
            <TextArea rows={3} placeholder="分析错误原因和改进方法" />
          </Form.Item>
          
          <Form.Item
            name="notes"
            label="学习笔记"
          >
            <TextArea rows={2} placeholder="记录学习心得和注意事项" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default MistakeBookPage;