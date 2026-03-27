import { create } from 'zustand';

export const useP2PStore = create((set, get) => ({
  nodeInfo: null,
  contacts: [],
  inbox: [],
  sent: [],
  logs: [],
  status: 'stopped', // 'stopped' | 'starting' | 'running'

  // 初始化默认测试数据
  initData: () => {
    const state = get();
    if (state.contacts.length === 0) {
      state.setContacts([
        { id: 1, name: '测试联系人', node_id: '707c12e8dd7dc34001e5dbe76aabaec89444440c', group: '测试', created_at: new Date().toISOString() },
        { id: 2, name: '张三', node_id: 'abc1234567890def1234567890abcdef12345678', group: '同事', created_at: new Date().toISOString() },
        { id: 3, name: '李四', node_id: 'fedcba0987654321098765432109876543210fed', group: '朋友', created_at: new Date().toISOString() }
      ]);
    }
    if (state.inbox.length === 0) {
      state.setInbox([
        {
          id: 1,
          message_id: 'test-msg-001',
          sender_id: '707c12e8dd7dc34001e5dbe76aabaec89444440c',
          recipient_id: '707c12e8dd7dc34001e5dbe76aabaec89444440c',
          subject: '欢迎使用P2P SecureMail',
          body: '这是一封测试邮件，展示P2P邮件系统的功能。\n\n您可以看到：\n1. 邮件列表\n2. 邮件详情\n3. 回复、转发、删除功能\n\n所有通信都是端到端加密的！',
          direction: 'received',
          timestamp: Date.now() / 1000 - 3600
        },
        {
          id: 2,
          message_id: 'test-msg-002',
          sender_id: 'abc1234567890def1234567890abcdef12345678',
          recipient_id: '707c12e8dd7dc34001e5dbe76aabaec89444440c',
          subject: '项目进度更新',
          body: '嗨！\n\n项目进展顺利，预计下周完成第一阶段的开发。\n\n主要更新：\n- 前端UI已完成\n- 后端API已对接\n- 正在进行测试\n\n祝好！',
          direction: 'received',
          timestamp: Date.now() / 1000 - 7200
        }
      ]);
    }
    if (state.sent.length === 0) {
      state.setSent([
        {
          id: 1,
          message_id: 'test-sent-001',
          sender_id: '707c12e8dd7dc34001e5dbe76aabaec89444440c',
          recipient_id: 'abc1234567890def1234567890abcdef12345678',
          subject: '回复：项目进度更新',
          body: '收到！\n\n很高兴听到项目进展顺利。\n\n期待下周的更新！',
          direction: 'sent',
          timestamp: Date.now() / 1000 - 1800
        }
      ]);
    }
  },

  setNodeInfo: (info) => set({ nodeInfo: info }),
  setContacts: (contacts) => set({ contacts }),
  setInbox: (inbox) => set({ inbox }),
  setSent: (sent) => set({ sent }),
  setStatus: (status) => set({ status }),
  addLog: (log) => set((state) => ({
    logs: [...state.logs.slice(-99), log] // 只保留最后100条日志
  })),
  clearLogs: () => set({ logs: [] })
}));
