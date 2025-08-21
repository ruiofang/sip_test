#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置文件加载
验证 PyInstaller 打包后是否能正确从外部读取配置文件
"""

import sys
import os
import json


def get_config_path(filename):
    """
    获取配置文件的正确路径
    兼容PyInstaller打包后的环境
    """
    if getattr(sys, 'frozen', False):
        # 如果是PyInstaller打包的可执行文件
        base_path = os.path.dirname(sys.executable)
    else:
        # 如果是普通Python脚本
        base_path = os.path.dirname(__file__)
    
    return os.path.join(base_path, filename)


def test_audio_config():
    """测试音频配置文件加载"""
    try:
        config_path = get_config_path('audio_config.json')
        print(f"🔍 配置文件路径: {config_path}")
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            audio_settings = config.get('audio_settings', {})
            
            print("🎵 音频配置设置:")
            print(f"  - 回声消除: {audio_settings.get('echo_cancellation', '未设置')}")
            print(f"  - 噪声抑制: {audio_settings.get('noise_suppression', '未设置')}")
            print(f"  - 自动增益控制: {audio_settings.get('auto_gain_control', '未设置')}")
            print(f"  - 语音活动检测: {audio_settings.get('voice_activity_detection', '未设置')}")
            
            return True
        else:
            print(f"❌ 配置文件不存在: {config_path}")
            return False
            
    except Exception as e:
        print(f"❌ 加载音频配置失败: {e}")
        return False


def test_client_config():
    """测试客户端配置文件加载"""
    try:
        config_path = get_config_path('client_config.json')
        print(f"🔍 配置文件路径: {config_path}")
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            servers = config.get('servers', {})
            user = config.get('user', {})
            
            print("🖥️ 服务器配置:")
            for server_id, server_info in servers.items():
                print(f"  - {server_id}: {server_info.get('name', '未命名')} ({server_info.get('ip', '未设置')}:{server_info.get('port', '未设置')})")
                
            print("👤 用户配置:")
            print(f"  - 默认用户名: {user.get('default_name', '未设置')}")
            print(f"  - 上次使用服务器: {user.get('last_server', '未设置')}")
            
            return True
        else:
            print(f"❌ 配置文件不存在: {config_path}")
            return False
            
    except Exception as e:
        print(f"❌ 加载客户端配置失败: {e}")
        return False


def main():
    """主函数"""
    print("📋 测试配置文件外置加载")
    print("=" * 50)
    
    print(f"🐍 Python 执行环境: {sys.executable}")
    print(f"📦 是否为打包环境: {'是' if getattr(sys, 'frozen', False) else '否'}")
    print(f"📂 工作目录: {os.getcwd()}")
    print()
    
    # 测试音频配置
    print("1️⃣ 测试音频配置文件:")
    test_audio_config()
    print()
    
    # 测试客户端配置
    print("2️⃣ 测试客户端配置文件:")
    test_client_config()
    print()
    
    print("✅ 测试完成!")


if __name__ == "__main__":
    main()
