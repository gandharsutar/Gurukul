import streamlit as st
from datetime import datetime
import time
import requests
import pandas as pd
from audio_recorder_streamlit import audio_recorder
import random
import os

# Backend log API endpoint
LOG_API_URL = "http://192.168.0.94:8000/agent-log/save"

# Streamlit UI Setup
st.set_page_config(page_title="Agent Dashboard", layout="wide")
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }
    .stExpander > summary {
        font-weight: 600;
        font-size: 1.1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Session state init
if 'agent_mood' not in st.session_state:
    st.session_state.agent_mood = "neutral"
if 'active_agents' not in st.session_state:
    st.session_state.active_agents = {
        "FinancialCrew": True,
        "EduMentor": True,
        "WellnessBot": True
    }

# Agent config
AGENT_CONFIG = {
    "FinancialCrew": {
        "icon": "💰",
        "color": "#2ecc71",
        "secondary_color": "#27ae60",
        "thought_icon": "📈",
        "description": "Financial advisor specializing in investments and budgeting",
        "backend_url": "https://your-friends-backend-url.com/api/financialcrew",
        "keywords": ["financial", "money", "invest", "budget", "stock"]
    },
    "EduMentor": {
        "icon": "📚",
        "color": "#3498db",
        "secondary_color": "#2980b9",
        "thought_icon": "🧠",
        "description": "Educational guide for learning resources and courses",
        "backend_url": "https://your-edumentor-backend-url.com/api/edumentor",
        "keywords": ["learn", "education", "course", "study", "school"]
    },
    "WellnessBot": {
        "icon": "🧘",
        "color": "#e74c3c",
        "secondary_color": "#c0392b",
        "thought_icon": "❤️",
        "description": "Mental health and wellness support companion",
        "backend_url": "https://your-wellnessbot-backend-url.com/api/wellnessbot",
        "keywords": ["wellness", "mental", "health", "stress", "meditation"]
    }
}

# Fetch logs from backend
def fetch_agent_logs():
    try:
        response = requests.get(LOG_API_URL)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error fetching logs: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Exception while fetching logs: {str(e)}")
        return []

# Determine agent based on input
def determine_agent(user_input):
    user_input_lower = user_input.lower()
    for agent, config in AGENT_CONFIG.items():
        if any(keyword in user_input_lower for keyword in config["keywords"]):
            return agent
    return "WellnessBot"

# Call backend
def call_agent_backend(agent_name, user_input):
    try:
        response = requests.post(
            AGENT_CONFIG[agent_name]["backend_url"],
            json={
                "message": user_input,
                "action": "process_request",
                "agent": agent_name
            },
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Backend returned status code {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

# Sidebar
with st.sidebar:
    st.header("⚙️ Agent Configuration")
    for agent in AGENT_CONFIG:
        st.session_state.active_agents[agent] = st.checkbox(
            f"{AGENT_CONFIG[agent]['icon']} {agent}",
            value=st.session_state.active_agents[agent]
        )

    st.subheader("🎙️ Audio Input")
    audio_bytes = audio_recorder()
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")

    user_input = st.text_input("Ask a question:")
    if user_input and st.button("Submit"):
        selected_agent = determine_agent(user_input)
        if st.session_state.active_agents[selected_agent]:
            backend_response = call_agent_backend(selected_agent, user_input)
            st.success(f"Request sent to {selected_agent} backend!")
        else:
            st.warning(f"{selected_agent} is inactive. Activate it in the sidebar.")

# Page title
st.title("📊 AI Agent Interaction Dashboard")

# Layout
col1, col2 = st.columns([2, 1])

# LEFT COLUMN
with col1:
    st.subheader("📈 Recent Confidence Scores")
    logs = fetch_agent_logs()

    if logs:
        for interaction in reversed(logs[-3:]):
            agent = interaction.get("agent", "Unknown")
            confidence = interaction.get("response", {}).get("confidence", 0.0)
            st.metric(label=agent, value=f"{confidence:.0%}")
            st.progress(confidence)
    else:
        st.info("No confidence scores yet.")

    st.subheader("🧾 Recent Interactions")
    if logs:
        for interaction in reversed(logs):
            agent = interaction.get("agent", "Unknown")
            config = AGENT_CONFIG.get(agent, {
                "color": "#cccccc",
                "secondary_color": "#999999",
                "icon": "🤖",
                "thought_icon": "💭",
                "description": "Unknown agent"
            })
            response = interaction.get("response", {})

            # User query
            st.markdown(f"""
                <div style="background-color:#f8f9fa; padding:15px; border-radius:10px; 
                            margin-bottom:10px; border-left:4px solid {config['color']};">
                    <strong>🗣️ You:</strong> {interaction.get("user_input", "")}
                </div>
            """, unsafe_allow_html=True)

            # Agent response
            st.markdown(f"""
                <div style="background-color:{config['color']}15; padding:15px; border-radius:10px;
                            border-left:5px solid {config['color']}; margin-bottom:20px;">
                    <h4 style="color:{config['color']}; margin:0 0 10px 0;">
                        {config['icon']} {agent}
                    </h4>
                    <div style="font-size: 1rem; margin-bottom: 10px;">
                        <strong>{response.get('title', '')}</strong><br/>
                        {response.get('content', '')}
                    </div>
            """, unsafe_allow_html=True)

            if "link" in response:
                st.markdown(f"[🔗 {response.get('reason', 'Learn more')}]({response['link']})")
            if "followup" in response:
                st.markdown(f"💬 _Follow-up:_ {response['followup']}")
            if "action" in response:
                st.button(response["action"], key=f"{agent}_{time.time()}")

            st.markdown("</div>", unsafe_allow_html=True)

            # Thought process
            with st.expander(f"{config['thought_icon']} Thought Process"):
                for i, step in enumerate(response.get("thought_steps", [])):
                    st.markdown(f"""
                        <div style="padding:10px; margin:8px 0; border-left:3px solid {config['secondary_color']}; 
                                    background-color:{config['color']}10; border-radius:5px;">
                            <b>Step {i+1}:</b> {step}
                        </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("No interactions recorded yet.")

# RIGHT COLUMN
with col2:
    st.subheader("💡 Agent Overview")
    mood_emoji = {
        "happy": "😊",
        "neutral": "😐",
        "sad": "😢"
    }.get(st.session_state.agent_mood, "🤖")
    st.metric("Overall Mood", f"{mood_emoji} {st.session_state.agent_mood.capitalize()}")

    st.markdown("### ✅ Active Agents")
    for agent, active in st.session_state.active_agents.items():
        if active:
            config = AGENT_CONFIG[agent]
            st.markdown(f"""
                <div style="background-color:{config['color']}20; padding:10px; border-radius:5px; 
                            margin:5px 0; border-left:3px solid {config['color']}">
                    {config['icon']} <b>{agent}</b><br>
                    <small>{config['description']}</small>
                </div>
            """, unsafe_allow_html=True)

# Debug
with st.expander("🔍 Debug: Raw Interaction Data"):
    st.write(logs if logs else "No data yet.")
