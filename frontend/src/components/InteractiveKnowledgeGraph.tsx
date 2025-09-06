import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Button,
  Select,
  Space,
  Typography,
  message,
  Spin,
  Modal,
  Drawer,
  Tag,
  Row,
  Col,
  Divider,
  Tooltip,
  Badge,
  List,
  Avatar,
  Dropdown,
  Input,
  Form,
  Slider,
  Switch
} from 'antd';
import {
  ReloadOutlined,
  DownloadOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined,
  InfoCircleOutlined,
  NodeIndexOutlined,
  EyeOutlined,
  BookOutlined,
  EditOutlined,
  DeleteOutlined,
  TagOutlined,
  DragOutlined,
  SaveOutlined,
  CloseOutlined
} from '@ant-design/icons';
import * as d3 from 'd3';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import knowledgeGraphApi from '../api/knowledgeGraph';
import { getSubjects, type Subject } from '../api/subjects';
import KnowledgeGraphEditor from './KnowledgeGraphEditor/KnowledgeGraphEditor';


const { Option } = Select;
const { Title, Text, Paragraph } = Typography;

// 扩展的节点接口，支持AI助理内容
interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  name: string;
  type: 'chapter' | 'knowledge_point' | 'sub_knowledge_point' | 'subject' | 'ai_content';
  level: number;
  difficulty?: number;
  importance?: number;
  mastery_level?: number;
  question_count?: number;
  content?: string;
  tags?: string[];
  created_at?: string;
  subject_name?: string;
  subject_id?: string;
}

interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  type: 'hierarchy' | 'relation' | 'semantic';
  strength: number;
  label?: string;
}

interface KnowledgeGraphData {
  nodes: GraphNode[];
  edges: GraphLink[];
}

interface InteractiveKnowledgeGraphProps {
  subjectId?: string;
  graphType?: string;
  height?: number;
  showControls?: boolean;
  onFilterChange?: (filters: { subjectId: string; graphType: string }) => void;
}

