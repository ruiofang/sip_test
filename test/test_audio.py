#!/usr/bin/env python3
"""
音频功能专项测试
专门测试音频发送和接收功能
"""

import socket
import time
import threading
import sys

def test_audio_echo():
    """测试音频回显功能"""
    print("开始音频回显测试...")
    
    server_ip = "120.27.145.121"
    audio_port = 5061
    
    # 创建客户端socket
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_sock.bind(('0.0.0.0', 0))
    
    local_port = client_sock.getsockname()[1]
    print(f"本地音频端口: {local_port}")
    
    # 设置超时
    client_sock.settimeout(2.0)
    
    # 构造测试音频包
    source_id = "testclient1"
    target_id = "testclient1"  # 发送给自己，测试回显
    
    # 创建音频数据（1024字节的测试数据）
    audio_data = bytes([i % 256 for i in range(1024)])
    
    # 构造完整包
    header = source_id.encode('utf-8').ljust(16, b'\x00')
    header += target_id.encode('utf-8').ljust(16, b'\x00')
    packet = header + audio_data
    
    print(f"发送音频包: {len(packet)} 字节")
    print(f"  包头长度: 32 字节")
    print(f"  音频数据: {len(audio_data)} 字节")
    
    # 发送数据包
    try:
        sent = client_sock.sendto(packet, (server_ip, audio_port))
        print(f"发送了 {sent} 字节到服务器")
        
        # 尝试接收响应
        try:
            response, addr = client_sock.recvfrom(4096)
            print(f"收到响应: {len(response)} 字节 from {addr}")
            
            if len(response) > 32:
                recv_audio = response[32:]
                print(f"收到音频数据: {len(recv_audio)} 字节")
                
                # 检查数据是否匹配
                if recv_audio == audio_data:
                    print("✅ 音频数据完全匹配!")
                else:
                    print("❌ 音频数据不匹配")
                    print(f"发送: {audio_data[:10]}...")
                    print(f"接收: {recv_audio[:10]}...")
            else:
                print("❌ 响应数据太短，没有音频内容")
                
        except socket.timeout:
            print("⏰ 等待响应超时")
            
    except Exception as e:
        print(f"❌ 发送失败: {e}")
    
    finally:
        client_sock.close()
    
    print("音频回显测试完成\n")

def test_two_client_audio():
    """测试两个客户端之间的音频传输"""
    print("开始双客户端音频测试...")
    
    server_ip = "120.27.145.121"
    audio_port = 5061
    
    # 客户端1
    client1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client1.bind(('0.0.0.0', 0))
    client1.settimeout(2.0)
    
    # 客户端2
    client2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client2.bind(('0.0.0.0', 0))
    client2.settimeout(2.0)
    
    port1 = client1.getsockname()[1]
    port2 = client2.getsockname()[1]
    
    print(f"客户端1端口: {port1}")
    print(f"客户端2端口: {port2}")
    
    # 测试数据
    test_message = b"Hello from client 1!"
    
    # 构造包：客户端1发送给客户端2
    header = b"client1".ljust(16, b'\x00')
    header += b"client2".ljust(16, b'\x00')
    packet1to2 = header + test_message
    
    try:
        # 客户端1发送数据
        print("客户端1发送数据给客户端2...")
        client1.sendto(packet1to2, (server_ip, audio_port))
        
        # 客户端2尝试接收
        print("客户端2等待接收数据...")
        try:
            data, addr = client2.recvfrom(4096)
            print(f"客户端2收到: {len(data)} 字节 from {addr}")
            
            if len(data) > 32:
                message = data[32:]
                print(f"收到消息: {message}")
                if message == test_message:
                    print("✅ 双客户端音频传输成功!")
                else:
                    print("❌ 数据不匹配")
            else:
                print("❌ 数据包太短")
                
        except socket.timeout:
            print("⏰ 客户端2接收超时")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    finally:
        client1.close()
        client2.close()
    
    print("双客户端音频测试完成\n")

if __name__ == "__main__":
    print("=== VoIP音频功能专项测试 ===\n")
    
    print("1. 音频回显测试")
    test_audio_echo()
    
    print("2. 双客户端音频传输测试")
    test_two_client_audio()
    
    print("=== 测试完成 ===")
