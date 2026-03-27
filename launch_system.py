#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能安全邮箱系统 - 统一启动器
支持: Socket(原始), gRPC, QUIC
"""

import os
import sys
import subprocess
import time
from pathlib import Path

class SystemLauncher:
    """系统启动器"""
    
    def __init__(self):
        self.processes = []
        self.base_dir = Path(__file__).parent / "ant coding"
        self.base_dir = self.base_dir.resolve()
        
        if not self.base_dir.exists():
            print(f"[-] 错误: 找不到目录 {self.base_dir}")
            sys.exit(1)
        
        os.chdir(self.base_dir)
    
    def print_menu(self):
        """打印启动菜单"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=" * 70)
        print("智能安全邮箱系统 - 启动器".center(70))
        print("=" * 70)
        print()
        print("请选择启动协议:")
        print()
        print("  [1] Socket (原始协议) - 端口 8080/8081")
        print("  [2] gRPC              - 端口 50051/50052")
        print("  [3] QUIC              - 端口 8443/8444")
        print("  [4] 全部启动")
        print("  [0] 退出")
        print()
        print("=" * 70)
    
    def start_socket_servers(self):
        """启动Socket服务器"""
        print("\n[+] 启动Socket服务器...")
        
        try:
            # 启动服务器
            proc = subprocess.Popen(
                [sys.executable, "server/main.py"],
                cwd=self.base_dir,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            self.processes.append(proc)
            print(f"    [+] Socket服务器启动: PID {proc.pid}")
            print(f"    [+] Domain 1: 端口 8080 (example1.com)")
            print(f"    [+] Domain 2: 端口 8081 (example2.com)")
            
            return True
            
        except Exception as e:
            print(f"    [-] 启动失败: {e}")
            return False
    
    def start_grpc_servers(self):
        """启动gRPC服务器"""
        print("\n[+] 启动gRPC服务器...")
        
        try:
            # 检查gRPC代码是否生成
            grpc_pb2 = self.base_dir / "grpc/mail_service_pb2.py"
            if not grpc_pb2.exists():
                print("    [!] gRPC代码未生成，正在生成...")
                os.chdir(self.base_dir / "grpc")
                result = subprocess.run([sys.executable, "generate_grpc.py"], capture_output=True)
                os.chdir(self.base_dir)
                
                if result.returncode == 0:
                    print("    [+] gRPC代码生成完成")
                else:
                    print(f"    [-] gRPC代码生成失败: {result.stderr.decode()}")
                    return False
            
            # Domain 1
            proc1 = subprocess.Popen(
                [sys.executable, "grpc/grpc_server.py",
                 "config/domain1_config.json", "example1.com", "50051"],
                cwd=self.base_dir,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            self.processes.append(proc1)
            print(f"    [+] Domain 1 (example1.com): 端口 50051 - PID {proc1.pid}")
            
            time.sleep(1)
            
            # Domain 2
            proc2 = subprocess.Popen(
                [sys.executable, "grpc/grpc_server.py",
                 "config/domain2_config.json", "example2.com", "50052"],
                cwd=self.base_dir,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            self.processes.append(proc2)
            print(f"    [+] Domain 2 (example2.com): 端口 50052 - PID {proc2.pid}")
            
            return True
            
        except Exception as e:
            print(f"    [-] 启动失败: {e}")
            return False
    
    def start_quic_servers(self):
        """启动QUIC服务器"""
        print("\n[+] 启动QUIC服务器...")
        
        try:
            # Domain 1
            proc1 = subprocess.Popen(
                [sys.executable, "quic/quic_server.py",
                 "config/domain1_config.json", "example1.com", "8443"],
                cwd=self.base_dir,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            self.processes.append(proc1)
            print(f"    [+] Domain 1 (example1.com): 端口 8443 - PID {proc1.pid}")
            
            time.sleep(1)
            
            # Domain 2
            proc2 = subprocess.Popen(
                [sys.executable, "quic/quic_server.py",
                 "config/domain2_config.json", "example2.com", "8444"],
                cwd=self.base_dir,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            self.processes.append(proc2)
            print(f"    [+] Domain 2 (example2.com): 端口 8444 - PID {proc2.pid}")
            
            print("    [!] 注意: QUIC在Windows上可能需要额外配置")
            
            return True
            
        except Exception as e:
            print(f"    [-] 启动失败: {e}")
            return False
    
    def start_all(self):
        """启动所有服务器"""
        print("\n[+] 启动所有服务器...")
        
        results = []
        results.append(("Socket", self.start_socket_servers()))
        results.append(("gRPC", self.start_grpc_servers()))
        results.append(("QUIC", self.start_quic_servers()))
        
        print("\n[+] 启动结果:")
        for name, success in results:
            status = "[OK]" if success else "[FAIL]"
            print(f"    {status} {name}")
        
        return all(r[1] for r in results)
    
    def stop_all(self):
        """停止所有服务器"""
        if not self.processes:
            print("    [-] 没有运行的服务器")
            return
        
        print("\n[+] 停止所有服务器...")
        for proc in self.processes:
            try:
                proc.terminate()
                proc.wait(timeout=3)
                print(f"    [+] 进程 {proc.pid} 已停止")
            except:
                try:
                    proc.kill()
                    print(f"    [!] 进程 {proc.pid} 已强制停止")
                except:
                    print(f"    [-] 进程 {proc.pid} 停止失败")
        
        self.processes.clear()
    
    def show_status(self):
        """显示运行状态"""
        print("\n[+] 当前运行的服务器:")
        
        if not self.processes:
            print("    [-] 无服务器运行")
        else:
            for i, proc in enumerate(self.processes, 1):
                status = "运行中" if proc.poll() is None else "已停止"
                print(f"    [{i}] PID: {proc.pid} - {status}")
    
    def run(self):
        """运行启动器"""
        while True:
            self.print_menu()
            
            try:
                choice = input("\n请选择 (0-4): ").strip()
                
                if choice == "0":
                    print("\n[!] 退出程序")
                    self.stop_all()
                    break
                
                elif choice == "1":
                    self.start_socket_servers()
                    self.show_status()
                    self.wait_for_user()
                    self.stop_all()
                
                elif choice == "2":
                    self.start_grpc_servers()
                    self.show_status()
                    self.wait_for_user()
                    self.stop_all()
                
                elif choice == "3":
                    self.start_quic_servers()
                    self.show_status()
                    self.wait_for_user()
                    self.stop_all()
                
                elif choice == "4":
                    self.start_all()
                    self.show_status()
                    self.wait_for_user()
                    self.stop_all()
                
                else:
                    print("\n[-] 无效选择，请重新输入")
                    time.sleep(1)
                    continue
                
            except KeyboardInterrupt:
                print("\n\n[!] 用户中断")
                self.stop_all()
                break
            except Exception as e:
                print(f"\n[-] 错误: {e}")
                self.stop_all()
                time.sleep(2)
    
    def wait_for_user(self):
        """等待用户输入"""
        print("\n" + "=" * 70)
        print("服务器运行中... 按回车键停止服务器")
        print("=" * 70)
        input()


def main():
    """主函数"""
    print("\n[+] 智能安全邮箱系统启动器")
    print("[+] 支持: Socket(原始), gRPC, QUIC")
    print()
    
    launcher = SystemLauncher()
    
    try:
        launcher.run()
    except KeyboardInterrupt:
        print("\n[!] 程序已退出")
    finally:
        launcher.stop_all()
        print("\n[+] 所有服务器已停止")
        print("[+] 再见!")


if __name__ == "__main__":
    main()
