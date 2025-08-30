# AI Score - 高中生提分系统

一个基于AI的高中生学习提分SaaS平台，支持多租户和多语言。

## 项目架构

### 技术栈
- **后端**: Python Flask + SQLAlchemy
- **前端**: React + TypeScript + Ant Design
- **数据库**: PostgreSQL + Redis
- **Web服务器**: Nginx
- **AI模型**: 豆包模型（可配置其他模型）
- **部署**: Docker + Docker Compose

### 核心功能
1. **提分公式**: 掌握 × 解题 × 应试 × 留存
2. **学科知识数字化**: 九科知识图谱
3. **个性化诊断**: AI自适应出题
4. **智能学习路径**: 动态调整学习计划
5. **记忆强化**: 艾宾浩斯遗忘曲线
6. **分层解题辅导**: 三层指导体系
7. **应试优化**: 限时模拟和策略优化
8. **效果追踪**: 多维度学习监测

## 项目结构

```
ai-score/
├── backend/                 # Python Flask 后端
├── frontend/                # React 前端
├── database/                # 数据库脚本和迁移
├── nginx/                   # Nginx 配置
├── docker/                  # Docker 配置文件
├── docs/                    # 项目文档
├── scripts/                 # 部署和工具脚本
├── docker-compose.yml       # Docker Compose 配置
└── README.md               # 项目说明
```

## 快速开始

1. 克隆项目
2. 配置环境变量
3. 启动服务: `docker-compose up -d`
4. 访问: http://localhost

## 多租户支持

- 基于域名的租户识别
- 数据隔离和权限管理
- 租户级别的配置管理

## 国际化支持

- 中文（简体/繁体）
- 英文
- 日文
- 韩文
- 可扩展其他语言