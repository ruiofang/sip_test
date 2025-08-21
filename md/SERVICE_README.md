# Cloud VoIP Server 服务管理

这个目录包含了用于管理 Cloud VoIP Server 自动启动的服务脚本。

## 文件说明

- `cloud-voip.service` - systemd 服务配置文件
- `install_service.sh` - 服务安装脚本
- `uninstall_service.sh` - 服务卸载脚本
- `service_manager.sh` - 服务管理脚本

## 安装步骤

1. 安装服务（需要管理员权限）：
```bash
sudo ./install_service.sh
```

这将会：
- 将服务文件复制到 `/etc/systemd/system/`
- 启用开机自启动
- 立即启动服务

## 服务管理

安装完成后，您可以使用以下命令管理服务：

### 使用 service_manager.sh 脚本（推荐）

```bash
# 查看所有可用命令
./service_manager.sh

# 启动服务
./service_manager.sh start

# 停止服务
./service_manager.sh stop

# 重启服务
./service_manager.sh restart

# 查看服务状态
./service_manager.sh status

# 查看服务日志
./service_manager.sh logs

# 启用开机自启动
./service_manager.sh enable

# 禁用开机自启动
./service_manager.sh disable
```

### 直接使用 systemctl 命令

```bash
# 启动服务
sudo systemctl start cloud-voip

# 停止服务
sudo systemctl stop cloud-voip

# 重启服务
sudo systemctl restart cloud-voip

# 查看服务状态
sudo systemctl status cloud-voip

# 查看服务日志
sudo journalctl -u cloud-voip -f

# 启用开机自启动
sudo systemctl enable cloud-voip

# 禁用开机自启动
sudo systemctl disable cloud-voip
```

## 卸载服务

如果需要卸载服务：

```bash
sudo ./uninstall_service.sh
```

## 服务配置说明

服务配置了以下特性：
- 自动重启：如果程序异常退出，会自动重启
- 开机自启：系统启动后自动运行
- 后台运行：输出重定向到 /dev/null，不产生日志文件
- 用户权限：以 ruio 用户身份运行
- 工作目录：/home/ruio/sip_test

## 故障排除

1. 如果服务启动失败，检查：
   - Python3 是否正确安装
   - cloud_voip_server.py 文件是否存在
   - 用户权限是否正确

2. 查看详细日志：
   ```bash
   sudo journalctl -u cloud-voip -n 50
   ```

3. 如果需要修改配置，编辑服务文件后重新加载：
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart cloud-voip
   ```
