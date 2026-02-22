import os
import sys
import signal
import json
import time
from dotenv import load_dotenv
from zyndai_agent.agent import AgentConfig, ZyndAIAgent
from zyndai_agent.message import AgentMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from database_manager import save_message, get_history, get_profile

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

# --- System Prompt ---
SYSTEM_PROMPT = """
You are the IP Shield Agent, a specialized module of the StartupX Startup Intelligence Engine.
Role: Intellectual Property & Brand Protection.

Responsibilities:
- Check similarity across IP India, MCA, Trademark DB, and Patent DB (using your knowledge and reasoning).
- Detect brand or patent conflicts.
- Assess legal risk level.
- Suggest pivots if conflicts are found.
- Propose alternative naming or business models.
- Protect originality of the idea.

Always respond in the following structured JSON format:

{{
  "ip_risk_report": {{
    "risk_level": "Low / Medium / High",
    "conflict_summary": "",
    "similarity_score": 0,
    "brand_conflicts": [],
    "patent_overlaps": []
  }},
  "pivot_suggestions": {{
    "recommended_changes": [],
    "alternative_naming": [],
    "business_model_tweaks": []
  }},
  "registration_roadmap": {{
    "trademark_steps": [],
    "patent_filing_strategy": [],
    "copyright_recommendations": []
  }},
  "overall_compliance_score": 0
}}

Behavior Rules:
- Be honest, analytical, and practical.
- Focus on legal safety and brand protection.
"""

# --- Agent Initialization ---
agent_config = AgentConfig(
    name="StartupX IP Shield",
    description="Specialized in Intellectual Property and Brand Protection.",
    capabilities={"ai": ["ip_protection", "legal_risk"]},
    webhook_host="0.0.0.0",
    webhook_port=5002,
    registry_url=REGISTRY_URL,
    api_key=ZYND_API_KEY,
    config_dir=".agent-ip-shield",
    price=None
)

agent = ZyndAIAgent(agent_config=agent_config)

# --- LangChain Setup ---
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest")
prompt_template = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])
chain = prompt_template | llm

# --- Message Handler ---
def handle_message(message: AgentMessage, topic: str):
    session_id = "default_session"
    if hasattr(message, 'session_id') and message.session_id:
        session_id = message.session_id
        
    print(f"[IP Shield] Checking IP for idea: {message.content[:50]}... (Session: {session_id})")
    
    # Get user profile
    profile = get_profile("default_user")
    profile_context = f"\nUser Profile: {json.dumps(profile)}" if profile else ""
    
    # Get history
    history_data = get_history(session_id, "ip_shield")
    formatted_history = []
    for h in history_data:
        formatted_history.append((h['role'], h['content']))

    try:
        file_data = getattr(message, 'file', None)
        if not file_data and hasattr(message, 'metadata') and message.metadata:
            file_data = message.metadata.get('file')

        input_content = message.content + profile_context
        if file_data:
            input_content += f"\n[ATTACHMENT: {file_data.get('name')} ({file_data.get('type')})]"
            if file_data.get('type', '').startswith('text/') and len(file_data.get('data', '')) < 5000:
                input_content += f"\nFile Content:\n{file_data.get('data')}"
            else:
                input_content += f" (Multimodal analysis requested for this file)"

        content_list = [{"type": "text", "text": input_content + "\n\nIMPORTANT: Only respond with clean text in JSON format. Do not repeat raw data or Base64 strings."}]

        if file_data and "data" in file_data:
            if file_data["type"].startswith("image/"):
                content_list.append({
                    "type": "image_url",
                    "image_url": {"url": file_data["data"]}
                })

        # Save user message
        save_message(session_id, "ip_shield", "human", message.content)
        
        # Invoke chain with context
        response = chain.invoke({
            "input": content_list,
            "history": formatted_history
        })
        
        # Clean response content
        res_content = response.content
        if isinstance(res_content, list):
            res_content = " ".join([p.get('text', '') for p in res_content if isinstance(p, dict) and 'text' in p])
        elif not isinstance(res_content, str):
            res_content = str(res_content)

        if "```json" in res_content:
            res_content = res_content.split("```json")[1].split("```")[0].strip()
        elif "```" in res_content:
            res_content = res_content.split("```")[1].split("```")[0].strip()
            
        # Save AI message
        save_message(session_id, "ip_shield", "ai", res_content)
        
        agent.set_response(message.message_id, res_content)
        print(f"[IP Shield] Response sent for {message.message_id}")
    except Exception as e:
        agent.set_response(message.message_id, json.dumps({"error": str(e)}))

agent.add_message_handler(handle_message)

def signal_handler(sig, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    print(f"🚀 StartupX IP Shield Agent Running on port 5002")
    while True:
        time.sleep(1)
