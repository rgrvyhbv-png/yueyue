#!/bin/bash

REPO_URL="https://github.com/rgrvyhbv-png/xiaoxiao.git"
PROJECT_DIR="/opt/roiify"
NUM_INSTANCES=${1:-3}

echo "=================================="
echo " Roiify Ad Simulator 一键部署"
echo "=================================="

echo "[1/6] 更新系统..."
apt update -y && apt upgrade -y

echo "[2/6] 安装依赖..."
apt install -y python3 python3-venv git nginx

echo "[3/6] 克隆代码..."
if [ -d "$PROJECT_DIR" ]; then
    cd "$PROJECT_DIR"
    git pull origin master
else
    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

echo "[4/6] 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt -q

echo "[5/6] 配置Nginx..."
cat > /etc/nginx/sites-available/roiify << EOF
upstream roiify_backend {
$(for i in $(seq 0 $((NUM_INSTANCES - 1))); do
    echo "    server 127.0.0.1:$((8765 + i));"
done)
}

server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://roiify_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
    }
}
EOF

if [ -L /etc/nginx/sites-enabled/roiify ]; then
    rm /etc/nginx/sites-enabled/roiify
fi
ln -s /etc/nginx/sites-available/roiify /etc/nginx/sites-enabled/
systemctl restart nginx

echo "[6/6] 启动服务..."
mkdir -p logs
pkill gunicorn 2>/dev/null
sleep 2

for i in $(seq 0 $((NUM_INSTANCES - 1))); do
    PORT=$((8765 + i))
    nohup gunicorn --workers=4 --bind=127.0.0.1:$PORT \
        --timeout=120 --access-logfile="logs/access_$PORT.log" \
        --error-logfile="logs/error_$PORT.log" \
        web_server:app > "logs/roiify_$PORT.log" 2>&1 &
    echo "  ✓ 实例 $((i+1)) 已启动 (端口: $PORT)"
    sleep 1
done

echo ""
echo "=================================="
echo " 部署完成！"
echo "=================================="
echo ""
echo "访问地址: http://$(curl -s ifconfig.me)"
echo "实例数: $NUM_INSTANCES"
echo "端口范围: 8765-$((8765 + NUM_INSTANCES - 1))"
echo "日志目录: $PROJECT_DIR/logs"
echo ""
echo "重启服务:"
echo "  cd $PROJECT_DIR && ./deploy.sh $NUM_INSTANCES"
echo ""
echo "查看日志:"
echo "  tail -f $PROJECT_DIR/logs/roiify_8765.log"
