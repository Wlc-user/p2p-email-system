import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useP2PStore } from '../store/p2p';
import { Plus, Trash2, Search, User, Mail, Copy, Check, Edit, X, Upload, QrCode } from 'lucide-react';

export function Contacts() {
  const navigate = useNavigate();
  const { contacts, setContacts } = useP2PStore();
  const [showAdd, setShowAdd] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [search, setSearch] = useState('');
  const [filterGroup, setFilterGroup] = useState('all');
  const [newContact, setNewContact] = useState({ name: '', node_id: '', group: '' });
  const [importText, setImportText] = useState('');
  const [copiedNodeId, setCopiedNodeId] = useState(null);
  const [validationError, setValidationError] = useState('');

  useEffect(() => {
    loadContacts();
  }, []);

  const loadContacts = async () => {
    try {
      const result = await fetch('http://localhost:8102/api/contacts');
      const data = await result.json();
      if (data.success) {
        setContacts(data.data || []);
      }
    } catch (error) {
      console.error('加载联系人失败:', error);
    }
  };

  const validateNodeId = (nodeId) => {
    if (!nodeId) {
      return '请输入节点ID';
    }
    if (nodeId.length !== 40) {
      return '节点ID必须是40位十六进制字符';
    }
    if (!/^[0-9a-fA-F]+$/.test(nodeId)) {
      return '节点ID只能包含0-9和a-f（或A-F）';
    }
    return '';
  };

  const handleNodeIdChange = (value) => {
    setNewContact({ ...newContact, node_id: value });
    const error = validateNodeId(value);
    setValidationError(error);
  };

  const handleAdd = async () => {
    if (!newContact.name || !newContact.node_id) {
      alert('请填写联系人名称和节点ID');
      return;
    }

    const validation = validateNodeId(newContact.node_id);
    if (validation) {
      alert(validation);
      return;
    }

    try {
      const result = await fetch('http://localhost:8102/api/contacts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newContact)
      });
      const data = await result.json();

      if (data.success) {
        await loadContacts();
        setShowAdd(false);
        setNewContact({ name: '', node_id: '', group: '' });
        setValidationError('');
        alert('联系人添加成功！');
      } else {
        alert(data.error || '添加失败');
      }
    } catch (error) {
      alert('添加失败: ' + error.message);
    }
  };

  const handleDelete = (id) => {
    if (confirm('确定要删除这个联系人吗？')) {
      setContacts(contacts.filter(c => c.id !== id));
    }
  };

  const handleSendMessage = (contact) => {
    // 存储要发送的目标节点 ID
    localStorage.setItem('compose-recipient', contact.node_id);
    navigate('/compose');
  };

  const handleCopyNodeId = (nodeId) => {
    navigator.clipboard.writeText(nodeId);
    setCopiedNodeId(nodeId);
    setTimeout(() => setCopiedNodeId(null), 2000);
  };

  const filteredContacts = contacts.filter(c => {
    const matchSearch = c.name.toLowerCase().includes(search.toLowerCase()) ||
                      c.node_id.toLowerCase().includes(search.toLowerCase());
    const matchGroup = filterGroup === 'all' || c.group === filterGroup;
    return matchSearch && matchGroup;
  });

  const groups = ['all', ...new Set(contacts.map(c => c.group || '未分类'))].filter(Boolean);

  const handleImport = () => {
    const lines = importText.trim().split('\n');
    const importedContacts = [];

    for (const line of lines) {
      const parts = line.split(/[,，]/).map(s => s.trim());
      if (parts.length >= 2) {
        const [name, nodeId, group = '导入'] = parts;
        const validation = validateNodeId(nodeId);
        if (!validation) {
          importedContacts.push({ name, node_id: nodeId, group });
        }
      }
    }

    if (importedContacts.length === 0) {
      alert('没有有效的联系人数据。格式：姓名,节点ID,分组');
      return;
    }

    const importContacts = async () => {
      let successCount = 0;
      for (const contact of importedContacts) {
        try {
          const result = await fetch('http://localhost:8102/api/contacts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(contact)
          });
          const data = await result.json();
          if (data.success) successCount++;
        } catch (error) {
          console.error('导入失败:', contact, error);
        }
      }
      await loadContacts();
      setShowImport(false);
      setImportText('');
      alert(`成功导入 ${successCount}/${importedContacts.length} 个联系人`);
    };

    importContacts();
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">联系人 ({contacts.length})</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setShowImport(true)}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 flex items-center gap-2 transition-colors"
            title="批量导入联系人"
          >
            <Upload className="w-4 h-4" />
            导入
          </button>
          <button
            onClick={() => setShowAdd(true)}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 flex items-center gap-2 transition-colors"
          >
            <Plus className="w-4 h-4" />
            添加联系人
          </button>
        </div>
      </div>

      {/* 搜索和筛选 */}
      <div className="mb-6 space-y-3">
        <div className="relative">
          <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索联系人名称或节点ID..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>

        {/* 分组筛选 */}
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setFilterGroup('all')}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              filterGroup === 'all'
                ? 'bg-primary-100 text-primary-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            全部
          </button>
          {groups.filter(g => g !== 'all').map(group => (
            <button
              key={group}
              onClick={() => setFilterGroup(group)}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                filterGroup === group
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {group}
            </button>
          ))}
        </div>
      </div>

      {/* 联系人列表 */}
      <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-100">
        {filteredContacts.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            <User className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p className="text-lg font-medium mb-2">暂无联系人</p>
            <p className="text-sm">点击"添加联系人"或"导入"开始使用</p>
          </div>
        ) : (
          <div className="grid gap-3">
            {filteredContacts.map((contact) => (
              <div
                key={contact.id}
                className="p-4 hover:bg-gray-50 transition-colors rounded-lg border border-transparent hover:border-gray-200"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4 flex-1">
                    <div className="w-14 h-14 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-white font-bold text-xl shadow-sm">
                      {contact.name[0]?.toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-semibold text-gray-900 text-lg">{contact.name}</h4>
                      <div className="flex items-center gap-2 mt-1 flex-wrap">
                        <p
                          onClick={() => handleCopyNodeId(contact.node_id)}
                          className="text-sm text-gray-500 font-mono cursor-pointer hover:text-primary-600 hover:bg-primary-50 px-2 py-0.5 rounded transition-all flex items-center gap-1 group border border-transparent hover:border-gray-200"
                          title="点击复制节点ID"
                        >
                          {contact.node_id?.slice(0, 16)}...
                          {copiedNodeId === contact.node_id ? (
                            <Check className="w-3.5 h-3.5 text-green-500" />
                          ) : (
                            <Copy className="w-3.5 h-3.5 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                          )}
                        </p>
                        {contact.group && (
                          <span className="inline-block px-2 py-0.5 bg-primary-100 text-primary-700 text-xs rounded-full font-medium">
                            {contact.group}
                          </span>
                        )}
                        <span className="text-xs text-gray-400">
                          添加于 {new Date(contact.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleSendMessage(contact)}
                      className="p-2.5 text-primary-600 hover:bg-primary-50 rounded-lg transition-all hover:scale-105"
                      title="发送邮件"
                    >
                      <Mail className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => handleCopyNodeId(contact.node_id)}
                      className="p-2.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-all hover:scale-105"
                      title="复制节点ID"
                    >
                      <Copy className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => handleDelete(contact.id)}
                      className="p-2.5 text-red-600 hover:bg-red-50 rounded-lg transition-all hover:scale-105"
                      title="删除联系人"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 添加联系人弹窗 */}
      {showAdd && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900">添加联系人</h3>
              <button
                onClick={() => setShowAdd(false)}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">名称</label>
                <input
                  type="text"
                  value={newContact.name}
                  onChange={(e) => setNewContact({ ...newContact, name: e.target.value })}
                  placeholder="联系人名称"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  节点ID <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newContact.node_id}
                  onChange={(e) => handleNodeIdChange(e.target.value)}
                  placeholder="40位十六进制节点ID"
                  className={`w-full px-4 py-2 border rounded-lg font-mono text-sm ${
                    validationError ? 'border-red-300 bg-red-50' : 'border-gray-300'
                  }`}
                />
                {validationError && (
                  <p className="text-sm text-red-600 mt-1">{validationError}</p>
                )}
                {!validationError && newContact.node_id && (
                  <p className="text-sm text-green-600 mt-1">
                    ✓ 节点ID格式正确 ({newContact.node_id.length}/40)
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">分组（可选）</label>
                <input
                  type="text"
                  value={newContact.group}
                  onChange={(e) => setNewContact({ ...newContact, group: e.target.value })}
                  placeholder="如：工作、家庭、朋友"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                />
              </div>
            </div>

            <div className="mt-6 flex gap-3">
              <button
                onClick={() => setShowAdd(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={handleAdd}
                className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                添加
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 批量导入弹窗 */}
      {showImport && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-lg max-h-[80vh] overflow-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900">批量导入联系人</h3>
              <button
                onClick={() => setShowImport(false)}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  联系人数据（每行一个，格式：姓名,节点ID,分组）
                </label>
                <textarea
                  value={importText}
                  onChange={(e) => setImportText(e.target.value)}
                  placeholder="张三,707c12e8dd7dc34001e5dbe76aabaec89444440c,同事&#10;李四,fedcba0987654321098765432109876543210fed,朋友"
                  className="w-full h-48 px-4 py-2 border border-gray-300 rounded-lg font-mono text-sm"
                />
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-2">说明：</h4>
                <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
                  <li>每行一个联系人，用逗号分隔</li>
                  <li>格式：姓名,节点ID,分组（分组可选）</li>
                  <li>节点ID必须是40位十六进制字符</li>
                  <li>支持中英文逗号</li>
                </ul>
              </div>
            </div>

            <div className="mt-6 flex gap-3">
              <button
                onClick={() => setShowImport(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={handleImport}
                disabled={!importText.trim()}
                className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                导入
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
