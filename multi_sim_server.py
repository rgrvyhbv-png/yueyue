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

from device.fingerprint import DeviceFingerprintGenerator, fingerprint_scheduler
from web.roiify_web_sdk import RoiifyWebSDK
from ad.webview import WebViewSimulator

from config import config, proxy
from core import RateLimiter, MultiInstanceCircuitManager


logging.basicConfig(level=logging.WARNING)
app_logger = logging.getLogger("multi_sim")
app_logger.setLevel(logging.INFO)

app = Flask(__name__, static_folder='web', static_url_path='')

MAX_WORKERS = 10

# 全局熔断器管理器
circuit_manager = MultiInstanceCircuitManager()

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
        
        # 限流模块
        self.rate_limiter = RateLimiter(
            max_requests_per_minute=config.INSTANCE_MAX_REQUESTS_PER_MINUTE,
            min_interval_ms=config.MIN_REQUEST_INTERVAL_MS,
            burst_size=config.BURST_SIZE,
            instance_id=f"worker_{worker_id}",
        )
        
        # 熔断器
        if config.ENABLE_CIRCUIT_BREAKER:
            circuit_manager.create_breaker(
                instance_id=f"worker_{worker_id}",
                failure_threshold=config.FAILURE_THRESHOLD,
                recovery_timeout=config.RECOVERY_TIMEOUT,
            )

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
        platform = _rnd.choice(["ios", "android"])
        
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
        
        gen = DeviceFingerprintGenerator(platform=platform, device_age_days=device_age, country="US")
        dev = gen.generate()
        
        web_sdk = RoiifyWebSDK(
            user_agent=dev.browser.user_agent,
            accept_language=dev.browser.accept_language,
            timezone=dev.system.timezone,
            locale=dev.system.locale,
            use_proxy=proxy.enabled,
            device_info=dev,
        )
        
        worker.log(f"  设备: {dev.hardware.brand} {dev.hardware.model}")
        worker.log(f"  UA: {dev.browser.user_agent[:80]}")
        
        conversion_values = {
            # 超高价值类别 ($1000+)
            "finance_private_banking": 1500.00,
            "automotive_luxury": 1200.00,
            "real_estate_luxury": 1100.00,
            "finance_hedge_funds": 1000.00,
            "healthcare_medical": 950.00,
            # 高价值类别 ($500-$900)
            "saas_enterprise": 850.00,
            "legal_services": 750.00,
            "finance_mortgage": 650.00,
            "real_estate_investing": 550.00,
            "finance_wealth_management": 520.00,
            # 中等价值类别 ($300-$500)
            "finance_investing_stocks": 450.00,
            "b2b_software": 400.00,
            "finance_insurance_health": 380.00,
            "finance_crypto_trading": 350.00,
            "business_franchise": 340.00,
            "insurance_annuities": 320.00,
            "finance_insurance_life": 300.00,
            # 普通价值类别 ($150-$280)
            "education_professional": 260.00,
            "finance_personal_loans": 220.00,
            "finance_credit_cards_premium": 200.00,
            "travel_luxury": 180.00,
            "ecommerce_luxury": 170.00,
            "finance_debt_consolidation": 160.00,
            "software_subscription": 140.00,
            "ecommerce_high_ticket": 120.00,
        }
        
        category_weights = {
            # 超高价值类别权重
            "finance_private_banking": 5.0,
            "automotive_luxury": 4.8,
            "real_estate_luxury": 4.5,
            "finance_hedge_funds": 4.2,
            "healthcare_medical": 4.0,
            # 高价值类别权重
            "saas_enterprise": 3.8,
            "legal_services": 3.2,
            "finance_mortgage": 3.0,
            "real_estate_investing": 2.8,
            "finance_wealth_management": 2.5,
            # 中等价值类别权重
            "finance_investing_stocks": 2.3,
            "b2b_software": 2.0,
            "finance_insurance_health": 2.0,
            "finance_crypto_trading": 1.8,
            "business_franchise": 1.8,
            "insurance_annuities": 1.6,
            "finance_insurance_life": 1.5,
            # 普通价值类别权重
            "education_professional": 1.2,
            "finance_personal_loans": 1.0,
            "finance_credit_cards_premium": 0.8,
            "travel_luxury": 0.8,
            "ecommerce_luxury": 0.7,
            "finance_debt_consolidation": 0.6,
            "software_subscription": 0.5,
            "ecommerce_high_ticket": 0.4,
        }
        
        categories = list(category_weights.keys())
        weights = [category_weights[c] for c in categories]
        ad_category = _rnd.choices(categories, weights=weights, k=1)[0]
        
        click_success_rate = 0.015
        will_click = _rnd.random() < click_success_rate
        
        worker.log(f"  广告类别: {ad_category} (价值${conversion_values.get(ad_category, 100)})")
        worker.log(f"  预估点击率: {click_success_rate*100:.1f}%")
        
        ad_response = None
        try:
            worker.log(f"  发送广告请求...")
            import random as _rnd
            placement_id = _rnd.choice(config.PLACEMENT_IDS)
            ad_response = web_sdk.request_ad(placement_id=placement_id, ad_format="banner")
            if ad_response:
                worker.log(f"  请求成功")
            else:
                worker.log(f"  [!] 请求返回空结果")
        except Exception as e:
            worker.log(f"  [!] 广告请求失败: {str(e)[:80]}")
        
        if ad_response:
            impression_token = ad_response.get("impressionToken")
            click_url = ad_response.get("clickUrl", "")
            
            worker.log(f"  广告曝光上报...")
            try:
                view_dur = _rnd.uniform(5.0, 12.0)
                web_sdk.send_impression(impression_token=impression_token, view_duration=view_dur)
                worker.log(f"  曝光成功")
            except Exception as e:
                worker.log(f"  [!] 曝光上报失败: {str(e)[:50]}")
            
            if will_click and click_url:
                worker.log(f"  用户点击广告...")
                try:
                    web_sdk.send_click()
                    worker.log(f"  点击成功")
                except Exception as e:
                    worker.log(f"  [!] 点击上报失败: {str(e)[:50]}")
                
                # 流量优化：根据配置的概率决定是否加载落地页
                landing_probability = config.LANDING_PAGE_LOAD_PROBABILITY
                if config.SKIP_UNNECESSARY_REQUESTS and _rnd.random() > landing_probability:
                    worker.log(f"  [流量优化] 跳过落地页加载 (概率 {landing_probability:.0%})")
                else:
                    try:
                        worker.log(f"  加载落地页...")
                        from utils.network import NetworkClient
                        net_client = NetworkClient(device=dev)
                        webview = WebViewSimulator(device=dev, network=net_client)
                        landing_result = webview.load_landing_page(
                            url=ad_response.get("clickUrl", ""),
                            referrer="https://www.roiify.net/",
                            simulate_behavior=True,
                        )
                        worker.log(f"  落地页: {'成功' if landing_result.get('success') else '失败'}")
                        worker.log(f"  停留: {landing_result.get('duration', 0):.1f}s")
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
    worker_id = f"worker_{worker.worker_id}"
    
    while worker.auto_running:
        # 定时检查并刷新设备指纹池
        if fingerprint_scheduler.check_and_refresh():
            status = fingerprint_scheduler.get_status()
            worker.log(f"  [指纹调度] 设备指纹池已刷新 | 使用机型数: {status['used_models_count']} | 动态设备数: {status['dynamic_devices_added']}")
        
        # 熔断器检查
        if config.ENABLE_CIRCUIT_BREAKER:
            if not circuit_manager.can_execute(worker_id):
                worker.log(f"  [熔断] 实例被限流，等待恢复...")
                time.sleep(5)
                continue
        
        # 限流器检查
        if config.ENABLE_ENVIRONMENT_ISOLATION:
            if not worker.rate_limiter.wait_for_token(max_wait=10.0):
                worker.log(f"  [限流] 请求间隔过短，等待令牌...")
                continue
        
        with worker.lock:
            worker.current_run += 1
            worker.stop_requested = False
        
        worker.log(f"\n═══════════════════════════")
        worker.log(f"  第 {worker.current_run} 次循环开始")
        worker.log(f"═══════════════════════════")
        
        result = run_single_worker(worker)
        
        # 根据结果更新熔断器状态
        if config.ENABLE_CIRCUIT_BREAKER:
            if result.get("success"):
                circuit_manager.record_success(worker_id)
                worker.rate_limiter.record_success()
            else:
                circuit_manager.record_failure(worker_id, status_code=0)
                worker.rate_limiter.record_failure()
        
        # 流量优化：减少落地页加载概率
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
    # 从环境变量获取账号密码
    username = os.environ.get("PROXY_USERNAME", "")
    password = os.environ.get("PROXY_PASSWORD", "")

    # 代理主机固定，地区由账号密码中的后缀决定（如 _custom_zone_US）
    proxy.enabled = bool(username and password)
    proxy.host = "us.proxy001.com"
    proxy.port = 7878
    proxy.username = username
    proxy.password = password
    proxy.country = "US"
    proxy.provider = "proxy001"
    proxy.proxy_type = "http"
    proxy.api_key = ""

@app.route('/')
def index():
    return send_file('web/index.html')

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

@app.route('/api/circuit-status')
def api_circuit_status():
    """获取熔断器状态"""
    return jsonify(circuit_manager.get_all_status())

@app.route('/api/rate-status')
def api_rate_status():
    """获取限流状态"""
    result = {}
    for wid, w in workers.items():
        result[f"worker_{wid}"] = w.rate_limiter.get_stats()
    return jsonify(result)

@app.route('/api/traffic')
def api_traffic():
    """获取流量统计"""
    return jsonify({
        "instances": len(workers),
        "total_requests": sum(w.stats["total_runs"] for w in workers.values()),
        "success_runs": sum(w.stats["success_runs"] for w in workers.values()),
        "total_revenue": sum(w.stats["total_revenue"] for w in workers.values()),
    })

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