#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络模拟器 - 在单机上模拟多主机网络环境
即使Wi-Fi坏了也能测试分布式系统
"""

import socket
import threading
import time
import subprocess
import os
import sys
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from pathlib import Path

class NetworkSimulator:
    """网络模拟器，模拟两个隔离的邮箱服务器网络环境"""
    
    def __init__(self, config_file: str = "config/network_config.json"):
        """
        初始化网络模拟器
        
        Args:
            config_file: 配置文件路径
        """
        self.config = self._load_config(config_file)
        self.log_file = Path("logs/network_simulator.log")
        self.log_file.parent.mkdir(exist_ok=True)
        
        # 模拟的网络状态
        self.network_status = {
            "example1.com": {
                "host": "127.0.0.1",
                "port": 8080,
                "active": True,
                "latency_ms": 0,
                "packet_loss": 0.0,
                "blocked_destinations": [],
                "last_failure": None,
                "connections": []
            },
            "example2.com": {
                "host": "127.0.0.1",
                "port": 8081,
                "active": True,
                "latency_ms": 0,
                "packet_loss": 0.0,
                "blocked_destinations": [],
                "last_failure": None,
                "connections": []
            }
        }
        
        # 模拟的客户端连接
        self.client_connections = []
        
        # 线程安全锁
        self.lock = threading.Lock()
        
        self._log("Network simulator initialized")
    
    def _load_config(self, config_file: str) -> Dict:
        """加载配置文件"""
        default_config = {
            "simulation_mode": "advanced",
            "max_latency_ms": 1000,
            "max_packet_loss": 0.5,
            "test_scenarios": [
                "normal_operation",
                "network_partition",
                "high_latency",
                "packet_loss",
                "server_failure"
            ],
            "monitoring_interval": 5,  # 秒
            "log_level": "INFO"
        }
        
        config_path = Path(config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return {**default_config, **json.load(f)}
            except Exception as e:
                print(f"Warning: Could not load config: {e}. Using defaults.")
        
        return default_config
    
    def _log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
        
        if level in ["ERROR", "WARNING"] or self.config.get('log_level') == 'DEBUG':
            print(log_entry)
    
    # ========== 网络状态控制 ==========
    
    def simulate_network_partition(self, duration: int = 60):
        """
        模拟网络分区 - 两个服务器无法通信
        
        Args:
            duration: 分区持续时间（秒）
        """
        self._log(f"Simulating network partition for {duration} seconds")
        
        with self.lock:
            # 阻止两个域之间的通信
            self.network_status["example1.com"]["blocked_destinations"] = ["example2.com"]
            self.network_status["example2.com"]["blocked_destinations"] = ["example1.com"]
        
        # 启动恢复线程
        recovery_thread = threading.Thread(
            target=self._recover_network_partition,
            args=(duration,),
            daemon=True
        )
        recovery_thread.start()
        
        return True
    
    def _recover_network_partition(self, duration: int):
        """恢复网络分区"""
        time.sleep(duration)
        
        with self.lock:
            self.network_status["example1.com"]["blocked_destinations"] = []
            self.network_status["example2.com"]["blocked_destinations"] = []
        
        self._log("Network partition recovered")
    
    def simulate_server_failure(self, domain: str, duration: int = 30):
        """
        模拟服务器故障
        
        Args:
            domain: 故障的域名
            duration: 故障持续时间（秒）
        """
        self._log(f"Simulating server failure for {domain} for {duration} seconds")
        
        with self.lock:
            self.network_status[domain]["active"] = False
            self.network_status[domain]["last_failure"] = time.time()
        
        # 启动恢复线程
        recovery_thread = threading.Thread(
            target=self._recover_server_failure,
            args=(domain, duration),
            daemon=True
        )
        recovery_thread.start()
        
        return True
    
    def _recover_server_failure(self, domain: str, duration: int):
        """恢复服务器故障"""
        time.sleep(duration)
        
        with self.lock:
            self.network_status[domain]["active"] = True
        
        self._log(f"Server {domain} recovered from failure")
    
    def add_network_latency(self, domain: str, latency_ms: int, duration: int = 0):
        """
        添加网络延迟
        
        Args:
            domain: 目标域名
            latency_ms: 延迟毫秒数
            duration: 延迟持续时间（0表示永久）
        """
        self._log(f"Adding {latency_ms}ms latency to {domain}")
        
        with self.lock:
            self.network_status[domain]["latency_ms"] = latency_ms
        
        if duration > 0:
            # 启动恢复线程
            recovery_thread = threading.Thread(
                target=self._remove_latency,
                args=(domain, duration),
                daemon=True
            )
            recovery_thread.start()
    
    def _remove_latency(self, domain: str, duration: int):
        """移除延迟"""
        time.sleep(duration)
        
        with self.lock:
            self.network_status[domain]["latency_ms"] = 0
        
        self._log(f"Removed latency from {domain}")
    
    def simulate_packet_loss(self, domain: str, loss_rate: float, duration: int = 0):
        """
        模拟丢包
        
        Args:
            domain: 目标域名
            loss_rate: 丢包率 (0.0-1.0)
            duration: 丢包持续时间（0表示永久）
        """
        self._log(f"Simulating {loss_rate*100:.1f}% packet loss for {domain}")
        
        with self.lock:
            self.network_status[domain]["packet_loss"] = loss_rate
        
        if duration > 0:
            # 启动恢复线程
            recovery_thread = threading.Thread(
                target=self._remove_packet_loss,
                args=(domain, duration),
                daemon=True
            )
            recovery_thread.start()
    
    def _remove_packet_loss(self, domain: str, duration: int):
        """移除丢包"""
        time.sleep(duration)
        
        with self.lock:
            self.network_status[domain]["packet_loss"] = 0.0
        
        self._log(f"Removed packet loss from {domain}")
    
    # ========== 网络代理功能 ==========
    
    def create_network_proxy(self, listen_port: int, target_host: str, target_port: int):
        """
        创建网络代理，可以拦截和修改流量
        
        Args:
            listen_port: 监听端口
            target_host: 目标主机
            target_port: 目标端口
        """
        self._log(f"Creating network proxy: {listen_port} -> {target_host}:{target_port}")
        
        proxy_thread = threading.Thread(
            target=self._run_proxy,
            args=(listen_port, target_host, target_port),
            daemon=True
        )
        proxy_thread.start()
        
        return proxy_thread
    
    def _run_proxy(self, listen_port: int, target_host: str, target_port: int):
        """运行网络代理"""
        try:
            proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            proxy_socket.bind(('0.0.0.0', listen_port))
            proxy_socket.listen(5)
            
            self._log(f"Proxy listening on port {listen_port}")
            
            while True:
                client_socket, client_addr = proxy_socket.accept()
                
                # 为每个客户端连接创建处理线程
                client_thread = threading.Thread(
                    target=self._handle_proxy_connection,
                    args=(client_socket, client_addr, target_host, target_port),
                    daemon=True
                )
                client_thread.start()
                
        except Exception as e:
            self._log(f"Proxy error: {e}", "ERROR")
    
    def _handle_proxy_connection(self, client_socket, client_addr, target_host, target_port):
        """处理代理连接"""
        try:
            self._log(f"Proxy connection from {client_addr}")
            
            # 连接到目标服务器
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect((target_host, target_port))
            
            # 双向转发数据
            self._forward_data(client_socket, server_socket, f"Client→Server {client_addr}")
            self._forward_data(server_socket, client_socket, f"Server→Client {client_addr}")
            
        except Exception as e:
            self._log(f"Proxy connection error: {e}", "ERROR")
        finally:
            client_socket.close()
    
    def _forward_data(self, source_socket, dest_socket, label: str):
        """转发数据，应用网络模拟效果"""
        try:
            while True:
                data = source_socket.recv(4096)
                if not data:
                    break
                
                # 这里可以添加延迟、丢包等模拟效果
                modified_data = self._apply_network_effects(data, label)
                dest_socket.send(modified_data)
        except:
            pass
    
    def _apply_network_effects(self, data: bytes, label: str) -> bytes:
        """应用网络效果（延迟、丢包等）"""
        # 在实际应用中，这里会根据配置添加延迟或随机丢包
        return data
    
    # ========== 测试场景 ==========
    
    def run_test_scenario(self, scenario_name: str):
        """
        运行预定义的测试场景
        
        Args:
            scenario_name: 场景名称
        """
        scenarios = {
            "normal_operation": self._scenario_normal,
            "network_partition": self._scenario_partition,
            "high_latency": self._scenario_high_latency,
            "packet_loss": self._scenario_packet_loss,
            "server_failure": self._scenario_server_failure,
            "gradual_degradation": self._scenario_gradual_degradation,
            "rapid_recovery": self._scenario_rapid_recovery
        }
        
        if scenario_name not in scenarios:
            self._log(f"Unknown scenario: {scenario_name}", "ERROR")
            return False
        
        self._log(f"Running test scenario: {scenario_name}")
        return scenarios[scenario_name]()
    
    def _scenario_normal(self):
        """正常操作场景"""
        self._log("Scenario: Normal operation")
        return True
    
    def _scenario_partition(self):
        """网络分区场景"""
        self.simulate_network_partition(duration=120)
        return True
    
    def _scenario_high_latency(self):
        """高延迟场景"""
        self.add_network_latency("example1.com", 500, duration=180)
        self.add_network_latency("example2.com", 300, duration=180)
        return True
    
    def _scenario_packet_loss(self):
        """丢包场景"""
        self.simulate_packet_loss("example1.com", 0.2, duration=150)
        self.simulate_packet_loss("example2.com", 0.15, duration=150)
        return True
    
    def _scenario_server_failure(self):
        """服务器故障场景"""
        # 模拟服务器1故障30秒
        self.simulate_server_failure("example1.com", duration=30)
        
        # 30秒后模拟服务器2故障
        time.sleep(30)
        self.simulate_server_failure("example2.com", duration=30)
        
        return True
    
    def _scenario_gradual_degradation(self):
        """逐步降级场景"""
        self._log("Scenario: Gradual network degradation")
        
        # 逐步增加延迟
        for latency in [100, 300, 500, 800]:
            self.add_network_latency("example1.com", latency, duration=300)
            self.add_network_latency("example2.com", latency, duration=300)
            time.sleep(60)
        
        return True
    
    def _scenario_rapid_recovery(self):
        """快速恢复场景"""
        self._log("Scenario: Rapid recovery testing")
        
        # 快速切换故障状态
        for _ in range(5):
            self.simulate_server_failure("example1.com", duration=10)
            time.sleep(15)
            self.simulate_server_failure("example2.com", duration=10)
            time.sleep(15)
        
        return True
    
    # ========== 监控和报告 ==========
    
    def start_monitoring(self, interval: int = 5):
        """启动网络监控"""
        self._log(f"Starting network monitoring (interval: {interval}s)")
        
        monitor_thread = threading.Thread(
            target=self._monitor_network,
            args=(interval,),
            daemon=True
        )
        monitor_thread.start()
        
        return monitor_thread
    
    def _monitor_network(self, interval: int):
        """监控网络状态"""
        while True:
            try:
                status_report = self.get_network_status()
                
                # 检查服务器连通性
                for domain, info in status_report.items():
                    if info["active"]:
                        try:
                            sock = socket.socket()
                            sock.settimeout(2)
                            sock.connect((info["host"], info["port"]))
                            sock.close()
                            info["reachable"] = True
                        except:
                            info["reachable"] = False
                    else:
                        info["reachable"] = False
                
                # 保存监控快照
                self._save_monitor_snapshot(status_report)
                
                time.sleep(interval)
                
            except Exception as e:
                self._log(f"Monitoring error: {e}", "ERROR")
                time.sleep(interval)
    
    def _save_monitor_snapshot(self, status_report: Dict):
        """保存监控快照"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "status": status_report
        }
        
        monitor_dir = Path("logs/monitoring")
        monitor_dir.mkdir(exist_ok=True)
        
        snapshot_file = monitor_dir / f"snapshot_{int(time.time())}.json"
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
    
    def get_network_status(self) -> Dict:
        """获取当前网络状态"""
        with self.lock:
            return self.network_status.copy()
    
    def generate_test_report(self) -> Dict:
        """生成测试报告"""
        status = self.get_network_status()
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "test_duration": 0,
            "scenarios_run": [],
            "network_status": status,
            "summary": {
                "servers_active": sum(1 for s in status.values() if s["active"]),
                "total_latency_ms": sum(s["latency_ms"] for s in status.values()),
                "average_packet_loss": sum(s["packet_loss"] for s in status.values()) / len(status)
            },
            "recommendations": []
        }
        
        # 基于状态生成建议
        if status["example1.com"]["latency_ms"] > 500:
            report["recommendations"].append("High latency detected on example1.com - consider optimization")
        
        if status["example2.com"]["packet_loss"] > 0.1:
            report["recommendations"].append("High packet loss on example2.com - check network stability")
        
        return report
    
    # ========== Windows特定功能 ==========
    
    def setup_windows_networking(self):
        """
        设置Windows网络环境（即使Wi-Fi坏了也能工作）
        """
        self._log("Setting up Windows networking for testing")
        
        if sys.platform != "win32":
            self._log("This function is for Windows only", "WARNING")
            return
        
        try:
            # 创建虚拟网络适配器配置（示例）
            self._create_virtual_network_config()
            
            # 配置本地防火墙规则
            self._configure_firewall_rules()
            
            self._log("Windows networking setup completed")
            
        except Exception as e:
            self._log(f"Windows networking setup failed: {e}", "ERROR")
    
    def _create_virtual_network_config(self):
        """创建虚拟网络配置"""
        # 在实际应用中，这里会使用Windows API创建虚拟网络适配器
        # 目前仅作为示例
        pass
    
    def _configure_firewall_rules(self):
        """配置防火墙规则"""
        # 为测试端口创建防火墙规则
        ports = [8080, 8081, 9000, 9001]
        
        for port in ports:
            try:
                # 创建入站规则
                cmd = f'netsh advfirewall firewall add rule name="TestPort{port}" dir=in action=allow protocol=TCP localport={port}'
                subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                # 创建出站规则  
                cmd = f'netsh advfirewall firewall add rule name="TestPort{port}_out" dir=out action=allow protocol=TCP localport={port}'
                subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
            except Exception as e:
                self._log(f"Failed to create firewall rule for port {port}: {e}", "WARNING")


