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
python3 cloud_voip_client.py [--server SERVER_IP] [--name CLIENT_NAME]
未提供 --server 时，将尝试从 client_config.json 读取默认服务器。

作者: RUIO
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
import numpy as np
from typing import Dict, Any, Optional, List

# 抑制ALSA警告
os.environ['ALSA_PCM_CARD'] = '0'
os.environ['ALSA_PCM_DEVICE'] = '0'

# 抑制numpy运行时警告
warnings.filterwarnings("ignore", category=RuntimeWarning, message="invalid value encountered in divide")
warnings.filterwarnings("ignore", category=RuntimeWarning, message="divide by zero encountered")

try:
    import pyaudio
    AUDIO_AVAILABLE = True
    warnings.filterwarnings("ignore", category=UserWarning)
except ImportError:
    AUDIO_AVAILABLE = False
    print("警告: pyaudio未安装，语音功能将不可用")


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


def load_client_config(config_file='client_config.json'):
    """加载客户端配置，失败时返回空配置。"""
    config_path = get_config_path(config_file)

    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as config_handle:
                return json.load(config_handle)
    except Exception as error:
        print(f"⚠️ 加载客户端配置失败: {error}")

    return {}


def resolve_server_args(args):
    """优先使用命令行参数，否则从客户端配置中解析服务器和默认名称。"""
    config = load_client_config()
    user_config = config.get('user', {})
    servers = config.get('servers', {})

    server_ip = args.server
    port = args.port
    client_name = args.name or user_config.get('default_name')

    if server_ip:
        return server_ip, port, client_name

    last_server = user_config.get('last_server', 'default')
    server_config = servers.get(last_server) or servers.get('default')

    if not server_config:
        raise ValueError('未提供 --server，且 client_config.json 中没有可用的服务器配置')

    server_ip = server_config.get('ip')
    port = server_config.get('port', port)

    if not server_ip:
        raise ValueError('client_config.json 中的服务器配置缺少 ip 字段')

    print(f"ℹ️ 未提供 --server，使用配置服务器: {server_ip}:{port}")
    return server_ip, port, client_name


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
        
        # 啸叫抑制配置
        self.echo_cancellation = True        # 回声消除
        self.noise_suppression = True        # 噪声抑制
        self.auto_gain_control = True        # 自动增益控制
        self.voice_activity_detection = True # 语音活动检测
        
        # 音频处理参数
        self.input_volume = 0.7              # 输入音量 (0.0-1.0)
        self.output_volume = 0.8             # 输出音量 (0.0-1.0)
        self.noise_gate_threshold = 0.01     # 噪声门限阈值
        self.echo_delay_samples = 1024       # 回声延迟采样数
        
        # 音频缓冲和历史数据
        self.audio_history = []              # 输出音频历史，用于回声消除
        self.history_size = 5                # 保留历史帧数（减少到5帧）
        self.silence_counter = 0             # 静音计数器
        self.silence_threshold = 50          # 静音阈值（连续静音帧数）
        
        # 改进的回声消除参数
        self.echo_threshold = 0.6            # 回声检测阈值（提高阈值）
        self.echo_suppression_factor = 0.7   # 回声抑制因子（降低抑制强度）
        self.echo_learning_rate = 0.1        # 自适应学习率
        self.min_suppression = 0.3           # 最小抑制量，避免完全静音
        
        # 语音增强参数
        self.spectral_subtraction = False    # 谱减法降噪
        self.adaptive_threshold = True       # 自适应阈值
        self.echo_detection_window = 3       # 回声检测窗口（帧数）
        
        # 线程锁
        self.clients_lock = threading.Lock()
        self.call_lock = threading.Lock()
        self.client_list_event = threading.Event()  # 用于客户端列表同步
        
        # 加载音频配置
        self.load_audio_config()

    def load_audio_config(self, config_file='audio_config.json'):
        """加载音频配置"""
        try:
            config_path = get_config_path(config_file)
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                audio_settings = config.get('audio_settings', {})
                
                # 更新基础配置
                self.echo_cancellation = audio_settings.get('echo_cancellation', self.echo_cancellation)
                self.noise_suppression = audio_settings.get('noise_suppression', self.noise_suppression)
                self.auto_gain_control = audio_settings.get('auto_gain_control', self.auto_gain_control)
                self.voice_activity_detection = audio_settings.get('voice_activity_detection', self.voice_activity_detection)
                self.input_volume = audio_settings.get('input_volume', self.input_volume)
                self.output_volume = audio_settings.get('output_volume', self.output_volume)
                self.noise_gate_threshold = audio_settings.get('noise_gate_threshold', self.noise_gate_threshold)
                self.echo_delay_samples = audio_settings.get('echo_delay_samples', self.echo_delay_samples)
                self.history_size = audio_settings.get('history_size', self.history_size)
                self.silence_threshold = audio_settings.get('silence_threshold', self.silence_threshold)
                
                # 更新新的回声消除参数
                self.echo_threshold = audio_settings.get('echo_threshold', getattr(self, 'echo_threshold', 0.6))
                self.echo_suppression_factor = audio_settings.get('echo_suppression_factor', getattr(self, 'echo_suppression_factor', 0.7))
                self.min_suppression = audio_settings.get('min_suppression', getattr(self, 'min_suppression', 0.3))
                self.echo_learning_rate = audio_settings.get('echo_learning_rate', getattr(self, 'echo_learning_rate', 0.1))
                self.spectral_subtraction = audio_settings.get('spectral_subtraction', getattr(self, 'spectral_subtraction', False))
                self.adaptive_threshold = audio_settings.get('adaptive_threshold', getattr(self, 'adaptive_threshold', True))
                self.echo_detection_window = audio_settings.get('echo_detection_window', getattr(self, 'echo_detection_window', 3))
                self.debug_audio_processing = audio_settings.get('debug_audio_processing', False)
                
                # 高级设置
                advanced_settings = config.get('advanced_settings', {})
                if advanced_settings.get('chunk_size'):
                    self.chunk = advanced_settings['chunk_size']
                if advanced_settings.get('sample_rate'):
                    self.rate = advanced_settings['sample_rate']
                
                print(f"✅ 已加载音频配置: {config_file}")
                if self.debug_audio_processing:
                    print("🐛 调试模式已启用")
            else:
                print(f"⚠️ 音频配置文件不存在: {config_file}，正在创建默认配置...")
                self._create_default_audio_config(config_path)
                print(f"✅ 已创建默认音频配置文件: {config_file}")
                
        except Exception as e:
            print(f"❌ 加载音频配置失败: {e}，使用默认配置")

    def _create_default_audio_config(self, config_path):
        """创建默认的音频配置文件"""
        default_config = {
            "audio_settings": {
                "echo_cancellation": self.echo_cancellation,
                "noise_suppression": self.noise_suppression,
                "auto_gain_control": self.auto_gain_control,
                "voice_activity_detection": self.voice_activity_detection,
                "input_volume": self.input_volume,
                "output_volume": self.output_volume,
                "noise_gate_threshold": self.noise_gate_threshold,
                "echo_delay_samples": self.echo_delay_samples,
                "history_size": self.history_size,
                "silence_threshold": self.silence_threshold,
                "echo_threshold": getattr(self, 'echo_threshold', 0.6),
                "echo_suppression_factor": getattr(self, 'echo_suppression_factor', 0.7),
                "min_suppression": getattr(self, 'min_suppression', 0.3),
                "echo_learning_rate": getattr(self, 'echo_learning_rate', 0.1),
                "spectral_subtraction": getattr(self, 'spectral_subtraction', False),
                "adaptive_threshold": getattr(self, 'adaptive_threshold', True),
                "echo_detection_window": getattr(self, 'echo_detection_window', 3),
                "debug_audio_processing": False
            },
            "advanced_settings": {
                "chunk_size": self.chunk,
                "sample_rate": self.rate,
                "channels": self.channels,
                "format": "paInt16",
                "low_latency_mode": True,
                "audio_buffer_size": 4096
            },
            "description": {
                "echo_cancellation": "回声消除 - 智能检测并减少扬声器声音被麦克风捕获",
                "noise_suppression": "噪声抑制 - 使用噪声门减少背景噪音",
                "auto_gain_control": "自动增益控制 - 保持音量稳定",
                "voice_activity_detection": "语音活动检测 - 只在有语音时发送音频",
                "input_volume": "输入音量 (0.0-1.0)",
                "output_volume": "输出音量 (0.0-1.0)",
                "noise_gate_threshold": "噪声门阈值 - 低于此值的信号将被衰减",
                "echo_threshold": "回声检测相关性阈值 - 越高越严格 (推荐0.6-0.8)",
                "echo_suppression_factor": "回声抑制强度 - 越高抑制越强 (推荐0.5-0.8)",
                "min_suppression": "最小抑制比例 - 避免完全静音 (推荐0.2-0.4)",
                "adaptive_threshold": "自适应阈值 - 根据环境自动调整检测阈值",
                "debug_audio_processing": "调试模式 - 显示详细的音频处理信息"
            },
            "troubleshooting": {
                "no_sound_after_echo_cancellation": {
                    "problem": "启用回声消除后没有声音",
                    "solutions": [
                        "降低echo_threshold到0.5或更低",
                        "增加min_suppression到0.4或更高",
                        "启用debug_audio_processing查看处理详情",
                        "暂时关闭echo_cancellation进行对比"
                    ]
                },
                "sound_cutting_off": {
                    "problem": "声音断断续续",
                    "solutions": [
                        "关闭voice_activity_detection",
                        "降低noise_gate_threshold到0.005",
                        "启用adaptive_threshold",
                        "检查网络连接稳定性"
                    ]
                },
                "echo_still_present": {
                    "problem": "仍然有回声",
                    "solutions": [
                        "降低echo_threshold到0.4",
                        "增加echo_suppression_factor到0.8",
                        "使用耳机替代扬声器",
                        "调整麦克风和扬声器位置"
                    ]
                }
            }
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ 创建默认配置文件失败: {e}")

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
            # 使用 sendall 避免短发送导致服务端接收不到完整包
            self.message_socket.sendall(length + data)
            return True
            
        except Exception as e:
            print(f"发送消息失败: {e}")
            return False

    def _recv_exact(self, size: int) -> Optional[bytes]:
        """从消息 socket 精确读取 size 字节，连接断开返回 None。"""
        data = bytearray()
        while len(data) < size:
            chunk = self.message_socket.recv(size - len(data))
            if not chunk:
                return None
            data.extend(chunk)
        return bytes(data)

    def message_receive_thread(self):
        """消息接收线程"""
        while self.running and self.connected:
            try:
                # 精确接收 4 字节长度，避免半包导致 struct.unpack 异常
                length_data = self._recv_exact(4)
                if not length_data:
                    break
                
                msg_length = struct.unpack('I', length_data)[0]
                if msg_length == 0 or msg_length > 1024 * 1024:  # 1MB限制
                    print(f"⚠️ 收到异常消息长度: {msg_length}")
                    break
                
                # 精确接收完整消息
                data = self._recv_exact(msg_length)
                if data is None:
                    break
                
                # 解析并处理消息
                try:
                    message = json.loads(data.decode('utf-8'))
                    self.handle_server_message(message)
                except json.JSONDecodeError as e:
                    print(f"⚠️ 解析服务器消息失败: {e}")
                    
            except Exception as e:
                if self.running:
                    print(f"接收消息错误: {e}")
                break
        
        self.connected = False
        print("与服务器的连接已断开")

    def handle_server_message(self, message: Dict[str, Any]):
        """处理服务器消息"""
        msg_type = message.get('type', 'unknown')
        
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
            self.handle_client_list(message)
        elif msg_type == 'heartbeat':
            self.handle_heartbeat(message)
        else:
            print(f"收到未知消息类型: {msg_type}")

    def handle_heartbeat(self, message: Dict[str, Any]):
        """响应服务器心跳，避免被服务端误判为超时断开。"""
        response = {
            'type': 'heartbeat_response',
            'timestamp': time.time(),
            'server_time': message.get('server_time'),
            'original_timestamp': message.get('timestamp')
        }
        self.send_message(response)

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
        
        # 存储待处理的通话请求
        if not hasattr(self, 'pending_calls'):
            self.pending_calls = {}
        
        self.pending_calls[call_id] = {
            'caller': caller,
            'timestamp': time.time()
        }
        
        # 立即显示选项界面
        self.show_call_options(call_id, caller)

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

    def show_call_options(self, call_id: str, caller: str):
        """显示通话选项界面"""
        # 自动接听模式，无需用户输入
        def handle_call_input():
            print(f"\n{'='*50}")
            print(f"📞 来自 {caller} 的通话请求")
            print(f"通话ID: {call_id}")
            print(f"{'='*50}")
            print("🤖 自动接听模式: 正在自动接受通话...")
            print(f"{'='*50}")
            
            # 自动接受通话
            if call_id in getattr(self, 'pending_calls', {}):
                self.accept_call(call_id)
            else:
                print(f"❌ 通话ID {call_id} 不存在")
        
        # 在单独线程中处理
        input_thread = threading.Thread(target=handle_call_input, daemon=True)
        input_thread.start()

    def handle_client_list(self, message: Dict[str, Any]):
        """处理客户端列表"""
        clients = message.get('clients', [])
        
        with self.clients_lock:
            self.online_clients = {}
            for client in clients:
                client_id = client['id']
                if client_id != self.client_id:  # 排除自己
                    self.online_clients[client_id] = client
        
        # 设置事件，通知show_clients函数
        self.client_list_event.set()

    def request_client_list(self):
        """请求客户端列表"""
        message = {
            'type': 'get_clients',
            'timestamp': time.time()
        }
        success = self.send_message(message)
        return success

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
            # 启动音频输入流（麦克风）- 添加更多配置以减少延迟
            self.audio_input = self.audio_instance.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk,
                input_device_index=None,  # 使用默认输入设备
                # 添加低延迟配置
                stream_callback=None,
                start=False
            )
            
            # 启动音频输出流（扬声器）- 添加更多配置以减少延迟
            self.audio_output = self.audio_instance.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.rate,
                output=True,
                frames_per_buffer=self.chunk,
                output_device_index=None,  # 使用默认输出设备
                # 添加低延迟配置
                stream_callback=None,
                start=False
            )
            
            # 初始化音频处理
            self.audio_processing_init()
            
            # 清除音频历史
            self.audio_history = []
            self.silence_counter = 0
            
            # 启动音频流
            self.audio_input.start_stream()
            self.audio_output.start_stream()
            
            # 启动音频线程
            self.audio_send_thread = threading.Thread(target=self.audio_send_loop)
            self.audio_send_thread.daemon = True
            self.audio_send_thread.start()
            
            self.audio_receive_thread = threading.Thread(target=self.audio_receive_loop)
            self.audio_receive_thread.daemon = True
            self.audio_receive_thread.start()
            
            print("🎵 音频流已启动")
            if self.echo_cancellation:
                print("🔇 回声消除: 启用")
            if self.noise_suppression:
                print("🔇 噪声抑制: 启用")
            if self.auto_gain_control:
                print("🔊 自动增益控制: 启用")
            if self.voice_activity_detection:
                print("🗣️ 语音活动检测: 启用")
            
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

    def audio_processing_init(self):
        """初始化音频处理参数"""
        try:
            # 检查numpy是否可用
            global np
            if 'np' not in globals():
                import numpy as np
        except ImportError:
            print("警告: numpy未安装，高级音频处理功能将受限")
            return False
        return True

    def apply_noise_gate(self, audio_data):
        """应用噪声门，抑制低于阈值的信号"""
        if not hasattr(self, 'numpy_available'):
            self.numpy_available = self.audio_processing_init()
        
        if not self.numpy_available:
            return audio_data
        
        try:
            # 将字节数据转换为numpy数组
            samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # 计算RMS音量
            rms = np.sqrt(np.mean(samples**2))
            
            # 如果音量低于阈值，则静音
            if rms < self.noise_gate_threshold:
                samples = samples * 0.1  # 大幅衰减而不是完全静音
                self.silence_counter += 1
            else:
                self.silence_counter = 0
            
            # 转换回字节数据
            return (samples * 32767).astype(np.int16).tobytes()
            
        except Exception as e:
            # 如果处理失败，返回原始数据
            return audio_data

    def apply_echo_cancellation(self, input_audio, reference_audio=None):
        """智能回声消除 - 改进版本"""
        if not hasattr(self, 'numpy_available'):
            self.numpy_available = self.audio_processing_init()
        
        if not self.numpy_available or not reference_audio or len(self.audio_history) == 0:
            return input_audio
        
        try:
            # 将音频数据转换为numpy数组
            input_samples = np.frombuffer(input_audio, dtype=np.int16).astype(np.float32) / 32768.0
            
            # 初始化回声检测变量
            echo_detected = False
            suppression_factor = 1.0
            
            # 多帧回声检测
            correlation_scores = []
            
            # 检查最近几帧的相关性
            check_frames = min(len(self.audio_history), self.echo_detection_window)
            
            for i in range(check_frames):
                ref_samples = np.frombuffer(self.audio_history[-(i+1)], dtype=np.int16).astype(np.float32) / 32768.0
                
                if len(input_samples) == len(ref_samples):
                    # 检查数据有效性，避免除零警告
                    input_std = np.std(input_samples)
                    ref_std = np.std(ref_samples)
                    
                    # 只有在两个信号都有足够的变化时才计算相关性
                    if input_std > 1e-8 and ref_std > 1e-8:
                        # 计算互相关
                        correlation = np.corrcoef(input_samples, ref_samples)[0, 1]
                        if not np.isnan(correlation):
                            correlation_scores.append(abs(correlation))
            
            # 如果有有效的相关性分数
            if correlation_scores:
                max_correlation = max(correlation_scores)
                avg_correlation = np.mean(correlation_scores)
                
                # 更智能的回声检测逻辑
                input_energy = np.sum(input_samples**2)
                
                # 只有在输入能量足够且相关性很高时才认为是回声
                if (max_correlation > self.echo_threshold and 
                    avg_correlation > 0.4 and 
                    input_energy > 0.001):  # 确保有足够的信号能量
                    
                    echo_detected = True
                    
                    # 动态计算抑制因子
                    # 相关性越高，抑制越强，但保留最小比例
                    base_suppression = max_correlation * self.echo_suppression_factor
                    suppression_factor = max(self.min_suppression, 1.0 - base_suppression)
                    
                    # 频率域处理（如果启用谱减法）
                    if self.spectral_subtraction:
                        suppression_factor = self.apply_spectral_subtraction(
                            input_samples, ref_samples, suppression_factor)
            
            # 应用抑制
            if echo_detected:
                # 渐进式抑制，避免突然的音量变化
                output_samples = input_samples * suppression_factor
                
                # 保留一些原始信号特征，避免完全静音
                if suppression_factor < 0.5:
                    # 加入少量原始信号，保持语音自然度
                    output_samples = output_samples * 0.8 + input_samples * 0.2
            else:
                output_samples = input_samples
            
            # 转换回字节数据
            return (np.clip(output_samples * 32767, -32767, 32767)).astype(np.int16).tobytes()
            
        except Exception as e:
            # 如果处理失败，返回原始数据
            return input_audio

    def apply_spectral_subtraction(self, input_samples, ref_samples, base_factor):
        """谱减法增强回声消除"""
        try:
            # 简化的谱减法
            # 在频域中进行更精细的回声消除
            input_fft = np.fft.rfft(input_samples)
            ref_fft = np.fft.rfft(ref_samples)
            
            # 计算频域相关性
            magnitude_ratio = np.abs(input_fft) / (np.abs(ref_fft) + 1e-10)
            
            # 只在相似频率成分上进行抑制
            suppression_mask = np.where(magnitude_ratio > 0.5, base_factor, 1.0)
            
            return np.mean(suppression_mask)
            
        except Exception:
            return base_factor

    def apply_auto_gain_control(self, audio_data):
        """自动增益控制，保持音量稳定"""
        if not hasattr(self, 'numpy_available'):
            self.numpy_available = self.audio_processing_init()
        
        if not self.numpy_available:
            return audio_data
        
        try:
            samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
            
            # 计算当前RMS
            current_rms = np.sqrt(np.mean(samples**2))
            target_rms = 3000.0  # 目标RMS值
            
            if current_rms > 0:
                # 计算增益
                gain = min(target_rms / current_rms, 2.0)  # 限制最大增益为2倍
                gain = max(gain, 0.5)  # 限制最小增益为0.5倍
                
                # 应用增益
                samples = samples * gain
                
                # 硬限制，防止溢出
                samples = np.clip(samples, -32767, 32767)
            
            return samples.astype(np.int16).tobytes()
            
        except Exception as e:
            return audio_data

    def detect_voice_activity(self, audio_data):
        """改进的语音活动检测"""
        if not hasattr(self, 'numpy_available'):
            self.numpy_available = self.audio_processing_init()
        
        if not self.numpy_available:
            return True  # 如果无法检测，假设有语音活动
        
        try:
            samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # 1. 能量检测
            energy = np.sum(samples**2) / len(samples)
            
            # 2. 过零率检测
            zero_crossings = np.sum(np.diff(np.sign(samples)) != 0)
            zero_crossing_rate = zero_crossings / len(samples)
            
            # 3. 频谱质心（语音的频谱特征）
            try:
                fft = np.fft.rfft(samples)
                magnitude = np.abs(fft)
                freqs = np.fft.rfftfreq(len(samples), 1.0 / 16000)
                
                if np.sum(magnitude) > 0:
                    spectral_centroid = np.sum(freqs * magnitude) / np.sum(magnitude)
                else:
                    spectral_centroid = 0
            except:
                spectral_centroid = 0
            
            # 4. 短时能量变化率
            if hasattr(self, 'prev_energy'):
                energy_delta = abs(energy - self.prev_energy)
            else:
                energy_delta = 0
            self.prev_energy = energy
            
            # 自适应阈值
            if self.adaptive_threshold:
                # 动态调整阈值
                if hasattr(self, 'avg_noise_energy'):
                    self.avg_noise_energy = 0.95 * self.avg_noise_energy + 0.05 * energy
                    energy_threshold = max(self.avg_noise_energy * 3, 0.001)
                else:
                    self.avg_noise_energy = energy
                    energy_threshold = 0.001
            else:
                energy_threshold = 0.001
            
            # 综合判断
            conditions = [
                energy > energy_threshold,                    # 能量足够
                zero_crossing_rate > 0.02,                   # 过零率适中（不是纯噪声）
                zero_crossing_rate < 0.8,                    # 过零率不过高（不是高频噪声）
                spectral_centroid > 100,                     # 频谱质心在语音范围
                spectral_centroid < 4000                     # 频谱质心不过高
            ]
            
            # 至少满足3个条件才认为有语音
            voice_score = sum(conditions)
            has_voice = voice_score >= 3
            
            # 避免频繁切换
            if hasattr(self, 'voice_history'):
                self.voice_history.append(has_voice)
                if len(self.voice_history) > 5:
                    self.voice_history.pop(0)
                
                # 使用滑动窗口平滑决策
                recent_voice_count = sum(self.voice_history)
                has_voice = recent_voice_count >= 3  # 5帧中至少3帧有语音
            else:
                self.voice_history = [has_voice]
            
            return has_voice
            
        except Exception as e:
            return True

    def process_input_audio(self, audio_data):
        """处理输入音频数据 - 改进版本"""
        if not self.echo_cancellation and not self.noise_suppression and not self.auto_gain_control:
            # 如果没有启用任何处理，只调整音量
            return self.adjust_volume(audio_data, self.input_volume)
        
        processed_data = audio_data
        processing_log = []
        
        # 检测输入信号特征
        if hasattr(self, 'numpy_available') and self.numpy_available:
            try:
                samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                input_energy = np.sum(samples**2) / len(samples)
                input_rms = np.sqrt(input_energy)
                processing_log.append(f"输入RMS: {input_rms:.4f}")
            except:
                input_energy = 0
                input_rms = 0
        
        # 1. 噪声门 - 但要更宽松
        if self.noise_suppression:
            processed_data = self.apply_noise_gate(processed_data)
            processing_log.append("应用噪声门")
        
        # 2. 回声消除 - 仅在有足够历史数据时应用
        if self.echo_cancellation and len(self.audio_history) >= 2:
            # 使用最近的输出音频作为参考，但要检查能量
            reference = self.audio_history[-1] if self.audio_history else None
            if reference:
                # 检查参考信号强度，避免在无输出时进行回声消除
                try:
                    ref_samples = np.frombuffer(reference, dtype=np.int16).astype(np.float32) / 32768.0
                    ref_energy = np.sum(ref_samples**2) / len(ref_samples)
                    
                    # 只有在参考信号有足够能量时才进行回声消除
                    if ref_energy > 0.0001:
                        old_data = processed_data
                        processed_data = self.apply_echo_cancellation(processed_data, reference)
                        
                        # 检查是否过度抑制
                        if hasattr(self, 'numpy_available') and self.numpy_available:
                            try:
                                old_samples = np.frombuffer(old_data, dtype=np.int16).astype(np.float32) / 32768.0
                                new_samples = np.frombuffer(processed_data, dtype=np.int16).astype(np.float32) / 32768.0
                                
                                old_rms = np.sqrt(np.sum(old_samples**2) / len(old_samples))
                                new_rms = np.sqrt(np.sum(new_samples**2) / len(new_samples))
                                
                                # 如果抑制过度（超过90%），恢复部分原始信号
                                if old_rms > 0 and (new_rms / old_rms) < 0.1:
                                    recovery_factor = 0.3
                                    recovered_samples = new_samples * (1 - recovery_factor) + old_samples * recovery_factor
                                    processed_data = (np.clip(recovered_samples * 32767, -32767, 32767)).astype(np.int16).tobytes()
                                    processing_log.append(f"回声消除+恢复 (因子: {recovery_factor})")
                                else:
                                    processing_log.append(f"回声消除 (抑制率: {1-(new_rms/old_rms if old_rms > 0 else 0):.2f})")
                            except:
                                processing_log.append("回声消除")
                    else:
                        processing_log.append("跳过回声消除 (参考信号弱)")
                except:
                    pass
        elif self.echo_cancellation:
            processing_log.append("等待回声消除历史数据")
        
        # 3. 自动增益控制 - 最后应用
        if self.auto_gain_control:
            processed_data = self.apply_auto_gain_control(processed_data)
            processing_log.append("自动增益控制")
        
        # 4. 音量调整
        processed_data = self.adjust_volume(processed_data, self.input_volume)
        processing_log.append(f"音量调整 ({self.input_volume})")
        
        # 调试信息（可选）
        if hasattr(self, 'debug_audio_processing') and self.debug_audio_processing:
            if processing_log:
                print(f"[音频处理] {' -> '.join(processing_log)}")
        
        return processed_data

    def process_output_audio(self, audio_data):
        """处理输出音频数据"""
        # 调整输出音量
        processed_data = self.adjust_volume(audio_data, self.output_volume)
        
        # 保存到历史记录用于回声消除
        if self.echo_cancellation:
            self.audio_history.append(processed_data)
            if len(self.audio_history) > self.history_size:
                self.audio_history.pop(0)
        
        return processed_data

    def adjust_volume(self, audio_data, volume):
        """调整音频音量"""
        if volume == 1.0:
            return audio_data
        
        if not hasattr(self, 'numpy_available'):
            self.numpy_available = self.audio_processing_init()
        
        if not self.numpy_available:
            return audio_data
        
        try:
            samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
            samples = samples * volume
            samples = np.clip(samples, -32767, 32767)
            return samples.astype(np.int16).tobytes()
        except Exception as e:
            return audio_data

    def audio_send_loop(self):
        """音频发送循环 - 改进版本"""
        consecutive_silence = 0
        frames_processed = 0
        
        while self.current_call and self.audio_input:
            try:
                # 读取音频数据
                data = self.audio_input.read(self.chunk, exception_on_overflow=False)
                frames_processed += 1
                
                # 语音活动检测
                has_voice = True
                if self.voice_activity_detection:
                    has_voice = self.detect_voice_activity(data)
                    
                    if not has_voice:
                        consecutive_silence += 1
                        # 允许短暂的静音期，避免切断正常语音间隙
                        if consecutive_silence < 3:  # 允许3帧的静音
                            has_voice = True
                    else:
                        consecutive_silence = 0
                
                # 如果检测到语音活动或关闭了VAD，进行处理
                if has_voice or not self.voice_activity_detection:
                    # 音频处理
                    processed_data = self.process_input_audio(data)
                    
                    # 检查处理后是否还有信号
                    if hasattr(self, 'numpy_available') and self.numpy_available:
                        try:
                            processed_samples = np.frombuffer(processed_data, dtype=np.int16).astype(np.float32)
                            processed_energy = np.sum(processed_samples**2) / len(processed_samples)
                            
                            # 如果处理后能量过低，使用原始数据的一定比例
                            if processed_energy < 10:  # 很低的阈值
                                original_samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                                original_energy = np.sum(original_samples**2) / len(original_samples)
                                
                                if original_energy > 1000:  # 原始信号有足够能量
                                    # 混合原始信号和处理后信号
                                    mixed_samples = processed_samples * 0.7 + original_samples * 0.3
                                    processed_data = mixed_samples.astype(np.int16).tobytes()
                                    
                                    if frames_processed % 100 == 0:  # 每100帧打印一次
                                        print(f"[音频恢复] 混合原始信号以保持音质")
                        except:
                            pass
                    
                    # 构造音频包并发送
                    if self.audio_socket and self.current_call:
                        target_id = self.current_call.get('peer', '')
                        if target_id:
                            # 构造包头：源客户端ID + 目标客户端ID
                            header = self.client_id.encode('utf-8').ljust(16, b'\x00')
                            header += target_id.encode('utf-8').ljust(16, b'\x00')
                            packet = header + processed_data
                            
                            try:
                                self.audio_socket.sendto(packet, (self.server_ip, self.audio_port))
                            except Exception as send_e:
                                print(f"音频发送失败: {send_e}")
                    else:
                        time.sleep(0.01)
                else:
                    # 发送静音或跳过发送
                    time.sleep(0.01)
                    
                # 定期状态报告
                if frames_processed % 1000 == 0 and hasattr(self, 'debug_audio_processing') and self.debug_audio_processing:
                    print(f"[音频状态] 已处理 {frames_processed} 帧，连续静音 {consecutive_silence} 帧")
                    
            except Exception as e:
                if self.current_call:
                    print(f"音频发送错误: {e}")
                break

    def audio_receive_loop(self):
        """音频接收循环"""
        # 设置更长的超时，避免过度阻塞
        if self.audio_socket:
            self.audio_socket.settimeout(1.0)  # 增加到1秒
            
        while self.current_call and self.audio_output:
            try:
                # 从服务器接收音频数据
                if self.audio_socket:
                    try:
                        data, addr = self.audio_socket.recvfrom(4096)
                        
                        # 解析包头，提取音频数据
                        if len(data) > 32:  # 32字节包头（16字节源ID + 16字节目标ID）
                            audio_data = data[32:]
                            
                            # 处理接收到的音频数据
                            if len(audio_data) > 0:
                                processed_audio = self.process_output_audio(audio_data)
                                
                                # 播放音频数据
                                self.audio_output.write(processed_audio)
                    except socket.timeout:
                        # 正常超时，继续循环
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

    def show_clients(self):
        """显示在线客户端"""
        # 清除之前的事件状态
        self.client_list_event.clear()
        
        # 请求客户端列表
        self.request_client_list()
        
        # 等待服务器响应（最多等待3秒）
        if self.client_list_event.wait(timeout=3.0):
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
        print("🤖 提示: 已开启自动接听模式，来电将自动接受")
        print("=" * 60)
        
        while self.running and self.connected:
            try:
                self.show_main_menu()
                choice = input("请选择功能 (0-7): ").strip()

                if choice == '0':
                    print("正在退出...")
                    self.running = False
                    break
                elif choice == '1':
                    self.show_clients()
                elif choice == '2':
                    self.interactive_call()
                elif choice == '3':
                    self.interactive_hangup()
                elif choice == '4':
                    self.interactive_broadcast()
                elif choice == '5':
                    self.interactive_private_message()
                elif choice == '6':
                    self.show_status()
                elif choice == '7':
                    self.audio_settings_menu()
                else:
                    print("❌ 无效选择，请输入 0-7")
                    
            except KeyboardInterrupt:
                print("\n收到中断信号，正在退出...")
                self.running = False
                break
            except EOFError:
                break

    def show_main_menu(self):
        """显示主菜单。"""
        print("\n功能菜单:")
        print("  1. 查看在线客户端")
        print("  2. 发起通话")
        print("  3. 挂断通话")
        print("  4. 发送广播消息")
        print("  5. 发送私聊消息")
        print("  6. 查看当前状态")
        print("  7. 音频设置")
        print("  0. 退出客户端")

    def show_status(self):
        """显示客户端状态。"""
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

    def interactive_hangup(self):
        """交互式挂断通话"""
        with self.call_lock:
            if not self.current_call:
                print("❌ 当前没有进行中的通话")
                return
        
        print(f"\n{'='*50}")
        print(f"📞 正在与 {self.current_call['peer']} 通话中")
        print(f"通话ID: {self.current_call['id']}")
        print(f"{'='*50}")
        print("确认要挂断通话吗？")
        print("  1. 挂断通话")
        print("  2. 继续通话")
        print(f"{'='*50}")
        
        while True:
            try:
                choice = input("请输入选项 (1/2): ").strip()
                
                if choice == '1':
                    self.hangup_call()
                    print("📞 通话已结束")
                    break
                elif choice == '2':
                    print("继续通话中...")
                    break
                else:
                    print("❌ 无效选项，请输入 1 或 2")
            except (EOFError, KeyboardInterrupt):
                print("\n继续通话中...")
                break

    def interactive_private_message(self):
        """交互式发送私聊消息"""
        print("\n💬 发送私聊消息")
        print("-" * 40)

        while True:
            # 获取最新的客户端列表
            self.request_client_list()
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
                print("  0. 返回主菜单")

            try:
                choice = input("\n请选择 (0-{}): ".format(len(clients_list))).strip()
                if not choice or choice == '0':
                    print("已退出私聊")
                    return

                choice_num = int(choice)
                if not 1 <= choice_num <= len(clients_list):
                    print("❌ 无效选择")
                    continue

                target_id = clients_list[choice_num - 1][0]
                target_name = clients_list[choice_num - 1][1].get('name', target_id)

                print(f"\n已进入与 {target_name} 的私聊。")

                while True:
                    print(f"\n私聊对象: {target_name}")
                    print("  1. 发送消息")
                    print("  2. 更换私聊对象")
                    print("  0. 退出私聊")
                    action = input("请选择操作 (0-2): ").strip()

                    if action == '0':
                        print("已退出私聊")
                        return
                    if action == '2':
                        break
                    if action != '1':
                        print("❌ 无效选择")
                        continue

                    message = input(f"请输入要发送给 {target_name} 的消息: ").strip()
                    if not message:
                        print("❌ 消息不能为空")
                        continue

                    if self.send_private_message(target_id, message):
                        print(f"✅ 消息已发送给 {target_name}")
                    else:
                        print("❌ 消息发送失败")

            except (ValueError, IndexError):
                print("❌ 请输入有效数字")
            except KeyboardInterrupt:
                print("\n已退出私聊")
                return

    def audio_settings_menu(self):
        """音频设置菜单"""
        while True:
            print(f"\n{'='*60}")
            print("🔊 音频设置")
            print(f"{'='*60}")
            
            # 显示当前设置
            print("当前设置:")
            print(f"  1. 回声消除:     {'✅ 启用' if self.echo_cancellation else '❌ 禁用'}")
            print(f"  2. 噪声抑制:     {'✅ 启用' if self.noise_suppression else '❌ 禁用'}")
            print(f"  3. 自动增益控制: {'✅ 启用' if self.auto_gain_control else '❌ 禁用'}")
            print(f"  4. 语音活动检测: {'✅ 启用' if self.voice_activity_detection else '❌ 禁用'}")
            print(f"  5. 输入音量:     {self.input_volume:.1f}")
            print(f"  6. 输出音量:     {self.output_volume:.1f}")
            print(f"  7. 噪声门阈值:   {self.noise_gate_threshold:.3f}")
            print(f"  8. 调试模式:     {'✅ 启用' if getattr(self, 'debug_audio_processing', False) else '❌ 禁用'}")
            print("  9. 重置为默认设置")
            print("  s. 保存当前设置")
            print("  0. 返回主菜单")
            print(f"{'='*60}")
            
            try:
                choice = input("请选择 (0-9/s): ").strip().lower()
                
                if choice == '0':
                    break
                elif choice == '1':
                    self.echo_cancellation = not self.echo_cancellation
                    print(f"回声消除已{'启用' if self.echo_cancellation else '禁用'}")
                elif choice == '2':
                    self.noise_suppression = not self.noise_suppression
                    print(f"噪声抑制已{'启用' if self.noise_suppression else '禁用'}")
                elif choice == '3':
                    self.auto_gain_control = not self.auto_gain_control
                    print(f"自动增益控制已{'启用' if self.auto_gain_control else '禁用'}")
                elif choice == '4':
                    self.voice_activity_detection = not self.voice_activity_detection
                    print(f"语音活动检测已{'启用' if self.voice_activity_detection else '禁用'}")
                elif choice == '5':
                    try:
                        new_volume = float(input(f"输入新的输入音量 (0.0-1.0, 当前: {self.input_volume}): "))
                        if 0.0 <= new_volume <= 1.0:
                            self.input_volume = new_volume
                            print(f"输入音量设置为: {new_volume}")
                        else:
                            print("❌ 音量值必须在0.0-1.0之间")
                    except ValueError:
                        print("❌ 请输入有效数字")
                elif choice == '6':
                    try:
                        new_volume = float(input(f"输入新的输出音量 (0.0-1.0, 当前: {self.output_volume}): "))
                        if 0.0 <= new_volume <= 1.0:
                            self.output_volume = new_volume
                            print(f"输出音量设置为: {new_volume}")
                        else:
                            print("❌ 音量值必须在0.0-1.0之间")
                    except ValueError:
                        print("❌ 请输入有效数字")
                elif choice == '7':
                    try:
                        new_threshold = float(input(f"输入新的噪声门阈值 (0.0-1.0, 当前: {self.noise_gate_threshold}): "))
                        if 0.0 <= new_threshold <= 1.0:
                            self.noise_gate_threshold = new_threshold
                            print(f"噪声门阈值设置为: {new_threshold}")
                        else:
                            print("❌ 阈值必须在0.0-1.0之间")
                    except ValueError:
                        print("❌ 请输入有效数字")
                elif choice == '8':
                    self.debug_audio_processing = not getattr(self, 'debug_audio_processing', False)
                    print(f"音频调试模式已{'启用' if self.debug_audio_processing else '禁用'}")
                    if self.debug_audio_processing:
                        print("💡 提示: 调试模式会显示音频处理详细信息")
                elif choice == '9':
                    self.reset_audio_defaults()
                    print("✅ 音频设置已重置为默认值")
                elif choice == 's':
                    self.save_audio_config()
                else:
                    print("❌ 无效选择")
                    
            except KeyboardInterrupt:
                print("\n返回主菜单")
                break

    def reset_audio_defaults(self):
        """重置音频设置为默认值"""
        self.echo_cancellation = True
        self.noise_suppression = True
        self.auto_gain_control = True
        self.voice_activity_detection = True
        self.input_volume = 0.7
        self.output_volume = 0.8
        self.noise_gate_threshold = 0.01

    def save_audio_config(self, config_file='audio_config.json'):
        """保存当前音频配置"""
        try:
            config = {
                "audio_settings": {
                    "echo_cancellation": self.echo_cancellation,
                    "noise_suppression": self.noise_suppression,
                    "auto_gain_control": self.auto_gain_control,
                    "voice_activity_detection": self.voice_activity_detection,
                    "input_volume": self.input_volume,
                    "output_volume": self.output_volume,
                    "noise_gate_threshold": self.noise_gate_threshold,
                    "echo_delay_samples": self.echo_delay_samples,
                    "history_size": self.history_size,
                    "silence_threshold": self.silence_threshold
                },
                "advanced_settings": {
                    "chunk_size": self.chunk,
                    "sample_rate": self.rate,
                    "channels": self.channels,
                    "format": "paInt16"
                }
            }
            
            config_path = get_config_path(config_file)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 音频配置已保存到: {config_file}")
            
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")

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

    def disconnect(self, user_initiated=False):
        """断开连接"""
        print("正在断开连接...")
        
        # 只有在用户主动断开时才设置running=False
        if user_initiated:
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
    parser.add_argument('--server', help='服务器IP地址；未提供时从 client_config.json 读取默认服务器')
    parser.add_argument('--name', help='客户端名称')
    parser.add_argument('--port', type=int, default=5060, help='服务器端口 (默认: 5060)')
    parser.add_argument('--auto-reconnect', action='store_true', help='自动重连模式')
    
    args = parser.parse_args()

    try:
        server_ip, port, client_name = resolve_server_args(args)
    except ValueError as error:
        parser.error(str(error))
    
    if args.auto_reconnect:
        # 自动重连模式
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                if retry_count > 0:
                    print(f"\n🔄 第 {retry_count + 1} 次连接尝试...")
                    time.sleep(2)
                
                client = CloudVoIPClient(
                    server_ip=server_ip,
                    client_name=client_name,
                    base_port=port
                )
                
                if client.connect():
                    print(f"✅ 连接成功 (第 {retry_count + 1} 次尝试)")
                    client.interactive_mode()
                else:
                    print(f"❌ 连接失败 (第 {retry_count + 1} 次尝试)")
                
                # 连接断开后检查是否用户主动退出
                user_quit = not client.running
                client.disconnect()
                retry_count += 1
                
                # 如果是正常退出(用户输入quit)，则不重连
                if user_quit:
                    print("🚪 用户主动退出，停止重连")
                    break
                    
            except KeyboardInterrupt:
                print(f"\n🛑 用户中断，停止重连")
                break
            except Exception as e:
                print(f"❌ 客户端异常: {e}")
                retry_count += 1
                
        print("📞 自动重连已结束")
    else:
        # 标准模式
        client = CloudVoIPClient(
            server_ip=server_ip,
            client_name=client_name,
            base_port=port
        )
        
        try:
            if client.connect():
                client.interactive_mode()
        except KeyboardInterrupt:
            print("\n收到中断信号")
        finally:
            client.disconnect(user_initiated=True)


if __name__ == "__main__":
    main()
