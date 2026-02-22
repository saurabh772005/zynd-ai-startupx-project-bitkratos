import os
import threading
import time
import signal
import sys
import requests
from dotenv import load_dotenv
from zyndai_agent.agent import AgentConfig, ZyndAIAgent
from zyndai_agent.message import AgentMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# --- Setup Environment ---
load_dotenv()

# --- Force Disable x402 (Standardized Monkeypatch) ---
try:
    import x402.http.middleware.flask
    class DummyMiddleware:
        def __init__(self, app, *args, **kwargs):
            self._app = app
            self._original_wsgi = app.wsgi_app
        def __call__(self, environ, start_response):
            return self._original_wsgi(environ, start_response)
    x402.http.middleware.flask.PaymentMiddleware = DummyMiddleware
except ImportError:
    pass

# --- Configuration ---
REGISTRY_URL = "https://registry.zynd.ai"
ZYND_API_KEY = os.environ.get("ZYND_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

if not ZYND_API_KEY or not GOOGLE_API_KEY:
    print("Error: ZYND_API_KEY and GOOGLE_API_KEY must be set in .env")
    sys.exit(1)

# --- Agent Definitions ---

class BaseZyndAgent:
    def __init__(self, name, description, capabilities, port, system_prompt, config_dir):
        self.config = AgentConfig(
            name=name,
            description=description,
            capabilities=capabilities,
            webhook_host="0.0.0.0",
            webhook_port=port,
            registry_url=REGISTRY_URL,
            api_key=ZYND_API_KEY,
            config_dir=config_dir,
            price="$0.01"
        )
        self.agent = ZyndAIAgent(agent_config=self.config)
        self.system_prompt = system_prompt
        self.llm = ChatGoogleGenerativeAI(model="gemini-flash-latest")
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{input}")
        ])
        self.chain = self.prompt_template | self.llm
        self.agent.add_message_handler(self.handle_message)
        print(f"[{name}] Started on port {port}. ID: {self.agent.agent_id}")

    def handle_message(self, message: AgentMessage, topic: str):
        print(f"[{self.config.name}] Processing message: {message.content[:50]}...")
        try:
            response = self.chain.invoke({"input": message.content})
            self.agent.set_response(message.message_id, response.content)
        except Exception as e:
            self.agent.set_response(message.message_id, f"Error: {str(e)}")

# --- Specific Agent Implementations ---

PROMPTS = {
    "compliance": "You are the Compliance & Strategy Agent. Deliver: Market Research, Competitor Analysis, and a Go/No-Go Decision.",
    "ip_shield": "You are the IP Shield Agent. Use your tools to check for IP conflicts and similarity. Deliver: Risk Level and Similarity Score.",
    "procurement": "You are the StartupX Procurement & Negotiation Agent. Deliver: Funding Plan, Legal Checklist, and Investor Readiness Score.",
    "risk": "You are the StartupX Failure Management & Risk Agent. Deliver: Failure Diagnosis and Recovery Strategy.",
    "core": "You are StartupX Core. Your job is to ORCHESTRATE the startup journey. You will coordinate between specialized agents."
}

def start_agent(agent_class, *args):
    agent_class(*args)

if __name__ == "__main__":
    # Create agents in separate threads
    agents_data = [
        ("StartupX Compliance Agent", "Market Research & Strategy", {"service": ["compliance"]}, 5001, PROMPTS["compliance"], ".agent-compliance"),
        ("StartupX IP Shield Agent", "IP & Brand Protection", {"service": ["ip_protection"]}, 5002, PROMPTS["ip_shield"], ".agent-ip"),
        ("StartupX Procurement Agent", "Funding & Legal readiness", {"service": ["procurement"]}, 5003, PROMPTS["procurement"], ".agent-procurement"),
        ("StartupX Risk Agent", "Risk & Recovery analysis", {"service": ["risk_management"]}, 5004, PROMPTS["risk"], ".agent-failure"),
    ]

    # Start specialized agents
    for data in agents_data:
        threading.Thread(target=start_agent, args=(BaseZyndAgent, *data), daemon=True).start()
    
    # Start Orchestrator (Core)
    core_config = AgentConfig(
        name="StartupX Core Orchestrator",
        description="The central intelligence hub for the Startup Intelligence Engine.",
        capabilities={"ai": ["orchestration"]},
        webhook_host="0.0.0.0",
        webhook_port=5005,
        registry_url=REGISTRY_URL,
        api_key=ZYND_API_KEY,
        config_dir=".agent-core"
    )
    core_agent = ZyndAIAgent(agent_config=core_config)
    
    print(f"\n🚀 STARTUPX MULTI-AGENT SYSTEM IS RUNNING")
    print(f"Core Orchestrator Port: 5005")
    print(f"Specialized Agents on Ports: 5001 - 5004")
    
    # Logic for Core to coordinate (Example handler)
    def core_handler(message: AgentMessage, topic: str):
        print(f"[Core] Coordinating workflow for Idea: {message.content[:30]}...")
        # In a real scenario, Core would search and call agents 5001-5004
        # For simplicity in this demo, Core aggregates a consolidated response
        llm = ChatGoogleGenerativeAI(model="gemini-flash-latest")
        res = llm.invoke(f"Coordinate this startup idea across Compliance, IP, and Procurement: {message.content}")
        core_agent.set_response(message.message_id, res.content)

    core_agent.add_message_handler(core_handler)

    while True:
        time.sleep(1)
