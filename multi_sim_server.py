#!/usr/bin/env python3
"""Roiify Ad Simulator - Multi-Threaded Server"""

import json
import logging
import time
import os
import sys
import threading
import queue
import random as _rnd
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, Response, send_file

from device.fingerprint import DeviceFingerprintGenerator
from web.roiify_web_sdk import RoiifyWebSDK
from ad.webview import WebViewSimulator

from config import config, proxy


logging.basicConfig(level=logging.WARNING)
app_logger = logging.getLogger("multi_sim")
app_logger.setLevel(logging.INFO)

app = Flask(__name__, static_folder='web', static_url_path='')

MAX_WORKERS = 10

class WorkerState:
    def __init__(self, worker_id):
        self.worker_id = worker_id
        self.lock = threading.Lock()
        self.running = False
        self.auto_running = False
        self.stop_requested = False
        self.phase = 0
        self.error = None
        self.logs = []
        self.log_queue = queue.Queue()
        self.current_run = 0
        self.stats = {
            "total_runs": 0,
            "success_runs": 0,
            "click_success": 0,
            "conversion_success": 0,
            "total_revenue": 0.0,
        }
        self.thread = None

    def log(self, msg):
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        with self.lock:
            self.logs.append(line)
            if len(self.logs) > 500:
                self.logs = self.logs[-300:]
        self.log_queue.put(line)
        app_logger.info(f"Worker {self.worker_id}: {msg}")

    def update_stats(self, data):
        with self.lock:
            self.stats["total_runs"] += 1
            if data.get("success"):
                self.stats["success_runs"] += 1
                self.stats["click_success"] += data.get("click_success", 0)
                self.stats["conversion_success"] += data.get("conversion_success", 0)
                self.stats["total_revenue"] += data.get("revenue", 0)

    def get_click_rate(self):
        with self.lock:
            total = self.stats["total_runs"]
            if total > 0:
                return round(self.stats["click_success"] / total * 100, 2)
            return 0

workers = {i: WorkerState(i) for i in range(1, MAX_WORKERS + 1)}

