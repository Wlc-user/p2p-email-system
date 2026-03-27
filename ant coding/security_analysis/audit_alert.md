# 📊 审计日志与异常告警系统设计

## 系统架构

```
[数据源] → [日志采集] → [日志处理] → [存储分析] → [告警引擎] → [通知渠道]
   ↓           ↓           ↓           ↓           ↓           ↓
客户端      Filebeat     Logstash   Elasticsearch 规则引擎  邮件/短信
服务器      Fluentd     处理管道     Splunk        机器学习  Slack/Webhook
数据库     自定义代理   过滤/丰富   数据仓库       AI分析    PagerDuty
```

## 审计日志设计

### 1. 日志分类与级别

```python
class AuditLogLevel:
    """审计日志级别定义"""
    
    CRITICAL = 0  # 系统崩溃、数据损坏
    ERROR    = 1  # 操作失败、安全违规
    WARNING  = 2  # 可疑行为、异常模式
    INFO     = 3  # 正常操作记录
    DEBUG    = 4  # 调试信息
    
class AuditLogCategory:
    """日志分类"""
    
    # 安全相关
    AUTHENTICATION = "auth"      # 认证/授权
    ACCESS_CONTROL = "access"    # 访问控制
    DATA_ACCESS    = "data"      # 数据访问
    CONFIG_CHANGE  = "config"    # 配置变更
    
    # 业务操作
    MAIL_SEND      = "mail_send"     # 邮件发送
    MAIL_RECEIVE   = "mail_receive"  # 邮件接收
    MAIL_DELETE    = "mail_delete"   # 邮件删除
    USER_MANAGE    = "user_manage"   # 用户管理
    
    # 系统操作
    SYSTEM_START   = "system_start"   # 系统启动
    SYSTEM_STOP    = "system_stop"    # 系统停止
    BACKUP_RESTORE = "backup"         # 备份恢复
```

### 2. 标准化日志格式

```python
class AuditLogEntry:
    """标准化审计日志条目"""
    
    def __init__(self):
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.log_id = self.generate_log_id()
        self.version = "1.0"
        
    def to_dict(self):
        return {
            # 元数据
            "metadata": {
                "log_id": self.log_id,
                "version": self.version,
                "timestamp": self.timestamp,
                "source": self.source,
                "environment": self.environment
            },
            
            # 事件数据
            "event": {
                "category": self.category,
                "type": self.event_type,
                "action": self.action,
                "severity": self.severity,
                "outcome": self.outcome  # success/failure
            },
            
            # 参与者
            "actors": {
                "initiator": {
                    "user_id": self.user_id,
                    "username": self.username,
                    "ip_address": self.client_ip,
                    "user_agent": self.user_agent,
                    "session_id": self.session_id
                },
                "target": {
                    "resource_type": self.resource_type,
                    "resource_id": self.resource_id,
                    "resource_name": self.resource_name
                }
            },
            
            # 上下文信息
            "context": {
                "location": {
                    "country": self.country,
                    "region": self.region,
                    "city": self.city,
                    "coordinates": self.coordinates
                },
                "device": {
                    "type": self.device_type,
                    "os": self.os,
                    "browser": self.browser,
                    "screen_resolution": self.screen_res
                },
                "network": {
                    "isp": self.isp,
                    "asn": self.asn,
                    "proxy_detected": self.proxy_detected
                }
            },
            
            # 详细数据
            "data": {
                "before_state": self.before_state,
                "after_state": self.after_state,
                "changes": self.changes,
                "parameters": self.parameters,
                "error_details": self.error_details
            },
            
            # 完整性保护
            "integrity": {
                "hash": self.calculate_hash(),
                "signature": self.signature,
                "chain_hash": self.chain_hash  # 区块链式完整性
            }
        }
```

### 3. 安全日志记录实现

