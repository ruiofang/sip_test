@echo off
REM 安装VoIP客户端啸叫抑制增强版依赖
echo 正在安装VoIP客户端增强版依赖...

echo.
echo 步骤1: 更新pip
python -m pip install --upgrade pip

echo.
echo 步骤2: 安装PyAudio
python -m pip install PyAudio==0.2.14

echo.
echo 步骤3: 安装NumPy (用于音频处理)
python -m pip install numpy>=1.21.0

echo.
echo 步骤4: 验证安装
echo 验证PyAudio...
python -c "import pyaudio; print('PyAudio版本:', pyaudio.__version__)"
echo 验证NumPy...
python -c "import numpy; print('NumPy版本:', numpy.__version__)"

echo.
echo 步骤5: 运行音频处理测试
python test_audio_processing.py

echo.
echo ================================================
echo 🎉 安装完成！
echo ================================================
echo.
echo 使用方法:
echo   python cloud_voip_client.py --server SERVER_IP --name YOUR_NAME
echo.
echo 🆕 新功能:
echo   - 智能回声消除 (Echo Cancellation)
echo   - 噪声抑制 (Noise Suppression)  
echo   - 自动增益控制 (Auto Gain Control)
echo   - 语音活动检测 (Voice Activity Detection)
echo   - 实时音频设置调整
echo   - 调试模式和音频诊断
echo.
echo 🛠️ 故障排除工具:
echo   python audio_quick_fix.py       - 快速修复常见问题
echo   python audio_diagnostic.py      - 详细音频诊断
echo.
echo 📁 重要文件:
echo   audio_config.json              - 配置文件
echo   md\ECHO_SUPPRESSION_GUIDE.md   - 详细使用指南
echo.
echo ⚠️ 常见问题解决:
echo   1. 如果启用回声消除后没有声音:
echo      运行: python audio_quick_fix.py
echo      选择选项1进行修复
echo.
echo   2. 如果声音断断续续:
echo      运行: python audio_quick_fix.py  
echo      选择选项2进行修复
echo.
echo   3. 如果需要保守配置:
echo      运行: python audio_quick_fix.py
echo      选择选项3应用保守设置
echo.
echo   4. 实时调试:
echo      在客户端中输入 'audio' 命令
echo      选择调试模式查看处理详情
echo.
pause
