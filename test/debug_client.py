#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import socket
import struct
import time
import argparse

def main():
    parser = argparse.ArgumentParser(description='Debug VoIP Client')
    parser.add_argument('--server', required=True, help='服务器IP地址')
    parser.add_argument('--port', type=int, default=5060, help='服务器端口')
    parser.add_argument('--name', default='debug_client', help='客户端名称')
    
    args = parser.parse_args()
    
    try:
        # 连接服务器
        print(f"连接到服务器 {args.server}:{args.port}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((args.server, args.port))
        
        # 注册客户端
        client_id = f"debug_{int(time.time())}"
        register_msg = {
            'type': 'register',
            'client_id': client_id,
            'client_name': args.name,
            'timestamp': time.time()
        }
        
        msg_data = json.dumps(register_msg).encode('utf-8')
        msg_length = len(msg_data)
        sock.sendall(struct.pack('I', msg_length) + msg_data)
        print(f"发送注册消息: {register_msg}")
        
        # 接收注册响应
        response_length = struct.unpack('I', sock.recv(4))[0]
        response_data = sock.recv(response_length)
        response = json.loads(response_data.decode('utf-8'))
        print(f"收到注册响应: {response}")
        
        # 请求客户端列表
        print("\n请求客户端列表...")
        get_clients_msg = {
            'type': 'get_clients',
            'timestamp': time.time()
        }
        
        msg_data = json.dumps(get_clients_msg).encode('utf-8')
        msg_length = len(msg_data)
        sock.sendall(struct.pack('I', msg_length) + msg_data)
        print(f"发送请求: {get_clients_msg}")
        
        # 接收客户端列表
        list_length = struct.unpack('I', sock.recv(4))[0]
        list_data = sock.recv(list_length)
        client_list = json.loads(list_data.decode('utf-8'))
        print(f"收到客户端列表: {client_list}")
        
        # 解析客户端列表
        if client_list.get('type') == 'client_list':
            clients = client_list.get('clients', [])
            if clients:
                print(f"\n在线客户端 ({len(clients)}):")
                for client in clients:
                    print(f"  - {client.get('name', 'unknown')} ({client.get('id', 'unknown')}) [{client.get('status', 'unknown')}]")
            else:
                print("没有其他在线客户端")
        else:
            print("收到的不是客户端列表消息")
            
        sock.close()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
