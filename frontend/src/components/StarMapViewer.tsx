import {
    DownloadOutlined,
    ReloadOutlined,
    FullscreenOutlined,
    InfoCircleOutlined
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
    Typography,
    Tooltip
} from 'antd';
import * as d3 from 'd3';
import React, { useEffect, useRef, useState } from 'react';
import api from '../services/api';

const { Option } = Select;
const { Text, Title } = Typography;

interface StarNode extends d3.SimulationNodeDatum {
    id: string;
    name: string;
    type: 'chapter' | 'knowledge_point' | 'sub_knowledge_point' | 'subject';
    level: number;
    difficulty: number;
    importance: number;
    examFrequency: number; // 考试频率 0-1
    mastery_level: number;
    question_count: number;
    examYears: number[]; // 出现在哪些年份的考试中
}

interface StarLink {
    source: string | StarNode;
    target: string | StarNode;
    type: 'hierarchy' | 'relation';
    strength: number;
}

interface StarMapData {
    id: string;
    subject_id: string;
    nodes: StarNode[];
    edges: StarLink[];
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

interface StarMapViewerProps {
    subjectId: string;
}

const StarMapViewer: React.FC<StarMapViewerProps> = ({ subjectId }) => {
    const [starMapData, setStarMapData] = useState<StarMapData | null>(null);
    const [loading, setLoading] = useState(false);
    const [selectedNode, setSelectedNode] = useState<StarNode | null>(null);
    const [relatedQuestions, setRelatedQuestions] = useState<Question[]>([]);
    const [questionsModalVisible, setQuestionsModalVisible] = useState(false);
    const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());
    const [selectedQuestion, setSelectedQuestion] = useState<Question | null>(null);
    const [viewMode, setViewMode] = useState('frequency'); // frequency, importance, mastery
    const [isFullscreen, setIsFullscreen] = useState(false);
    const svgRef = useRef<SVGSVGElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const simulationRef = useRef<d3.Simulation<StarNode, StarLink> | null>(null);

    useEffect(() => {
        fetchStarMapData();
    }, [subjectId]);

    useEffect(() => {
        if (starMapData && svgRef.current) {
            renderStarMap();
        }
        return () => {
            if (simulationRef.current) {
                simulationRef.current.stop();
            }
        };
    }, [starMapData, viewMode, isFullscreen]);

    const fetchStarMapData = async () => {
        setLoading(true);
        try {
            // 获取知识图谱数据
            const graphResponse = await api.get(`/knowledge-graph/${subjectId}?type=exam_scope`);
            const graphData = graphResponse.data.data;
            
            // 获取考试频率数据
            const examResponse = await api.get(`/subjects/${subjectId}/exam-frequency`);
            const examData = examResponse.data.data;
            
            // 合并数据，添加考试频率信息
            const enhancedNodes = graphData.nodes.map((node: any) => {
                const examInfo = examData.find((item: any) => item.knowledge_point_id === node.id);
                return {
                    ...node,
                    examFrequency: examInfo ? examInfo.frequency : 0,
                    examYears: examInfo ? examInfo.years : []
                };
            });
            
            setStarMapData({
                id: graphData.id,
                subject_id: graphData.subject_id,
                nodes: enhancedNodes,
                edges: graphData.edges
            });
        } catch (error) {
            message.error('获取星图数据失败');
            // 使用模拟数据作为后备
            setStarMapData(generateMockStarMapData());
        } finally {
            setLoading(false);
        }
    };