const InteractiveKnowledgeGraph: React.FC<InteractiveKnowledgeGraphProps> = ({
  subjectId,
  graphType = 'ai_assistant_content',
  height = 600,
  showControls = true,
  onFilterChange
}) => {
  // 检查是否为外部控制模式
  const isExternallyControlled = subjectId !== undefined || (graphType !== 'ai_assistant_content' && graphType !== undefined);
  const [graphData, setGraphData] = useState<KnowledgeGraphData | null>(null);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [nodeDetailVisible, setNodeDetailVisible] = useState(false);
  const [editingNode, setEditingNode] = useState<GraphNode | null>(null);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [contextMenuVisible, setContextMenuVisible] = useState(false);
  const [contextMenuPosition, setContextMenuPosition] = useState({ x: 0, y: 0 });
  const [contextMenuNode, setContextMenuNode] = useState<GraphNode | null>(null);
  const [tagModalVisible, setTagModalVisible] = useState(false);
  const [managingTagsNode, setManagingTagsNode] = useState<GraphNode | null>(null);
  const [newTag, setNewTag] = useState('');
  const [moveModalVisible, setMoveModalVisible] = useState(false);
  const [movingNode, setMovingNode] = useState<GraphNode | null>(null);
  const [targetSubjectId, setTargetSubjectId] = useState<string>('');
  const [fullscreen, setFullscreen] = useState(false);
  const [currentSubjectId, setCurrentSubjectId] = useState(subjectId || 'all');
  const [currentGraphType, setCurrentGraphType] = useState(graphType);
  const [layoutType, setLayoutType] = useState<'force' | 'hierarchical' | 'circular'>('force');
  const [selectedNodes, setSelectedNodes] = useState<Set<string>>(new Set());
  const [multiSelectMode, setMultiSelectMode] = useState(false);
  const [mergeModalVisible, setMergeModalVisible] = useState(false);
  const [mergeTitle, setMergeTitle] = useState('');
  const [mergeDescription, setMergeDescription] = useState('');
  
  const svgRef = useRef<SVGSVGElement>(null);
  const simulationRef = useRef<d3.Simulation<GraphNode, GraphLink> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchSubjects();
  }, []);

  // 同步外部props到内部状态
  useEffect(() => {
    if (subjectId && subjectId !== currentSubjectId) {
      setCurrentSubjectId(subjectId);
    }
  }, [subjectId]);

  useEffect(() => {
    if (graphType && graphType !== currentGraphType) {
      setCurrentGraphType(graphType);
    }
  }, [graphType]);

  useEffect(() => {
    // 确保学科数据加载完成后再获取知识图谱数据
    if (subjects.length > 0) {
      // 使用setTimeout实现懒加载，避免竞态条件
      const timer = setTimeout(() => {
        fetchKnowledgeGraphData();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [currentSubjectId, currentGraphType, subjects]);

  // 处理学科筛选变化
  const handleSubjectChange = (value: string) => {
    setCurrentSubjectId(value);
    if (onFilterChange) {
      onFilterChange({ subjectId: value, graphType: currentGraphType });
    }
  };

  // 处理图谱类型变化
  const handleGraphTypeChange = (value: string) => {
    setCurrentGraphType(value);
    if (onFilterChange) {
      onFilterChange({ subjectId: currentSubjectId, graphType: value });
    }
  };

  useEffect(() => {
    if (graphData && svgRef.current) {
      renderGraph();
    }
    return () => {
      if (simulationRef.current) {
        simulationRef.current.stop();
      }
    };
  }, [graphData, layoutType, fullscreen]);

  const fetchSubjects = async () => {
    try {
      const subjects = await getSubjects();
      setSubjects(subjects);
      // 学科数据加载完成后，立即获取知识图谱数据
      if (subjects.length > 0) {
        fetchKnowledgeGraphData();
      }
    } catch (error) {
      console.error('Failed to fetch subjects:', error);
    }
  };

  const fetchKnowledgeGraphData = async () => {
    setLoading(true);
    try {
      let data;
      console.log('🔄 fetchKnowledgeGraphData - Starting fetch with params:', { currentSubjectId, currentGraphType });
      
      if (currentGraphType === 'all') {
        // 获取所有类型的知识图谱数据
        const params: any = {};
        if (currentSubjectId && currentSubjectId !== 'all') {
          params.subjectId = currentSubjectId;
        }
        
        console.log('🔄 fetchKnowledgeGraphData - Fetching all types with params:', params);
        
        // 并行获取所有类型的数据
        const [aiResponse, examResponse, fullResponse, masteryResponse] = await Promise.all([
          knowledgeGraphApi.getKnowledgeGraphs({ ...params, graphType: 'ai_assistant_content' }),
          knowledgeGraphApi.getKnowledgeGraphs({ ...params, graphType: 'exam_scope' }),
          knowledgeGraphApi.getKnowledgeGraphs({ ...params, graphType: 'full_knowledge' }),
          knowledgeGraphApi.getKnowledgeGraphs({ ...params, graphType: 'mastery_level' })
        ]);
        
        console.log('🔄 fetchKnowledgeGraphData - Raw API responses:', {
          aiResponse,
          examResponse,
          fullResponse,
          masteryResponse
        });
        
        // 合并所有数据
        const aiData = transformAIContentToGraph(aiResponse);
        const examData = transformTraditionalGraph(examResponse, 'exam_scope');
        const fullData = transformTraditionalGraph(fullResponse, 'full_knowledge');
        const masteryData = transformTraditionalGraph(masteryResponse, 'mastery_level');
        
        console.log('🔄 fetchKnowledgeGraphData - Transformed data:', {
          aiData,
          examData,
          fullData,
          masteryData
        });
        
        data = {
          nodes: [...aiData.nodes, ...examData.nodes, ...fullData.nodes, ...masteryData.nodes],
          edges: [...aiData.edges, ...examData.edges, ...fullData.edges, ...masteryData.edges]
        };
      } else if (currentGraphType === 'ai_assistant_content') {
        // 获取AI助理生成的知识图谱内容
        const params: any = { graphType: 'ai_assistant_content' };
        if (currentSubjectId && currentSubjectId !== 'all') {
          params.subjectId = currentSubjectId;
        }
        console.log('🔄 fetchKnowledgeGraphData - Fetching AI content with params:', params);
        
        // 强制使用最新数据，避免缓存问题
        const timestamp = new Date().getTime();
        const response = await knowledgeGraphApi.getKnowledgeGraphs({
          ...params,
          _t: timestamp // 添加时间戳参数避免缓存
        });
        
        console.log('🔄 fetchKnowledgeGraphData - AI content raw response:', response);
        data = transformAIContentToGraph(response);
        console.log('🔄 fetchKnowledgeGraphData - AI content transformed data:', data);
      } else {
        // 获取传统知识图谱
        const params: any = { graphType: currentGraphType };
        if (currentSubjectId && currentSubjectId !== 'all') {
          params.subjectId = currentSubjectId;
        }
        console.log('🔄 fetchKnowledgeGraphData - Fetching traditional graph with params:', params);
        
        // 强制使用最新数据，避免缓存问题
        const timestamp = new Date().getTime();
        const response = await knowledgeGraphApi.getKnowledgeGraphs({
          ...params,
          _t: timestamp // 添加时间戳参数避免缓存
        });
        
        console.log('🔄 fetchKnowledgeGraphData - Traditional graph raw response:', response);
        data = transformTraditionalGraph(response, currentGraphType);
        console.log('🔄 fetchKnowledgeGraphData - Traditional graph transformed data:', data);
      }
      
      console.log('🔄 fetchKnowledgeGraphData - Final data to set:', data);
      setGraphData(data);
    } catch (error) {
      console.error('Failed to fetch knowledge graph:', error);
      message.error('获取知识图谱数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 将AI助理内容转换为图谱数据结构
  const transformAIContentToGraph = (aiContents: any[]): KnowledgeGraphData => {
    const nodes: GraphNode[] = [];
    const edges: GraphLink[] = [];
    const subjectNodes = new Map<string, GraphNode>();
    
    // 如果没有内容，返回空图谱
    if (!aiContents || aiContents.length === 0) {
      return { nodes, edges };
    }

    // 创建学科节点
    const subjectGroups = new Map<string, any[]>();
    aiContents.forEach(content => {
      const subjectId = content.subject_id || 'unknown';
      if (!subjectGroups.has(subjectId)) {
        subjectGroups.set(subjectId, []);
      }
      const group = subjectGroups.get(subjectId);
      if (group) {
        group.push(content);
      }
    });

    // 为每个学科创建中心节点
    subjectGroups.forEach((contents, subjectId) => {
      // 确保subjects数组已加载，否则延迟处理
      if (subjects.length === 0) {
        console.log('学科数据尚未加载完成，使用内容中的学科信息');
      }
      
      // 首先尝试从subjects数组中查找，如果找不到则尝试从内容中获取学科名称
      const subject = subjects.find(s => s.id === subjectId);
      let subjectName = subject?.name;
      
      // 如果subjects中没有找到，尝试从内容中获取学科名称
      if (!subjectName) {
        // 尝试从内容中找到学科名称
        const contentWithSubjectName = contents.find(c => c.subject_name);
        subjectName = contentWithSubjectName?.subject_name || '未知学科';
      }
      
      const subjectNode: GraphNode = {
        id: `subject_${subjectId}`,
        name: subjectName || '未知学科',
        type: 'subject',
        level: 0,
        content: `学科：${subjectName || '未知学科'}\n包含 ${contents.length} 个知识图谱`,
        question_count: contents.length
      };
      nodes.push(subjectNode);
      subjectNodes.set(subjectId, subjectNode);

      // 为每个AI内容创建节点
      contents.forEach((content, index) => {
        // 从多个来源提取标签（统一标签体系）
        let nodeTags: string[] = [];
        
        // 1. 首先检查content.tags（后端to_dict方法提取的标签）
        if (content.tags && Array.isArray(content.tags)) {
          nodeTags = [...content.tags];
          console.log('Using content.tags:', nodeTags);
        }
        // 2. 如果没有找到标签，尝试从nodes数组中提取
        else if (content.nodes && Array.isArray(content.nodes) && content.nodes.length > 0) {
          // 调试日志：查看节点数据结构
          console.log('Content ID:', content.id, 'Nodes:', content.nodes.map((n: any) => ({ id: n.id, tags: n.tags })));
          
          // AI内容类型：查找对应的内容节点
          const contentNodeData = content.nodes.find((node: any) => 
            node.id === `content_${content.id}` || node.id === content.id
          );
          if (contentNodeData && contentNodeData.tags) {
            nodeTags = contentNodeData.tags;
            console.log('Found matching node tags:', nodeTags);
          } else if (content.nodes[0] && content.nodes[0].tags) {
            // 如果找不到特定节点，使用第一个节点的标签
            nodeTags = content.nodes[0].tags;
            console.log('Using first node tags:', nodeTags);
          } else {
            console.log('No tags found in nodes array for content:', content.id);
          }
        }
        
        const contentNode: GraphNode = {
          id: `content_${content.id}`,
          name: content.title || `知识图谱 ${index + 1}`,
          type: 'ai_content',
          level: 1,
          content: content.content,
          tags: nodeTags, // 使用从nodes数组中提取的标签
          created_at: content.created_at,
          subject_name: subject?.name,
          subject_id: subjectId
        };
        nodes.push(contentNode);

        // 创建学科到内容的连接
        edges.push({
          source: subjectNode.id,
          target: contentNode.id,
          type: 'hierarchy',
          strength: 1,
          label: '包含'
        });
      });
    });

    // 基于标签创建语义连接
    const tagGroups = new Map<string, GraphNode[]>();
    nodes.filter(n => n.type === 'ai_content' && n.tags).forEach(node => {
      if (node.tags && Array.isArray(node.tags)) {
        node.tags.forEach(tag => {
          if (!tagGroups.has(tag)) {
            tagGroups.set(tag, []);
          }
          const group = tagGroups.get(tag);
          if (group) {
            group.push(node);
          }
        });
      }
    });

    // 为相同标签的节点创建连接
    tagGroups.forEach((tagNodes, tag) => {
      if (tagNodes.length > 1) {
        for (let i = 0; i < tagNodes.length; i++) {
          for (let j = i + 1; j < tagNodes.length; j++) {
            edges.push({
              source: tagNodes[i].id,
              target: tagNodes[j].id,
              type: 'semantic',
              strength: 0.5,
              label: tag
            });
          }
        }
      }
    });

    return { nodes, edges };
  };

  // 转换传统知识图谱数据
  const transformTraditionalGraph = (data: any[], prefix?: string): KnowledgeGraphData => {
    const nodes: GraphNode[] = [];
    const edges: GraphLink[] = [];

    data.forEach(graph => {
      // 处理图谱中的节点
      if (graph.nodes && Array.isArray(graph.nodes)) {
        graph.nodes.forEach((node: any) => {
          const graphNode: GraphNode = {
            id: prefix ? `${prefix}_${node.id}` : (node.id || `node_${nodes.length}`),
            name: node.name || node.label || '未命名节点',
            type: node.type || 'knowledge_point',
            level: node.level || 1,
            content: node.content || node.description || '',
            tags: node.tags || [],
            difficulty: node.difficulty,
            importance: node.importance,
            mastery_level: node.mastery_level,
            question_count: node.question_count,
            subject_name: graph.subject_name
          };
          nodes.push(graphNode);
        });
      }

      // 处理图谱中的边
      if (graph.edges && Array.isArray(graph.edges)) {
        graph.edges.forEach((edge: any) => {
          const graphEdge: GraphLink = {
            source: prefix ? `${prefix}_${edge.source || edge.from}` : (edge.source || edge.from),
            target: prefix ? `${prefix}_${edge.target || edge.to}` : (edge.target || edge.to),
            type: edge.type || 'relation',
            strength: edge.strength || edge.weight || 1,
            label: edge.label || edge.name
          };
          edges.push(graphEdge);
        });
      }
    });

    return { nodes, edges };
  };

  const getNodeColor = (node: GraphNode): string => {
    const colors = {
      subject: '#722ed1',
      chapter: '#1890ff', 
      knowledge_point: '#52c41a',
      sub_knowledge_point: '#faad14',
      ai_content: '#13c2c2'
    };
    return colors[node.type] || '#d9d9d9';
  };

  const getNodeSize = (node: GraphNode): number => {
    const baseSizes = {
      subject: 20,
      chapter: 15,
      knowledge_point: 12,
      sub_knowledge_point: 10,
      ai_content: 14
    };
    const baseSize = baseSizes[node.type] || 10;
    const contentFactor = node.content ? Math.min(node.content.length / 100, 2) : 0;
    const tagFactor = node.tags ? node.tags.length * 0.5 : 0;
    return baseSize + contentFactor + tagFactor;
  };

  const renderGraph = (): void => {
    if (!graphData || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const containerWidth = fullscreen ? window.innerWidth - 40 : 800;
    const containerHeight = fullscreen ? window.innerHeight - 200 : height;
    const margin = { top: 20, right: 20, bottom: 20, left: 20 };
    const graphWidth = containerWidth - margin.left - margin.right;
    const graphHeight = containerHeight - margin.top - margin.bottom;

    svg.attr('width', containerWidth).attr('height', containerHeight);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // 创建缩放和拖拽行为
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 5])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // 创建力导向图模拟
    let simulation: d3.Simulation<GraphNode, GraphLink>;
    
    if (layoutType === 'force') {
      simulation = d3.forceSimulation<GraphNode>(graphData.nodes)
        .force('link', d3.forceLink<GraphNode, GraphLink>(graphData.edges)
          .id(d => d.id)
          .distance(d => {
            if (d.type === 'hierarchy') return 80;
            if (d.type === 'semantic') return 120;
            return 100;
          })
          .strength(d => d.strength)
        )
        .force('charge', d3.forceManyBody().strength(-400))
        .force('center', d3.forceCenter(graphWidth / 2, graphHeight / 2))
        .force('collision', d3.forceCollide().radius(d => getNodeSize(d as GraphNode) + 10));
    } else if (layoutType === 'hierarchical') {
      // 层次布局 - 处理多根节点问题
      try {
        // 找出所有根节点（没有父节点的节点）
        const rootNodes = graphData.nodes.filter(node => {
          const hasParent = graphData.edges.some(e => 
            (e.target as GraphNode).id === node.id && e.type === 'hierarchy'
          );
          return !hasParent;
        });

        if (rootNodes.length === 0) {
          // 如果没有根节点，使用力导向布局作为后备
          console.warn('层次布局：未找到根节点，使用力导向布局');
          simulation = d3.forceSimulation<GraphNode>(graphData.nodes)
            .force('link', d3.forceLink<GraphNode, GraphLink>(graphData.edges)
              .id(d => d.id)
              .distance(100)
            )
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(graphWidth / 2, graphHeight / 2));
        } else if (rootNodes.length === 1) {
          // 单根节点，使用标准层次布局
          const hierarchy = d3.stratify<GraphNode>()
            .id(d => d.id)
            .parentId(d => {
              const parentEdge = graphData.edges.find(e => 
                (e.target as GraphNode).id === d.id && e.type === 'hierarchy'
              );
              return parentEdge ? (parentEdge.source as GraphNode).id : null;
            })(graphData.nodes);

          const tree = d3.tree<GraphNode>().size([graphWidth, graphHeight]);
          const root = tree(hierarchy);
          
          root.descendants().forEach(d => {
            d.data.x = d.x;
            d.data.y = d.y;
            d.data.fx = d.x;
            d.data.fy = d.y;
          });

          simulation = d3.forceSimulation<GraphNode>(graphData.nodes)
            .force('link', d3.forceLink<GraphNode, GraphLink>(graphData.edges)
              .id(d => d.id)
              .distance(50)
            )
            .alphaDecay(0.1);
        } else {
           // 多根节点，使用改进的多根层次布局
           console.log(`层次布局：检测到${rootNodes.length}个根节点，使用多根节点布局`);
           
           // 按层级分组节点
           const levels = new Map<number, GraphNode[]>();
           graphData.nodes.forEach(node => {
             const level = node.level || 0;
             if (!levels.has(level)) {
               levels.set(level, []);
             }
             levels.get(level)!.push(node);
           });

           // 计算布局参数
           const maxLevel = Math.max(...Array.from(levels.keys()));
           const minLevel = Math.min(...Array.from(levels.keys()));
           const levelCount = maxLevel - minLevel + 1;
           const levelHeight = Math.max(120, graphHeight / Math.max(levelCount, 3)); // 最小层高120px
           const startY = 60; // 顶部边距

           // 为每层分配坐标，按层级从上到下排列
           Array.from(levels.keys()).sort((a, b) => a - b).forEach((level, levelIndex) => {
             const nodes = levels.get(level)!;
             const y = startY + levelIndex * levelHeight;
             
             // 计算节点间距，确保不会太拥挤
             const minNodeSpacing = 100; // 最小节点间距
             const totalRequiredWidth = (nodes.length - 1) * minNodeSpacing;
             const availableWidth = graphWidth - 120; // 左右各留60px边距
             const nodeSpacing = Math.max(minNodeSpacing, availableWidth / Math.max(nodes.length - 1, 1));
             
             // 计算起始X坐标，使节点居中
             const totalWidth = (nodes.length - 1) * nodeSpacing;
             const startX = (graphWidth - totalWidth) / 2;
             
             nodes.forEach((node, index) => {
               node.x = startX + index * nodeSpacing;
               node.y = y;
               // 在多根节点布局中，我们不固定位置，让力导向算法进行微调
               // node.fx = node.x;
               // node.fy = node.y;
             });
           });

           // 使用温和的力导向算法进行微调
           simulation = d3.forceSimulation<GraphNode>(graphData.nodes)
             .force('link', d3.forceLink<GraphNode, GraphLink>(graphData.edges)
               .id(d => d.id)
               .distance(d => {
                 // 根据连接类型调整距离
                 if (d.type === 'hierarchy') return 100;
                 return 120;
               })
               .strength(0.3) // 降低连接强度，避免过度拉扯
             )
             .force('charge', d3.forceManyBody().strength(-200)) // 适度的排斥力
             .force('collision', d3.forceCollide().radius(d => getNodeSize(d as GraphNode) + 25))
             .force('y', d3.forceY().y(d => d.y || 0).strength(0.8)) // 保持Y轴层次结构
             .force('x', d3.forceX().x(d => d.x || 0).strength(0.1)) // 轻微的X轴约束
             .alphaDecay(0.02) // 更慢的衰减，让布局有更多时间稳定
             .velocityDecay(0.4); // 增加阻尼，减少震荡
         }
      } catch (error) {
        console.error('层次布局失败，使用力导向布局作为后备:', error);
        // 后备方案：使用力导向布局
        simulation = d3.forceSimulation<GraphNode>(graphData.nodes)
          .force('link', d3.forceLink<GraphNode, GraphLink>(graphData.edges)
            .id(d => d.id)
            .distance(100)
          )
          .force('charge', d3.forceManyBody().strength(-300))
          .force('center', d3.forceCenter(graphWidth / 2, graphHeight / 2))
          .force('collision', d3.forceCollide().radius(d => getNodeSize(d as GraphNode) + 10));
      }
    } else {
      // 圆形布局
      const radius = Math.min(graphWidth, graphHeight) / 2 - 50;
      graphData.nodes.forEach((node, i) => {
        const angle = (i / graphData.nodes.length) * 2 * Math.PI;
        node.x = graphWidth / 2 + radius * Math.cos(angle);
        node.y = graphHeight / 2 + radius * Math.sin(angle);
        node.fx = node.x;
        node.fy = node.y;
      });

      simulation = d3.forceSimulation<GraphNode>(graphData.nodes)
        .force('link', d3.forceLink<GraphNode, GraphLink>(graphData.edges)
          .id(d => d.id)
          .distance(50)
        )
        .alphaDecay(0.1);
    }

    simulationRef.current = simulation;

    // 创建连线
    const links = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(graphData.edges)
      .enter().append('line')
      .attr('stroke', d => {
        if (d.type === 'hierarchy') return '#999';
        if (d.type === 'semantic') return '#52c41a';
        return '#d9d9d9';
      })
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', d => {
        if (d.type === 'hierarchy') return 2;
        if (d.type === 'semantic') return 1;
        return 1;
      })
      .attr('stroke-dasharray', d => d.type === 'semantic' ? '5,5' : 'none');

    // 创建连线标签
    const linkLabels = g.append('g')
      .attr('class', 'link-labels')
      .selectAll('text')
      .data(graphData.edges.filter(d => d.label))
      .enter().append('text')
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('fill', '#666')
      .text(d => d.label || '');

    // 创建节点组
    const nodeGroups = g.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(graphData.nodes)
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
          if (layoutType === 'force') {
            d.fx = null;
            d.fy = null;
          }
        })
      );

    // 添加节点圆圈
    nodeGroups.append('circle')
      .attr('r', d => getNodeSize(d))
      .attr('fill', d => getNodeColor(d))
      .attr('stroke', d => selectedNodes.has(d.id) ? '#1890ff' : '#fff')
      .attr('stroke-width', d => selectedNodes.has(d.id) ? 4 : 2)
      .on('click', (event, d) => {
        if (multiSelectMode) {
          handleNodeSelect(d.id);
        } else {
          setSelectedNode(d);
          setNodeDetailVisible(true);
        }
      })
      .on('contextmenu', (event, d) => {
        event.preventDefault();
        setContextMenuNode(d);
        setContextMenuPosition({ x: event.pageX, y: event.pageY });
        setContextMenuVisible(true);
      })
      .on('mouseover', function(event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', getNodeSize(d) * 1.2)
          .attr('stroke-width', 3);
        
        // 显示tooltip
        const tooltip = d3.select('body').append('div')
          .attr('class', 'graph-tooltip')
          .style('position', 'absolute')
          .style('background', 'rgba(0, 0, 0, 0.8)')
          .style('color', 'white')
          .style('padding', '8px')
          .style('border-radius', '4px')
          .style('font-size', '12px')
          .style('pointer-events', 'none')
          .style('z-index', 1000)
          .html(`
            <div><strong>${d.name}</strong></div>
            <div>类型: ${d.type}</div>
            ${d.tags ? `<div>标签: ${d.tags.join(', ')}</div>` : ''}
            <div>点击查看详情</div>
          `)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 10) + 'px');
      })
      .on('mouseout', function(event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', getNodeSize(d))
          .attr('stroke-width', 2);
        
        d3.selectAll('.graph-tooltip').remove();
      });

    // 添加节点标签
    nodeGroups.append('text')
      .text(d => d.name.length > 10 ? d.name.substring(0, 10) + '...' : d.name)
      .attr('text-anchor', 'middle')
      .attr('dy', d => getNodeSize(d) + 15)
      .attr('font-size', '11px')
      .attr('fill', '#333')
      .style('pointer-events', 'none');

    // 添加标签指示器
    nodeGroups.filter(d => Boolean(d.tags && d.tags.length > 0))
      .append('circle')
      .attr('r', 4)
      .attr('cx', d => getNodeSize(d) - 4)
      .attr('cy', d => -getNodeSize(d) + 4)
      .attr('fill', '#fa8c16')
      .attr('stroke', '#fff')
      .attr('stroke-width', 1);

    // 更新位置
    simulation.on('tick', () => {
      links
        .attr('x1', d => (d.source as GraphNode).x || 0)
        .attr('y1', d => (d.source as GraphNode).y || 0)
        .attr('x2', d => (d.target as GraphNode).x || 0)
        .attr('y2', d => (d.target as GraphNode).y || 0);

      linkLabels
        .attr('x', d => ((d.source as GraphNode).x! + (d.target as GraphNode).x!) / 2)
        .attr('y', d => ((d.source as GraphNode).y! + (d.target as GraphNode).y!) / 2);

      nodeGroups
        .attr('transform', d => `translate(${d.x || 0},${d.y || 0})`);
    });
  };

  // 处理节点编辑
  const handleEditNode = (node: GraphNode): void => {
    setEditingNode(node);
    setEditModalVisible(true);
    setContextMenuVisible(false);
  };

  // 编辑成功回调
  const handleEditSuccess = (): void => {
    setEditModalVisible(false);
    setEditingNode(null);
    // 强制延迟重新获取数据以确保标签更新
    console.log('编辑节点成功，准备刷新数据');
    setTimeout(() => {
      fetchKnowledgeGraphData();
    }, 500);
  };

  // 关闭编辑器
  const handleEditClose = (): void => {
    setEditModalVisible(false);
    setEditingNode(null);
  };



  // 处理节点移动
  const handleMoveNode = (node: GraphNode): void => {
    setMovingNode(node);
    setTargetSubjectId('');
    setMoveModalVisible(true);
    setContextMenuVisible(false);
  };

  // 执行节点移动
  const handleExecuteMove = async (): Promise<void> => {
    try {
      if (movingNode && targetSubjectId && movingNode.type === 'ai_content') {
        const actualId = movingNode.id.startsWith('content_') ? movingNode.id.replace('content_', '') : movingNode.id;
        await knowledgeGraphApi.updateKnowledgeGraph(actualId, {
          subject_id: targetSubjectId
        });
        message.success('节点移动成功');
        setMoveModalVisible(false);
        setMovingNode(null);
        setTargetSubjectId('');
        fetchKnowledgeGraphData();
      }
    } catch (error) {
      console.error('移动节点失败:', error);
      message.error('移动节点失败');
    }
  };

   // 处理节点删除
   const handleDeleteNode = (node: GraphNode): void => {
     Modal.confirm({
       title: '确认删除',
       content: `确定要删除节点 "${node.name}" 吗？此操作不可撤销。`,
       okText: '删除',
       okType: 'danger',
       cancelText: '取消',
       onOk: async (): Promise<void> => {
         try {
           const actualId = node.id.startsWith('content_') ? node.id.replace('content_', '') : node.id;
           await knowledgeGraphApi.deleteKnowledgeGraph(actualId);
           message.success('节点删除成功');
           fetchKnowledgeGraphData();
         } catch (error) {
           console.error('删除节点失败:', error);
           message.error('删除节点失败');
         }
       }
     });
     setContextMenuVisible(false);
   };

  // 处理标签管理
  const handleManageTags = (node: GraphNode): void => {
    setManagingTagsNode(node);
    setTagModalVisible(true);
    setContextMenuVisible(false);
  };

  // 添加标签
  const handleAddTag = (): void => {
    if (!newTag.trim() || !managingTagsNode) return;
    
    const updatedTags = [...(managingTagsNode.tags || []), newTag.trim()];
    const updatedNode = { ...managingTagsNode, tags: updatedTags };
    setManagingTagsNode(updatedNode);
    setNewTag('');
  };

  // 删除标签
  const handleRemoveTag = (tagToRemove: string): void => {
    if (!managingTagsNode) return;
    
    const updatedTags = (managingTagsNode.tags || []).filter(tag => tag !== tagToRemove);
    const updatedNode = { ...managingTagsNode, tags: updatedTags };
    setManagingTagsNode(updatedNode);
  };

  // 保存标签更改
  const handleSaveTagChanges = async (): Promise<void> => {
    try {
      if (managingTagsNode) {
        const actualId = managingTagsNode.id.startsWith('content_') ? managingTagsNode.id.replace('content_', '') : managingTagsNode.id;
        console.log('保存标签更改:', actualId, managingTagsNode.tags);
        await knowledgeGraphApi.updateKnowledgeGraph(actualId, {
          tags: managingTagsNode.tags || []
        });
        message.success('标签更新成功');
        setTagModalVisible(false);
        setManagingTagsNode(null);
        // 强制延迟获取数据，确保后端处理完成
        setTimeout(() => {
          fetchKnowledgeGraphData();
        }, 500);
      }
    } catch (error) {
      console.error('更新标签失败:', error);
      message.error('更新标签失败');
    }
  };

  // 切换多选模式
  const toggleMultiSelectMode = (): void => {
    setMultiSelectMode(!multiSelectMode);
    setSelectedNodes(new Set());
  };

  // 处理节点选择
  const handleNodeSelect = (nodeId: string): void => {
    if (!multiSelectMode) return;
    
    const newSelectedNodes = new Set(selectedNodes);
    if (newSelectedNodes.has(nodeId)) {
      newSelectedNodes.delete(nodeId);
    } else {
      newSelectedNodes.add(nodeId);
    }
    setSelectedNodes(newSelectedNodes);
  };

  // 开始合并节点
  const handleStartMerge = (): void => {
    if (selectedNodes.size < 2) {
      message.warning('请至少选择两个节点进行合并');
      return;
    }
    
    const selectedNodesList = Array.from(selectedNodes)
      .map(id => graphData?.nodes.find(n => n.id === id))
      .filter(Boolean) as GraphNode[];
    
    // 检查是否都是AI内容节点
    const hasNonAIContent = selectedNodesList.some(node => node.type !== 'ai_content');
    if (hasNonAIContent) {
      message.warning('只能合并AI助理内容节点');
      return;
    }
    
    // 生成默认合并标题和描述
    const titles = selectedNodesList.map(node => node.name);
    const contents = selectedNodesList.map(node => node.content || '').filter(Boolean);
    
    setMergeTitle(`合并节点：${titles.join('、')}`);
    setMergeDescription(contents.join('\n\n---\n\n'));
    setMergeModalVisible(true);
  };

  // 执行节点合并
  const handleExecuteMerge = async (): Promise<void> => {
    if (!mergeTitle.trim()) {
      message.error('请输入合并后的标题');
      return;
    }
    
    try {
      const selectedNodesList = Array.from(selectedNodes)
        .map(id => graphData?.nodes.find(n => n.id === id))
        .filter(Boolean) as GraphNode[];
      
      // 收集所有标签
      const allTags = new Set<string>();
      selectedNodesList.forEach(node => {
        node.tags?.forEach(tag => allTags.add(tag));
      });
      
      // 使用第一个节点的学科信息
      const firstNode = selectedNodesList[0];
      const subjectInfo = subjects.find(s => s.name === firstNode.subject_name);
      
      // 创建合并后的新节点
      const mergeData = {
        title: mergeTitle,
        subject_id: subjectInfo?.id || '',
        content: mergeDescription,
        description: mergeDescription,
        tags: Array.from(allTags)
      };
      
      await knowledgeGraphApi.generateKnowledgeGraph(mergeData);
      
      // 删除原有节点
      for (const node of selectedNodesList) {
        await knowledgeGraphApi.deleteKnowledgeGraph(node.id);
      }
      
      message.success('节点合并成功');
      setMergeModalVisible(false);
      setMergeTitle('');
      setMergeDescription('');
      setSelectedNodes(new Set());
      setMultiSelectMode(false);
      fetchKnowledgeGraphData();
    } catch (error) {
      console.error('合并节点失败:', error);
      message.error('合并节点失败');
    }
  };





  // 右键菜单项
  const getContextMenuItems = (node: GraphNode) => {
    const items: any[] = [
      {
        key: 'view',
        icon: <EyeOutlined />,
        label: '查看详情',
        onClick: () => {
          setSelectedNode(node);
          setNodeDetailVisible(true);
          setContextMenuVisible(false);
        }
      }
    ];

    if (node.type === 'ai_content') {
      items.push(
        {
          key: 'edit',
          icon: <EditOutlined />,
          label: '编辑内容',
          onClick: () => handleEditNode(node)
        },
        {
          key: 'tags',
          icon: <TagOutlined />,
          label: '管理标签',
          onClick: () => handleManageTags(node)
        },
        {
          key: 'move',
          icon: <DragOutlined />,
          label: '移动节点',
          onClick: () => handleMoveNode(node)
        },
        {
          key: 'divider',
          type: 'divider'
        },
        {
          key: 'delete',
          icon: <DeleteOutlined />,
          label: '删除节点',
          danger: true,
          onClick: () => handleDeleteNode(node)
        }
      );
    }

    return { items };
  };

  const handleDownload = () => {
    if (!svgRef.current) return;

    const svgElement = svgRef.current;
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svgElement);
    const blob = new Blob([svgString], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `knowledge-graph-${currentGraphType}-${Date.now()}.svg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const renderNodeDetail = () => {
    if (!selectedNode) return null;

    return (
      <Drawer
        title={
          <Space>
            <Avatar 
              style={{ backgroundColor: getNodeColor(selectedNode) }}
              icon={<NodeIndexOutlined />}
            />
            <div>
              <div>{selectedNode.name}</div>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {selectedNode.type === 'subject' ? '学科' :
                 selectedNode.type === 'chapter' ? '章节' :
                 selectedNode.type === 'knowledge_point' ? '知识点' :
                 selectedNode.type === 'sub_knowledge_point' ? '子知识点' :
                 'AI助理内容'}
              </Text>
            </div>
          </Space>
        }
        placement="right"
        width={600}
        open={Boolean(nodeDetailVisible)}
        onClose={() => setNodeDetailVisible(false)}
      >
        <div>
          {selectedNode.tags && selectedNode.tags.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <Text strong>标签：</Text>
              <div style={{ marginTop: 8 }}>
                {selectedNode.tags.map(tag => (
                  <Tag key={tag} color="blue">{tag}</Tag>
                ))}
              </div>
            </div>
          )}

          {selectedNode.subject_name && (
            <div style={{ marginBottom: 16 }}>
              <Text strong>所属学科：</Text>
              <Tag color="purple">{selectedNode.subject_name}</Tag>
            </div>
          )}

          {selectedNode.created_at && (
            <div style={{ marginBottom: 16 }}>
              <Text strong>创建时间：</Text>
              <Text>{new Date(selectedNode.created_at).toLocaleString()}</Text>
            </div>
          )}

          {selectedNode.content && (
            <div>
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
                  {selectedNode.content}
                </ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      </Drawer>
    );
  };

  const renderControls = () => {
    if (!showControls) return null;

    return (
      <Space wrap style={{ marginBottom: 16 }}>
        {/* 只有在没有外部筛选器控制时才显示学科和图谱类型选择器 */}
        {!isExternallyControlled && (
          <>
            <Select
              value={currentSubjectId}
              onChange={handleSubjectChange}
              style={{ width: 150 }}
              placeholder="选择学科"
            >
              <Option value="all">全部学科</Option>
              {subjects.map(subject => (
                <Option key={subject.id} value={subject.id}>
                  {subject.name}
                </Option>
              ))}
            </Select>

            <Select
              value={currentGraphType}
              onChange={handleGraphTypeChange}
              style={{ width: 150 }}
            >
              <Option value="all">全部类型</Option>
              <Option value="ai_assistant_content">AI助理内容</Option>
              <Option value="exam_scope">考试范围</Option>
              <Option value="full_knowledge">完整知识</Option>
              <Option value="mastery_level">掌握情况</Option>
            </Select>
          </>
        )}

        <Select
          value={layoutType}
          onChange={setLayoutType}
          style={{ width: 120 }}
        >
          <Option value="force">力导向</Option>
          <Option value="hierarchical">层次布局</Option>
          <Option value="circular">圆形布局</Option>
        </Select>

        <Button
          icon={<ReloadOutlined />}
          onClick={fetchKnowledgeGraphData}
          loading={loading}
        >
          刷新
        </Button>

        <Button
          icon={<DownloadOutlined />}
          onClick={handleDownload}
          disabled={!graphData}
        >
          导出
        </Button>

        <Button
          icon={fullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
          onClick={() => setFullscreen(!fullscreen)}
        >
          {fullscreen ? '退出全屏' : '全屏'}
        </Button>

        <Divider type="vertical" />

        <Tooltip title={multiSelectMode ? '退出多选模式' : '进入多选模式，可选择多个AI助理内容节点进行合并'}>
          <Button
            type={multiSelectMode ? 'primary' : 'default'}
            onClick={toggleMultiSelectMode}
          >
            {multiSelectMode ? '退出多选' : '多选模式'}
          </Button>
        </Tooltip>

        {multiSelectMode && (
          <>
            <Badge count={selectedNodes.size} showZero>
              <Tooltip title={selectedNodes.size < 2 ? '请至少选择2个AI助理内容节点' : `合并选中的${selectedNodes.size}个节点`}>
                <Button
                  type="primary"
                  onClick={handleStartMerge}
                  disabled={selectedNodes.size < 2}
                >
                  合并节点
                </Button>
              </Tooltip>
            </Badge>
            
            <Button
              onClick={() => setSelectedNodes(new Set())}
              disabled={selectedNodes.size === 0}
            >
              清空选择
            </Button>
            
            <Text type="secondary" style={{ fontSize: '12px', marginLeft: 8 }}>
              提示：点击AI助理内容节点（青色圆圈）进行选择，选中后可合并为新节点
            </Text>
          </>
        )}
      </Space>
    );
  };

  const renderLegend = () => {
    const legendItems = [
      { color: '#722ed1', label: '学科', type: 'subject' },
      { color: '#1890ff', label: '章节', type: 'chapter' },
      { color: '#52c41a', label: '知识点', type: 'knowledge_point' },
      { color: '#faad14', label: '子知识点', type: 'sub_knowledge_point' },
      { color: '#13c2c2', label: 'AI助理内容', type: 'ai_content' }
    ];

    const connectionTypes = [
      { color: '#999', label: '层次关系', style: 'solid' },
      { color: '#52c41a', label: '语义关系', style: 'dashed' }
    ];

    return (
      <Card size="small" title="图例" style={{ marginTop: 16 }}>
        <Row gutter={[16, 8]}>
          <Col span={12}>
            <Text strong>节点类型：</Text>
            <div style={{ marginTop: 8 }}>
              {legendItems.map(item => (
                <div key={item.type} style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
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
            </div>
          </Col>
          <Col span={12}>
            <Text strong>连接类型：</Text>
            <div style={{ marginTop: 8 }}>
              {connectionTypes.map((item, index) => (
                <div key={index} style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
                  <div
                    style={{
                      width: 20,
                      height: 2,
                      backgroundColor: item.color,
                      marginRight: 8,
                      borderStyle: item.style === 'dashed' ? 'dashed' : 'solid',
                      borderWidth: item.style === 'dashed' ? '1px 0' : '0'
                    }}
                  />
                  <Text style={{ fontSize: 12 }}>{item.label}</Text>
                </div>
              ))}
            </div>
          </Col>
        </Row>
      </Card>
    );
  };

  const containerStyle = fullscreen ? {
    position: 'fixed' as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'white',
    zIndex: 1000,
    padding: 20
  } : {};

  return (
    <div ref={containerRef} style={containerStyle}>
      <Card
        title={
          <Space>
            <NodeIndexOutlined />
            <span>交互式知识图谱</span>
            {graphData && (
              <Badge 
                count={graphData.nodes.length} 
                style={{ backgroundColor: '#52c41a' }}
                title="节点数量"
              />
            )}
          </Space>
        }
        extra={renderControls()}
      >
        <Spin spinning={loading}>
          <div style={{ textAlign: 'center', marginBottom: 16 }}>
            <svg 
              ref={svgRef} 
              style={{ 
                border: '1px solid #d9d9d9', 
                borderRadius: 4,
                backgroundColor: '#fafafa'
              }} 
            />
          </div>
          
          {!loading && graphData && graphData.nodes.length === 0 && (
            <div style={{ textAlign: 'center', padding: 40 }}>
              <Text type="secondary">暂无知识图谱数据</Text>
            </div>
          )}
        </Spin>

        {renderLegend()}
      </Card>

      {renderNodeDetail()}

      {/* 右键菜单 */}
      {contextMenuVisible && contextMenuNode && (
        <Dropdown
          open={contextMenuVisible}
          menu={getContextMenuItems(contextMenuNode)}
          trigger={['contextMenu']}
          onOpenChange={(visible) => {
            if (!visible) {
              setContextMenuVisible(false);
              setContextMenuNode(null);
            }
          }}
        >
          <div
            style={{
              position: 'fixed',
              left: contextMenuPosition.x,
              top: contextMenuPosition.y,
              width: 1,
              height: 1,
              pointerEvents: 'none'
            }}
          />
        </Dropdown>
      )}

      {/* 编辑器组件 */}
      <KnowledgeGraphEditor
        visible={editModalVisible}
        onClose={handleEditClose}
        onSuccess={handleEditSuccess}
        editMode={true}
        editData={editingNode ? {
          id: editingNode.id.startsWith('content_') ? editingNode.id.replace('content_', '') : editingNode.id,
          title: editingNode.name,
          subject_id: editingNode.subject_id || '',
          subject_name: editingNode.subject_name,
          content: editingNode.content || '',
          description: editingNode.content || '',
          tags: editingNode.tags || []
        } : undefined}
      />

        {/* 标签管理模态框 */}
        <Modal
          title="管理标签"
          open={tagModalVisible}
          onOk={handleSaveTagChanges}
          onCancel={() => {
            setTagModalVisible(false);
            setManagingTagsNode(null);
            setNewTag('');
          }}
          width={600}
          okText="保存"
          cancelText="取消"
        >
          {managingTagsNode && (
            <div>
              <div style={{ marginBottom: 16 }}>
                <Text strong>节点：</Text>
                <Text>{managingTagsNode.name}</Text>
              </div>
              
              <div style={{ marginBottom: 16 }}>
                <Text strong>当前标签：</Text>
                <div style={{ marginTop: 8 }}>
                  {(managingTagsNode.tags || []).map(tag => (
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
                  {(!managingTagsNode.tags || managingTagsNode.tags.length === 0) && (
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

         {/* 节点移动模态框 */}
         <Modal
           title="移动节点"
           open={moveModalVisible}
           onOk={handleExecuteMove}
           onCancel={() => {
             setMoveModalVisible(false);
             setMovingNode(null);
             setTargetSubjectId('');
           }}
           width={500}
           okText="移动"
           cancelText="取消"
           okButtonProps={{ disabled: !targetSubjectId }}
         >
           {movingNode && (
             <div>
               <div style={{ marginBottom: 16 }}>
                 <Text strong>节点：</Text>
                 <Text>{movingNode.name}</Text>
               </div>
               
               <div style={{ marginBottom: 16 }}>
                 <Text strong>当前学科：</Text>
                 <Text>{movingNode.subject_name || '未知'}</Text>
               </div>
               
               <div>
                 <Text strong>目标学科：</Text>
                 <Select
                   value={targetSubjectId}
                   onChange={setTargetSubjectId}
                   placeholder="选择目标学科"
                   style={{ width: '100%', marginTop: 8 }}
                 >
                   {subjects.map(subject => (
                     <Option key={subject.id} value={subject.id}>
                       {subject.name}
                     </Option>
                   ))}
                 </Select>
               </div>
             </div>
           )}
         </Modal>

         {/* 节点合并模态框 */}
         <Modal
           title="合并节点"
           open={mergeModalVisible}
           onOk={handleExecuteMerge}
           onCancel={() => {
             setMergeModalVisible(false);
             setMergeTitle('');
             setMergeDescription('');
           }}
           width={700}
           okText="合并"
           cancelText="取消"
           okButtonProps={{ disabled: !mergeTitle.trim() }}
         >
           <div>
             <div style={{ marginBottom: 16 }}>
               <Text strong>选中的节点 ({selectedNodes.size} 个)：</Text>
               <div style={{ marginTop: 8 }}>
                 {Array.from(selectedNodes).map(nodeId => {
                   const node = graphData?.nodes.find(n => n.id === nodeId);
                   return node ? (
                     <Tag key={nodeId} color="blue" style={{ marginBottom: 4 }}>
                       {node.name}
                     </Tag>
                   ) : null;
                 })}
               </div>
             </div>
             
             <div style={{ marginBottom: 16 }}>
               <Text strong>合并后的标题：</Text>
               <Input
                 value={mergeTitle}
                 onChange={(e) => setMergeTitle(e.target.value)}
                 placeholder="输入合并后的节点标题"
                 style={{ marginTop: 8 }}
               />
             </div>
             
             <div>
               <Text strong>合并后的内容：</Text>
               <Input.TextArea
                 value={mergeDescription}
                 onChange={(e) => setMergeDescription(e.target.value)}
                 placeholder="输入合并后的节点内容"
                 rows={8}
                 style={{ marginTop: 8 }}
               />
             </div>
           </div>
         </Modal>
       </div>
     );
   };
 
    export default InteractiveKnowledgeGraph;