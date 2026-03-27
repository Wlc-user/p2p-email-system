import { create } from 'zustand';

export const useAuthStore = create((set, get) => ({
  isAuthenticated: false,
  user: null,
  token: null,

  login: (token) => {
    set({ token, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('node_id');
    localStorage.removeItem('username');
    localStorage.removeItem('public_key');
    localStorage.removeItem('private_key');
    set({ isAuthenticated: false, user: null, token: null });
  },

  setAuth: (isAuthenticated) => {
    set({ isAuthenticated });
  },

  setUserInfo: (user) => {
    set({ user });
  },

  // 初始化时检查是否已登录
  checkAuth: () => {
    const token = localStorage.getItem('token');
    const nodeId = localStorage.getItem('node_id');
    const username = localStorage.getItem('username');
    const publicKey = localStorage.getItem('public_key');

    if (token) {
      set({
        isAuthenticated: true,
        token,
        user: {
          nodeId,
          username,
          publicKey
        }
      });
      return true;
    }
    return false;
  }
}));
