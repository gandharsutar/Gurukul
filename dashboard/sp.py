import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import random

# FastAPI endpoint
FASTAPI_URL = "http://127.0.0.1:8000/interactions/"

# Initialize session state
if 'interactions' not in st.session_state:
    st.session_state.interactions = []
if 'agent_mood' not in st.session_state:
    st.session_state.agent_mood = "neutral"
if 'active_agents' not in st.session_state:
    st.session_state.active_agents = {
        "FinancialCrew": True,
        "EduMentor": True,
        "WellnessBot": True
    }

# Fetch real-time data from FastAPI
def fetch_realtime_data():
    """Fetch real-time data from FastAPI."""
    try:
        response = requests.get(FASTAPI_URL)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch data: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return []

# Send interaction data to FastAPI
def send_interaction_to_api(interaction):
    """Send interaction data to FastAPI."""
    try:
        response = requests.post(FASTAPI_URL, json=interaction)
        if response.status_code != 200:
            st.error(f"Failed to send interaction: {response.status_code}")
    except Exception as e:
        st.error(f"Error sending interaction: {e}")

# Agent configurations
AGENT_CONFIG = {
    "FinancialCrew": {"icon": "💰", "color": "#2ecc71"},
    "EduMentor": {"icon": "📚", "color": "#3498db"},
    "WellnessBot": {"icon": "🧘", "color": "#e74c3c"}
}

# Decision logic functions
def determine_agent_response(user_input):
    input_lower = user_input.lower()
    if any(word in input_lower for word in ['finance', 'money', 'invest']):
        return "FinancialCrew"
    elif any(word in input_lower for word in ['learn', 'education', 'course']):
        return "EduMentor"
    elif any(word in input_lower for word in ['sad', 'depressed', 'lonely']):
        return "WellnessBot"
    else:
        return random.choice(list(AGENT_CONFIG.keys()))

# Dashboard layout
st.title("🤖 Multi-Agent Interaction Dashboard")
st.markdown("Track specialized agents and their decision processes in real-time")

# Sidebar controls
with st.sidebar:
    st.header("Agent Configuration")
    for agent in AGENT_CONFIG:
        st.session_state.active_agents[agent] = st.checkbox(
            f"{AGENT_CONFIG[agent]['icon']} {agent}",
            value=st.session_state.active_agents[agent],
            key=f"active_{agent}"
        )

    st.subheader("Simulate Interaction")
    user_input = st.text_input("Enter a message to begin")

    if st.button("Send Message") or user_input:
        selected_agent = determine_agent_response(user_input)
        if st.session_state.active_agents[selected_agent]:
            interaction = {
                "user_input": user_input,
                "agent": selected_agent,
                "response": {"content": f"Response from {selected_agent}"},
                "timestamp": datetime.now().isoformat(),
                "mood": "neutral"
            }
            send_interaction_to_api(interaction)
        else:
            st.warning(f"{selected_agent} is currently inactive. Enable in sidebar.")

# Main dashboard
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Agent Responses")
    realtime_data = fetch_realtime_data()
    if realtime_data:
        for interaction in realtime_data:
            st.write(f"Time: {interaction['timestamp']}")
            st.write(f"User Input: {interaction['user_input']}")
            st.write(f"Agent: {interaction['agent']}")
            st.write(f"Response: {interaction['response']['content']}")
            st.write("---")
    else:
        st.info("No real-time data available.")

with col2:
    st.subheader("Agent Status")
    for agent, active in st.session_state.active_agents.items():
        if active:
            st.markdown(f"{AGENT_CONFIG[agent]['icon']} {agent}")