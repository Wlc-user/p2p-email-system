import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  Inbox,
  Send,
  FileText,
  Users,
  Settings,
  Shield,
  Lock,
  Zap,
  LogOut,
  User
} from 'lucide-react';
import { useAuthStore } from '../store/auth';
import { cn } from '../utils/cn';

export function Layout() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    if (confirm('确定要退出登录吗？')) {
      logout();
      navigate('/login');
    }
  };

  const navItems = [
    { path: '/', label: '仪表盘', icon: Zap },
    { path: '/inbox', label: '收件箱', icon: Inbox },
    { path: '/sent', label: '已发送', icon: Send },
    { path: '/compose', label: '写邮件', icon: FileText },
    { path: '/contacts', label: '联系人', icon: Users },
    { path: '/settings', label: '设置', icon: Settings },
  ];

  return (
    <div className="flex w-full h-full">
      {/* 侧边栏 */}
      <div className="w-64 bg-gradient-to-b from-blue-600 to-indigo-700 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-blue-500/30">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-white font-bold text-lg">安全邮件</h1>
              <p className="text-blue-200 text-xs">端到端加密</p>
            </div>
          </div>
        </div>

        {/* 用户信息 */}
        <div className="px-4 py-3 border-b border-blue-500/30">
          <div className="flex items-center gap-2 text-white">
            <User className="w-4 h-4 text-blue-200" />
            <span className="text-sm font-medium truncate">{user?.username || '未登录'}</span>
          </div>
          <p className="text-xs text-blue-200 mt-1 font-mono truncate">
            {user?.nodeId?.slice(0, 16)}...
          </p>
        </div>

        {/* 导航 */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all',
                  isActive
                    ? 'bg-white text-blue-600 shadow-lg'
                    : 'text-blue-100 hover:bg-blue-500/50'
                )
              }
            >
              <item.icon className="w-5 h-5" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* 底部 */}
        <div className="p-4 border-t border-blue-500/30 space-y-2">
          <div className="flex items-center gap-2 text-blue-200 text-xs">
            <Lock className="w-4 h-4" />
            <span>已加密</span>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-4 py-2 bg-blue-500/30 text-white rounded-lg hover:bg-blue-500/50 transition-colors text-sm"
          >
            <LogOut className="w-4 h-4" />
            退出登录
          </button>
        </div>
      </div>

      {/* 主内容 */}
      <div className="flex-1 overflow-auto">
        <Outlet />
      </div>
    </div>
  );
}
