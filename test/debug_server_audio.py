#!/usr/bin/env python3
"""
服务器音频转发调试工具
用于调试服务器端的音频转发功能
"""

import socket
import time
import threading
import struct

def debug_server_audio_handling():
    """调试服务器音频处理"""
    print("开始服务器音频处理调试...")
    
    server_ip = "120.27.145.121"
    audio_port = 5061
    
    # 创建监听socket来模拟服务器接收
    debug_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    debug_socket.bind(('0.0.0.0', 0))
    debug_socket.settimeout(5.0)
    
    local_port = debug_socket.getsockname()[1]
    print(f"调试监听端口: {local_port}")
    
    # 创建发送socket
    send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # 构造测试音频包
    source_id = "debugclient"
    target_id = "debugclient"
    test_data = b"DEBUG_AUDIO_DATA_" + bytes([i % 256 for i in range(100)])
    
    header = source_id.encode('utf-8').ljust(16, b'\x00')
    header += target_id.encode('utf-8').ljust(16, b'\x00')
    packet = header + test_data
    
    print(f"构造的测试包:")
    print(f"  源ID: '{source_id}'")
    print(f"  目标ID: '{target_id}'")
    print(f"  包头: {header.hex()}")
    print(f"  数据长度: {len(test_data)}")
    print(f"  总包长度: {len(packet)}")
    
    try:
        print(f"发送测试包到服务器 {server_ip}:{audio_port}")
        send_socket.sendto(packet, (server_ip, audio_port))
        
        print("等待服务器响应...")
        try:
            response, addr = debug_socket.recvfrom(4096)
            print(f"收到响应: {len(response)} 字节 from {addr}")
            
            # 分析响应包
            if len(response) >= 32:
                recv_source = response[:16].rstrip(b'\x00').decode('utf-8')
                recv_target = response[16:32].rstrip(b'\x00').decode('utf-8')
                recv_data = response[32:]
                
                print(f"响应包分析:")
                print(f"  源ID: '{recv_source}'")
                print(f"  目标ID: '{recv_target}'")
                print(f"  数据长度: {len(recv_data)}")
                print(f"  数据匹配: {recv_data == test_data}")
            else:
                print(f"响应包太短: {len(response)} 字节")
                print(f"原始数据: {response.hex()}")
                
        except socket.timeout:
            print("⏰ 等待响应超时 - 服务器可能没有转发音频包")
            
    except Exception as e:
        print(f"发送失败: {e}")
    
    finally:
        send_socket.close()
        debug_socket.close()
    
    print("服务器音频处理调试完成\n")

def test_server_connectivity():
    """测试服务器连通性"""
    print("测试服务器连通性...")
    
    server_ip = "120.27.145.121"
    ports_to_test = [5060, 5061, 5062]
    
    for port in ports_to_test:
        try:
            if port == 5060:  # TCP端口
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3.0)
                result = sock.connect_ex((server_ip, port))
                if result == 0:
                    print(f"✅ TCP端口 {port} 可达")
                else:
                    print(f"❌ TCP端口 {port} 不可达")
                sock.close()
            else:  # UDP端口
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(2.0)
                test_data = b"UDP_TEST"
                try:
                    sock.sendto(test_data, (server_ip, port))
                    print(f"✅ UDP端口 {port} 数据发送成功")
                except Exception as e:
                    print(f"❌ UDP端口 {port} 发送失败: {e}")
                finally:
                    sock.close()
        except Exception as e:
            print(f"❌ 端口 {port} 测试异常: {e}")
    
    print("服务器连通性测试完成\n")

def analyze_audio_packet_format():
    """分析音频包格式"""
    print("分析音频包格式...")
    
    # 模拟客户端发送的包格式
    source_id = "client1"
    target_id = "client2"
    audio_data = bytes([0x80, 0x60] * 512)  # 模拟PCM音频数据
    
    # 按照代码中的格式构造包
    header = source_id.encode('utf-8').ljust(16, b'\x00')
    header += target_id.encode('utf-8').ljust(16, b'\x00')
    full_packet = header + audio_data
    
    print(f"音频包格式分析:")
    print(f"  源ID (0-15): '{source_id}' -> {header[:16].hex()}")
    print(f"  目标ID (16-31): '{target_id}' -> {header[16:32].hex()}")
    print(f"  音频数据 (32+): {len(audio_data)} 字节")
    print(f"  总包长度: {len(full_packet)} 字节")
    
    # 测试解析
    parsed_source = full_packet[:16].rstrip(b'\x00').decode('utf-8')
    parsed_target = full_packet[16:32].rstrip(b'\x00').decode('utf-8')
    parsed_audio = full_packet[32:]
    
    print(f"  解析结果:")
    print(f"    源ID: '{parsed_source}'")
    print(f"    目标ID: '{parsed_target}'")
    print(f"    音频长度: {len(parsed_audio)}")
    print(f"    解析正确: {parsed_source == source_id and parsed_target == target_id}")
    
    print("音频包格式分析完成\n")

if __name__ == "__main__":
    print("=== VoIP服务器音频调试工具 ===\n")
    
    print("1. 服务器连通性测试")
    test_server_connectivity()
    
    print("2. 音频包格式分析")
    analyze_audio_packet_format()
    
    print("3. 服务器音频处理调试")
    debug_server_audio_handling()
    
    print("=== 调试完成 ===")
