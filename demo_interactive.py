#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VoIP客户端交互功能演示脚本

演示如何使用新的选择式界面功能:
- 选择式发起通话
- 选择式发送私聊消息  
- 选择式发送广播消息

使用方法:
1. 启动服务器
2. 启动多个客户端实例
3. 在客户端中使用以下命令:
   - call     (不带参数，进入选择模式)
   - private  (不带参数，进入选择模式)
   - broadcast(不带参数，进入选择模式)

作者: GitHub Copilot
日期: 2025年8月21日
"""

def print_demo_guide():
    """打印使用指南"""
    print("🎉 VoIP客户端交互功能使用指南")
    print("=" * 60)
    print()
    print("🔧 新功能概览:")
    print("  ✨ 选择式发起通话 - 直接输入 'call'")
    print("  ✨ 选择式私聊消息 - 直接输入 'private'") 
    print("  ✨ 选择式广播消息 - 直接输入 'broadcast'")
    print()
    print("📋 使用步骤:")
    print("  1. 启动云VoIP服务器")
    print("  2. 启动多个客户端实例 (建议2-3个)")
    print("  3. 在任一客户端控制台输入以下命令:")
    print()
    print("     🔹 发起通话:")
    print("        输入: call")
    print("        → 系统显示在线用户列表")
    print("        → 选择要通话的用户编号")
    print("        → 自动发起通话请求")
    print()
    print("     🔹 发送私聊:")
    print("        输入: private")
    print("        → 系统显示在线用户列表")
    print("        → 选择私聊对象编号")
    print("        → 输入消息内容")
    print("        → 自动发送私聊消息")
    print()
    print("     🔹 发送广播:")
    print("        输入: broadcast") 
    print("        → 直接输入广播内容")
    print("        → 自动发送给所有在线用户")
    print()
    print("💡 优势:")
    print("  ✅ 无需记忆用户ID")
    print("  ✅ 避免输入错误")
    print("  ✅ 操作更直观友好")
    print("  ✅ 支持原有命令格式 (向后兼容)")
    print()
    print("🎯 兼容性:")
    print("  📌 新格式: call, private, broadcast")
    print("  📌 旧格式: call <id>, private <id> <msg>, broadcast <msg>")
    print("  📌 两种格式可同时使用")
    print()
    print("🚀 开始体验:")
    print("  运行: python3 voip_client_launcher.py")
    print("  选择: 快速连接服务器")
    print("  然后在控制台尝试新功能！")
    print("=" * 60)

if __name__ == "__main__":
    print_demo_guide()
