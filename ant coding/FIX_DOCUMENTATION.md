# 客户端UI命令解析修复说明

## 问题描述

用户在客户端界面中看到的是带编号的命令菜单（如 1-6），但输入数字后系统提示"未知命令"。

例如：
```
可用命令 (main):
----------------------------------------
 1. connect        - 连接到服务器
 2. register       - 注册新用户
 3. login          - 用户登录
 4. exit           - 退出程序
 5. help           - 显示帮助信息
 6. about          - 关于程序
----------------------------------------
> 1
[错误] 未知命令: 1
```

## 问题原因

`client_ui.py` 中的 `_handle_command()` 方法只处理文本命令（如 "connect", "login"），但菜单显示的是编号，导致用户输入的数字无法被正确解析。

## 解决方案

修改了 `_handle_command()` 方法，在处理命令前增加数字输入的解析逻辑：

```python
# 处理数字输入（对应菜单编号）
if command.isdigit():
    cmd_index = int(command) - 1
    current_commands = self.commands.get(self.current_menu, [])
    if 0 <= cmd_index < len(current_commands):
        command = current_commands[cmd_index]  # 将数字映射为命令
    else:
        self._print_error(f"无效的命令编号: {command}")
        return
```

## 修复效果

修复后，用户可以：
1. **输入数字**选择菜单项（如输入 "1" 执行 connect 命令）
2. **直接输入命令名称**（如输入 "connect" 仍然有效）
3. **使用快捷命令**（如 "help", "?", "exit", "q"）

### 示例

```
可用命令 (main):
----------------------------------------
 1. connect        - 连接到服务器
 2. register       - 注册新用户
 3. login          - 用户登录
 4. exit           - 退出程序
 5. help           - 显示帮助信息
 6. about          - 关于程序
----------------------------------------
> 1
[成功] 正在连接服务器...

或者：

> connect
[成功] 正在连接服务器...
```

## 修改文件

- `e:\pyspace\ant-coding-main\ant coding\client\client_ui.py`
  - 修改了 `_handle_command()` 方法（第 236-270 行）

## 测试

创建了测试脚本 `test_client_ui_fix.py` 用于验证修复的有效性。

## 向后兼容

此修复完全向后兼容，不影响原有的文本命令输入方式。
