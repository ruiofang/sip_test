#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
音频问题快速修复工具
一键解决常见的音频问题
"""

import json
import os
import sys

class AudioQuickFix:
    def __init__(self):
        self.config_file = 'audio_config.json'
        self.config_path = os.path.join(os.path.dirname(__file__), self.config_file)
    
    def load_current_config(self):
        """加载当前配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return self.get_default_config()
    
    def get_default_config(self):
        """获取默认配置"""
        return {
            "audio_settings": {
                "echo_cancellation": True,
                "noise_suppression": True,
                "auto_gain_control": True,
                "voice_activity_detection": True,
                "input_volume": 0.7,
                "output_volume": 0.8,
                "noise_gate_threshold": 0.01,
                "echo_threshold": 0.6,
                "echo_suppression_factor": 0.7,
                "min_suppression": 0.3,
                "adaptive_threshold": True,
                "debug_audio_processing": False
            },
            "advanced_settings": {
                "chunk_size": 1024,
                "sample_rate": 16000,
                "channels": 1,
                "format": "paInt16"
            }
        }
    
    def save_config(self, config):
        """保存配置"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def fix_no_sound_issue(self):
        """修复没有声音的问题"""
        print("🔧 修复：启用回声消除后没有声音")
        
        config = self.load_current_config()
        
        # 调整回声消除参数
        audio_settings = config.setdefault("audio_settings", {})
        
        # 降低检测敏感度
        audio_settings["echo_threshold"] = 0.4  # 从默认0.6降到0.4
        audio_settings["min_suppression"] = 0.4  # 从默认0.3增加到0.4
        audio_settings["echo_suppression_factor"] = 0.6  # 从默认0.7降到0.6
        
        # 启用调试模式
        audio_settings["debug_audio_processing"] = True
        
        if self.save_config(config):
            print("✅ 配置已更新:")
            print("   - 回声检测阈值: 0.6 → 0.4 (更宽松)")
            print("   - 最小抑制比例: 0.3 → 0.4 (更保守)")
            print("   - 抑制强度: 0.7 → 0.6 (更轻)")
            print("   - 调试模式: 已启用")
            print("\n💡 请重启客户端使配置生效")
        else:
            print("❌ 配置更新失败")
    
    def fix_choppy_audio(self):
        """修复声音断断续续的问题"""
        print("🔧 修复：声音断断续续")
        
        config = self.load_current_config()
        audio_settings = config.setdefault("audio_settings", {})
        
        # 调整相关参数
        audio_settings["voice_activity_detection"] = False  # 关闭VAD
        audio_settings["noise_gate_threshold"] = 0.005  # 降低噪声门
        audio_settings["adaptive_threshold"] = True  # 启用自适应
        
        if self.save_config(config):
            print("✅ 配置已更新:")
            print("   - 语音活动检测: 已关闭")
            print("   - 噪声门阈值: 0.01 → 0.005 (更敏感)")
            print("   - 自适应阈值: 已启用")
            print("\n💡 请重启客户端使配置生效")
        else:
            print("❌ 配置更新失败")
    
    def conservative_config(self):
        """应用保守配置 - 确保基本功能"""
        print("🔧 应用保守配置 - 优先保证有声音")
        
        config = self.load_current_config()
        audio_settings = config.setdefault("audio_settings", {})
        
        # 保守设置
        audio_settings["echo_cancellation"] = False  # 暂时关闭回声消除
        audio_settings["noise_suppression"] = True
        audio_settings["auto_gain_control"] = True
        audio_settings["voice_activity_detection"] = False
        audio_settings["noise_gate_threshold"] = 0.005
        audio_settings["input_volume"] = 0.8
        audio_settings["output_volume"] = 0.8
        audio_settings["debug_audio_processing"] = False
        
        if self.save_config(config):
            print("✅ 保守配置已应用:")
            print("   - 回声消除: 已关闭")
            print("   - 语音活动检测: 已关闭")
            print("   - 噪声门阈值: 降低到0.005")
            print("   - 音量: 提升到0.8")
            print("\n💡 这个配置应该能确保有声音")
            print("💡 稳定后可以逐步启用其他功能")
        else:
            print("❌ 配置更新失败")
    
    def optimal_config(self):
        """应用优化配置 - 平衡所有功能"""
        print("🔧 应用优化配置 - 平衡功能和稳定性")
        
        config = self.load_current_config()
        audio_settings = config.setdefault("audio_settings", {})
        
        # 优化设置
        audio_settings["echo_cancellation"] = True
        audio_settings["noise_suppression"] = True
        audio_settings["auto_gain_control"] = True
        audio_settings["voice_activity_detection"] = True
        audio_settings["echo_threshold"] = 0.5  # 适中的检测阈值
        audio_settings["echo_suppression_factor"] = 0.65  # 适中的抑制强度
        audio_settings["min_suppression"] = 0.35  # 适中的最小抑制
        audio_settings["noise_gate_threshold"] = 0.01
        audio_settings["input_volume"] = 0.7
        audio_settings["output_volume"] = 0.8
        audio_settings["adaptive_threshold"] = True
        audio_settings["debug_audio_processing"] = False
        
        if self.save_config(config):
            print("✅ 优化配置已应用:")
            print("   - 所有功能: 已启用")
            print("   - 回声检测: 适中敏感度(0.5)")
            print("   - 抑制强度: 适中(0.65)")
            print("   - 最小抑制: 适中(0.35)")
            print("   - 自适应阈值: 已启用")
            print("\n💡 这是推荐的平衡配置")
        else:
            print("❌ 配置更新失败")
    
    def reset_to_default(self):
        """重置为默认配置"""
        print("🔧 重置为默认配置")
        
        config = self.get_default_config()
        
        if self.save_config(config):
            print("✅ 已重置为默认配置")
            print("\n💡 请重启客户端使配置生效")
        else:
            print("❌ 重置失败")
    
    def show_current_config(self):
        """显示当前配置"""
        print("📋 当前音频配置:")
        
        config = self.load_current_config()
        audio_settings = config.get("audio_settings", {})
        
        print("\n核心功能:")
        print(f"  回声消除: {'✅' if audio_settings.get('echo_cancellation', True) else '❌'}")
        print(f"  噪声抑制: {'✅' if audio_settings.get('noise_suppression', True) else '❌'}")
        print(f"  自动增益: {'✅' if audio_settings.get('auto_gain_control', True) else '❌'}")
        print(f"  语音检测: {'✅' if audio_settings.get('voice_activity_detection', True) else '❌'}")
        
        print("\n关键参数:")
        print(f"  输入音量: {audio_settings.get('input_volume', 0.7)}")
        print(f"  输出音量: {audio_settings.get('output_volume', 0.8)}")
        print(f"  噪声门阈值: {audio_settings.get('noise_gate_threshold', 0.01)}")
        
        if audio_settings.get('echo_cancellation', True):
            print(f"  回声检测阈值: {audio_settings.get('echo_threshold', 0.6)}")
            print(f"  抑制强度: {audio_settings.get('echo_suppression_factor', 0.7)}")
            print(f"  最小抑制: {audio_settings.get('min_suppression', 0.3)}")
        
        print(f"  调试模式: {'✅' if audio_settings.get('debug_audio_processing', False) else '❌'}")

def main():
    """主函数"""
    fixer = AudioQuickFix()
    
    while True:
        print("\n🛠️ VoIP音频问题快速修复工具")
        print("=" * 50)
        print("1. 修复：启用回声消除后没有声音")
        print("2. 修复：声音断断续续")
        print("3. 应用保守配置（优先保证有声音）")
        print("4. 应用优化配置（平衡功能）")
        print("5. 重置为默认配置")
        print("6. 显示当前配置")
        print("7. 运行音频诊断工具")
        print("0. 退出")
        print("=" * 50)
        
        try:
            choice = input("请选择修复方案 (0-7): ").strip()
            
            if choice == '0':
                print("👋 再见！")
                break
            elif choice == '1':
                fixer.fix_no_sound_issue()
            elif choice == '2':
                fixer.fix_choppy_audio()
            elif choice == '3':
                fixer.conservative_config()
            elif choice == '4':
                fixer.optimal_config()
            elif choice == '5':
                fixer.reset_to_default()
            elif choice == '6':
                fixer.show_current_config()
            elif choice == '7':
                print("🔍 启动音频诊断工具...")
                try:
                    import audio_diagnostic
                    diagnostic = audio_diagnostic.AudioDiagnostic()
                    diagnostic.run_full_diagnostic()
                except ImportError:
                    print("❌ 音频诊断工具不可用")
                except Exception as e:
                    print(f"❌ 诊断工具错误: {e}")
            else:
                print("❌ 无效选择")
                
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 操作出错: {e}")

if __name__ == "__main__":
    main()
