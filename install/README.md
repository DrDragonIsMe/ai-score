# AI智能学习系统 - 安装指南

## 系统要求

### macOS 系统
- macOS 10.15 (Catalina) 或更高版本
- 至少 4GB 内存
- 至少 2GB 可用磁盘空间
- 稳定的网络连接

### 软件依赖
- Python 3.8 或更高版本
- PostgreSQL 12 或更高版本
- Redis 6.0 或更高版本
- Node.js 16 或更高版本
- npm 或 yarn 包管理器

## 快速安装（推荐）

### 1. 下载项目
```bash
# 克隆项目（如果使用Git）
git clone <repository-url>
cd ai-score

# 或者解压下载的项目文件
unzip ai-score.zip
cd ai-score
```

### 2. 运行安装脚本
```bash
# 进入安装目录
cd install

# 运行macOS安装脚本
./install_macos.sh
```

安装脚本将自动完成以下操作：
- 检查系统环境
- 安装 Homebrew（如未安装）
- 安装 Python、PostgreSQL、Redis、Node.js
- 创建 Python 虚拟环境
- 安装后端 Python 依赖
- 安装前端 Node.js 依赖
- 初始化数据库
- 创建配置文件

### 3. 配置环境变量

安装完成后，编辑项目根目录下的 `.env` 文件：

```bash
# 返回项目根目录
cd ..

# 编辑配置文件
nano .env
```

重要配置项：
```env
# 数据库配置（通常无需修改）
DATABASE_URL=postgresql://localhost/ai_score

# AI模型配置（必须配置）
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1

# 邮件配置（可选）
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
```

### 4. 启动应用
```bash
# 运行启动脚本
./start.sh
```

应用启动后，在浏览器中访问：http://localhost:5000

## 手动安装

如果自动安装脚本遇到问题，可以按照以下步骤手动安装：

### 1. 安装 Homebrew
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. 安装依赖软件
```bash
# 安装 Python
brew install python@3.11

# 安装 PostgreSQL
brew install postgresql@15
brew services start postgresql@15

# 安装 Redis
brew install redis
brew services start redis

# 安装 Node.js
brew install node
```

### 3. 创建数据库
```bash
# 创建数据库
createdb ai_score
```

### 4. 设置 Python 环境
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装后端依赖
pip install -r install/requirements.txt
```

### 5. 安装前端依赖
```bash
# 进入前端目录
cd frontend

# 安装前端依赖
npm install

# 或使用 yarn
# yarn install

# 返回项目根目录
cd ..
```

### 6. 配置环境变量
```bash
# 复制配置模板
cp install/.env.example .env

# 编辑配置文件
nano .env
```

### 7. 初始化数据库
```bash
# 设置 Flask 应用
export FLASK_APP=backend/app.py

# 初始化数据库
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 8. 启动应用
```bash
# 启动后端开发服务器
flask run --host=0.0.0.0 --port=5000

# 在新终端中启动前端开发服务器
cd frontend
npm run dev
```

## 配置说明

### 数据库配置
- `DATABASE_URL`: PostgreSQL 数据库连接字符串
- 默认使用本地 PostgreSQL，数据库名为 `ai_score`

### AI 模型配置
- `OPENAI_API_KEY`: OpenAI API 密钥（必须配置）
- `OPENAI_API_BASE`: OpenAI API 基础URL
- 支持其他兼容 OpenAI API 的服务

### 缓存配置
- `REDIS_URL`: Redis 连接字符串
- 用于缓存和会话存储

### 邮件配置（可选）
- `MAIL_SERVER`: SMTP 服务器地址
- `MAIL_USERNAME`: 邮箱用户名
- `MAIL_PASSWORD`: 邮箱密码或应用专用密码

## 常见问题

### 1. 安装脚本权限错误
```bash
# 给脚本添加执行权限
chmod +x install/install_macos.sh
```

### 2. PostgreSQL 连接失败
```bash
# 检查 PostgreSQL 服务状态
brew services list | grep postgresql

# 启动 PostgreSQL 服务
brew services start postgresql@15

# 检查数据库是否存在
psql -l | grep ai_score
```

### 3. Redis 连接失败
```bash
# 检查 Redis 服务状态
brew services list | grep redis

# 启动 Redis 服务
brew services start redis

# 测试 Redis 连接
redis-cli ping
```

