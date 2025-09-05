import React, { useState, useEffect } from 'react';
import {
  Row,
  Col,
  Card,
  Button,
  Table,
  Modal,
  Form,
  Input,
  Select,
  Upload,
  message,
  Tag,
  Space,
  Statistic,
  Typography,
  Popconfirm,
  InputNumber,
  Spin,
  Alert,
  Switch,
  Tooltip
} from 'antd';
import {
  UploadOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  CloudDownloadOutlined,
  SearchOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { useAuthStore } from '../stores/authStore';
import { examPaperApi } from '../services/api';

const { Title } = Typography;
const { Option } = Select;

interface ExamPaper {
  id: string;
  title: string;
  subject_id: string;
  exam_type: string;
  year: number;
  region: string;
  difficulty_level: number;
  question_count: number;
  total_score: number;
  parse_status: 'pending' | 'parsing' | 'completed' | 'failed';
  file_size: number;
  file_type: string;
  download_count: number;
  tags?: string[];
  created_at: string;
  updated_at: string;
}

interface Subject {
  id: string;
  name: string;
  code: string;
}

const ExamPaperManagement: React.FC = () => {
  const { token } = useAuthStore();
  const [papers, setPapers] = useState<ExamPaper[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [downloadModalVisible, setDownloadModalVisible] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterSubject, setFilterSubject] = useState<string>('');
  const [filterYear, setFilterYear] = useState<number>();
  const [filterTag, setFilterTag] = useState<string>('');
  const [uploadForm] = Form.useForm();
  const [downloadForm] = Form.useForm();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    if (!token) {
      message.error('请先登录');
      return;
    }

    setLoading(true);
    try {
      const [papersResponse, subjectsResponse] = await Promise.all([
        examPaperApi.getExamPapers(token),
        examPaperApi.getSubjects(token)
      ]);
      setPapers(Array.isArray(papersResponse.data) ? papersResponse.data : []);
      setSubjects(Array.isArray(subjectsResponse.data) ? subjectsResponse.data : []);
    } catch (error) {
      console.error('Failed to load data:', error);
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (values: any) => {
    if (!token) {
      message.error('请先登录');
      return;
    }

    const { file } = values;
    if (!file || !file.fileList || file.fileList.length === 0) {
      message.error('请选择文件');
      return;
    }

    setUploading(true);
    try {
      const formData = {
        ...values,
        file: file.fileList[0].originFileObj
      };
      await examPaperApi.uploadExamPaper(token, formData.file, formData);
      message.success('上传成功');
      setUploadModalVisible(false);
      uploadForm.resetFields();
      loadData();
    } catch (error) {
      console.error('Upload failed:', error);
      message.error('上传失败');
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (values: any) => {
    if (!token) {
      message.error('请先登录');
      return;
    }

    setDownloading(true);
    try {
      await examPaperApi.downloadSubjectPapers(token, values.subject_id, values.years);
      message.success('开始抓取试卷，请稍后查看');
      setDownloadModalVisible(false);
      downloadForm.resetFields();
      setTimeout(() => {
        loadData();
      }, 2000);
    } catch (error) {
      console.error('Download failed:', error);
      message.error('下载失败');
    } finally {
      setDownloading(false);
    }
  };

  const handleDelete = async (paperId: string) => {
    if (!token) {
      message.error('请先登录');
      return;
    }

    try {
      await examPaperApi.deleteExamPaper(token, paperId);
      message.success('删除成功');
      loadData();
    } catch (error) {
      console.error('Delete failed:', error);
      message.error('删除失败');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'parsing': return 'processing';
      case 'pending': return 'default';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return '已解析';
      case 'parsing': return '解析中';
      case 'pending': return '待解析';
      case 'failed': return '解析失败';
      default: return '未知';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const filteredPapers = Array.isArray(papers) ? papers.filter(paper => {
    const matchesSearch = paper.title.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSubject = !filterSubject || paper.subject_id === filterSubject;
    const matchesYear = !filterYear || paper.year === filterYear;
    const matchesTag = !filterTag || (paper.tags && paper.tags.some(tag => 
      tag.toLowerCase().includes(filterTag.toLowerCase())
    ));
    return matchesSearch && matchesSubject && matchesYear && matchesTag;
  }) : [];

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      render: (text: string) => (
        <Space>
          <FileTextOutlined />
          <span>{text}</span>
        </Space>
      )
    },
    {
      title: '科目',
      dataIndex: 'subject_id',
      key: 'subject_id',
      render: (subjectId: string) => {
        const subject = subjects.find(s => s.id === subjectId);
        return subject?.name || '未知';
      }
    },
    {
      title: '类型',
      dataIndex: 'exam_type',
      key: 'exam_type'
    },
    {
      title: '年份',
      dataIndex: 'year',
      key: 'year'
    },
    {
      title: '地区',
      dataIndex: 'region',
      key: 'region'
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags: string[]) => (
        <Space wrap>
          {tags && tags.length > 0 ? tags.map((tag, index) => (
            <Tag key={index} color="blue">{tag}</Tag>
          )) : <span style={{ color: '#999' }}>无标签</span>}
        </Space>
      )
    },
    {
      title: '解析状态',
      dataIndex: 'parse_status',
      key: 'parse_status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {getStatusText(status)}
        </Tag>
      )
    },
    {
      title: '题目数',
      dataIndex: 'question_count',
      key: 'question_count'
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      render: (size: number) => formatFileSize(size)
    },
    {
      title: '操作',
      key: 'action',
      render: (record: ExamPaper) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            size="small"
          >
            查看
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            size="small"
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这份试卷吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              size="small"
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>试卷管理</Title>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic title="总试卷数" value={papers.length} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="已解析" 
              value={papers.filter(p => p.parse_status === 'completed').length} 
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="总题目数" 
              value={papers.reduce((sum, p) => sum + p.question_count, 0)} 
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="总下载次数" 
              value={papers.reduce((sum, p) => sum + p.download_count, 0)} 
            />
          </Card>
        </Col>
      </Row>

      {/* 操作按钮和筛选 */}
      <Row justify="space-between" align="middle" style={{ marginBottom: '16px' }}>
        <Col>
          <Space>
            <Button 
              type="primary" 
              icon={<UploadOutlined />}
              onClick={() => setUploadModalVisible(true)}
            >
              上传试卷
            </Button>
            <Button 
              icon={<CloudDownloadOutlined />}
              onClick={() => setDownloadModalVisible(true)}
            >
              抓取真题
            </Button>
          </Space>
        </Col>
        <Col>
          <Space>
            <Input
              placeholder="搜索试卷标题"
              prefix={<SearchOutlined />}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ width: 200 }}
            />
            <Select
              placeholder="筛选科目"
              value={filterSubject}
              onChange={setFilterSubject}
              style={{ width: 120 }}
              allowClear
            >
              {subjects.map(subject => (
                <Option key={subject.id} value={subject.id}>
                  {subject.name}
                </Option>
              ))}
            </Select>
            <InputNumber
              placeholder="年份"
              value={filterYear}
              onChange={(value) => setFilterYear(value || undefined)}
              style={{ width: 100 }}
            />
            <Input
              placeholder="搜索标签"
              value={filterTag}
              onChange={(e) => setFilterTag(e.target.value)}
              style={{ width: 120 }}
            />
          </Space>
        </Col>
      </Row>

      {/* 试卷列表 */}
      <Card>
        <Table
          columns={columns}
          dataSource={filteredPapers}
          rowKey="id"
          loading={loading}
          pagination={{
            total: filteredPapers.length,
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </Card>

      {/* 上传试卷模态框 */}
      <Modal
        title="上传试卷"
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={uploadForm}
          layout="vertical"
          onFinish={handleUpload}
        >
          <Form.Item
            name="title"
            label="试卷标题"
            rules={[{ required: true, message: '请输入试卷标题' }]}
          >
            <Input placeholder="请输入试卷标题" />
          </Form.Item>
          
          <Form.Item
            name="subject_id"
            label="科目"
            rules={[{ required: true, message: '请选择科目' }]}
          >
            <Select placeholder="请选择科目">
              {subjects.map(subject => (
                <Option key={subject.id} value={subject.id}>
                  {subject.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="exam_type"
            label="考试类型"
            rules={[{ required: true, message: '请输入考试类型' }]}
          >
            <Input placeholder="如：期中考试、期末考试、模拟考试等" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="year"
                label="年份"
                rules={[{ required: true, message: '请输入年份' }]}
              >
                <InputNumber
                  placeholder="如：2024"
                  min={2000}
                  max={2030}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="region"
                label="地区"
                rules={[{ required: true, message: '请输入地区' }]}
              >
                <Input placeholder="如：北京、上海、全国等" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="tags"
            label="标签"
          >
            <Input placeholder="请输入标签，多个标签用逗号分隔" />
          </Form.Item>

          <Form.Item
            name="auto_generate_kg"
            label={
              <Space>
                <span>自动生成知识图谱</span>
                <Tooltip title="开启后将自动为试卷生成知识图谱并进行向量化存储，便于智能检索和分析">
                  <span style={{ color: '#1890ff', cursor: 'help' }}>(?)</span>
                </Tooltip>
              </Space>
            }
            valuePropName="checked"
            initialValue={true}
          >
            <Switch />
          </Form.Item>

          <Form.Item
            name="file"
            label="试卷文件"
            rules={[{ required: true, message: '请选择试卷文件' }]}
          >
            <Upload
              beforeUpload={() => false}
              maxCount={1}
              accept=".pdf,.jpg,.jpeg,.png"
            >
              <Button icon={<UploadOutlined />}>选择文件</Button>
            </Upload>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={uploading}>
                {uploading ? '上传中...' : '上传'}
              </Button>
              <Button onClick={() => setUploadModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 抓取真题模态框 */}
      <Modal
        title="抓取真题"
        open={downloadModalVisible}
        onCancel={() => setDownloadModalVisible(false)}
        footer={null}
      >
        <Form
          form={downloadForm}
          layout="vertical"
          onFinish={handleDownload}
        >
          <Form.Item
            name="subject_id"
            label="科目"
            rules={[{ required: true, message: '请选择科目' }]}
          >
            <Select placeholder="请选择要抓取的科目">
              {subjects.map(subject => (
                <Option key={subject.id} value={subject.id}>
                  {subject.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="years"
            label="抓取年数"
            rules={[{ required: true, message: '请输入抓取年数' }]}
          >
            <InputNumber
              placeholder="如：3（表示抓取最近3年的试卷）"
              min={1}
              max={10}
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Alert
            message="提示"
            description="抓取过程可能需要几分钟时间，请耐心等待。抓取完成后会自动刷新列表。"
            type="info"
            style={{ marginBottom: '16px' }}
          />

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={downloading}>
                {downloading ? '抓取中...' : '开始抓取'}
              </Button>
              <Button onClick={() => setDownloadModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ExamPaperManagement;