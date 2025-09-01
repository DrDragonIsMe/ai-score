import {
    CloudDownloadOutlined,
    DeleteOutlined,
    DownloadOutlined,
    EyeOutlined,
    FilePdfOutlined,
    FileTextOutlined,
    PictureOutlined,
    PlusOutlined,
    StarOutlined,
    SyncOutlined,
    UploadOutlined
} from '@ant-design/icons';
import {
    Badge,
    Button,
    Card,
    Col,
    Divider,
    Form,
    Image,
    Input,
    List,
    message,
    Modal,
    Popconfirm,
    Progress,
    Row,
    Select,
    Space,
    Statistic,
    Table,
    Tag,
    Tooltip,
    Typography,
    Upload
} from 'antd';
import type { UploadFile, UploadProps } from 'antd/es/upload/interface';
import React, { useEffect, useState } from 'react';
import api, { examPaperApi } from '../services/api';
import ExamPaperStarMap from './ExamPaperStarMap';

const { Option } = Select;
const { TextArea } = Input;
const { Text, Title } = Typography;
const { Dragger } = Upload;

interface ExamPaper {
    id: string;
    title: string;
    description: string;
    subject_id: string;
    year: number;
    exam_type: string;
    difficulty: number;
    total_score: number;
    question_count: number;
    file_path: string;
    file_type: string;
    file_size: number;
    upload_time: string;
    parse_status: 'pending' | 'processing' | 'completed' | 'failed';
    parse_progress: number;
    tags: string[];
    source: string;
    region: string;
}

interface Question {
    id: string;
    paper_id: string;
    question_number: number;
    content: string;
    type: string;
    difficulty: number;
    score: number;
    answer: string;
    explanation: string;
    knowledge_points: string[];
    image_paths: string[];
}

interface ExamPaperManagerProps {
    subjectId: string;
}

