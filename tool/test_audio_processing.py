#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
音频处理测试脚本
测试啸叫抑制功能
"""

import sys
import os
import time
import numpy as np

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

try:
    from cloud_voip_client import CloudVoIPClient
    import pyaudio
    AUDIO_AVAILABLE = True
except ImportError as e:
    print(f"导入错误: {e}")
    AUDIO_AVAILABLE = False

def test_audio_processing():
    """测试音频处理功能"""
    print("🧪 开始音频处理测试...")
    
    if not AUDIO_AVAILABLE:
        print("❌ 音频库不可用，跳过测试")
        return False
    
    # 创建客户端实例（用于测试音频处理）
    client = CloudVoIPClient("127.0.0.1", "TestClient")
    
    # 生成测试音频数据
    duration = 1.0  # 1秒
    sample_rate = 16000
    samples = int(duration * sample_rate)
    
    print(f"📊 生成测试音频数据: {samples} 样本, {sample_rate}Hz")
    
    # 生成不同类型的测试信号
    test_signals = {
        "静音": np.zeros(samples, dtype=np.float32),
        "正弦波": np.sin(2 * np.pi * 440 * np.arange(samples) / sample_rate).astype(np.float32),
        "白噪声": np.random.normal(0, 0.1, samples).astype(np.float32),
        "高音量正弦波": np.sin(2 * np.pi * 880 * np.arange(samples) / sample_rate).astype(np.float32) * 2.0,
    }
    
    # 测试每种信号
    for signal_name, signal in test_signals.items():
        print(f"\n🔊 测试信号: {signal_name}")
        
        # 转换为字节数据
        audio_bytes = (signal * 32767).astype(np.int16).tobytes()
        
        # 测试噪声门
        print("  测试噪声门...")
        processed = client.apply_noise_gate(audio_bytes)
        processed_samples = np.frombuffer(processed, dtype=np.int16).astype(np.float32) / 32767.0
        original_rms = np.sqrt(np.mean(signal**2))
        processed_rms = np.sqrt(np.mean(processed_samples**2))
        print(f"    原始RMS: {original_rms:.4f}, 处理后RMS: {processed_rms:.4f}")
        
        # 测试自动增益控制
        print("  测试自动增益控制...")
        processed = client.apply_auto_gain_control(audio_bytes)
        processed_samples = np.frombuffer(processed, dtype=np.int16).astype(np.float32) / 32767.0
        processed_rms = np.sqrt(np.mean(processed_samples**2))
        print(f"    AGC后RMS: {processed_rms:.4f}")
        
        # 测试语音活动检测
        print("  测试语音活动检测...")
        has_voice = client.detect_voice_activity(audio_bytes)
        print(f"    检测结果: {'有语音活动' if has_voice else '无语音活动'}")
        
        # 测试音量调整
        print("  测试音量调整...")
        volume_adjusted = client.adjust_volume(audio_bytes, 0.5)
        adjusted_samples = np.frombuffer(volume_adjusted, dtype=np.int16).astype(np.float32) / 32767.0
        adjusted_rms = np.sqrt(np.mean(adjusted_samples**2))
        print(f"    50%音量后RMS: {adjusted_rms:.4f}")
    
    print("\n✅ 音频处理测试完成")
    return True

def test_configuration():
    """测试配置加载"""
    print("\n🔧 测试配置加载...")
    
    client = CloudVoIPClient("127.0.0.1", "TestClient")
    
    print(f"回声消除: {'✅' if client.echo_cancellation else '❌'}")
    print(f"噪声抑制: {'✅' if client.noise_suppression else '❌'}")
    print(f"自动增益控制: {'✅' if client.auto_gain_control else '❌'}")
    print(f"语音活动检测: {'✅' if client.voice_activity_detection else '❌'}")
    print(f"输入音量: {client.input_volume}")
    print(f"输出音量: {client.output_volume}")
    print(f"噪声门阈值: {client.noise_gate_threshold}")
    
    print("✅ 配置测试完成")

def performance_test():
    """性能测试"""
    print("\n⏱️ 性能测试...")
    
    if not AUDIO_AVAILABLE:
        print("❌ 音频库不可用，跳过性能测试")
        return
    
    client = CloudVoIPClient("127.0.0.1", "TestClient")
    
    # 生成测试数据
    samples = 1024  # 一个chunk的大小
    test_audio = (np.random.normal(0, 0.1, samples) * 32767).astype(np.int16).tobytes()
    
    # 测试处理速度
    iterations = 1000
    start_time = time.time()
    
    for i in range(iterations):
        processed = client.process_input_audio(test_audio)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"处理 {iterations} 个音频块用时: {duration:.3f}秒")
    print(f"平均每块处理时间: {duration/iterations*1000:.2f}毫秒")
    print(f"实时性能评估: {'✅ 良好' if duration/iterations < 0.001 else '⚠️ 需优化'}")
    
    print("✅ 性能测试完成")

def main():
    """主测试函数"""
    print("🎵 VoIP客户端音频处理测试套件")
    print("=" * 50)
    
    try:
        # 配置测试
        test_configuration()
        
        # 音频处理测试
        if test_audio_processing():
            # 性能测试
            performance_test()
        
        print("\n🎉 所有测试完成！")
        
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")

if __name__ == "__main__":
    main()
