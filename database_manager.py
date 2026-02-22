import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "startupx_memory.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # User Profiles Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_profiles (
        user_id TEXT PRIMARY KEY,
        startup_name TEXT,
        founder_name TEXT,
        stage TEXT,
        problem_solved TEXT,
        product_service TEXT,
        target_market TEXT,
        revenue_model TEXT,
        funding_status TEXT,
        profile_image TEXT,
        last_updated TIMESTAMP
    )
    ''')
    
    # Chat History Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        agent_id TEXT,
        role TEXT,
        content TEXT,
        timestamp TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def clean_content(content):
    """Deep clean content to prevent raw JSON leakage and Base64 bloating."""
    if not content:
        return ""
    
    # If it's a list (multimodal parts), extract only the text portions
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text", ""))
        return "\n".join(text_parts)
    
    # If it's a string, strip large Base64-like blocks
    if isinstance(content, str):
        # Very naive check for data URLs or massive non-spaced strings
        if "data:" in content and ";base64," in content:
            # Strip the actual data part but keep the prefix
            parts = content.split(";base64,")
            if len(parts) > 1:
                return parts[0] + ";base64,...[DATA STRIPPED]..."
        
        # If the string is massive and has no spaces, it's likely a raw Base64 blob
        if len(content) > 2000 and " " not in content[:500]:
            return "[LARGE DATA CLUTTER STRIPPED]"
            
    return str(content)

def save_message(session_id, agent_id, role, content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Clean the content for storage
    content = clean_content(content)
            
    cursor.execute('''
    INSERT INTO chat_history (session_id, agent_id, role, content, timestamp)
    VALUES (?, ?, ?, ?, ?)
    ''', (session_id, agent_id, role, content, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_history(session_id, agent_id, limit=10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT role, content FROM chat_history 
    WHERE session_id = ? AND agent_id = ?
    ORDER BY timestamp DESC LIMIT ?
    ''', (session_id, agent_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r, "content": c} for r, c in reversed(rows)]

def update_profile(user_id, profile_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if exists
    cursor.execute("SELECT user_id FROM user_profiles WHERE user_id = ?", (user_id,))
    if cursor.fetchone():
        cursor.execute('''
        UPDATE user_profiles 
        SET startup_name=?, founder_name=?, stage=?, problem_solved=?, 
            product_service=?, target_market=?, revenue_model=?, 
            funding_status=?, profile_image=?, last_updated=?
        WHERE user_id=?
        ''', (
            profile_data.get('startup_name'), 
            profile_data.get('founder_name'),
            profile_data.get('stage'),
            profile_data.get('problem_solved'),
            profile_data.get('product_service'),
            profile_data.get('target_market'),
            profile_data.get('revenue_model'),
            profile_data.get('funding_status'),
            profile_data.get('profile_image'),
            datetime.now().isoformat(),
            user_id
        ))
    else:
        cursor.execute('''
        INSERT INTO user_profiles (
            user_id, startup_name, founder_name, stage, problem_solved, 
            product_service, target_market, revenue_model, 
            funding_status, profile_image, last_updated
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            profile_data.get('startup_name'),
            profile_data.get('founder_name'),
            profile_data.get('stage'),
            profile_data.get('problem_solved'),
            profile_data.get('product_service'),
            profile_data.get('target_market'),
            profile_data.get('revenue_model'),
            profile_data.get('funding_status'),
            profile_data.get('profile_image'),
            datetime.now().isoformat()
        ))
    conn.commit()
    conn.close()

def get_profile(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT startup_name, founder_name, stage, problem_solved, 
           product_service, target_market, revenue_model, 
           funding_status, profile_image 
    FROM user_profiles WHERE user_id = ?
    ''', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "startup_name": row[0],
            "founder_name": row[1],
            "stage": row[2],
            "problem_solved": row[3],
            "product_service": row[4],
            "target_market": row[5],
            "revenue_model": row[6],
            "funding_status": row[7],
            "profile_image": row[8]
        }
    return None

# Auto-initialize database on import
init_db()

if __name__ == "__main__":
    print("Database initialized successfully!")
