import React, { useState, useEffect } from 'react';
import { Shield, Server, Database, Bell, Info, Power } from 'lucide-react';

export function Settings() {
  const [port, setPort] = useState(8100);
  const [stunEnabled, setStunEnabled] = useState(false);
  const [status, setStatus] = useState('未运行');
  const [nodeInfo, setNodeInfo] = useState(null);

  // 定期检查服务器状态
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await fetch('http://localhost:8102/api/health');
        if (response.ok) {
          const result = await response.json();
          setStatus('运行中');
          setNodeInfo(result);
        } else {
          setStatus('已停止');
          setNodeInfo(null);
        }
      } catch (error) {
        setStatus('已停止');
        setNodeInfo(null);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleStopServer = async () => {
    if (!confirm('确定要停止服务器吗？')) return;

    try {
      const response = await fetch('http://localhost:8102/api/stop', {
        method: 'POST'
      });
      const result = await response.json();
      if (result.success) {
        alert('服务器正在停止');
        setStatus('已停止');
        setNodeInfo(null);
      }
    } catch (error) {
      alert('停止失败：' + error.message);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">设置</h2>

      {/* 服务器状态 */}
      <div className="bg-white rounded-xl p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Server className="w-6 h-6 text-primary-500" />
            <h3 className="text-lg font-semibold text-gray-900">服务器状态</h3>
          </div>
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${
            status === '运行中' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {status}
          </div>
        </div>

        {nodeInfo && (
          <div className="space-y-2 text-sm">
            <p><strong>节点ID:</strong> {nodeInfo.node_id?.slice(0, 16)}...</p>
            <p><strong>API地址:</strong> http://localhost:8102</p>
            <p><strong>P2P端口:</strong> 8000</p>
            <p><strong>运行时间:</strong> {Math.floor((Date.now() / 1000 - nodeInfo.timestamp))} 秒</p>
          </div>
        )}

        {status === '运行中' && (
          <button
            onClick={handleStopServer}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2"
          >
            <Power className="w-4 h-4" />
            停止服务器
          </button>
        )}
      </div>

      {/* 网络设置 */}
      <div className="bg-white rounded-xl p-6 border border-gray-200">
        <div className="flex items-center gap-3 mb-6">
          <Server className="w-6 h-6 text-primary-500" />
          <h3 className="text-lg font-semibold text-gray-900">网络设置</h3>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">本地端口</label>
            <input
              type="number"
              value={port}
              onChange={(e) => setPort(parseInt(e.target.value))}
              className="w-64 px-4 py-2 border border-gray-300 rounded-lg"
            />
            <p className="text-sm text-gray-500 mt-1">用于P2P通信的本地端口</p>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">启用STUN</label>
              <p className="text-sm text-gray-500">自动发现公网IP和NAT穿透</p>
            </div>
            <button
              onClick={() => setStunEnabled(!stunEnabled)}
              className={`relative w-12 h-6 rounded-full transition-colors ${
                stunEnabled ? 'bg-primary-600' : 'bg-gray-300'
              }`}
            >
              <span
                className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                  stunEnabled ? 'left-7' : 'left-1'
                }`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* 安全设置 */}
      <div className="bg-white rounded-xl p-6 border border-gray-200">
        <div className="flex items-center gap-3 mb-6">
          <Shield className="w-6 h-6 text-primary-500" />
          <h3 className="text-lg font-semibold text-gray-900">安全设置</h3>
        </div>

        <div className="space-y-4">
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <h4 className="font-medium text-green-900 mb-2">当前加密算法</h4>
            <ul className="text-sm text-green-800 space-y-1">
              <li>• 密钥交换: X25519 (ECDH)</li>
              <li>• 数据加密: ChaCha20-Poly1305</li>
              <li>• 安全等级: 军用级 (256位)</li>
            </ul>
          </div>

          <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">
            重新生成密钥对
          </button>
        </div>
      </div>

      {/* 存储设置 */}
      <div className="bg-white rounded-xl p-6 border border-gray-200">
        <div className="flex items-center gap-3 mb-6">
          <Database className="w-6 h-6 text-primary-500" />
          <h3 className="text-lg font-semibold text-gray-900">存储设置</h3>
        </div>

        <div className="space-y-4">
          <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">
            清空收件箱
          </button>
          <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">
            清空已发送
          </button>
          <button className="px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50">
            清空所有数据
          </button>
        </div>
      </div>

      {/* 关于 */}
      <div className="bg-white rounded-xl p-6 border border-gray-200">
        <div className="flex items-center gap-3 mb-6">
          <Info className="w-6 h-6 text-primary-500" />
          <h3 className="text-lg font-semibold text-gray-900">关于</h3>
        </div>

        <div className="space-y-2 text-sm text-gray-600">
          <p><strong>版本:</strong> 1.0.0</p>
          <p><strong>协议:</strong> P2P SecureMail</p>
          <p><strong>加密:</strong> X25519 + ChaCha20-Poly1305</p>
          <p><strong>开源:</strong> MIT License</p>
        </div>
      </div>
    </div>
  );
}
