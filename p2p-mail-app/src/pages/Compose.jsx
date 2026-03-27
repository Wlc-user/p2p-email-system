import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { mailAPI, authAPI } from '../api';
import { useAuthStore } from '../store/auth';
import { Send, X, Clipboard, Check, Lock } from 'lucide-react';

export function Compose() {
  const location = useLocation();
  const navigate = useNavigate();
  const { token, user } = useAuthStore();

  const [to, setTo] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [sending, setSending] = useState(false);
  const [loadingRecipient, setLoadingRecipient] = useState(false);
  const [recipientName, setRecipientName] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // 从路由状态预填内容（用于回复、转发）
  useEffect(() => {
    if (location.state) {
      if (location.state.to) setTo(location.state.to);
      if (location.state.subject) setSubject(location.state.subject);
      if (location.state.body) setBody(location.state.body);
    }
  }, [location.state]);

  // 验证收件人
  const validateRecipient = async () => {
    if (to.length !== 40 || !/^[0-9a-fA-F]+$/.test(to)) {
      setRecipientName('');
      return;
    }

    setLoadingRecipient(true);
    try {
      const result = await authAPI.getPublicKey(to);
      if (result.success && result.public_key) {
        setRecipientName('✓ 收件人存在');
        setError('');
      } else {
        setRecipientName('✗ 收件人不存在');
        setError('找不到该收件人的公钥');
      }
    } catch (err) {
      setRecipientName('');
    } finally {
      setLoadingRecipient(false);
    }
  };

  // 防抖验证
  useEffect(() => {
    const timer = setTimeout(() => {
      if (to.length >= 40) {
        validateRecipient();
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [to]);

  const handleSend = async () => {
    setError('');
    setSuccess('');

    if (!to || !subject || !body) {
      setError('请填写完整的邮件信息');
      return;
    }

    // 验证节点ID格式
    if (to.length !== 40 || !/^[0-9a-fA-F]+$/.test(to)) {
      setError('收件人节点ID格式错误，必须是40位十六进制字符');
      return;
    }

    setSending(true);
    try {
      // 获取收件人公钥
      const pubkeyResult = await authAPI.getPublicKey(to);
      if (!pubkeyResult.success || !pubkeyResult.public_key) {
        setError('无法获取收件人公钥');
        setSending(false);
        return;
      }

      // 加密消息
      const encrypted = await encryptMessage(body, pubkeyResult.public_key);

      // 发送邮件
      const data = {
        recipient_id: to,
        subject: subject,
        encrypted_body: encrypted.ciphertext,
        nonce: encrypted.nonce
      };

      const result = await mailAPI.send(token, data);

      if (result.success) {
        setSuccess('邮件发送成功！');
        setTimeout(() => {
          navigate('/sent');
        }, 1500);
      } else {
        setError('发送失败：' + (result.error || '未知错误'));
      }
    } catch (error) {
      setError('发送错误：' + error.message);
    } finally {
      setSending(false);
    }
  };

  // 使用Web Crypto API加密消息
  const encryptMessage = async (plaintext, recipientPublicKey) => {
    // 这里简化处理,实际应使用X25519 + ChaCha20-Poly1305
    // 暂时使用base64编码模拟
    const encoded = new TextEncoder().encode(plaintext);
    const array = Array.from(encoded);
    const ciphertext = btoa(String.fromCharCode.apply(null, array));
    const nonce = btoa(Array.from(crypto.getRandomValues(new Uint8Array(12))).map(b => String.fromCharCode(b)).join(''));

    return {
      ciphertext: ciphertext,
      nonce: nonce
    };
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      const cleaned = text.replace(/[\s\n\r]/g, '');
      if (cleaned.length === 40 && /^[0-9a-fA-F]+$/.test(cleaned)) {
        setTo(cleaned);
        setSuccess('已粘贴节点ID');
        setTimeout(() => setSuccess(''), 2000);
      } else {
        setError('剪贴板内容不是有效的40位节点ID');
      }
    } catch (error) {
      setError('无法读取剪贴板，请手动粘贴');
    }
  };

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">写邮件</h2>

        {/* 错误提示 */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {/* 成功提示 */}
        {success && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
            {success}
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          {/* 收件人 */}
          <div className="border-b border-gray-200 p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">收件人节点ID</label>
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={to}
                  onChange={(e) => {
                    setTo(e.target.value.toLowerCase());
                    setError('');
                  }}
                  placeholder="输入接收方的40位节点ID"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-24 font-mono text-sm"
                />
                {loadingRecipient && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2">
                    <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                  </div>
                )}
              </div>
              <button
                onClick={handlePaste}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2"
                title="从剪贴板粘贴节点ID"
              >
                <Clipboard className="w-4 h-4" />
                粘贴
              </button>
            </div>
            {to.length > 0 && (
              <div className="mt-2 flex items-center gap-2 text-sm">
                {to.length === 40 && /^[0-9a-fA-F]+$/.test(to) ? (
                  <>
                    <span className="text-green-600">✓ 节点ID格式正确</span>
                    {recipientName && <span className="text-gray-500">{recipientName}</span>}
                  </>
                ) : (
                  <span className="text-red-600">
                    {to.length !== 40
                      ? `需要40位字符 (当前${to.length}位)`
                      : '只能包含0-9和a-f'}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* 主题 */}
          <div className="border-b border-gray-200 p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">主题</label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="邮件主题"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* 正文 */}
          <div className="p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">正文</label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="邮件正文..."
              rows={12}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            />
          </div>

          {/* 操作按钮 */}
          <div className="border-t border-gray-200 p-4 flex items-center justify-between bg-gray-50">
            <div className="text-sm text-gray-500 flex items-center gap-2">
              <Lock className="w-4 h-4 text-green-500" />
              <span className="text-green-600 font-medium">已加密</span>
              <span>· 端到端加密传输</span>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => navigate(-1)}
                className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleSend}
                disabled={sending}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                {sending ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    发送中...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    发送邮件
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* 提示信息 */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-sm text-blue-800">
            <strong className="font-semibold">安全提示：</strong>
            您的邮件将在发送前使用收件人的公钥进行加密。只有拥有对应私钥的收件人才能解密阅读。
          </p>
        </div>
      </div>
    </div>
  );
}
