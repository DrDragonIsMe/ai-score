import {
    DownloadOutlined,
    ReloadOutlined
} from '@ant-design/icons';
import {
    Button,
    Card,
    Col,
    List,
    message,
    Modal,
    Row,
    Select,
    Space,
    Spin,
    Tag,
    Typography
} from 'antd';
import * as d3 from 'd3';
import React, { useEffect, useRef, useState } from 'react';
import api from '../services/api';

const { Option } = Select;
const { Text, Title } = Typography;

interface KnowledgePoint {
    id: string;
    name: string;
    difficulty: number;
    importance: number;
    mastery_level: number;
    question_count: number;
    chapter_id: string;
    chapter_name: string;
}

interface GraphNode extends d3.SimulationNodeDatum {
    id: string;
    name: string;
    type: 'chapter' | 'knowledge_point' | 'sub_knowledge_point' | 'subject' | 'ai_content';
    level: number;
    difficulty: number;
    importance: number;
    mastery_level: number;
    question_count: number;
    content?: string;
}

interface GraphLink {
    source: string | GraphNode;
    target: string | GraphNode;
    type: 'hierarchy' | 'relation';
    strength: number;
}

interface KnowledgeGraph {
    id: string;
    subject_id: string;
    graph_type: string;
    nodes: GraphNode[];
    edges: GraphLink[];
    layout_config: {
        layout: string;
        node_size_factor: number;
        link_strength_factor: number;
        color_scheme: string;
    };
}

interface Question {
    id: string;
    content: string;
    type: string;
    difficulty: number;
    score: number;
    knowledge_points: string[];
    paper_name: string;
    year: number;
}

interface KnowledgeGraphViewerProps {
    subjectId: string;
}

