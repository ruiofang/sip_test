@echo off
chcp 65001 >nul
title CloudVoIP客户端

echo 启动 CloudVoIP 客户端...
echo.

REM 使用默认配置启动
CloudVoIPClient.exe --server 120.27.145.121 --name u1

echo.
echo 客户端已退出，按任意键关闭窗口...
pause >nul
