import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Inbox } from './pages/Inbox';
import { Sent } from './pages/Sent';
import { Compose } from './pages/Compose';
import { Contacts } from './pages/Contacts';
import { Settings } from './pages/Settings';
import { TestAPI } from './pages/TestAPI';
import { P2PStatus } from './components/P2PStatus';
import { useP2PStore } from './store/p2p';
import { useAuthStore } from './store/auth';
import { systemAPI } from './api';

// 私有路由组件
function PrivateRoute({ children }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

function App() {
  const { status, initData } = useP2PStore();
  const { checkAuth } = useAuthStore();
  const [serverStatus, setServerStatus] = useState('unknown');

  // 初始化认证状态
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // 检查服务器状态
  useEffect(() => {
    const checkServerStatus = async () => {
      try {
        const data = await systemAPI.health();
        if (data.success) {
          setServerStatus('running');
          if (data.node_id) {
            useP2PStore.getState().setStatus('running');
          }
        }
      } catch {
        setServerStatus('offline');
      }
    };

    // 初始化测试数据
    initData();

    checkServerStatus();
    const interval = setInterval(checkServerStatus, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* 顶部状态栏 - 只在登录后显示 */}
      <PrivateRoute>
        <P2PStatus />
      </PrivateRoute>

      {/* 主内容区 */}
      <div className="flex-1 flex overflow-hidden">
        <Routes>
          {/* 登录页 - 公开路由 */}
          <Route path="/login" element={<Login />} />

          {/* 受保护的路由 */}
          <Route element={<PrivateRoute><Layout /></PrivateRoute>}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/inbox" element={<Inbox />} />
            <Route path="/sent" element={<Sent />} />
            <Route path="/compose" element={<Compose />} />
            <Route path="/contacts" element={<Contacts />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/test" element={<TestAPI />} />
          </Route>

          {/* 默认重定向 */}
          <Route path="*" element={<Navigate to={checkAuth() ? '/' : '/login'} replace />} />
        </Routes>
      </div>
    </div>
  );
}

export default App;
