#!/bin/bash

# Cloud VoIP 服务管理脚本

SERVICE_NAME="cloud-voip"

case "$1" in
    start)
        echo "启动 $SERVICE_NAME 服务..."
        sudo systemctl start $SERVICE_NAME
        ;;
    stop)
        echo "停止 $SERVICE_NAME 服务..."
        sudo systemctl stop $SERVICE_NAME
        ;;
    restart)
        echo "重启 $SERVICE_NAME 服务..."
        sudo systemctl restart $SERVICE_NAME
        ;;
    status)
        echo "查看 $SERVICE_NAME 服务状态..."
        sudo systemctl status $SERVICE_NAME --no-pager
        ;;
    logs)
        echo "查看 $SERVICE_NAME 服务日志..."
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    enable)
        echo "启用 $SERVICE_NAME 开机自启动..."
        sudo systemctl enable $SERVICE_NAME
        ;;
    disable)
        echo "禁用 $SERVICE_NAME 开机自启动..."
        sudo systemctl disable $SERVICE_NAME
        ;;
    install)
        echo "安装 $SERVICE_NAME 服务..."
        sudo ./install_service.sh
        ;;
    uninstall)
        echo "卸载 $SERVICE_NAME 服务..."
        sudo ./uninstall_service.sh
        ;;
    *)
        echo "Cloud VoIP 服务管理脚本"
        echo ""
        echo "使用方法: $0 {start|stop|restart|status|logs|enable|disable|install|uninstall}"
        echo ""
        echo "命令说明："
        echo "  start      - 启动服务"
        echo "  stop       - 停止服务"
        echo "  restart    - 重启服务"
        echo "  status     - 查看服务状态"
        echo "  logs       - 查看服务日志"
        echo "  enable     - 启用开机自启动"
        echo "  disable    - 禁用开机自启动"
        echo "  install    - 安装服务"
        echo "  uninstall  - 卸载服务"
        exit 1
        ;;
esac
