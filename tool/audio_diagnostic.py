#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
音频问题诊断工具
帮助诊断和解决VoIP客户端音频问题
"""

import sys
import os
import json
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

class AudioDiagnostic:
    def __init__(self):
        self.client = None
        self.test_results = {}
        
    def run_full_diagnostic(self):
        """运行完整的音频诊断"""
        print("🔍 VoIP客户端音频诊断工具")
        print("=" * 60)
        
        if not AUDIO_AVAILABLE:
            print("❌ 音频库不可用，无法进行诊断")
            return
        
        # 创建测试客户端
        self.client = CloudVoIPClient("127.0.0.1", "DiagnosticClient")
        
        # 执行各项测试
        tests = [
            ("配置检查", self.check_configuration),
            ("音频设备检查", self.check_audio_devices),
            ("基础音频处理", self.test_basic_audio_processing),
            ("回声消除测试", self.test_echo_cancellation),
            ("语音活动检测", self.test_voice_activity_detection),
            ("性能测试", self.test_performance)
        ]
        
        for test_name, test_func in tests:
            print(f"\n🧪 {test_name}...")
            try:
                result = test_func()
                self.test_results[test_name] = result
                print(f"✅ {test_name}: {'通过' if result else '失败'}")
            except Exception as e:
                print(f"❌ {test_name}: 出错 - {e}")
                self.test_results[test_name] = False
        
        # 生成报告
        self.generate_report()
        
    def check_configuration(self):
        """检查配置"""
        print("  检查音频配置参数...")
        
        issues = []
        
        # 检查回声消除参数
        if self.client.echo_threshold > 0.8:
            issues.append("回声检测阈值过高，可能导致正常语音被误判")
        
        if self.client.echo_suppression_factor > 0.9:
            issues.append("回声抑制强度过高，可能导致声音过度衰减")
            
        if self.client.min_suppression < 0.1:
            issues.append("最小抑制比例过低，可能导致完全静音")
            
        if self.client.noise_gate_threshold > 0.05:
            issues.append("噪声门阈值过高，可能切断正常语音")
        
        if issues:
            print("  ⚠️ 发现配置问题:")
            for issue in issues:
                print(f"    - {issue}")
            return False
        else:
            print("  ✅ 配置参数正常")
            return True
    
    def check_audio_devices(self):
        """检查音频设备"""
        try:
            audio_instance = pyaudio.PyAudio()
            
            print(f"  可用音频设备数量: {audio_instance.get_device_count()}")
            
            # 检查默认设备
            try:
                default_input = audio_instance.get_default_input_device_info()
                print(f"  默认输入设备: {default_input['name']}")
            except:
                print("  ⚠️ 无法获取默认输入设备")
                return False
            
            try:
                default_output = audio_instance.get_default_output_device_info()
                print(f"  默认输出设备: {default_output['name']}")
            except:
                print("  ⚠️ 无法获取默认输出设备")
                return False
            
            audio_instance.terminate()
            return True
            
        except Exception as e:
            print(f"  ❌ 音频设备检查失败: {e}")
            return False
    
    def test_basic_audio_processing(self):
        """测试基础音频处理"""
        print("  生成测试信号...")
        
        # 生成不同类型的测试信号
        duration = 0.5  # 0.5秒
        samples = int(duration * self.client.rate)
        
        test_signals = {
            "静音": np.zeros(samples, dtype=np.float32),
            "低音量语音": np.sin(2 * np.pi * 300 * np.arange(samples) / self.client.rate).astype(np.float32) * 0.1,
            "正常音量语音": np.sin(2 * np.pi * 500 * np.arange(samples) / self.client.rate).astype(np.float32) * 0.3,
            "高音量语音": np.sin(2 * np.pi * 700 * np.arange(samples) / self.client.rate).astype(np.float32) * 0.8,
        }
        
        processing_ok = True
        
        for signal_name, signal in test_signals.items():
            print(f"    测试 {signal_name}...")
            
            # 转换为字节数据
            audio_bytes = (signal * 32767).astype(np.int16).tobytes()
            
            # 处理音频
            processed = self.client.process_input_audio(audio_bytes)
            
            # 分析处理结果
            original_samples = signal
            processed_samples = np.frombuffer(processed, dtype=np.int16).astype(np.float32) / 32767.0
            
            original_rms = np.sqrt(np.mean(original_samples**2))
            processed_rms = np.sqrt(np.mean(processed_samples**2))
            
            print(f"      原始RMS: {original_rms:.4f}, 处理后RMS: {processed_rms:.4f}")
            
            # 检查是否过度抑制
            if original_rms > 0.01 and processed_rms < 0.001:
                print(f"      ⚠️ {signal_name} 被过度抑制")
                processing_ok = False
            elif original_rms > 0.1 and (processed_rms / original_rms) < 0.05:
                print(f"      ⚠️ {signal_name} 抑制过强")
                processing_ok = False
            else:
                print(f"      ✅ {signal_name} 处理正常")
        
        return processing_ok
    
    def test_echo_cancellation(self):
        """测试回声消除"""
        print("  模拟回声场景...")
        
        # 生成原始语音信号
        duration = 1.0
        samples = int(duration * self.client.rate)
        voice_signal = np.sin(2 * np.pi * 440 * np.arange(samples) / self.client.rate).astype(np.float32) * 0.5
        
        # 模拟回声信号（延迟+衰减的原始信号）
        echo_delay = 0.1  # 100ms延迟
        delay_samples = int(echo_delay * self.client.rate)
        echo_signal = np.zeros_like(voice_signal)
        if delay_samples < len(voice_signal):
            echo_signal[delay_samples:] = voice_signal[:-delay_samples] * 0.3  # 30%强度的回声
        
        # 混合信号（语音+回声）
        mixed_signal = voice_signal + echo_signal
        
        # 准备参考信号（模拟扬声器输出）
        reference_signal = voice_signal * 0.8  # 稍微衰减的参考信号
        
        # 转换为字节数据
        mixed_bytes = (mixed_signal * 32767).astype(np.int16).tobytes()
        reference_bytes = (reference_signal * 32767).astype(np.int16).tobytes()
        
        # 添加参考信号到历史记录
        self.client.audio_history = [reference_bytes]
        
        # 应用回声消除
        processed = self.client.apply_echo_cancellation(mixed_bytes, reference_bytes)
        processed_samples = np.frombuffer(processed, dtype=np.int16).astype(np.float32) / 32767.0
        
        # 分析结果
        original_rms = np.sqrt(np.mean(mixed_signal**2))
        processed_rms = np.sqrt(np.mean(processed_samples**2))
        voice_rms = np.sqrt(np.mean(voice_signal**2))
        
        print(f"    原始混合信号RMS: {original_rms:.4f}")
        print(f"    处理后信号RMS: {processed_rms:.4f}")
        print(f"    纯语音信号RMS: {voice_rms:.4f}")
        
        # 判断回声消除效果
        suppression_ratio = processed_rms / original_rms if original_rms > 0 else 0
        voice_preservation = processed_rms / voice_rms if voice_rms > 0 else 0
        
        print(f"    抑制比率: {1-suppression_ratio:.2f}")
        print(f"    语音保留率: {voice_preservation:.2f}")
        
        # 效果评估
        if voice_preservation < 0.1:
            print("    ❌ 语音被过度抑制")
            return False
        elif voice_preservation > 0.3 and suppression_ratio < 0.8:
            print("    ✅ 回声消除效果良好")
            return True
        else:
            print("    ⚠️ 回声消除效果一般")
            return True
    
    def test_voice_activity_detection(self):
        """测试语音活动检测"""
        print("  测试语音活动检测准确性...")
        
        test_cases = [
            ("纯静音", np.zeros(1024, dtype=np.float32), False),
            ("白噪声", np.random.normal(0, 0.05, 1024).astype(np.float32), False),
            ("语音信号", np.sin(2 * np.pi * 300 * np.arange(1024) / self.client.rate).astype(np.float32) * 0.3, True),
            ("高频噪声", np.sin(2 * np.pi * 8000 * np.arange(1024) / self.client.rate).astype(np.float32) * 0.2, False),
        ]
        
        correct_detections = 0
        
        for case_name, signal, expected in test_cases:
            audio_bytes = (signal * 32767).astype(np.int16).tobytes()
            detected = self.client.detect_voice_activity(audio_bytes)
            
            if detected == expected:
                print(f"    ✅ {case_name}: 检测正确 ({'有语音' if detected else '无语音'})")
                correct_detections += 1
            else:
                print(f"    ❌ {case_name}: 检测错误 (检测: {'有语音' if detected else '无语音'}, 期望: {'有语音' if expected else '无语音'})")
        
        accuracy = correct_detections / len(test_cases)
        print(f"    检测准确率: {accuracy:.1%}")
        
        return accuracy >= 0.75  # 至少75%准确率
    
    def test_performance(self):
        """测试性能"""
        print("  测试音频处理性能...")
        
        # 生成测试数据
        test_audio = (np.random.normal(0, 0.1, 1024) * 32767).astype(np.int16).tobytes()
        
        # 测试处理速度
        iterations = 100
        start_time = time.time()
        
        for i in range(iterations):
            self.client.process_input_audio(test_audio)
        
        end_time = time.time()
        duration = end_time - start_time
        avg_time = duration / iterations * 1000  # 毫秒
        
        print(f"    平均处理时间: {avg_time:.2f}ms/帧")
        
        # 实时性要求：处理时间应该小于帧时间的50%
        frame_duration = 1024 / self.client.rate * 1000  # 帧持续时间（毫秒）
        max_allowed = frame_duration * 0.5
        
        print(f"    帧持续时间: {frame_duration:.2f}ms")
        print(f"    允许最大处理时间: {max_allowed:.2f}ms")
        
        if avg_time <= max_allowed:
            print(f"    ✅ 性能良好")
            return True
        else:
            print(f"    ⚠️ 处理时间过长，可能影响实时性")
            return False
    
    def generate_report(self):
        """生成诊断报告"""
        print(f"\n{'='*60}")
        print("📋 诊断报告")
        print(f"{'='*60}")
        
        passed_tests = sum(1 for result in self.test_results.values() if result)
        total_tests = len(self.test_results)
        
        print(f"总体结果: {passed_tests}/{total_tests} 项测试通过")
        
        print(f"\n详细结果:")
        for test_name, result in self.test_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {test_name}: {status}")
        
        print(f"\n🛠️ 建议:")
        
        # 根据测试结果给出建议
        if not self.test_results.get("回声消除测试", True):
            print("  - 调整回声消除参数:")
            print("    * 降低echo_threshold到0.5")
            print("    * 增加min_suppression到0.4")
            print("    * 减少echo_suppression_factor到0.6")
        
        if not self.test_results.get("语音活动检测", True):
            print("  - 优化语音活动检测:")
            print("    * 关闭voice_activity_detection")
            print("    * 或调整检测阈值")
        
        if not self.test_results.get("基础音频处理", True):
            print("  - 基础音频处理问题:")
            print("    * 检查noise_gate_threshold设置")
            print("    * 确认音频设备工作正常")
            print("    * 启用debug_audio_processing查看详情")
        
        if not self.test_results.get("性能测试", True):
            print("  - 性能优化:")
            print("    * 关闭不必要的音频处理功能")
            print("    * 增加chunk_size以减少处理频率")
            print("    * 检查系统负载")
        
        # 推荐配置
        print(f"\n💡 针对问题的推荐配置:")
        if passed_tests < total_tests:
            print("  # 保守配置（优先保证有声音）")
            print('  "echo_cancellation": false,')
            print('  "noise_suppression": true,')
            print('  "auto_gain_control": true,')
            print('  "voice_activity_detection": false,')
            print('  "noise_gate_threshold": 0.005')
            print()
            print("  # 如果需要启用回声消除")
            print('  "echo_threshold": 0.5,')
            print('  "echo_suppression_factor": 0.6,')
            print('  "min_suppression": 0.4')

def main():
    """主函数"""
    diagnostic = AudioDiagnostic()
    try:
        diagnostic.run_full_diagnostic()
    except KeyboardInterrupt:
        print("\n⏹️ 诊断被用户中断")
    except Exception as e:
        print(f"\n❌ 诊断出错: {e}")

if __name__ == "__main__":
    main()
