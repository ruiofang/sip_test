@echo off
chcp 65001 >nul
title CloudVoIP客户端启动器

echo ================================
echo      CloudVoIP客户端启动器
echo ================================
echo.

:menu
echo 请选择启动方式：
echo #############
echo 1. 连接默认服务器 120.27.145.121
echo 2. 连接本地服务器 127.0.0.1
echo 3. 自定义服务器
echo 4. 查看帮助信息
echo 5. 退出
echo.
set /p choice="请输入选择 (1-5): "

if "%choice%"=="1" goto default_server
if "%choice%"=="2" goto local_server
if "%choice%"=="3" goto custom_server
if "%choice%"=="4" goto help
if "%choice%"=="5" goto exit
echo 无效选择，请重新输入！
echo.
goto menu

:default_server
echo.
echo 正在连接默认服务器...
set /p client_name="请输入客户端名称 (默认: u1): "
if "%client_name%"=="" set client_name=u1
CloudVoIPClient.exe --server 120.27.145.121 --name %client_name%
goto end

:local_server
echo.
echo 正在连接本地服务器...
set /p client_name="请输入客户端名称 (默认: TestClient): "
if "%client_name%"=="" set client_name=TestClient
CloudVoIPClient.exe --server 127.0.0.1 --name %client_name%
goto end

:custom_server
echo.
set /p server_ip="请输入服务器IP地址: "
if "%server_ip%"=="" (
    echo 服务器IP不能为空！
    goto menu
)
set /p client_name="请输入客户端名称: "
if "%client_name%"=="" set client_name=CustomClient
CloudVoIPClient.exe --server %server_ip% --name %client_name%
goto end

:help
echo.
echo 显示帮助信息：
CloudVoIPClient.exe --help
echo.
pause
goto menu

:end
echo.
echo 客户端已退出。
pause
goto menu

:exit
echo 感谢使用 CloudVoIP 客户端！
exit
