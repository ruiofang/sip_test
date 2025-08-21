#!/bin/bash
# Cloud VoIP Server 启动脚本 - 后台运行模式

cd /home/ruio/sip_test
exec python3 cloud_voip_server.py --daemon