```python
class SecureAuditLogger:
    """安全审计日志记录器"""
    
    def __init__(self):
        self.conn = self.create_secure_connection()
        self.write_queue = queue.Queue()
        self.writer_thread = threading.Thread(target=self._write_worker)
        self.writer_thread.start()
        
        # 初始化区块链式日志链
        self.log_chain = []
        self.last_hash = "0" * 64
        
    def log_security_event(self, event_data):
        """记录安全事件"""
        
        # 创建日志条目
        log_entry = AuditLogEntry(
            category=AuditLogCategory.AUTHENTICATION,
            event_type="failed_login",
            severity=AuditLogLevel.WARNING,
            **event_data
        )
        
        # 计算链式哈希
        entry_hash = self.calculate_entry_hash(log_entry, self.last_hash)
        log_entry.integrity["chain_hash"] = entry_hash
        self.last_hash = entry_hash
        
        # 数字签名
        log_entry.sign()
        
        # 异步写入队列
        self.write_queue.put(log_entry)
        
        # 实时分析
        self.realtime_analyzer.analyze(log_entry)
        
    def _write_worker(self):
        """后台写入线程"""
        while True:
            try:
                log_entry = self.write_queue.get(timeout=1)
                
                # 写入主数据库
                self.write_to_database(log_entry)
                
                # 写入副本
                self.write_to_replica(log_entry)
                
                # 写入不可变存储
                self.write_to_immutable_store(log_entry)
                
                # 更新区块链
                if self.enable_blockchain:
                    self.add_to_blockchain(log_entry)
                    
            except queue.Empty:
                continue
                
    def write_to_immutable_store(self, log_entry):
        """写入不可变存储（WORM）"""
        
        # 使用Write Once Read Many存储
        immutable_data = {
            "log_entry": log_entry.to_dict(),
            "timestamp": time.time(),
            "storage_proof": self.generate_storage_proof(log_entry)
        }
        
        # 存储到多个位置确保持久性
        storage_locations = [
            self.immutable_db,
            self.ipfs_storage,
            self.tape_backup
        ]
        
        for storage in storage_locations:
            storage.store(immutable_data)
```

## 异常检测与告警

### 1. 异常检测规则引擎

```python
class AnomalyDetectionEngine:
    """异常检测引擎"""
    
    def __init__(self):
        self.rules = self.load_detection_rules()
        self.ml_models = self.load_ml_models()
        self.baselines = self.calculate_baselines()
        
    def load_detection_rules(self):
        """加载检测规则"""
        return [
            # 暴力破解检测
            {
                "id": "BRUTE_FORCE_DETECTION",
                "name": "暴力破解检测",
                "description": "检测登录尝试频率异常",
                "condition": "COUNT(events[type='failed_login']) > 10 WITHIN 5m",
                "severity": "HIGH",
                "window": "5m",
                "threshold": 10
            },
            
            # 地理异常检测
            {
                "id": "GEO_ANOMALY",
                "name": "地理位置异常",
                "description": "用户从异常位置登录",
                "condition": "NEW_LOCATION_DISTANCE > 1000km AND TIME_DIFF < 1h",
                "severity": "MEDIUM",
                "baseline": "user_location_history"
            },
            
            # 数据泄露检测
            {
                "id": "DATA_EXFILTRATION",
                "name": "数据外泄检测",
                "description": "检测异常数据访问模式",
                "condition": "DATA_ACCESS_VOLUME > 3 * BASELINE",
                "severity": "CRITICAL",
                "window": "1h"
            },
            
            # 权限提升检测
            {
                "id": "PRIVILEGE_ESCALATION",
                "name": "权限提升尝试",
                "description": "检测未授权权限变更",
                "condition": "UNAUTHORIZED_ROLE_CHANGE",
                "severity": "CRITICAL"
            }
        ]
```

### 2. 机器学习异常检测

