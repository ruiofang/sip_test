#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VoIP客户端交互式启动脚本
提供友好的用户界面和功能选择

功能：
- 快速连接服务器
- 服务器连接测试
- 音频功能测试
- 配置管理
- 帮助文档

作者: GitHub Copilot
日期: 2025年8月21日
"""

import os
import sys
import json
import subprocess
import socket
import time
import shutil
from typing import Dict, Any, Optional

# 添加colorama导入用于彩色输出
try:
    from colorama import Fore, Back, Style, init
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    # 如果colorama不可用，创建空的替代品
    class ColorFallback:
        def __getattr__(self, name):
            return ""
    
    Fore = Back = Style = ColorFallback()
    COLORS_AVAILABLE = False

class VoIPClientLauncher:
    def __init__(self):
        self.config_file = "client_config.json"
        self.config = self.load_config()
        self.python_cmd = self.get_python_command()
    
    def get_python_command(self):
        """获取Python命令"""
        # 直接使用系统Python，不使用虚拟环境
        if shutil.which("python3"):
            return "python3"
        elif shutil.which("python"):
            return "python"
        else:
            print(f"{Fore.RED}❌ 未找到Python解释器{Style.RESET_ALL}")
            return None
    
    def load_config(self):
        """加载配置文件"""
        default_config = {
            "servers": {
                "default": {
                    "name": "默认服务器",
                    "ip": "120.27.145.121",
                    "port": 5060
                }
            },
            "user": {
                "default_name": "用户",
                "last_server": "default"
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置
                    for key in default_config:
                        if key not in config:
                            config[key] = default_config[key]
                    return config
            else:
                return default_config
        except Exception as e:
            print(f"⚠️  加载配置文件失败: {e}")
            return default_config
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ 保存配置文件失败: {e}")
            return False
    
    def print_header(self):
        """打印程序头部"""
        print("\n" + "=" * 60)
        print("🎙️  VoIP云端语音通话系统 - 客户端启动器")
        print("=" * 60)
        print("📞 支持语音通话、文本消息、多用户连接")
        print("🔧 版本: v1.2.0 | 作者: GitHub Copilot")
        print("=" * 60)
    
    def print_menu(self):
        """打印主菜单"""
        print("\n📋 功能菜单:")
        print("1. 🚀 快速连接服务器")
        print("2. 🔧 服务器管理")
        print("3. 🧪 连接测试")
        print("4. 🎵 音频测试")
        print("5. ⚙️  配置管理")
        print("6. 📖 使用帮助")
        print("7. ❌ 退出程序")
        print("-" * 60)
    
    def quick_connect(self):
        """快速连接服务器"""
        print("\n🚀 快速连接服务器")
        print("-" * 40)
        
        # 显示可用服务器
        print("可用服务器:")
        for key, server in self.config["servers"].items():
            marker = "👉" if key == self.config["user"]["last_server"] else "  "
            print(f"{marker} {key}: {server['name']} ({server['ip']}:{server['port']})")
        
        print("\n选项:")
        print("1. 使用默认服务器")
        print("2. 选择其他服务器") 
        print("3. 输入新服务器地址")
        print("4. 返回主菜单")
        
        choice = input("\n请选择 (1-4): ").strip()
        
        if choice == "1":
            last_server = self.config["user"]["last_server"]
            server_info = self.config["servers"][last_server]
            self.connect_to_server(server_info["ip"], server_info["port"])
        
        elif choice == "2":
            self.select_server()
        
        elif choice == "3":
            self.add_new_server()
        
        elif choice == "4":
            return
        
        else:
            print("❌ 无效选择，请重新输入")
            self.quick_connect()
    
    def select_server(self):
        """选择服务器"""
        print("\n🔧 选择服务器")
        print("-" * 30)
        
        servers = list(self.config["servers"].keys())
        for i, key in enumerate(servers, 1):
            server = self.config["servers"][key]
            print(f"{i}. {server['name']} ({server['ip']}:{server['port']})")
        
        try:
            choice = int(input(f"\n请选择服务器 (1-{len(servers)}): "))
            if 1 <= choice <= len(servers):
                server_key = servers[choice - 1]
                server_info = self.config["servers"][server_key]
                self.config["user"]["last_server"] = server_key
                self.save_config()
                self.connect_to_server(server_info["ip"], server_info["port"])
            else:
                print("❌ 选择超出范围")
        except ValueError:
            print("❌ 请输入数字")
    
    def add_new_server(self):
        """添加新服务器"""
        print("\n➕ 添加新服务器")
        print("-" * 30)
        
        name = input("服务器名称: ").strip()
        if not name:
            name = "新服务器"
        
        ip = input("服务器IP地址: ").strip()
        if not ip:
            print("❌ IP地址不能为空")
            return
        
        port_str = input("端口号 (默认5060): ").strip()
        try:
            port = int(port_str) if port_str else 5060
        except ValueError:
            print("❌ 端口号必须是数字")
            return
        
        # 添加到配置
        server_key = f"server_{len(self.config['servers'])}"
        self.config["servers"][server_key] = {
            "name": name,
            "ip": ip,
            "port": port
        }
        self.config["user"]["last_server"] = server_key
        
        if self.save_config():
            print(f"✅ 服务器 '{name}' 添加成功")
            self.connect_to_server(ip, port)
        else:
            print("❌ 保存服务器配置失败")
    
    def connect_to_server(self, ip: str, port: int):
        """连接到指定服务器"""
        print(f"\n🔗 正在连接服务器 {ip}:{port}")
        
        # 获取用户名
        default_name = self.config["user"]["default_name"]
        name = input(f"请输入用户名 (默认: {default_name}): ").strip()
        if not name:
            name = default_name
        
        # 更新默认用户名
        if name != default_name:
            self.config["user"]["default_name"] = name
            self.save_config()
        
        # 启动客户端
        cmd = [
            self.python_cmd,
            "cloud_voip_client.py",
            "--server", ip,
            "--name", name
        ]
        
        print(f"🚀 启动命令: {' '.join(cmd)}")
        print("💡 提示: 使用 Ctrl+C 可以退出客户端")
        print("-" * 40)
        
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            print("\n👋 客户端已退出")
        except Exception as e:
            print(f"❌ 启动失败: {e}")
    
    def server_management(self):
        """服务器管理"""
        print("\n🔧 服务器管理")
        print("-" * 40)
        
        while True:
            print("\n当前服务器列表:")
            for key, server in self.config["servers"].items():
                marker = "👉" if key == self.config["user"]["last_server"] else "  "
                print(f"{marker} {key}: {server['name']} ({server['ip']}:{server['port']})")
            
            print("\n操作选项:")
            print("1. 添加服务器")
            print("2. 删除服务器")
            print("3. 编辑服务器")
            print("4. 设为默认服务器")
            print("5. 返回主菜单")
            
            choice = input("\n请选择操作 (1-5): ").strip()
            
            if choice == "1":
                self.add_new_server()
                break
            elif choice == "2":
                self.delete_server()
            elif choice == "3":
                self.edit_server()
            elif choice == "4":
                self.set_default_server()
            elif choice == "5":
                break
            else:
                print("❌ 无效选择")
    
    def delete_server(self):
        """删除服务器"""
        if len(self.config["servers"]) <= 1:
            print("❌ 至少需要保留一个服务器")
            return
        
        servers = list(self.config["servers"].keys())
        print("\n选择要删除的服务器:")
        for i, key in enumerate(servers, 1):
            server = self.config["servers"][key]
            print(f"{i}. {server['name']} ({key})")
        
        try:
            choice = int(input(f"\n请选择 (1-{len(servers)}): "))
            if 1 <= choice <= len(servers):
                server_key = servers[choice - 1]
                server_name = self.config["servers"][server_key]["name"]
                
                confirm = input(f"确认删除服务器 '{server_name}'? (y/N): ").strip().lower()
                if confirm == 'y':
                    del self.config["servers"][server_key]
                    
                    # 如果删除的是默认服务器，设置新的默认服务器
                    if self.config["user"]["last_server"] == server_key:
                        self.config["user"]["last_server"] = list(self.config["servers"].keys())[0]
                    
                    if self.save_config():
                        print(f"✅ 服务器 '{server_name}' 已删除")
                    else:
                        print("❌ 删除失败")
                else:
                    print("取消删除")
            else:
                print("❌ 选择超出范围")
        except ValueError:
            print("❌ 请输入数字")
    
    def edit_server(self):
        """编辑服务器"""
        servers = list(self.config["servers"].keys())
        print("\n选择要编辑的服务器:")
        for i, key in enumerate(servers, 1):
            server = self.config["servers"][key]
            print(f"{i}. {server['name']} ({key})")
        
        try:
            choice = int(input(f"\n请选择 (1-{len(servers)}): "))
            if 1 <= choice <= len(servers):
                server_key = servers[choice - 1]
                server = self.config["servers"][server_key]
                
                print(f"\n编辑服务器: {server['name']}")
                
                name = input(f"服务器名称 (当前: {server['name']}): ").strip()
                if name:
                    server['name'] = name
                
                ip = input(f"IP地址 (当前: {server['ip']}): ").strip()
                if ip:
                    server['ip'] = ip
                
                port_str = input(f"端口号 (当前: {server['port']}): ").strip()
                if port_str:
                    try:
                        server['port'] = int(port_str)
                    except ValueError:
                        print("❌ 端口号格式错误，保持原值")
                
                if self.save_config():
                    print("✅ 服务器信息已更新")
                else:
                    print("❌ 保存失败")
            else:
                print("❌ 选择超出范围")
        except ValueError:
            print("❌ 请输入数字")
    
    def set_default_server(self):
        """设置默认服务器"""
        servers = list(self.config["servers"].keys())
        print("\n选择默认服务器:")
        for i, key in enumerate(servers, 1):
            server = self.config["servers"][key]
            marker = "👉" if key == self.config["user"]["last_server"] else "  "
            print(f"{i}.{marker} {server['name']}")
        
        try:
            choice = int(input(f"\n请选择 (1-{len(servers)}): "))
            if 1 <= choice <= len(servers):
                server_key = servers[choice - 1]
                self.config["user"]["last_server"] = server_key
                
                if self.save_config():
                    server_name = self.config["servers"][server_key]["name"]
                    print(f"✅ 默认服务器已设为: {server_name}")
                else:
                    print("❌ 保存失败")
            else:
                print("❌ 选择超出范围")
        except ValueError:
            print("❌ 请输入数字")
    
    def connection_test(self):
        """连接测试"""
        print("\n🧪 连接测试")
        print("-" * 40)
        
        print("选择测试类型:")
        print("1. 测试默认服务器")
        print("2. 测试指定服务器")
        print("3. 返回主菜单")
        
        choice = input("\n请选择 (1-3): ").strip()
        
        if choice == "1":
            last_server = self.config["user"]["last_server"]
            server_info = self.config["servers"][last_server]
            self.test_server_connection(server_info["ip"], server_info["port"])
        
        elif choice == "2":
            ip = input("请输入服务器IP: ").strip()
            if not ip:
                print("❌ IP地址不能为空")
                return
            
            port_str = input("请输入端口号 (默认5060): ").strip()
            try:
                port = int(port_str) if port_str else 5060
                self.test_server_connection(ip, port)
            except ValueError:
                print("❌ 端口号必须是数字")
        
        elif choice == "3":
            return
        else:
            print("❌ 无效选择")
    
    def test_server_connection(self, ip: str, port: int):
        """测试服务器连接"""
        print(f"\n🔍 测试连接到 {ip}:{port}")
        print("-" * 30)
        
        # TCP连接测试
        print("1. TCP连接测试...")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                print("   ✅ TCP连接正常")
            else:
                print("   ❌ TCP连接失败")
                return
        except Exception as e:
            print(f"   ❌ TCP连接异常: {e}")
            return
        
        # UDP连接测试
        print("2. UDP连接测试...")
        try:
            cmd = [self.python_cmd, "debug_connection.py"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if "TCP连接测试完成" in result.stdout:
                print("   ✅ UDP音频端口可达")
            else:
                print("   ⚠️  UDP测试超时")
        except subprocess.TimeoutExpired:
            print("   ⚠️  UDP测试超时")
        except Exception as e:
            print(f"   ❌ UDP测试异常: {e}")
        
        print("\n✅ 连接测试完成")
        input("按回车键继续...")
    
    def audio_test(self):
        """音频功能测试"""
        print("\n🎵 音频功能测试")
        print("-" * 40)
        
        print("选择测试类型:")
        print("1. 音频设备检测")
        print("2. 音频传输测试")
        print("3. 返回主菜单")
        
        choice = input("\n请选择 (1-3): ").strip()
        
        if choice == "1":
            self.test_audio_devices()
        elif choice == "2":
            self.test_audio_transmission()
        elif choice == "3":
            return
        else:
            print("❌ 无效选择")
    
    def test_audio_devices(self):
        """测试音频设备"""
        print("\n🎤 音频设备检测")
        print("-" * 30)
        
        try:
            import pyaudio
            
            print("检测音频系统...")
            audio = pyaudio.PyAudio()
            
            print(f"可用音频设备数量: {audio.get_device_count()}")
            
            # 查找默认输入输出设备
            try:
                default_input = audio.get_default_input_device_info()
                print(f"✅ 默认输入设备: {default_input['name']}")
            except:
                print("❌ 未找到默认输入设备")
            
            try:
                default_output = audio.get_default_output_device_info()
                print(f"✅ 默认输出设备: {default_output['name']}")
            except:
                print("❌ 未找到默认输出设备")
            
            audio.terminate()
            print("\n✅ 音频设备检测完成")
            
        except ImportError:
            print("❌ PyAudio未安装，请先安装音频依赖:")
            print("   pip install PyAudio")
        except Exception as e:
            print(f"❌ 音频设备检测失败: {e}")
        
        input("\n按回车键继续...")
    
    def test_audio_transmission(self):
        """测试音频传输"""
        print("\n📡 音频传输测试")
        print("-" * 30)
        
        if not os.path.exists("test_audio.py"):
            print("❌ 音频测试脚本不存在")
            return
        
        try:
            print("🔄 运行音频传输测试...")
            cmd = [self.python_cmd, "test_audio.py"]
            subprocess.run(cmd)
        except Exception as e:
            print(f"❌ 音频测试失败: {e}")
        
        input("\n按回车键继续...")
    
    def config_management(self):
        """配置管理"""
        print("\n⚙️  配置管理")
        print("-" * 40)
        
        while True:
            print("\n当前配置:")
            print(f"默认用户名: {self.config['user']['default_name']}")
            print(f"默认服务器: {self.config['user']['last_server']}")
            print(f"服务器数量: {len(self.config['servers'])}")
            
            print("\n操作选项:")
            print("1. 修改默认用户名")
            print("2. 查看完整配置")
            print("3. 重置配置")
            print("4. 导出配置")
            print("5. 导入配置")
            print("6. 返回主菜单")
            
            choice = input("\n请选择 (1-6): ").strip()
            
            if choice == "1":
                name = input(f"请输入新的默认用户名 (当前: {self.config['user']['default_name']}): ").strip()
                if name:
                    self.config['user']['default_name'] = name
                    if self.save_config():
                        print("✅ 用户名已更新")
                    else:
                        print("❌ 保存失败")
            
            elif choice == "2":
                print("\n📄 完整配置:")
                print(json.dumps(self.config, indent=2, ensure_ascii=False))
                input("\n按回车键继续...")
            
            elif choice == "3":
                confirm = input("确认重置所有配置? (y/N): ").strip().lower()
                if confirm == 'y':
                    self.config = {
                        "servers": {
                            "default": {
                                "name": "默认服务器",
                                "ip": "120.27.145.121",
                                "port": 5060
                            }
                        },
                        "user": {
                            "default_name": "用户",
                            "last_server": "default"
                        }
                    }
                    if self.save_config():
                        print("✅ 配置已重置")
                    else:
                        print("❌ 重置失败")
            
            elif choice == "4":
                filename = input("导出文件名 (默认: config_backup.json): ").strip()
                if not filename:
                    filename = "config_backup.json"
                
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.config, f, indent=2, ensure_ascii=False)
                    print(f"✅ 配置已导出到: {filename}")
                except Exception as e:
                    print(f"❌ 导出失败: {e}")
            
            elif choice == "5":
                filename = input("导入文件名: ").strip()
                if filename and os.path.exists(filename):
                    try:
                        with open(filename, 'r', encoding='utf-8') as f:
                            imported_config = json.load(f)
                        
                        # 验证配置格式
                        if "servers" in imported_config and "user" in imported_config:
                            self.config = imported_config
                            if self.save_config():
                                print("✅ 配置已导入")
                            else:
                                print("❌ 保存失败")
                        else:
                            print("❌ 配置文件格式错误")
                    except Exception as e:
                        print(f"❌ 导入失败: {e}")
                else:
                    print("❌ 文件不存在")
            
            elif choice == "6":
                break
            else:
                print("❌ 无效选择")
    
    def show_help(self):
        """显示帮助信息"""
        print("\n📖 使用帮助")
        print("=" * 50)
        
        print("\n🎯 主要功能:")
        print("• 语音通话: 支持高质量实时语音通话")
        print("• 文本消息: 支持广播和私聊消息")
        print("• 多用户: 支持多个用户同时在线")
        print("• 跨平台: 支持Windows、macOS、Linux")
        
        print("\n📋 客户端命令:")
        print("连接服务器后，可以使用以下命令：")
        print("• clients                    - 显示在线客户端")
        print("• call <client_id>           - 发起通话")
        print("• accept <call_id>           - 接受通话")
        print("• reject <call_id>           - 拒绝通话")
        print("• hangup                     - 挂断通话")
        print("• broadcast <message>        - 发送广播消息")
        print("• private <client_id> <msg>  - 发送私聊消息")
        print("• status                     - 显示状态")
        print("• quit                       - 退出客户端")
        
        print("\n🔧 系统要求:")
        print("• Python 3.8 或更高版本")
        print("• PyAudio 音频库")
        print("• 稳定的网络连接")
        print("• 音频设备（麦克风和扬声器）")
        
        print("\n🛠️  故障排除:")
        print("• 连接失败: 检查服务器地址和网络连接")
        print("• 音频无声: 检查麦克风权限和音频设备")
        print("• 延迟较高: 检查网络质量和服务器性能")
        
        print("\n📞 技术支持:")
        print("• GitHub: https://github.com/your-repo/voip-system")
        print("• 文档: 查看 README.md 了解详细信息")
        
        input("\n按回车键返回主菜单...")
    
    def run(self):
        """运行主程序"""
        try:
            while True:
                self.print_header()
                self.print_menu()
                
                choice = input("请选择功能 (1-7): ").strip()
                
                if choice == "1":
                    self.quick_connect()
                elif choice == "2":
                    self.server_management()
                elif choice == "3":
                    self.connection_test()
                elif choice == "4":
                    self.audio_test()
                elif choice == "5":
                    self.config_management()
                elif choice == "6":
                    self.show_help()
                elif choice == "7":
                    print("\n👋 感谢使用VoIP语音通话系统!")
                    break
                else:
                    print("❌ 无效选择，请输入1-7之间的数字")
                    input("按回车键继续...")
        
        except KeyboardInterrupt:
            print("\n\n👋 程序已退出")
        except Exception as e:
            print(f"\n❌ 程序运行错误: {e}")

def main():
    """主函数"""
    launcher = VoIPClientLauncher()
    launcher.run()

if __name__ == "__main__":
    main()
