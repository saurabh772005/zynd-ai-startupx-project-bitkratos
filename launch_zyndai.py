import subprocess
import time
import os
import signal
import sys

# List of scripts to run
agents = [
    "compliance_advisor_agent.py",
    "ip_shield_agent.py",
    "procurement_agent.py",
    "risk_agent.py",
    "zyndai_core.py",
    "dashboard.py"
]

processes = []

def start_agents():
    print("🚀 Starting StartupX Multi-Agent System...")
    for agent_file in agents:
        print(f"Starting {agent_file}...")
        # Open log files for each agent
        log_file = open(f"{agent_file}.log", "w")
        p = subprocess.Popen([sys.executable, agent_file], stdout=log_file, stderr=log_file)
        processes.append((agent_file, p, log_file))
        time.sleep(2) # Wait for port binding
    print("✅ All systems are launching in the background.")
    print("StartupX Dashboard on: http://localhost:8081")

def stop_agents(sig, frame):
    print("\n🛑 Stopping all systems...")
    for name, p, log in processes:
        print(f"Terminating {name}...")
        p.terminate()
        log.close()
    sys.exit(0)

signal.signal(signal.SIGINT, stop_agents)

if __name__ == "__main__":
    start_agents()
    
    # Monitor processes
    try:
        while True:
            for name, p, log in processes:
                if p.poll() is not None:
                    print(f"⚠️ Warning: {name} has stopped unexpectedly. Exit code: {p.returncode}")
            time.sleep(5)
    except KeyboardInterrupt:
        stop_agents(None, None)
