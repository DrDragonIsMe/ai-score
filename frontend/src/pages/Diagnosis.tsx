import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Radio,
  Progress,
  Typography,
  Space,
  Row,
  Col,
  Alert,
  Modal,
  Select,
  Divider,
  Tag,
  Result,
} from 'antd';
import {
  PlayCircleOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  TrophyOutlined,
  BookOutlined,
} from '@ant-design/icons';
import type { Question, DiagnosisSession, DiagnosisResult } from '../types';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

interface DiagnosisState {
  session: DiagnosisSession | null;
  currentQuestion: Question | null;
  currentQuestionIndex: number;
  userAnswers: Record<number, string | string[]>;
  timeRemaining: number;
  isCompleted: boolean;
  result: DiagnosisResult | null;
}

const Diagnosis: React.FC = () => {
  const [selectedSubject, setSelectedSubject] = useState<number | null>(null);
  const [diagnosisState, setDiagnosisState] = useState<DiagnosisState>({
    session: null,
    currentQuestion: null,
    currentQuestionIndex: 0,
    userAnswers: {},
    timeRemaining: 0,
    isCompleted: false,
    result: null,
  });
  const [isStarted, setIsStarted] = useState(false);
  const [loading, setLoading] = useState(false);

  // 模拟数据
  const subjects = [
    { id: 1, name: '数学', description: '代数、几何、微积分等' },
    { id: 2, name: '英语', description: '语法、词汇、阅读理解等' },
    { id: 3, name: '物理', description: '力学、电磁学、光学等' },
    { id: 4, name: '化学', description: '有机化学、无机化学等' },
    { id: 5, name: '生物', description: '细胞生物学、遗传学等' },
  ];

  const mockQuestions: Question[] = [
    {
      id: 1,
      subject_id: 1,
      knowledge_point_ids: [1, 2],
      type: 'single_choice',
      difficulty: 3,
      content: '下列哪个函数是奇函数？',
      options: ['f(x) = x²', 'f(x) = x³', 'f(x) = |x|', 'f(x) = x² + 1'],
      correct_answer: 'f(x) = x³',
      explanation: '奇函数满足f(-x) = -f(x)，只有x³满足这个条件。',
      created_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 2,
      subject_id: 1,
      knowledge_point_ids: [3],
      type: 'single_choice',
      difficulty: 2,
      content: '求导数：d/dx(x² + 3x + 1) = ?',
      options: ['2x + 3', 'x² + 3', '2x + 1', 'x + 3'],
      correct_answer: '2x + 3',
      explanation: '多项式求导：每一项的系数乘以指数，指数减1。',
      created_at: '2024-01-01T00:00:00Z',
    },
  ];

  // 计时器
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isStarted && diagnosisState.timeRemaining > 0 && !diagnosisState.isCompleted) {
      timer = setInterval(() => {
        setDiagnosisState(prev => {
          if (prev.timeRemaining <= 1) {
            // 时间到，自动提交
            handleSubmitDiagnosis();
            return { ...prev, timeRemaining: 0 };
          }
          return { ...prev, timeRemaining: prev.timeRemaining - 1 };
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [isStarted, diagnosisState.timeRemaining, diagnosisState.isCompleted]);

  const startDiagnosis = async () => {
    if (!selectedSubject) return;
    
    setLoading(true);
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const session: DiagnosisSession = {
        id: Date.now(),
        user_id: 1,
        subject_id: selectedSubject,
        status: 'in_progress',
        total_questions: mockQuestions.length,
        answered_questions: 0,
        created_at: new Date().toISOString(),
      };

      setDiagnosisState({
        session,
        currentQuestion: mockQuestions[0],
        currentQuestionIndex: 0,
        userAnswers: {},
        timeRemaining: 1800, // 30分钟
        isCompleted: false,
        result: null,
      });
      setIsStarted(true);
    } catch (error) {
      console.error('启动诊断失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (value: string) => {
    if (!diagnosisState.currentQuestion) return;
    
    setDiagnosisState(prev => ({
      ...prev,
      userAnswers: {
        ...prev.userAnswers,
        [prev.currentQuestion!.id]: value,
      },
    }));
  };

  const nextQuestion = () => {
    const nextIndex = diagnosisState.currentQuestionIndex + 1;
    if (nextIndex < mockQuestions.length) {
      setDiagnosisState(prev => ({
        ...prev,
        currentQuestion: mockQuestions[nextIndex],
        currentQuestionIndex: nextIndex,
      }));
    } else {
      handleSubmitDiagnosis();
    }
  };

  const prevQuestion = () => {
    const prevIndex = diagnosisState.currentQuestionIndex - 1;
    if (prevIndex >= 0) {
      setDiagnosisState(prev => ({
        ...prev,
        currentQuestion: mockQuestions[prevIndex],
        currentQuestionIndex: prevIndex,
      }));
    }
  };

  const handleSubmitDiagnosis = async () => {
    setLoading(true);
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 计算结果
      const correctAnswers = mockQuestions.filter(q => 
        diagnosisState.userAnswers[q.id] === q.correct_answer
      ).length;
      
      const result: DiagnosisResult = {
        id: Date.now(),
        session_id: diagnosisState.session!.id,
        overall_score: Math.round((correctAnswers / mockQuestions.length) * 100),
        knowledge_mastery: { 1: 80, 2: 60, 3: 90 },
        weak_points: [2],
        strong_points: [1, 3],
        recommendations: [
          '建议加强代数基础练习',
          '可以尝试更多几何题目',
          '继续保持微积分的学习',
        ],
        created_at: new Date().toISOString(),
      };

      setDiagnosisState(prev => ({
        ...prev,
        isCompleted: true,
        result,
      }));
    } catch (error) {
      console.error('提交诊断失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const restartDiagnosis = () => {
    setIsStarted(false);
    setSelectedSubject(null);
    setDiagnosisState({
      session: null,
      currentQuestion: null,
      currentQuestionIndex: 0,
      userAnswers: {},
      timeRemaining: 0,
      isCompleted: false,
      result: null,
    });
  };

  // 如果诊断已完成，显示结果
  if (diagnosisState.isCompleted && diagnosisState.result) {
    return (
      <div>
        <Result
          icon={<TrophyOutlined style={{ color: '#52c41a' }} />}
          title="诊断完成！"
          subTitle={`您的总体得分：${diagnosisState.result.overall_score}分`}
          extra={[
            <Button type="primary" key="restart" onClick={restartDiagnosis}>
              重新诊断
            </Button>,
            <Button key="path" onClick={() => window.location.href = '/learning-path'}>
              查看学习路径
            </Button>,
          ]}
        />
        
        <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
          <Col xs={24} lg={12}>
            <Card title="知识点掌握情况">
              <Space direction="vertical" style={{ width: '100%' }}>
                {Object.entries(diagnosisState.result.knowledge_mastery).map(([pointId, mastery]) => (
                  <div key={pointId}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <Text>知识点 {pointId}</Text>
                      <Text strong>{mastery}%</Text>
                    </div>
                    <Progress percent={mastery} strokeColor={mastery >= 80 ? '#52c41a' : mastery >= 60 ? '#faad14' : '#ff4d4f'} />
                  </div>
                ))}
              </Space>
            </Card>
          </Col>
          
          <Col xs={24} lg={12}>
            <Card title="学习建议">
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <Text strong style={{ color: '#52c41a' }}>优势领域：</Text>
                  <div style={{ marginTop: 8 }}>
                    {diagnosisState.result.strong_points.map(point => (
                      <Tag key={point} color="green">知识点 {point}</Tag>
                    ))}
                  </div>
                </div>
                
                <div>
                  <Text strong style={{ color: '#ff4d4f' }}>薄弱环节：</Text>
                  <div style={{ marginTop: 8 }}>
                    {diagnosisState.result.weak_points.map(point => (
                      <Tag key={point} color="red">知识点 {point}</Tag>
                    ))}
                  </div>
                </div>
                
                <Divider />
                
                <div>
                  <Text strong>个性化建议：</Text>
                  <ul style={{ marginTop: 8 }}>
                    {diagnosisState.result.recommendations.map((rec, index) => (
                      <li key={index}>{rec}</li>
                    ))}
                  </ul>
                </div>
              </Space>
            </Card>
          </Col>
        </Row>
      </div>
    );
  }

  // 如果诊断已开始，显示题目
  if (isStarted && diagnosisState.currentQuestion) {
    const progress = ((diagnosisState.currentQuestionIndex + 1) / mockQuestions.length) * 100;
    const isAnswered = diagnosisState.userAnswers[diagnosisState.currentQuestion.id] !== undefined;
    
    return (
      <div>
        {/* 顶部信息栏 */}
        <Card style={{ marginBottom: 16 }}>
          <Row justify="space-between" align="middle">
            <Col>
              <Space>
                <Text strong>题目进度：</Text>
                <Text>{diagnosisState.currentQuestionIndex + 1} / {mockQuestions.length}</Text>
              </Space>
            </Col>
            <Col>
              <Space>
                <ClockCircleOutlined />
                <Text strong style={{ color: diagnosisState.timeRemaining < 300 ? '#ff4d4f' : '#1890ff' }}>
                  {formatTime(diagnosisState.timeRemaining)}
                </Text>
              </Space>
            </Col>
          </Row>
          <Progress percent={progress} strokeColor="#1890ff" style={{ marginTop: 16 }} />
        </Card>

        {/* 题目卡片 */}
        <Card>
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <div>
              <Space>
                <Tag color="blue">难度: {diagnosisState.currentQuestion.difficulty}/5</Tag>
                <Tag color="green">{diagnosisState.currentQuestion.type}</Tag>
              </Space>
            </div>
            
            <Title level={4}>
              {diagnosisState.currentQuestionIndex + 1}. {diagnosisState.currentQuestion.content}
            </Title>
            
            {diagnosisState.currentQuestion.type === 'single_choice' && (
              <Radio.Group
                value={diagnosisState.userAnswers[diagnosisState.currentQuestion.id]}
                onChange={(e) => handleAnswerChange(e.target.value)}
                style={{ width: '100%' }}
              >
                <Space direction="vertical" style={{ width: '100%' }}>
                  {diagnosisState.currentQuestion.options?.map((option, index) => (
                    <Radio key={index} value={option} style={{ padding: '8px 0' }}>
                      {option}
                    </Radio>
                  ))}
                </Space>
              </Radio.Group>
            )}
            
            <Row justify="space-between" style={{ marginTop: 24 }}>
              <Col>
                <Button 
                  onClick={prevQuestion} 
                  disabled={diagnosisState.currentQuestionIndex === 0}
                >
                  上一题
                </Button>
              </Col>
              <Col>
                <Space>
                  {diagnosisState.currentQuestionIndex === mockQuestions.length - 1 ? (
                    <Button 
                      type="primary" 
                      onClick={handleSubmitDiagnosis}
                      loading={loading}
                      disabled={!isAnswered}
                    >
                      提交诊断
                    </Button>
                  ) : (
                    <Button 
                      type="primary" 
                      onClick={nextQuestion}
                      disabled={!isAnswered}
                    >
                      下一题
                    </Button>
                  )}
                </Space>
              </Col>
            </Row>
          </Space>
        </Card>
      </div>
    );
  }

  // 初始选择界面
  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>学习诊断</Title>
        <Paragraph type="secondary">
          通过智能诊断测试，我们将评估您的知识掌握情况，为您制定个性化的学习路径。
        </Paragraph>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="选择诊断科目" extra={<BookOutlined />}>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <Alert
                message="诊断说明"
                description="本次诊断包含多道题目，预计用时30分钟。请在安静的环境中完成，以确保结果的准确性。"
                type="info"
                showIcon
              />
              
              <div>
                <Text strong style={{ marginBottom: 16, display: 'block' }}>请选择要诊断的科目：</Text>
                <Select
                  placeholder="选择科目"
                  style={{ width: '100%' }}
                  size="large"
                  value={selectedSubject}
                  onChange={setSelectedSubject}
                >
                  {subjects.map(subject => (
                    <Option key={subject.id} value={subject.id}>
                      <Space>
                        <BookOutlined />
                        <div>
                          <div>{subject.name}</div>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {subject.description}
                          </Text>
                        </div>
                      </Space>
                    </Option>
                  ))}
                </Select>
              </div>
              
              <Button
                type="primary"
                size="large"
                icon={<PlayCircleOutlined />}
                onClick={startDiagnosis}
                loading={loading}
                disabled={!selectedSubject}
                style={{ width: '100%' }}
              >
                开始诊断
              </Button>
            </Space>
          </Card>
        </Col>
        
        <Col xs={24} lg={8}>
          <Card title="诊断特色">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                <Text>AI智能出题，精准评估</Text>
              </div>
              <div>
                <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                <Text>多维度能力分析</Text>
              </div>
              <div>
                <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                <Text>个性化学习建议</Text>
              </div>
              <div>
                <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                <Text>实时进度跟踪</Text>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Diagnosis;