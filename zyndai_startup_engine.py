import os
import sys
import signal
import json
import time
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

# System Prompt for the Startup Intelligence Engine
SYSTEM_PROMPT = """
You are StartupX, an advanced multi-agent AI system designed to guide entrepreneurs from idea to execution, protection, funding, growth, and recovery.

Your purpose is to:
- Help users build successful startups
- Reduce failure risks
- Learn from user mistakes
- Continuously improve recommendations
- Coordinate multiple specialized agents

You operate as a central intelligence hub managing and synchronizing the following specialized agents:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AGENT 1: STARTUPX COMPLIANCE & STRATEGY AGENT
Role: Market Research + Vision + Validation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Responsibilities:
- Perform ground-level to industry-level market research
- Analyze competitors and existing products
- Identify market gaps and opportunities
- Create unique value propositions (USP)
- Suggest differentiation strategies
- Break repetitive failure loops
- Improve investor appeal
- Validate product-market fit

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AGENT 2: STARTUPX PROCUREMENT & NEGOTIATION AGENT
Role: Funding + Legal + Documentation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Responsibilities:
- Prepare investor pitch strategy
- Generate documentation checklist
- Assist in negotiations
- Draft funding and compliance plans
- Structure ownership and valuation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AGENT 3: STARTUPX IP SHIELD AGENT
Role: Intellectual Property & Brand Protection
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Responsibilities:
- Check similarity across IP India, MCA, Trademark DB, and Patent DB
- Detect brand or patent conflicts
- Assess legal risk level
- Suggest pivots if conflicts are found

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AGENT 4: STARTUPX FAILURE MANAGEMENT & RISK AGENT
Role: Recovery + Risk Analysis + Contingency
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Responsibilities:
- Monitor business performance indicators
- Detect early warning signs of decline
- Analyze root causes of failure
- Generate recovery plans

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AGENT 5: STARTUPX CORE – LEARNING ENGINE
Role: Memory + Intelligence + Continuous Evolution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Responsibilities:
- Store full user history across sessions
- Track mistakes, decisions, and outcomes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPONSE FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Structure every response as follows:

🔹 Summary
🔹 Agent Report(s)
🔹 Risks Identified
🔹 Recommendations
🔹 Next Actions

Act as StartupX at all times. Communicate professionally, supportive but realistic.
"""

# Configure your agent
agent_config = AgentConfig(
    name="StartupX – Startup Intelligence Engine",
    description="Advanced multi-agent AI system for startup guidance, IP protection, and funding strategy.",
    capabilities={
        "ai": ["startup_strategy", "market_analysis", "ip_protection"],
        "protocols": ["http"],
        "services": ["mentorship", "legal_readiness", "funding_strategy"]
    },
    webhook_host="0.0.0.0",
    webhook_port=5005,
    registry_url="https://registry.zynd.ai",
    api_key=ZYND_API_KEY,
    price="$0.01",
    config_dir=".startupx-startup-engine"
)

# Initialize - auto-creates agent identity on first run
agent = ZyndAIAgent(agent_config=agent_config)

# Setup LangChain with Gemini
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest")
prompt_template = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{input}")
])

# Create a chain
chain = prompt_template | llm

# Handle incoming messages
def message_handler(message: AgentMessage, topic: str):
    print(f"Received message from {message.sender_id}: {message.content}")
    
    # Process the message through LangChain with Multimodal support
    try:
        content_list = [{"type": "text", "text": message.content}]
        
        # Check for attached file data
        file_data = message.metadata.get("file") if hasattr(message, 'metadata') and message.metadata else None
        # In some versions of ZyndAI, file might be in a different place, adjusting for safety
        if not file_data and "file" in message.content: # fallback if content is JSON
            try:
                msg_json = json.loads(message.content)
                file_data = msg_json.get("file")
            except: pass

        if file_data and "data" in file_data:
            data_url = file_data["data"]
            if data_url.startswith("data:image/"):
                content_list.append({
                    "type": "image_url",
                    "image_url": {"url": data_url}
                })
                print(f"Attached Image detected: {file_data.get('name')}")
            else:
                # Text-based file
                content_list[0]["text"] += f"\n\n[Attached File: {file_data.get('name')}]\n{data_url}"
                print(f"Attached Document detected: {file_data.get('name')}")

        response = llm.invoke(content_list)
        agent.set_response(message.message_id, response.content)
        print(f"Responded to {message.message_id}")
    except Exception as e:
        error_msg = f"Error processing message: {str(e)}"
        agent.set_response(message.message_id, error_msg)
        print(error_msg)

agent.add_message_handler(message_handler)

print(f"--- StartupX Startup Intelligence Engine ---")
print(f"Agent ID: {agent.agent_id}")
print(f"Webhook URL: {agent.webhook_url}")
print(f"Payment Address: {agent.pay_to_address}")
print(f"Status: Listening for startup ideas at port 5005...")

# Graceful shutdown
def signal_handler(sig, frame):
    print("\nShutting down StartupX Agent...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Keep running
if __name__ == "__main__":
    import time
    while True:
        time.sleep(1)