const KnowledgeGraphViewer: React.FC<KnowledgeGraphViewerProps> = ({ subjectId }) => {
    const [graph, setGraph] = useState<KnowledgeGraph | null>(null);
    const [loading, setLoading] = useState(false);
    const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
    const [relatedQuestions, setRelatedQuestions] = useState<Question[]>([]);
    const [questionsModalVisible, setQuestionsModalVisible] = useState(false);
    const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());
    const [selectedQuestion, setSelectedQuestion] = useState<Question | null>(null);
    const [graphType, setGraphType] = useState('exam_scope');
    const svgRef = useRef<SVGSVGElement>(null);
    const simulationRef = useRef<d3.Simulation<GraphNode, GraphLink> | null>(null);

    useEffect(() => {
        fetchKnowledgeGraph();
    }, [subjectId, graphType]);

    useEffect(() => {
        if (graph && svgRef.current) {
            renderGraph();
        }
        return () => {
            if (simulationRef.current) {
                simulationRef.current.stop();
            }
        };
    }, [graph]);

    const fetchKnowledgeGraph = async () => {
        setLoading(true);
        try {
            const response = await api.get(`/knowledge-graph/${subjectId}?type=${graphType}`);
            console.log('Knowledge graph response:', response.data.data);
            console.log('Nodes count:', response.data.data?.nodes?.length || 0);
            console.log('Edges count:', response.data.data?.edges?.length || 0);
            setGraph(response.data.data);
        } catch (error) {
            console.error('Failed to fetch knowledge graph:', error);
            message.error('获取知识图谱失败');
        } finally {
            setLoading(false);
        }
    };

    const fetchRelatedQuestions = async (knowledgePointId: string) => {
        try {
            const response = await api.get(`/knowledge-graph/knowledge-points/${knowledgePointId}/questions`);
            setRelatedQuestions(response.data.data);
            setQuestionsModalVisible(true);
        } catch (error) {
            message.error('获取相关题目失败');
        }
    };

    const handleQuestionClick = (question: Question) => {
        setSelectedQuestion(question);
        // 高亮显示与该题目相关的知识点
        const relatedNodeIds = new Set(question.knowledge_points);
        setHighlightedNodes(relatedNodeIds);

        // 重新渲染图谱以显示高亮效果
        if (graph) {
            renderGraph();
        }
    };

    const clearHighlight = () => {
        setHighlightedNodes(new Set());
        setSelectedQuestion(null);
        // 重新渲染图谱以清除高亮效果
        if (graph) {
            renderGraph();
        }
    };

    const getNodeColor = (node: GraphNode) => {
        // 如果节点被高亮，使用特殊颜色
        if (highlightedNodes.has(node.id)) {
            return '#ff1890'; // 高亮颜色 - 粉红色
        }

        // 根据图谱类型使用不同的颜色方案
        if (graphType === 'exam_scope') {
            // 考试范围：根据重要程度着色
            const importance = node.importance || 1;
            if (importance >= 5) return '#ff4d4f'; // 极重要 - 红色
            if (importance >= 4) return '#fa8c16'; // 重要 - 橙色
            if (importance >= 3) return '#fadb14'; // 一般重要 - 黄色
            return '#d9d9d9'; // 不重要 - 灰色
        } else if (graphType === 'mastery_level') {
            // 掌握情况：根据掌握度着色
            const mastery = node.mastery_level || 0;
            if (mastery >= 0.8) return '#52c41a'; // 已掌握 - 绿色
            if (mastery >= 0.6) return '#fadb14'; // 基本掌握 - 黄色
            if (mastery >= 0.4) return '#fa8c16'; // 部分掌握 - 橙色
            return '#ff4d4f'; // 未掌握 - 红色
        } else {
            // 完整知识图谱：按节点类型着色
            const colors = {
                subject: '#722ed1',
                chapter: '#1890ff',
                knowledge_point: '#52c41a',
                sub_knowledge_point: '#faad14',
                ai_content: '#13c2c2'
            };
            return colors[node.type as keyof typeof colors] || '#d9d9d9';
        }
    };

    const getNodeSize = (node: GraphNode) => {
        const baseSize = 8;
        const importanceFactor = (node.importance || 1) * 2;
        const questionFactor = Math.log(Math.max(node.question_count || 1, 1)) + 1;
        return baseSize + importanceFactor + questionFactor;
    };

    const renderGraph = () => {
        if (!graph || !svgRef.current) {
            console.log('Cannot render graph:', { graph: !!graph, svgRef: !!svgRef.current });
            return;
        }

        console.log('Rendering graph with nodes:', graph.nodes.length, 'edges:', graph.edges.length);
        const svg = d3.select(svgRef.current);
        svg.selectAll('*').remove();

        const width = 800;
        const height = 600;
        const margin = { top: 20, right: 20, bottom: 20, left: 20 };

        svg.attr('width', width).attr('height', height);

        const g = svg.append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        // 创建缩放行为
        const zoom = d3.zoom<SVGSVGElement, unknown>()
            .scaleExtent([0.1, 3])
            .on('zoom', (event) => {
                g.attr('transform', event.transform);
            });

        svg.call(zoom);

        // 创建力导向图模拟
        const simulation = d3.forceSimulation<GraphNode>(graph.nodes)
            .force('link', d3.forceLink<GraphNode, GraphLink>(graph.edges)
                .id(d => d.id)
                .distance(d => 50 + (d.strength || 1) * 30)
            )
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter((width - margin.left - margin.right) / 2, (height - margin.top - margin.bottom) / 2))
            .force('collision', d3.forceCollide().radius(d => getNodeSize(d as GraphNode) + 5))

        simulationRef.current = simulation;

        // 创建连线
        const links = g.append('g')
            .attr('class', 'links')
            .selectAll('line')
            .data(graph.edges)
            .enter().append('line')
            .attr('stroke', '#999')
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', d => Math.sqrt(d.strength || 1));

        // 创建节点组
        const nodeGroups = g.append('g')
            .attr('class', 'nodes')
            .selectAll('g')
            .data(graph.nodes)
            .enter().append('g')
            .attr('class', 'node')
            .style('cursor', 'pointer')
            .call(d3.drag<SVGGElement, GraphNode>()
                .on('start', (event, d) => {
                    if (!event.active) simulation.alphaTarget(0.3).restart();
                    d.fx = d.x;
                    d.fy = d.y;
                })
                .on('drag', (event, d) => {
                    d.fx = event.x;
                    d.fy = event.y;
                })
                .on('end', (event, d) => {
                    if (!event.active) simulation.alphaTarget(0);
                    d.fx = null;
                    d.fy = null;
                })
            );

        // 添加节点圆圈
        nodeGroups.append('circle')
            .attr('r', d => getNodeSize(d))
            .attr('fill', d => getNodeColor(d))
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .on('click', (event, d) => {
                setSelectedNode(d);
                if (d.type === 'knowledge_point' || d.type === 'sub_knowledge_point') {
                    fetchRelatedQuestions(d.id);
                }
            })
            .on('mouseover', function (event, d) {
                d3.select(this)
                    .transition()
                    .duration(200)
                    .attr('r', getNodeSize(d) * 1.2)
                    .attr('stroke-width', 3);
            })
            .on('mouseout', function (event, d) {
                d3.select(this)
                    .transition()
                    .duration(200)
                    .attr('r', getNodeSize(d))
                    .attr('stroke-width', 2);
            });

        // 添加节点标签
        nodeGroups.append('text')
            .text(d => d.name.length > 8 ? d.name.substring(0, 8) + '...' : d.name)
            .attr('text-anchor', 'middle')
            .attr('dy', d => getNodeSize(d) + 15)
            .attr('font-size', '12px')
            .attr('fill', '#333')
            .style('pointer-events', 'none');

        // 添加掌握度指示器
        nodeGroups.filter(d => d.mastery_level !== undefined)
            .append('circle')
            .attr('r', 3)
            .attr('cx', d => getNodeSize(d) - 3)
            .attr('cy', d => -getNodeSize(d) + 3)
            .attr('fill', d => {
                const level = d.mastery_level || 0;
                if (level >= 0.8) return '#52c41a';
                if (level >= 0.6) return '#faad14';
                if (level >= 0.4) return '#fa8c16';
                return '#f5222d';
            })
            .attr('stroke', '#fff')
            .attr('stroke-width', 1);

        // 更新位置
        simulation.on('tick', () => {
            links
                .attr('x1', d => (d.source as GraphNode).x || 0)
                .attr('y1', d => (d.source as GraphNode).y || 0)
                .attr('x2', d => (d.target as GraphNode).x || 0)
                .attr('y2', d => (d.target as GraphNode).y || 0);

            nodeGroups
                .attr('transform', d => `translate(${d.x || 0},${d.y || 0})`);
        });
    };

    const handleDownloadGraph = () => {
        if (!svgRef.current) return;

        const svgElement = svgRef.current;
        const serializer = new XMLSerializer();
        const svgString = serializer.serializeToString(svgElement);
        const blob = new Blob([svgString], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = url;
        link.download = `knowledge-graph-${graphType}.svg`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    const renderLegend = () => {
        const legendItems = [];

        // 添加高亮颜色说明（如果有高亮节点）
        if (highlightedNodes.size > 0) {
            legendItems.push(
                { color: '#ff1890', label: '高亮知识点 (与选中题目相关)' }
            );
        }

        if (graphType === 'exam_scope') {
            legendItems.push(
                { color: '#ff4d4f', label: '极重要知识点 (重要度≥5)' },
                { color: '#fa8c16', label: '重要知识点 (重要度≥4)' },
                { color: '#fadb14', label: '一般重要 (重要度≥3)' },
                { color: '#d9d9d9', label: '不重要 (重要度<3)' }
            );
        } else if (graphType === 'mastery_level') {
            legendItems.push(
                { color: '#52c41a', label: '已掌握 (掌握度≥80%)' },
                { color: '#fadb14', label: '基本掌握 (掌握度≥60%)' },
                { color: '#fa8c16', label: '部分掌握 (掌握度≥40%)' },
                { color: '#ff4d4f', label: '未掌握 (掌握度<40%)' }
            );
        } else {
            legendItems.push(
                { color: '#722ed1', label: '学科' },
                { color: '#1890ff', label: '章节' },
                { color: '#52c41a', label: '知识点' },
                { color: '#faad14', label: '子知识点' },
                { color: '#13c2c2', label: 'AI助理内容' }
            );
        }

        return (
            <Card size="small" title="图例" style={{ marginTop: 16 }}>
                <Space wrap>
                    {legendItems.map((item, index) => (
                        <div key={index} style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
                            <div
                                style={{
                                    width: 12,
                                    height: 12,
                                    backgroundColor: item.color,
                                    borderRadius: '50%',
                                    marginRight: 8
                                }}
                            />
                            <Text style={{ fontSize: 12 }}>{item.label}</Text>
                        </div>
                    ))}
                </Space>
            </Card>
        );
    };

    const renderNodeInfo = () => {
        if (!selectedNode) return null;

        return (
            <Card size="small" title="节点信息" style={{ marginTop: 16 }}>
                <Row gutter={[16, 8]}>
                    <Col span={24}>
                        <Title level={5}>{selectedNode.name}</Title>
                    </Col>
                    <Col span={12}>
                        <Text strong>类型：</Text>
                        <Tag color={getNodeColor(selectedNode)}>
                            {selectedNode.type === 'chapter' ? '章节' :
                                selectedNode.type === 'knowledge_point' ? '知识点' : '子知识点'}
                        </Tag>
                    </Col>
                    <Col span={12}>
                        <Text strong>难度：</Text>
                        <Text>{selectedNode.difficulty || '-'}</Text>
                    </Col>
                    <Col span={12}>
                        <Text strong>重要性：</Text>
                        <Text>{selectedNode.importance || '-'}</Text>
                    </Col>
                    <Col span={12}>
                        <Text strong>题目数量：</Text>
                        <Text>{selectedNode.question_count || 0}</Text>
                    </Col>
                    {selectedNode.mastery_level !== undefined && (
                        <Col span={24}>
                            <Text strong>掌握度：</Text>
                            <Text style={{
                                color: selectedNode.mastery_level >= 0.8 ? '#52c41a' :
                                    selectedNode.mastery_level >= 0.6 ? '#faad14' :
                                        selectedNode.mastery_level >= 0.4 ? '#fa8c16' : '#f5222d'
                            }}>
                                {Math.round((selectedNode.mastery_level || 0) * 100)}%
                            </Text>
                        </Col>
                    )}
                </Row>
            </Card>
        );
    };

    return (
        <div>
            <Card
                title="知识图谱"
                extra={
                    <Space>
                        <Select
                            value={graphType}
                            onChange={setGraphType}
                            style={{ width: 140 }}
                        >
                            <Option value="exam_scope">考试范围</Option>
                            <Option value="full_knowledge">完整知识</Option>
                            <Option value="mastery_level">掌握情况</Option>
                            <Option value="ai_assistant_content">AI助理内容</Option>
                        </Select>
                        <Button
                            icon={<ReloadOutlined />}
                            onClick={fetchKnowledgeGraph}
                            loading={loading}
                        >
                            刷新
                        </Button>
                        <Button
                            icon={<DownloadOutlined />}
                            onClick={handleDownloadGraph}
                            disabled={!graph}
                        >
                            导出
                        </Button>
                    </Space>
                }
            >
                <Spin spinning={loading}>
                    <div style={{ textAlign: 'center', marginBottom: 16 }}>
                        <svg ref={svgRef} style={{ border: '1px solid #d9d9d9', borderRadius: 4 }} />
                    </div>
                </Spin>

                {renderNodeInfo()}
                {renderLegend()}
            </Card>

            <Modal
                title={
                    <Space>
                        <span>{`相关题目 - ${selectedNode?.name}`}</span>
                        {highlightedNodes.size > 0 && (
                            <Button size="small" onClick={clearHighlight}>
                                清除高亮
                            </Button>
                        )}
                    </Space>
                }
                open={questionsModalVisible}
                onCancel={() => {
                    setQuestionsModalVisible(false);
                    clearHighlight();
                }}
                footer={null}
                width={800}
            >
                {selectedQuestion && (
                    <div style={{ marginBottom: 16, padding: 12, backgroundColor: '#f0f2f5', borderRadius: 6 }}>
                        <Text strong>当前选中题目：</Text>
                        <div style={{ marginTop: 8 }}>
                            <Space>
                                <Text>{selectedQuestion.paper_name}</Text>
                                <Tag>{selectedQuestion.year}年</Tag>
                                <Tag color="blue">{selectedQuestion.type}</Tag>
                                <Tag color="orange">{selectedQuestion.score}分</Tag>
                            </Space>
                        </div>
                        <div style={{ marginTop: 8 }}>
                            <Text>相关知识点已在图谱中高亮显示</Text>
                        </div>
                    </div>
                )}
                <List
                    dataSource={relatedQuestions}
                    renderItem={(question, index) => (
                        <List.Item
                            style={{
                                cursor: 'pointer',
                                backgroundColor: selectedQuestion?.id === question.id ? '#e6f7ff' : 'transparent'
                            }}
                            onClick={() => handleQuestionClick(question)}
                        >
                            <List.Item.Meta
                                avatar={<div style={{
                                    width: 24,
                                    height: 24,
                                    borderRadius: '50%',
                                    backgroundColor: selectedQuestion?.id === question.id ? '#1890ff' : '#d9d9d9',
                                    color: 'white',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontSize: '12px'
                                }}>
                                    {index + 1}
                                </div>}
                                title={
                                    <Space>
                                        <Text strong>{question.paper_name}</Text>
                                        <Tag>{question.year}年</Tag>
                                        <Tag color="blue">{question.type}</Tag>
                                        <Tag color="orange">{question.score}分</Tag>
                                        {selectedQuestion?.id === question.id && (
                                            <Tag color="pink">已选中</Tag>
                                        )}
                                    </Space>
                                }
                                description={
                                    <div>
                                        <Text>{question.content.substring(0, 100)}...</Text>
                                        <br />
                                        <Text type="secondary">难度: {question.difficulty}</Text>
                                        <br />
                                        <Text type="secondary" style={{ fontSize: '12px' }}>
                                            点击查看相关知识点高亮
                                        </Text>
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
            </Modal>
        </div>
    );
};

export default KnowledgeGraphViewer;
