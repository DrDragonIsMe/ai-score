import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { Card, Spin, Typography, Tag, Space, Statistic, Row, Col, Divider } from 'antd';

const { Title, Text } = Typography;

interface KnowledgePoint {
    id: string;
    name: string;
    code: string;
    difficulty: number;
    importance: number;
    chapter: {
        id: string;
        name: string;
    } | null;
    paper_stats: {
        question_count: number;
        total_score: number;
        avg_difficulty: number;
        question_types: string[];
    };
}

interface StarNode extends KnowledgePoint {
    x?: number;
    y?: number;
    vx?: number;
    vy?: number;
    fx?: number | null;
    fy?: number | null;
    radius: number;
}

interface StarMapData {
    paper_info: {
        id: string;
        title: string;
        year: number;
        exam_type: string;
        total_score: number;
        question_count: number;
    };
    knowledge_points: KnowledgePoint[];
    highlight_nodes: string[];
    statistics: {
        total_knowledge_points: number;
        coverage_rate: number;
    };
}

interface ExamPaperStarMapProps {
    data: StarMapData | null;
    loading: boolean;
}

const ExamPaperStarMap: React.FC<ExamPaperStarMapProps> = ({ data, loading }) => {
    const svgRef = useRef<SVGSVGElement>(null);
    const [selectedNode, setSelectedNode] = useState<KnowledgePoint | null>(null);

    useEffect(() => {
        if (!data || !svgRef.current) return;

        const svg = d3.select(svgRef.current);
        svg.selectAll('*').remove();

        const width = 800;
        const height = 600;
        const margin = { top: 20, right: 20, bottom: 20, left: 20 };

        svg.attr('width', width).attr('height', height);

        // 创建主容器
        const container = svg.append('g')
            .attr('transform', `translate(${margin.left}, ${margin.top})`);

        // 准备节点数据
        const nodes: StarNode[] = data.knowledge_points.map(kp => ({
            ...kp,
            x: Math.random() * (width - 2 * margin.left),
            y: Math.random() * (height - 2 * margin.top),
            radius: Math.max(8, Math.min(30, kp.paper_stats.question_count * 5 + kp.importance * 3))
        }));

        // 创建力导向图模拟
        const simulation = d3.forceSimulation<StarNode>(nodes)
            .force('charge', d3.forceManyBody().strength(-100))
            .force('center', d3.forceCenter((width - 2 * margin.left) / 2, (height - 2 * margin.top) / 2))
            .force('collision', d3.forceCollide<StarNode>().radius(d => d.radius + 5));

        // 创建节点组
        const nodeGroups = container.selectAll('.node-group')
            .data(nodes)
            .enter()
            .append('g')
            .attr('class', 'node-group')
            .style('cursor', 'pointer');

        // 添加光晕效果
        nodeGroups.append('circle')
            .attr('r', d => d.radius + 3)
            .attr('fill', d => getNodeColor(d))
            .attr('opacity', 0.3)
            .attr('class', 'node-glow');

        // 添加主节点
        nodeGroups.append('circle')
            .attr('r', d => d.radius)
            .attr('fill', d => getNodeColor(d))
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .attr('opacity', 0.8)
            .on('click', (event, d) => {
                setSelectedNode(d);
            })
            .on('mouseover', function(event, d) {
                d3.select(this)
                    .transition()
                    .duration(200)
                    .attr('r', d.radius * 1.2)
                    .attr('opacity', 1);
                
                // 显示tooltip
                showTooltip(event, d);
            })
            .on('mouseout', function(event, d) {
                d3.select(this)
                    .transition()
                    .duration(200)
                    .attr('r', d.radius)
                    .attr('opacity', 0.8);
                
                hideTooltip();
            });

        // 添加节点标签
        nodeGroups.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', d => d.radius + 15)
            .attr('font-size', '10px')
            .attr('fill', '#333')
            .text(d => d.name.length > 6 ? d.name.substring(0, 6) + '...' : d.name);

        // 添加题目数量标签
        nodeGroups.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '0.35em')
            .attr('font-size', '10px')
            .attr('font-weight', 'bold')
            .attr('fill', '#fff')
            .text(d => d.paper_stats.question_count);

        // 更新节点位置
        simulation.on('tick', () => {
            nodeGroups.attr('transform', d => `translate(${d.x}, ${d.y})`);
        });

        // 清理函数
        return () => {
            simulation.stop();
        };
    }, [data]);

    const getNodeColor = (node: KnowledgePoint) => {
        // 根据题目数量和重要程度确定颜色
        const questionCount = node.paper_stats.question_count;
        const importance = node.importance;
        
        if (questionCount >= 3) {
            return '#ff4d4f'; // 红色 - 高频考点
        } else if (questionCount >= 2) {
            return '#fa8c16'; // 橙色 - 中频考点
        } else if (questionCount >= 1) {
            return '#52c41a'; // 绿色 - 低频考点
        } else {
            return '#d9d9d9'; // 灰色 - 未涉及
        }
    };

    const showTooltip = (event: any, node: KnowledgePoint) => {
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
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 10) + 'px')
            .html(`
                <div><strong>${node.name}</strong></div>
                <div>章节: ${node.chapter?.name || '未分类'}</div>
                <div>题目数量: ${node.paper_stats.question_count}</div>
                <div>总分值: ${node.paper_stats.total_score}</div>
                <div>平均难度: ${node.paper_stats.avg_difficulty}</div>
                <div>题型: ${node.paper_stats.question_types.join(', ')}</div>
            `);
    };

    const hideTooltip = () => {
        d3.selectAll('.star-tooltip').remove();
    };

    if (loading) {
        return (
            <div style={{ textAlign: 'center', padding: '50px' }}>
                <Spin size="large" />
                <div style={{ marginTop: 16 }}>正在加载星图数据...</div>
            </div>
        );
    }

    if (!data) {
        return (
            <div style={{ textAlign: 'center', padding: '50px' }}>
                <Text type="secondary">暂无数据</Text>
            </div>
        );
    }

    return (
        <div>
            {/* 试卷信息 */}
            <Card size="small" style={{ marginBottom: 16 }}>
                <Row gutter={16}>
                    <Col span={6}>
                        <Statistic title="试卷标题" value={data.paper_info.title} />
                    </Col>
                    <Col span={4}>
                        <Statistic title="年份" value={data.paper_info.year} />
                    </Col>
                    <Col span={4}>
                        <Statistic title="题目数量" value={data.paper_info.question_count} />
                    </Col>
                    <Col span={4}>
                        <Statistic title="总分" value={data.paper_info.total_score} />
                    </Col>
                    <Col span={6}>
                        <Statistic title="涉及知识点" value={data.statistics.total_knowledge_points} />
                    </Col>
                </Row>
            </Card>

            <Row gutter={16}>
                {/* 星图可视化 */}
                <Col span={16}>
                    <Card title="知识点分布星图" size="small">
                        <div style={{ textAlign: 'center' }}>
                            <svg ref={svgRef}></svg>
                        </div>
                        <div style={{ marginTop: 16, textAlign: 'center' }}>
                            <Space>
                                <Tag color="#ff4d4f">高频考点 (≥3题)</Tag>
                                <Tag color="#fa8c16">中频考点 (2题)</Tag>
                                <Tag color="#52c41a">低频考点 (1题)</Tag>
                                <Tag color="#d9d9d9">未涉及</Tag>
                            </Space>
                        </div>
                    </Card>
                </Col>

                {/* 详细信息 */}
                <Col span={8}>
                    <Card title="知识点详情" size="small">
                        {selectedNode ? (
                            <div>
                                <Title level={5}>{selectedNode.name}</Title>
                                <Divider />
                                <Space direction="vertical" style={{ width: '100%' }}>
                                    <div>
                                        <Text strong>所属章节: </Text>
                                        <Text>{selectedNode.chapter?.name || '未分类'}</Text>
                                    </div>
                                    <div>
                                        <Text strong>题目数量: </Text>
                                        <Tag color="blue">{selectedNode.paper_stats.question_count}</Tag>
                                    </div>
                                    <div>
                                        <Text strong>总分值: </Text>
                                        <Tag color="green">{selectedNode.paper_stats.total_score}分</Tag>
                                    </div>
                                    <div>
                                        <Text strong>平均难度: </Text>
                                        <Tag color="orange">{selectedNode.paper_stats.avg_difficulty}</Tag>
                                    </div>
                                    <div>
                                        <Text strong>重要程度: </Text>
                                        <Tag color="red">{selectedNode.importance}</Tag>
                                    </div>
                                    <div>
                                        <Text strong>题型分布: </Text>
                                        <div style={{ marginTop: 4 }}>
                                            {selectedNode.paper_stats.question_types.map((type, index) => (
                                                <Tag key={index} style={{ marginBottom: 4 }}>{type}</Tag>
                                            ))}
                                        </div>
                                    </div>
                                </Space>
                            </div>
                        ) : (
                            <div style={{ textAlign: 'center', padding: '20px' }}>
                                <Text type="secondary">点击星图中的节点查看详细信息</Text>
                            </div>
                        )}
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

export default ExamPaperStarMap;