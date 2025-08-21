#!/usr/bin/env python3
"""
音频调试测试脚本
用于诊断VoIP系统中的音频问题
"""

import socket
import time
import struct
import threading

def test_audio_connection():
    """测试音频连接"""
    print("开始音频连接测试...")
    
    # 服务器信息
    server_ip = "120.27.145.121"
    audio_port = 5061
    
    try:
        # 创建UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', 0))  # 绑定到本地任意端口
        
        local_port = sock.getsockname()[1]
        print(f"本地音频端口: {local_port}")
        
        # 构造测试音频包
        source_id = "testclient1".encode('utf-8').ljust(16, b'\x00')
        target_id = "testclient2".encode('utf-8').ljust(16, b'\x00')
        audio_data = b'\x00' * 1024  # 1KB的静默音频数据
        
        packet = source_id + target_id + audio_data
        
        # 发送测试包
        print(f"发送测试音频包到 {server_ip}:{audio_port}")
        sock.sendto(packet, (server_ip, audio_port))
        
        # 尝试接收响应
        sock.settimeout(5.0)
        try:
            data, addr = sock.recvfrom(4096)
            print(f"收到音频数据: {len(data)} 字节 from {addr}")
        except socket.timeout:
            print("没有收到音频数据响应（超时）")
        
        sock.close()
        print("音频连接测试完成")
        
    except Exception as e:
        print(f"音频连接测试失败: {e}")

def test_tcp_connection():
    """测试TCP连接"""
    print("开始TCP连接测试...")
    
    server_ip = "120.27.145.121"
    message_port = 5060
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10.0)
        
        print(f"连接到 {server_ip}:{message_port}")
        sock.connect((server_ip, message_port))
        
        # 发送注册消息
        register_msg = {
            'type': 'register',
            'client_id': 'test_client',
            'client_name': 'Test Client',
            'audio_port': 12345,
            'timestamp': time.time()
        }
        
        import json
        data = json.dumps(register_msg).encode('utf-8')
        length = struct.pack('I', len(data))
        sock.send(length + data)
        
        # 接收响应
        length_data = sock.recv(4)
        if length_data:
            msg_length = struct.unpack('I', length_data)[0]
            response_data = sock.recv(msg_length)
            response = json.loads(response_data.decode('utf-8'))
            print(f"服务器响应: {response}")
        
        sock.close()
        print("TCP连接测试完成")
        
    except Exception as e:
        print(f"TCP连接测试失败: {e}")

if __name__ == "__main__":
    print("=== VoIP连接诊断工具 ===")
    print("1. TCP连接测试")
    test_tcp_connection()
    
    print("\n2. 音频连接测试")
    test_audio_connection()
    
    print("\n=== 诊断完成 ===")
