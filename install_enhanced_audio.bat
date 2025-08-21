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
echo 新功能:
echo   - 回声消除 (Echo Cancellation)
echo   - 噪声抑制 (Noise Suppression)  
echo   - 自动增益控制 (Auto Gain Control)
echo   - 语音活动检测 (Voice Activity Detection)
echo   - 实时音频设置调整
echo.
echo 配置文件: audio_config.json
echo 使用指南: md\ECHO_SUPPRESSION_GUIDE.md
echo.
echo 故障排除:
echo   - 如果仍有啸叫，请使用耳机或降低音量
echo   - 在客户端中输入 'audio' 命令调整设置
echo   - 参考使用指南进行详细配置
echo.
pause