```python
class MLAnomalyDetector:
    """机器学习异常检测"""
    
    def __init__(self):
        # 加载预训练模型
        self.models = {
            "isolation_forest": self.load_isolation_forest(),
            "autoencoder": self.load_autoencoder(),
            "lof": self.load_local_outlier_factor(),
            "svm": self.load_one_class_svm()
        }
        
        # 特征工程
        self.feature_extractor = FeatureExtractor()
        
    def detect_anomalies(self, log_events):
        """检测异常"""
        
        # 特征提取
        features = self.feature_extractor.extract_features(log_events)
        
        # 多模型检测
        anomalies = []
        for model_name, model in self.models.items():
            predictions = model.predict(features)
            scores = model.decision_function(features)
            
            for i, (pred, score) in enumerate(zip(predictions, scores)):
                if pred == -1:  # 异常
                    anomalies.append({
                        "event_index": i,
                        "model": model_name,
                        "score": float(score),
                        "features": features[i].tolist()
                    })
        
        # 集成投票
        final_anomalies = self.ensemble_voting(anomalies)
        
        return final_anomalies
    
    def extract_features(self, events):
        """提取异常检测特征"""
        
        features = []
        for event in events:
            feature_vector = [
                # 时间特征
                event.hour_of_day,
                event.day_of_week,
                event.is_weekend,
                event.time_since_last_event,
                
                # 频率特征
                event.events_per_minute,
                event.failed_attempts_rate,
                event.success_rate,
                
                # 位置特征
                event.distance_from_usual,
                event.new_country_flag,
                event.new_city_flag,
                
                # 行为特征
                event.unusual_resource_access,
                event.privilege_change_count,
                event.data_volume_mb,
                
                # 设备特征
                event.new_device_flag,
                event.browser_change_flag,
                event.os_change_flag,
                
                # 网络特征
                event.tor_exit_node,
                event.vpn_detected,
                event.proxy_detected
            ]
            features.append(feature_vector)
        
        return np.array(features)
```

### 3. 实时流式检测

```python
class RealTimeAnomalyDetection:
    """实时异常检测"""
    
    def __init__(self):
        # 使用Apache Flink进行流处理
        self.env = StreamExecutionEnvironment.get_execution_environment()
        self.setup_stream_processing()
        
    def setup_stream_processing(self):
        """设置流处理管道"""
        
        # 创建数据流
        log_stream = self.env.add_source(KafkaSource())
        
        # 实时处理管道
        processed_stream = (
            log_stream
            .map(self.parse_log_event)
            .filter(self.filter_security_events)
            .key_by(lambda e: e.user_id)
            .window(TumblingEventTimeWindows.of(Time.minutes(5)))
            .process(self.analyze_window)
            .filter(self.detect_anomalies)
            .map(self.generate_alert)
        )
        
        # 输出到告警系统
        processed_stream.add_sink(AlertSink())
        
    def analyze_window(self, events, ctx):
        """分析时间窗口"""
        
        window_analysis = {
            "window_start": ctx.window().get_start(),
            "window_end": ctx.window().get_end(),
            "event_count": len(events),
            "failed_logins": sum(1 for e in events if e.type == "failed_login"),
            "unique_ips": len(set(e.ip_address for e in events)),
            "data_volume": sum(e.data_size for e in events),
            "geographic_spread": self.calculate_geo_spread(events)
        }
        
        # 检测异常模式
        anomalies = self.detect_window_anomalies(window_analysis)
        
        yield anomalies
```

## 告警系统设计

### 1. 告警分级与路由

```python
class AlertRoutingSystem:
    """告警路由系统"""
    
    ALERT_LEVELS = {
        "CRITICAL": {
            "response_time": "5分钟",
            "escalation": "15分钟未响应自动升级",
            "channels": ["pagerduty", "sms", "phone", "slack_critical"],
            "teams": ["security_team", "oncall_engineer", "management"]
        },
        "HIGH": {
            "response_time": "30分钟",
            "escalation": "2小时未响应自动升级",
            "channels": ["slack", "email", "sms"],
            "teams": ["security_team", "operations"]
        },
        "MEDIUM": {
            "response_time": "4小时",
            "escalation": "24小时未响应自动升级",
            "channels": ["slack", "email"],
            "teams": ["security_team"]
        },
        "LOW": {
            "response_time": "24小时",
            "escalation": "无需自动升级",
            "channels": ["email", "dashboard"],
            "teams": ["security_team"]
        }
    }
    
    def route_alert(self, alert):
        """路由告警"""
        
        level_config = self.ALERT_LEVELS[alert.severity]
        
        # 根据时间路由
        if self.is_business_hours():
            routing = level_config["channels"]
        else:
            routing = self.get_after_hours_routing(level_config)
        
        # 根据告警类型路由
        if alert.type == "data_breach":
            routing.append("legal_team")
        elif alert.type == "system_outage":
            routing.append("infrastructure_team")
        
        return routing
```

