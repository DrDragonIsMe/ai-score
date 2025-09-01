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
  Radio,
  Checkbox,
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
  Divider,
  Steps,
  Alert
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
  BarChartOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  FileTextOutlined,
  StarOutlined
} from '@ant-design/icons';
import type { ExamSession, Question, Subject } from '../types';

const { TextArea } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { Title, Text } = Typography;
// const { TabPane } = Tabs; // 已弃用，改用items属性
const { Step } = Steps;

// 扩展考试会话类型
interface ExtendedExamSession extends ExamSession {
  subjectName?: string;
  questionCount?: number;
  passedCount?: number;
  accuracy?: number;
}

// 考试统计数据类型
interface ExamStats {
  totalExams: number;
  completedExams: number;
  averageScore: number;
  passRate: number;
  subjectPerformance: { subject: string; score: number; count: number }[];
  recentExams: { date: string; score: number; subject: string }[];
}

// 模拟学科数据
const mockSubjects: Subject[] = [
  { id: 1, name: '数学', description: '数学学科', created_at: '2024-01-01' },
  { id: 2, name: '物理', description: '物理学科', created_at: '2024-01-01' },
  { id: 3, name: '化学', description: '化学学科', created_at: '2024-01-01' }
];

// 模拟考试数据
const mockExamSessions: ExtendedExamSession[] = [
  {
    id: 1,
    user_id: 1,
    exam_type: 'practice',
    subject_id: 1,
    total_questions: 20,
    correct_answers: 16,
    score: 80,
    time_spent: 1800,
    started_at: '2024-01-15T10:00:00Z',
    completed_at: '2024-01-15T10:30:00Z',
    subjectName: '数学',
    questionCount: 20,
    passedCount: 16,
    accuracy: 80
  },
  {
    id: 2,
    user_id: 1,
    exam_type: 'formal',
    subject_id: 2,
    total_questions: 25,
    correct_answers: 20,
    score: 85,
    time_spent: 2400,
    started_at: '2024-01-14T14:00:00Z',
    completed_at: '2024-01-14T14:40:00Z',
    subjectName: '物理',
    questionCount: 25,
    passedCount: 20,
    accuracy: 85
  },
  {
    id: 3,
    user_id: 1,
    exam_type: 'practice',
    subject_id: 3,
    total_questions: 15,
    correct_answers: 12,
    score: 75,
    time_spent: 1200,
    started_at: '2024-01-13T09:00:00Z',
    completed_at: '2024-01-13T09:20:00Z',
    subjectName: '化学',
    questionCount: 15,
    passedCount: 12,
    accuracy: 75
  }
];

// 模拟题目数据
const mockQuestions: Question[] = [
  {
    id: 1,
    subject_id: 1,
    knowledge_point_ids: [1, 2],
    content: '函数f(x)=x²-2x+1的最小值是？',
    question_type: 'single_choice',
    options: ['0', '1', '-1', '2'],
    correct_answer: '0',
    difficulty_level: 3,
    explanation: '这是一个二次函数，开口向上，顶点为(1,0)，所以最小值为0。',
    created_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 2,
    subject_id: 1,
    knowledge_point_ids: [3],
    content: '求导数：f(x)=3x²+2x-1，f\'(x)=？',
    question_type: 'single_choice',
    options: ['6x+2', '3x+2', '6x-1', '3x-1'],
    correct_answer: '6x+2',
    difficulty_level: 2,
    explanation: '根据求导法则，f\'(x)=6x+2。',
    created_at: '2024-01-01T00:00:00Z'
  }
];

// 模拟统计数据
const mockExamStats: ExamStats = {
  totalExams: 15,
  completedExams: 12,
  averageScore: 78.5,
  passRate: 80,
  subjectPerformance: [
    { subject: '数学', score: 82, count: 5 },
    { subject: '物理', score: 78, count: 4 },
    { subject: '化学', score: 75, count: 3 }
  ],
  recentExams: [
    { date: '2024-01-15', score: 80, subject: '数学' },
    { date: '2024-01-14', score: 85, subject: '物理' },
    { date: '2024-01-13', score: 75, subject: '化学' },
    { date: '2024-01-12', score: 88, subject: '数学' },
    { date: '2024-01-11', score: 72, subject: '物理' }
  ]
};

