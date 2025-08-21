#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VoIP客户端交互式启动脚本 (无虚拟环境版本)
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
from typing import Dict, Any, Optional

class VoIPClientLauncher:
    def __init__(self):
        self.config_file = "client_config.json"
        self.config = self.load_config()
        self.python_cmd = self.get_python_command()
    
    def get_python_command(self):
        """获取Python命令"""
        # 直接使用系统Python
        try:
            result = subprocess.run([sys.executable, "--version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return sys.executable
        except:
            pass
        
        # 尝试其他Python命令
        for cmd in ["python3", "python"]:
            try:
                result = subprocess.run([cmd, "--version"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    return cmd
            except:
                continue
        
        print("❌ 未找到Python解释器")
        return None
    
    def load_config(self):
        """加载配置文件"""
        default_config = {
            "servers": {
                "default": {
                    "name": "默认服务器",
                    "ip": "120.27.145.121",
                    "port": 5060
                },
                "local": {
                    "name": "本地测试服务器",
                    "ip": "127.0.0.1", 
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
        except Exception as e:
            print(f"⚠️ 加载配置文件失败，使用默认配置: {e}")
        
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
            if last_server in self.config["servers"]:
                server_info = self.config["servers"][last_server]
                self.connect_to_server(server_info["ip"], server_info["port"])
            else:
                print("❌ 默认服务器配置不存在")
        
        elif choice == "2":
            self.select_server()
        
        elif choice == "3":
            self.add_new_server()
        
        elif choice == "4":
            return
        
        else:
            print("❌ 无效选择，请重新输入")
            input("按回车键继续...")
    
    def select_server(self):
        """选择服务器"""
        print("\n🔧 选择服务器")
        print("-" * 30)
        
        servers = list(self.config["servers"].keys())
        for i, key in enumerate(servers, 1):
            server = self.config["servers"][key]
            print(f"{i}. {server['name']} ({server['ip']}:{server['port']})")
        
        try:
            choice = input(f"\n请选择服务器 (1-{len(servers)}): ").strip()
            index = int(choice) - 1
            
            if 0 <= index < len(servers):
                server_key = servers[index]
                server_info = self.config["servers"][server_key]
                self.config["user"]["last_server"] = server_key
                self.save_config()
                self.connect_to_server(server_info["ip"], server_info["port"])
            else:
                print("❌ 无效选择")
        
        except ValueError:
            print("❌ 请输入数字")
        
        input("按回车键继续...")
    
    def add_new_server(self):
        """添加新服务器"""
        print("\n➕ 添加新服务器")
        print("-" * 30)
        
        name = input("服务器名称: ").strip()
        if not name:
            print("❌ 服务器名称不能为空")
            return
        
        ip = input("服务器IP地址: ").strip()
        if not ip:
            print("❌ IP地址不能为空")
            return
        
        port_str = input("端口 (默认5060): ").strip()
        port = 5060
        if port_str:
            try:
                port = int(port_str)
            except ValueError:
                print("❌ 端口必须是数字")
                return
        
        # 添加到配置
        server_key = f"custom_{len(self.config['servers'])}"
        self.config["servers"][server_key] = {
            "name": name,
            "ip": ip,
            "port": port
        }
        
        if self.save_config():
            print(f"✅ 服务器 '{name}' 已添加")
            
            # 询问是否立即连接
            connect_now = input("是否立即连接到此服务器? (y/N): ").strip().lower()
            if connect_now == 'y':
                self.config["user"]["last_server"] = server_key
                self.save_config()
                self.connect_to_server(ip, port)
    
    def connect_to_server(self, server_ip: str, port: int):
        """连接到服务器"""
        print(f"\n🔌 连接到服务器 {server_ip}:{port}")
        
        # 获取用户名
        default_name = self.config["user"]["default_name"]
        user_name = input(f"用户名 (默认: {default_name}): ").strip()
        if not user_name:
            user_name = default_name
        
        # 更新配置
        self.config["user"]["default_name"] = user_name
        self.save_config()
        
        # 构造命令
        if not self.python_cmd:
            print("❌ 无法找到Python解释器")
            return
        
        cmd = [
            self.python_cmd,
            "cloud_voip_client.py",
            "--server", server_ip,
            "--name", user_name
        ]
        
        if port != 5060:
            cmd.extend(["--port", str(port)])
        
        print(f"🚀 启动客户端: {user_name}")
        print("💡 按 Ctrl+C 可以退出客户端")
        input("按回车键开始连接...")
        
        try:
            # 启动客户端
            subprocess.run(cmd, cwd=os.path.dirname(__file__))
        except KeyboardInterrupt:
            print("\n📞 客户端已断开连接")
        except FileNotFoundError:
            print("❌ 找不到 cloud_voip_client.py 文件")
        except Exception as e:
            print(f"❌ 启动客户端失败: {e}")
        
        input("按回车键返回菜单...")
    
    def server_management(self):
        """服务器管理"""
        print("\n🔧 服务器管理")
        print("-" * 30)
        
        print("1. 查看所有服务器")
        print("2. 添加新服务器")
        print("3. 编辑服务器")
        print("4. 删除服务器")
        print("5. 返回主菜单")
        
        choice = input("\n请选择 (1-5): ").strip()
        
        if choice == "1":
            self.list_servers()
        elif choice == "2":
            self.add_new_server()
        elif choice == "3":
            self.edit_server()
        elif choice == "4":
            self.delete_server()
        elif choice == "5":
            return
        else:
            print("❌ 无效选择")
            input("按回车键继续...")
    
    def list_servers(self):
        """列出所有服务器"""
        print("\n📋 服务器列表")
        print("-" * 40)
        
        for key, server in self.config["servers"].items():
            status = " (默认)" if key == self.config["user"]["last_server"] else ""
            print(f"🖥️  {server['name']}{status}")
            print(f"   地址: {server['ip']}:{server['port']}")
            print(f"   ID: {key}")
            print()
        
        input("按回车键继续...")
    
    def edit_server(self):
        """编辑服务器"""
        print("\n✏️  编辑服务器")
        print("-" * 30)
        
        servers = list(self.config["servers"].keys())
        for i, key in enumerate(servers, 1):
            server = self.config["servers"][key]
            print(f"{i}. {server['name']} ({server['ip']}:{server['port']})")
        
        try:
            choice = input(f"\n选择要编辑的服务器 (1-{len(servers)}): ").strip()
            index = int(choice) - 1
            
            if 0 <= index < len(servers):
                server_key = servers[index]
                server = self.config["servers"][server_key]
                
                print(f"\n编辑服务器: {server['name']}")
                
                new_name = input(f"名称 (当前: {server['name']}): ").strip()
                if new_name:
                    server['name'] = new_name
                
                new_ip = input(f"IP地址 (当前: {server['ip']}): ").strip()
                if new_ip:
                    server['ip'] = new_ip
                
                new_port = input(f"端口 (当前: {server['port']}): ").strip()
                if new_port:
                    try:
                        server['port'] = int(new_port)
                    except ValueError:
                        print("❌ 端口必须是数字")
                        return
                
                if self.save_config():
                    print("✅ 服务器信息已更新")
            else:
                print("❌ 无效选择")
        
        except ValueError:
            print("❌ 请输入数字")
        
        input("按回车键继续...")
    
    def delete_server(self):
        """删除服务器"""
        print("\n🗑️  删除服务器")
        print("-" * 30)
        
        servers = list(self.config["servers"].keys())
        # 不允许删除默认服务器
        editable_servers = [key for key in servers if key != "default"]
        
        if not editable_servers:
            print("❌ 没有可删除的服务器")
            input("按回车键继续...")
            return
        
        for i, key in enumerate(editable_servers, 1):
            server = self.config["servers"][key]
            print(f"{i}. {server['name']} ({server['ip']}:{server['port']})")
        
        try:
            choice = input(f"\n选择要删除的服务器 (1-{len(editable_servers)}): ").strip()
            index = int(choice) - 1
            
            if 0 <= index < len(editable_servers):
                server_key = editable_servers[index]
                server = self.config["servers"][server_key]
                
                confirm = input(f"确定删除服务器 '{server['name']}'? (y/N): ").strip().lower()
                if confirm == 'y':
                    del self.config["servers"][server_key]
                    
                    # 如果删除的是当前默认服务器，重置为default
                    if self.config["user"]["last_server"] == server_key:
                        self.config["user"]["last_server"] = "default"
                    
                    if self.save_config():
                        print("✅ 服务器已删除")
            else:
                print("❌ 无效选择")
        
        except ValueError:
            print("❌ 请输入数字")
        
        input("按回车键继续...")
    
    def connection_test(self):
        """连接测试"""
        print("\n🧪 连接测试")
        print("-" * 30)
        
        # 选择要测试的服务器
        servers = list(self.config["servers"].keys())
        print("选择要测试的服务器:")
        for i, key in enumerate(servers, 1):
            server = self.config["servers"][key]
            print(f"{i}. {server['name']} ({server['ip']}:{server['port']})")
        
        try:
            choice = input(f"\n请选择 (1-{len(servers)}): ").strip()
            index = int(choice) - 1
            
            if 0 <= index < len(servers):
                server_key = servers[index]
                server = self.config["servers"][server_key]
                self.test_server_connection(server["ip"], server["port"])
            else:
                print("❌ 无效选择")
        
        except ValueError:
            print("❌ 请输入数字")
    
    def test_server_connection(self, ip: str, port: int):
        """测试服务器连接"""
        print(f"\n🔍 测试连接到 {ip}:{port}")
        print("-" * 40)
        
        # TCP连接测试 (消息服务)
        print("🔌 TCP连接测试 (消息服务)...")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                print("   ✅ TCP连接成功")
            else:
                print(f"   ❌ TCP连接失败 (错误码: {result})")
        except Exception as e:
            print(f"   ❌ TCP连接异常: {e}")
        
        # UDP连接测试 (音频服务)
        print("📡 UDP连接测试 (音频服务)...")
        try:
            # 运行专门的音频测试脚本
            if os.path.exists("test_audio.py"):
                result = subprocess.run([self.python_cmd, "test_audio.py"], 
                                      capture_output=True, text=True, timeout=10)
                if "✅" in result.stdout:
                    print("   ✅ 音频服务可达")
                else:
                    print("   ⚠️  音频测试超时或失败")
            else:
                print("   ⚠️  找不到音频测试脚本")
        except subprocess.TimeoutExpired:
            print("   ⚠️  音频测试超时")
        except Exception as e:
            print(f"   ❌ 音频测试异常: {e}")
        
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
            input("按回车键继续...")
    
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
            print("❌ PyAudio未安装")
            print("💡 请安装: pip install PyAudio")
        except Exception as e:
            print(f"❌ 音频设备检测失败: {e}")
        
        input("按回车键继续...")
    
    def test_audio_transmission(self):
        """测试音频传输"""
        print("\n📡 音频传输测试")
        print("-" * 30)
        
        if os.path.exists("test_audio.py"):
            print("🔄 运行音频传输测试...")
            try:
                result = subprocess.run([self.python_cmd, "test_audio.py"], 
                                      timeout=30)
                if result.returncode == 0:
                    print("✅ 音频传输测试完成")
                else:
                    print(f"⚠️  音频传输测试异常 (退出码: {result.returncode})")
            except subprocess.TimeoutExpired:
                print("⏰ 音频传输测试超时")
            except Exception as e:
                print(f"❌ 音频传输测试失败: {e}")
        else:
            print("❌ 找不到 test_audio.py 测试脚本")
            print("💡 请确保测试脚本存在于当前目录")
        
        input("按回车键继续...")
    
    def config_management(self):
        """配置管理"""
        print("\n⚙️ 配置管理")
        print("-" * 30)
        
        print("1. 查看当前配置")
        print("2. 重置为默认配置")
        print("3. 导出配置文件")
        print("4. 导入配置文件")
        print("5. 返回主菜单")
        
        choice = input("\n请选择 (1-5): ").strip()
        
        if choice == "1":
            self.show_config()
        elif choice == "2":
            self.reset_config()
        elif choice == "3":
            self.export_config()
        elif choice == "4":
            self.import_config()
        elif choice == "5":
            return
        else:
            print("❌ 无效选择")
            input("按回车键继续...")
    
    def show_config(self):
        """显示当前配置"""
        print("\n📋 当前配置")
        print("-" * 30)
        print(json.dumps(self.config, indent=2, ensure_ascii=False))
        input("\n按回车键继续...")
    
    def reset_config(self):
        """重置配置"""
        print("\n🔄 重置配置")
        print("-" * 30)
        
        confirm = input("确定要重置所有配置吗? (y/N): ").strip().lower()
        if confirm == 'y':
            # 重新加载默认配置
            self.__init__()
            if self.save_config():
                print("✅ 配置已重置为默认值")
        else:
            print("❌ 取消重置")
        
        input("按回车键继续...")
    
    def export_config(self):
        """导出配置"""
        filename = input("导出文件名 (默认: config_backup.json): ").strip()
        if not filename:
            filename = "config_backup.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"✅ 配置已导出到 {filename}")
        except Exception as e:
            print(f"❌ 导出失败: {e}")
        
        input("按回车键继续...")
    
    def import_config(self):
        """导入配置"""
        filename = input("导入文件名: ").strip()
        
        if not filename:
            print("❌ 请输入文件名")
            input("按回车键继续...")
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # 验证配置格式
            if "servers" not in imported_config or "user" not in imported_config:
                print("❌ 无效的配置文件格式")
                input("按回车键继续...")
                return
            
            self.config = imported_config
            if self.save_config():
                print(f"✅ 配置已从 {filename} 导入")
        except FileNotFoundError:
            print("❌ 文件不存在")
        except json.JSONDecodeError:
            print("❌ 文件格式错误")
        except Exception as e:
            print(f"❌ 导入失败: {e}")
        
        input("按回车键继续...")
    
    def show_help(self):
        """显示帮助信息"""
        print("\n📖 使用帮助")
        print("-" * 40)
        
        print("🎯 功能介绍:")
        print("本程序是VoIP语音通话系统的客户端启动器，提供以下功能：")
        print("• 连接到VoIP服务器进行语音通话")
        print("• 发送文本消息（广播和私聊）")
        print("• 管理多个服务器配置")
        print("• 测试网络连接和音频设备")
        
        print("\n📞 客户端使用说明:")
        print("连接成功后，在客户端中可以使用以下命令：")
        print("• clients                    - 查看在线用户")
        print("• call <client_id>           - 发起通话")
        print("• accept <call_id>           - 接受来电")
        print("• reject <call_id>           - 拒绝来电")
        print("• hangup                     - 挂断通话")
        print("• broadcast <message>        - 发送广播消息")
        print("• private <client_id> <msg>  - 发送私聊消息")
        print("• status                     - 显示状态")
        print("• quit                       - 退出客户端")
        
        print("\n🔧 系统要求:")
        print("• Python 3.8 或更高版本")
        print("• PyAudio 音频库 (pip install PyAudio)")
        print("• 稳定的网络连接")
        print("• 音频设备（麦克风和扬声器）")
        
        print("\n🛠️  故障排除:")
        print("• 连接失败: 检查服务器地址和网络连接")
        print("• 音频无声: 检查麦克风权限和音频设备")
        print("• 延迟较高: 检查网络质量和服务器性能")
        print("• PyAudio错误: sudo apt install portaudio19-dev (Linux)")
        
        print("\n📞 技术支持:")
        print("• 查看 README.md 了解详细信息")
        print("• 运行连接测试和音频测试进行故障排除")
        
        input("\n按回车键返回主菜单...")
    
    def run(self):
        """运行主程序"""
        # 检查Python环境
        if not self.python_cmd:
            print("❌ 无法找到Python解释器，程序无法运行")
            return
        
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
