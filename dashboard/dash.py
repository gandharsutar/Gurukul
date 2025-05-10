import streamlit as st
from datetime import datetime
import time
import requests
import pandas as pd
from audio_recorder_streamlit import audio_recorder
import random
import os

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

# Agent configurations with backend URLs
AGENT_CONFIG = {
    "FinancialCrew": {
        "icon": "💰",
        "color": "#2ecc71",
        "secondary_color": "#27ae60",
        "thought_icon": "📈",
        "description": "Financial advisor specializing in investments and budgeting",
        "backend_url": "https://financial-crew-backend.com/api",
        "signal": "lets_go_finance"
    },
    "EduMentor": {
        "icon": "📚",
        "color": "#3498db",
        "secondary_color": "#2980b9",
        "thought_icon": "🧠",
        "description": "Educational guide for learning resources and courses",
        "backend_url": "https://edumentor-backend.com/api",
        "signal": "lets_go_learn"
    },
    "WellnessBot": {
        "icon": "🧘",
        "color": "#e74c3c",
        "secondary_color": "#c0392b",
        "thought_icon": "❤️",
        "description": "Mental health and wellness support companion",
        "backend_url": "https://wellnessbot-backend.com/api",
        "signal": "lets_go_wellness"
    }
}

def render_agent_response(agent, response):
    """Render the agent's response in the UI"""
    config = AGENT_CONFIG[agent]
    
    with st.container():
        st.markdown(f"""
        <div style="background-color:{config['color']}20; padding:15px; border-radius:10px; 
                    border-left:5px solid {config['color']}; margin-bottom:15px">
            <h3 style="color:{config['color']}; margin:0;">
                {config['icon']} {agent}
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander(f"{response['title']} (Confidence: {response['confidence']:.0%})", expanded=True):
            st.write(response["content"])
            if "link" in response:
                st.markdown(f"[🔗 {response.get('reason', 'Learn more')}]({response['link']})")
            if "action" in response:
                st.button(response["action"], key=f"{agent}_{time.time()}")
            if "followup" in response:
                st.write(response["followup"])
        
        with st.expander(f"{config['thought_icon']} Thought Process"):
            for i, step in enumerate(response["thought_steps"]):
                st.markdown(f"""
                <div style="padding:10px; margin:5px 0; border-left:3px solid {config['secondary_color']}; 
                            background-color:{config['color']}10;">
                    <b>Step {i+1}:</b> {step}
                </div>
                """, unsafe_allow_html=True)

                if i < len(response["thought_steps"]) - 1:
                    st.markdown(f"""
                    <div style="border-left:2px dashed {config['secondary_color']}; 
                                height:15px; margin-left:15px;"></div>
                    """, unsafe_allow_html=True)

# Main App Layout
st.title("📊 Agent Interaction Dashboard")
st.markdown("Monitor user-agent interactions and AI thought trails")

# Sidebar for agent configuration only
with st.sidebar:
    st.header("Agent Configuration")
    for agent in AGENT_CONFIG:
        st.session_state.active_agents[agent] = st.checkbox(
            f"{AGENT_CONFIG[agent]['icon']} {agent}", 
            value=st.session_state.active_agents[agent],
            key=f"active_{agent}"
        )
    
    st.subheader("Audio Input")
    audio_bytes = audio_recorder()
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")

# Interaction history
st.subheader("🧾 Interaction History")

if st.session_state.interactions:
    for interaction in reversed(st.session_state.interactions):
        st.markdown(f"""
        <div style="background-color:#f0f2f6; padding:10px; border-radius:10px; 
                    margin-bottom:10px;">
            <strong>🗣 User:</strong> {interaction["user_input"]}
        </div>
        """, unsafe_allow_html=True)
        
        render_agent_response(
            interaction["agent"],
            interaction["response"]
        )
else:
    st.info("No interactions to display yet.")

# Mood and agent status
st.subheader("Agent Overview")

mood_emoji = {
    "happy": "😊",
    "neutral": "😐",
    "sad": "😢"
}.get(st.session_state.agent_mood, "🤖")

st.metric("Overall Mood", f"{mood_emoji} {st.session_state.agent_mood.capitalize()}")

st.markdown("### Active Agents")
for agent, active in st.session_state.active_agents.items():
    if active:
        config = AGENT_CONFIG[agent]
        st.markdown(f"""
        <div style="background-color:{config['color']}20; padding:10px; border-radius:5px; 
                    margin:5px 0; border-left:3px solid {config['color']}">
            {config['icon']} <b>{agent}</b>
        </div>
        """, unsafe_allow_html=True)

# Recent confidence section
if st.session_state.interactions:
    st.markdown("### Recent Confidence Scores")
    latest_confidences = [
        {"Agent": i["agent"], 
         "Confidence": i["response"]["confidence"],
         "Color": AGENT_CONFIG[i["agent"]]["color"]}
        for i in st.session_state.interactions[-3:]
    ]
    
    for conf in reversed(latest_confidences):
        st.metric(
            label=conf["Agent"],
            value=f"{conf['Confidence']:.0%}",
            help=f"Confidence in last response from {conf['Agent']}"
        )
        st.progress(conf["Confidence"])

# Debug view
with st.expander("🔍 Debug: View Raw Interaction Data"):
    if st.session_state.interactions:
        st.write(st.session_state.interactions)
    else:
        st.write("No interaction data available.")
