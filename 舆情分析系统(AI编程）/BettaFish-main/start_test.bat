@echo off
chcp 65001 >nul
echo ============================================================
echo BettaFish 一键启动测试脚本
echo ============================================================
echo.

REM 检查当前目录
cd /d "%~dp0"
echo [1/5] 当前目录: %CD%
echo.

REM 检查 Python 是否安装
echo [2/5] 检查 Python 环境...
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

REM 检查 Docker 容器
echo [3/5] 检查数据库容器...
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
    echo ✅ 数据库容器已启动
) else (
    echo ✅ 数据库容器正在运行
)
echo.

REM 运行 Bug 修复验证
echo [4/5] 运行 Bug 修复验证...
python test_bugfix.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ Bug 修复验证失败，请检查代码
    pause
    exit /b 1
)
echo.

REM 启动后端
echo [5/5] 启动后端服务...
echo.
echo ============================================================
echo 后端服务启动中...
echo 请在浏览器中访问: http://localhost:8080
echo 按 Ctrl+C 可停止服务
echo ============================================================
echo.

python app.py

pause
