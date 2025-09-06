import React, { useState, useEffect } from 'react';
import { useLocation, useSearchParams } from 'react-router-dom';
import {
  Card,
  Button,
  Select,
  Tag,
  Space,
  Typography,
  message,
  Spin,
  Row,
  Col,
  Modal,
  Form,
  Input,
  Dropdown,
  Popconfirm,
  Drawer,
  Avatar
} from 'antd';
import {
  ReloadOutlined,
  EyeOutlined,
  CalendarOutlined,
  BookOutlined,
  TagOutlined,
  PartitionOutlined,
  UnorderedListOutlined,
  EditOutlined,
  DeleteOutlined,
  MoreOutlined,
  NodeIndexOutlined
} from '@ant-design/icons';
import knowledgeGraphApi from '../api/knowledgeGraph';
import { getSubjects, type Subject } from '../api/subjects';
import InteractiveKnowledgeGraph from '../components/InteractiveKnowledgeGraph';
import KnowledgeGraphEditor from '../components/KnowledgeGraphEditor/KnowledgeGraphEditor';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const { Option } = Select;
const { Title, Text } = Typography;

interface KnowledgeGraphItem {
  id: string;
  name: string;
  description: string;
  subject_id: string;
  subject_name?: string;
  graph_type: string;
  year: number;
  nodes: any[];
  edges: any[];
  created_at: string;
  updated_at: string;
  content?: string;
  tags?: string[];
}

// Subject接口已从../api/subjects导入

