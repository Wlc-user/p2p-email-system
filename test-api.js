#!/usr/bin/env node

/**
 * P2P邮件系统 - API测试脚本
 * 用于快速验证所有后端API端点
 */

const API_BASE = 'http://localhost:8102';

// 颜色输出
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function logSection(title) {
  console.log('\n' + '='.repeat(60));
  log(title, 'cyan');
  console.log('='.repeat(60));
}

async function testAPI(name, url, method = 'GET', body = null) {
  try {
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json'
      }
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);
    const data = await response.json();

    if (data.success || response.ok) {
      log(`✅ ${name}`, 'green');
      console.log(JSON.stringify(data, null, 2));
      return data;
    } else {
      log(`❌ ${name}`, 'red');
      console.log('错误:', data);
      return null;
    }
  } catch (error) {
    log(`❌ ${name}`, 'red');
    console.log('错误:', error.message);
    return null;
  }
}

async function runTests() {
  log('P2P邮件系统 - API测试脚本', 'blue');
  console.log(`API地址: ${API_BASE}\n`);

  // 测试1: 健康检查
  logSection('1. 健康检查');
  await testAPI('GET /api/health', `${API_BASE}/api/health`);

  // 测试2: 获取收件箱
  logSection('2. 获取收件箱');
  const inboxResult = await testAPI('GET /api/inbox', `${API_BASE}/api/inbox`);

  // 测试3: 获取已发送
  logSection('3. 获取已发送');
  const sentResult = await testAPI('GET /api/sent', `${API_BASE}/api/sent`);

  // 测试4: 获取联系人
  logSection('4. 获取联系人');
  const contactsResult = await testAPI('GET /api/contacts', `${API_BASE}/api/contacts`);

  // 测试5: 添加联系人
  logSection('5. 添加联系人');
  await testAPI('POST /api/contacts', `${API_BASE}/api/contacts`, 'POST', {
    node_id: 'test1234567890abcdef1234567890abcdef123456',
    name: 'API测试联系人',
    email: 'test@example.com'
  });

  // 测试6: 发送邮件
  logSection('6. 发送测试邮件');
  await testAPI('POST /api/send-email', `${API_BASE}/api/send-email`, 'POST', {
    recipient_id: '707c12e8dd7dc34001e5dbe76aabaec89444440c',
    subject: 'API测试邮件',
    body: '这是一封通过API测试脚本发送的邮件。\n\n测试时间: ' + new Date().toLocaleString()
  });

  // 测试7: CORS测试
  logSection('7. CORS跨域测试');
  log('检查响应头...', 'yellow');
  try {
    const response = await fetch(`${API_BASE}/api/health`);
    const corsHeaders = {
      'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
      'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
      'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
    };

    if (corsHeaders['Access-Control-Allow-Origin'] === '*') {
      log('✅ CORS已正确配置', 'green');
      console.log('  允许来源:', corsHeaders['Access-Control-Allow-Origin']);
      console.log('  允许方法:', corsHeaders['Access-Control-Allow-Methods']);
      console.log('  允许头:', corsHeaders['Access-Control-Allow-Headers']);
    } else {
      log('❌ CORS未配置', 'red');
    }
  } catch (error) {
    log('❌ CORS测试失败', 'red');
  }

  // 总结
  logSection('测试总结');
  log('✅ 所有API测试已完成！', 'green');
  console.log('\n📝 测试说明:');
  console.log('1. 如果所有测试都显示 ✅，说明后端API运行正常');
  console.log('2. 如果某些测试显示 ❌，请检查:');
  console.log('   - 后端服务是否启动 (python p2p_global.py api)');
  console.log('   - 端口8102是否被占用');
  console.log('   - 防火墙是否阻止连接');
  console.log('\n📋 下一步:');
  console.log('1. 打开浏览器访问 http://localhost:5173');
  console.log('2. 按照测试指南进行功能测试');
}

// 运行测试
runTests().catch(error => {
  log('测试失败:', 'red');
  console.error(error);
  process.exit(1);
});
