#!/bin/bash

BASE_DIR=$(cd "$(dirname "$0")" && pwd)
LOG_DIR="$BASE_DIR/logs"
PID_DIR="$BASE_DIR/pids"
SERVER_IP="178.236.47.224"
BASE_PORT=8765

echo "=============================="
echo " Roiify Ad Simulator 状态"
echo "=============================="
echo ""

echo "[系统资源]"
echo "CPU 使用率: $(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{printf "%.1f%%", 100 - $1}')"
echo "内存使用: $(free -m | grep Mem | awk '{printf "%d / %d MB (%.1f%%)", $3, $2, $3*100/$2}')"
echo "磁盘使用: $(df -h . | grep /dev | awk '{print $3 "/" $2 " (" $5 ")"}')"
echo ""

echo "[运行实例]"
running_count=0
for pid_file in "$PID_DIR"/*.pid; do
    [ -f "$pid_file" ] || continue
    
    pid=$(cat "$pid_file")
    port=$(basename "$pid_file" .pid | sed 's/roiify_//')
    
    if kill -0 $pid 2>/dev/null; then
        echo "✓ 端口 $port: 运行中 (PID: $pid)"
        running_count=$((running_count + 1))
    else
        echo "✗ 端口 $port: 已停止"
        rm -f "$pid_file"
    fi
done

if [ $running_count -eq 0 ]; then
    echo "  没有运行中的实例"
else
    echo ""
    echo "访问地址:"
    for i in $(seq 1 $running_count); do
        PORT=$((BASE_PORT + i - 1))
        echo "  - http://${SERVER_IP}:${PORT}"
    done
fi

echo ""
echo "[最近日志]"
echo "---"
for log_file in $(ls -t "$LOG_DIR"/*.log 2>/dev/null | head -3); do
    echo "文件: $(basename "$log_file")"
    tail -5 "$log_file" 2>/dev/null
    echo "---"
done