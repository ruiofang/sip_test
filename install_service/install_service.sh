#!/bin/bash

# 云端VoIP服务器自动启动安装脚本

SERVICE_NAME="cloud-voip"
SERVICE_FILE="cloud-voip.service"
SYSTEMD_DIR="/etc/systemd/system"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "正在安装 Cloud VoIP 服务..."

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then
    echo "错误：请使用 sudo 运行此脚本"
    echo "使用方法: sudo ./install_service.sh"
    exit 1
fi

# 复制服务文件到 systemd 目录
echo "复制服务文件到 $SYSTEMD_DIR..."
cp "$CURRENT_DIR/$SERVICE_FILE" "$SYSTEMD_DIR/"

# 重新加载 systemd 配置
echo "重新加载 systemd 配置..."
systemctl daemon-reload

# 启用服务（开机自启动）
echo "启用服务开机自启动..."
systemctl enable $SERVICE_NAME

# 启动服务
echo "启动服务..."
systemctl start $SERVICE_NAME

# 检查服务状态
echo "检查服务状态..."
systemctl status $SERVICE_NAME --no-pager

echo ""
echo "安装完成！"
echo ""
echo "常用命令："
echo "查看服务状态: sudo systemctl status $SERVICE_NAME"
echo "停止服务:     sudo systemctl stop $SERVICE_NAME"
echo "重启服务:     sudo systemctl restart $SERVICE_NAME"
echo "查看日志:     sudo journalctl -u $SERVICE_NAME -f"
echo "禁用开机自启: sudo systemctl disable $SERVICE_NAME"
echo "卸载服务:     sudo ./uninstall_service.sh"
