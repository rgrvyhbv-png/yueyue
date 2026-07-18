#!/bin/bash

BASE_DIR=$(cd "$(dirname "$0")" && pwd)
VENV_DIR="$BASE_DIR/venv"
LOG_DIR="$BASE_DIR/logs"
PID_DIR="$BASE_DIR/pids"
SERVER_IP="178.236.47.224"
BASE_PORT=8765

NUM_INSTANCES=${1:-10}

PYTHON_BIN="$VENV_DIR/bin/python3"

if [ ! -d "$VENV_DIR" ]; then
    echo "[INIT] 创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
fi

echo "[INIT] 安装依赖..."
$PYTHON_BIN -m pip install -r "$BASE_DIR/requirements.txt" -q

mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

stop_all() {
    echo "[STOP] 停止所有实例..."
    pkill -f "python3 web_server.py" 2>/dev/null
    sleep 3
    rm -f "$PID_DIR"/*.pid
    echo "[STOP] 所有实例已停止"
}

start_instance() {
    local index=$1
    local port=$((BASE_PORT + index - 1))
    local log_file="$LOG_DIR/roiify_${port}_$(date +%Y%m%d).log"
    local pid_file="$PID_DIR/roiify_${port}.pid"
    
    echo "[START] 启动实例 $index (端口: $port)..."
    nohup $PYTHON_BIN web_server.py --port $port >> "$log_file" 2>&1 &
    local pid=$!
    
    echo $pid > "$pid_file"
    sleep 3
    
    if kill -0 $pid 2>/dev/null; then
        echo "[OK] 实例 $index 启动成功，PID: $pid"
        return 0
    else
        echo "[FAIL] 实例 $index 启动失败"
        echo "[DEBUG] 查看日志: tail -20 $log_file"
        rm -f "$pid_file"
        return 1
    fi
}

stop_all

success_count=0
for i in $(seq 1 $NUM_INSTANCES); do
    start_instance $i
    if [ $? -eq 0 ]; then
        success_count=$((success_count + 1))
    fi
    sleep 2
done

echo ""
echo "=============================="
echo "启动完成！"
echo "=============================="
echo "总实例数: $NUM_INSTANCES"
echo "成功启动: $success_count"
echo "失败: $((NUM_INSTANCES - success_count))"
echo ""
echo "访问地址:"
for i in $(seq 1 $success_count); do
    PORT=$((BASE_PORT + i - 1))
    echo "  - http://${SERVER_IP}:${PORT}"
done
echo "  - 控制面板: http://${SERVER_IP}:${BASE_PORT}/control.html"
echo ""
echo "日志目录: $LOG_DIR"
echo "PID目录: $PID_DIR"