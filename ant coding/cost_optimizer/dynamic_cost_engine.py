#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态成本优化引擎 - 实现基于使用频率的分布式系统成本优化
"""

import time
import json
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict
import statistics
import math

@dataclass
class UserActivity:
    """用户活动数据"""
    user_id: str
    message_count: int = 0
    storage_mb: float = 0.0
    relay_count: int = 0
    online_hours: float = 0.0
    last_active: datetime = None
    contribution_score: float = 0.0
    
    def update_activity(self, message_size_mb: float = 0.0, is_relay: bool = False):
        """更新用户活动"""
        self.message_count += 1
        self.storage_mb += message_size_mb
        if is_relay:
            self.relay_count += 1
        self.last_active = datetime.now()
        
        # 计算贡献分数
        self.contribution_score = self._calculate_contribution_score()
    
    def _calculate_contribution_score(self) -> float:
        """计算用户贡献分数"""
        # 基于多个维度的加权分数
        score = (
            self.message_count * 0.3 +
            math.log1p(self.storage_mb) * 0.2 +
            self.relay_count * 0.4 +
            self.online_hours * 0.1
        )
        return score

@dataclass
class NetworkMetrics:
    """网络指标数据"""
    timestamp: datetime
    concurrent_users: int
    messages_per_minute: float
    storage_growth_mb: float
    network_latency_ms: float
    bandwidth_usage_mbps: float
    server_load_percent: float
    
    @classmethod
    def from_current_state(cls, network_state: Dict):
        """从当前网络状态创建指标"""
        return cls(
            timestamp=datetime.now(),
            concurrent_users=network_state.get('concurrent_users', 0),
            messages_per_minute=network_state.get('messages_per_minute', 0.0),
            storage_growth_mb=network_state.get('storage_growth_mb', 0.0),
            network_latency_ms=network_state.get('avg_latency_ms', 50.0),
            bandwidth_usage_mbps=network_state.get('bandwidth_mbps', 10.0),
            server_load_percent=network_state.get('server_load', 30.0)
        )

@dataclass
class CostOptimizationResult:
    """成本优化结果"""
    timestamp: datetime
    base_cost_per_message: float
    dynamic_cost_per_message: float
    cost_reduction_percent: float
    optimal_server_config: Dict[str, Any]
    user_tier_adjustments: Dict[str, float]
    resource_allocations: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

class DynamicCostEngine:
    """动态成本优化引擎"""
    
    def __init__(self, config_file: str = "config/cost_config.json"):
        """初始化动态成本引擎"""
        self.config = self._load_config(config_file)
        self.user_activities: Dict[str, UserActivity] = {}
        self.network_history: List[NetworkMetrics] = []
        self.cost_history: List[CostOptimizationResult] = []
        
        # 初始化时间窗口
        self.time_windows = {
            'peak': (9, 18),      # 9:00-18:00
            'off_peak': (0, 9),   # 0:00-9:00
            'evening': (18, 24)   # 18:00-24:00
        }
        
        # 成本参数
        self.base_cost_params = {
            'compute_cost_per_hour': 0.10,      # 计算成本 $/小时
            'storage_cost_per_gb_month': 0.023, # 存储成本 $/GB/月
            'bandwidth_cost_per_gb': 0.085,     # 带宽成本 $/GB
            'maintenance_cost_per_user': 0.001, # 维护成本 $/用户
        }
        
        print("✅ 动态成本优化引擎初始化完成")
    
    def _load_config(self, config_file: str) -> Dict:
        """加载配置文件"""
        default_config = {
            'optimization_interval_minutes': 5,
            'prediction_horizon_hours': 24,
            'min_cost_per_message': 0.0001,
            'max_cost_per_message': 0.01,
            'activity_tiers': {
                'high': {'threshold': 100, 'discount': 0.6},
                'medium': {'threshold': 30, 'discount': 0.8},
                'low': {'threshold': 10, 'discount': 1.0},
                'inactive': {'threshold': 0, 'discount': 1.2}
            },
            'time_adjustments': {
                'peak': 1.2,
                'off_peak': 0.7,
                'evening': 0.9
            },
            'load_adjustments': {
                'low': 0.8,      # <30%负载
                'medium': 1.0,   # 30-70%负载
                'high': 1.3,     # >70%负载
                'critical': 1.5  # >90%负载
            }
        }
        
        # 实际项目中从文件加载
        return default_config
    
    def record_user_activity(self, user_id: str, message_size_mb: float = 0.1, is_relay: bool = False):
        """记录用户活动"""
        if user_id not in self.user_activities:
            self.user_activities[user_id] = UserActivity(user_id=user_id)
        
        self.user_activities[user_id].update_activity(message_size_mb, is_relay)
    
    def record_network_metrics(self, network_state: Dict):
        """记录网络指标"""
        metrics = NetworkMetrics.from_current_state(network_state)
        self.network_history.append(metrics)
        
        # 保持最近24小时的数据
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.network_history = [
            m for m in self.network_history 
            if m.timestamp > cutoff_time
        ]
    
    def calculate_dynamic_cost(self, user_id: str = None) -> Tuple[float, Dict]:
        """
        计算动态成本
        
        Args:
            user_id: 用户ID，如果为None则计算平均成本
            
        Returns:
            (动态成本, 成本明细)
        """
        # 获取当前网络状态
        if not self.network_history:
            current_metrics = NetworkMetrics(
                timestamp=datetime.now(),
                concurrent_users=0,
                messages_per_minute=0.0,
                storage_growth_mb=0.0,
                network_latency_ms=50.0,
                bandwidth_usage_mbps=1.0,
                server_load_percent=10.0
            )
        else:
            current_metrics = self.network_history[-1]
        
        # 1. 计算基础成本
        base_cost = self._calculate_base_cost(current_metrics)
        
        # 2. 计算时间调整因子
        time_factor = self._get_time_adjustment_factor()
        
        # 3. 计算负载调整因子
        load_factor = self._get_load_adjustment_factor(current_metrics.server_load_percent)
        
        # 4. 用户特定调整
        if user_id and user_id in self.user_activities:
            user_factor = self._get_user_adjustment_factor(user_id)
        else:
            user_factor = 1.0
        
        # 5. 网络贡献奖励
        network_bonus = 0.0
        if user_id:
            network_bonus = self._calculate_network_contribution_bonus(user_id)
        
        # 6. 计算动态成本
        dynamic_cost = base_cost * time_factor * load_factor * user_factor - network_bonus
        
        # 应用成本限制
        dynamic_cost = max(
            self.config['min_cost_per_message'],
            min(dynamic_cost, self.config['max_cost_per_message'])
        )
        
        # 成本明细
        cost_breakdown = {
            'base_cost': base_cost,
            'time_factor': time_factor,
            'load_factor': load_factor,
            'user_factor': user_factor if user_id else 'N/A',
            'network_bonus': network_bonus,
            'final_cost': dynamic_cost,
            'cost_reduction_percent': ((base_cost - dynamic_cost) / base_cost * 100) if base_cost > 0 else 0
        }
        
        return dynamic_cost, cost_breakdown
    
    def _calculate_base_cost(self, metrics: NetworkMetrics) -> float:
        """计算基础成本"""
        
        # 计算各项成本
        compute_cost = (
            self.base_cost_params['compute_cost_per_hour'] / 3600 *  # 每秒成本
            (metrics.concurrent_users / 100)  # 用户规模因子
        )
        
        storage_cost = (
            self.base_cost_params['storage_cost_per_gb_month'] / 
            (30 * 24 * 3600) *  # 转换为每秒成本
            metrics.storage_growth_mb / 1024  # MB转换为GB
        )
        
        bandwidth_cost = (
            self.base_cost_params['bandwidth_cost_per_gb'] / 
            (1024 * 8) *  # $/GB转换为$/Mbps
            metrics.bandwidth_usage_mbps
        )
        
        maintenance_cost = (
            self.base_cost_params['maintenance_cost_per_user'] / 
            (30 * 24 * 3600) *  # 转换为每秒成本
            metrics.concurrent_users
        )
        
        # 总基础成本
        total_base_cost = compute_cost + storage_cost + bandwidth_cost + maintenance_cost
        
        # 分摊到每封邮件
        if metrics.messages_per_minute > 0:
            cost_per_message = total_base_cost / (metrics.messages_per_minute / 60)
        else:
            cost_per_message = 0.001  # 默认成本
        
        return cost_per_message
    
    def _get_time_adjustment_factor(self) -> float:
        """获取时间调整因子"""
        current_hour = datetime.now().hour
        
        for time_window, (start, end) in self.time_windows.items():
            if start <= current_hour < end:
                return self.config['time_adjustments'][time_window]
        
        return 1.0  # 默认值
    
    def _get_load_adjustment_factor(self, server_load_percent: float) -> float:
        """获取负载调整因子"""
        if server_load_percent < 30:
            return self.config['load_adjustments']['low']
        elif server_load_percent < 70:
            return self.config['load_adjustments']['medium']
        elif server_load_percent < 90:
            return self.config['load_adjustments']['high']
        else:
            return self.config['load_adjustments']['critical']
    
    def _get_user_adjustment_factor(self, user_id: str) -> float:
        """获取用户调整因子"""
        if user_id not in self.user_activities:
            return 1.0
        
        user = self.user_activities[user_id]
        activity_score = user.contribution_score
        
        # 根据活跃度分级
        for tier_name, tier_config in self.config['activity_tiers'].items():
            if activity_score >= tier_config['threshold']:
                return tier_config['discount']
        
        return 1.0
    
    def _calculate_network_contribution_bonus(self, user_id: str) -> float:
        """计算网络贡献奖励"""
        if user_id not in self.user_activities:
            return 0.0
        
        user = self.user_activities[user_id]
        
        # 基于中继贡献的奖励
        relay_bonus = user.relay_count * 0.00005
        
        # 基于存储贡献的奖励
        storage_bonus = min(user.storage_mb / 1024, 10) * 0.0001
        
        # 基于在线时间的奖励
        online_bonus = min(user.online_hours, 720) * 0.000001  # 最多奖励30天
        
        total_bonus = relay_bonus + storage_bonus + online_bonus
        
        # 限制奖励额度
        max_bonus = 0.001  # 最大奖励
        return min(total_bonus, max_bonus)
    
    def optimize_server_resources(self) -> Dict[str, Any]:
        """优化服务器资源配置"""
        
        if not self.network_history:
            return self._get_default_server_config()
        
        # 分析历史数据
        recent_metrics = self.network_history[-12:]  # 最近1小时数据（如果5分钟收集一次）
        
        # 计算平均负载
        avg_concurrent = statistics.mean([m.concurrent_users for m in recent_metrics])
        avg_messages = statistics.mean([m.messages_per_minute for m in recent_metrics])
        avg_bandwidth = statistics.mean([m.bandwidth_usage_mbps for m in recent_metrics])
        
        # 预测未来负载
        predicted_load = self._predict_future_load(recent_metrics)
        
        # 计算最优配置
        optimal_config = {
            'compute_nodes': self._calculate_optimal_compute_nodes(avg_concurrent, predicted_load),
            'storage_gb': self._calculate_optimal_storage(avg_messages),
            'bandwidth_mbps': self._calculate_optimal_bandwidth(avg_bandwidth, predicted_load),
            'cache_size_mb': self._calculate_optimal_cache(avg_messages),
            'backup_frequency_hours': self._calculate_optimal_backup_frequency(avg_messages),
            'estimated_cost_per_hour': self._estimate_hourly_cost(avg_concurrent, avg_messages, avg_bandwidth)
        }
        
        return optimal_config
    
    def _predict_future_load(self, recent_metrics: List[NetworkMetrics]) -> Dict[str, float]:
        """预测未来负载"""
        # 简单的时间序列预测
        if len(recent_metrics) < 2:
            return {'concurrent_users': 0, 'messages_per_minute': 0}
        
        # 计算趋势
        latest = recent_metrics[-1]
        previous = recent_metrics[-2]
        
        concurrent_trend = latest.concurrent_users - previous.concurrent_users
        message_trend = latest.messages_per_minute - previous.messages_per_minute
        
        # 基于趋势预测（简化版）
        predicted_concurrent = max(0, latest.concurrent_users + concurrent_trend * 0.5)
        predicted_messages = max(0, latest.messages_per_minute + message_trend * 0.5)
        
        return {
            'concurrent_users': predicted_concurrent,
            'messages_per_minute': predicted_messages
        }
    
    def _calculate_optimal_compute_nodes(self, current_users: float, predicted_load: Dict) -> int:
        """计算最优计算节点数量"""
        base_nodes = 2  # 最小节点数
        
        # 根据用户规模增加节点
        max_users = max(current_users, predicted_load['concurrent_users'])
        
        if max_users < 100:
            return base_nodes
        elif max_users < 500:
            return base_nodes + 1
        elif max_users < 2000:
            return base_nodes + 2
        elif max_users < 5000:
            return base_nodes + 4
        else:
            return base_nodes + 8
    
    def _calculate_optimal_storage(self, messages_per_minute: float) -> float:
        """计算最优存储大小（GB）"""
        # 假设每封邮件平均0.1MB，保留7天数据
        daily_storage_gb = messages_per_minute * 60 * 24 * 0.1 / 1024
        seven_day_storage = daily_storage_gb * 7
        
        # 添加20%缓冲
        optimal_storage = seven_day_storage * 1.2
        
        # 最小1GB，最大100GB
        return max(1.0, min(optimal_storage, 100.0))
    
    def _calculate_optimal_bandwidth(self, current_bandwidth: float, predicted_load: Dict) -> float:
        """计算最优带宽（Mbps）"""
        # 基于当前使用和预测值
        max_bandwidth = max(current_bandwidth, predicted_load['messages_per_minute'] * 0.1)
        
        # 添加50%缓冲，最小10Mbps
        optimal_bandwidth = max_bandwidth * 1.5
        
        return max(10.0, optimal_bandwidth)
    
    def _calculate_optimal_cache(self, messages_per_minute: float) -> float:
        """计算最优缓存大小（MB）"""
        # 缓存最近1小时的热点数据
        hourly_cache_mb = messages_per_minute * 60 * 0.1
        
        # 最小100MB，最大2048MB
        return max(100.0, min(hourly_cache_mb, 2048.0))
    
    def _calculate_optimal_backup_frequency(self, messages_per_minute: float) -> int:
        """计算最优备份频率（小时）"""
        if messages_per_minute < 10:
            return 24  # 每天备份一次
        elif messages_per_minute < 100:
            return 6   # 每6小时备份
        else:
            return 1   # 每小时备份
    
    def _estimate_hourly_cost(self, concurrent_users: float, messages_per_minute: float, 
                            bandwidth_mbps: float) -> float:
        """估计每小时成本"""
        hourly_cost = 0.0
        
        # 计算节点成本（假设$0.10/小时/节点）
        nodes = self._calculate_optimal_compute_nodes(concurrent_users, 
                                                     {'concurrent_users': concurrent_users})
        hourly_cost += nodes * 0.10
        
        # 带宽成本（假设$0.085/GB）
        hourly_bandwidth_gb = bandwidth_mbps * 3600 / (8 * 1024)
        hourly_cost += hourly_bandwidth_gb * 0.085
        
        # 存储成本（假设$0.023/GB/月）
        storage_gb = self._calculate_optimal_storage(messages_per_minute)
        hourly_storage_cost = storage_gb * 0.023 / (30 * 24)
        hourly_cost += hourly_storage_cost
        
        return round(hourly_cost, 4)
    
    def _get_default_server_config(self) -> Dict[str, Any]:
        """获取默认服务器配置"""
        return {
            'compute_nodes': 2,
            'storage_gb': 10.0,
            'bandwidth_mbps': 10.0,
            'cache_size_mb': 256.0,
            'backup_frequency_hours': 24,
            'estimated_cost_per_hour': 0.25
        }
    
    def run_optimization_cycle(self) -> CostOptimizationResult:
        """运行完整的优化周期"""
        print(f"\n🔄 开始成本优化周期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 计算平均动态成本
        avg_dynamic_cost, avg_breakdown = self.calculate_dynamic_cost()
        
        # 2. 优化服务器资源配置
        optimal_config = self.optimize_server_resources()
        
        # 3. 计算用户层级调整
        user_tiers = {}
        for user_id in list(self.user_activities.keys())[:10]:  # 抽样前10个用户
            user_factor = self._get_user_adjustment_factor(user_id)
            user_tiers[user_id] = user_factor
        
        # 4. 资源分配建议
        resource_allocations = {
            'compute_priority': '均衡分配',
            'storage_tiering': '热数据SSD，冷数据HDD',
            'bandwidth_qos': '邮件传输优先，附件下载次之',
            'cache_strategy': 'LRU + 时间加权'
        }
        
        # 5. 创建优化结果
        result = CostOptimizationResult(
            timestamp=datetime.now(),
            base_cost_per_message=avg_breakdown['base_cost'],
            dynamic_cost_per_message=avg_dynamic_cost,
            cost_reduction_percent=avg_breakdown['cost_reduction_percent'],
            optimal_server_config=optimal_config,
            user_tier_adjustments=user_tiers,
            resource_allocations=resource_allocations
        )
        
        # 6. 保存历史
        self.cost_history.append(result)
        
        # 7. 输出结果
        self._print_optimization_result(result)
        
        return result
    
    def _print_optimization_result(self, result: CostOptimizationResult):
        """打印优化结果"""
        print("=" * 60)
        print("📊 成本优化结果")
        print("=" * 60)
        print(f"时间: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"基础成本: ${result.base_cost_per_message:.6f}/邮件")
        print(f"动态成本: ${result.dynamic_cost_per_message:.6f}/邮件")
        print(f"成本降低: {result.cost_reduction_percent:.1f}%")
        print()
        print("🖥️  最优服务器配置:")
        for key, value in result.optimal_server_config.items():
            if isinstance(value, float):
                print(f"  • {key}: {value:.2f}")
            else:
                print(f"  • {key}: {value}")
        print()
        print("👥 用户层级调整（抽样）:")
        for user_id, factor in result.user_tier_adjustments.items():
            tier = "高频" if factor < 0.8 else "中频" if factor < 1.0 else "低频"
            print(f"  • {user_id[:8]}...: {tier} ({factor:.2f}x)")
        print("=" * 60)
    
    def generate_cost_report(self, period_hours: int = 24) -> Dict[str, Any]:
        """生成成本报告"""
        if not self.cost_history:
            return {"error": "没有足够的历史数据"}
        
        # 筛选指定时间段的数据
        cutoff_time = datetime.now() - timedelta(hours=period_hours)
        relevant_results = [
            r for r in self.cost_history 
            if r.timestamp > cutoff_time
        ]
        
        if not relevant_results:
            return {"error": "指定时间段内没有数据"}
        
        # 计算统计信息
        base_costs = [r.base_cost_per_message for r in relevant_results]
        dynamic_costs = [r.dynamic_cost_per_message for r in relevant_results]
        reductions = [r.cost_reduction_percent for r in relevant_results]
        
        report = {
            'report_period': f'last_{period_hours}_hours',
            'generated_at': datetime.now().isoformat(),
            'total_optimization_cycles': len(relevant_results),
            'cost_statistics': {
                'avg_base_cost': statistics.mean(base_costs),
                'avg_dynamic_cost': statistics.mean(dynamic_costs),
                'avg_cost_reduction': statistics.mean(reductions),
                'max_cost_reduction': max(reductions) if reductions else 0,
                'min_cost_reduction': min(reductions) if reductions else 0,
                'total_cost_savings': sum(base_costs) - sum(dynamic_costs)
            },
            'user_activity_summary': {
                'total_active_users': len(self.user_activities),
                'high_activity_users': sum(1 for u in self.user_activities.values() 
                                          if u.contribution_score > 100),
                'medium_activity_users': sum(1 for u in self.user_activities.values() 
                                            if 30 <= u.contribution_score <= 100),
                'low_activity_users': sum(1 for u in self.user_activities.values() 
                                         if u.contribution_score < 30)
            },
            'recommendations': self._generate_recommendations(relevant_results)
        }
        
        return report
    
    def _generate_recommendations(self, results: List[CostOptimizationResult]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 分析成本模式
        avg_reduction = statistics.mean([r.cost_reduction_percent for r in results])
        
        if avg_reduction < 20:
            recommendations.append("成本优化空间有限，考虑重新设计成本模型")
        elif avg_reduction > 50:
            recommendations.append("成本优化效果显著，考虑进一步优化资源分配")
        
        # 分析用户活动
        high_activity_count = sum(1 for u in self.user_activities.values() 
                                 if u.contribution_score > 100)
        total_users = len(self.user_activities)
        
        if total_users > 0:
            high_activity_ratio = high_activity_count / total_users
            if high_activity_ratio < 0.1:
                recommendations.append("高活跃用户比例较低，考虑激励机制提升用户参与度")
        
        # 服务器配置分析
        recent_config = results[-1].optimal_server_config if results else None
        if recent_config and recent_config['compute_nodes'] > 4:
            recommendations.append("计算节点较多，考虑使用更强大的单节点或容器化部署")
        
        if recent_config and recent_config['estimated_cost_per_hour'] > 1.0:
            recommendations.append("每小时成本较高，考虑使用云服务的预留实例或spot实例")
        
        return recommendations if recommendations else ["当前配置已达到较优状态，继续保持"]


# ========== 演示程序 ==========

def demo_dynamic_cost_optimization():
    """演示动态成本优化"""
    print("=" * 60)
    print("     动态成本优化演示")
    print("=" * 60)
    print()
    
    # 创建成本引擎
    cost_engine = DynamicCostEngine()
    
    # 模拟用户活动
    print("👥 模拟用户活动...")
    users = ["alice@example1.com", "bob@example2.com", "charlie@example1.com", 
             "david@example2.com", "eve@example1.com"]
    
    for i in range(50):
        user = np.random.choice(users)
        message_size = np.random.uniform(0.01, 5.0)  # 0.01-5MB
        is_relay = np.random.random() < 0.3  # 30%的概率是中继
        
        cost_engine.record_user_activity(user, message_size, is_relay)
    
    print(f"已记录 {len(cost_engine.user_activities)} 个用户的活动")
    
    # 模拟网络指标
    print("\n🌐 模拟网络指标...")
    for i in range(12):  # 模拟1小时的数据（5分钟间隔）
        network_state = {
            'concurrent_users': np.random.randint(50, 500),
            'messages_per_minute': np.random.uniform(10, 200),
            'storage_growth_mb': np.random.uniform(10, 100),
            'avg_latency_ms': np.random.uniform(20, 200),
            'bandwidth_mbps': np.random.uniform(5, 50),
            'server_load': np.random.uniform(20, 80)
        }
        cost_engine.record_network_metrics(network_state)
        time.sleep(0.1)  # 模拟时间间隔
    
    print(f"已收集 {len(cost_engine.network_history)} 条网络指标")
    
    # 演示动态成本计算
    print("\n💰 演示动态成本计算...")
    
    for user in users[:3]:  # 演示前3个用户
        dynamic_cost, breakdown = cost_engine.calculate_dynamic_cost(user)
        
        print(f"\n用户: {user}")
        print(f"  基础成本: ${breakdown['base_cost']:.6f}")
        print(f"  最终成本: ${breakdown['final_cost']:.6f}")
        print(f"  成本降低: {breakdown['cost_reduction_percent']:.1f}%")
        
        # 显示调整因子
        print(f"  调整因子: 时间({breakdown['time_factor']:.2f}x), " +
              f"负载({breakdown['load_factor']:.2f}x), " +
              f"用户({breakdown['user_factor']:.2f}x)")
    
    # 运行完整优化周期
    print("\n🔄 运行完整优化周期...")
    optimization_result = cost_engine.run_optimization_cycle()
    
    # 生成报告
    print("\n📈 生成成本报告...")
    report = cost_engine.generate_cost_report(period_hours=1)
    
    if 'error' not in report:
        print(f"报告期间: {report['report_period']}")
        print(f"优化周期: {report['total_optimization_cycles']} 次")
        print(f"平均成本降低: {report['cost_statistics']['avg_cost_reduction']:.1f}%")
        print(f"总成本节省: ${report['cost_statistics']['total_cost_savings']:.4f}")
        
        print("\n💡 优化建议:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
    
    print("\n" + "=" * 60)
    print("🎉 演示完成!")
    print("=" * 60)
    
    return cost_engine

if __name__ == "__main__":
    demo_dynamic_cost_optimization()