# ========== 主程序 ==========

def main():
    """主程序"""
    print("=" * 60)
    print("智能安全邮箱系统 - 网络模拟器")
    print("=" * 60)
    print()
    print("即使Wi-Fi坏了，也能在单机上测试分布式系统！")
    print()
    
    # 初始化网络模拟器
    simulator = NetworkSimulator()
    
    # 设置Windows网络环境
    if sys.platform == "win32":
        print("检测到Windows系统，正在设置网络环境...")
        simulator.setup_windows_networking()
    
    print("\n可用测试场景：")
    print("1. 正常操作 (normal_operation)")
    print("2. 网络分区 (network_partition)")
    print("3. 高延迟 (high_latency)")
    print("4. 丢包 (packet_loss)")
    print("5. 服务器故障 (server_failure)")
    print("6. 逐步降级 (gradual_degradation)")
    print("7. 快速恢复 (rapid_recovery)")
    print("8. 所有场景 (all)")
    print("9. 自定义场景 (custom)")
    print("0. 退出")
    
    while True:
        try:
            choice = input("\n请选择测试场景 (0-9): ").strip()
            
            if choice == "0":
                print("退出网络模拟器")
                break
            
            elif choice == "1":
                simulator.run_test_scenario("normal_operation")
                print("正常操作场景已启动")
                
            elif choice == "2":
                duration = int(input("分区持续时间（秒）: "))
                simulator.simulate_network_partition(duration)
                print(f"网络分区场景已启动，持续{duration}秒")
                
            elif choice == "3":
                latency = int(input("延迟毫秒数: "))
                duration = int(input("持续时间（秒，0表示永久）: "))
                domain = input("目标域名 (example1.com/example2.com/all): ")
                
                if domain == "all":
                    simulator.add_network_latency("example1.com", latency, duration)
                    simulator.add_network_latency("example2.com", latency, duration)
                else:
                    simulator.add_network_latency(domain, latency, duration)
                
                print(f"高延迟场景已启动")
                
            elif choice == "4":
                loss_rate = float(input("丢包率 (0.0-1.0): "))
                duration = int(input("持续时间（秒，0表示永久）: "))
                domain = input("目标域名 (example1.com/example2.com/all): ")
                
                if domain == "all":
                    simulator.simulate_packet_loss("example1.com", loss_rate, duration)
                    simulator.simulate_packet_loss("example2.com", loss_rate, duration)
                else:
                    simulator.simulate_packet_loss(domain, loss_rate, duration)
                
                print(f"丢包场景已启动")
                
            elif choice == "5":
                domain = input("故障域名 (example1.com/example2.com): ")
                duration = int(input("故障持续时间（秒）: "))
                simulator.simulate_server_failure(domain, duration)
                print(f"服务器故障场景已启动")
                
            elif choice == "6":
                simulator.run_test_scenario("gradual_degradation")
                print("逐步降级场景已启动")
                
            elif choice == "7":
                simulator.run_test_scenario("rapid_recovery")
                print("快速恢复场景已启动")
                
            elif choice == "8":
                print("运行所有测试场景...")
                scenarios = ["network_partition", "high_latency", "packet_loss", 
                           "server_failure", "gradual_degradation", "rapid_recovery"]
                for scenario in scenarios:
                    simulator.run_test_scenario(scenario)
                    time.sleep(10)
                print("所有场景已启动")
                
            elif choice == "9":
                print("自定义场景配置...")
                # 这里可以扩展自定义场景配置
                
            else:
                print("无效选择")
                
            # 显示当前状态
            status = simulator.get_network_status()
            print("\n当前网络状态:")
            for domain, info in status.items():
                status_str = "✅ 正常" if info["active"] else "❌ 故障"
                print(f"  {domain}: {status_str}, 延迟: {info['latency_ms']}ms, "
                      f"丢包: {info['packet_loss']*100:.1f}%")
            
        except KeyboardInterrupt:
            print("\n用户中断")
            break
        except Exception as e:
            print(f"错误: {e}")
    
    # 生成最终报告
    print("\n生成测试报告...")
    report = simulator.generate_test_report()
    
    report_file = Path("logs/test_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"测试报告已保存到: {report_file}")
    print("网络模拟器已完成")


if __name__ == "__main__":
    main()