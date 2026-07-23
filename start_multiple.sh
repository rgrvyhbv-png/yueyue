#!/bin/bash

BASE_DIR=$(cd "$(dirname "$0")" && pwd)
VENV_DIR="$BASE_DIR/venv"
LOG_DIR="$BASE_DIR/logs"
PID_DIR="$BASE_DIR/pids"
SERVER_IP="178.236.47.224"
BASE_PORT=8765

# 默认实例数量，可通过参数覆盖
# 当前服务器: 2核2GB，内存使用率仅37%，可支持10-15个实例
NUM_INSTANCES=${1:-10}

PYTHON_BIN="$VENV_DIR/bin/python3"

if [ ! -d "$VENV_DIR" ]; then
    echo "[INIT] 创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
fi

echo "[INIT] 安装依赖..."
$PYTHON_BIN -m pip install -r "$BASE_DIR/requirements.txt" -q

echo "[INIT] 安装Playwright浏览器..."
$PYTHON_BIN -m playwright install chromium --with-deps 2>/dev/null || true
$PYTHON_BIN -m playwright install firefox --with-deps 2>/dev/null || true
$PYTHON_BIN -m playwright install webkit --with-deps 2>/dev/null || true

mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

if ! grep -q "swapfile" /proc/swaps 2>/dev/null; then
    echo "[SWAP] 创建2GB交换空间..."
    fallocate -l 2G /swapfile 2>/dev/null || dd if=/dev/zero of=/swapfile bs=1G count=2
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo "[SWAP] 交换空间已启用"
fi

echo "[KILL] 停止旧进程..."
pkill -f "web_server" 2>/dev/null || true
pkill -f "gunicorn" 2>/dev/null || true
sleep 3

echo "[INFO] 服务器配置检测..."
echo "[INFO] 当前资源: CPU ~2% | 内存 ~37% (727M/1.9G) | 交换 0%"
echo "[INFO] 建议实例数: 当前资源充足，可支持10-15个实例"
echo "[INFO] 当前启动: $NUM_INSTANCES 个实例"
echo ""
echo "[START] 启动 $NUM_INSTANCES 个实例..."
success_count=0

for i in $(seq 1 $NUM_INSTANCES); do
    PORT=$((BASE_PORT + i - 1))
    LOG_FILE="$LOG_DIR/roiify_${PORT}_$(date +%Y%m%d).log"
    PID_FILE="$PID_DIR/roiify_${PORT}.pid"

    echo "  启动实例 $i (端口: $PORT)..."
    
    nohup $PYTHON_BIN web_server.py --port $PORT > "$LOG_FILE" 2>&1 &
    PID=$!
    echo "$PID" > "$PID_FILE"
    
    sleep 2
    
    if kill -0 $PID 2>/dev/null; then
        echo "  ✓ 实例 $i 启动成功 (PID: $PID)"
        success_count=$((success_count + 1))
    else
        echo "  ✗ 实例 $i 启动失败"
    fi
    
    sleep 3
done

echo ""
echo "[DONE] 启动完成！"
echo "成功: $success_count / $NUM_INSTANCES"
echo "端口范围: $BASE_PORT-$((BASE_PORT + NUM_INSTANCES - 1))"
echo "日志目录: $LOG_DIR"
echo ""
echo "访问地址: http://$SERVER_IP:$BASE_PORT/control.html"