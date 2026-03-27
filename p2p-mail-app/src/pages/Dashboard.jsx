import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useP2PStore } from '../store/p2p';
import { Mail, Send, Users, Activity } from 'lucide-react';

export function Dashboard() {
  const navigate = useNavigate();
  const { inbox, sent, contacts } = useP2PStore();

  const stats = [
    { label: '收件箱', value: inbox.length, icon: Mail, color: 'bg-blue-500' },
    { label: '已发送', value: sent.length, icon: Send, color: 'bg-green-500' },
    { label: '联系人', value: contacts.length, icon: Users, color: 'bg-purple-500' },
    { label: '在线节点', value: '-', icon: Activity, color: 'bg-orange-500' },
  ];

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">仪表盘</h2>

      {/* 统计卡片 */}
      <div className="grid grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <div className={`w-12 h-12 ${stat.color} rounded-lg flex items-center justify-center`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
              <span className="text-3xl font-bold text-gray-900">{stat.value}</span>
            </div>
            <p className="text-sm text-gray-600">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* 欢迎信息 */}
      <div className="bg-gradient-to-r from-primary-500 to-primary-600 rounded-xl p-6 text-white">
        <h3 className="text-xl font-bold mb-2">欢迎使用 P2P SecureMail</h3>
        <p className="text-primary-100 mb-4">
          这是完全去中心化的加密邮件系统，您的邮件只存储在本地，端到端加密，无需邮件服务器。
        </p>
        <div className="flex gap-3">
          <button className="px-4 py-2 bg-white text-primary-600 rounded-lg font-medium hover:bg-primary-50 transition-colors">
            开始使用
          </button>
          <button className="px-4 py-2 bg-primary-700 text-white rounded-lg font-medium hover:bg-primary-800 transition-colors">
            了解更多
          </button>
        </div>
      </div>

      {/* 快速操作 */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h4 className="font-semibold text-gray-900 mb-4">快速操作</h4>
          <div className="space-y-2">
            <button className="w-full text-left px-4 py-3 rounded-lg hover:bg-gray-50 flex items-center gap-3 transition-colors">
              <Mail className="w-5 h-5 text-primary-500" />
              查看收件箱
            </button>
            <button className="w-full text-left px-4 py-3 rounded-lg hover:bg-gray-50 flex items-center gap-3 transition-colors">
              <Send className="w-5 h-5 text-primary-500" />
              写新邮件
            </button>
            <button className="w-full text-left px-4 py-3 rounded-lg hover:bg-gray-50 flex items-center gap-3 transition-colors">
              <Users className="w-5 h-5 text-primary-500" />
              添加联系人
            </button>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h4 className="font-semibold text-gray-900 mb-4">安全提示</h4>
          <ul className="space-y-3 text-sm text-gray-600">
            <li className="flex items-start gap-2">
              <span className="text-green-500">✓</span>
              端到端加密：只有收发双方能查看邮件
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-500">✓</span>
              无服务器依赖：邮件直接点对点传输
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-500">✓</span>
              数据本地存储：您的数据完全自主
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-500">✓</span>
              抗审查通信：DHT分布式网络
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
