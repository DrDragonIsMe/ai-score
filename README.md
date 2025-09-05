# AI Score - 高中生提分系统

一个基于AI的高中生学习提分SaaS平台，支持多租户和多语言。

## 📋 版本信息

- **当前版本**: AI 1.0
- **更新日期**: 2025-01-24
- **状态**: AI交互侧边版 ✅

### 🔄 最新更新 (AI 1.0 - AI交互侧边版)

- 🎨 **UI界面优化**: 全面优化用户界面设计，提升视觉体验和交互流畅性
- 🌈 **统一色彩系统**: 建立完整的色彩变量体系，实现主题色彩的统一管理
- 🔘 **按钮样式标准化**: 统一按钮背景色和交互状态，提供一致的用户体验
- 📝 **字体规范化**: 建立统一的字体规范，包括字体族、大小、粗细和行高标准
- 🎯 **响应式设计**: 优化各组件在不同屏幕尺寸下的显示效果
- 🔧 **CSS变量系统**: 引入CSS自定义属性，提高样式维护性和主题切换能力
- 📱 **交互体验提升**: 优化按钮悬停效果、焦点状态和视觉反馈
- 🎪 **主题一致性**: 确保整个应用的视觉风格统一，提升品牌识别度
- 🛠️ **开发效率**: 通过标准化样式变量，提高后续功能开发的效率
- 📊 **可维护性**: 建立可扩展的样式架构，便于未来的主题定制和扩展

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
9. **AI助理快捷操作**: 六大智能学习助手功能
   - 💡 解释概念、📝 练习题目、📚 知识总结
   - 📅 学习计划、🔍 错题分析、🎯 智能推荐
10. **PPT模板选择与生成**: 智能PPT创建系统
    - 🎨 多种专业模板（商务、教育、学术）
    - 📤 自定义模板上传和管理功能
    - 🤖 AI智能内容生成和模板适配
    - 📥 一键生成和下载PPT文件
11. **学科知识数字化增强**: 完整的知识图谱系统
    - 📚 九大学科完整知识结构（语文、数学、英语、物理、化学、生物、历史、地理、政治）
    - 🌟 可视化知识星图，直观展示学科知识关联
    - 🔗 章节与知识点的层次化组织和智能关联
    - 📖 支持syllabus自动解析和模板降级机制
12. **个人资料系统**: 完整的用户信息管理
    - 👤 个人资料编辑和头像上传
    - 🤖 AI助手个性化昵称设置
    - 🔐 JWT认证优化和安全性增强
    - 📱 响应式界面设计和用户体验优化
13. **AI交互侧边版特性**: 全新的UI/UX设计体验 🆕
    - 🎨 **统一视觉设计**: 建立完整的设计系统和色彩规范
    - 🌈 **主题色彩管理**: CSS变量驱动的动态主题切换能力
    - 🔘 **标准化组件**: 统一的按钮、表单和交互组件样式
    - 📝 **字体系统**: 完整的字体层级和排版规范
    - 🎯 **响应式布局**: 适配各种设备的流畅交互体验
    - 🛠️ **开发友好**: 基于CSS变量的可维护样式架构

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
   - 系统会自动初始化学科数据和知识图谱

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

本项目采用 Apache License 2.0 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

**重要说明：**
- 本软件不得用于多租户服务或SaaS服务
- 不得移除或修改原始的版权声明、许可证信息、LOGO和归属声明
- 必须保留对原始项目的引用和归属

## 支持

如果您遇到问题或需要帮助，请：

1. 查看本文档的故障排除部分
2. 搜索已有的 Issues
3. 创建新的 Issue 并提供详细信息

---

**AI Score** - 让学习更智能，让提分更高效！