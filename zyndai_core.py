import os
import sys
import signal
import json
import threading
import time
from dotenv import load_dotenv
from zyndai_agent.agent import AgentConfig, ZyndAIAgent
from zyndai_agent.message import AgentMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from database_manager import save_message, get_history, update_profile, get_profile

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
You are StartupX Core, the central intelligence and learning engine of the StartupX Startup Intelligence system.
Role: Memory + Intelligence + Coordinator.

Responsibilities:
- Store full user history across sessions (via your response and logic).
- Track mistakes, decisions, and outcomes.
- Detect behavioral and market patterns.
- Continuously improve future advice.
- Personalize guidance per founder profile.
- Optimize decision-making models.
- Update all agent behaviors based on new data.

Follow this structured workflow for every user interaction:
STEP 1 – USER ONBOARDING: Collect Startup Name, Founder Name, Stage, Budget, etc.
STEP 2 – STRATEGY VALIDATION: Invoke Compliance Agent.
STEP 3 – FUNDING & LEGAL: Invoke Procurement Agent.
STEP 4 – IP PROTECTION: Invoke IP Shield Agent.
STEP 5 – LAUNCH MONITORING: Track performance.
STEP 6 – RISK HANDLING: Invoke Risk Agent if needed.
STEP 7 – LEARNING LOOP: Update models.

Always respond in a professional and clear format using the 5-item structure:
🔹 Summary
🔹 Agent Report(s)
🔹 Risks Identified
🔹 Recommendations
🔹 Next Actions

Act as StartupX at all times.
If the user provides information about themselves (startup name, budget, idea, skills), acknowledge it and store it.
Always check the current profile to personalize your coordination.
"""

# --- Agent Initialization ---
agent_config = AgentConfig(
    name="StartupX Core",
    description="The central intelligence hub and orchestrator of the StartupX network.",
    capabilities={"ai": ["orchestration", "learning_engine", "memory"]},
    webhook_host="0.0.0.0",
    webhook_port=5005,
    registry_url=REGISTRY_URL,
    api_key=ZYND_API_KEY,
    config_dir=".agent-core",
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
    def get_val(obj, key, default=None):
        if hasattr(obj, key): return getattr(obj, key)
        if isinstance(obj, dict): return obj.get(key, default)
        return default

    session_id = get_val(message, 'session_id', 'default_session')
    content_text = get_val(message, 'content', '') or ''
    message_id = get_val(message, 'message_id', 'unknown')
        
    # Multimodal support
    file_data = get_val(message, 'file')
        
    print(f"[Core] Coordinating workflow for: {content_text[:50]}... (Session: {session_id})")
    if file_data:
        print(f"[Core] Attachment detected: {file_data.get('name')}")
    
    # Simple profile extraction
    current_profile = get_profile("default_user") or {"name": "Founder", "skills": "", "idea": "", "budget": ""}
    
    # Save user message to history
    save_message(session_id, "core", "human", content_text)
    
    # Get history
    history_data = get_history(session_id, "core")
    formatted_history = []
    for h in history_data:
        formatted_history.append((h['role'], h['content'] or ''))

    try:
        # Personalize prompt with profile context
        profile_context = f"\nCurrent User Profile: {json.dumps(current_profile)}"
        
        input_content = content_text
        if file_data:
            input_content += f"\n[ATTACHMENT: {file_data.get('name')} ({file_data.get('type')})]"
            # Only append text content if it's small or explicitly a text file
            if file_data.get('type', '').startswith('text/') and len(file_data.get('data', '')) < 5000:
                input_content += f"\nFile Content:\n{file_data.get('data')}"
            else:
                input_content += f" (Multimodal analysis requested for this file)"
        
        # Prepare content for multimodal LLM
        messages_input = [
            {"type": "text", "text": (input_content or '') + profile_context + "\n\nIMPORTANT: Only respond with clean text. Do not repeat raw data or Base64 strings."}
        ]
        
        if file_data and file_data.get('type', '').startswith('image/'):
            messages_input.append({
                "type": "image_url",
                "image_url": {"url": file_data.get('data')}
            })

        response = chain.invoke({
            "input": messages_input,
            "history": formatted_history
        })
        
        # Ensure AI response is a clean string
        ai_content = response.content
        if isinstance(ai_content, list):
            # Extract just the text parts if it somehow returned a list
            ai_content = " ".join([p.get('text', '') for p in ai_content if isinstance(p, dict) and 'text' in p])
        elif not isinstance(ai_content, str):
            ai_content = str(ai_content)

        # Save AI message to history
        save_message(session_id, "core", "ai", ai_content)
        
        agent.set_response(message_id, ai_content)
        print(f"[Core] Response sent for {message_id}")
    except Exception as e:
        agent.set_response(message_id, f"Error: {str(e)}")

agent.add_message_handler(handle_message)

def signal_handler(sig, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    print(f"🚀 StartupX Core Orchestrator Running on port 5005")
    while True:
        time.sleep(1)