### 2. 告警抑制与聚合

```python
class AlertSuppression:
    """告警抑制与聚合"""
    
    def __init__(self):
        self.suppression_rules = self.load_suppression_rules()
        self.aggregation_window = timedelta(minutes=10)
        self.alert_cache = {}
        
    def should_suppress(self, alert):
        """判断是否应该抑制告警"""
        
        # 基于规则的抑制
        for rule in self.suppression_rules:
            if self.matches_rule(alert, rule):
                if self.within_suppression_window(alert, rule):
                    return True
        
        # 基于频率的抑制
        alert_key = self.get_alert_key(alert)
        recent_alerts = self.get_recent_alerts(alert_key)
        
        if len(recent_alerts) > self.get_frequency_threshold(alert):
            # 聚合告警而不是抑制
            return self.aggregate_alerts(alert_key, recent_alerts + [alert])
        
        return False
    
    def aggregate_alerts(self, alert_key, alerts):
        """聚合相似告警"""
        
        aggregated = {
            "aggregated_id": f"agg_{alert_key}_{int(time.time())}",
            "original_count": len(alerts),
            "first_occurrence": min(a.timestamp for a in alerts),
            "last_occurrence": max(a.timestamp for a in alerts),
            "sample_alerts": alerts[:3],  # 保留样本
            "summary": self.generate_aggregated_summary(alerts)
        }
        
        # 发送聚合告警
        self.send_aggregated_alert(aggregated)
        
        return True
```

### 3. 告警响应自动化

```python
class AutomatedResponse:
    """自动化响应系统"""
    
    def __init__(self):
        self.response_playbooks = self.load_response_playbooks()
        self.soar_integration = SOARIntegration()
        
    def execute_response(self, alert):
        """执行自动化响应"""
        
        playbook = self.select_playbook(alert)
        
        response_actions = []
        
        # 执行playbook中的步骤
        for step in playbook["steps"]:
            action_result = self.execute_action(step, alert)
            response_actions.append(action_result)
            
            # 如果步骤失败，执行回滚
            if not action_result.success:
                self.rollback_actions(response_actions)
                break
        
        # 记录响应结果
        self.log_response(alert, playbook, response_actions)
        
        # 如果需要人工介入，创建工单
        if playbook.get("requires_human_review"):
            self.create_incident_ticket(alert, response_actions)
            
        return response_actions
    
    def execute_action(self, step, alert):
        """执行响应动作"""
        
        actions = {
            "isolate_user": self.isolate_user_account,
            "block_ip": self.block_ip_address,
            "revoke_sessions": self.revoke_user_sessions,
            "enable_mfa": self.enable_mfa_for_user,
            "quarantine_data": self.quarantine_suspicious_data,
            "backup_state": self.backup_current_state,
            "notify_stakeholders": self.notify_stakeholders
        }
        
        if step["action"] in actions:
            return actions[step["action"]](alert, **step.get("parameters", {}))
        
        return ActionResult(success=False, error=f"未知动作: {step['action']}")
```

## 可视化与报告

### 1. 安全仪表板

```python
class SecurityDashboard:
    """安全仪表板"""
    
    def generate_dashboard(self):
        """生成安全仪表板"""
        
        dashboard_data = {
            "overview": {
                "total_alerts_today": self.get_today_alert_count(),
                "critical_alerts": self.get_critical_alerts(),
                "mean_time_to_detect": self.get_mttd(),
                "mean_time_to_respond": self.get_mttr()
            },
            
            "threat_intelligence": {
                "top_threats": self.get_top_threats(),
                "attack_vectors": self.get_attack_vectors(),
                "geographic_threats": self.get_geo_threats()
            },
            
            "user_behavior": {
                "risk_scores": self.get_user_risk_scores(),
                "anomalous_users": self.get_anomalous_users(),
                "privilege_changes": self.get_privilege_changes()
            },
            
            "system_security": {
                "vulnerabilities": self.get_vulnerability_status(),
                "patch_status": self.get_patch_status(),
                "compliance_status": self.get_compliance_status()
            }
        }
        
        return dashboard_data
```