const ExamPaperManager: React.FC<ExamPaperManagerProps> = ({ subjectId }) => {
    const [papers, setPapers] = useState<ExamPaper[]>([]);
    const [questions, setQuestions] = useState<Question[]>([]);
    const [loading, setLoading] = useState(false);
    const [uploadModalVisible, setUploadModalVisible] = useState(false);
    const [paperDetailModalVisible, setPaperDetailModalVisible] = useState(false);
    const [starMapModalVisible, setStarMapModalVisible] = useState(false);
    const [selectedPaper, setSelectedPaper] = useState<ExamPaper | null>(null);
    const [starMapData, setStarMapData] = useState<any>(null);
    const [starMapLoading, setStarMapLoading] = useState(false);
    const [fileList, setFileList] = useState<UploadFile[]>([]);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [downloadModalVisible, setDownloadModalVisible] = useState(false);
    const [downloadLoading, setDownloadLoading] = useState(false);
    const [form] = Form.useForm();
    const [downloadForm] = Form.useForm();
    
    // 筛选相关状态
    const [filters, setFilters] = useState<{
        year?: number;
        exam_type?: string;
        difficulty?: number;
        parse_status?: string;
        source?: string;
    }>({});
    const [searchText, setSearchText] = useState('');
    const [filteredPapers, setFilteredPapers] = useState<ExamPaper[]>([]);

    useEffect(() => {
        fetchPapers();
    }, [subjectId]);

    // 筛选逻辑
    useEffect(() => {
        let filtered = papers;
        
        // 搜索文本筛选
        if (searchText) {
            filtered = filtered.filter(paper => 
                paper.title.toLowerCase().includes(searchText.toLowerCase()) ||
                paper.description.toLowerCase().includes(searchText.toLowerCase())
            );
        }
        
        if (filters.year) {
            filtered = filtered.filter(paper => paper.year === filters.year);
        }
        
        if (filters.exam_type) {
            filtered = filtered.filter(paper => paper.exam_type === filters.exam_type);
        }
        
        if (filters.difficulty) {
            filtered = filtered.filter(paper => paper.difficulty === filters.difficulty);
        }
        
        if (filters.parse_status) {
            filtered = filtered.filter(paper => paper.parse_status === filters.parse_status);
        }
        
        if (filters.source) {
            filtered = filtered.filter(paper => paper.source && paper.source.includes(filters.source!));
        }
        
        setFilteredPapers(filtered);
    }, [papers, filters, searchText]);

    const fetchPapers = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                message.error('请先登录');
                return;
            }
            const response = await examPaperApi.getExamPapers(token, subjectId);
            setPapers(response.data.papers || []);
        } catch (error) {
            message.error('获取试卷列表失败');
        } finally {
            setLoading(false);
        }
    };

    const fetchQuestions = async (paperId: string) => {
        try {
            const response = await api.get(`/exam-papers/${paperId}/questions`);
            setQuestions(response.data.data);
        } catch (error) {
            message.error('获取题目列表失败');
        }
    };

    const fetchStarMapData = async (paperId: string) => {
        setStarMapLoading(true);
        try {
            const response = await api.get(`/knowledge-graph/exam-papers/${paperId}/star-map`);
            setStarMapData(response.data.data);
        } catch (error) {
            message.error('获取星图数据失败');
        } finally {
            setStarMapLoading(false);
        }
    };

    const handleViewStarMap = async (paper: ExamPaper) => {
        setSelectedPaper(paper);
        setStarMapModalVisible(true);
        await fetchStarMapData(paper.id);
    };

    const handleUpload = async (values: any) => {
        if (fileList.length === 0) {
            message.error('请选择要上传的文件');
            return;
        }

        const formData = new FormData();
        formData.append('file', fileList[0].originFileObj as File);
        formData.append('title', values.title);
        formData.append('description', values.description || '');
        formData.append('subject_id', subjectId);
        formData.append('year', values.year);
        formData.append('exam_type', values.exam_type);
        formData.append('difficulty', values.difficulty);
        formData.append('source', values.source || '');
        formData.append('region', values.region || '');
        formData.append('tags', JSON.stringify(values.tags || []));

        try {
            setUploadProgress(0);
            const response = await api.post('/exam-papers/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                },
                onUploadProgress: (progressEvent) => {
                    const progress = Math.round(
                        (progressEvent.loaded * 100) / (progressEvent.total || 1)
                    );
                    setUploadProgress(progress);
                }
            });

            message.success('上传成功，正在解析试卷...');
            setUploadModalVisible(false);
            setFileList([]);
            form.resetFields();
            fetchPapers();

            // 开始轮询解析状态
            pollParseStatus(response.data.data.id);
        } catch (error) {
            message.error('上传失败');
        }
    };

    const pollParseStatus = async (paperId: string) => {
        const checkStatus = async () => {
            try {
                const response = await api.get(`/exam-papers/${paperId}/parse-status`);
                const parseInfo = response.data.data;

                if (parseInfo.parse_status === 'completed') {
                    message.success(`试卷解析完成，识别到 ${parseInfo.question_count} 道题目`);
                    fetchPapers();
                    return;
                } else if (parseInfo.parse_status === 'failed') {
                    const errorMsg = parseInfo.parse_result?.error || '未知错误';
                    message.error(`试卷解析失败: ${errorMsg}`);
                    fetchPapers();
                    return;
                }

                // 继续轮询
                setTimeout(checkStatus, 3000);
            } catch (error) {
                console.error('检查解析状态失败:', error);
                // 如果API调用失败，回退到获取完整试卷信息
                try {
                    const response = await api.get(`/exam-papers/${paperId}`);
                    const paper = response.data.data;

                    if (paper.parse_status === 'completed' || paper.parse_status === 'failed') {
                        fetchPapers();
                        return;
                    }

                    setTimeout(checkStatus, 3000);
                } catch (fallbackError) {
                    console.error('回退检查也失败:', fallbackError);
                }
            }
        };

        checkStatus();
    };

    const handleDelete = async (paperId: string) => {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                message.error('请先登录');
                return;
            }
            await examPaperApi.deleteExamPaper(token, paperId);
            message.success('删除成功');
            fetchPapers();
        } catch (error) {
            message.error('删除失败');
        }
    };

    const handleViewDetail = (paper: ExamPaper) => {
        setSelectedPaper(paper);
        fetchQuestions(paper.id);
        setPaperDetailModalVisible(true);
    };

    const handleDownload = async (paperId: string) => {
        try {
            const response = await api.get(`/exam-papers/${paperId}/download`, {
                responseType: 'blob'
            });

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `exam-paper-${paperId}.pdf`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch (error) {
            message.error('下载失败');
        }
    };

    const handleDownloadPapers = async (values: any) => {
        setDownloadLoading(true);
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                message.error('请先登录');
                return;
            }
            const response = await examPaperApi.downloadSubjectPapers(token, subjectId, values.years);

            if (response && response.data) {
                message.success(
                    `成功下载真题！找到 ${response.data.total_found || 0} 份试卷，保存 ${response.data.saved_count || 0} 份`
                );
                setDownloadModalVisible(false);
                fetchPapers(); // 刷新试卷列表
            } else {
                message.error('下载失败');
            }
        } catch (error) {
            message.error('下载真题失败');
        } finally {
            setDownloadLoading(false);
        }
    };

    const uploadProps: UploadProps = {
        name: 'file',
        multiple: false,
        fileList,
        beforeUpload: (file) => {
            const isPdf = file.type === 'application/pdf';
            const isImage = file.type.startsWith('image/');

            if (!isPdf && !isImage) {
                message.error('只能上传 PDF 或图片文件！');
                return false;
            }

            const isLt10M = file.size / 1024 / 1024 < 10;
            if (!isLt10M) {
                message.error('文件大小不能超过 10MB！');
                return false;
            }

            return false; // 阻止自动上传
        },
        onChange: (info) => {
            setFileList(info.fileList.slice(-1)); // 只保留最后一个文件
        },
        onRemove: () => {
            setFileList([]);
        }
    };

    const getStatusColor = (status: string) => {
        const colors = {
            pending: 'default',
            processing: 'processing',
            completed: 'success',
            failed: 'error'
        };
        return colors[status as keyof typeof colors] || 'default';
    };

    const getStatusText = (status: string) => {
        const texts = {
            pending: '待解析',
            processing: '解析中',
            completed: '已完成',
            failed: '解析失败'
        };
        return texts[status as keyof typeof texts] || status;
    };

    const getFileIcon = (fileType: string) => {
        if (fileType === 'application/pdf') {
            return <FilePdfOutlined style={{ color: '#f5222d' }} />;
        } else if (fileType.startsWith('image/')) {
            return <PictureOutlined style={{ color: '#52c41a' }} />;
        }
        return <FileTextOutlined />;
    };

    const columns = [
        {
            title: '试卷信息',
            key: 'info',
            render: (record: ExamPaper) => (
                <div>
                    <div style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
                        {getFileIcon(record.file_type)}
                        <Text strong style={{ marginLeft: 8 }}>{record.title}</Text>
                    </div>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                        {record.description}
                    </Text>
                </div>
            )
        },
        {
            title: '年份/类型',
            key: 'year_type',
            render: (record: ExamPaper) => (
                <div>
                    <Tag color="blue">{record.year}年</Tag>
                    <br />
                    <Tag>{record.exam_type}</Tag>
                </div>
            )
        },
        {
            title: '难度/分数',
            key: 'difficulty_score',
            render: (record: ExamPaper) => (
                <div>
                    <div>难度: {record.difficulty}</div>
                    <div>总分: {record.total_score}</div>
                </div>
            )
        },
        {
            title: '题目数量',
            dataIndex: 'question_count',
            key: 'question_count',
            render: (count: number) => (
                <Badge count={count} showZero style={{ backgroundColor: '#52c41a' }} />
            )
        },
        {
            title: '解析状态',
            key: 'parse_status',
            render: (record: ExamPaper) => (
                <div>
                    <Tag color={getStatusColor(record.parse_status)}>
                        {getStatusText(record.parse_status)}
                    </Tag>
                    {record.parse_status === 'processing' && (
                        <Progress
                            percent={record.parse_progress}
                            size="small"
                            style={{ marginTop: 4 }}
                        />
                    )}
                </div>
            )
        },
        {
            title: '操作',
            key: 'actions',
            render: (record: ExamPaper) => (
                <Space>
                    <Tooltip title="查看详情">
                        <Button
                            type="text"
                            icon={<EyeOutlined />}
                            onClick={() => handleViewDetail(record)}
                        />
                    </Tooltip>
                    <Tooltip title="知识点星图">
                        <Button
                            type="text"
                            icon={<StarOutlined />}
                            onClick={() => handleViewStarMap(record)}
                            disabled={record.parse_status !== 'completed'}
                        />
                    </Tooltip>
                    <Tooltip title="下载文件">
                        <Button
                            type="text"
                            icon={<DownloadOutlined />}
                            onClick={() => handleDownload(record.id)}
                        />
                    </Tooltip>
                    <Popconfirm
                        title="确定要删除这份试卷吗？"
                        onConfirm={() => handleDelete(record.id)}
                        okText="确定"
                        cancelText="取消"
                    >
                        <Button
                            type="text"
                            danger
                            icon={<DeleteOutlined />}
                        />
                    </Popconfirm>
                </Space>
            )
        }
    ];

    const renderQuestionList = () => {
        return (
            <List
                dataSource={questions}
                renderItem={(question, index) => (
                    <List.Item>
                        <List.Item.Meta
                            avatar={
                                <div style={{
                                    width: 32,
                                    height: 32,
                                    borderRadius: '50%',
                                    backgroundColor: '#1890ff',
                                    color: 'white',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontSize: '14px',
                                    fontWeight: 'bold'
                                }}>
                                    {question.question_number}
                                </div>
                            }
                            title={
                                <Space>
                                    <Tag color="blue">{question.type}</Tag>
                                    <Tag color="orange">{question.score}分</Tag>
                                    <Tag>难度: {question.difficulty}</Tag>
                                </Space>
                            }
                            description={
                                <div>
                                    <Text>{question.content.substring(0, 200)}...</Text>
                                    {question.knowledge_points && question.knowledge_points.length > 0 && (
                                        <div style={{ marginTop: 8 }}>
                                            <Text strong>关联知识点: </Text>
                                            {question.knowledge_points.map((kp, idx) => (
                                                <Tag key={idx} color="green" style={{ marginBottom: 4 }}>
                                                    {kp}
                                                </Tag>
                                            ))}
                                        </div>
                                    )}
                                    {question.image_paths && question.image_paths.length > 0 && (
                                        <div style={{ marginTop: 8 }}>
                                            <Text strong>题目图片: </Text>
                                            <Image.PreviewGroup>
                                                {question.image_paths.map((path, idx) => (
                                                    <Image
                                                        key={idx}
                                                        width={60}
                                                        height={60}
                                                        src={path}
                                                        style={{ marginRight: 8, objectFit: 'cover' }}
                                                    />
                                                ))}
                                            </Image.PreviewGroup>
                                        </div>
                                    )}
                                </div>
                            }
                        />
                    </List.Item>
                )}
                pagination={{
                    pageSize: 5,
                    showSizeChanger: false,
                    showQuickJumper: true
                }}
            />
        );
    };

    return (
        <div>
            <Card
                title="试卷管理"
                extra={
                    <Space>
                        <Button
                            type="primary"
                            icon={<PlusOutlined />}
                            onClick={() => setUploadModalVisible(true)}
                        >
                            上传试卷
                        </Button>
                        <Button
                            icon={<CloudDownloadOutlined />}
                            onClick={() => setDownloadModalVisible(true)}
                        >
                            下载真题
                        </Button>
                        <Button
                            icon={<SyncOutlined />}
                            onClick={fetchPapers}
                            loading={loading}
                        >
                            刷新
                        </Button>
                    </Space>
                }
            >
                {/* 搜索框 */}
                <Row style={{ marginBottom: 16 }}>
                    <Col span={8}>
                        <Input.Search
                            placeholder="搜索试卷标题或描述"
                            allowClear
                            value={searchText}
                            onChange={(e) => setSearchText(e.target.value)}
                            onSearch={(value) => setSearchText(value)}
                            style={{ width: '100%' }}
                        />
                    </Col>
                </Row>
                
                {/* 筛选控件 */}
                <Row gutter={16} style={{ marginBottom: 16 }}>
                    <Col span={4}>
                        <Select
                            placeholder="选择年份"
                            allowClear
                            style={{ width: '100%' }}
                            value={filters.year}
                            onChange={(value) => setFilters({ ...filters, year: value })}
                        >
                            {Array.from(new Set(papers.map(p => p.year))).sort((a, b) => b - a).map(year => (
                                <Option key={year} value={year}>{year}年</Option>
                            ))}
                        </Select>
                    </Col>
                    <Col span={4}>
                        <Select
                            placeholder="考试类型"
                            allowClear
                            style={{ width: '100%' }}
                            value={filters.exam_type}
                            onChange={(value) => setFilters({ ...filters, exam_type: value })}
                        >
                            {Array.from(new Set(papers.map(p => p.exam_type))).map(type => (
                                <Option key={type} value={type}>{type}</Option>
                            ))}
                        </Select>
                    </Col>
                    <Col span={4}>
                        <Select
                            placeholder="难度等级"
                            allowClear
                            style={{ width: '100%' }}
                            value={filters.difficulty}
                            onChange={(value) => setFilters({ ...filters, difficulty: value })}
                        >
                            <Option value={1}>简单</Option>
                            <Option value={2}>中等</Option>
                            <Option value={3}>困难</Option>
                        </Select>
                    </Col>
                    <Col span={4}>
                        <Select
                            placeholder="解析状态"
                            allowClear
                            style={{ width: '100%' }}
                            value={filters.parse_status}
                            onChange={(value) => setFilters({ ...filters, parse_status: value })}
                        >
                            <Option value="pending">待解析</Option>
                            <Option value="processing">解析中</Option>
                            <Option value="completed">已完成</Option>
                            <Option value="failed">解析失败</Option>
                        </Select>
                    </Col>
                    <Col span={4}>
                        <Select
                            placeholder="试卷来源"
                            allowClear
                            style={{ width: '100%' }}
                            value={filters.source}
                            onChange={(value) => setFilters({ ...filters, source: value })}
                        >
                            {Array.from(new Set(papers.map(p => p.source).filter(Boolean))).map(source => (
                                <Option key={source} value={source}>{source}</Option>
                            ))}
                        </Select>
                    </Col>
                    <Col span={4}>
                        <Button
                            onClick={() => {
                                setFilters({});
                                setSearchText('');
                            }}
                            style={{ width: '100%' }}
                        >
                            清除筛选
                        </Button>
                    </Col>
                </Row>
                <Table
                    columns={columns}
                    dataSource={filteredPapers}
                    rowKey="id"
                    loading={loading}
                    pagination={{
                        pageSize: 10,
                        showSizeChanger: true,
                        showQuickJumper: true,
                        showTotal: (total) => `共 ${total} 份试卷 (总计 ${papers.length} 份)`
                    }}
                />
            </Card>

            {/* 上传试卷模态框 */}
            <Modal
                title="上传试卷"
                open={uploadModalVisible}
                onCancel={() => {
                    setUploadModalVisible(false);
                    setFileList([]);
                    form.resetFields();
                }}
                footer={null}
                width={600}
            >
                <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleUpload}
                >
                    <Form.Item
                        name="file"
                        label="选择文件"
                        rules={[{ required: true, message: '请选择要上传的文件' }]}
                    >
                        <Dragger {...uploadProps}>
                            <p className="ant-upload-drag-icon">
                                <UploadOutlined />
                            </p>
                            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                            <p className="ant-upload-hint">
                                支持 PDF 和图片格式，文件大小不超过 10MB
                            </p>
                        </Dragger>
                    </Form.Item>

                    {uploadProgress > 0 && uploadProgress < 100 && (
                        <Progress percent={uploadProgress} style={{ marginBottom: 16 }} />
                    )}

                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item
                                name="title"
                                label="试卷标题"
                                rules={[{ required: true, message: '请输入试卷标题' }]}
                            >
                                <Input placeholder="如：2023年高考数学全国卷I" />
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Form.Item
                                name="year"
                                label="年份"
                                rules={[{ required: true, message: '请选择年份' }]}
                            >
                                <Select placeholder="请选择">
                                    {Array.from({ length: 20 }, (_, i) => new Date().getFullYear() - i).map(year => (
                                        <Option key={year} value={year}>{year}年</Option>
                                    ))}
                                </Select>
                            </Form.Item>
                        </Col>
                    </Row>

                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item
                                name="exam_type"
                                label="考试类型"
                                rules={[{ required: true, message: '请选择考试类型' }]}
                            >
                                <Select placeholder="请选择">
                                    <Option value="高考">高考</Option>
                                    <Option value="模拟考">模拟考</Option>
                                    <Option value="月考">月考</Option>
                                    <Option value="期中考试">期中考试</Option>
                                    <Option value="期末考试">期末考试</Option>
                                    <Option value="练习题">练习题</Option>
                                </Select>
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Form.Item
                                name="difficulty"
                                label="难度等级"
                                rules={[{ required: true, message: '请选择难度等级' }]}
                            >
                                <Select placeholder="请选择">
                                    <Option value={1}>简单</Option>
                                    <Option value={2}>较易</Option>
                                    <Option value={3}>中等</Option>
                                    <Option value={4}>较难</Option>
                                    <Option value={5}>困难</Option>
                                </Select>
                            </Form.Item>
                        </Col>
                    </Row>

                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item name="source" label="试卷来源">
                                <Input placeholder="如：教育部考试中心" />
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Form.Item name="region" label="地区">
                                <Input placeholder="如：全国、北京、上海" />
                            </Form.Item>
                        </Col>
                    </Row>

                    <Form.Item name="description" label="试卷描述">
                        <TextArea
                            rows={3}
                            placeholder="请输入试卷描述信息"
                        />
                    </Form.Item>

                    <Form.Item name="tags" label="标签">
                        <Select
                            mode="tags"
                            placeholder="添加标签，按回车确认"
                            style={{ width: '100%' }}
                        >
                            <Option value="重点">重点</Option>
                            <Option value="基础">基础</Option>
                            <Option value="提高">提高</Option>
                            <Option value="综合">综合</Option>
                        </Select>
                    </Form.Item>

                    <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
                        <Space>
                            <Button onClick={() => setUploadModalVisible(false)}>
                                取消
                            </Button>
                            <Button type="primary" htmlType="submit" disabled={fileList.length === 0}>
                                上传并解析
                            </Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>

            {/* 试卷详情模态框 */}
            <Modal
                title={selectedPaper?.title}
                open={paperDetailModalVisible}
                onCancel={() => setPaperDetailModalVisible(false)}
                footer={null}
                width={900}
            >
                {selectedPaper && (
                    <div>
                        <Row gutter={16} style={{ marginBottom: 16 }}>
                            <Col span={6}>
                                <Statistic title="年份" value={selectedPaper.year} suffix="年" />
                            </Col>
                            <Col span={6}>
                                <Statistic title="总分" value={selectedPaper.total_score} suffix="分" />
                            </Col>
                            <Col span={6}>
                                <Statistic title="题目数" value={selectedPaper.question_count} suffix="题" />
                            </Col>
                            <Col span={6}>
                                <Statistic title="难度" value={selectedPaper.difficulty} suffix="级" />
                            </Col>
                        </Row>

                        <Divider>题目列表</Divider>
                        {renderQuestionList()}
                    </div>
                )}
            </Modal>

            {/* 下载真题模态框 */}
            <Modal
                title="下载真题"
                open={downloadModalVisible}
                onCancel={() => setDownloadModalVisible(false)}
                footer={[
                    <Button key="cancel" onClick={() => setDownloadModalVisible(false)}>
                        取消
                    </Button>,
                    <Button
                        key="download"
                        type="primary"
                        loading={downloadLoading}
                        onClick={() => {
                            downloadForm.validateFields().then(values => {
                                handleDownloadPapers(values);
                            });
                        }}
                    >
                        开始下载
                    </Button>
                ]}
            >
                <Form
                    form={downloadForm}
                    layout="vertical"
                    initialValues={{
                        years: 10
                    }}
                >
                    <Form.Item
                        name="years"
                        label="下载年份范围"
                        rules={[
                            { required: true, message: '请选择下载年份范围' },
                            { type: 'number', min: 1, max: 20, message: '年份范围应在1-20年之间' }
                        ]}
                    >
                        <Select placeholder="选择下载年份范围">
                            <Option value={5}>近5年</Option>
                            <Option value={10}>近10年</Option>
                            <Option value={15}>近15年</Option>
                            <Option value={20}>近20年</Option>
                        </Select>
                    </Form.Item>
                    <div style={{ color: '#666', fontSize: '12px', marginTop: '8px' }}>
                        <p>• 系统将自动搜索并下载指定年份范围内的真题</p>
                        <p>• 下载的试卷将自动进行AI解析，识别题目和知识点</p>
                        <p>• 重复的试卷将自动跳过</p>
                    </div>
                </Form>
            </Modal>

            {/* 星图模态框 */}
            <Modal
                title={`知识点分布星图 - ${selectedPaper?.title || ''}`}
                open={starMapModalVisible}
                onCancel={() => {
                    setStarMapModalVisible(false);
                    setSelectedPaper(null);
                    setStarMapData(null);
                }}
                footer={null}
                width={1200}
                style={{ top: 20 }}
            >
                <ExamPaperStarMap 
                    data={starMapData} 
                    loading={starMapLoading} 
                />
            </Modal>
        </div>
    );
};

export default ExamPaperManager;
