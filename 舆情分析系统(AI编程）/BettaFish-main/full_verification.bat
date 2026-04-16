@echo off
chcp 65001 >nul
echo.
echo ============================================================
echo BettaFish Bug 修复 - 完整验证清单
echo ============================================================
echo.
echo 本脚本将引导你完成所有验证步骤
echo 预计耗时: 15-20 分钟
echo.
pause

REM 切换到项目目录
cd /d "%~dp0"

echo.
echo ============================================================
echo [步骤 1/6] 环境检查
echo ============================================================
echo.

REM 检查 Python
echo [1.1] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 未安装或未添加到 PATH
    echo 请先安装 Python 3.8+ 并添加到系统 PATH
    pause
    exit /b 1
)
python --version
echo ✅ Python 环境正常
echo.

REM 检查 Docker
echo [1.2] 检查 Docker 环境...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker 未安装或未运行
    echo 请先安装并启动 Docker Desktop
    pause
    exit /b 1
)
docker --version
echo ✅ Docker 环境正常
echo.

REM 检查数据库容器
echo [1.3] 检查数据库容器...
docker ps | findstr "bettafish-db" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  数据库容器未运行，尝试启动...
    docker start bettafish-db >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ 数据库容器启动失败
        echo 请手动执行: docker start bettafish-db
        pause
        exit /b 1
    )
    timeout /t 3 /nobreak >nul
    echo ✅ 数据库容器已启动
) else (
    echo ✅ 数据库容器正在运行
)
echo.

echo ✅ 环境检查完成
pause

echo.
echo ============================================================
echo [步骤 2/6] 代码验证
echo ============================================================
echo.

echo [2.1] 运行自动化验证脚本...
echo.
python test_bugfix.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ 代码验证失败，请检查修复是否正确应用
    pause
    exit /b 1
)

echo.
echo ✅ 代码验证完成
pause

echo.
echo ============================================================
echo [步骤 3/6] 启动后端服务
echo ============================================================
echo.

echo [3.1] 准备启动后端...
echo.
echo 提示: 后端将在新窗口中启动
echo 请保持该窗口打开，不要关闭
echo.
pause

start "BettaFish Backend" cmd /k "python app.py"

echo [3.2] 等待后端启动...
timeout /t 5 /nobreak >nul

echo.
echo [3.3] 检查后端是否启动成功...
curl -s http://localhost:8080 >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  后端可能未完全启动，请检查后端窗口
    echo 如果看到 "Running on http://0.0.0.0:8080" 则表示启动成功
    echo.
    pause
) else (
    echo ✅ 后端启动成功
)

echo.
echo ✅ 后端服务已启动
pause

echo.
echo ============================================================
echo [步骤 4/6] 打开浏览器
echo ============================================================
echo.

echo [4.1] 打开浏览器访问系统...
start http://localhost:8080

echo.
echo [4.2] 打开测试指南...
start QUICK_TEST_GUIDE.md

echo.
echo ✅ 浏览器已打开
pause

echo.
echo ============================================================
echo [步骤 5/6] 功能测试
echo ============================================================
echo.

echo 请按照以下步骤进行功能测试:
echo.
echo ┌─────────────────────────────────────────────────────────┐
echo │ 测试 1: 新搜索流程 (5 分钟)                              │
echo ├─────────────────────────────────────────────────────────┤
echo │ 1. 在搜索框输入关键词 (如 "人工智能")                    │
echo │ 2. 点击【开始分析】                                      │
echo │ 3. 按 F12 打开开发者工具 → Network 标签                  │
echo │ 4. 等待报告生成完成                                      │
echo │                                                           │
echo │ 验证点:                                                   │
echo │ ✓ Network 请求使用短 hash (如 056d9ca5)                  │
echo │ ✓ 返回 200 状态码 (不是 404)                             │
echo │ ✓ Agent 节点完全消失                                     │
echo │ ✓ 控制台完全消失                                         │
echo │ ✓ 全息进度条平滑移除                                     │
echo │ ✓ 报告内容清晰可见                                       │
echo └─────────────────────────────────────────────────────────┘
echo.
pause

echo.
echo ┌─────────────────────────────────────────────────────────┐
echo │ 测试 2: 历史报告查看 (3 分钟)                            │
echo ├─────────────────────────────────────────────────────────┤
echo │ 1. 点击页面右上角的【历史报告】按钮                      │
echo │ 2. 在弹出的抽屉中选择任意一条历史记录                    │
echo │ 3. 按 F12 → Console 标签查看是否有错误                   │
echo │                                                           │
echo │ 验证点:                                                   │
echo │ ✓ 无 "_holoPolling is not defined" 错误                  │
echo │ ✓ 无其他 JavaScript 错误                                 │
echo │ ✓ 报告正常加载                                           │
echo │ ✓ UI 干净无残留                                          │
echo └─────────────────────────────────────────────────────────┘
echo.
pause

echo.
echo ┌─────────────────────────────────────────────────────────┐
echo │ 测试 3: 边界情况 (5 分钟)                                │
echo ├─────────────────────────────────────────────────────────┤
echo │ 1. 快速点击 3 个不同的历史报告 (间隔 < 1 秒)             │
echo │ 2. 在报告加载过程中按 F5 刷新页面                        │
echo │ 3. 打开 Network 标签，勾选 Offline，点击历史报告         │
echo │                                                           │
echo │ 验证点:                                                   │
echo │ ✓ 快速切换无 UI 残留                                     │
echo │ ✓ 刷新后页面正常                                         │
echo │ ✓ 网络错误有友好提示                                     │
echo └─────────────────────────────────────────────────────────┘
echo.
pause

echo.
echo ============================================================
echo [步骤 6/6] 测试结果记录
echo ============================================================
echo.

echo 请回答以下问题:
echo.

set /p test1="测试 1 (新搜索流程) 是否通过? (Y/N): "
set /p test2="测试 2 (历史报告查看) 是否通过? (Y/N): "
set /p test3="测试 3 (边界情况) 是否通过? (Y/N): "

echo.
echo ============================================================
echo 测试结果汇总
echo ============================================================
echo.

echo 测试 1 (新搜索流程): %test1%
echo 测试 2 (历史报告查看): %test2%
echo 测试 3 (边界情况): %test3%
echo.

if /i "%test1%"=="Y" if /i "%test2%"=="Y" if /i "%test3%"=="Y" (
    echo ============================================================
    echo 🎉 恭喜！所有测试通过！
    echo ============================================================
    echo.
    echo 修复验证完成，系统可以正常使用。
    echo.
    echo 下一步:
    echo 1. 填写 TEST_REPORT_TEMPLATE.md 记录详细测试结果
    echo 2. 如果需要，可以将修复部署到生产环境
    echo 3. 继续监控系统运行状态
    echo.
) else (
    echo ============================================================
    echo ⚠️  部分测试未通过
    echo ============================================================
    echo.
    echo 请提供以下信息以便进一步排查:
    echo 1. 浏览器控制台截图 (F12 → Console)
    echo 2. Network 请求截图 (F12 → Network)
    echo 3. 后端终端日志 (最后 50 行)
    echo 4. 详细的复现步骤
    echo.
    echo 参考文档:
    echo - BUGFIX_REPORT.md (详细修复报告)
    echo - QUICK_TEST_GUIDE.md (完整测试指南)
    echo - QUICK_REFERENCE.md (快速参考卡片)
    echo.
)

echo.
echo ============================================================
echo 验证流程完成
echo ============================================================
echo.
echo 感谢使用 BettaFish 舆情分析系统！
echo.
pause
