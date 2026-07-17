#!/bin/bash

BASE_DIR=$(cd "$(dirname "$0")" && pwd)
PID_DIR="$BASE_DIR/pids"

echo "[STOP] 停止所有实例..."

stopped_count=0
for pid_file in "$PID_DIR"/*.pid; do
    [ -f "$pid_file" ] || continue
    
    pid=$(cat "$pid_file")
    port=$(basename "$pid_file" .pid | sed 's/roiify_//')
    
    if kill -0 $pid 2>/dev/null; then
        kill $pid 2>/dev/null
        sleep 1
        
        if kill -0 $pid 2>/dev/null; then
            kill -9 $pid 2>/dev/null
            echo "[FORCE] 强制停止端口 $port (PID: $pid)"
        else
            echo "[OK] 停止端口 $port (PID: $pid)"
        fi
        stopped_count=$((stopped_count + 1))
    else
        echo "[WARN] 端口 $port 进程已不存在"
    fi
    
    rm -f "$pid_file"
done

pkill -f "python web_server.py" 2>/dev/null
sleep 2

echo ""
echo "[STOP] 已停止 $stopped_count 个实例"
echo "[STOP] 所有实例已停止"