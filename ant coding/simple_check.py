#!/usr/bin/env python3
# 最简单的环境检查

import os
import sys

print("=" * 50)
print("智能安全邮箱系统 - 环境状态")
print("=" * 50)
print()

# 检查Python
print("Python检查:")
print(f"  版本: {sys.version.split()[0]}")
print(f"  路径: {sys.executable}")
print()

# 检查关键文件
print("项目文件检查:")
essential_files = [
    ("Dockerfile", "容器配置"),
    ("docker-compose.yml", "服务编排"),
    ("requirements.txt", "Python依赖"),
    ("server/main.py", "服务器代码"),
    ("client/main.py", "客户端代码"),
]

all_exist = True
for file, desc in essential_files:
    exists = os.path.exists(file)
    status = "✅ 存在" if exists else "❌ 缺失"
    print(f"  {file:30} {status:10} ({desc})")
    if not exists:
        all_exist = False

print()

# 建议
print("建议:")
if all_exist:
    print("✅ 项目文件完整！")
    print()
    print("启动选项:")
    print("  1. Docker启动: 运行 start_with_docker.bat")
    print("  2. Python启动: 运行 python start_servers.py")
    print("  3. 仅查看: 阅读 QUICK_START.md")
else:
    print("⚠️  项目文件不完整")
    print()
    print("解决方案:")
    print("  1. 确保项目文件夹完整")
    print("  2. 从源码重新下载")
    print("  3. 使用Docker方式（不依赖本地文件）")

print()
print("=" * 50)