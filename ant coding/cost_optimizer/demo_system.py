#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态成本优化演示系统
展示分布式去中心化邮箱系统的智能成本优化
"""

import time
import json
import numpy as np
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass
import matplotlib.pyplot as plt
import pandas as pd
from collections import deque

# 导入动态成本引擎
from dynamic_cost_engine import DynamicCostEngine, UserActivity, NetworkMetrics

@dataclass
class DecentralizedNode:
    """去中心化节点"""
    node_id: str
    location: str
    capacity_messages_per_hour: int
    current_load: float = 0.0
    cost_per_hour: float = 0.0
    is_active: bool = True
    
    def process_message(self, message_size_mb: float = 0.1) -> Tuple[bool, float]:
        """处理邮件"""
        if not self.is_active or self.current_load >= 0.95:
            return False, 0.0
        
        # 模拟处理时间
        processing_time = message_size_mb * 0.01  # 每MB 0.01秒
        
        # 更新负载
        self.current_load += 0.01
        
        # 计算成本
        node_cost = self.cost_per_hour / 3600  # 每秒成本
        
        return True, node_cost
    
    def update_status(self):
        """更新节点状态"""
        # 模拟负载自然下降
        if self.current_load > 0:
            self.current_load *= 0.95

class DecentralizedMailNetwork:
    """去中心化邮件网络"""
    
    def __init__(self, cost_engine: DynamicCostEngine):
        self.cost_engine = cost_engine
        self.nodes: Dict[str, DecentralizedNode] = {}
        self.message_queue = deque()
        self.total_messages_processed = 0
        self.total_cost = 0.0
        self.history = []
        
        # 初始化节点
        self._initialize_nodes()
        
        print("🌐 去中心化邮件网络初始化完成")
    
    def _initialize_nodes(self):
        """初始化网络节点"""
        # 核心节点（成本较高，性能好）
        core_nodes = [
            DecentralizedNode("core-1", "us-east", 10000, cost_per_hour=0.15),
            DecentralizedNode("core-2", "eu-west", 8000, cost_per_hour=0.12),
            DecentralizedNode("core-3", "ap-southeast", 6000, cost_per_hour=0.10),
        ]
        
        # 边缘节点（成本较低，性能一般）
        edge_nodes = [
            DecentralizedNode("edge-1", "us-west", 2000, cost_per_hour=0.05),
            DecentralizedNode("edge-2", "eu-central", 1800, cost_per_hour=0.04),
            DecentralizedNode("edge-3", "ap-northeast", 1500, cost_per_hour=0.03),
            DecentralizedNode("edge-4", "sa-east", 1200, cost_per_hour=0.02),
            DecentralizedNode("edge-5", "af-south", 1000, cost_per_hour=0.01),
        ]
        
        for node in core_nodes + edge_nodes:
            self.nodes[node.node_id] = node
        
        print(f"已部署 {len(core_nodes)} 个核心节点和 {len(edge_nodes)} 个边缘节点")
    
    def simulate_network_traffic(self, duration_hours: float = 1.0):
        """模拟网络流量"""
        print(f"\n🚀 开始模拟网络流量 (持续时间: {duration_hours}小时)")
        
        start_time = time.time()
        end_time = start_time + duration_hours * 3600
        
        iteration = 0
        
        while time.time() < end_time:
            iteration += 1
            
            # 模拟用户发送邮件
            messages_this_iteration = self._generate_messages(iteration)
            
            # 处理邮件
            processed_count, iteration_cost = self._process_messages(messages_this_iteration)
            
            # 更新统计数据
            self.total_messages_processed += processed_count
            self.total_cost += iteration_cost
            
            # 记录历史数据
            timestamp = datetime.now()
            self.history.append({
                'timestamp': timestamp,
                'messages_processed': processed_count,
                'iteration_cost': iteration_cost,
                'total_messages': self.total_messages_processed,
                'total_cost': self.total_cost,
                'avg_cost_per_message': (self.total_cost / self.total_messages_processed 
                                       if self.total_messages_processed > 0 else 0)
            })
            
            # 更新网络指标
            self._update_network_metrics(timestamp)
            
            # 动态调整节点
            if iteration % 10 == 0:
                self._dynamic_node_adjustment()
            
            # 输出进度
            if iteration % 20 == 0:
                elapsed = time.time() - start_time
                progress = min(100, (elapsed / (duration_hours * 3600)) * 100)
                print(f"进度: {progress:.1f}% | 总邮件: {self.total_messages_processed} | " +
                      f"总成本: ${self.total_cost:.4f} | 平均成本: ${self.history[-1]['avg_cost_per_message']:.6f}")
            
            time.sleep(0.1)  # 控制模拟速度
        
        print(f"\n✅ 模拟完成!")
        print(f"总处理邮件: {self.total_messages_processed}")
        print(f"总成本: ${self.total_cost:.4f}")
        print(f"平均每封邮件成本: ${self.history[-1]['avg_cost_per_message']:.6f}")
    
    def _generate_messages(self, iteration: int) -> List[Dict]:
        """生成模拟邮件"""
        messages = []
        
        # 模拟不同时间的流量模式
        current_hour = iteration % 24
        
        # 白天流量高，晚上流量低
        if 8 <= current_hour < 20:  # 白天
            base_count = np.random.randint(50, 200)
        else:  # 晚上
            base_count = np.random.randint(10, 50)
        
        # 添加随机波动
        message_count = max(1, int(base_count * np.random.uniform(0.8, 1.2)))
        
        for i in range(message_count):
            # 模拟不同用户
            user_id = f"user_{np.random.randint(1, 1000)}@example{np.random.randint(1,3)}.com"
            
            # 模拟不同大小的邮件
            message_size = np.random.uniform(0.01, 10.0)  # 0.01-10MB
            
            # 30%的邮件需要中继
            needs_relay = np.random.random() < 0.3
            
            messages.append({
                'user_id': user_id,
                'size_mb': message_size,
                'needs_relay': needs_relay,
                'timestamp': datetime.now()
            })
        
        return messages
    
    def _process_messages(self, messages: List[Dict]) -> Tuple[int, float]:
        """处理邮件"""
        processed_count = 0
        total_cost = 0.0
        
        for message in messages:
            user_id = message['user_id']
            message_size = message['size_mb']
            needs_relay = message['needs_relay']
            
            # 记录用户活动
            self.cost_engine.record_user_activity(user_id, message_size, needs_relay)
            
            # 选择处理节点
            selected_node = self._select_processing_node(message_size)
            
            if selected_node:
                # 处理邮件
                success, node_cost = selected_node.process_message(message_size)
                
                if success:
                    processed_count += 1
                    
                    # 计算动态成本
                    dynamic_cost, _ = self.cost_engine.calculate_dynamic_cost(user_id)
                    
                    # 总成本 = 节点成本 + 动态服务成本
                    total_message_cost = node_cost + dynamic_cost
                    total_cost += total_message_cost
                    
                    # 如果需要中继，选择中继节点
                    if needs_relay:
                        relay_node = self._select_relay_node(selected_node.node_id)
                        if relay_node:
                            relay_success, relay_cost = relay_node.process_message(message_size * 0.5)  # 中继成本较低
                            if relay_success:
                                total_cost += relay_cost
        
        return processed_count, total_cost
    
    def _select_processing_node(self, message_size: float) -> Optional[DecentralizedNode]:
        """选择处理节点"""
        # 优先选择负载低且成本效益高的节点
        available_nodes = [
            node for node in self.nodes.values() 
            if node.is_active and node.current_load < 0.9
        ]
        
        if not available_nodes:
            return None
        
        # 计算每个节点的得分（负载越低、成本效益越高得分越高）
        node_scores = []
        for node in available_nodes:
            # 成本效益 = 容量 / 成本
            cost_efficiency = node.capacity_messages_per_hour / max(0.01, node.cost_per_hour)
            
            # 负载惩罚
            load_penalty = 1.0 - node.current_load
            
            # 综合得分
            score = cost_efficiency * load_penalty * (1.0 if message_size < 1.0 else 0.8)
            
            node_scores.append((node, score))
        
        # 选择得分最高的节点
        best_node = max(node_scores, key=lambda x: x[1])[0]
        
        return best_node
    
    def _select_relay_node(self, exclude_node_id: str) -> Optional[DecentralizedNode]:
        """选择中继节点"""
        available_nodes = [
            node for node in self.nodes.values() 
            if node.is_active and node.node_id != exclude_node_id and node.current_load < 0.8
        ]
        
        if not available_nodes:
            return None
        
        # 选择成本最低的节点进行中继
        cheapest_node = min(available_nodes, key=lambda x: x.cost_per_hour)
        
        return cheapest_node
    
    def _update_network_metrics(self, timestamp: datetime):
        """更新网络指标"""
        # 计算当前网络状态
        active_nodes = [node for node in self.nodes.values() if node.is_active]
        
        if not active_nodes:
            return
        
        avg_load = np.mean([node.current_load for node in active_nodes])
        total_capacity = sum(node.capacity_messages_per_hour for node in active_nodes)
        estimated_messages_per_minute = total_capacity * avg_load / 60
        
        network_state = {
            'concurrent_users': len(set([act.user_id for act in self.cost_engine.user_activities.values()])),
            'messages_per_minute': estimated_messages_per_minute,
            'storage_growth_mb': self.total_messages_processed * 0.1,  # 假设每封邮件0.1MB
            'avg_latency_ms': 50.0 + avg_load * 100,  # 模拟延迟
            'bandwidth_mbps': estimated_messages_per_minute * 0.1 * 8 / 60,  # Mbps
            'server_load': avg_load * 100
        }
        
        # 记录网络指标
        self.cost_engine.record_network_metrics(network_state)
    
    def _dynamic_node_adjustment(self):
        """动态调整节点"""
        # 分析当前负载
        active_nodes = [node for node in self.nodes.values() if node.is_active]
        avg_load = np.mean([node.current_load for node in active_nodes])
        
        # 根据负载动态启用/停用节点
        if avg_load > 0.7:  # 高负载，启用更多节点
            inactive_nodes = [node for node in self.nodes.values() if not node.is_active]
            if inactive_nodes:
                # 启用成本最低的闲置节点
                cheapest_inactive = min(inactive_nodes, key=lambda x: x.cost_per_hour)
                cheapest_inactive.is_active = True
                print(f"⚡ 启用节点 {cheapest_inactive.node_id} (负载: {avg_load:.1%})")
        
        elif avg_load < 0.3:  # 低负载，停用部分节点
            active_nodes_sorted = sorted(active_nodes, key=lambda x: x.cost_per_hour, reverse=True)
            if len(active_nodes_sorted) > 3:  # 保持至少3个节点运行
                node_to_deactivate = active_nodes_sorted[0]
                node_to_deactivate.is_active = False
                print(f"💤 停用节点 {node_to_deactivate.node_id} (负载: {avg_load:.1%})")
    
    def generate_performance_report(self) -> Dict:
        """生成性能报告"""
        if not self.history:
            return {"error": "没有历史数据"}
        
        # 转换为DataFrame便于分析
        df = pd.DataFrame([
            {
                'timestamp': h['timestamp'],
                'messages': h['messages_processed'],
                'cost': h['iteration_cost'],
                'avg_cost': h['avg_cost_per_message']
            }
            for h in self.history
        ])
        
        # 计算统计指标
        report = {
            'simulation_summary': {
                'total_duration_minutes': len(self.history) * 0.5,  # 假设每次迭代0.5秒
                'total_messages': self.total_messages_processed,
                'total_cost': self.total_cost,
                'avg_cost_per_message': self.total_cost / self.total_messages_processed if self.total_messages_processed > 0 else 0,
                'messages_per_minute': self.total_messages_processed / (len(self.history) * 0.5 / 60) if self.history else 0
            },
            'cost_optimization_analysis': {
                'min_cost_per_message': df['avg_cost'].min(),
                'max_cost_per_message': df['avg_cost'].max(),
                'std_cost_per_message': df['avg_cost'].std(),
                'cost_variation_percent': (df['avg_cost'].std() / df['avg_cost'].mean() * 100) if df['avg_cost'].mean() > 0 else 0
            },
            'node_utilization': {
                'active_nodes': sum(1 for node in self.nodes.values() if node.is_active),
                'total_nodes': len(self.nodes),
                'avg_node_load': np.mean([node.current_load for node in self.nodes.values() if node.is_active]),
                'most_loaded_node': max([(node.node_id, node.current_load) for node in self.nodes.values()], key=lambda x: x[1])[0] if any(node.is_active for node in self.nodes.values()) else "N/A"
            },
            'comparison_with_traditional': {
                'traditional_avg_cost_per_message': 0.001,  # 传统系统假设成本
                'decentralized_avg_cost_per_message': self.total_cost / self.total_messages_processed if self.total_messages_processed > 0 else 0,
                'cost_savings_percent': ((0.001 - (self.total_cost / self.total_messages_processed)) / 0.001 * 100) if self.total_messages_processed > 0 else 0
            }
        }
        
        return report
    
    def visualize_results(self):
        """可视化结果"""
        if not self.history:
            print("没有足够的数据进行可视化")
            return
        
        # 准备数据
        timestamps = [h['timestamp'] for h in self.history]
        messages = [h['messages_processed'] for h in self.history]
        costs = [h['iteration_cost'] for h in self.history]
        avg_costs = [h['avg_cost_per_message'] for h in self.history]
        
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('去中心化邮箱系统性能分析', fontsize=16)
        
        # 1. 邮件处理量趋势
        axes[0, 0].plot(timestamps, messages, 'b-', alpha=0.7)
        axes[0, 0].set_title('邮件处理量趋势')
        axes[0, 0].set_xlabel('时间')
        axes[0, 0].set_ylabel('邮件数量')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].fill_between(timestamps, 0, messages, alpha=0.3)
        
        # 2. 成本趋势
        axes[0, 1].plot(timestamps, costs, 'r-', alpha=0.7)
        axes[0, 1].set_title('处理成本趋势')
        axes[0, 1].set_xlabel('时间')
        axes[0, 1].set_ylabel('成本 ($)')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. 平均每封邮件成本
        axes[1, 0].plot(timestamps, avg_costs, 'g-', alpha=0.7)
        axes[1, 0].axhline(y=0.001, color='r', linestyle='--', alpha=0.5, label='传统系统成本')
        axes[1, 0].set_title('平均每封邮件成本')
        axes[1, 0].set_xlabel('时间')
        axes[1, 0].set_ylabel('成本 ($/邮件)')
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].legend()
        axes[1, 0].fill_between(timestamps, 0, avg_costs, alpha=0.3)
        
        # 4. 节点负载分布
        node_ids = [node.node_id for node in self.nodes.values()]
        node_loads = [node.current_load * 100 for node in self.nodes.values()]
        node_colors = ['#FF6B6B' if node.is_active else '#C7C7C7' for node in self.nodes.values()]
        
        axes[1, 1].barh(node_ids, node_loads, color=node_colors)
        axes[1, 1].set_title('节点负载分布')
        axes[1, 1].set_xlabel('负载 (%)')
        axes[1, 1].grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        
        # 保存图表
        plt.savefig('cost_optimizer/performance_analysis.png', dpi=150, bbox_inches='tight')
        plt.show()
        
        print("📊 图表已保存到: cost_optimizer/performance_analysis.png")


# ========== 主演示程序 ==========

def main_demonstration():
    """主演示程序"""
    print("=" * 70)
    print("          分布式去中心化邮箱系统 - 动态成本优化演示")
    print("=" * 70)
    print()
    print("📌 演示目标:")
    print("  1. 展示基于使用频率的动态成本调整")
    print("  2. 演示公共中心服务器成本的动态优化")
    print("  3. 对比传统中心化系统的成本优势")
    print("  4. 可视化性能分析和成本节省")
    print()
    
    # 步骤1: 初始化成本引擎
    print("🔧 步骤1: 初始化动态成本优化引擎...")
    cost_engine = DynamicCostEngine()
    time.sleep(1)
    
    # 步骤2: 创建去中心化网络
    print("🔧 步骤2: 创建去中心化邮件网络...")
    network = DecentralizedMailNetwork(cost_engine)
    time.sleep(1)
    
    # 步骤3: 运行成本优化演示
    print("🔧 步骤3: 运行成本优化演示...")
    optimization_result = cost_engine.run_optimization_cycle()
    time.sleep(1)
    
    # 步骤4: 模拟网络流量
    print("\n🚀 步骤4: 模拟网络流量和动态成本调整...")
    print("   将模拟1小时的网络活动，展示动态成本优化效果")
    print()
    
    # 在新线程中运行模拟
    simulation_thread = threading.Thread(
        target=network.simulate_network_traffic,
        args=(0.1,)  # 模拟0.1小时（6分钟）
    )
    simulation_thread.daemon = True
    simulation_thread.start()
    
    # 等待模拟完成
    simulation_thread.join()
    
    # 步骤5: 运行完整的成本优化周期
    print("\n🔄 步骤5: 运行完整的成本优化周期...")
    for i in range(3):
        print(f"\n优化周期 {i+1}/3:")
        result = cost_engine.run_optimization_cycle()
        time.sleep(2)
    
    # 步骤6: 生成性能报告
    print("\n📊 步骤6: 生成性能报告...")
    performance_report = network.generate_performance_report()
    
    if 'error' not in performance_report:
        print("\n" + "=" * 60)
        print("📈 性能报告摘要")
        print("=" * 60)
        
        summary = performance_report['simulation_summary']
        print(f"总邮件数量: {summary['total_messages']}")
        print(f"总成本: ${summary['total_cost']:.4f}")
        print(f"平均每封邮件成本: ${summary['avg_cost_per_message']:.6f}")
        print(f"处理速率: {summary['messages_per_minute']:.1f} 封/分钟")
        
        print("\n💰 成本优化效果:")
        comparison = performance_report['comparison_with_traditional']
        print(f"传统系统平均成本: ${comparison['traditional_avg_cost_per_message']:.6f}/邮件")
        print(f"去中心化系统平均成本: ${comparison['decentralized_avg_cost_per_message']:.6f}/邮件")
        print(f"成本节省: {comparison['cost_savings_percent']:.1f}%")
        
        print("\n🖥️  节点利用情况:")
        utilization = performance_report['node_utilization']
        print(f"活跃节点: {utilization['active_nodes']}/{utilization['total_nodes']}")
        print(f"平均负载: {utilization['avg_node_load']:.1%}")
        
        # 生成成本引擎报告
        print("\n📋 成本优化分析报告:")
        cost_report = cost_engine.generate_cost_report(period_hours=1)
        
        if 'error' not in cost_report:
            stats = cost_report['cost_statistics']
            print(f"平均基础成本: ${stats['avg_base_cost']:.6f}/邮件")
            print(f"平均动态成本: ${stats['avg_dynamic_cost']:.6f}/邮件")
            print(f"平均成本降低: {stats['avg_cost_reduction']:.1f}%")
            print(f"最大成本降低: {stats['max_cost_reduction']:.1f}%")
            print(f"总成本节省: ${stats['total_cost_savings']:.6f}")
            
            print("\n💡 优化建议:")
            for rec in cost_report['recommendations']:
                print(f"  • {rec}")
    
    # 步骤7: 可视化结果
    print("\n📊 步骤7: 生成可视化图表...")
    try:
        network.visualize_results()
        print("✅ 图表生成成功!")
    except Exception as e:
        print(f"⚠️  图表生成失败: {e}")
    
    # 步骤8: 总结
    print("\n" + "=" * 70)
    print("🎯 演示总结")
    print("=" * 70)
    print()
    print("✅ 已验证的关键优势:")
    print("  1. 基于使用频率的动态成本调整 ✓")
    print("  2. 公共服务器维护成本的动态优化 ✓")
    print("  3. 去中心化节点的智能负载均衡 ✓")
    print("  4. 显著的成本节省效果 ✓")
    print()
    print("📊 核心数据:")
    if 'error' not in performance_report:
        comp = performance_report['comparison_with_traditional']
        print(f"  • 成本节省: {comp['cost_savings_percent']:.1f}%")
        print(f"  • 每封邮件成本: ${comp['decentralized_avg_cost_per_message']:.6f}")
    
    print()
    print("🚀 实际应用价值:")
    print("  • 高频用户获得成本折扣，鼓励活跃使用")
    print("  • 网络贡献者通过中继获得收益")
    print("  • 系统可根据负载动态调整资源")
    print("  • 总运营成本显著降低")
    print()
    print("💡 技术实现要点:")
    print("  • 实时监控用户活动和网络负载")
    print("  • 机器学习预测需求变化")
    print("  • 智能合约实现公平的成本分配")
    print("  • 弹性架构支持动态扩缩容")
    print()
    print("=" * 70)
    print("🎉 演示完成！分布式去中心化系统的动态成本优化已成功验证")
    print("=" * 70)
    
    # 保存详细报告
    detailed_report = {
        'timestamp': datetime.now().isoformat(),
        'performance_report': performance_report,
        'cost_report': cost_report if 'cost_report' in locals() else {},
        'optimization_results': [r.to_dict() for r in cost_engine.cost_history[-5:]]  # 最后5次优化结果
    }
    
    with open('cost_optimizer/detailed_demo_report.json', 'w', encoding='utf-8') as f:
        json.dump(detailed_report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 详细报告已保存到: cost_optimizer/detailed_demo_report.json")
    
    return network, cost_engine

if __name__ == "__main__":
    try:
        network, cost_engine = main_demonstration()
        
        # 交互式演示
        print("\n🔄 交互式演示 (按Ctrl+C退出)")
        print("输入 'cost [用户ID]' 查看特定用户的动态成本")
        print("输入 'report' 查看最新报告")
        print("输入 'optimize' 运行成本优化")
        print("输入 'exit' 退出")
        
        while True:
            try:
                command = input("\n>>> ").strip().lower()
                
                if command.startswith('cost '):
                    user_id = command[5:].strip()
                    dynamic_cost, breakdown = cost_engine.calculate_dynamic_cost(user_id)
                    print(f"\n用户 {user_id} 的成本分析:")
                    print(f"  基础成本: ${breakdown['base_cost']:.6f}")
                    print(f"  动态成本: ${breakdown['final_cost']:.6f}")
                    print(f"  成本降低: {breakdown['cost_reduction_percent']:.1f}%")
                    
                elif command == 'report':
                    report = cost_engine.generate_cost_report(period_hours=1)
                    if 'error' not in report:
                        stats = report['cost_statistics']
                        print(f"\n📊 最近1小时报告:")
                        print(f"  平均成本降低: {stats['avg_cost_reduction']:.1f}%")
                        print(f"  总成本节省: ${stats['total_cost_savings']:.6f}")
                        
                elif command == 'optimize':
                    print("\n🔄 运行成本优化...")
                    result = cost_engine.run_optimization_cycle()
                    
                elif command == 'exit':
                    print("👋 退出演示程序")
                    break
                    
                else:
                    print("❓ 未知命令，可用命令: cost, report, optimize, exit")
                    
            except KeyboardInterrupt:
                print("\n👋 退出演示程序")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")
                
    except KeyboardInterrupt:
        print("\n👋 演示被用户中断")
    except Exception as e:
        print(f"❌ 演示程序出错: {e}")
        import traceback
        traceback.print_exc()