const ExamPage: React.FC = () => {
  const [examSessions, setExamSessions] = useState<ExtendedExamSession[]>(mockExamSessions);
  const [currentQuestions, setCurrentQuestions] = useState<Question[]>(mockQuestions);
  const [examStats] = useState<ExamStats>(mockExamStats);
  const [isExamModalVisible, setIsExamModalVisible] = useState(false);
  const [isQuestionModalVisible, setIsQuestionModalVisible] = useState(false);
  const [currentExam, setCurrentExam] = useState<ExtendedExamSession | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState<Record<number, string>>({});
  const [examInProgress, setExamInProgress] = useState(false);
  const [examTimeLeft, setExamTimeLeft] = useState(3600); // 60分钟
  const [form] = Form.useForm();

  // 考试会话表格列配置
  const examColumns = [
    {
      title: '考试ID',
      dataIndex: 'id',
      key: 'id',
      width: 80
    },
    {
      title: '学科',
      dataIndex: 'subjectName',
      key: 'subjectName',
      render: (text: string) => <Tag color="blue">{text}</Tag>
    },
    {
      title: '考试类型',
      dataIndex: 'exam_type',
      key: 'exam_type',
      render: (type: string) => (
        <Tag color={type === 'formal' ? 'red' : 'green'}>
          {type === 'formal' ? '正式考试' : '练习考试'}
        </Tag>
      )
    },
    {
      title: '题目数量',
      dataIndex: 'total_questions',
      key: 'total_questions'
    },
    {
      title: '正确数量',
      dataIndex: 'correct_answers',
      key: 'correct_answers',
      render: (correct: number, record: ExtendedExamSession) => (
        <span style={{ color: correct >= record.total_questions * 0.6 ? '#52c41a' : '#ff4d4f' }}>
          {correct}/{record.total_questions}
        </span>
      )
    },
    {
      title: '得分',
      dataIndex: 'score',
      key: 'score',
      render: (score: number) => (
        <span style={{ color: score >= 60 ? '#52c41a' : '#ff4d4f', fontWeight: 'bold' }}>
          {score}分
        </span>
      )
    },
    {
      title: '用时',
      dataIndex: 'time_spent',
      key: 'time_spent',
      render: (time: number) => `${Math.floor(time / 60)}分${time % 60}秒`
    },
    {
      title: '开始时间',
      dataIndex: 'started_at',
      key: 'started_at',
      render: (date: string) => new Date(date).toLocaleString()
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: ExtendedExamSession) => (
        <Space size="middle">
          <Tooltip title="查看详情">
            <Button
              type="link"
              icon={<EyeOutlined />}
              onClick={() => handleViewExam(record)}
            />
          </Tooltip>
          <Tooltip title="重新考试">
            <Button
              type="link"
              icon={<PlayCircleOutlined />}
              onClick={() => handleRetakeExam(record)}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  // 处理创建新考试
  const handleCreateExam = () => {
    setIsExamModalVisible(true);
    form.resetFields();
  };

  // 处理开始考试
  const handleStartExam = async (values: any) => {
    try {
      // 这里应该调用API获取题目
      setCurrentQuestions(mockQuestions.slice(0, values.questionCount));
      setCurrentQuestionIndex(0);
      setUserAnswers({});
      setExamInProgress(true);
      setExamTimeLeft(values.timeLimit * 60);
      setIsExamModalVisible(false);
      setIsQuestionModalVisible(true);
      message.success('考试已开始！');
    } catch (error) {
      message.error('开始考试失败');
    }
  };

  // 处理查看考试详情
  const handleViewExam = (exam: ExtendedExamSession) => {
    setCurrentExam(exam);
    // 这里可以打开详情模态框
    message.info(`查看考试 ${exam.id} 的详情`);
  };

  // 处理重新考试
  const handleRetakeExam = (exam: ExtendedExamSession) => {
    setCurrentExam(exam);
    setIsExamModalVisible(true);
    form.setFieldsValue({
      subjectId: exam.subject_id,
      examType: exam.exam_type,
      questionCount: exam.total_questions,
      timeLimit: 60
    });
  };

  // 处理答题
  const handleAnswerQuestion = (questionId: number, answer: string) => {
    setUserAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
  };

  // 处理下一题
  const handleNextQuestion = () => {
    if (currentQuestionIndex < currentQuestions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    } else {
      handleSubmitExam();
    }
  };

  // 处理上一题
  const handlePrevQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  };

  // 处理提交考试
  const handleSubmitExam = () => {
    Modal.confirm({
      title: '确认提交',
      content: '确定要提交考试吗？提交后将无法修改答案。',
      onOk: () => {
        // 计算得分
        let correctCount = 0;
        currentQuestions.forEach(question => {
          if (userAnswers[question.id] === question.correct_answer) {
            correctCount++;
          }
        });
        
        const score = Math.round((correctCount / currentQuestions.length) * 100);
        
        // 创建新的考试记录
        const newExam: ExtendedExamSession = {
          id: Date.now(),
          user_id: 1,
          exam_type: 'practice',
          subject_id: 1,
          total_questions: currentQuestions.length,
          correct_answers: correctCount,
          score,
          time_spent: 3600 - examTimeLeft,
          started_at: new Date().toISOString(),
          completed_at: new Date().toISOString(),
          subjectName: '数学',
          questionCount: currentQuestions.length,
          passedCount: correctCount,
          accuracy: score
        };
        
        setExamSessions(prev => [newExam, ...prev]);
        setExamInProgress(false);
        setIsQuestionModalVisible(false);
        
        message.success(`考试完成！得分：${score}分`);
      }
    });
  };

  // 格式化时间
  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <TrophyOutlined style={{ marginRight: 8 }} />
          考试测评
        </Title>
        <Text type="secondary">在线考试系统，支持练习和正式考试</Text>
      </div>

      <Tabs 
        defaultActiveKey="exams"
        items={[
          {
            key: 'exams',
            label: '考试记录',
            children: (
              <Card>
                <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Space>
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={handleCreateExam}
                    >
                      开始新考试
                    </Button>
                  </Space>
                </div>
                
                <Table
                  columns={examColumns}
                  dataSource={examSessions}
                  rowKey="id"
                  pagination={{
                    pageSize: 10,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total) => `共 ${total} 条记录`
                  }}
                />
              </Card>
            )
          },
          {
            key: 'analysis',
            label: '成绩分析',
            children: (
              <>
                <Row gutter={16}>
                  <Col span={6}>
                    <Card>
                      <Statistic
                        title="总考试次数"
                        value={examStats.totalExams}
                        prefix={<BookOutlined />}
                      />
                    </Card>
                  </Col>
                  <Col span={6}>
                    <Card>
                      <Statistic
                        title="完成考试"
                        value={examStats.completedExams}
                        prefix={<CheckCircleOutlined />}
                        suffix={`/ ${examStats.totalExams}`}
                      />
                    </Card>
                  </Col>
                  <Col span={6}>
                    <Card>
                      <Statistic
                        title="平均分数"
                        value={examStats.averageScore}
                        precision={1}
                        prefix={<StarOutlined />}
                        suffix="分"
                      />
                    </Card>
                  </Col>
                  <Col span={6}>
                    <Card>
                      <Statistic
                        title="通过率"
                        value={examStats.passRate}
                        prefix={<TrophyOutlined />}
                        suffix="%"
                      />
                    </Card>
                  </Col>
                </Row>

                <Row gutter={16} style={{ marginTop: 16 }}>
                  <Col span={12}>
                    <Card title="学科表现" extra={<BarChartOutlined />}>
                      <List
                        dataSource={examStats.subjectPerformance}
                        renderItem={item => (
                          <List.Item>
                            <List.Item.Meta
                              avatar={<Avatar style={{ backgroundColor: '#1890ff' }}>{item.count}</Avatar>}
                              title={item.subject}
                              description={`平均分：${item.score}分，考试${item.count}次`}
                            />
                            <Progress percent={item.score} size="small" />
                          </List.Item>
                        )}
                      />
                    </Card>
                  </Col>
                  <Col span={12}>
                    <Card title="最近考试">
                      <List
                        dataSource={examStats.recentExams}
                        renderItem={item => (
                          <List.Item>
                            <List.Item.Meta
                              title={new Date(item.date).toLocaleDateString()}
                              description={item.subject}
                            />
                            <div>
                              <Text strong style={{ color: item.score >= 60 ? '#52c41a' : '#ff4d4f' }}>
                                {item.score}分
                              </Text>
                            </div>
                          </List.Item>
                        )}
                      />
                    </Card>
                  </Col>
                </Row>
              </>
            )
          }
        ]}
      />

      {/* 创建考试模态框 */}
      <Modal
        title="开始新考试"
        open={isExamModalVisible}
        onCancel={() => setIsExamModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleStartExam}
        >
          <Form.Item
            name="subjectId"
            label="选择学科"
            rules={[{ required: true, message: '请选择学科' }]}
          >
            <Select placeholder="请选择学科">
              {mockSubjects.map(subject => (
                <Option key={subject.id} value={subject.id}>
                  {subject.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="examType"
            label="考试类型"
            rules={[{ required: true, message: '请选择考试类型' }]}
          >
            <Radio.Group>
              <Radio value="practice">练习考试</Radio>
              <Radio value="formal">正式考试</Radio>
            </Radio.Group>
          </Form.Item>

          <Form.Item
            name="questionCount"
            label="题目数量"
            rules={[{ required: true, message: '请选择题目数量' }]}
          >
            <Select placeholder="请选择题目数量">
              <Option value={10}>10题</Option>
              <Option value={20}>20题</Option>
              <Option value={30}>30题</Option>
              <Option value={50}>50题</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="timeLimit"
            label="考试时长（分钟）"
            rules={[{ required: true, message: '请选择考试时长' }]}
          >
            <Select placeholder="请选择考试时长">
              <Option value={30}>30分钟</Option>
              <Option value={60}>60分钟</Option>
              <Option value={90}>90分钟</Option>
              <Option value={120}>120分钟</Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                开始考试
              </Button>
              <Button onClick={() => setIsExamModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 答题模态框 */}
      <Modal
        title={`考试进行中 - 第${currentQuestionIndex + 1}题 / 共${currentQuestions.length}题`}
        open={isQuestionModalVisible}
        onCancel={() => {
          Modal.confirm({
            title: '确认退出',
            content: '确定要退出考试吗？当前进度将不会保存。',
            onOk: () => {
              setExamInProgress(false);
              setIsQuestionModalVisible(false);
            }
          });
        }}
        footer={null}
        width={800}
        closable={false}
      >
        {currentQuestions.length > 0 && (
          <div>
            <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Steps current={currentQuestionIndex} size="small" style={{ flex: 1 }}>
                {currentQuestions.map((_, index) => (
                  <Step key={index} />
                ))}
              </Steps>
              <div style={{ marginLeft: 16 }}>
                <Text strong>剩余时间：{formatTime(examTimeLeft)}</Text>
              </div>
            </div>

            <Alert
              message={`难度等级：${currentQuestions[currentQuestionIndex]?.difficulty_level || 1}星`}
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Card>
              <div style={{ marginBottom: 24 }}>
                <Title level={4}>
                  题目 {currentQuestionIndex + 1}：
                </Title>
                <div style={{ fontSize: 16, lineHeight: 1.6 }}>
                  {currentQuestions[currentQuestionIndex]?.content}
                </div>
              </div>

              {currentQuestions[currentQuestionIndex]?.question_type === 'single_choice' && (
                <Radio.Group
                  value={userAnswers[currentQuestions[currentQuestionIndex]?.id]}
                  onChange={(e) => handleAnswerQuestion(currentQuestions[currentQuestionIndex]?.id, e.target.value)}
                  style={{ width: '100%' }}
                >
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {currentQuestions[currentQuestionIndex]?.options?.map((option, index) => (
                      <Radio key={index} value={option} style={{ fontSize: 16, padding: '8px 0' }}>
                        {String.fromCharCode(65 + index)}. {option}
                      </Radio>
                    ))}
                  </Space>
                </Radio.Group>
              )}
            </Card>

            <div style={{ marginTop: 24, display: 'flex', justifyContent: 'space-between' }}>
              <Button
                disabled={currentQuestionIndex === 0}
                onClick={handlePrevQuestion}
              >
                上一题
              </Button>
              
              <div>
                <Text type="secondary">
                  已答题：{Object.keys(userAnswers).length} / {currentQuestions.length}
                </Text>
              </div>

              <Button
                type="primary"
                onClick={handleNextQuestion}
              >
                {currentQuestionIndex === currentQuestions.length - 1 ? '提交考试' : '下一题'}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default ExamPage;