def run_single_worker(worker):
    apply_proxy_config()
    
    worker.log(f"开始模拟运行")
    
    try:
        systems = ["ios", "android", "macos", "linux", "chromeos"]
        system_weights = [30, 30, 15, 15, 10]
        system = _rnd.choices(systems, weights=system_weights, k=1)[0]
        
        if system in ["macos", "linux", "chromeos"]:
            platform = "android"
        else:
            platform = system
        
        device_age = _rnd.randint(30, 730)
        
        target_country = None
        real_ip_info = None
        real_ip = None
        real_isp = None
        
        if proxy.enabled:
            worker.log(f"  代理已启用: {proxy.host}:{proxy.port}")
            try:
                import requests
                proxy_url = f"http://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
                test_r = requests.get("http://httpbin.org/ip", proxies={"http": proxy_url, "https": proxy_url}, timeout=10)
                if test_r.ok:
                    ip_data = test_r.json()
                    real_ip = ip_data.get("origin", "unknown")
                    worker.log(f"  代理IP: {real_ip}")
            except Exception as e:
                worker.log(f"  [警告] 代理连接测试失败: {str(e)[:50]}")
        
        gen = DeviceFingerprintGenerator()
        if platform == "android":
            dev = gen.generate_android()
        else:
            dev = gen.generate_ios()
        
        web_sdk = RoiifyWebSDK(
            device_fingerprint=dev,
            proxy_config=proxy
        )
        
        worker.log(f"  设备: {dev.hardware.brand} {dev.hardware.model}")
        worker.log(f"  UA: {dev.browser.user_agent[:80]}")
        
        conversion_values = {
            "saas_enterprise": 800.0,
            "finance_mortgage": 600.0,
            "finance_investing_stocks": 350.0,
            "finance_crypto_trading": 300.0,
            "finance_insurance_life": 250.0,
            "finance_personal_loans": 200.0,
            "finance_credit_cards_premium": 180.0,
            "finance_debt_consolidation": 150.0,
            "software_subscription": 120.0,
            "ecommerce_high_ticket": 100.0,
            "finance_credit_cards": 50.0,
            "finance_banking": 40.0,
            "ecommerce": 30.0,
            "education": 25.0,
            "software": 20.0,
        }
        
        category_weights = {
            "saas_enterprise": 3.0,
            "finance_mortgage": 2.5,
            "finance_investing_stocks": 2.0,
            "finance_crypto_trading": 1.8,
            "finance_insurance_life": 1.5,
            "finance_personal_loans": 1.2,
            "finance_credit_cards_premium": 1.0,
            "finance_debt_consolidation": 0.8,
            "software_subscription": 0.6,
            "ecommerce_high_ticket": 0.5,
            "finance_credit_cards": 0.3,
            "finance_banking": 0.2,
            "ecommerce": 0.1,
            "education": 0.1,
            "software": 0.1,
        }
        
        categories = list(category_weights.keys())
        weights = [category_weights[c] for c in categories]
        ad_category = _rnd.choices(categories, weights=weights, k=1)[0]
        
        click_success_rate = 0.01
        will_click = _rnd.random() < click_success_rate
        
        worker.log(f"  广告类别: {ad_category} (价值${conversion_values.get(ad_category, 100)})")
        worker.log(f"  预估点击率: {click_success_rate*100:.1f}%")
        
        ad_response = None
        try:
            worker.log(f"  发送广告请求...")
            ad_response = web_sdk.request_ad()
            worker.log(f"  请求成功")
        except Exception as e:
            worker.log(f"  [!] 广告请求失败: {str(e)[:80]}")
        
        if ad_response and ad_response.get("success"):
            worker.log(f"  广告曝光上报...")
            try:
                web_sdk.send_impression()
                worker.log(f"  曝光成功")
            except Exception as e:
                worker.log(f"  [!] 曝光上报失败: {str(e)[:50]}")
            
            if will_click and ad_response.get("clickUrl"):
                worker.log(f"  用户点击广告...")
                try:
                    web_sdk.send_click()
                    worker.log(f"  点击成功")
                except Exception as e:
                    worker.log(f"  [!] 点击上报失败: {str(e)[:50]}")
                
                try:
                    worker.log(f"  加载落地页...")
                    webview = WebViewSimulator(device=dev, proxy_config=proxy)
                    landing_result = webview.simulate_landing_page(ad_response.get("clickUrl", ""))
                    worker.log(f"  落地页: {'成功' if landing_result.get('success') else '失败'}")
                except Exception as e:
                    worker.log(f"  [!] 落地页模拟失败: {str(e)[:50]}")
            
            else:
                worker.log(f"  用户未点击广告")
        
        actual_value = conversion_values.get(ad_category, 100) if will_click else 0
        
        worker.update_stats({
            "success": True,
            "click_success": 1 if will_click else 0,
            "conversion_success": 1 if will_click else 0,
            "revenue": actual_value,
        })
        
        worker.log(f"  完成 | 收益: ${actual_value:.2f}")
        
        return {"success": True, "revenue": actual_value, "clicked": will_click}
    
    except Exception as e:
        import traceback
        worker.log(f"  [!] 运行出错: {str(e)[:100]}")
        worker.update_stats({"success": False})
        return {"success": False, "error": str(e)[:100]}

def worker_loop(worker):
    while worker.auto_running:
        with worker.lock:
            worker.current_run += 1
            worker.stop_requested = False
        
        worker.log(f"\n═══════════════════════════")
        worker.log(f"  第 {worker.current_run} 次循环开始")
        worker.log(f"═══════════════════════════")
        
        run_single_worker(worker)
        
        wait_secs = _rnd.uniform(5, 15)
        for _ in range(int(wait_secs * 10)):
            if worker.stop_requested or not worker.auto_running:
                break
            time.sleep(0.1)
    
    with worker.lock:
        worker.auto_running = False
        worker.running = False
    worker.log("自动化循环已停止")

def apply_proxy_config():
    pc = config.get("proxy", {})
    proxy.enabled = pc.get("enabled", False)
    proxy_protocol = pc.get("proxy_type", "http").lower()
    proxy.country = pc.get("country", "")
    proxy.api_key = pc.get("api_key", "")
    proxy.proxy_type = proxy_protocol
    
    proxy.host = ""
    proxy.port = 0
    proxy.username = ""
    proxy.password = ""
    proxy.provider = "proxy001"
    
    if proxy.api_key:
        proxy.fetch_and_update_from_api()

