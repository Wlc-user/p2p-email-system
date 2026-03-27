import React, { useEffect, useState } from 'react';
import { mailAPI } from '../api';
import { useAuthStore } from '../store/auth';
import { Send, Clock, Trash2, RefreshCw, Lock, Undo } from 'lucide-react';

export function Sent() {
  const { token } = useAuthStore();
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [recallLoading, setRecallLoading] = useState(false);

  const loadSent = async () => {
    setLoading(true);
    try {
      const result = await mailAPI.sent(token);
      if (result.success) {
        setEmails(result.emails || []);
      }
    } catch (error) {
      console.error('加载已发送失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      loadSent();
    }
  }, [token]);

  const handleRecall = async () => {
    if (!selectedEmail) return;
    if (!confirm('确定要撤回这封邮件吗？撤回后对方将无法查看。')) return;

    setRecallLoading(true);
    try {
      const result = await mailAPI.recall(token, selectedEmail.id);
      if (result.success) {
        alert('邮件已撤回');
        loadSent();
        setSelectedEmail(null);
      } else {
        alert('撤回失败：' + (result.error || '未知错误'));
      }
    } catch (error) {
      alert('撤回错误：' + error.message);
    } finally {
      setRecallLoading(false);
    }
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays < 7) return `${diffDays}天前`;
    return date.toLocaleDateString('zh-CN');
  };

  return (
    <div className="p-6 space-y-6">
      {/* 标题和操作 */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">已发送</h2>
        <button
          onClick={loadSent}
          className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          disabled={loading}
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          刷新
        </button>
      </div>

      {selectedEmail ? (
        /* 邮件详情 */
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <button
            onClick={() => setSelectedEmail(null)}
            className="text-gray-600 hover:text-gray-900 mb-4 transition-colors"
          >
            ← 返回列表
          </button>

          <div className="border-b border-gray-200 pb-4 mb-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xl font-bold text-gray-900">{selectedEmail.subject}</h3>
              <span className="text-sm text-gray-500">{formatTime(selectedEmail.created_at)}</span>
            </div>
            <div className="flex items-center gap-2 text-gray-700">
              <span className="font-medium">收件人:</span>
              <span className="font-mono text-sm">{selectedEmail.recipient_id?.slice(0, 20)}...</span>
            </div>
          </div>

          <div className="flex items-center gap-4 mb-4 text-sm text-gray-500">
            <div className="flex items-center gap-1">
              <Lock className="w-4 h-4 text-green-500" />
              端到端加密
            </div>
            {selectedEmail.status === 'recalled' && (
              <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded-full text-xs">
                已撤回
              </span>
            )}
          </div>

          <div className="p-4 bg-gray-50 rounded-lg mb-4">
            <p className="text-gray-700 whitespace-pre-wrap">
              {selectedEmail.decrypted_body || '加密内容'}
            </p>
          </div>

          {selectedEmail.status !== 'recalled' && (
            <button
              onClick={handleRecall}
              disabled={recallLoading}
              className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {recallLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  撤回中...
                </>
              ) : (
                <>
                  <Undo className="w-4 h-4" />
                  撤回邮件
                </>
              )}
            </button>
          )}
        </div>
      ) : (
        <>
          {/* 邮件列表 */}
          {loading ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
              <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-gray-500">加载中...</p>
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 divide-y divide-gray-100">
              {emails.length === 0 ? (
                <div className="p-12 text-center text-gray-500">
                  <Send className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                  <p className="text-lg font-medium">暂无已发送邮件</p>
                  <p className="text-sm mt-2">您的邮件将显示在这里</p>
                </div>
              ) : (
                emails.map((email) => (
                  <div
                    key={email.id}
                    onClick={() => setSelectedEmail(email)}
                    className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <div className="flex items-start gap-4">
                      <Send className="w-5 h-5 text-green-500 mt-1" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-gray-900 truncate">
                            收件人: {email.recipient_id?.slice(0, 16)}...
                          </span>
                          <span className="text-sm text-gray-500">
                            {formatTime(email.created_at)}
                          </span>
                        </div>
                        <p className="font-medium text-gray-900 truncate mb-1">{email.subject}</p>
                        <p className="text-sm text-gray-500 truncate">
                          {email.decrypted_body || '加密邮件内容...'}
                        </p>
                        {email.status === 'recalled' && (
                          <span className="inline-block mt-2 px-2 py-0.5 bg-orange-100 text-orange-700 rounded-full text-xs">
                            已撤回
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
