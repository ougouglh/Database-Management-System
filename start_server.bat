@echo off
REM 内网数据导入导出系统启动脚本 (Windows)

echo ========================================
echo   内网数据导入导出系统
echo ========================================
echo.

REM 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 安装依赖
echo 正在检查依赖...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

REM 创建导出目录
if not exist static\exports mkdir static\exports

REM 启动服务
echo.
echo ========================================
echo 正在启动服务...
echo ========================================
echo.
echo 访问地址: http://localhost:11219
echo 按 Ctrl+C 停止服务
echo.

python app.py
pause