    const generateMockStarMapData = (): StarMapData => {
        const mockNodes: StarNode[] = [
            { id: '1', name: '函数', type: 'chapter', level: 1, difficulty: 4, importance: 5, examFrequency: 0.95, mastery_level: 0.8, question_count: 150, examYears: [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024] },
            { id: '2', name: '导数', type: 'knowledge_point', level: 2, difficulty: 5, importance: 5, examFrequency: 0.9, mastery_level: 0.7, question_count: 120, examYears: [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024] },
            { id: '3', name: '三角函数', type: 'knowledge_point', level: 2, difficulty: 3, importance: 4, examFrequency: 0.85, mastery_level: 0.9, question_count: 100, examYears: [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023] },
            { id: '4', name: '数列', type: 'knowledge_point', level: 2, difficulty: 4, importance: 4, examFrequency: 0.8, mastery_level: 0.6, question_count: 90, examYears: [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022] },
            { id: '5', name: '立体几何', type: 'knowledge_point', level: 2, difficulty: 3, importance: 3, examFrequency: 0.75, mastery_level: 0.8, question_count: 80, examYears: [2015, 2016, 2017, 2018, 2019, 2020, 2021] },
            { id: '6', name: '解析几何', type: 'knowledge_point', level: 2, difficulty: 5, importance: 4, examFrequency: 0.7, mastery_level: 0.5, question_count: 70, examYears: [2015, 2016, 2017, 2018, 2019, 2020] },
            { id: '7', name: '概率统计', type: 'knowledge_point', level: 2, difficulty: 3, importance: 3, examFrequency: 0.65, mastery_level: 0.7, question_count: 60, examYears: [2015, 2016, 2017, 2018, 2019] },
            { id: '8', name: '不等式', type: 'knowledge_point', level: 2, difficulty: 2, importance: 2, examFrequency: 0.4, mastery_level: 0.9, question_count: 40, examYears: [2015, 2016, 2017] },
            { id: '9', name: '复数', type: 'knowledge_point', level: 2, difficulty: 2, importance: 2, examFrequency: 0.3, mastery_level: 0.8, question_count: 30, examYears: [2015, 2016] },
            { id: '10', name: '向量', type: 'knowledge_point', level: 2, difficulty: 3, importance: 3, examFrequency: 0.6, mastery_level: 0.75, question_count: 50, examYears: [2015, 2016, 2017, 2018] }
        ];
        
        const mockEdges: StarLink[] = [
            { source: '1', target: '2', type: 'hierarchy', strength: 1 },
            { source: '1', target: '3', type: 'hierarchy', strength: 1 },
            { source: '1', target: '4', type: 'hierarchy', strength: 1 },
            { source: '1', target: '5', type: 'hierarchy', strength: 1 },
            { source: '1', target: '6', type: 'hierarchy', strength: 1 },
            { source: '1', target: '7', type: 'hierarchy', strength: 1 },
            { source: '1', target: '8', type: 'hierarchy', strength: 1 },
            { source: '1', target: '9', type: 'hierarchy', strength: 1 },
            { source: '1', target: '10', type: 'hierarchy', strength: 1 }
        ];
        
        return {
            id: 'mock-star-map',
            subject_id: subjectId,
            nodes: mockNodes,
            edges: mockEdges
        };
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

    const getStarColor = (node: StarNode) => {
        if (highlightedNodes.has(node.id)) {
            return '#FFD700'; // 高亮时使用金色
        }

        switch (viewMode) {
            case 'frequency':
                const freq = node.examFrequency || 0;
                if (freq >= 0.8) return '#FF6B6B'; // 必考 - 亮红色
                if (freq >= 0.6) return '#FFA500'; // 常考 - 橙色
                if (freq >= 0.4) return '#FFD700'; // 一般 - 金色
                return '#87CEEB'; // 少考 - 天蓝色
            
            case 'importance':
                const importance = node.importance || 1;
                if (importance >= 5) return '#FF1493'; // 极重要 - 深粉色
                if (importance >= 4) return '#FF6347'; // 重要 - 番茄色
                if (importance >= 3) return '#FFA500'; // 一般重要 - 橙色
                return '#B0C4DE'; // 不重要 - 浅钢蓝色
            
            case 'mastery':
                const mastery = node.mastery_level || 0;
                if (mastery >= 0.8) return '#32CD32'; // 已掌握 - 酸橙绿
                if (mastery >= 0.6) return '#FFD700'; // 基本掌握 - 金色
                if (mastery >= 0.4) return '#FFA500'; // 部分掌握 - 橙色
                return '#FF6B6B'; // 未掌握 - 亮红色
            
            default:
                return '#87CEEB';
        }
    };

    const getStarSize = (node: StarNode) => {
        const baseSize = 4;
        let sizeFactor = 1;
        
        switch (viewMode) {
            case 'frequency':
                sizeFactor = (node.examFrequency || 0) * 3 + 1;
                break;
            case 'importance':
                sizeFactor = (node.importance || 1) * 0.8;
                break;
            case 'mastery':
                sizeFactor = (1 - (node.mastery_level || 0)) * 3 + 1; // 掌握度越低，星星越大
                break;
        }
        
        return baseSize + sizeFactor * 2;
    };

    const getStarOpacity = (node: StarNode) => {
        if (highlightedNodes.has(node.id)) {
            return 1;
        }
        
        switch (viewMode) {
            case 'frequency':
                return 0.3 + (node.examFrequency || 0) * 0.7;
            case 'importance':
                return 0.3 + ((node.importance || 1) / 5) * 0.7;
            case 'mastery':
                return 0.3 + (node.mastery_level || 0) * 0.7;
            default:
                return 0.8;
        }
    };

    const renderStarMap = () => {
        if (!starMapData || !svgRef.current) return;

        const svg = d3.select(svgRef.current);
        svg.selectAll('*').remove();

        const width = isFullscreen ? window.innerWidth : 800;
        const height = isFullscreen ? window.innerHeight : 600;
        const margin = { top: 20, right: 20, bottom: 20, left: 20 };

        svg.attr('width', width).attr('height', height);

        // 创建星空背景
        const defs = svg.append('defs');
        
        // 创建径向渐变背景
        const gradient = defs.append('radialGradient')
            .attr('id', 'starfield-gradient')
            .attr('cx', '50%')
            .attr('cy', '50%')
            .attr('r', '50%');
        
        gradient.append('stop')
            .attr('offset', '0%')
            .attr('stop-color', '#0B1426')
            .attr('stop-opacity', 1);
        
        gradient.append('stop')
            .attr('offset', '100%')
            .attr('stop-color', '#000000')
            .attr('stop-opacity', 1);
        
        // 添加背景
        svg.append('rect')
            .attr('width', width)
            .attr('height', height)
            .attr('fill', 'url(#starfield-gradient)');
        
        // 添加背景星星
        const backgroundStars = svg.append('g').attr('class', 'background-stars');
        for (let i = 0; i < 200; i++) {
            backgroundStars.append('circle')
                .attr('cx', Math.random() * width)
                .attr('cy', Math.random() * height)
                .attr('r', Math.random() * 1.5 + 0.5)
                .attr('fill', '#FFFFFF')
                .attr('opacity', Math.random() * 0.8 + 0.2)
                .style('animation', `twinkle ${Math.random() * 3 + 2}s infinite`);
        }
        
        // 添加CSS动画
        const style = document.createElement('style');
        style.textContent = `
            @keyframes twinkle {
                0%, 100% { opacity: 0.2; }
                50% { opacity: 1; }
            }
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.2); }
            }
        `;
        document.head.appendChild(style);

        const g = svg.append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        // 创建缩放行为
        const zoom = d3.zoom<SVGSVGElement, unknown>()
            .scaleExtent([0.1, 5])
            .on('zoom', (event) => {
                g.attr('transform', `translate(${margin.left + event.transform.x},${margin.top + event.transform.y}) scale(${event.transform.k})`);
            });

        svg.call(zoom);

        // 创建力导向图模拟
        const simulation = d3.forceSimulation<StarNode>(starMapData.nodes)
            .force('link', d3.forceLink<StarNode, StarLink>(starMapData.edges)
                .id(d => d.id)
                .distance(d => 80 + (d.strength || 1) * 40)
            )
            .force('charge', d3.forceManyBody().strength(-200))
            .force('center', d3.forceCenter((width - margin.left - margin.right) / 2, (height - margin.top - margin.bottom) / 2))
            .force('collision', d3.forceCollide().radius(d => getStarSize(d as StarNode) + 10));

        simulationRef.current = simulation;

        // 创建连线（星座线）
        const links = g.append('g')
            .attr('class', 'constellation-lines')
            .selectAll('line')
            .data(starMapData.edges)
            .enter().append('line')
            .attr('stroke', '#4A90E2')
            .attr('stroke-opacity', 0.3)
            .attr('stroke-width', 1)
            .attr('stroke-dasharray', '2,2');

        // 创建节点组（星星）
        const nodeGroups = g.append('g')
            .attr('class', 'stars')
            .selectAll('g')
            .data(starMapData.nodes)
            .enter().append('g')
            .attr('class', 'star')
            .style('cursor', 'pointer')
            .call(d3.drag<SVGGElement, StarNode>()
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

        // 添加星星光晕
        nodeGroups.append('circle')
            .attr('r', d => getStarSize(d) * 2)
            .attr('fill', d => getStarColor(d))
            .attr('opacity', 0.1)
            .attr('class', 'star-glow');

        // 添加星星主体
        nodeGroups.append('circle')
            .attr('r', d => getStarSize(d))
            .attr('fill', d => getStarColor(d))
            .attr('opacity', d => getStarOpacity(d))
            .attr('stroke', '#FFFFFF')
            .attr('stroke-width', 0.5)
            .attr('class', 'star-body')
            .style('filter', 'drop-shadow(0 0 3px currentColor)')
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
                    .attr('r', getStarSize(d) * 1.5)
                    .style('animation', 'pulse 1s infinite');
                
                // 显示tooltip
                const tooltip = d3.select('body').append('div')
                    .attr('class', 'star-tooltip')
                    .style('position', 'absolute')
                    .style('background', 'rgba(0, 0, 0, 0.8)')
                    .style('color', 'white')
                    .style('padding', '8px')
                    .style('border-radius', '4px')
                    .style('font-size', '12px')
                    .style('pointer-events', 'none')
                    .style('z-index', '1000')
                    .html(`
                        <strong>${d.name}</strong><br/>
                        考试频率: ${(d.examFrequency * 100).toFixed(1)}%<br/>
                        重要程度: ${d.importance}/5<br/>
                        掌握程度: ${(d.mastery_level * 100).toFixed(1)}%<br/>
                        题目数量: ${d.question_count}
                    `)
                    .style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 10) + 'px');
            })
            .on('mouseout', function (event, d) {
                d3.select(this)
                    .transition()
                    .duration(200)
                    .attr('r', getStarSize(d))
                    .style('animation', null);
                
                d3.selectAll('.star-tooltip').remove();
            });

        // 添加星星标签
        nodeGroups.append('text')
            .text(d => d.name.length > 6 ? d.name.substring(0, 6) + '...' : d.name)
            .attr('text-anchor', 'middle')
            .attr('dy', d => getStarSize(d) + 20)
            .attr('font-size', '11px')
            .attr('fill', '#FFFFFF')
            .attr('opacity', 0.8)
            .style('pointer-events', 'none')
            .style('text-shadow', '1px 1px 2px rgba(0,0,0,0.8)');

        // 更新位置
        simulation.on('tick', () => {
            links
                .attr('x1', d => (d.source as StarNode).x || 0)
                .attr('y1', d => (d.source as StarNode).y || 0)
                .attr('x2', d => (d.target as StarNode).x || 0)
                .attr('y2', d => (d.target as StarNode).y || 0);

            nodeGroups
                .attr('transform', d => `translate(${d.x || 0},${d.y || 0})`);
        });
    };

    const handleFullscreen = () => {
        setIsFullscreen(!isFullscreen);
    };

    const handleDownloadStarMap = () => {
        if (!svgRef.current) return;

        const svgElement = svgRef.current;
        const serializer = new XMLSerializer();
        const svgString = serializer.serializeToString(svgElement);
        const blob = new Blob([svgString], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = url;
        link.download = `star-map-${viewMode}.svg`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    const renderLegend = () => {
        const legendItems = [];
        
        switch (viewMode) {
            case 'frequency':
                legendItems.push(
                    { color: '#FF6B6B', label: '必考 (≥80%)', size: 'large' },
                    { color: '#FFA500', label: '常考 (60-80%)', size: 'medium' },
                    { color: '#FFD700', label: '一般 (40-60%)', size: 'small' },
                    { color: '#87CEEB', label: '少考 (<40%)', size: 'small' }
                );
                break;
            case 'importance':
                legendItems.push(
                    { color: '#FF1493', label: '极重要 (5分)', size: 'large' },
                    { color: '#FF6347', label: '重要 (4分)', size: 'medium' },
                    { color: '#FFA500', label: '一般重要 (3分)', size: 'small' },
                    { color: '#B0C4DE', label: '不重要 (≤2分)', size: 'small' }
                );
                break;
            case 'mastery':
                legendItems.push(
                    { color: '#32CD32', label: '已掌握 (≥80%)', size: 'small' },
                    { color: '#FFD700', label: '基本掌握 (60-80%)', size: 'small' },
                    { color: '#FFA500', label: '部分掌握 (40-60%)', size: 'medium' },
                    { color: '#FF6B6B', label: '未掌握 (<40%)', size: 'large' }
                );
                break;
        }
        
        return (
            <Card size="small" title="图例" style={{ marginTop: 16 }}>
                <Space direction="vertical" size="small">
                    {legendItems.map((item, index) => (
                        <Space key={index} size="small">
                            <div
                                style={{
                                    width: item.size === 'large' ? 16 : item.size === 'medium' ? 12 : 8,
                                    height: item.size === 'large' ? 16 : item.size === 'medium' ? 12 : 8,
                                    backgroundColor: item.color,
                                    borderRadius: '50%',
                                    boxShadow: `0 0 6px ${item.color}`
                                }}
                            />
                            <Text style={{ fontSize: 12 }}>{item.label}</Text>
                        </Space>
                    ))}
                </Space>
            </Card>
        );
    };

    return (
        <div ref={containerRef} style={{ height: isFullscreen ? '100vh' : 'auto' }}>
            <Card
                title="知识点星图"
                extra={
                    <Space>
                        <Select
                            value={viewMode}
                            onChange={setViewMode}
                            style={{ width: 120 }}
                        >
                            <Option value="frequency">考试频率</Option>
                            <Option value="importance">重要程度</Option>
                            <Option value="mastery">掌握情况</Option>
                        </Select>
                        <Tooltip title="全屏显示">
                            <Button
                                icon={<FullscreenOutlined />}
                                onClick={handleFullscreen}
                            />
                        </Tooltip>
                        <Tooltip title="刷新数据">
                            <Button
                                icon={<ReloadOutlined />}
                                onClick={fetchStarMapData}
                                loading={loading}
                            />
                        </Tooltip>
                        <Tooltip title="下载星图">
                            <Button
                                icon={<DownloadOutlined />}
                                onClick={handleDownloadStarMap}
                            />
                        </Tooltip>
                    </Space>
                }
                style={{
                    position: isFullscreen ? 'fixed' : 'relative',
                    top: isFullscreen ? 0 : 'auto',
                    left: isFullscreen ? 0 : 'auto',
                    width: isFullscreen ? '100vw' : 'auto',
                    height: isFullscreen ? '100vh' : 'auto',
                    zIndex: isFullscreen ? 1000 : 'auto',
                    backgroundColor: isFullscreen ? '#000' : 'auto'
                }}
            >
                <Spin spinning={loading}>
                    <Row gutter={16}>
                        <Col span={isFullscreen ? 24 : 18}>
                            <div style={{ 
                                border: '1px solid #d9d9d9', 
                                borderRadius: 6,
                                overflow: 'hidden',
                                backgroundColor: '#000'
                            }}>
                                <svg
                                    ref={svgRef}
                                    style={{ display: 'block' }}
                                />
                            </div>
                        </Col>
                        {!isFullscreen && (
                            <Col span={6}>
                                {renderLegend()}
                                {selectedNode && (
                                    <Card size="small" title="节点信息" style={{ marginTop: 16 }}>
                                        <Space direction="vertical" size="small">
                                            <Text><strong>名称:</strong> {selectedNode.name}</Text>
                                            <Text><strong>类型:</strong> {selectedNode.type}</Text>
                                            <Text><strong>考试频率:</strong> {(selectedNode.examFrequency * 100).toFixed(1)}%</Text>
                                            <Text><strong>重要程度:</strong> {selectedNode.importance}/5</Text>
                                            <Text><strong>掌握程度:</strong> {(selectedNode.mastery_level * 100).toFixed(1)}%</Text>
                                            <Text><strong>题目数量:</strong> {selectedNode.question_count}</Text>
                                            {selectedNode.examYears.length > 0 && (
                                                <div>
                                                    <Text><strong>考试年份:</strong></Text>
                                                    <div style={{ marginTop: 4 }}>
                                                        {selectedNode.examYears.map(year => (
                                                            <Tag key={year}>{year}</Tag>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </Space>
                                    </Card>
                                )}
                            </Col>
                        )}
                    </Row>
                </Spin>
            </Card>

            <Modal
                title="相关题目"
                open={questionsModalVisible}
                onCancel={() => setQuestionsModalVisible(false)}
                footer={null}
                width={800}
            >
                <List
                    dataSource={relatedQuestions}
                    renderItem={(question) => (
                        <List.Item
                            key={question.id}
                            style={{
                                cursor: 'pointer',
                                backgroundColor: selectedQuestion?.id === question.id ? '#f0f0f0' : 'transparent'
                            }}
                            onClick={() => setSelectedQuestion(question)}
                        >
                            <List.Item.Meta
                                title={
                                    <Space>
                                        <Text>{question.paper_name}</Text>
                                        <Tag color="blue">{question.year}</Tag>
                                        <Tag color="green">{question.type}</Tag>
                                        <Tag color="orange">{question.score}分</Tag>
                                    </Space>
                                }
                                description={question.content.substring(0, 100) + '...'}
                            />
                        </List.Item>
                    )}
                />
            </Modal>
        </div>
    );
};

export default StarMapViewer;