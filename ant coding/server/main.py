#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器主程序 - 启动双域名邮箱服务器
"""

import os
import sys
import json
import time
import threading
import logging
from pathlib import Path

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from server.server_manager import ServerManager


class DualDomainServer:
    """双域名服务器管理器"""
    
    def __init__(self):
        self.servers = {}
        self.running = False
        self.logger = logging.getLogger("DualDomainServer")
        
        # 设置日志
        self._setup_logging()
        
    def _setup_logging(self):
        """设置日志"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'dual_server.log'),
                logging.StreamHandler()
            ]
        )
    
    def start_servers(self):
        """启动两个服务器"""
        self.logger.info("Starting dual domain mail servers...")
        
        # 创建数据目录
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        (data_dir / "domain1").mkdir(exist_ok=True)
        (data_dir / "domain2").mkdir(exist_ok=True)
        
        # 配置路径
        config_dir = Path("config")
        domain1_config = config_dir / "domain1_config.json"
        domain2_config = config_dir / "domain2_config.json"
        
        # 启动域名1服务器
        self.logger.info(f"Starting server for domain1.com on port 8080")
        server1 = ServerManager(str(domain1_config), "example1.com")
        
        server1_thread = threading.Thread(
            target=server1.start,
            daemon=True
        )
        server1_thread.start()
        
        self.servers["example1.com"] = {
            "manager": server1,
            "thread": server1_thread,
            "port": 8080
        }
        
        # 等待服务器1启动
        time.sleep(2)
        
        # 启动域名2服务器
        self.logger.info(f"Starting server for example2.com on port 8081")
        server2 = ServerManager(str(domain2_config), "example2.com")
        
        server2_thread = threading.Thread(
            target=server2.start,
            daemon=True
        )
        server2_thread.start()
        
        self.servers["example2.com"] = {
            "manager": server2,
            "thread": server2_thread,
            "port": 8081
        }
        
        self.running = True
        self.logger.info("Both servers started successfully")
        
        # 启动服务器间通信桥接
        self._start_inter_domain_bridge()
    
    def _start_inter_domain_bridge(self):
        """启动服务器间通信桥接"""
        self.logger.info("Starting inter-domain communication bridge...")
        
        # 这里可以实现服务器间的邮件转发逻辑
        # 为了简化，我们假设服务器可以通过网络直接通信
        
        # 记录桥接信息
        bridge_info = {
            "domain1": {
                "server": "example1.com",
                "port": 8080,
                "smtp_port": 2525,
                "admin_email": "admin@example1.com"
            },
            "domain2": {
                "server": "example2.com",
                "port": 8081,
                "smtp_port": 2526,
                "admin_email": "admin@example2.com"
            },
            "bridge_started": time.time(),
            "status": "active"
        }
        
        # 保存桥接配置
        bridge_file = Path("data/inter_domain_bridge.json")
        with open(bridge_file, 'w', encoding='utf-8') as f:
            json.dump(bridge_info, f, indent=2, ensure_ascii=False)
        
        self.logger.info("Inter-domain bridge started")
    
    def stop_servers(self):
        """停止所有服务器"""
        self.logger.info("Stopping all servers...")
        self.running = False
        
        for domain, server_info in self.servers.items():
            try:
                self.logger.info(f"Stopping server for {domain}")
                server_info["manager"].stop()
                
                # 等待线程结束
                if server_info["thread"].is_alive():
                    server_info["thread"].join(timeout=5)
                    
            except Exception as e:
                self.logger.error(f"Error stopping server {domain}: {e}")
        
        self.logger.info("All servers stopped")
    
    def check_server_status(self):
        """检查服务器状态"""
        status = {}
        
        for domain, server_info in self.servers.items():
            server_status = {
                "running": server_info["thread"].is_alive(),
                "port": server_info["port"],
                "active_sessions": len(server_info["manager"].active_sessions),
                "client_threads": len(server_info["manager"].client_threads)
            }
            status[domain] = server_status
        
        return status
    
    def run(self):
        """运行服务器"""
        try:
            self.start_servers()
            
            # 主循环
            while self.running:
                try:
                    # 每30秒检查一次状态
                    time.sleep(30)
                    
                    # 检查服务器状态
                    status = self.check_server_status()
                    self.logger.debug(f"Server status: {status}")
                    
                    # 如果有服务器宕机，尝试重启
                    for domain, server_status in status.items():
                        if not server_status["running"]:
                            self.logger.warning(f"Server {domain} is not running. Attempting to restart...")
                            # 这里可以添加重启逻辑
                            
                except KeyboardInterrupt:
                    self.logger.info("Received interrupt signal")
                    break
                except Exception as e:
                    self.logger.error(f"Error in main loop: {e}")
                    
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
        finally:
            self.stop_servers()


def start_servers_in_background():
    """在后台启动服务器（用于测试）"""
    server = DualDomainServer()
    
    # 启动服务器
    server_thread = threading.Thread(target=server.start_servers, daemon=True)
    server_thread.start()
    
    # 等待服务器启动
    time.sleep(3)
    
    # 检查状态
    status = server.check_server_status()
    print("\n" + "="*60)
    print("双域名邮箱服务器状态")
    print("="*60)
    
    for domain, server_status in status.items():
        print(f"域名: {domain}")
        print(f"  状态: {'运行中' if server_status['running'] else '已停止'}")
        print(f"  端口: {server_status['port']}")
        print(f"  活跃会话: {server_status['active_sessions']}")
        print(f"  客户端线程: {server_status['client_threads']}")
        print()
    
    return server


def main():
    """主函数"""
    print("="*60)
    print("智能安全邮箱系统 - 双域名服务器")
    print("="*60)
    print("启动两个隔离的邮件服务器:")
    print("  1. example1.com - 端口 8080")
    print("  2. example2.com - 端口 8081")
    print("="*60)
    
    server = DualDomainServer()
    
    try:
        # 启动服务器
        server.start_servers()
        
        print("\n服务器已启动!")
        print("按 Ctrl+C 停止服务器\n")
        
        # 显示状态
        while server.running:
            try:
                time.sleep(5)
                
                # 显示状态
                status = server.check_server_status()
                print("\nCurrent server status:")
                for domain, server_status in status.items():
                    status_text = "[+] Running" if server_status["running"] else "[-] Stopped"
                    print(f"  {domain}: {status_text}")
                
            except KeyboardInterrupt:
                break
                
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
    except Exception as e:
        print(f"错误: {e}")
    finally:
        server.stop_servers()
        print("服务器已停止")


if __name__ == "__main__":
    # 直接运行主函数
    main()