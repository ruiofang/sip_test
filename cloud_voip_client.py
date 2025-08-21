#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
云VoIP客户端
连接云VoIP服务器进行多人语音通信

功能特性：
- 连接云服务器
- 语音通话
- 文本消息和广播
- 房间管理
- 客户端列表管理

使用方法:
python3 cloud_voip_client.py --server SERVER_IP [--name CLIENT_NAME]

作者: GitHub Copilot
日期: 2025年8月20日
"""

import sys
import time
import threading
import json
import socket
import struct
import argparse
import uuid
import os
import warnings
from typing import Dict, Any, Optional, List

# 抑制ALSA警告
os.environ['ALSA_PCM_CARD'] = '0'
os.environ['ALSA_PCM_DEVICE'] = '0'

try:
    import pyaudio
    AUDIO_AVAILABLE = True
    warnings.filterwarnings("ignore", category=UserWarning)
except ImportError:
    AUDIO_AVAILABLE = False
    print("警告: pyaudio未安装，语音功能将不可用")


class CloudVoIPClient:
    def __init__(self, server_ip: str, client_name: str = None, base_port: int = 5060):
        """
        初始化云VoIP客户端
        
        Args:
            server_ip: 服务器IP地址
            client_name: 客户端名称
            base_port: 服务器基础端口
        """
        self.server_ip = server_ip
        self.base_port = base_port
        
        # 生成唯一客户端ID
        self.client_id = str(uuid.uuid4())[:8]
        self.client_name = client_name or f"Client_{self.client_id}"
        
        # 连接状态
        self.connected = False
        self.running = True
        
        # 服务端口
        self.message_port = base_port      # 5060
        self.audio_port = base_port + 1    # 5061
        self.control_port = base_port + 2  # 5062
        
        # 套接字
        self.message_socket = None
        self.audio_socket = None
        self.control_socket = None
        
        # 线程
        self.message_thread = None
        self.audio_receive_thread = None
        self.audio_send_thread = None
        
        # 状态管理
        self.online_clients = {}  # {client_id: client_info}
        self.current_call = None  # 当前通话信息
        self.current_room = None  # 当前房间
        
        # 音频配置
        self.audio_format = pyaudio.paInt16 if AUDIO_AVAILABLE else None
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024
        self.audio_instance = None
        self.audio_input = None
        self.audio_output = None
        
        # 线程锁
        self.clients_lock = threading.Lock()
        self.call_lock = threading.Lock()
        self.client_list_event = threading.Event()  # 用于客户端列表同步

    def connect(self) -> bool:
        """连接到服务器"""
        print(f"正在连接到服务器 {self.server_ip}:{self.message_port}...")
        
        try:
            # 连接消息服务
            self.message_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.message_socket.connect((self.server_ip, self.message_port))
            
            # 设置连接状态
            self.connected = True
            
            # 启动消息接收线程
            self.message_thread = threading.Thread(target=self.message_receive_thread)
            self.message_thread.daemon = True
            self.message_thread.start()
            
            # 初始化音频（如果可用）
            audio_port = None
            if AUDIO_AVAILABLE:
                if self.init_audio():
                    audio_port = self.audio_socket.getsockname()[1]
            
            # 发送注册消息（包含音频端口信息）
            register_msg = {
                'type': 'register',
                'client_id': self.client_id,
                'client_name': self.client_name,
                'audio_port': audio_port,  # 添加音频端口信息
                'timestamp': time.time()
            }
            
            self.send_message(register_msg)
            
            print(f"✅ 已连接到服务器")
            print(f"客户端ID: {self.client_id}")
            print(f"客户端名称: {self.client_name}")
            if audio_port:
                print(f"音频端口: {audio_port}")
            
            return True
            
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False

    def init_audio(self):
        """初始化音频"""
        if not AUDIO_AVAILABLE:
            return False
        
        try:
            self.audio_instance = pyaudio.PyAudio()
            
            # 连接音频服务
            self.audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 绑定到本地任意可用端口
            self.audio_socket.bind(('0.0.0.0', 0))
            local_audio_port = self.audio_socket.getsockname()[1]
            
            print(f"🎵 音频系统已初始化，本地音频端口: {local_audio_port}")
            return True
            
        except Exception as e:
            print(f"音频初始化失败: {e}")
            return False

    def send_message(self, message: Dict[str, Any]):
        """发送消息到服务器"""
        if not self.message_socket:
            return False
        
        try:
            # 添加客户端ID
            if 'client_id' not in message:
                message['client_id'] = self.client_id
            
            data = json.dumps(message).encode('utf-8')
            length = struct.pack('I', len(data))
            self.message_socket.send(length + data)
            return True
            
        except Exception as e:
            print(f"发送消息失败: {e}")
            return False

    def message_receive_thread(self):
        """消息接收线程"""
        print(f"🔍 [DEBUG] 消息接收线程启动")
        while self.running and self.connected:
            try:
                print(f"🔍 [DEBUG] 等待接收消息...")
                # 接收消息长度
                length_data = self.message_socket.recv(4)
                if not length_data:
                    print(f"🔍 [DEBUG] 收到空的长度数据，连接可能关闭")
                    break
                
                msg_length = struct.unpack('I', length_data)[0]
                print(f"🔍 [DEBUG] 收到消息长度: {msg_length}")
                if msg_length > 1024 * 1024:  # 1MB限制
                    print(f"🔍 [DEBUG] 消息长度过大: {msg_length}")
                    break
                
                # 接收完整消息
                data = b''
                while len(data) < msg_length:
                    chunk = self.message_socket.recv(min(msg_length - len(data), 4096))
                    if not chunk:
                        print(f"🔍 [DEBUG] 收到空的数据块，连接可能关闭")
                        break
                    data += chunk
                
                if len(data) != msg_length:
                    print(f"🔍 [DEBUG] 数据长度不匹配: 期望 {msg_length}, 实际 {len(data)}")
                    break
                
                print(f"🔍 [DEBUG] 成功接收完整消息，长度: {len(data)}")
                
                # 解析并处理消息
                try:
                    message = json.loads(data.decode('utf-8'))
                    print(f"🔍 [DEBUG] 成功解析消息，准备处理...")
                    self.handle_server_message(message)
                except json.JSONDecodeError as e:
                    print(f"🔍 [DEBUG] JSON解析失败: {e}")
                    print(f"🔍 [DEBUG] 原始数据: {data}")
                    pass
                    
            except Exception as e:
                if self.running:
                    print(f"接收消息错误: {e}")
                    print(f"🔍 [DEBUG] 详细错误: {e}")
                break
        
        self.connected = False
        print("与服务器的连接已断开")

    def handle_server_message(self, message: Dict[str, Any]):
        """处理服务器消息"""
        msg_type = message.get('type', 'unknown')
        print(f"🔍 [DEBUG] 收到服务器消息: {msg_type}")
        
        if msg_type == 'register_response':
            self.handle_register_response(message)
        elif msg_type == 'broadcast':
            self.handle_broadcast_message(message)
        elif msg_type == 'private':
            self.handle_private_message(message)
        elif msg_type == 'call_request':
            self.handle_call_request(message)
        elif msg_type == 'call_answer':
            self.handle_call_answer(message)
        elif msg_type == 'call_hangup':
            self.handle_call_hangup(message)
        elif msg_type == 'client_list':
            print(f"🔍 [DEBUG] 准备处理客户端列表消息")
            self.handle_client_list(message)
        else:
            print(f"收到未知消息类型: {msg_type}")
            print(f"🔍 [DEBUG] 完整消息内容: {message}")

    def handle_register_response(self, message: Dict[str, Any]):
        """处理注册响应"""
        status = message.get('status')
        if status == 'success':
            print("✅ 注册成功")
            # 请求客户端列表
            self.request_client_list()
        else:
            print("❌ 注册失败")

    def handle_broadcast_message(self, message: Dict[str, Any]):
        """处理广播消息"""
        sender = message.get('from', 'unknown')
        content = message.get('content', '')
        timestamp = message.get('timestamp', time.time())
        
        time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
        print(f"\n📢 [广播] {sender} ({time_str}): {content}")

    def handle_private_message(self, message: Dict[str, Any]):
        """处理私聊消息"""
        sender = message.get('from', 'unknown')
        content = message.get('content', '')
        timestamp = message.get('timestamp', time.time())
        
        time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
        print(f"\n💬 [私聊] {sender} ({time_str}): {content}")

    def handle_call_request(self, message: Dict[str, Any]):
        """处理通话请求"""
        call_id = message.get('call_id')
        caller = message.get('from')
        
        print(f"\n📞 收到来自 {caller} 的通话请求 (通话ID: {call_id})")
        print(f"💡 输入 'accept {call_id}' 接受通话，或 'reject {call_id}' 拒绝通话")
        
        # 存储待处理的通话请求
        if not hasattr(self, 'pending_calls'):
            self.pending_calls = {}
        
        self.pending_calls[call_id] = {
            'caller': caller,
            'timestamp': time.time()
        }

    def handle_call_answer(self, message: Dict[str, Any]):
        """处理通话应答"""
        call_id = message.get('call_id')
        accepted = message.get('accepted', False)
        responder = message.get('from')
        
        if accepted:
            print(f"✅ {responder} 接受了您的通话请求")
            with self.call_lock:
                self.current_call = {
                    'id': call_id,
                    'peer': responder,
                    'status': 'active'
                }
            self.start_audio_streams()
        else:
            print(f"❌ {responder} 拒绝了您的通话请求")

    def handle_call_hangup(self, message: Dict[str, Any]):
        """处理挂断通话"""
        call_id = message.get('call_id')
        peer = message.get('from')
        
        print(f"📞 {peer} 挂断了通话")
        
        with self.call_lock:
            self.current_call = None
        
        self.stop_audio_streams()

    def handle_client_list(self, message: Dict[str, Any]):
        """处理客户端列表"""
        print(f"📋 收到客户端列表响应")
        clients = message.get('clients', [])
        print(f"🔢 服务器返回 {len(clients)} 个客户端")
        
        with self.clients_lock:
            self.online_clients = {}
            for client in clients:
                client_id = client['id']
                if client_id != self.client_id:  # 排除自己
                    self.online_clients[client_id] = client
                    print(f"  - 发现客户端: {client.get('name', client_id)} ({client_id})")
        
        # 设置事件，通知show_clients函数
        self.client_list_event.set()
        print(f"✅ 客户端列表更新完成")

    def request_client_list(self):
        """请求客户端列表"""
        message = {
            'type': 'get_clients',
            'timestamp': time.time()
        }
        print(f"🔍 正在请求客户端列表...")
        success = self.send_message(message)
        print(f"📤 发送客户端列表请求: {'成功' if success else '失败'}")

    def send_broadcast(self, content: str):
        """发送广播消息"""
        message = {
            'type': 'broadcast',
            'content': content,
            'timestamp': time.time()
        }
        return self.send_message(message)

    def send_private_message(self, target_id: str, content: str):
        """发送私聊消息"""
        message = {
            'type': 'private',
            'target': target_id,
            'content': content,
            'timestamp': time.time()
        }
        return self.send_message(message)

    def make_call(self, target_id: str):
        """发起通话"""
        if self.current_call:
            print("❌ 当前已在通话中")
            return False
        
        message = {
            'type': 'call_request',
            'target': target_id,
            'timestamp': time.time()
        }
        
        if self.send_message(message):
            print(f"📞 正在呼叫 {target_id}...")
            return True
        return False

    def accept_call(self, call_id: str):
        """接受通话"""
        if not hasattr(self, 'pending_calls'):
            self.pending_calls = {}
        
        if call_id not in self.pending_calls:
            print(f"❌ 未找到通话ID: {call_id}")
            return False
        
        caller = self.pending_calls[call_id]['caller']
        
        # 发送接受消息
        answer_msg = {
            'type': 'call_answer',
            'call_id': call_id,
            'accepted': True,
            'timestamp': time.time()
        }
        
        if self.send_message(answer_msg):
            with self.call_lock:
                self.current_call = {
                    'id': call_id,
                    'peer': caller,
                    'status': 'active'
                }
            print(f"✅ 已接受来自 {caller} 的通话")
            self.start_audio_streams()
            
            # 删除待处理的通话请求
            del self.pending_calls[call_id]
            return True
        return False

    def reject_call(self, call_id: str):
        """拒绝通话"""
        if not hasattr(self, 'pending_calls'):
            self.pending_calls = {}
        
        if call_id not in self.pending_calls:
            print(f"❌ 未找到通话ID: {call_id}")
            return False
        
        caller = self.pending_calls[call_id]['caller']
        
        # 发送拒绝消息
        answer_msg = {
            'type': 'call_answer',
            'call_id': call_id,
            'accepted': False,
            'timestamp': time.time()
        }
        
        if self.send_message(answer_msg):
            print(f"❌ 已拒绝来自 {caller} 的通话")
            
            # 删除待处理的通话请求
            del self.pending_calls[call_id]
            return True
        return False

    def hangup_call(self):
        """挂断当前通话"""
        with self.call_lock:
            if not self.current_call:
                print("❌ 当前没有进行中的通话")
                return False
            
            call_id = self.current_call['id']
            self.current_call = None
        
        message = {
            'type': 'call_hangup',
            'call_id': call_id,
            'timestamp': time.time()
        }
        
        self.send_message(message)
        self.stop_audio_streams()
        print("📞 通话已结束")
        return True

    def start_audio_streams(self):
        """开始音频流"""
        if not AUDIO_AVAILABLE or not self.audio_instance:
            print("音频功能不可用")
            return
        
        try:
            # 启动音频输入流（麦克风）
            self.audio_input = self.audio_instance.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            # 启动音频输出流（扬声器）
            self.audio_output = self.audio_instance.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.rate,
                output=True,
                frames_per_buffer=self.chunk
            )
            
            # 启动音频线程
            self.audio_send_thread = threading.Thread(target=self.audio_send_loop)
            self.audio_send_thread.daemon = True
            self.audio_send_thread.start()
            
            self.audio_receive_thread = threading.Thread(target=self.audio_receive_loop)
            self.audio_receive_thread.daemon = True
            self.audio_receive_thread.start()
            
            print("🎵 音频流已启动")
            
        except Exception as e:
            print(f"启动音频流失败: {e}")

    def stop_audio_streams(self):
        """停止音频流"""
        try:
            if self.audio_input:
                self.audio_input.stop_stream()
                self.audio_input.close()
                self.audio_input = None
            
            if self.audio_output:
                self.audio_output.stop_stream()
                self.audio_output.close()
                self.audio_output = None
            
            print("🔇 音频流已停止")
            
        except Exception as e:
            print(f"停止音频流错误: {e}")

    def audio_send_loop(self):
        """音频发送循环"""
        print("🎵 [DEBUG] 音频发送循环开始")
        while self.current_call and self.audio_input:
            try:
                # 读取音频数据
                data = self.audio_input.read(self.chunk, exception_on_overflow=False)
                
                # 构造音频包
                if self.audio_socket and self.current_call:
                    # 获取目标客户端ID - 修复变量名错误
                    target_id = self.current_call.get('peer', '')
                    if target_id:
                        # 构造包头：源客户端ID + 目标客户端ID
                        header = self.client_id.encode('utf-8').ljust(16, b'\x00')  # 16字节源ID
                        header += target_id.encode('utf-8').ljust(16, b'\x00')      # 16字节目标ID
                        packet = header + data
                        
                        # 发送到服务器
                        try:
                            self.audio_socket.sendto(packet, (self.server_ip, self.audio_port))
                            print(f"🔊 [DEBUG] 发送音频数据: {len(data)} 字节到 {target_id}")
                        except Exception as send_e:
                            print(f"音频发送失败: {send_e}")
                    else:
                        print(f"🔊 [DEBUG] 没有找到目标客户端ID，当前通话信息: {self.current_call}")
                else:
                    time.sleep(0.01)  # 避免过度消耗CPU
                    
            except Exception as e:
                if self.current_call:
                    print(f"音频发送错误: {e}")
                break
        print("🎵 [DEBUG] 音频发送循环结束")

    def audio_receive_loop(self):
        """音频接收循环"""
        print("🎵 [DEBUG] 音频接收循环开始")
        # 设置更长的超时，避免过度阻塞
        if self.audio_socket:
            self.audio_socket.settimeout(1.0)  # 增加到1秒
            
        while self.current_call and self.audio_output:
            try:
                # 从服务器接收音频数据
                if self.audio_socket:
                    try:
                        data, addr = self.audio_socket.recvfrom(4096)
                        print(f"🔊 [DEBUG] 接收音频数据: {len(data)} 字节 from {addr}")
                        
                        # 解析包头，提取音频数据
                        if len(data) > 32:  # 32字节包头（16字节源ID + 16字节目标ID）
                            audio_data = data[32:]
                            
                            # 播放音频数据
                            if len(audio_data) > 0:
                                self.audio_output.write(audio_data)
                                print(f"🔊 [DEBUG] 播放音频数据: {len(audio_data)} 字节")
                        else:
                            print(f"🔊 [DEBUG] 收到短音频包: {len(data)} 字节")
                    except socket.timeout:
                        # 正常超时，继续循环
                        continue
                        continue
                    except Exception as recv_e:
                        print(f"音频接收异常: {recv_e}")
                        time.sleep(0.01)
                else:
                    time.sleep(0.01)
                    
            except Exception as e:
                if self.current_call:
                    print(f"音频接收错误: {e}")
                break
        print("🎵 [DEBUG] 音频接收循环结束")

    def show_clients(self):
        """显示在线客户端"""
        # 清除之前的事件状态
        self.client_list_event.clear()
        print("🔄 清除之前的客户端列表事件")
        
        # 请求客户端列表
        self.request_client_list()
        
        # 等待服务器响应（最多等待3秒）
        print("⏳ 等待服务器响应（最多3秒）...")
        if self.client_list_event.wait(timeout=3.0):
            print("✅ 收到服务器响应")
            with self.clients_lock:
                if self.online_clients:
                    print(f"\n在线客户端 ({len(self.online_clients)}):")
                    for client_id, client_info in self.online_clients.items():
                        name = client_info.get('name', client_id)
                        status = client_info.get('status', 'unknown')
                        print(f"  - {name} ({client_id}) [{status}]")
                else:
                    print("没有其他在线客户端")
        else:
            print("⏰ 获取客户端列表超时")

    def interactive_mode(self):
        """交互模式"""
        print("\n" + "=" * 60)
        print("云VoIP客户端控制台")
        print("=" * 60)
        print("可用命令:")
        print("  clients                    - 显示在线客户端")
        print("  call                       - 发起通话 (选择式)")
        print("  accept <call_id>           - 接受通话")
        print("  reject <call_id>           - 拒绝通话")
        print("  hangup                     - 挂断通话")
        print("  broadcast                  - 发送广播消息 (选择式)")
        print("  private                    - 发送私聊消息 (选择式)")
        print("  status                     - 显示客户端状态")
        print("  quit                       - 退出客户端")
        print("  help                       - 显示帮助")
        print("=" * 60)
        
        while self.running and self.connected:
            try:
                cmd_line = input(f"{self.client_name}> ").strip()
                if not cmd_line:
                    continue
                
                parts = cmd_line.split(' ')
                cmd = parts[0].lower()
                
                if cmd == 'quit':
                    print("正在退出...")
                    break
                elif cmd == 'clients':
                    self.show_clients()
                elif cmd == 'call':
                    if len(parts) > 1:
                        # 兼容旧的直接指定ID的方式
                        target_id = parts[1]
                        self.make_call(target_id)
                    else:
                        # 新的选择式方式
                        self.interactive_call()
                elif cmd == 'hangup':
                    self.hangup_call()
                elif cmd == 'accept' and len(parts) > 1:
                    call_id = parts[1]
                    self.accept_call(call_id)
                elif cmd == 'reject' and len(parts) > 1:
                    call_id = parts[1]
                    self.reject_call(call_id)
                elif cmd == 'broadcast':
                    if len(parts) > 1:
                        # 兼容旧的直接输入消息的方式
                        message = ' '.join(parts[1:])
                        if self.send_broadcast(message):
                            print("广播消息已发送")
                    else:
                        # 新的选择式方式
                        self.interactive_broadcast()
                elif cmd == 'private':
                    if len(parts) > 2:
                        # 兼容旧的直接指定ID和消息的方式
                        target_id = parts[1]
                        message = ' '.join(parts[2:])
                        if self.send_private_message(target_id, message):
                            print(f"私聊消息已发送给 {target_id}")
                    else:
                        # 新的选择式方式
                        self.interactive_private_message()
                elif cmd == 'status':
                    call_status = "无通话"
                    if self.current_call:
                        call_status = f"与 {self.current_call['peer']} 通话中"
                    
                    print(f"\n客户端状态:")
                    print(f"  ID: {self.client_id}")
                    print(f"  名称: {self.client_name}")
                    print(f"  服务器: {self.server_ip}:{self.message_port}")
                    print(f"  连接状态: {'已连接' if self.connected else '未连接'}")
                    print(f"  通话状态: {call_status}")
                    print(f"  在线客户端数量: {len(self.online_clients)}")
                elif cmd == 'help':
                    print("\n可用命令:")
                    print("  clients                    - 显示在线客户端")
                    print("  call                       - 发起通话 (选择式)")
                    print("  accept <call_id>           - 接受通话")
                    print("  reject <call_id>           - 拒绝通话")
                    print("  hangup                     - 挂断通话")
                    print("  broadcast                  - 发送广播消息 (选择式)")
                    print("  private                    - 发送私聊消息 (选择式)")
                    print("  status                     - 显示客户端状态")
                    print("  quit                       - 退出客户端")
                    print("  help                       - 显示帮助")
                    print("\n💡 提示: 现在支持选择式操作，直接输入命令即可选择目标！")
                else:
                    print(f"未知命令: {cmd}. 输入 'help' 查看可用命令")
                    
            except KeyboardInterrupt:
                print("\n收到中断信号，正在退出...")
                break
            except EOFError:
                break

    def interactive_call(self):
        """交互式发起通话"""
        print("\n📞 发起通话")
        print("-" * 40)
        
        # 获取最新的客户端列表
        self.request_client_list()
        # 等待客户端列表更新
        if self.client_list_event.wait(timeout=3):
            self.client_list_event.clear()
        
        with self.clients_lock:
            if not self.online_clients:
                print("❌ 没有其他在线客户端")
                return
            
            print("选择要通话的客户端:")
            clients_list = list(self.online_clients.items())
            for i, (client_id, client_info) in enumerate(clients_list, 1):
                client_name = client_info.get('name', client_id)
                print(f"  {i}. {client_name} ({client_id})")
            print(f"  0. 取消")
            
            try:
                choice = input("\n请选择 (0-{}): ".format(len(clients_list))).strip()
                if not choice or choice == '0':
                    print("已取消通话")
                    return
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(clients_list):
                    target_id = clients_list[choice_num - 1][0]
                    target_name = clients_list[choice_num - 1][1].get('name', target_id)
                    
                    print(f"正在呼叫 {target_name}...")
                    self.make_call(target_id)
                else:
                    print("❌ 无效选择")
                    
            except (ValueError, IndexError):
                print("❌ 请输入有效数字")
            except KeyboardInterrupt:
                print("\n已取消通话")

    def interactive_private_message(self):
        """交互式发送私聊消息"""
        print("\n💬 发送私聊消息")
        print("-" * 40)
        
        # 获取最新的客户端列表
        self.request_client_list()
        # 等待客户端列表更新
        if self.client_list_event.wait(timeout=3):
            self.client_list_event.clear()
        
        with self.clients_lock:
            if not self.online_clients:
                print("❌ 没有其他在线客户端")
                return
            
            print("选择私聊对象:")
            clients_list = list(self.online_clients.items())
            for i, (client_id, client_info) in enumerate(clients_list, 1):
                client_name = client_info.get('name', client_id)
                print(f"  {i}. {client_name} ({client_id})")
            print(f"  0. 取消")
            
            try:
                choice = input("\n请选择 (0-{}): ".format(len(clients_list))).strip()
                if not choice or choice == '0':
                    print("已取消发送")
                    return
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(clients_list):
                    target_id = clients_list[choice_num - 1][0]
                    target_name = clients_list[choice_num - 1][1].get('name', target_id)
                    
                    # 输入消息内容
                    message = input(f"\n请输入要发送给 {target_name} 的消息: ").strip()
                    if message:
                        if self.send_private_message(target_id, message):
                            print(f"✅ 消息已发送给 {target_name}")
                        else:
                            print("❌ 消息发送失败")
                    else:
                        print("❌ 消息不能为空")
                else:
                    print("❌ 无效选择")
                    
            except (ValueError, IndexError):
                print("❌ 请输入有效数字")
            except KeyboardInterrupt:
                print("\n已取消发送")

    def interactive_broadcast(self):
        """交互式发送广播消息"""
        print("\n📢 发送广播消息")
        print("-" * 40)
        
        try:
            message = input("请输入广播消息内容: ").strip()
            if message:
                if self.send_broadcast(message):
                    print("✅ 广播消息已发送")
                else:
                    print("❌ 广播消息发送失败")
            else:
                print("❌ 消息不能为空")
        except KeyboardInterrupt:
            print("\n已取消发送")

    def disconnect(self):
        """断开连接"""
        print("正在断开连接...")
        self.running = False
        self.connected = False
        
        # 挂断当前通话
        if self.current_call:
            self.hangup_call()
        
        # 停止音频流
        self.stop_audio_streams()
        
        # 关闭套接字
        if self.message_socket:
            self.message_socket.close()
        if self.audio_socket:
            self.audio_socket.close()
        if self.control_socket:
            self.control_socket.close()
        
        # 清理音频
        if self.audio_instance:
            self.audio_instance.terminate()
        
        print("已断开连接")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='云VoIP客户端')
    parser.add_argument('--server', required=True, help='服务器IP地址')
    parser.add_argument('--name', help='客户端名称')
    parser.add_argument('--port', type=int, default=5060, help='服务器端口 (默认: 5060)')
    
    args = parser.parse_args()
    
    client = CloudVoIPClient(
        server_ip=args.server,
        client_name=args.name,
        base_port=args.port
    )
    
    try:
        if client.connect():
            client.interactive_mode()
    except KeyboardInterrupt:
        print("\n收到中断信号")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