@app.route('/')
def index():
    return send_file('web/dashboard.html')

@app.route('/control.html')
def control():
    return send_file('web/multi_control.html')

@app.route('/api/workers')
def api_workers():
    result = []
    for wid, w in workers.items():
        with w.lock:
            result.append({
                "id": wid,
                "running": w.running,
                "auto_running": w.auto_running,
                "current_run": w.current_run,
                "stats": w.stats,
                "click_rate": w.get_click_rate(),
            })
    return jsonify({"workers": result})

@app.route('/api/worker/<int:wid>/single', methods=['POST'])
def api_worker_single(wid):
    worker = workers.get(wid)
    if not worker:
        return jsonify({"error": "Invalid worker ID"}), 400
    
    with worker.lock:
        if worker.running:
            return jsonify({"error": "Worker is already running"}), 400
        worker.running = True
    
    try:
        result = run_single_worker(worker)
        with worker.lock:
            worker.running = False
        return jsonify({"success": True, "result": result})
    except Exception as e:
        with worker.lock:
            worker.running = False
        return jsonify({"error": str(e)}), 500

@app.route('/api/worker/<int:wid>/auto-start', methods=['POST'])
def api_worker_auto_start(wid):
    worker = workers.get(wid)
    if not worker:
        return jsonify({"error": "Invalid worker ID"}), 400
    
    with worker.lock:
        if worker.auto_running:
            return jsonify({"error": "Worker is already auto-running"}), 400
        worker.auto_running = True
        worker.running = True
    
    worker.thread = threading.Thread(target=worker_loop, args=(worker,), daemon=True)
    worker.thread.start()
    
    return jsonify({"success": True, "worker_id": wid})

@app.route('/api/worker/<int:wid>/stop', methods=['POST'])
def api_worker_stop(wid):
    worker = workers.get(wid)
    if not worker:
        return jsonify({"error": "Invalid worker ID"}), 400
    
    with worker.lock:
        worker.stop_requested = True
        worker.auto_running = False
    
    return jsonify({"success": True, "worker_id": wid})

@app.route('/api/worker/<int:wid>/logs')
def api_worker_logs(wid):
    worker = workers.get(wid)
    if not worker:
        return jsonify({"error": "Invalid worker ID"}), 400
    
    with worker.lock:
        return jsonify({"logs": worker.logs[-100:]})

@app.route('/api/all/auto-start', methods=['POST'])
def api_all_auto_start():
    count = 0
    for wid, worker in workers.items():
        with worker.lock:
            if not worker.auto_running:
                worker.auto_running = True
                worker.running = True
                t = threading.Thread(target=worker_loop, args=(worker,), daemon=True)
                t.start()
                worker.thread = t
                count += 1
            time.sleep(0.3)
    
    return jsonify({"success": True, "started": count})

@app.route('/api/all/stop', methods=['POST'])
def api_all_stop():
    for wid, worker in workers.items():
        with worker.lock:
            worker.stop_requested = True
            worker.auto_running = False
        time.sleep(0.1)
    
    return jsonify({"success": True, "stopped": len(workers)})

@app.route('/api/stats')
def api_stats():
    total_runs = 0
    success_runs = 0
    total_revenue = 0.0
    
    for w in workers.values():
        with w.lock:
            total_runs += w.stats["total_runs"]
            success_runs += w.stats["success_runs"]
            total_revenue += w.stats["total_revenue"]
    
    return jsonify({
        "total_runs": total_runs,
        "success_runs": success_runs,
        "total_revenue": round(total_revenue, 2),
    })

@app.route('/api/state')
def api_state():
    return jsonify({"running": any(w.running for w in workers.values())})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765, help='Port to listen on')
    args = parser.parse_args()
    
    port = args.port
    print(f"\n  Roiify Multi-Threaded Simulator")
    print(f"  http://localhost:{port}")
    print(f"  Workers: {MAX_WORKERS}")
    print(f"\n  控制面板: http://localhost:{port}/control.html\n")
    
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

if __name__ == "__main__":
    main()