# AI Score - 高中生提分系统

一个基于AI的高中生学习提分SaaS平台，支持多租户和多语言。

## 📋 版本信息

- **当前版本**: v1.1.0
- **更新日期**: 2025-08-30
- **状态**: 稳定版本 ✅

### 🔄 最新更新 (v1.1.0)

- ✅ 修复了所有 SQLAlchemy Column 类型错误
- ✅ 优化了数据库操作和查询性能
- ✅ 增强了类型安全和错误处理
- ✅ 改进了代码质量和一致性
- ✅ 更新了文档和注释

> 📖 详细更新日志请查看 [CHANGELOG.md](./CHANGELOG.md)

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
│   ├── app/                 # 应用核心代码
│   ├── models/              # 数据模型
│   ├── api/                 # API接口
│   └── utils/               # 工具函数
├── frontend/                # React + TypeScript 前端
│   ├── src/                 # 源代码
│   ├── public/              # 静态资源
│   └── package.json         # 前端依赖
├── install/                 # 安装脚本和配置
│   ├── install_macos.sh     # macOS 安装脚本
│   └── requirements.txt     # Python 依赖
├── docs/                    # 项目文档
├── .env.example             # 环境变量模板
└── README.md               # 项目说明
```

## 系统要求

### macOS 环境
- macOS 10.15+ (Catalina 或更高版本)
- Xcode Command Line Tools
- 至少 4GB 可用内存
- 至少 2GB 可用磁盘空间

### 软件依赖
- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Redis 6+
- Homebrew (macOS 包管理器)

## 快速安装

### 自动安装 (推荐)

1. **下载项目**
   ```bash
   git clone <repository-url>
   cd ai-score
   ```

2. **运行安装脚本**
   ```bash
   chmod +x install/install_macos.sh
   ./install/install_macos.sh
   ```

3. **启动系统**
   ```bash
   # 启动完整系统（前端+后端）
   ./start.sh
   
   # 或者分别启动
   ./start_backend.sh   # 后端服务
   ./start_frontend.sh  # 前端服务
   ```

4. **访问系统**
   - 前端界面: http://localhost:5173
   - 后端API: http://localhost:5001

### 手动安装

如果自动安装失败，可以按照以下步骤手动安装：

1. **安装基础环境**
   ```bash
   # 安装 Homebrew
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # 安装依赖
   brew install python@3.9 node@18 postgresql@13 redis
   ```

2. **设置数据库**
   ```bash
   # 启动服务
   brew services start postgresql
   brew services start redis
   
   # 创建数据库
   createdb ai_score_db
   ```

3. **配置后端**
   ```bash
   # 创建虚拟环境
   python3 -m venv venv
   source venv/bin/activate
   
   # 安装依赖
   pip install -r install/requirements.txt
   
   # 配置环境变量
   cp .env.example .env
   # 编辑 .env 文件，配置数据库连接等
   ```

4. **配置前端**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

5. **初始化数据库**
   ```bash
   source venv/bin/activate
   python -c "from backend.app import create_app; app = create_app(); app.app_context().push(); from backend.models import db; db.create_all()"
   ```

## 使用指南

### 系统管理

**查看服务状态**
```bash
# 查看所有服务
tmux attach -t ai-score

# 检查后端服务
curl http://localhost:5001/api/health

# 检查前端服务
curl http://localhost:5173
```

**停止服务**
```bash
# 停止所有服务
tmux kill-session -t ai-score

# 或者在tmux会话中按 Ctrl+C
```

**重启服务**
```bash
# 停止服务
tmux kill-session -t ai-score

# 重新启动
./start.sh
```

### 开发模式

**后端开发**
```bash
# 激活虚拟环境
source venv/bin/activate

# 启动开发服务器
cd backend
python -c "from app import create_app; app = create_app(); app.run(debug=True, host='0.0.0.0', port=5001)"
```

**前端开发**
```bash
# 启动开发服务器
cd frontend
npm run dev
```

## 故障排除

### 常见问题

**1. 端口被占用**
```bash
# 查看端口占用
lsof -i :5001  # 后端端口
lsof -i :5173  # 前端端口

# 杀死占用进程
kill -9 <PID>
```

**2. 数据库连接失败**
```bash
# 检查PostgreSQL状态
brew services list | grep postgresql

# 重启PostgreSQL
brew services restart postgresql

# 检查数据库是否存在
psql -l | grep ai_score_db
```

**3. Redis连接失败**
```bash
# 检查Redis状态
brew services list | grep redis

# 重启Redis
brew services restart redis

# 测试Redis连接
redis-cli ping
```

**4. Python依赖问题**
```bash
# 重新安装依赖
source venv/bin/activate
pip install --upgrade pip
pip install -r install/requirements.txt
```

**5. Node.js依赖问题**
```bash
# 清理缓存并重新安装
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### 日志查看

**系统日志**
```bash
# 查看tmux会话
tmux attach -t ai-score

# 在tmux中切换窗口
# Ctrl+B, 然后按数字键 0, 1, 2...
```

**应用日志**
- 后端日志：在后端tmux窗口中查看
- 前端日志：在前端tmux窗口中查看
- 数据库日志：`tail -f /usr/local/var/log/postgresql@13.log`

## 开发指南

### 项目架构

**后端架构**
- Flask应用工厂模式
- SQLAlchemy ORM
- JWT身份认证
- RESTful API设计

**前端架构**
- React 18 + TypeScript
- Ant Design UI组件库
- React Router路由管理
- Zustand状态管理

### 添加新功能

**后端API**
1. 在 `backend/models/` 中定义数据模型
2. 在 `backend/api/` 中创建API路由
3. 更新数据库迁移

**前端页面**
1. 在 `frontend/src/pages/` 中创建页面组件
2. 在 `frontend/src/types/` 中定义TypeScript类型
3. 更新路由配置

### 代码规范

**Python代码**
- 遵循PEP 8规范
- 使用类型注解
- 编写单元测试

**TypeScript代码**
- 使用ESLint和Prettier
- 严格的TypeScript配置
- 组件化开发

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

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 支持

如果您遇到问题或需要帮助，请：

1. 查看本文档的故障排除部分
2. 搜索已有的 Issues
3. 创建新的 Issue 并提供详细信息

---

**AI Score** - 让学习更智能，让提分更高效！