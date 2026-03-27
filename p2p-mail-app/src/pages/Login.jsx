import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI, systemAPI } from '../api';
import { LogIn, UserPlus, Lock, AlertCircle, CheckCircle } from 'lucide-react';
import { useAuthStore } from '../store/auth';

export function Login() {
  const navigate = useNavigate();
  const { login: setAuth, setUserInfo } = useAuthStore();
  
  const [isRegister, setIsRegister] = useState(false);
  const [nodeId, setNodeId] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const generateNodeId = () => {
    // 生成40位十六进制字符串
    const array = new Uint8Array(20);
    crypto.getRandomValues(array);
    return Array.from(array, b => b.toString(16).padStart(2, '0')).join('');
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    // 验证输入
    if (!username.trim()) {
      setError('请输入用户名');
      return;
    }

    if (password && password.length < 8) {
      setError('密码长度至少8位');
      return;
    }

    if (password !== confirmPassword) {
      setError('两次密码输入不一致');
      return;
    }

    setLoading(true);

    try {
      const result = await authAPI.register(
        nodeId || generateNodeId(),
        username.trim(),
        password || null,
        confirmPassword || null
      );

      if (result.success) {
        setSuccess('注册成功!请保存您的私钥,系统将自动登录...');

        // 保存私钥到localStorage
        localStorage.setItem('private_key', result.private_key);
        localStorage.setItem('node_id', result.user.node_id);
        localStorage.setItem('username', result.user.username);
        localStorage.setItem('public_key', result.user.public_key);
        localStorage.setItem('token', result.token || '');

        // 更新store
        setUserInfo({
          nodeId: result.user.node_id,
          username: result.user.username,
          publicKey: result.user.public_key
        });
        
        setAuth(true);

        // 延迟跳转到主页
        setTimeout(() => {
          navigate('/');
        }, 2000);
      } else {
        setError(result.error || '注册失败');
      }
    } catch (err) {
      setError('网络错误,请检查服务器连接');
      console.error('注册错误:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!nodeId.trim()) {
      setError('请输入节点ID');
      return;
    }

    setLoading(true);

    try {
      const result = await authAPI.login(nodeId.trim(), password || null);

      if (result.success) {
        setSuccess('登录成功!');

        // 保存到localStorage
        localStorage.setItem('token', result.token);
        localStorage.setItem('node_id', nodeId);
        
        // 尝试从localStorage获取用户信息
        const storedUsername = localStorage.getItem('username');
        const storedPublicKey = localStorage.getItem('public_key');
        const storedPrivateKey = localStorage.getItem('private_key');

        if (storedUsername) {
          setUserInfo({
            nodeId: nodeId,
            username: storedUsername,
            publicKey: storedPublicKey
          });
        }

        setAuth(true);

        // 延迟跳转
        setTimeout(() => {
          navigate('/');
        }, 1000);
      } else {
        setError(result.error || '登录失败');
      }
    } catch (err) {
      setError('网络错误,请检查服务器连接');
      console.error('登录错误:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* 标题卡片 */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          {/* 头部 */}
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-8 py-6">
            <h1 className="text-2xl font-bold text-white mb-2">
              {isRegister ? '创建账户' : '安全邮件系统'}
            </h1>
            <p className="text-blue-100 text-sm">
              {isRegister ? '注册新账户并开始加密通信' : '使用您的节点ID登录系统'}
            </p>
          </div>

          {/* 表单 */}
          <div className="px-8 py-6">
            {/* 错误提示 */}
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <span className="text-sm text-red-600">{error}</span>
              </div>
            )}

            {/* 成功提示 */}
            {success && (
              <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-start gap-2">
                <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                <span className="text-sm text-green-600">{success}</span>
              </div>
            )}

            <form onSubmit={isRegister ? handleRegister : handleLogin} className="space-y-4">
              {/* 节点ID */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  节点ID (Node ID)
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={nodeId}
                    onChange={(e) => setNodeId(e.target.value)}
                    placeholder="40位十六进制字符"
                    className="w-full px-4 py-3 pr-24 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                    readOnly={isRegister}
                  />
                  {!isRegister && (
                    <button
                      type="button"
                      onClick={() => setNodeId(generateNodeId())}
                      className="absolute right-2 top-1/2 -translate-y-1/2 px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded text-gray-600 transition-colors"
                    >
                      生成
                    </button>
                  )}
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  {isRegister ? '将自动生成,或手动输入自定义ID' : '请输入您注册时的节点ID'}
                </p>
              </div>

              {/* 用户名(仅注册时) */}
              {isRegister && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    用户名
                  </label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="您的显示名称"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  />
                </div>
              )}

              {/* 密码(可选) */}
              {(isRegister || password) && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    密码 {isRegister && '(可选,至少8位)'}
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder={isRegister ? '设置密码(可选)' : '输入密码'}
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                    />
                  </div>
                </div>
              )}

              {/* 确认密码(仅注册时) */}
              {isRegister && password && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    确认密码
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="再次输入密码"
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                    />
                  </div>
                </div>
              )}

              {/* 提交按钮 */}
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    处理中...
                  </span>
                ) : isRegister ? (
                  <span className="flex items-center justify-center gap-2">
                    <UserPlus className="w-5 h-5" />
                    注册账户
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <LogIn className="w-5 h-5" />
                    登录
                  </span>
                )}
              </button>
            </form>

            {/* 切换登录/注册 */}
            <div className="mt-6 text-center">
              <button
                onClick={() => {
                  setIsRegister(!isRegister);
                  setError('');
                  setSuccess('');
                }}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
              >
                {isRegister ? '已有账户? 点击登录' : '没有账户? 点击注册'}
              </button>
            </div>

            {/* 安全提示 */}
            <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-xs text-blue-800 leading-relaxed">
                <strong className="font-semibold">安全提示:</strong>{' '}
                您的私钥将在注册时生成,请务必妥善保存。系统使用端到端加密,只有您和收件人才能查看邮件内容。
              </p>
            </div>
          </div>
        </div>

        {/* 页脚 */}
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>Powered by CS架构邮件系统 | 端到端加密</p>
        </div>
      </div>
    </div>
  );
}
