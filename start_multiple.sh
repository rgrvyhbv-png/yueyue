#!/bin/bash

BASE_DIR=$(cd "$(dirname "$0")" && pwd)
VENV_DIR="$BASE_DIR/venv"
LOG_DIR="$BASE_DIR/logs"
PID_DIR="$BASE_DIR/pids"
SERVER_IP="178.236.47.224"
PORT=8765

PYTHON_BIN="$VENV_DIR/bin/python3"

if [ ! -d "$VENV_DIR" ]; then
    echo "[INIT] 创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
fi

echo "[INIT] 安装依赖..."
$PYTHON_BIN -m pip install -r "$BASE_DIR/requirements.txt" -q

mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

stop_server() {
    echo "[STOP] 停止服务..."
    pkill -f "python3 multi_sim_server.py" 2>/dev/null
    pkill -f "python3 web_server.py" 2>/dev/null
    sleep 3
    rm -f "$PID_DIR"/*.pid
    echo "[STOP] 服务已停止"
}

start_server() {
    local log_file="$LOG_DIR/multi_sim_$(date +%Y%m%d).log"
    local pid_file="$PID_DIR/multi_sim.pid"
    
    echo "[START] 启动多线程服务器..."
    nohup $PYTHON_BIN multi_sim_server.py --port $PORT >> "$log_file" 2>&1 &
    local pid=$!
    
    echo $pid > "$pid_file"
    
    local waited=0
    local max_wait=20
    local port_ready=0
    
    while [ $waited -lt $max_wait ]; do
        sleep 1
        waited=$((waited + 1))
        
        if kill -0 $pid 2>/dev/null; then
            if netstat -tlnp 2>/dev/null | grep -q ":$PORT "; then
                port_ready=1
                break
            fi
        else
            break
        fi
    done
    
    if [ $port_ready -eq 1 ]; then
        echo "[OK] 服务器启动成功，PID: $pid，端口: $PORT"
        return 0
    elif kill -0 $pid 2>/dev/null; then
        echo "[WARN] 进程运行中但端口未监听"
        echo "[DEBUG] 查看日志: tail -30 $log_file"
        return 0
    else
        echo "[FAIL] 服务器启动失败"
        echo "[DEBUG] 查看日志: tail -30 $log_file"
        rm -f "$pid_file"
        return 1
    fi
}

stop_server
start_server

echo ""
echo "=============================="
echo "启动完成！"
echo "=============================="
echo "模式: 单进程多线程 (10个工作线程)"
echo ""
echo "访问地址:"
echo "  - 主界面: http://${SERVER_IP}:${PORT}"
echo "  - 控制面板: http://${SERVER_IP}:${PORT}/control.html"
echo ""
echo "日志目录: $LOG_DIR"
echo "PID目录: $PID_DIR"