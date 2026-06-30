#!/bin/bash
# 内网数据导入导出系统启动脚本

echo "========================================"
echo "  内网数据导入导出系统"
echo "========================================"
echo ""

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3，请先安装 Python 3.8+"
    exit 1
fi

# 安装依赖
echo "正在检查依赖..."
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 创建导出目录
mkdir -p static/exports

# 启动服务
echo ""
echo "========================================"
echo "正在启动服务..."
echo "========================================"
echo ""
echo "访问地址: http://192.168.239.131:8000"
echo "按 Ctrl+C 停止服务"
echo ""

python3 app.py