### 2. 定期报告

```python
class SecurityReportGenerator:
    """安全报告生成器"""
    
    def generate_daily_report(self):
        """生成日报"""
        
        report = {
            "executive_summary": self.generate_executive_summary(),
            "incident_summary": {
                "total_incidents": self.get_daily_incident_count(),
                "by_severity": self.get_incidents_by_severity(),
                "by_category": self.get_incidents_by_category(),
                "top_incidents": self.get_top_incidents()
            },
            "threat_landscape": {
                "new_threats": self.get_new_threats(),
                "attack_trends": self.get_attack_trends(),
                "vulnerability_status": self.get_vulnerability_updates()
            },
            "performance_metrics": {
                "mttd": self.calculate_mttd(),
                "mttr": self.calculate_mttr(),
                "false_positives": self.get_false_positive_rate(),
                "coverage": self.get_detection_coverage()
            },
            "recommendations": self.generate_recommendations()
        }
        
        return report
```

## 合规性与取证

### 1. 合规性日志

```python
class ComplianceLogger:
    """合规性日志记录"""
    
    COMPLIANCE_FRAMEWORKS = {
        "GDPR": {
            "data_access_logging": True,
            "consent_management": True,
            "right_to_be_forgotten": True,
            "data_breach_notification": True
        },
        "HIPAA": {
            "phi_access_logging": True,
            "audit_trail_retention": 6,  # 年
            "access_reviews": True
        },
        "PCI_DSS": {
            "cardholder_data_logging": True,
            "access_monitoring": True,
            "regular_testing": True
        },
        "SOX": {
            "financial_data_logging": True,
            "change_management": True,
            "access_control": True
        }
    }
    
    def ensure_compliance(self, framework):
        """确保符合特定合规框架"""
        
        requirements = self.COMPLIANCE_FRAMEWORKS[framework]
        
        for requirement, enabled in requirements.items():
            if enabled:
                self.enable_compliance_logging(requirement)
                
        # 生成合规报告
        compliance_report = self.generate_compliance_report(framework)
        
        return compliance_report
```

### 2. 数字取证支持

```python
class ForensicSupport:
    """数字取证支持"""
    
    def collect_evidence(self, incident_id):
        """收集取证证据"""
        
        evidence = {
            "timeline": self.reconstruct_timeline(incident_id),
            "network_logs": self.collect_network_logs(incident_id),
            "system_logs": self.collect_system_logs(incident_id),
            "application_logs": self.collect_application_logs(incident_id),
            "memory_dumps": self.collect_memory_dumps(),
            "disk_images": self.create_disk_images(),
            "metadata": self.extract_metadata(),
            "chain_of_custody": self.establish_chain_of_custody()
        }
        
        # 计算哈希值确保完整性
        for key, data in evidence.items():
            evidence[key]["hash"] = self.calculate_hash(data)
            
        return evidence
    
    def reconstruct_timeline(self, incident_id):
        """重构事件时间线"""
        
        events = self.get_related_events(incident_id)
        
        timeline = []
        for event in events:
            timeline.append({
                "timestamp": event.timestamp,
                "event_type": event.type,
                "user": event.user,
                "source": event.source_ip,
                "action": event.action,
                "target": event.target,
                "result": event.result,
                "evidence_id": event.evidence_id
            })
        
        return sorted(timeline, key=lambda x: x["timestamp"])
```

## 实施路线图

### 阶段1：基础日志（1-2个月）
- 实现基本审计日志记录
- 设置日志存储和保留策略
- 创建基础告警规则

### 阶段2：高级检测（3-4个月）
- 实施机器学习异常检测
- 部署实时流处理
- 建立告警路由和抑制

### 阶段3：自动化响应（5-6个月）
- 实施自动化响应playbook
- 集成SOAR平台
- 建立取证能力

### 阶段4：持续优化（7-12个月）
- 优化检测规则
- 实施威胁情报集成
- 建立合规报告自动化

这个审计日志与异常告警系统提供了企业级的安全监控能力，能够及时发现和响应安全威胁。