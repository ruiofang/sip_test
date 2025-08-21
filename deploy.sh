#!/bin/bash

# VoIP系统快速部署脚本
# 用法: ./deploy.sh [server|client]

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印彩色日志
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

# 检查Python版本
check_python() {
    log_info "检查Python版本..."
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version | cut -d' ' -f2)
        major=$(echo $python_version | cut -d'.' -f1)
        minor=$(echo $python_version | cut -d'.' -f2)
        
        if [[ $major -ge 3 && $minor -ge 8 ]]; then
            log_success "Python版本: $python_version ✓"
        else
            log_error "需要Python 3.8或更高版本，当前版本: $python_version"
            exit 1
        fi
    else
        log_error "未找到Python3，请先安装Python3"
        exit 1
    fi
}

# 安装系统依赖
install_system_deps() {
    log_info "安装系统依赖..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt &> /dev/null; then
            sudo apt update
            sudo apt install -y portaudio19-dev python3-dev python3-pip python3-venv
            log_success "Ubuntu/Debian依赖安装完成"
        elif command -v yum &> /dev/null; then
            sudo yum install -y portaudio-devel python3-devel python3-pip
            log_success "CentOS/RHEL依赖安装完成"
        else
            log_warning "未识别的Linux发行版，请手动安装portaudio开发包"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install portaudio
            log_success "macOS依赖安装完成"
        else
            log_warning "请安装Homebrew并运行: brew install portaudio"
        fi
    else
        log_warning "未识别的操作系统，请手动安装依赖"
    fi
}

# 创建虚拟环境
create_venv() {
    log_info "创建Python虚拟环境..."
    
    if [[ ! -d ".venv" ]]; then
        python3 -m venv .venv
        log_success "虚拟环境创建完成"
    else
        log_info "虚拟环境已存在"
    fi
    
    source .venv/bin/activate
    log_success "虚拟环境已激活"
}

# 安装Python依赖
install_python_deps() {
    log_info "安装Python依赖包..."
    
    pip install --upgrade pip
    pip install -r requirements.txt
    
    log_success "Python依赖安装完成"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙规则..."
    
    if command -v ufw &> /dev/null; then
        sudo ufw allow 5060/tcp  # 消息服务
        sudo ufw allow 5061/udp  # 音频传输
        sudo ufw allow 5062/tcp  # 控制服务
        log_success "UFW防火墙配置完成"
    elif command -v firewall-cmd &> /dev/null; then
        sudo firewall-cmd --permanent --add-port=5060/tcp
        sudo firewall-cmd --permanent --add-port=5061/udp
        sudo firewall-cmd --permanent --add-port=5062/tcp
        sudo firewall-cmd --reload
        log_success "FirewallD防火墙配置完成"
    else
        log_warning "请手动开放端口: TCP 5060,5062 和 UDP 5061"
    fi
}

# 部署服务器
deploy_server() {
    log_info "部署VoIP服务器..."
    
    check_python
    install_system_deps
    create_venv
    install_python_deps
    configure_firewall
    
    log_success "服务器部署完成！"
    echo ""
    log_info "启动服务器:"
    echo "python3 cloud_voip_server.py --host 0.0.0.0"
    echo ""
    log_info "后台运行:"
    echo "nohup python3 cloud_voip_server.py --host 0.0.0.0 > voip_server.log 2>&1 &"
}

# 部署客户端
deploy_client() {
    log_info "部署VoIP客户端..."
    
    check_python
    install_system_deps
    create_venv
    install_python_deps
    
    log_success "客户端部署完成！"
    echo ""
    log_info "启动客户端:"
    echo "python3 cloud_voip_client.py --server YOUR_SERVER_IP --name \"你的名称\""
}

# 运行测试
run_tests() {
    log_info "运行系统测试..."
    
    if [[ -f "test_audio.py" ]]; then
        python3 test_audio.py
    fi
    
    if [[ -f "debug_connection.py" ]]; then
        python3 debug_connection.py
    fi
    
    log_success "测试完成"
}

# 显示帮助信息
show_help() {
    echo "VoIP系统部署脚本"
    echo ""
    echo "用法:"
    echo "  $0 server    - 部署服务器端"
    echo "  $0 client    - 部署客户端"
    echo "  $0 test      - 运行测试"
    echo "  $0 help      - 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 server    # 在云服务器上运行"
    echo "  $0 client    # 在客户端机器上运行"
}

# 主函数
main() {
    echo "=========================================="
    echo "  VoIP云端语音通话系统 - 部署脚本"
    echo "=========================================="
    echo ""
    
    case "$1" in
        "server")
            deploy_server
            ;;
        "client")
            deploy_client
            ;;
        "test")
            run_tests
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        "")
            log_error "请指定部署类型"
            show_help
            exit 1
            ;;
        *)
            log_error "未知的参数: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
