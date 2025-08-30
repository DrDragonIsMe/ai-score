#!/bin/bash

# AI智能学习系统 - macOS安装脚本
# 适用于 macOS 系统

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查系统要求
check_system() {
    log_info "检查系统环境..."
    
    # 检查操作系统
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_error "此脚本仅适用于 macOS 系统"
        exit 1
    fi
    
    # 检查macOS版本
    macos_version=$(sw_vers -productVersion)
    log_info "macOS 版本: $macos_version"
    
    # 检查是否安装了Xcode Command Line Tools
    if ! xcode-select -p &> /dev/null; then
        log_warning "未检测到 Xcode Command Line Tools，正在安装..."
        xcode-select --install
        log_info "请在弹出的对话框中完成 Xcode Command Line Tools 的安装，然后重新运行此脚本"
        exit 1
    fi
    
    log_success "系统环境检查完成"
}

# 安装Homebrew
install_homebrew() {
    if command_exists brew; then
        log_info "Homebrew 已安装"
        brew update
    else
        log_info "正在安装 Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # 添加Homebrew到PATH
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [[ -f "/usr/local/bin/brew" ]]; then
            echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/usr/local/bin/brew shellenv)"
        fi
        
        log_success "Homebrew 安装完成"
    fi
}

# 安装Python
install_python() {
    log_info "检查 Python 环境..."
    
    if command_exists python3; then
        python_version=$(python3 --version | cut -d' ' -f2)
        log_info "Python 版本: $python_version"
        
        # 检查Python版本是否满足要求（3.8+）
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            log_success "Python 版本满足要求"
        else
            log_warning "Python 版本过低，正在安装最新版本..."
            brew install python@3.11
        fi
    else
        log_info "正在安装 Python..."
        brew install python@3.11
    fi
    
    # 确保pip可用
    if ! command_exists pip3; then
        log_info "正在安装 pip..."
        python3 -m ensurepip --upgrade
    fi
    
    log_success "Python 环境准备完成"
}

# 安装PostgreSQL
install_postgresql() {
    log_info "检查 PostgreSQL..."
    
    if command_exists psql; then
        log_info "PostgreSQL 已安装"
    else
        log_info "正在安装 PostgreSQL..."
        brew install postgresql@15
        
        # 启动PostgreSQL服务
        brew services start postgresql@15
        
        # 添加到PATH
        echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> ~/.zprofile
        export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
        
        log_success "PostgreSQL 安装完成"
    fi
    
    # 创建数据库
    log_info "创建数据库..."
    createdb ai_score 2>/dev/null || log_warning "数据库可能已存在"
}

# 安装Redis
install_redis() {
    log_info "检查 Redis..."
    
    if command_exists redis-server; then
        log_info "Redis 已安装"
    else
        log_info "正在安装 Redis..."
        brew install redis
        
        # 启动Redis服务
        brew services start redis
        
        log_success "Redis 安装完成"
    fi
}

# 创建Python虚拟环境
setup_virtualenv() {
    log_info "创建 Python 虚拟环境..."
    
    cd "$(dirname "$0")/.."
    
    if [[ -d "venv" ]]; then
        log_warning "虚拟环境已存在，正在删除旧环境..."
        rm -rf venv
    fi
    
    python3 -m venv venv
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    log_success "虚拟环境创建完成"
}

# 安装Python依赖
install_dependencies() {
    log_info "安装 Python 依赖包..."
    
    cd "$(dirname "$0")/.."
    source venv/bin/activate
    
    # 安装依赖
    pip install -r install/requirements.txt
    
    log_success "依赖包安装完成"
}

# 配置环境变量
setup_environment() {
    log_info "配置环境变量..."
    
    cd "$(dirname "$0")/.."
    
    # 创建.env文件
    if [[ ! -f ".env" ]]; then
        cat > .env << EOF
# 数据库配置
DATABASE_URL=postgresql://localhost/ai_score

# Redis配置
REDIS_URL=redis://localhost:6379/0

# Flask配置
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# JWT配置
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
JWT_ACCESS_TOKEN_EXPIRES=3600

# AI模型配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1

# 邮件配置
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password

# 文件上传配置
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
EOF
        
        log_success "环境变量配置文件已创建: .env"
        log_warning "请编辑 .env 文件，填入正确的配置信息"
    else
        log_info "环境变量配置文件已存在"
    fi
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    cd "$(dirname "$0")/.."
    source venv/bin/activate
    
    # 设置Flask应用
    export FLASK_APP=backend/app.py
    
    # 初始化数据库迁移
    if [[ ! -d "migrations" ]]; then
        flask db init
    fi
    
    # 创建迁移文件
    flask db migrate -m "Initial migration"
    
    # 应用迁移
    flask db upgrade
    
    log_success "数据库初始化完成"
}

# 创建启动脚本
create_start_script() {
    log_info "创建启动脚本..."
    
    cd "$(dirname "$0")/.."
    
    cat > start.sh << 'EOF'
#!/bin/bash

# AI智能学习系统启动脚本

cd "$(dirname "$0")"

# 激活虚拟环境
source venv/bin/activate

# 设置环境变量
export FLASK_APP=backend/app.py
export FLASK_ENV=development

# 启动应用
echo "正在启动 AI智能学习系统..."
echo "访问地址: http://localhost:5000"
echo "按 Ctrl+C 停止服务"

flask run --host=0.0.0.0 --port=5000
EOF
    
    chmod +x start.sh
    
    log_success "启动脚本已创建: start.sh"
}

# 主安装流程
main() {
    echo "==========================================="
    echo "    AI智能学习系统 - macOS 安装程序"
    echo "==========================================="
    echo ""
    
    # 检查系统
    check_system
    
    # 安装基础软件
    install_homebrew
    install_python
    install_postgresql
    install_redis
    
    # 设置Python环境
    setup_virtualenv
    install_dependencies
    
    # 配置应用
    setup_environment
    init_database
    create_start_script
    
    echo ""
    echo "==========================================="
    log_success "安装完成！"
    echo "==========================================="
    echo ""
    echo "下一步操作："
    echo "1. 编辑 .env 文件，配置必要的参数"
    echo "2. 运行 ./start.sh 启动应用"
    echo "3. 在浏览器中访问 http://localhost:5000"
    echo ""
    echo "如需帮助，请查看 install/README.md 文档"
    echo ""
}

# 运行主程序
main "$@"