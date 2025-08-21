#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VoIP系统演示脚本

演示局域网VoIP系统的基本功能

使用方法:
python demo_voip.py

作者: GitHub Copilot
日期: 2025年8月20日
"""

import time
import json
import socket
import threading


def demo_client(server_ip="192.168.100.15", client_name="Demo Client"):
    """演示客户端功能"""
    message_port = 5061
    
    print(f"🎯 演示客户端 [{client_name}] 连接到服务器 {server_ip}")
    
    # 测试文本消息
    try:
        print("📝 发送文本消息...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server_ip, message_port))
        
        message = f"Hello from {client_name}! Current time: {time.strftime('%H:%M:%S')}"
        sock.send(message.encode('utf-8'))
        
        response = sock.recv(1024).decode('utf-8')
        print(f"✅ 文本消息已发送，服务器响应: {response}")
        sock.close()
        
    except Exception as e:
        print(f"❌ 文本消息发送失败: {e}")
        return
    
    # 测试JSON消息
    try:
        print("📋 发送JSON消息...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server_ip, message_port))
        
        json_data = {
            "type": "demo",
            "client": client_name,
            "timestamp": time.time(),
            "message": "This is a demo JSON message",
            "data": {
                "version": "1.0",
                "features": ["text", "json", "audio"]
            }
        }
        
        json_str = json.dumps(json_data, ensure_ascii=False)
        sock.send(json_str.encode('utf-8'))
        
        response = sock.recv(1024).decode('utf-8')
        response_data = json.loads(response)
        print(f"✅ JSON消息已发送，服务器响应: {response_data}")
        sock.close()
        
    except Exception as e:
        print(f"❌ JSON消息发送失败: {e}")
        return
    
    # 测试通话请求
    try:
        print("📞 发送通话请求...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server_ip, message_port))
        
        call_request = {
            "type": "call_request",
            "caller": client_name,
            "target": "any_available_client",
            "timestamp": time.time()
        }
        
        json_str = json.dumps(call_request, ensure_ascii=False)
        sock.send(json_str.encode('utf-8'))
        
        response = sock.recv(1024).decode('utf-8')
        response_data = json.loads(response)
        print(f"✅ 通话请求已发送，服务器响应: {response_data}")
        sock.close()
        
    except Exception as e:
        print(f"❌ 通话请求发送失败: {e}")


def main():
    """主函数"""
    print("=" * 60)
    print("🎪 VoIP系统功能演示")
    print("=" * 60)
    print()
    
    server_ip = "192.168.100.15"  # 你可以修改为实际的服务器IP
    
    print(f"目标服务器: {server_ip}")
    print("确保服务器已启动: python lan_voip_server.py")
    print()
    
    # 运行演示
    try:
        demo_client(server_ip, "Demo Client A")
        print()
        print("-" * 40)
        print()
        
        # 稍等一下，再运行另一个客户端演示
        time.sleep(2)
        demo_client(server_ip, "Demo Client B")
        
    except KeyboardInterrupt:
        print("\n演示已被中断")
    
    print()
    print("=" * 60)
    print("🎉 演示完成！")
    print()
    print("下一步你可以：")
    print("1. 运行完整客户端：python lan_voip_client.py 192.168.100.15")
    print("2. 在多台电脑上运行客户端进行真实通话测试")
    print("3. 尝试语音通话功能（需要麦克风和扬声器）")
    print("=" * 60)


if __name__ == "__main__":
    main()
