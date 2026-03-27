import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, AlertCircle, Loader2 } from 'lucide-react';

export function TestAPI() {
  const [tests, setTests] = useState([]);
  const [running, setRunning] = useState(false);

  const runTest = async (name, testFn) => {
    const testId = Date.now();
    setTests(prev => [...prev, { id: testId, name, status: 'running' }]);

    try {
      await testFn();
      setTests(prev => prev.map(t =>
        t.id === testId ? { ...t, status: 'success', message: '通过' } : t
      ));
    } catch (error) {
      setTests(prev => prev.map(t =>
        t.id === testId ? { ...t, status: 'error', message: error.message } : t
      ));
    }
  };

  const runAllTests = async () => {
    setRunning(true);

    await runTest('连接API服务器', async () => {
      const response = await fetch('http://localhost:8102/api/health');
      if (!response.ok) throw new Error('服务器未响应');
    });

    await runTest('获取节点信息', async () => {
      const response = await fetch('http://localhost:8102/api/node');
      const data = await response.json();
      if (!data.success) throw new Error('获取失败');
    });

    await runTest('获取收件箱', async () => {
      const response = await fetch('http://localhost:8102/api/inbox');
      const data = await response.json();
      if (!data.success) throw new Error('获取失败');
    });

    await runTest('获取已发送', async () => {
      const response = await fetch('http://localhost:8102/api/sent');
      const data = await response.json();
      if (!data.success) throw new Error('获取失败');
    });

    await runTest('获取联系人列表', async () => {
      const response = await fetch('http://localhost:8102/api/contacts');
      const data = await response.json();
      if (!data.success) throw new Error('获取失败');
    });

    await runTest('添加测试联系人', async () => {
      const response = await fetch('http://localhost:8102/api/contacts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: '测试联系人',
          node_id: '0' * 40,
          group: '测试'
        })
      });
      const data = await response.json();
      if (!data.success) throw new Error('添加失败');
    });

    setRunning(false);
  };

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">API测试</h1>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">API连接测试</h2>
              <p className="text-sm text-gray-500 mt-1">测试前后端通信是否正常</p>
            </div>
            <button
              onClick={runAllTests}
              disabled={running}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {running ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  测试中...
                </>
              ) : (
                <>
                  <CheckCircle className="w-5 h-5" />
                  运行所有测试
                </>
              )}
            </button>
          </div>
        </div>

        <div className="space-y-3">
          {tests.map((test) => (
            <div key={test.id} className="bg-white rounded-lg border border-gray-200 p-4 flex items-center gap-4">
              {test.status === 'running' && (
                <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
              )}
              {test.status === 'success' && (
                <CheckCircle className="w-6 h-6 text-green-500" />
              )}
              {test.status === 'error' && (
                <XCircle className="w-6 h-6 text-red-500" />
              )}

              <div className="flex-1">
                <h3 className="font-medium text-gray-900">{test.name}</h3>
                <p className="text-sm text-gray-500 mt-1">
                  {test.status === 'running' && '正在测试...'}
                  {test.status === 'success' && test.message}
                  {test.status === 'error' && test.message}
                </p>
              </div>

              {test.status === 'success' && (
                <span className="px-3 py-1 bg-green-100 text-green-700 text-sm font-medium rounded-full">
                  通过
                </span>
              )}
              {test.status === 'error' && (
                <span className="px-3 py-1 bg-red-100 text-red-700 text-sm font-medium rounded-full">
                  失败
                </span>
              )}
              {test.status === 'running' && (
                <span className="px-3 py-1 bg-blue-100 text-blue-700 text-sm font-medium rounded-full">
                  测试中
                </span>
              )}
            </div>
          ))}

          {tests.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <AlertCircle className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p>点击"运行所有测试"开始测试</p>
            </div>
          )}
        </div>

        {tests.length > 0 && tests.every(t => t.status === 'success') && (
          <div className="mt-6 bg-green-50 border border-green-200 rounded-xl p-6">
            <div className="flex items-center gap-3">
              <CheckCircle className="w-8 h-8 text-green-600" />
              <div>
                <h3 className="text-lg font-semibold text-green-900">所有测试通过！</h3>
                <p className="text-sm text-green-800 mt-1">
                  前后端通信正常，可以开始使用应用。
                </p>
              </div>
            </div>
          </div>
        )}

        {tests.some(t => t.status === 'error') && (
          <div className="mt-6 bg-red-50 border border-red-200 rounded-xl p-6">
            <div className="flex items-center gap-3">
              <XCircle className="w-8 h-8 text-red-600" />
              <div>
                <h3 className="text-lg font-semibold text-red-900">部分测试失败</h3>
                <p className="text-sm text-red-800 mt-1">
                  请检查Python API服务器是否正常运行。
                  <br />
                  API服务器应该运行在 http://localhost:8102
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
