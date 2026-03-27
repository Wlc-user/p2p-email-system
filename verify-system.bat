@echo off
chcp 65001 >nul
echo ========================================
echo   P2P邮件系统 - 完整性验证
echo ========================================
echo.

echo [1/3] 验证前端路由...
echo.
echo 正在测试前端页面访问...
powershell -Command "$urls = @('http://localhost:5173/', 'http://localhost:5173/inbox', 'http://localhost:5173/sent', 'http://localhost:5173/compose', 'http://localhost:5173/contacts', 'http://localhost:5173/settings', 'http://localhost:5173/test'); foreach ($url in $urls) { try { $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5; Write-Host \"  ✓ $url\" -ForegroundColor Green } catch { Write-Host \"  ✗ $url (无法访问)\" -ForegroundColor Red } }"
echo.

echo [2/3] 验证API端点...
echo.
echo 正在测试API端点...
powershell -Command "$api = 'http://localhost:8102'; $endpoints = @('GET /', 'GET /api/health', 'GET /api/inbox', 'GET /api/sent', 'GET /api/contacts', 'GET /api/node', 'POST /api/start', 'POST /api/stop', 'POST /api/send-email', 'POST /api/contacts'); foreach ($ep in $endpoints) { $method, $path = $ep.Split(' '); try { if ($method -eq 'POST') { $body = '{}'; $response = Invoke-WebRequest -Uri \"$api$path\" -Method POST -Body $body -ContentType 'application/json' -UseBasicParsing -TimeoutSec 5 } else { $response = Invoke-WebRequest -Uri \"$api$path\" -UseBasicParsing -TimeoutSec 5 }; Write-Host \"  ✓ $method $path\" -ForegroundColor Green } catch { Write-Host \"  ✗ $method $path (无法连接)\" -ForegroundColor Red } }"
echo.

echo [3/3] 验证CORS配置...
echo.
echo 正在测试CORS跨域请求...
powershell -Command "$headers = @{'Origin'='http://localhost:5173'; 'Access-Control-Request-Method'='GET'}; try { $response = Invoke-WebRequest -Uri 'http://localhost:8102/api/health' -Method OPTIONS -Headers $headers -UseBasicParsing -TimeoutSec 5; $cors = $response.Headers['Access-Control-Allow-Origin']; if ($cors -eq '*') { Write-Host \"  ✓ CORS已正确配置 (Access-Control-Allow-Origin: *)\" -ForegroundColor Green } else { Write-Host \"  ✗ CORS配置错误: $cors\" -ForegroundColor Red } } catch { Write-Host \"  ✗ CORS测试失败\" -ForegroundColor Red }"
echo.

echo ========================================
echo   验证完成！
echo ========================================
echo.
echo 提示：
echo   - 所有测试都应该显示 ✓
echo   - 如果有 ✗ 标记，请检查对应的服务
echo   - 前端地址: http://localhost:5173
echo   - 后端API: http://localhost:8102
echo.
pause
