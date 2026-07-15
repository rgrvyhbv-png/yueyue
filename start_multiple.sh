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

for i in $(seq 1 $NUM_INSTANCES); do
    PORT=$((8765 + i - 1))
    LOG_FILE="$BASE_DIR/logs/roiify_$i.log"
    
    echo "启动实例 $i (端口: $PORT)..."
    nohup gunicorn --workers=4 --bind=127.0.0.1:$PORT \
        --timeout=120 --access-logfile="$BASE_DIR/logs/access_$i.log" \
        --error-logfile="$BASE_DIR/logs/error_$i.log" \
        web_server:app > "$LOG_FILE" 2>&1 &
    
    echo "实例 $i PID: $!"
    sleep 2
done

echo "成功启动 $NUM_INSTANCES 个实例"
echo "端口列表: $(seq -s, 8765 $((8765 + NUM_INSTANCES - 1)))"
