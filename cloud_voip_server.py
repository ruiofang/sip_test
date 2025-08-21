#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
云主机VoIP服务器
支持多客户端连接和相互通讯的云端VoIP服务

功能特性：
- 多客户端语音通话中转
- 文本消息广播和私聊
- JSON数据传输
- 客户端注册和管理
- 会话状态管理
- 通话房间管理

部署说明：
1. 在云主机上运行此服务器
2. 确保防火墙开放相关端口
3. 客户端通过公网IP连接

使用方法:
python cloud_voip_server.py [--host HOST] [--port PORT]

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
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

try:
    import pyaudio
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("警告: pyaudio未安装，语音功能将不可用")


class CloudVoIPServer:
    def __init__(self, host: str = "0.0.0.0", base_port: int = 5060):
        """
        初始化云VoIP服务器
        
        Args:
            host: 绑定的主机地址，0.0.0.0表示绑定所有接口
            base_port: 基础端口，将使用base_port到base_port+3的端口
        """
        self.host = host
        self.base_port = base_port
        self.running = True
        
        # 服务端口配置
        self.message_port = base_port      # 5060 - 消息服务
        self.audio_port = base_port + 1    # 5061 - 语音数据
        self.control_port = base_port + 2  # 5062 - 控制信令
        self.web_port = base_port + 3      # 5063 - Web管理接口
        
        # 套接字
        self.message_socket = None
        self.audio_socket = None
        self.control_socket = None
        
        # 线程
        self.message_thread = None
        self.audio_thread = None
        self.control_thread = None
        
        # 客户端管理
        self.clients = {}  # {client_id: ClientInfo}
        self.client_sockets = {}  # {client_id: socket}
        self.client_audio_addrs = {}  # {client_id: (ip, port)} - 实际音频地址
        self.rooms = {}  # {room_id: [client_ids]}
        self.calls = {}  # {call_id: {caller, callee, status}}
        
        # 线程锁
        self.clients_lock = threading.Lock()
        self.rooms_lock = threading.Lock()
        self.calls_lock = threading.Lock()
        
        # 日志配置
        self.setup_logging()

    def setup_logging(self):
        """配置日志"""
        logging.basicConfig(
            level=logging.DEBUG,  # 改为DEBUG级别以查看详细信息
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('cloud_voip_server.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def get_public_ip(self):
        """获取公网IP地址"""
        try:
            # 尝试连接外部服务获取公网IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            self.logger.warning(f"无法获取公网IP: {e}")
            return "127.0.0.1"

    def start(self):
        """启动服务器"""
        self.logger.info("正在启动云VoIP服务器...")
        
        # 显示服务器信息
        public_ip = self.get_public_ip()
        self.logger.info(f"服务器地址: {self.host}")
        self.logger.info(f"检测到的IP地址: {public_ip}")
        self.logger.info(f"消息端口: {self.message_port}")
        self.logger.info(f"语音端口: {self.audio_port}")
        self.logger.info(f"控制端口: {self.control_port}")
        
        # 启动各服务
        services_started = 0
        
        if self.init_message_server():
            services_started += 1
        
        if self.init_audio_server():
            services_started += 1
            
        if self.init_control_server():
            services_started += 1
        
        if services_started > 0:
            self.logger.info(f"服务器启动成功，{services_started}/3 个服务已启动")
            self.logger.info("=" * 50)
            self.logger.info("客户端连接信息:")
            self.logger.info(f"  消息服务: {public_ip}:{self.message_port}")
            self.logger.info(f"  语音服务: {public_ip}:{self.audio_port}")
            self.logger.info(f"  控制服务: {public_ip}:{self.control_port}")
            self.logger.info("=" * 50)
            return True
        else:
            self.logger.error("服务器启动失败")
            return False

    def init_message_server(self):
        """初始化消息服务器"""
        try:
            self.message_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.message_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.message_socket.bind((self.host, self.message_port))
            self.message_socket.listen(100)  # 支持更多并发连接
            
            self.message_thread = threading.Thread(target=self.message_server_thread)
            self.message_thread.daemon = True
            self.message_thread.start()
            
            self.logger.info(f"消息服务器已启动 - {self.host}:{self.message_port}")
            return True
            
        except Exception as e:
            self.logger.error(f"消息服务器初始化失败: {e}")
            return False

    def init_audio_server(self):
        """初始化音频服务器"""
        try:
            self.audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.audio_socket.bind((self.host, self.audio_port))
            self.audio_socket.settimeout(1.0)  # 设置超时，避免阻塞
            
            self.audio_thread = threading.Thread(target=self.audio_relay_thread)
            self.audio_thread.daemon = True
            self.audio_thread.start()
            
            self.logger.info(f"音频服务器已启动 - {self.host}:{self.audio_port}")
            return True
            
        except Exception as e:
            self.logger.error(f"音频服务器初始化失败: {e}")
            return False

    def init_control_server(self):
        """初始化控制服务器"""
        try:
            self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.control_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.control_socket.bind((self.host, self.control_port))
            self.control_socket.listen(50)
            
            self.control_thread = threading.Thread(target=self.control_server_thread)
            self.control_thread.daemon = True
            self.control_thread.start()
            
            self.logger.info(f"控制服务器已启动 - {self.host}:{self.control_port}")
            return True
            
        except Exception as e:
            self.logger.error(f"控制服务器初始化失败: {e}")
            return False

    def message_server_thread(self):
        """消息服务器线程"""
        while self.running:
            try:
                client_sock, addr = self.message_socket.accept()
                self.logger.info(f"新客户端连接到消息服务: {addr}")
                
                # 为每个客户端创建处理线程
                client_thread = threading.Thread(
                    target=self.handle_message_client, 
                    args=(client_sock, addr)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    self.logger.error(f"消息服务器线程错误: {e}")

    def control_server_thread(self):
        """控制服务器线程"""
        while self.running:
            try:
                client_sock, addr = self.control_socket.accept()
                self.logger.info(f"新客户端连接到控制服务: {addr}")
                
                # 为每个客户端创建处理线程
                client_thread = threading.Thread(
                    target=self.handle_control_client, 
                    args=(client_sock, addr)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    self.logger.error(f"控制服务器线程错误: {e}")

    def audio_relay_thread(self):
        """音频中转线程"""
        self.logger.info("音频中转线程启动")
        while self.running:
            try:
                data, addr = self.audio_socket.recvfrom(4096)
                self.logger.debug(f"收到音频数据包: {len(data)} 字节 from {addr}")
                
                # 解析音频数据包头部（新格式：16字节源ID + 16字节目标ID + 音频数据）
                if len(data) > 32:
                    # 解析包头
                    source_id = data[:16].rstrip(b'\x00').decode('utf-8')
                    target_id = data[16:32].rstrip(b'\x00').decode('utf-8')
                    audio_data = data[32:]
                    
                    # 更新源客户端的实际音频地址
                    if source_id:
                        self.client_audio_addrs[source_id] = addr
                        self.logger.debug(f"更新客户端 {source_id} 音频地址为: {addr}")
                    
                    self.logger.debug(f"音频转发: {source_id} -> {target_id}, 数据长度: {len(audio_data)}")
                    
                    # 转发音频数据
                    self.forward_audio(source_id, target_id, audio_data, addr)
                else:
                    self.logger.warning(f"收到无效音频数据包，长度: {len(data)}")
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.logger.error(f"音频中转线程错误: {e}")

    def handle_message_client(self, client_sock: socket.socket, addr: Tuple[str, int]):
        """处理消息客户端"""
        client_id = None
        try:
            while self.running:
                # 接收消息长度
                length_data = client_sock.recv(4)
                if not length_data:
                    break
                
                msg_length = struct.unpack('I', length_data)[0]
                if msg_length > 1024 * 1024:  # 1MB限制
                    self.logger.warning(f"消息长度过大: {msg_length}")
                    break
                
                # 接收完整消息
                data = b''
                while len(data) < msg_length:
                    chunk = client_sock.recv(min(msg_length - len(data), 4096))
                    if not chunk:
                        break
                    data += chunk
                
                if len(data) != msg_length:
                    break
                
                # 解析消息
                try:
                    message = json.loads(data.decode('utf-8'))
                    client_id = message.get('client_id', client_id)
                    
                    # 更新客户端信息
                    if client_id:
                        with self.clients_lock:
                            self.clients[client_id] = {
                                'addr': addr,
                                'socket': client_sock,
                                'last_seen': time.time(),
                                'status': 'online'
                            }
                            self.client_sockets[client_id] = client_sock
                    
                    # 处理不同类型的消息
                    self.process_message(message, client_sock, addr, client_id)
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON解析错误: {e}")
                    
        except Exception as e:
            self.logger.error(f"处理消息客户端错误: {e}")
        finally:
            # 清理客户端
            if client_id:
                with self.clients_lock:
                    if client_id in self.clients:
                        del self.clients[client_id]
                    if client_id in self.client_sockets:
                        del self.client_sockets[client_id]
                    # 清理音频地址缓存
                    if client_id in self.client_audio_addrs:
                        del self.client_audio_addrs[client_id]
                self.logger.info(f"客户端 {client_id} ({addr}) 已断开连接")
            
            try:
                client_sock.close()
            except:
                pass

    def handle_control_client(self, client_sock: socket.socket, addr: Tuple[str, int]):
        """处理控制客户端"""
        try:
            while self.running:
                data = client_sock.recv(1024)
                if not data:
                    break
                
                try:
                    message = json.loads(data.decode('utf-8'))
                    self.process_control_message(message, client_sock, addr)
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            self.logger.error(f"处理控制客户端错误: {e}")
        finally:
            try:
                client_sock.close()
            except:
                pass

    def process_message(self, message: Dict[str, Any], client_sock: socket.socket, 
                       addr: Tuple[str, int], client_id: str):
        """处理客户端消息"""
        msg_type = message.get('type', 'unknown')
        self.logger.info(f"处理消息类型: {msg_type} from {client_id}")
        
        if msg_type == 'register':
            self.handle_client_register(message, client_sock, addr)
        elif msg_type == 'broadcast':
            self.handle_broadcast_message(message, client_id)
        elif msg_type == 'private':
            self.handle_private_message(message, client_id)
        elif msg_type == 'call_request':
            self.handle_call_request(message, client_id)
        elif msg_type == 'call_answer':
            self.handle_call_answer(message, client_id)
        elif msg_type == 'call_hangup':
            self.handle_call_hangup(message, client_id)
        elif msg_type == 'join_room':
            self.handle_join_room(message, client_id)
        elif msg_type == 'leave_room':
            self.handle_leave_room(message, client_id)
        elif msg_type == 'get_clients':
            self.logger.info(f"调用 handle_get_clients 函数")
            self.handle_get_clients(message, client_sock)
        else:
            self.logger.warning(f"未知消息类型: {msg_type}")

    def handle_client_register(self, message: Dict[str, Any], client_sock: socket.socket, addr: Tuple[str, int]):
        """处理客户端注册"""
        client_id = message.get('client_id')
        client_name = message.get('client_name', f'Client_{client_id}')
        audio_port = message.get('audio_port')  # 获取客户端音频端口
        
        with self.clients_lock:
            self.clients[client_id] = {
                'id': client_id,
                'name': client_name,
                'addr': addr,
                'audio_port': audio_port,  # 保存音频端口信息
                'socket': client_sock,
                'last_seen': time.time(),
                'status': 'online'
            }
            self.client_sockets[client_id] = client_sock
        
        # 发送注册确认
        response = {
            'type': 'register_response',
            'status': 'success',
            'client_id': client_id,
            'server_time': time.time()
        }
        self.send_message(client_sock, response)
        
        audio_info = f", 音频端口: {audio_port}" if audio_port else ", 无音频支持"
        self.logger.info(f"客户端已注册: {client_name} ({client_id}) from {addr}{audio_info}")

    def handle_broadcast_message(self, message: Dict[str, Any], sender_id: str):
        """处理广播消息"""
        content = message.get('content', '')
        
        # 构造广播消息
        broadcast_msg = {
            'type': 'broadcast',
            'from': sender_id,
            'content': content,
            'timestamp': time.time()
        }
        
        # 发送给所有在线客户端
        with self.clients_lock:
            for client_id, client_info in self.clients.items():
                if client_id != sender_id and client_info['status'] == 'online':
                    try:
                        self.send_message(client_info['socket'], broadcast_msg)
                    except:
                        pass
        
        self.logger.info(f"广播消息 from {sender_id}: {content}")

    def handle_private_message(self, message: Dict[str, Any], sender_id: str):
        """处理私聊消息"""
        target_id = message.get('target')
        content = message.get('content', '')
        
        # 构造私聊消息
        private_msg = {
            'type': 'private',
            'from': sender_id,
            'content': content,
            'timestamp': time.time()
        }
        
        # 发送给目标客户端
        with self.clients_lock:
            if target_id in self.clients and self.clients[target_id]['status'] == 'online':
                try:
                    self.send_message(self.clients[target_id]['socket'], private_msg)
                    self.logger.info(f"私聊消息 {sender_id} -> {target_id}: {content}")
                except:
                    self.logger.warning(f"发送私聊消息失败: {sender_id} -> {target_id}")

    def handle_call_request(self, message: Dict[str, Any], caller_id: str):
        """处理通话请求"""
        callee_id = message.get('target')
        
        if not callee_id:
            return
        
        # 生成通话ID
        call_id = f"{caller_id}_{callee_id}_{int(time.time())}"
        
        # 记录通话信息
        with self.calls_lock:
            self.calls[call_id] = {
                'caller': caller_id,
                'callee': callee_id,
                'status': 'requesting',
                'start_time': time.time()
            }
        
        # 转发通话请求
        call_request = {
            'type': 'call_request',
            'call_id': call_id,
            'from': caller_id,
            'timestamp': time.time()
        }
        
        with self.clients_lock:
            if callee_id in self.clients and self.clients[callee_id]['status'] == 'online':
                try:
                    self.send_message(self.clients[callee_id]['socket'], call_request)
                    self.logger.info(f"通话请求: {caller_id} -> {callee_id} (Call ID: {call_id})")
                except:
                    self.logger.warning(f"发送通话请求失败: {caller_id} -> {callee_id}")

    def handle_call_answer(self, message: Dict[str, Any], client_id: str):
        """处理通话应答"""
        call_id = message.get('call_id')
        accepted = message.get('accepted', False)
        
        if not call_id:
            return
        
        with self.calls_lock:
            if call_id in self.calls:
                call_info = self.calls[call_id]
                if accepted:
                    call_info['status'] = 'active'
                else:
                    call_info['status'] = 'rejected'
                
                # 通知发起者
                caller_id = call_info['caller']
                response = {
                    'type': 'call_answer',
                    'call_id': call_id,
                    'accepted': accepted,
                    'from': client_id,
                    'timestamp': time.time()
                }
                
                with self.clients_lock:
                    if caller_id in self.clients:
                        try:
                            self.send_message(self.clients[caller_id]['socket'], response)
                            self.logger.info(f"通话应答: {client_id} {'接受' if accepted else '拒绝'} {caller_id} (Call ID: {call_id})")
                        except:
                            pass

    def handle_call_hangup(self, message: Dict[str, Any], client_id: str):
        """处理挂断通话"""
        call_id = message.get('call_id')
        
        if not call_id:
            return
        
        with self.calls_lock:
            if call_id in self.calls:
                call_info = self.calls[call_id]
                call_info['status'] = 'ended'
                
                # 通知另一方
                other_client = call_info['callee'] if client_id == call_info['caller'] else call_info['caller']
                
                hangup_msg = {
                    'type': 'call_hangup',
                    'call_id': call_id,
                    'from': client_id,
                    'timestamp': time.time()
                }
                
                with self.clients_lock:
                    if other_client in self.clients:
                        try:
                            self.send_message(self.clients[other_client]['socket'], hangup_msg)
                            self.logger.info(f"通话结束: {call_id}")
                        except:
                            pass
                
                # 删除通话记录
                del self.calls[call_id]

    def handle_join_room(self, message: Dict[str, Any], client_id: str):
        """处理加入房间"""
        room_id = message.get('room_id')
        
        if not room_id:
            return
        
        with self.rooms_lock:
            if room_id not in self.rooms:
                self.rooms[room_id] = []
            
            if client_id not in self.rooms[room_id]:
                self.rooms[room_id].append(client_id)
        
        self.logger.info(f"客户端 {client_id} 加入房间 {room_id}")

    def handle_leave_room(self, message: Dict[str, Any], client_id: str):
        """处理离开房间"""
        room_id = message.get('room_id')
        
        if not room_id:
            return
        
        with self.rooms_lock:
            if room_id in self.rooms and client_id in self.rooms[room_id]:
                self.rooms[room_id].remove(client_id)
                if not self.rooms[room_id]:
                    del self.rooms[room_id]
        
        self.logger.info(f"客户端 {client_id} 离开房间 {room_id}")

    def handle_get_clients(self, message: Dict[str, Any], client_sock: socket.socket):
        """处理获取客户端列表请求"""
        self.logger.info("收到获取客户端列表请求")
        with self.clients_lock:
            client_list = []
            for client_id, client_info in self.clients.items():
                client_list.append({
                    'id': client_id,
                    'name': client_info.get('name', client_id),
                    'status': client_info['status'],
                    'last_seen': client_info['last_seen'],
                    'audio_port': client_info.get('audio_port'),  # 添加音频端口信息
                    'addr': client_info.get('addr')  # 添加地址信息用于调试
                })
        
        self.logger.info(f"准备发送客户端列表，共 {len(client_list)} 个客户端")
        response = {
            'type': 'client_list',
            'clients': client_list,
            'timestamp': time.time()
        }
        
        try:
            self.send_message(client_sock, response)
            self.logger.info("客户端列表发送成功")
        except Exception as e:
            self.logger.error(f"发送客户端列表失败: {e}")

    def process_control_message(self, message: Dict[str, Any], client_sock: socket.socket, addr: Tuple[str, int]):
        """处理控制消息"""
        cmd_type = message.get('type', 'unknown')
        
        if cmd_type == 'get_status':
            status = self.get_server_status()
            response = {
                'type': 'status_response',
                'status': status,
                'timestamp': time.time()
            }
            self.send_message(client_sock, response)

    def forward_audio(self, source_id: str, target_id: str, audio_data: bytes, source_addr: Tuple[str, int]):
        """转发音频数据"""
        try:
            if len(audio_data) > 0:
                self.logger.debug(f"转发音频数据: {source_id} -> {target_id}, {len(audio_data)} bytes")
                
                # 查找目标客户端的音频地址（优先使用实际音频地址）
                target_audio_addr = None
                
                # 首先尝试使用记录的实际音频地址
                if target_id in self.client_audio_addrs:
                    target_audio_addr = self.client_audio_addrs[target_id]
                    self.logger.debug(f"使用已记录的音频地址: {target_audio_addr}")
                else:
                    # 如果没有实际地址，尝试使用注册时的信息
                    with self.clients_lock:
                        if target_id in self.clients:
                            client_info = self.clients[target_id]
                            if client_info['status'] == 'online' and client_info.get('audio_port'):
                                # 使用客户端的IP和其注册时提供的音频端口
                                client_ip = client_info['addr'][0]
                                audio_port = client_info['audio_port']
                                target_audio_addr = (client_ip, audio_port)
                                self.logger.debug(f"使用注册时的音频地址: {target_audio_addr}")
                
                if target_audio_addr:
                    # 重新构造数据包（保持原格式，让接收端能正确解析）
                    header = source_id.encode('utf-8').ljust(16, b'\x00')
                    header += target_id.encode('utf-8').ljust(16, b'\x00')
                    packet = header + audio_data
                    
                    # 转发到目标客户端
                    self.audio_socket.sendto(packet, target_audio_addr)
                    self.logger.debug(f"音频数据已转发到 {target_audio_addr}")
                else:
                    self.logger.warning(f"找不到目标客户端 {target_id} 的音频地址或客户端不在线")
        except Exception as e:
            self.logger.error(f"转发音频数据失败: {e}")

    def send_message(self, client_sock: socket.socket, message: Dict[str, Any]):
        """发送消息给客户端"""
        try:
            data = json.dumps(message).encode('utf-8')
            length = struct.pack('I', len(data))
            msg_type = message.get('type', 'unknown')
            self.logger.info(f"[DEBUG] 准备发送消息类型 {msg_type}，数据长度: {len(data)}")
            client_sock.send(length + data)
            self.logger.info(f"[DEBUG] 消息 {msg_type} 发送成功")
        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")
            import traceback
            self.logger.error(f"详细错误: {traceback.format_exc()}")

    def get_server_status(self) -> Dict[str, Any]:
        """获取服务器状态"""
        with self.clients_lock:
            online_clients = len([c for c in self.clients.values() if c['status'] == 'online'])
            
        with self.rooms_lock:
            active_rooms = len(self.rooms)
            
        with self.calls_lock:
            active_calls = len([c for c in self.calls.values() if c['status'] == 'active'])
        
        return {
            'server_time': time.time(),
            'uptime': time.time() - getattr(self, 'start_time', time.time()),
            'clients': {
                'total': len(self.clients),
                'online': online_clients
            },
            'rooms': {
                'active': active_rooms
            },
            'calls': {
                'active': active_calls,
                'total': len(self.calls)
            },
            'services': {
                'message': self.message_socket is not None,
                'audio': self.audio_socket is not None,
                'control': self.control_socket is not None
            }
        }

    def interactive_mode(self):
        """交互模式"""
        print("\n" + "=" * 60)
        print("云VoIP服务器管理控制台")
        print("=" * 60)
        print("可用命令:")
        print("  status      - 显示服务器状态")
        print("  clients     - 显示连接的客户端")
        print("  rooms       - 显示活动房间")
        print("  calls       - 显示活动通话")
        print("  broadcast <message> - 广播消息")
        print("  kick <client_id>    - 踢出客户端")
        print("  shutdown    - 关闭服务器")
        print("  help        - 显示帮助")
        print("=" * 60)
        
        while self.running:
            try:
                cmd_line = input("server> ").strip()
                if not cmd_line:
                    continue
                
                parts = cmd_line.split(' ', 1)
                cmd = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ''
                
                if cmd == 'shutdown':
                    print("正在关闭服务器...")
                    break
                elif cmd == 'status':
                    status = self.get_server_status()
                    print(json.dumps(status, indent=2, ensure_ascii=False))
                elif cmd == 'clients':
                    with self.clients_lock:
                        print(f"\n连接的客户端 ({len(self.clients)}):")
                        for client_id, client_info in self.clients.items():
                            name = client_info.get('name', client_id)
                            addr = client_info['addr']
                            status = client_info['status']
                            last_seen = datetime.fromtimestamp(client_info['last_seen']).strftime('%H:%M:%S')
                            print(f"  - {name} ({client_id}) [{status}] {addr} (最后活动: {last_seen})")
                elif cmd == 'rooms':
                    with self.rooms_lock:
                        print(f"\n活动房间 ({len(self.rooms)}):")
                        for room_id, members in self.rooms.items():
                            print(f"  - {room_id}: {len(members)} 成员 {members}")
                elif cmd == 'calls':
                    with self.calls_lock:
                        print(f"\n活动通话 ({len(self.calls)}):")
                        for call_id, call_info in self.calls.items():
                            status = call_info['status']
                            caller = call_info['caller']
                            callee = call_info['callee']
                            duration = time.time() - call_info['start_time']
                            print(f"  - {call_id}: {caller} <-> {callee} [{status}] ({duration:.1f}s)")
                elif cmd == 'broadcast' and args:
                    broadcast_msg = {
                        'type': 'broadcast',
                        'from': 'server',
                        'content': args,
                        'timestamp': time.time()
                    }
                    
                    sent_count = 0
                    with self.clients_lock:
                        for client_id, client_info in self.clients.items():
                            if client_info['status'] == 'online':
                                try:
                                    self.send_message(client_info['socket'], broadcast_msg)
                                    sent_count += 1
                                except:
                                    pass
                    
                    print(f"广播消息已发送给 {sent_count} 个客户端")
                elif cmd == 'kick' and args:
                    client_id = args.strip()
                    with self.clients_lock:
                        if client_id in self.clients:
                            try:
                                self.clients[client_id]['socket'].close()
                                print(f"客户端 {client_id} 已被踢出")
                            except:
                                print(f"踢出客户端失败: {client_id}")
                        else:
                            print(f"客户端 {client_id} 不存在")
                elif cmd == 'help':
                    print("\n可用命令:")
                    print("  status      - 显示服务器状态")
                    print("  clients     - 显示连接的客户端")
                    print("  rooms       - 显示活动房间")
                    print("  calls       - 显示活动通话")
                    print("  broadcast <message> - 广播消息")
                    print("  kick <client_id>    - 踢出客户端")
                    print("  shutdown    - 关闭服务器")
                    print("  help        - 显示帮助")
                else:
                    print(f"未知命令: {cmd}. 输入 'help' 查看可用命令")
                    
            except KeyboardInterrupt:
                print("\n收到中断信号，正在关闭服务器...")
                break
            except EOFError:
                break

    def stop(self):
        """停止服务器"""
        self.logger.info("正在关闭服务器...")
        self.running = False
        
        # 关闭套接字
        if self.message_socket:
            self.message_socket.close()
        if self.audio_socket:
            self.audio_socket.close()
        if self.control_socket:
            self.control_socket.close()
        
        # 关闭所有客户端连接
        with self.clients_lock:
            for client_info in self.clients.values():
                try:
                    client_info['socket'].close()
                except:
                    pass
        
        self.logger.info("服务器已关闭")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='云VoIP服务器')
    parser.add_argument('--host', default='0.0.0.0', help='绑定的主机地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5060, help='基础端口号 (默认: 5060)')
    parser.add_argument('--daemon', action='store_true', help='后台运行模式，不进入交互界面')
    
    args = parser.parse_args()
    
    server = CloudVoIPServer(host=args.host, base_port=args.port)
    server.start_time = time.time()
    
    try:
        if server.start():
            if args.daemon:
                # 后台运行模式，保持服务运行
                print(f"服务器已启动 (后台模式) - {args.host}:{args.port}")
                print("按 Ctrl+C 停止服务")
                while True:
                    time.sleep(1)
            else:
                server.interactive_mode()
    except KeyboardInterrupt:
        print("\n收到中断信号")
    finally:
        server.stop()


if __name__ == "__main__":
    main()
