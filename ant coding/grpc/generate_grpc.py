#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成gRPC Python代码
"""

import subprocess
import sys
from pathlib import Path

def generate_grpc_code():
    """生成gRPC Python代码"""
    proto_dir = Path(__file__).parent
    proto_file = proto_dir / "mail_service.proto"
    
    if not proto_file.exists():
        print(f"[-] 错误: 找不到协议文件 {proto_file}")
        return False
    
    print("[+] 正在生成gRPC Python代码...")
    print(f"[+] 协议文件: {proto_file}")
    print(f"[+] 输出目录: {proto_dir}")
    
    try:
        # 生成gRPC代码
        cmd = [
            sys.executable,
            "-m", "grpc_tools.protoc",
            f"--proto_path={proto_dir}",
            f"--python_out={proto_dir}",
            f"--grpc_python_out={proto_dir}",
            str(proto_file)
        ]
        
        print(f"[+] 执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("[+] gRPC代码生成成功!")
            print(f"[+] 生成的文件:")
            
            # 列出生成的文件
            generated_files = [
                proto_dir / "mail_service_pb2.py",
                proto_dir / "mail_service_pb2_grpc.py"
            ]
            
            for file in generated_files:
                if file.exists():
                    print(f"    [+] {file.name}")
                else:
                    print(f"    [-] 警告: {file.name} 未生成")
            
            return True
        else:
            print(f"[-] gRPC代码生成失败!")
            print(f"[-] 错误输出: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"[-] 生成gRPC代码时出错: {e}")
        return False

def create_init_file():
    """创建__init__.py文件"""
    grpc_dir = Path(__file__).parent
    init_file = grpc_dir / "__init__.py"
    
    if not init_file.exists():
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write('# gRPC模块\n')
        print(f"[+] 创建了 {init_file}")
    
    return True

def create_setup_file():
    """创建setup文件便于导入"""
    grpc_dir = Path(__file__).parent
    setup_file = grpc_dir / "setup_path.py"
    
    content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gRPC模块路径设置
"""

import sys
from pathlib import Path

# 添加grpc目录到Python路径
grpc_dir = Path(__file__).parent
sys.path.insert(0, str(grpc_dir))
'''
    
    with open(setup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[+] 创建了 {setup_file}")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("gRPC代码生成工具")
    print("=" * 60)
    
    # 检查是否安装了grpcio-tools
    try:
        import grpc_tools
        print("[+] 检测到grpcio-tools已安装")
    except ImportError:
        print("[-] 错误: 未安装grpcio-tools")
        print("[-] 请运行: pip install -r requirements_grpc.txt")
        sys.exit(1)
    
    # 生成gRPC代码
    if generate_grpc_code():
        print()
        create_init_file()
        create_setup_file()
        print()
        print("=" * 60)
        print("[!] 完成!")
        print("[!] 可以使用以下方式导入:")
        print("[!]     from grpc.mail_service_pb2 import *")
        print("[!]     from grpc.mail_service_pb2_grpc import *")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("[-] 生成失败,请检查错误信息")
        print("=" * 60)
        sys.exit(1)
