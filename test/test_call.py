#!/usr/bin/env python3
"""
VoIP通话测试脚本
用于自动化测试两个客户端之间的通话
"""

import time
import subprocess
import threading
import sys

def start_client(name, server_ip="120.27.145.121"):
    """启动一个客户端"""
    cmd = [
        "/home/ruio/sip_test/.venv/bin/python",
        "/home/ruio/sip_test/cloud_voip_client.py",
        "--server", server_ip,
        "--name", name
    ]
    
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    return process

def send_command(process, command):
    """向客户端发送命令"""
    try:
        process.stdin.write(command + "\n")
        process.stdin.flush()
    except Exception as e:
        print(f"发送命令失败: {e}")

if __name__ == "__main__":
    print("启动VoIP通话测试...")
    
    # 启动两个客户端
    client1 = start_client("TestClient1")
    time.sleep(2)
    client2 = start_client("TestClient2")
    time.sleep(3)
    
    # 让client1查看在线客户端
    print("\n=== Client1 查看在线客户端 ===")
    send_command(client1, "clients")
    time.sleep(2)
    
    # 让client2查看在线客户端
    print("\n=== Client2 查看在线客户端 ===")
    send_command(client2, "clients")
    time.sleep(2)
    
    print("\n测试完成。请手动测试通话功能。")
    print("提示：在一个客户端中输入 'call <client_id>' 发起通话")
    
    # 保持进程运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在关闭客户端...")
        client1.terminate()
        client2.terminate()
        sys.exit(0)
