#!/usr/bin/env python3
"""
服务器状态调试工具
检查服务器是否正确保存了客户端信息
"""

import socket
import json
import struct
import time

def query_server_state():
    """查询服务器状态"""
    print("查询服务器内部状态...")
    
    server_ip = "120.27.145.121"
    message_port = 5060
    
    try:
        # 连接到服务器
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server_ip, message_port))
        
        # 注册一个测试客户端
        register_msg = {
            'type': 'register',
            'client_id': 'debug_client',
            'client_name': 'Debug Client',
            'audio_port': 12345,
            'timestamp': time.time()
        }
        
        # 发送注册消息
        data = json.dumps(register_msg).encode('utf-8')
        length = struct.pack('I', len(data))
        sock.send(length + data)
        
        # 接收响应
        length_data = sock.recv(4)
        if length_data:
            msg_length = struct.unpack('I', length_data)[0]
            response_data = sock.recv(msg_length)
            response = json.loads(response_data.decode('utf-8'))
            print(f"注册响应: {response}")
            
            if response.get('status') == 'success':
                print("✅ 客户端注册成功")
                
                # 请求客户端列表来验证服务器状态
                list_msg = {
                    'type': 'get_clients',
                    'timestamp': time.time()
                }
                
                data = json.dumps(list_msg).encode('utf-8')
                length = struct.pack('I', len(data))
                sock.send(length + data)
                
                # 接收客户端列表响应
                length_data = sock.recv(4)
                if length_data:
                    msg_length = struct.unpack('I', length_data)[0]
                    response_data = sock.recv(msg_length)
                    response = json.loads(response_data.decode('utf-8'))
                    print(f"客户端列表响应: {response}")
                    
                    clients = response.get('clients', [])
                    print(f"服务器上的客户端数量: {len(clients)}")
                    
                    for client in clients:
                        print(f"  客户端: {client}")
                        if client.get('id') == 'debug_client':
                            print("  ✅ 找到了我们注册的测试客户端")
                            if 'audio_port' in client:
                                print(f"  ✅ 音频端口已保存: {client['audio_port']}")
                            else:
                                print("  ❌ 音频端口信息丢失")
            else:
                print("❌ 客户端注册失败")
        
        sock.close()
        
    except Exception as e:
        print(f"查询服务器状态失败: {e}")

def test_audio_with_debug():
    """带调试信息的音频测试"""
    print("\n带调试的音频测试...")
    
    server_ip = "120.27.145.121"
    audio_port = 5061
    
    # 创建发送socket
    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # 创建接收socket
    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    recv_sock.bind(('0.0.0.0', 0))
    recv_sock.settimeout(5.0)
    
    recv_port = recv_sock.getsockname()[1]
    print(f"接收端口: {recv_port}")
    
    # 构造音频包
    source_id = "debug_client"
    target_id = "debug_client"  # 发给自己测试
    test_audio = b"DEBUG_AUDIO_" + bytes(range(100))
    
    header = source_id.encode('utf-8').ljust(16, b'\x00')
    header += target_id.encode('utf-8').ljust(16, b'\x00')
    packet = header + test_audio
    
    print(f"发送音频包到服务器: {len(packet)} 字节")
    print(f"  源ID: '{source_id}'")
    print(f"  目标ID: '{target_id}'")
    print(f"  音频数据: {len(test_audio)} 字节")
    
    try:
        # 发送音频包
        send_sock.sendto(packet, (server_ip, audio_port))
        print("音频包已发送")
        
        # 尝试接收
        try:
            response, addr = recv_sock.recvfrom(4096)
            print(f"收到音频响应: {len(response)} 字节 from {addr}")
            
            if len(response) > 32:
                recv_audio = response[32:]
                if recv_audio == test_audio:
                    print("✅ 音频数据匹配")
                else:
                    print("❌ 音频数据不匹配")
            
        except socket.timeout:
            print("⏰ 音频接收超时")
    
    except Exception as e:
        print(f"音频测试失败: {e}")
    
    finally:
        send_sock.close()
        recv_sock.close()

if __name__ == "__main__":
    print("=== 服务器状态调试 ===\n")
    
    query_server_state()
    test_audio_with_debug()
    
    print("\n=== 调试完成 ===")
