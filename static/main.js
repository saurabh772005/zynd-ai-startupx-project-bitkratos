// StartupX - Premium Multi-Agent Dashboard
const sessionId = 'session_' + Math.random().toString(36).substr(2, 9);

const agents = {
    "core": { name: "StartupX Core", desc: "Your central AI brain and strategic coordinator.", color: "#00d4ff" },
    "compliance": { name: "Strategy & Market Agent", desc: "Market research, competitor analysis, and compliance.", color: "#00ff9d" },
    "ip_shield": { name: "IP & Legal Shield", desc: "Trademark checks, patent overlaps, and brand protection.", color: "#7000ff" },
    "procurement": { name: "Funding & Procurement", desc: "Investor readiness, budget allocation, and vendor sourcing.", color: "#ffaa00" },
    "risk": { name: "Failure Risk Agent", desc: "Risk diagnosis, contingency planning, and recovery strategies.", color: "#ff3c3c" }
};

let activeAgent = "core";

const chatContainer = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const loading = document.getElementById('loading');
const agentBtns = document.querySelectorAll('.agent-btn');

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    updateStatus();
    updateProfile();
    setInterval(updateStatus, 15000);
    setInterval(updateProfile, 10000);

    userInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // File Upload Listeners
    const attachBtn = document.getElementById('attach-btn');
    const fileInput = document.getElementById('file-input');
    const filePreview = document.getElementById('file-preview-container');
    const fileName = document.getElementById('file-name');
    const removeFile = document.getElementById('remove-file');
    let selectedFileData = null;

    attachBtn.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            selectedFileData = {
                name: file.name,
                type: file.type,
                data: event.target.result
            };
            fileName.innerText = file.name;
            filePreview.style.display = 'flex';
        };

        if (file.type.startsWith('image/')) {
            reader.readAsDataURL(file); // Base64
        } else {
            reader.readAsText(file); // Plain text
        }
    });

    removeFile.addEventListener('click', () => {
        selectedFileData = null;
        fileInput.value = '';
        filePreview.style.display = 'none';
    });

    window.selectedFileData = () => selectedFileData;
});

// --- Agent Switching ---
agentBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        agentBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        activeAgent = btn.dataset.agent;
        document.getElementById('active-agent-name').innerText = agents[activeAgent].name;
        document.getElementById('active-agent-desc').innerText = agents[activeAgent].desc;

        document.documentElement.style.setProperty('--accent', agents[activeAgent].color);
        addMessage(`Focus shifted to ${agents[activeAgent].name}`, 'system');
    });
});

// --- API Calls ---
async function updateStatus() {
    try {
        const res = await fetch('/api/status');
        const status = await res.json();
        Object.keys(status).forEach(aid => {
            const btn = document.querySelector(`.agent-btn[data-agent="${aid}"]`);
            if (btn) {
                const indicator = btn.querySelector('.status-indicator');
                indicator.className = `status-indicator ${status[aid]}`;
            }
        });
    } catch (e) { console.error("Status check failed", e); }
}

async function updateProfile() {
    try {
        const res = await fetch('/api/profile');
        const profile = await res.json();

        const logoText = document.querySelector('.logo-text');
        if (logoText) logoText.innerText = "STARTUPX";

        // Update profile card
        const startupEl = document.getElementById('prof-startup');
        const founderEl = document.getElementById('prof-founder');
        const stageEl = document.getElementById('prof-stage');
        const imgContainer = document.getElementById('user-profile-img-container');
        const imgEl = document.getElementById('user-profile-img');

        if (startupEl) startupEl.innerText = profile.startup_name || "New Venture";
        if (founderEl) founderEl.innerText = profile.founder_name || "Founder";
        if (stageEl) stageEl.innerText = (profile.stage || "Ideation") + " Stage";

        if (profile.profile_image) {
            imgEl.src = profile.profile_image;
            imgContainer.style.display = 'block';
        } else {
            imgContainer.style.display = 'none';
        }
    } catch (e) { console.error("Profile fetch failed", e); }
}

function addMessage(text, type) {
    if (typeof text !== 'string') text = JSON.stringify(text);

    // Safety filter: If the text looks like raw JSON with type:text, extract the inner text
    if (text.trim().startsWith('[{') && text.includes('"type":"text"')) {
        try {
            const parsed = JSON.parse(text);
            text = parsed.filter(p => p.type === 'text').map(p => p.text).join('\n');
        } catch (e) { }
    }

    // Safety filter: Strip massive Base64 blobs if they somehow reached the UI
    if (text.length > 5000 && text.includes(';base64,')) {
        text = text.replace(/data:.*?;base64,[A-Za-z0-9+/=]{100,}/g, '[FILE DATA STRIPPED]');
    }

    const div = document.createElement('div');
    div.className = `message ${type}`;
    const formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
    div.innerHTML = `<div class="msg-content">${formatted}</div>`;
    chatContainer.appendChild(div);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function handleSend() {
    const text = userInput.value.trim();
    if (!text) return;

    const fileData = window.selectedFileData ? window.selectedFileData() : null;
    userInput.value = '';
    userInput.style.height = 'auto';

    // Clear preview
    if (fileData) {
        addMessage(`Shared file: ${fileData.name}`, 'user');
        document.getElementById('remove-file').click();
    }

    addMessage(text, 'user');
    loading.classList.remove('hidden');

    try {
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                agent_id: activeAgent,
                content: text,
                session_id: sessionId,
                file: fileData
            })
        });
        const data = await response.json();
        if (data.error) addMessage(`Error: ${data.error}`, 'system');
        else (Array.isArray(data.response) ? data.response : [{ text: data.response }]).forEach(m => addMessage(m.text || m, 'ai'));
    } catch (e) { addMessage(`Network error: ${e.message}`, 'system'); }
    finally { loading.classList.add('hidden'); }
}

sendBtn.addEventListener('click', handleSend);
userInput.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } });
function clearChat() { chatContainer.innerHTML = '<div class="message system"><div class="msg-content">Protocol refreshed.</div></div>'; }