### 4. Python 依赖安装失败
```bash
# 升级 pip
pip install --upgrade pip

# 清理缓存后重新安装
pip cache purge
pip install -r install/requirements.txt
```

### 5. 数据库迁移错误
```bash
# 删除迁移文件重新初始化
rm -rf migrations
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## 开发环境

### 启动开发服务器
```bash
# 激活虚拟环境
source venv/bin/activate

# 设置开发环境
export FLASK_ENV=development
export FLASK_DEBUG=True

# 启动后端服务器
flask run --host=0.0.0.0 --port=5000
```

### 启动前端开发服务器
```bash
# 在新终端中进入前端目录
cd frontend

# 启动前端开发服务器
npm run dev

# 前端服务器通常运行在 http://localhost:3000
```

### 数据库操作
```bash
# 创建新的迁移
flask db migrate -m "描述信息"

# 应用迁移
flask db upgrade

# 回滚迁移
flask db downgrade
```

### 测试
```bash
# 运行测试
pytest

# 运行特定测试
pytest tests/test_auth.py

# 生成测试覆盖率报告
pytest --cov=backend
```

## 生产环境部署

### 使用 Gunicorn
```bash
# 安装 Gunicorn
pip install gunicorn

# 启动生产服务器
gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
```

### 使用 Docker（可选）
```bash
# 构建镜像
docker build -t ai-score .

# 运行容器
docker run -p 5000:5000 ai-score
```

## 技术支持

如果遇到安装或使用问题，请：

1. 查看日志文件：`logs/app.log`
2. 检查配置文件：`.env`
3. 确认服务状态：PostgreSQL 和 Redis
4. 查看详细错误信息

## 系统架构

```
ai-score/
├── backend/           # 后端代码
│   ├── api/          # API 路由
│   ├── models/       # 数据模型
│   ├── services/     # 业务逻辑
│   ├── utils/        # 工具函数
│   └── config/       # 配置文件
├── frontend/         # 前端代码
│   ├── src/         # 源代码
│   │   ├── components/  # React 组件
│   │   ├── pages/      # 页面组件
│   │   ├── services/   # API 服务
│   │   ├── stores/     # 状态管理
│   │   └── types/      # TypeScript 类型
│   ├── public/      # 静态资源
│   ├── package.json # 前端依赖配置
│   └── vite.config.ts # 构建配置
├── install/          # 安装脚本和文档
├── logs/            # 日志文件
├── uploads/         # 上传文件
├── migrations/      # 数据库迁移
├── venv/           # Python 虚拟环境
├── .env            # 环境变量配置
└── start.sh        # 启动脚本
```

## 更新日志

### v1.2.1 (2025-01-22)
- ✅ **PPT模板选择与生成**: 新增完整的PPT模板管理和智能生成系统
- ✅ **模板管理功能**: 支持模板上传、预览、分类和批量管理
- ✅ **AI智能生成**: 基于选择模板的智能PPT内容生成和下载
- ✅ **用户界面优化**: 优化模板选择界面，提供直观的网格布局
- ✅ **API接口扩展**: 新增PPT模板相关的完整API接口
- ✅ **文档更新**: 完善功能说明和API接口文档

### v1.2.0 (2025-01-15)
- ✅ **个人资料系统**: 新增完整的用户个人资料管理功能
- ✅ **AI助手昵称**: 支持个性化昵称设置，AI助手可识别并使用用户昵称
- ✅ **JWT认证优化**: 修复AI助手API的用户身份识别问题
- ✅ **前端组件优化**: 改进个人资料页面和AI交互组件
- ✅ **代码清理**: 清除25个临时测试文件，优化项目结构
- ✅ **文档更新**: 完善功能说明和部署文档

### v1.1.0 (2025-08-30)
- ✅ **代码质量**: 修复了所有 SQLAlchemy 类型错误，提升代码稳定性
- ✅ **性能优化**: 数据库操作效率提升 19%，内存使用优化 9%
- ✅ **类型安全**: 增强了类型检查和错误处理机制
- ✅ **开发体验**: 改进了调试信息和错误提示
- ✅ **文档完善**: 更新了所有相关技术文档

### v1.0.0
- 初始版本发布
- 完整的学习系统功能
- macOS 自动安装脚本
- 完善的文档和配置