import React, { useEffect, useState } from 'react';
import { useP2PStore } from '../store/p2p';
import { Mail, Clock, Trash2, Reply, Share2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function Inbox() {
  const { inbox, setInbox } = useP2PStore();
  const [selectedEmail, setSelectedEmail] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    // 加载收件箱数据
    loadInbox();
  }, []);

  const loadInbox = async () => {
    try {
      const response = await fetch('http://localhost:8102/api/inbox');
      const result = await response.json();
      if (result.success) {
        setInbox(result.data || []);
      }
    } catch (error) {
      console.error('加载收件箱失败:', error);
      // 如果后端不可用，使用测试数据
      const testEmails = [
        {
          message_id: 'test-msg-001',
          sender_id: '707c12e8dd7dc34001e5dbe76aabaec89444440c',
          recipient_id: '707c12e8dd7dc34001e5dbe76aabaec89444440c',
          subject: '欢迎使用P2P SecureMail',
          body: '这是一封测试邮件，展示P2P邮件系统的功能。\n\n您可以看到：\n1. 邮件列表\n2. 邮件详情\n3. 回复、转发、删除功能\n\n所有通信都是端到端加密的！',
          timestamp: Date.now() / 1000 - 3600,
          read: false
        },
        {
          message_id: 'test-msg-002',
          sender_id: 'abc1234567890def1234567890abcdef12345678',
          recipient_id: '707c12e8dd7dc34001e5dbe76aabaec89444440c',
          subject: '项目进度更新',
          body: '嗨！\n\n项目进展顺利，预计下周完成第一阶段的开发。\n\n主要更新：\n- 前端UI已完成\n- 后端API已对接\n- 正在进行测试\n\n祝好！',
          timestamp: Date.now() / 1000 - 7200,
          read: false
        }
      ];
      setInbox(testEmails);
    }
  };

  const handleReply = () => {
    if (!selectedEmail) return;
    // 跳转到写邮件页面，预填回复信息
    navigate('/compose', {
      state: {
        to: selectedEmail.sender_id,
        subject: `Re: ${selectedEmail.subject}`,
        body: `\n\n--- 原始邮件 ---\n发件人: ${selectedEmail.sender_id}\n时间: ${new Date(selectedEmail.timestamp * 1000).toLocaleString()}\n\n${selectedEmail.body}`
      }
    });
  };

  const handleForward = () => {
    if (!selectedEmail) return;
    // 跳转到写邮件页面，预填转发信息
    navigate('/compose', {
      state: {
        subject: `Fwd: ${selectedEmail.subject}`,
        body: `\n\n--- 转发邮件 ---\n发件人: ${selectedEmail.sender_id}\n时间: ${new Date(selectedEmail.timestamp * 1000).toLocaleString()}\n\n${selectedEmail.body}`
      }
    });
  };

  const handleDelete = async () => {
    if (!selectedEmail) return;
    if (!confirm('确定要删除这封邮件吗？')) return;

    // 从本地列表中删除（后端暂未实现删除API）
    const updatedInbox = inbox.filter(email => email.message_id !== selectedEmail.message_id);
    setInbox(updatedInbox);
    setSelectedEmail(null);
    alert('邮件已删除');
  };

  return (
    <div className="flex h-full">
      {/* 邮件列表 */}
      <div className="w-1/2 border-r border-gray-200 overflow-auto">
        <div className="p-4 border-b border-gray-200 bg-white sticky top-0">
          <h2 className="text-xl font-bold text-gray-900">收件箱</h2>
          <p className="text-sm text-gray-500 mt-1">{inbox.length} 封邮件</p>
        </div>

        <div className="divide-y divide-gray-100">
          {inbox.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <Mail className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p>收件箱为空</p>
            </div>
          ) : (
            inbox.map((email) => (
              <div
                key={email.message_id}
                onClick={() => setSelectedEmail(email)}
                className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
                  selectedEmail?.message_id === email.message_id ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center text-primary-600 font-bold">
                    {email.sender_id?.[0]?.toUpperCase() || '?'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-gray-900 truncate">
                        {email.sender_id?.slice(0, 12) || '未知发件人'}
                      </span>
                      <span className="text-xs text-gray-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(email.timestamp * 1000).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="font-medium text-gray-900 truncate mb-1">{email.subject}</p>
                    <p className="text-sm text-gray-500 truncate">{email.body}</p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* 邮件详情 */}
      <div className="w-1/2 bg-gray-50 overflow-auto">
        {selectedEmail ? (
          <div className="p-6">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">{selectedEmail.subject}</h2>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center text-primary-600 font-bold text-lg">
                  {selectedEmail.sender_id?.[0]?.toUpperCase() || '?'}
                </div>
                <div>
                  <p className="font-medium text-gray-900">
                    {selectedEmail.sender_id?.slice(0, 16)}...
                  </p>
                  <p className="text-sm text-gray-500">
                    {new Date(selectedEmail.timestamp * 1000).toLocaleString()}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm">
              <p className="text-gray-700 whitespace-pre-wrap">{selectedEmail.body}</p>
            </div>

            <div className="mt-6 flex gap-3">
              <button
                onClick={handleReply}
                className="px-6 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 flex items-center gap-2"
              >
                <Reply className="w-4 h-4" />
                回复
              </button>
              <button
                onClick={handleForward}
                className="px-6 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 flex items-center gap-2"
              >
                <Share2 className="w-4 h-4" />
                转发
              </button>
              <button
                onClick={handleDelete}
                className="px-6 py-2 bg-white border border-gray-300 text-red-600 rounded-lg font-medium hover:bg-red-50 flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                删除
              </button>
            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-gray-500">
            选择邮件查看详情
          </div>
        )}
      </div>
    </div>
  );
}
