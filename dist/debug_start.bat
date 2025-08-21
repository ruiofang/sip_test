@echo off
chcp 65001 >nul
title CloudVoIP客户端 - 调试模式

echo ================================
echo    CloudVoIP客户端 - 调试模式
echo ================================
echo.

echo 当前目录: %cd%
echo 检查文件是否存在...
if exist "CloudVoIPClient.exe" (
    echo ✓ CloudVoIPClient.exe 存在
) else (
    echo ✗ CloudVoIPClient.exe 不存在！
    pause
    exit /b 1
)

echo.
echo 尝试启动客户端 (连接到默认服务器)...
echo 命令: CloudVoIPClient.exe --server 120.27.145.121 --name test1
echo.

CloudVoIPClient.exe --server 120.27.145.121 --name u1 2>&1

echo.
echo 退出码: %ERRORLEVEL%
if %ERRORLEVEL% neq 0 (
    echo 程序异常退出！错误码: %ERRORLEVEL%
) else (
    echo 程序正常退出。
)

echo.
echo 按任意键关闭窗口...
pause >nul
