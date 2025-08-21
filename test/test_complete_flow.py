#!/usr/bin/env python3
"""
完整VoIP流程测试
模拟完整的客户端注册和音频通话流程
"""

import socket
import time
import json
import struct
import threading

class VoIPTestClient:
    def __init__(self, client_id, client_name, server_ip="120.27.145.121"):
        self.client_id = client_id
        self.client_name = client_name
        self.server_ip = server_ip
        self.message_port = 5060
        self.audio_port = 5061
        
        # 套接字
        self.message_socket = None
        self.audio_socket = None
        self.audio_listen_port = None
        
        # 状态
        self.registered = False
        self.in_call = False
        self.call_peer = None

    def connect_and_register(self):
        """连接并注册到服务器"""
        try:
            # 连接消息服务器
            self.message_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.message_socket.connect((self.server_ip, self.message_port))
            print(f"[{self.client_name}] 已连接到消息服务器")
            
            # 创建音频socket
            self.audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.audio_socket.bind(('0.0.0.0', 0))
            self.audio_listen_port = self.audio_socket.getsockname()[1]
            print(f"[{self.client_name}] 音频监听端口: {self.audio_listen_port}")
            
            # 发送注册消息
            register_msg = {
                'type': 'register',
                'client_id': self.client_id,
                'client_name': self.client_name,
                'audio_port': self.audio_listen_port,
                'timestamp': time.time()
            }
            
            self.send_message(register_msg)
            
            # 等待注册响应
            response = self.receive_message()
            if response and response.get('type') == 'register_response':
                if response.get('status') == 'success':
                    self.registered = True
                    print(f"[{self.client_name}] 注册成功")
                    return True
                else:
                    print(f"[{self.client_name}] 注册失败")
            
            return False
            
        except Exception as e:
            print(f"[{self.client_name}] 连接注册失败: {e}")
            return False

    def send_message(self, message):
        """发送消息"""
        try:
            data = json.dumps(message).encode('utf-8')
            length = struct.pack('I', len(data))
            self.message_socket.send(length + data)
            return True
        except Exception as e:
            print(f"[{self.client_name}] 发送消息失败: {e}")
            return False

    def receive_message(self, timeout=5.0):
        """接收消息"""
        try:
            self.message_socket.settimeout(timeout)
            
            # 接收长度
            length_data = self.message_socket.recv(4)
            if not length_data:
                return None
            
            msg_length = struct.unpack('I', length_data)[0]
            
            # 接收完整消息
            data = b''
            while len(data) < msg_length:
                chunk = self.message_socket.recv(min(msg_length - len(data), 4096))
                if not chunk:
                    break
                data += chunk
            
            if len(data) == msg_length:
                return json.loads(data.decode('utf-8'))
            
            return None
            
        except Exception as e:
            print(f"[{self.client_name}] 接收消息失败: {e}")
            return None

    def send_audio_data(self, target_client_id, audio_data):
        """发送音频数据"""
        try:
            # 构造音频包
            header = self.client_id.encode('utf-8').ljust(16, b'\x00')
            header += target_client_id.encode('utf-8').ljust(16, b'\x00')
            packet = header + audio_data
            
            # 发送到服务器音频端口
            self.audio_socket.sendto(packet, (self.server_ip, self.audio_port))
            print(f"[{self.client_name}] 发送音频数据: {len(audio_data)} 字节 -> {target_client_id}")
            return True
            
        except Exception as e:
            print(f"[{self.client_name}] 发送音频数据失败: {e}")
            return False

    def listen_for_audio(self, timeout=5.0):
        """监听音频数据"""
        try:
            self.audio_socket.settimeout(timeout)
            data, addr = self.audio_socket.recvfrom(4096)
            
            if len(data) > 32:
                source_id = data[:16].rstrip(b'\x00').decode('utf-8')
                target_id = data[16:32].rstrip(b'\x00').decode('utf-8')
                audio_data = data[32:]
                
                print(f"[{self.client_name}] 收到音频数据: {len(audio_data)} 字节 from {source_id}")
                return source_id, audio_data
            
            return None, None
            
        except socket.timeout:
            print(f"[{self.client_name}] 音频接收超时")
            return None, None
        except Exception as e:
            print(f"[{self.client_name}] 音频接收失败: {e}")
            return None, None

    def close(self):
        """关闭连接"""
        if self.message_socket:
            self.message_socket.close()
        if self.audio_socket:
            self.audio_socket.close()

def test_two_clients_audio():
    """测试两个客户端的音频通讯"""
    print("=== 开始两客户端音频测试 ===\n")
    
    # 创建两个测试客户端
    client1 = VoIPTestClient("testclient1", "TestClient1")
    client2 = VoIPTestClient("testclient2", "TestClient2")
    
    try:
        # 客户端1注册
        print("1. 客户端1注册...")
        if not client1.connect_and_register():
            print("客户端1注册失败")
            return
        
        time.sleep(1)
        
        # 客户端2注册
        print("\n2. 客户端2注册...")
        if not client2.connect_and_register():
            print("客户端2注册失败")
            return
        
        time.sleep(1)
        
        # 测试音频传输
        print("\n3. 测试音频传输...")
        test_audio_data = b"HELLO_AUDIO_TEST_" + bytes([i % 256 for i in range(100)])
        
        # 启动客户端2音频监听
        def client2_listen():
            source, data = client2.listen_for_audio(timeout=10.0)
            if data:
                print(f"客户端2收到音频: {len(data)} 字节 from {source}")
                if data == test_audio_data:
                    print("✅ 音频数据完全匹配!")
                else:
                    print("❌ 音频数据不匹配")
            else:
                print("客户端2没有收到音频数据")
        
        # 在线程中启动客户端2监听
        listen_thread = threading.Thread(target=client2_listen)
        listen_thread.start()
        
        time.sleep(0.5)
        
        # 客户端1发送音频给客户端2
        print("客户端1发送音频数据给客户端2...")
        if client1.send_audio_data("testclient2", test_audio_data):
            print("音频数据发送成功")
        else:
            print("音频数据发送失败")
        
        # 等待监听线程完成
        listen_thread.join()
        
    except Exception as e:
        print(f"测试异常: {e}")
    
    finally:
        print("\n4. 清理资源...")
        client1.close()
        client2.close()
    
    print("=== 两客户端音频测试完成 ===\n")

if __name__ == "__main__":
    test_two_clients_audio()
