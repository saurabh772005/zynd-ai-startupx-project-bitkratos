from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv
from database_manager import get_profile, init_db, update_profile

load_dotenv()

app = Flask(__name__)

# System Branding
SYSTEM_NAME = "StartupX"

# Agent Configuration
AGENTS = {
    "core": {"port": 5005, "name": "StartupX Core Intelligence", "color": "#00d4ff"},
    "compliance": {"port": 5001, "name": "StartupX Compliance & Strategy", "color": "#00ff9d"},
    "ip_shield": {"port": 5002, "name": "StartupX IP Shield Agent", "color": "#7000ff"},
    "procurement": {"port": 5003, "name": "StartupX Procurement & Negotiation", "color": "#ffaa00"},
    "risk": {"port": 5004, "name": "StartupX Failure Risk Agent", "color": "#ff3c3c"}
}

@app.route('/')
def onboarding():
    return render_template('onboarding.html')

@app.route('/dashboard')
def index():
    return render_template('index.html')

@app.route('/api/onboard', methods=['POST'])
def onboard_user():
    try:
        data = request.json
        # Standardize keys if needed or pass directly
        update_profile("default_user", data)
        return jsonify({"status": "success", "redirect": "/dashboard"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/query', methods=['POST'])
def query_agent():
    data = request.json
    agent_id = data.get('agent_id', 'core')
    content = data.get('content', '')
    
    if agent_id not in AGENTS:
        return jsonify({"error": "Unknown agent"}), 400
        
    port = AGENTS[agent_id]['port']
    url = f"http://localhost:{port}/webhook/sync"
    
    # Pass session_id and file data to maintain memory context and support multimodal
    session_id = data.get('session_id', 'default_session')
    payload = {
        "content": content, 
        "session_id": session_id,
        "metadata": {"file": data.get('file')}
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    import socket
    status = {}
    for aid, info in AGENTS.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex(('127.0.0.1', info['port']))
        status[aid] = "online" if result == 0 else "offline"
        sock.close()
    return jsonify(status)

@app.route('/api/profile', methods=['GET'])
def get_user_profile():
    profile = get_profile("default_user") or {
        "startup_name": "New Venture",
        "founder_name": "New Founder",
        "stage": "Ideation",
        "problem_solved": "Not set",
        "product_service": "Not set",
        "target_market": "Not set",
        "revenue_model": "Not set",
        "funding_status": "Not set",
        "profile_image": None
    }
    return jsonify(profile)

if __name__ == '__main__':
    print("🚀 StartupX Dashboard starting on http://localhost:8081")
    # Using threaded=True to handle multiple parallel requests (UI + status checks)
    app.run(host='0.0.0.0', port=8081, debug=False, threaded=True)
