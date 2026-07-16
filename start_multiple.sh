#!/bin/bash

BASE_DIR=$(cd "$(dirname "$0")" && pwd)
VENV_DIR="$BASE_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
fi

echo "激活虚拟环境..."
source "$VENV_DIR/bin/activate"

echo "安装依赖..."
pip install -r "$BASE_DIR/requirements.txt" -q

NUM_INSTANCES=${1:-3}

mkdir -p "$BASE_DIR/logs"

echo "停止已有实例..."
pkill -f "python web_server.py"
sleep 2

for i in $(seq 1 $NUM_INSTANCES); do
    PORT=$((8765 + i - 1))
    LOG_FILE="$BASE_DIR/logs/roiify_$PORT.log"
    
    echo "启动实例 $i (端口: $PORT)..."
    nohup python web_server.py --port $PORT > "$LOG_FILE" 2>&1 &
    
    echo "实例 $i PID: $!"
    sleep 1
done

echo ""
echo "成功启动 $NUM_INSTANCES 个实例"
echo "端口列表:"
for i in $(seq 1 $NUM_INSTANCES); do
    PORT=$((8765 + i - 1))
    echo "  - http://178.236.47.224:$PORT"
done
