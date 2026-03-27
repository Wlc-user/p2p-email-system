#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能安全邮箱系统 - Web界面
使用Flask提供Web UI
"""

import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# 模拟数据（实际应该从后端获取）
users_db = {}
mails_db = {}

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        domain = request.form.get('domain', 'example1.com')
        
        # TODO: 连接到真实后端
        if username and password:
            session['user'] = f"{username}@{domain}"
            return redirect(url_for('dashboard'))
        
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        domain = request.form.get('domain', 'example1.com')
        
        # TODO: 连接到真实后端
        if username and email and password:
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    """邮箱仪表板"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user = session['user']
    
    # 模拟收件箱数据（实际应该从后端获取）
    sample_inbox = [
        {
            'id': 1,
            'sender': 'alice@example1.com',
            'subject': '欢迎使用智能安全邮箱系统',
            'time': '2024-03-26 15:30',
            'is_read': False
        },
        {
            'id': 2,
            'sender': 'admin@example2.com',
            'subject': '系统通知',
            'time': '2024-03-26 14:20',
            'is_read': True
        }
    ]
    
    return render_template('dashboard.html', user=user, inbox=sample_inbox)

@app.route('/compose', methods=['GET', 'POST'])
def compose():
    """编写邮件"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        to = request.form.get('to')
        subject = request.form.get('subject')
        body = request.form.get('body')
        
        # TODO: 发送到真实后端
        if to and subject:
            return redirect(url_for('dashboard'))
    
    return render_template('compose.html')

@app.route('/mail/<mail_id>')
def view_mail(mail_id):
    """查看邮件"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # TODO: 从后端获取邮件
    return render_template('view_mail.html', mail_id=mail_id)

@app.route('/api/inbox')
def api_inbox():
    """API: 获取收件箱"""
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    # TODO: 从后端获取真实数据
    return jsonify([])

@app.route('/api/send', methods=['POST'])
def api_send():
    """API: 发送邮件"""
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    # TODO: 发送到真实后端
    return jsonify({'success': True})

if __name__ == '__main__':
    print("""
    ============================================================
              智能安全邮箱系统 - Web界面
    ============================================================

    Web界面启动中...
    
    访问地址:
      • http://localhost:5000
    
    功能:
      • 用户注册/登录
      • 查看收件箱
      • 发送邮件
      • 邮件管理
    
    注意: 当前为演示模式，需要连接到真实后端API
    """)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
