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
- Node.js 16 或更高版本（如需前端开发）

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
- 安装 Python、PostgreSQL、Redis
- 创建 Python 虚拟环境
- 安装项目依赖
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

# 安装依赖
pip install -r install/requirements.txt
```

### 5. 配置环境变量
```bash
# 复制配置模板
cp install/.env.example .env

# 编辑配置文件
nano .env
```

### 6. 初始化数据库
```bash
# 设置 Flask 应用
export FLASK_APP=backend/app.py

# 初始化数据库
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 7. 启动应用
```bash
# 启动开发服务器
flask run --host=0.0.0.0 --port=5000
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

# 启动服务器
flask run --host=0.0.0.0 --port=5000
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
├── install/          # 安装脚本和文档
├── logs/            # 日志文件
├── uploads/         # 上传文件
├── migrations/      # 数据库迁移
├── venv/           # Python 虚拟环境
├── .env            # 环境变量配置
└── start.sh        # 启动脚本
```

## 更新日志

### v1.0.0
- 初始版本发布
- 完整的学习系统功能
- macOS 自动安装脚本
- 完善的文档和配置