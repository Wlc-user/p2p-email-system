#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查运行环境
"""

import sys
import os
import subprocess
import platform

def check_python():
    """检查Python环境"""
    print("🔍 检查Python环境...")
    
    try:
        python_version = platform.python_version()
        python_executable = sys.executable
        python_path = sys.path
        
        print(f"✅ Python版本: {python_version}")
        print(f"✅ Python路径: {python_executable}")
        
        # 检查关键模块
        required_modules = ['flask', 'cryptography', 'numpy', 'pandas']
        missing_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
                print(f"✅ 模块 {module} 已安装")
            except ImportError:
                missing_modules.append(module)
                print(f"❌ 模块 {module} 未安装")
        
        if missing_modules:
            print(f"\n⚠️  缺少模块: {', '.join(missing_modules)}")
            print("请运行: pip install -r requirements.txt")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Python环境检查失败: {e}")
        return False

def check_docker():
    """检查Docker环境"""
    print("\n🔍 检查Docker环境...")
    
    try:
        # 检查Docker版本
        result = subprocess.run(
            ['docker', '--version'], 
            capture_output=True, 
            text=True, 
            shell=True
        )
        
        if result.returncode == 0:
            print(f"✅ Docker已安装: {result.stdout.strip()}")
            
            # 检查Docker Compose
            compose_result = subprocess.run(
                ['docker-compose', '--version'], 
                capture_output=True, 
                text=True, 
                shell=True
            )
            
            if compose_result.returncode == 0:
                print(f"✅ Docker Compose已安装: {compose_result.stdout.strip()}")
            else:
                print("⚠️  Docker Compose未安装")
                
            return True
        else:
            print("❌ Docker未安装或未启动")
            return False
            
    except FileNotFoundError:
        print("❌ Docker未安装")
        return False
    except Exception as e:
        print(f"❌ Docker检查失败: {e}")
        return False

def check_system():
    """检查系统环境"""
    print("\n🔍 检查系统环境...")
    
    system_info = {
        '系统': platform.system(),
        '版本': platform.version(),
        '架构': platform.architecture()[0],
        '处理器': platform.processor(),
        'Python构建': platform.python_build()
    }
    
    for key, value in system_info.items():
        print(f"✅ {key}: {value}")
    
    return True

def check_project_structure():
    """检查项目结构"""
    print("\n🔍 检查项目结构...")
    
    required_dirs = [
        'server',
        'client', 
        'config',
        'cost_optimizer',
        'logs',
        'data'
    ]
    
    required_files = [
        'requirements.txt',
        'Dockerfile',
        'docker-compose.yml',
        'server/main.py',
        'client/main.py'
    ]
    
    missing_dirs = []
    missing_files = []
    
    # 检查目录
    for dir_path in required_dirs:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            print(f"✅ 目录 {dir_path}/ 存在")
        else:
            missing_dirs.append(dir_path)
            print(f"❌ 目录 {dir_path}/ 不存在")
    
    # 检查文件
    for file_path in required_files:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            print(f"✅ 文件 {file_path} 存在")
        else:
            missing_files.append(file_path)
            print(f"❌ 文件 {file_path} 不存在")
    
    if missing_dirs or missing_files:
        print("\n⚠️  项目结构不完整")
        if missing_dirs:
            print(f"需要创建目录: {', '.join(missing_dirs)}")
        if missing_files:
            print(f"需要创建文件: {', '.join(missing_files)}")
        return False
    
    return True

def install_requirements():
    """安装依赖"""
    print("\n📦 安装Python依赖...")
    
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt 文件不存在")
        return False
    
    try:
        # 检查pip
        pip_check = subprocess.run(
            [sys.executable, '-m', 'pip', '--version'],
            capture_output=True,
            text=True,
            shell=True
        )
        
        if pip_check.returncode != 0:
            print("❌ pip未安装")
            return False
        
        print("✅ pip已安装")
        
        # 安装依赖
        print("正在安装依赖，这可能需要几分钟...")
        
        install_result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
            capture_output=True,
            text=True,
            shell=True
        )
        
        if install_result.returncode == 0:
            print("✅ 依赖安装成功")
            return True
        else:
            print(f"❌ 依赖安装失败: {install_result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 安装依赖时出错: {e}")
        return False

def create_minimal_demo():
    """创建最小化演示"""
    print("\n🎯 创建最小化演示...")
    
    demo_code = '''
import sys
print("=" * 50)
print("智能安全邮箱系统 - 最小化演示")
print("=" * 50)
print()
print("✅ Python环境正常")
print(f"版本: {sys.version}")
print()
print("🚀 项目组件:")
print("  • 双服务器邮箱系统")
print("  • 动态成本优化引擎")
print("  • 去中心化网络模拟")
print("  • 完整安全模块")
print()
print("📁 已创建的文件:")
print("  • Dockerfile - 容器化部署")
print("  • docker-compose.yml - 服务编排")
print("  • requirements.txt - Python依赖")
print()
print("🔧 下一步:")
print("  1. 运行: docker-compose up -d")
print("  2. 访问: http://localhost:8080")
print("  3. 运行: python cost_optimizer/demo_system.py")
print("=" * 50)
'''
    
    try:
        with open('minimal_demo.py', 'w', encoding='utf-8') as f:
            f.write(demo_code)
        
        print("✅ 最小化演示文件已创建: minimal_demo.py")
        
        # 运行演示
        print("\n🚀 运行最小化演示...")
        exec(demo_code)
        
        return True
        
    except Exception as e:
        print(f"❌ 创建演示失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("      智能安全邮箱系统 - 环境检查工具")
    print("=" * 60)
    print()
    
    checks_passed = 0
    total_checks = 5
    
    # 检查系统
    if check_system():
        checks_passed += 1
    
    # 检查Python
    python_ok = check_python()
    if python_ok:
        checks_passed += 1
    
    # 检查Docker
    docker_ok = check_docker()
    if docker_ok:
        checks_passed += 1
    
    # 检查项目结构
    structure_ok = check_project_structure()
    if structure_ok:
        checks_passed += 1
    
    # 如果Python正常但缺少依赖，尝试安装
    if python_ok and not structure_ok:
        install_success = install_requirements()
        if install_success:
            checks_passed += 1
    
    print(f"\n📊 检查结果: {checks_passed}/{total_checks} 项通过")
    
    if checks_passed == total_checks:
        print("🎉 所有检查通过！可以正常运行项目")
        
        # 创建最小化演示
        create_minimal_demo()
        
        print("\n🚀 启动建议:")
        print("  选项1: Docker启动 - docker-compose up -d")
        print("  选项2: Python启动 - python start_servers.py")
        print("  选项3: 演示模式 - python cost_optimizer/demo_system.py")
        
    elif docker_ok:
        print("\n✅ Docker环境正常，建议使用Docker启动:")
        print("  1. docker-compose build")
        print("  2. docker-compose up -d")
        print("  3. docker-compose logs -f")
        
    else:
        print("\n⚠️  环境不完整，建议:")
        
        if not python_ok:
            print("  1. 安装Python 3.8+")
            print("  2. 安装pip")
            print("  3. 运行: pip install -r requirements.txt")
        
        if not docker_ok:
            print("  1. 安装Docker Desktop")
            print("  2. 启动Docker服务")
            print("  3. 安装Docker Compose")
        
        print("\n💡 快速开始（无需Python/Docker）:")
        print("  查看文档: cat README.md")
        print("  查看架构: cat docs/architecture.md")
    
    print("\n" + "=" * 60)
    print("      环境检查完成")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 用户中断")
    except Exception as e:
        print(f"\n❌ 检查过程中出错: {e}")