#!/bin/bash

echo "=========================================="
echo "狼人杀游戏 - 9人标准局"
echo "=========================================="
echo ""

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到Python3，请先安装Python 3.8+"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "未找到虚拟环境，正在创建..."
    python3 -m venv venv
    echo "虚拟环境创建成功！"
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
if [ ! -f "venv/.installed" ]; then
    echo "安装依赖..."
    pip install -r requirements.txt
    touch venv/.installed
    echo "依赖安装完成！"
fi

# 运行游戏
echo ""
echo "启动游戏..."
echo ""
python main.py

# 退出虚拟环境
deactivate
