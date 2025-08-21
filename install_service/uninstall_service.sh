#!/bin/bash

# 云端VoIP服务器卸载脚本

SERVICE_NAME="cloud-voip"
SYSTEMD_DIR="/etc/systemd/system"

echo "正在卸载 Cloud VoIP 服务..."

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then
    echo "错误：请使用 sudo 运行此脚本"
    echo "使用方法: sudo ./uninstall_service.sh"
    exit 1
fi

# 停止服务
echo "停止服务..."
systemctl stop $SERVICE_NAME

# 禁用服务
echo "禁用服务..."
systemctl disable $SERVICE_NAME

# 删除服务文件
echo "删除服务文件..."
rm -f "$SYSTEMD_DIR/$SERVICE_NAME.service"

# 重新加载 systemd 配置
echo "重新加载 systemd 配置..."
systemctl daemon-reload

echo "卸载完成！"
