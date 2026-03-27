import React, { useEffect, useState } from 'react';
import { Wifi, WifiOff, Activity, Lock, Loader2, Globe, Copy, Check } from 'lucide-react';
import { useP2PStore } from '../store/p2p';
import { useNavigate } from 'react-router-dom';

export function P2PStatus() {
  const navigate = useNavigate();
  const [nodeId, setNodeId] = useState('未启动');
  const [publicAddress, setPublicAddress] = useState(null);
  const { status, setStatus, addLog } = useP2PStore();
  const [starting, setStarting] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    // 从存储获取节点ID
    const saved = localStorage.getItem('p2p-node-id');
    if (saved) {
      setNodeId(saved);
    }

    // 定期检查节点信息（包括公网地址）
    const checkNodeInfo = async () => {
      try {
        const response = await fetch('http://localhost:8102/api/node');
        const result = await response.json();
        if (result.success && result.data) {
          // 检查是否有公网地址（通过 ICE candidates）
          const publicCandidate = result.data.ice_candidates?.find(c => c.type === 'public' || c.type === 'TLS443');
          if (publicCandidate) {
            setPublicAddress(`${publicCandidate.host}:${publicCandidate.port}`);
          }
        }
      } catch (error) {
        // 忽略错误
      }
    };

    checkNodeInfo();
    const interval = setInterval(checkNodeInfo, 3000);
    return () => clearInterval(interval);
  }, []);

  const startNode = async () => {
    setStarting(true);
    setStatus('starting');
    addLog({ type: 'info', message: '正在启动P2P节点...' });

    try {
      console.log('发送启动请求到: http://localhost:8102/api/start');
      const response = await fetch('http://localhost:8102/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });

      console.log('响应状态:', response.status);
      const data = await response.json();
      console.log('响应数据:', data);

      if (data.success) {
        const id = data.data?.node_id;
        if (id) {
          setNodeId(id);
          localStorage.setItem('p2p-node-id', id);
        }
        setStatus('running');
        addLog({ type: 'success', message: 'P2P节点启动成功' });
      } else {
        throw new Error(data.error || '启动失败');
      }
    } catch (error) {
      console.error('启动失败:', error);
      setStatus('stopped');
      addLog({ type: 'error', message: `启动失败: ${error.message}` });
      alert(`启动失败: ${error.message}`);
    } finally {
      setStarting(false);
    }
  };

  const handleCopyNodeId = () => {
    if (nodeId && nodeId !== '未启动') {
      navigator.clipboard.writeText(nodeId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-6">
        {/* 连接状态 */}
        <div className="flex items-center gap-2">
          {status === 'running' ? (
            <Wifi className="w-5 h-5 text-green-500" />
          ) : (
            <WifiOff className="w-5 h-5 text-red-500" />
          )}
          <span className="text-sm font-medium text-gray-700">
            {status === 'running' ? '已连接' : '未连接'}
            {status === 'starting' && ' (启动中...)'}
          </span>
        </div>

        {/* 节点ID - 可点击复制 */}
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-primary-500" />
          <span
            onClick={handleCopyNodeId}
            className="text-sm text-gray-600 cursor-pointer hover:text-primary-600 hover:bg-primary-50 px-2 py-1 rounded transition-all flex items-center gap-1 group"
            title="点击复制节点ID"
          >
            ID: {nodeId !== '未启动' ? `${nodeId.slice(0, 8)}...` : nodeId}
            {copied ? (
              <Check className="w-3.5 h-3.5 text-green-500" />
            ) : (
              <Copy className="w-3.5 h-3.5 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            )}
          </span>
        </div>

        {/* 公网地址显示 */}
        {publicAddress && (
          <div className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-blue-500" />
            <span className="text-sm text-gray-600">
              公网: {publicAddress}
            </span>
          </div>
        )}

        {/* 加密状态 */}
        <div className="flex items-center gap-2">
          <Lock className="w-5 h-5 text-green-600" />
          <span className="text-sm text-green-600 font-medium">端到端加密</span>
        </div>
      </div>

      {/* 操作按钮 */}
      {status === 'stopped' && (
        <button
          onClick={startNode}
          disabled={starting}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {starting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              启动中...
            </>
          ) : (
            '启动节点'
          )}
        </button>
      )}
    </div>
  );
}