const KnowledgeGraph: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [knowledgeGraphs, setKnowledgeGraphs] = useState<KnowledgeGraphItem[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSubject, setSelectedSubject] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedYear, setSelectedYear] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'list' | 'grid' | 'graph'>('grid');
  const [fromSubjectManagement, setFromSubjectManagement] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingGraph, setEditingGraph] = useState<KnowledgeGraphItem | null>(null);
  const [tagModalVisible, setTagModalVisible] = useState(false);
  const [managingTagsGraph, setManagingTagsGraph] = useState<KnowledgeGraphItem | null>(null);
  const [newTag, setNewTag] = useState('');
  const [form] = Form.useForm();
  const [detailDrawerVisible, setDetailDrawerVisible] = useState(false);
  const [selectedGraphForDetail, setSelectedGraphForDetail] = useState<KnowledgeGraphItem | null>(null);


  const graphTypeNames = {
    'exam_scope': '考试范围',
    'full_knowledge': '完整知识图谱',
    'mastery_level': '掌握情况图谱',
    'ai_assistant_content': 'AI助理内容'
  };

  useEffect(() => {
    fetchSubjects();
    
    // 检查URL参数，如果来自学科管理页面，则设置相应的筛选条件
    const subjectParam = searchParams.get('subject');
    const subjectNameParam = searchParams.get('subjectName');
    
    if (subjectParam && subjectParam !== 'all') {
      setSelectedSubject(subjectParam);
      setFromSubjectManagement(true);
      // 移除筛选提示，避免重复显示
    }
    
    // 只有在没有URL参数时才立即获取数据，否则让第二个useEffect处理
    if (!subjectParam || subjectParam === 'all') {
      fetchKnowledgeGraphs();
    }
  }, [searchParams]);

  useEffect(() => {
    fetchKnowledgeGraphs();
  }, [selectedSubject, selectedType, selectedYear]);

  const fetchSubjects = async () => {
    try {
      const subjects = await getSubjects();
      setSubjects(subjects || []);
    } catch (error) {
      console.error('获取学科列表失败:', error);
      message.error('获取学科列表失败');
    }
  };

  const fetchKnowledgeGraphs = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (selectedSubject !== 'all') {
        params.subject_id = selectedSubject;
      }
      if (selectedYear !== 'all' && selectedYear !== '全部') {
        params.year = parseInt(selectedYear);
      }

      let graphs: any[] = [];
      const typesToFetch = selectedType !== 'all' 
        ? [selectedType] 
        : ['exam_scope', 'full_knowledge', 'mastery_level', 'ai_assistant_content'];

      const promises = typesToFetch.map(type => {
        const apiParams: any = {};
        if (params.subject_id) apiParams.subjectId = params.subject_id;
        if (params.year) apiParams.year = params.year;
        apiParams.graphType = type;
        return knowledgeGraphApi.getKnowledgeGraphs(apiParams);
      });

      const results = await Promise.all(promises);
      graphs = results.flat();

      const graphsWithSubjectNames = graphs.map((graph: any) => {
        const subject = subjects.find(s => s.id === graph.subject_id);
        // 修复：确保从nodes中提取标签，作为备用
        const tags = graph.tags || (graph.nodes && graph.nodes.length > 0 && graph.nodes[0].tags) || [];
        return {
          id: graph.id,
          name: graph.name || (graph.content ? graph.content.substring(0, 50) + '...' : '知识图谱'),
          description: graph.description || graph.content || '',
          subject_id: graph.subject_id,
          subject_name: subject?.name || '未知学科',
          graph_type: graph.graph_type,
          year: graph.year || new Date(graph.created_at).getFullYear(),
          nodes: graph.nodes || graph.knowledge_graph?.nodes || [],
          edges: graph.edges || graph.knowledge_graph?.edges || [],
          created_at: graph.created_at,
          updated_at: graph.updated_at,
          content: graph.content,
          tags: tags,
        } as KnowledgeGraphItem;
      });
      
      setKnowledgeGraphs(graphsWithSubjectNames);
    } catch (error) {
      console.error('获取知识图谱失败:', error);
      message.error('获取知识图谱失败');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    fetchKnowledgeGraphs();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('zh-CN');
  };

  // 处理编辑知识图谱
  const handleEditGraph = (graph: KnowledgeGraphItem) => {
    setEditingGraph(graph);
    setEditModalVisible(true);
  };

  // 编辑成功回调
  const handleEditSuccess = () => {
    setEditModalVisible(false);
    setEditingGraph(null);
    fetchKnowledgeGraphs();
  };

  // 关闭编辑器
  const handleEditClose = () => {
    setEditModalVisible(false);
    setEditingGraph(null);
  };

  // 处理图谱内筛选器变化
  const handleGraphFilterChange = (filters: { subjectId: string; graphType: string }) => {
    setSelectedSubject(filters.subjectId);
    setSelectedType(filters.graphType);
  };



  // 删除知识图谱
  const handleDeleteGraph = async (graph: KnowledgeGraphItem) => {
    try {
      await knowledgeGraphApi.deleteKnowledgeGraph(graph.id);
      message.success('知识图谱删除成功');
      fetchKnowledgeGraphs();
    } catch (error) {
      console.error('删除知识图谱失败:', error);
      message.error('删除知识图谱失败');
    }
  };

  // 管理标签
  const handleManageTags = (graph: KnowledgeGraphItem) => {
    // 从nodes数组中提取所有标签
    const nodeTags = new Set<string>();
    graph.nodes.forEach(node => {
      if (node.tags && Array.isArray(node.tags)) {
        node.tags.forEach((tag: string) => nodeTags.add(tag));
      }
    });
    const graphWithNodeTags = { ...graph, tags: Array.from(nodeTags) };
    setManagingTagsGraph(graphWithNodeTags);
    setTagModalVisible(true);
  };

  // 添加标签
  const handleAddTag = () => {
    if (!newTag.trim() || !managingTagsGraph) return;
    
    const updatedTags = [...(managingTagsGraph.tags || []), newTag.trim()];
    const updatedGraph = { ...managingTagsGraph, tags: updatedTags };
    setManagingTagsGraph(updatedGraph);
    setNewTag('');
  };

  // 删除标签
  const handleRemoveTag = (tagToRemove: string) => {
    if (!managingTagsGraph) return;
    
    const updatedTags = (managingTagsGraph.tags || []).filter(tag => tag !== tagToRemove);
    const updatedGraph = { ...managingTagsGraph, tags: updatedTags };
    setManagingTagsGraph(updatedGraph);
  };

  // 保存标签更改
  const handleSaveTagChanges = async () => {
    try {
      if (managingTagsGraph) {
        // 使用tags字段更新，后端会将标签应用到所有节点
        await knowledgeGraphApi.updateKnowledgeGraph(managingTagsGraph.id, {
          tags: managingTagsGraph.tags
        });
        message.success('标签更新成功');
        setTagModalVisible(false);
        setManagingTagsGraph(null);
        fetchKnowledgeGraphs();
      }
    } catch (error) {
      console.error('更新标签失败:', error);
      message.error('更新标签失败');
    }
  };

  // 查看详情
  const handleViewDetail = (graph: KnowledgeGraphItem) => {
    setSelectedGraphForDetail(graph);
    setDetailDrawerVisible(true);
  };

  // 获取操作菜单项
  const getActionMenuItems = (graph: KnowledgeGraphItem) => {
    return {
      items: [
        {
          key: 'edit',
          icon: <EditOutlined />,
          label: '编辑',
          onClick: () => handleEditGraph(graph)
        },
        {
          key: 'tags',
          icon: <TagOutlined />,
          label: '管理标签',
          onClick: () => handleManageTags(graph)
        },
        {
          key: 'delete',
          icon: <DeleteOutlined />,
          label: '删除',
          danger: true,
          onClick: () => handleDeleteGraph(graph)
        }
      ]
    };
  };

  const renderKnowledgeGraphCard = (graph: KnowledgeGraphItem) => {
    return (
      <Card 
        key={graph.id} 
        style={{ 
          marginBottom: 16,
          borderRadius: 12,
          border: '1px solid #e2e8f0',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
        }}
        hoverable
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
          <div style={{ flex: 1, marginRight: 16 }}>
            <Title level={4} style={{ margin: 0, color: '#1e293b' }}>
              {graph.name || '未命名知识图谱'}
            </Title>
            {graph.description && (
              <Text type="secondary" style={{ marginTop: 6, display: 'block', lineHeight: 1.5 }}>
                {graph.description}
              </Text>
            )}
          </div>
          <Space direction="vertical" align="end">
            <Tag color="blue" style={{ borderRadius: 12 }}>
              {graphTypeNames[graph.graph_type as keyof typeof graphTypeNames] || graph.graph_type}
            </Tag>
            <Tag style={{ borderRadius: 12 }}>{graph.year}</Tag>
          </Space>
        </div>
        
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          {/* 基本信息 */}
          <div style={{ 
            display: 'flex', 
            flexWrap: 'wrap', 
            gap: 16,
            padding: 12,
            backgroundColor: '#f8fafc',
            borderRadius: 8,
            border: '1px solid #e2e8f0'
          }}>
            <Space size={6}>
              <BookOutlined style={{ color: '#3b82f6' }} />
              <Text strong style={{ color: '#1e293b' }}>{graph.subject_name}</Text>
            </Space>
            <Space size={6}>
              <CalendarOutlined style={{ color: '#10b981' }} />
              <Text type="secondary">创建于 {formatDate(graph.created_at)}</Text>
            </Space>
            <Space size={6}>
              <Text type="secondary">节点: </Text>
              <Text strong style={{ color: '#dc2626' }}>{graph.nodes?.length || 0}</Text>
            </Space>
            <Space size={6}>
              <Text type="secondary">连接: </Text>
              <Text strong style={{ color: '#7c3aed' }}>{graph.edges?.length || 0}</Text>
            </Space>
          </div>

          {/* 显示AI助理内容的详细信息 */}
          {graph.graph_type === 'ai_assistant_content' && graph.nodes && graph.nodes.length > 0 && (
            <div style={{ 
              padding: 16, 
              backgroundColor: '#fefefe', 
              borderRadius: 10,
              border: '1px solid #e5e7eb'
            }}>
              <Text strong style={{ marginBottom: 12, display: 'block', color: '#374151' }}>📝 内容详情</Text>
              {graph.nodes.map((node, index) => (
                <div key={index} style={{ marginBottom: index < graph.nodes.length - 1 ? 16 : 0 }}>
                  {node.content && (
                    <div style={{ 
                      marginBottom: 8, 
                      padding: 12,
                      backgroundColor: '#f9fafb',
                      borderRadius: 8,
                      borderLeft: '3px solid #3b82f6'
                    }}>
                      <Text style={{ 
                        display: 'block', 
                        color: '#4b5563',
                        lineHeight: 1.6,
                        fontSize: '14px'
                      }}>
                        {node.content.length > 150 
                          ? `${node.content.substring(0, 150)}...` 
                          : node.content
                        }
                      </Text>
                    </div>
                  )}
                  {node.tags && node.tags.length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      <Space wrap size={[6, 6]}>
                        {node.tags.map((tag: string, tagIndex: number) => (
                          <Tag 
                            key={tagIndex} 
                            style={{
                              borderRadius: 12,
                              backgroundColor: '#eff6ff',
                              color: '#1d4ed8',
                              border: '1px solid #bfdbfe',
                              fontSize: '12px'
                            }}
                          >
                            <TagOutlined style={{ marginRight: 4 }} />
                            {tag}
                          </Tag>
                        ))}
                      </Space>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* 显示其他类型图谱的标签 */}
          {graph.tags && graph.tags.length > 0 && graph.graph_type !== 'ai_assistant_content' && (
            <div>
              <Text strong style={{ marginBottom: 8, display: 'block', color: '#374151' }}>🏷️ 标签</Text>
              <Space wrap size={[6, 6]}>
                {graph.tags.map((tag: string, tagIndex: number) => (
                  <Tag 
                    key={tagIndex} 
                    style={{
                      borderRadius: 12,
                      backgroundColor: '#f0fdf4',
                      color: '#166534',
                      border: '1px solid #bbf7d0',
                      fontSize: '12px'
                    }}
                  >
                    <TagOutlined style={{ marginRight: 4 }} />
                    {tag}
                  </Tag>
                ))}
              </Space>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Button 
              type="default" 
              size="small" 
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(graph)}
            >
              查看详情
            </Button>
            <Dropdown menu={getActionMenuItems(graph)} trigger={['click']}>
              <Button type="text" size="small" icon={<MoreOutlined />} />
            </Dropdown>
          </div>
        </Space>
      </Card>
    );
  };

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>知识图谱</Title>
        <Space>
          <Space.Compact>
            <Button
              type={viewMode === 'list' ? 'primary' : 'default'}
              icon={<UnorderedListOutlined />}
              onClick={() => setViewMode('list')}
            >
              列表
            </Button>
            <Button
              type={viewMode === 'grid' ? 'primary' : 'default'}
              icon={<EyeOutlined />}
              onClick={() => setViewMode('grid')}
            >
              网格
            </Button>
            <Button
              type={viewMode === 'graph' ? 'primary' : 'default'}
              icon={<PartitionOutlined />}
              onClick={() => setViewMode('graph')}
            >
              图谱
            </Button>
          </Space.Compact>
          <Button 
            type="primary" 
            icon={<ReloadOutlined spin={loading} />} 
            onClick={handleRefresh} 
            loading={loading}
          >
            刷新
          </Button>
        </Space>
      </div>

      {/* 筛选器 */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col xs={24} sm={8}>
            <div style={{ marginBottom: 8 }}>
              <Text strong>学科</Text>
            </div>
            <Select 
              style={{ width: '100%' }} 
              value={selectedSubject} 
              onChange={setSelectedSubject}
              placeholder="选择学科"
            >
              <Option value="all">全部学科</Option>
              {subjects.map((subject) => (
                <Option key={subject.id} value={subject.id}>
                  {subject.name}
                </Option>
              ))}
            </Select>
          </Col>
          
          <Col xs={24} sm={8}>
            <div style={{ marginBottom: 8 }}>
              <Text strong>类型</Text>
            </div>
            <Select 
              style={{ width: '100%' }} 
              value={selectedType} 
              onChange={setSelectedType}
              placeholder="选择类型"
            >
              <Option value="all">全部类型</Option>
              {Object.entries(graphTypeNames).map(([key, name]) => (
                <Option key={key} value={key}>
                  {name}
                </Option>
              ))}
            </Select>
          </Col>
          
          <Col xs={24} sm={8}>
            <div style={{ marginBottom: 8 }}>
              <Text strong>年份</Text>
            </div>
            <Select 
              style={{ width: '100%' }} 
              value={selectedYear} 
              onChange={setSelectedYear}
              placeholder="选择年份"
            >
              <Option value="all">全部年份</Option>
              {Array.from({ length: 5 }, (_, i) => {
                const year = new Date().getFullYear() - i;
                return (
                  <Option key={year} value={year.toString()}>
                    {year}
                  </Option>
                );
              })}
            </Select>
          </Col>
        </Row>
      </Card>

      {/* 知识图谱内容 */}
      <Spin spinning={loading}>
        {viewMode === 'graph' ? (
          <InteractiveKnowledgeGraph 
            subjectId={selectedSubject}
            graphType={selectedType}
            height={600}
            showControls={true}
            onFilterChange={handleGraphFilterChange}
          />
        ) : viewMode === 'list' ? (
          knowledgeGraphs.length === 0 ? (
            <Card>
              <div style={{ textAlign: 'center', padding: 48 }}>
                <Text type="secondary">暂无知识图谱数据</Text>
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    尝试在AI助理中保存一些内容到知识图谱，或调整筛选条件
                  </Text>
                </div>
              </div>
            </Card>
          ) : (
            <div>
              {knowledgeGraphs.map(renderKnowledgeGraphCard)}
            </div>
          )
        ) : (
          knowledgeGraphs.length === 0 ? (
            <Card>
              <div style={{ textAlign: 'center', padding: 48 }}>
                <Text type="secondary">暂无知识图谱数据</Text>
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    尝试在AI助理中保存一些内容到知识图谱，或调整筛选条件
                  </Text>
                </div>
              </div>
            </Card>
          ) : (
            <Row gutter={[16, 16]}>
              {knowledgeGraphs.map((graph) => (
                <Col xs={24} md={12} lg={8} key={graph.id}>
                  {renderKnowledgeGraphCard(graph)}
                </Col>
              ))}
            </Row>
          )
        )}
      </Spin>

      {/* 编辑器组件 */}
      <KnowledgeGraphEditor
        visible={editModalVisible}
        onClose={handleEditClose}
        onSuccess={handleEditSuccess}
        editMode={true}
        editData={editingGraph ? {
          id: editingGraph.id,
          title: editingGraph.name,
          subject_id: editingGraph.subject_id,
          subject_name: editingGraph.subject_name,
          content: editingGraph.content || editingGraph.description || '',
          description: editingGraph.description,
          tags: editingGraph.tags || []
        } : undefined}
      />

      {/* 标签管理模态框 */}
      <Modal
        title="管理标签"
        open={tagModalVisible}
        onOk={handleSaveTagChanges}
        onCancel={() => {
          setTagModalVisible(false);
          setManagingTagsGraph(null);
          setNewTag('');
        }}
        width={600}
        okText="保存"
        cancelText="取消"
      >
        {managingTagsGraph && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <Text strong>知识图谱：</Text>
              <Text>{managingTagsGraph.name}</Text>
            </div>
            
            <div style={{ marginBottom: 16 }}>
              <Text strong>当前标签：</Text>
              <div style={{ marginTop: 8 }}>
                {(managingTagsGraph.tags || []).map(tag => (
                  <Tag
                    key={tag}
                    closable
                    onClose={() => handleRemoveTag(tag)}
                    color="blue"
                    style={{ marginBottom: 4 }}
                  >
                    {tag}
                  </Tag>
                ))}
                {(!managingTagsGraph.tags || managingTagsGraph.tags.length === 0) && (
                  <Text type="secondary">暂无标签</Text>
                )}
              </div>
            </div>
            
            <div>
              <Text strong>添加新标签：</Text>
              <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
                <Input
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  placeholder="输入标签名称"
                  onPressEnter={handleAddTag}
                  style={{ flex: 1 }}
                />
                <Button
                  type="primary"
                  onClick={handleAddTag}
                  disabled={!newTag.trim()}
                >
                  添加
                </Button>
              </div>
            </div>
          </div>
        )}
      </Modal>

      {/* 详情展示抽屉 */}
      <Drawer
        title={
          selectedGraphForDetail ? (
            <Space>
              <Avatar 
                style={{ backgroundColor: '#1890ff' }}
                icon={<NodeIndexOutlined />}
              />
              <div>
                <div>{selectedGraphForDetail.name || '未命名知识图谱'}</div>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  {graphTypeNames[selectedGraphForDetail.graph_type as keyof typeof graphTypeNames] || selectedGraphForDetail.graph_type}
                </Text>
              </div>
            </Space>
          ) : null
        }
        placement="right"
        width={600}
        open={detailDrawerVisible}
        onClose={() => setDetailDrawerVisible(false)}
      >
        {selectedGraphForDetail && (
          <div>
            {/* 基本信息 */}
            <div style={{ marginBottom: 16 }}>
              <Text strong>基本信息：</Text>
              <div style={{ marginTop: 8, padding: 12, backgroundColor: '#f8fafc', borderRadius: 6 }}>
                <Row gutter={[16, 8]}>
                  <Col span={12}>
                    <Text type="secondary">学科：</Text>
                    <Text>{selectedGraphForDetail.subject_name || '未知学科'}</Text>
                  </Col>
                  <Col span={12}>
                    <Text type="secondary">年份：</Text>
                    <Text>{selectedGraphForDetail.year}</Text>
                  </Col>
                  <Col span={24}>
                    <Text type="secondary">创建时间：</Text>
                    <Text>{new Date(selectedGraphForDetail.created_at).toLocaleString()}</Text>
                  </Col>
                  <Col span={24}>
                    <Text type="secondary">更新时间：</Text>
                    <Text>{new Date(selectedGraphForDetail.updated_at).toLocaleString()}</Text>
                  </Col>
                </Row>
              </div>
            </div>

            {/* 描述信息 */}
            {selectedGraphForDetail.description && (
              <div style={{ marginBottom: 16 }}>
                <Text strong>描述：</Text>
                <div style={{ 
                  marginTop: 8, 
                  padding: 12, 
                  backgroundColor: '#f8fafc', 
                  borderRadius: 6 
                }}>
                  <Text>{selectedGraphForDetail.description}</Text>
                </div>
              </div>
            )}

            {/* 标签信息 */}
            {selectedGraphForDetail.tags && selectedGraphForDetail.tags.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <Text strong>标签：</Text>
                <div style={{ marginTop: 8 }}>
                  {selectedGraphForDetail.tags.map(tag => (
                    <Tag key={tag} color="blue" style={{ marginBottom: 4 }}>{tag}</Tag>
                  ))}
                </div>
              </div>
            )}

            {/* 图谱统计 */}
            <div style={{ marginBottom: 16 }}>
              <Text strong>图谱统计：</Text>
              <div style={{ marginTop: 8, padding: 12, backgroundColor: '#f8fafc', borderRadius: 6 }}>
                <Row gutter={[16, 8]}>
                  <Col span={12}>
                    <Text type="secondary">节点数量：</Text>
                    <Text>{selectedGraphForDetail.nodes?.length || 0}</Text>
                  </Col>
                  <Col span={12}>
                    <Text type="secondary">边数量：</Text>
                    <Text>{selectedGraphForDetail.edges?.length || 0}</Text>
                  </Col>
                </Row>
              </div>
            </div>

            {/* 内容信息 */}
            {selectedGraphForDetail.content && (
              <div style={{ marginBottom: 16 }}>
                <Text strong>内容：</Text>
                <div style={{ 
                  marginTop: 8, 
                  padding: 16, 
                  backgroundColor: '#f5f5f5', 
                  borderRadius: 6,
                  maxHeight: '400px',
                  overflow: 'auto'
                }}>
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {selectedGraphForDetail.content}
                  </ReactMarkdown>
                </div>
              </div>
            )}

            {/* 节点详情 */}
            {selectedGraphForDetail.nodes && selectedGraphForDetail.nodes.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <Text strong>节点详情：</Text>
                <div style={{ marginTop: 8, maxHeight: '300px', overflow: 'auto' }}>
                  {selectedGraphForDetail.nodes.slice(0, 10).map((node: any, index: number) => (
                    <Card key={node.id || index} size="small" style={{ marginBottom: 8 }}>
                      <div>
                        <Text strong>{node.name || `节点 ${index + 1}`}</Text>
                        {node.tags && node.tags.length > 0 && (
                           <div style={{ marginTop: 4 }}>
                             {node.tags.map((tag: string) => (
                               <Tag key={tag} color="green" style={{ fontSize: '12px' }}>{tag}</Tag>
                             ))}
                           </div>
                         )}
                        {node.content && (
                          <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                            {node.content.length > 100 ? `${node.content.substring(0, 100)}...` : node.content}
                          </div>
                        )}
                      </div>
                    </Card>
                  ))}
                  {selectedGraphForDetail.nodes.length > 10 && (
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      显示前10个节点，共{selectedGraphForDetail.nodes.length}个节点
                    </Text>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default KnowledgeGraph;