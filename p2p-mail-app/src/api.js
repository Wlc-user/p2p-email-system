/**
 * API适配层
 * 对接双服务器CS架构邮件系统
 */

const isElectron = () => typeof window !== 'undefined' && window.electronAPI;

// 服务器配置
const SERVER_A_URL = 'http://localhost:5001';
const SERVER_B_URL = 'http://localhost:5002';
const ACTIVE_SERVER = SERVER_A_URL; // 默认使用服务器A

// 用户认证API
export const authAPI = {
  register: async (nodeId, username, password, confirmPassword) => {
    const data = {
      node_id: nodeId,
      username: username
    };

    if (password) {
      data.password = password;
      data.confirm_password = confirmPassword;
    }

    const response = await fetch(`${ACTIVE_SERVER}/api/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    return await response.json();
  },

  login: async (nodeId, password) => {
    const data = { node_id: nodeId };

    if (password) {
      data.password = password;
    }

    const response = await fetch(`${ACTIVE_SERVER}/api/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    return await response.json();
  },

  getPublicKey: async (nodeId) => {
    const response = await fetch(`${ACTIVE_SERVER}/api/publickey/${nodeId}`);
    return await response.json();
  }
};

// 邮件API
export const mailAPI = {
  inbox: async (token) => {
    const response = await fetch(`${ACTIVE_SERVER}/api/emails/inbox`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return await response.json();
  },

  sent: async (token) => {
    const response = await fetch(`${ACTIVE_SERVER}/api/emails/sent`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return await response.json();
  },

  send: async (token, data) => {
    const response = await fetch(`${ACTIVE_SERVER}/api/emails/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data)
    });
    return await response.json();
  },

  recall: async (token, emailId) => {
    const response = await fetch(`${ACTIVE_SERVER}/api/emails/recall/${emailId}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return await response.json();
  }
};

// 系统健康检查API
export const systemAPI = {
  health: async () => {
    const response = await fetch(`${ACTIVE_SERVER}/api/health`);
    return await response.json();
  },

  getServerInfo: async () => {
    const response = await fetch(`${ACTIVE_SERVER}/api/server-info`);
    return await response.json();
  }
};

// 联系人API (基于邮件系统扩展)
export const contactAPI = {
  list: async (token) => {
    // 从已发送邮件中提取联系人
    const sent = await mailAPI.sent(token);
    if (sent.success && sent.emails) {
      const recipients = sent.emails.map(email => ({
        node_id: email.recipient_id,
        username: email.recipient_username || 'Unknown',
        last_contact: email.created_at
      }));
      // 去重
      return { success: true, contacts: [...new Map(recipients.map(r => [r.node_id, r])).values()] };
    }
    return { success: true, contacts: [] };
  },

  add: async (token, contact) => {
    // 客户端存储联系人(使用localStorage)
    const contacts = JSON.parse(localStorage.getItem('contacts') || '[]');
    contacts.push(contact);
    localStorage.setItem('contacts', JSON.stringify(contacts));
    return { success: true, message: '联系人已添加' };
  }
};
