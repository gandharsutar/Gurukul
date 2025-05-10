import streamlit as st
from datetime import datetime
import time
import requests
import pandas as pd
from audio_recorder_streamlit import audio_recorder
import random
import os

# Page configuration and custom CSS
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

# Agent configuration
AGENT_CONFIG = {
    "FinancialCrew": {
        "icon": "💰",
        "color": "#2ecc71",
        "secondary_color": "#27ae60",
        "thought_icon": "📈",
        "description": "Financial advisor specializing in investments and budgeting",
    },
    "EduMentor": {
        "icon": "📚",
        "color": "#3498db",
        "secondary_color": "#2980b9",
        "thought_icon": "🧠",
        "description": "Educational guide for learning resources and courses",
    },
    "WellnessBot": {
        "icon": "🧘",
        "color": "#e74c3c",
        "secondary_color": "#c0392b",
        "thought_icon": "❤️",
        "description": "Mental health and wellness support companion",
    }
}

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

# Page Title
st.title("📊 AI Agent Interaction Dashboard")

# Swapped layout: LEFT = Confidence + Interactions, RIGHT = Agent Overview
col1, col2 = st.columns([2, 1])

# LEFT COLUMN: Confidence + Interactions
with col1:
    st.subheader("📈 Recent Confidence Scores")
    if st.session_state.interactions:
        for interaction in reversed(st.session_state.interactions[-3:]):
            agent = interaction["agent"]
            confidence = interaction["response"]["confidence"]
            st.metric(
                label=agent,
                value=f"{confidence:.0%}",
                help="Confidence score of the last response"
            )
            st.progress(confidence)
    else:
        st.info("No confidence scores yet.")

    st.subheader("🧾 Recent Interactions")
    if st.session_state.interactions:
        for interaction in reversed(st.session_state.interactions):
            agent = interaction["agent"]
            config = AGENT_CONFIG[agent]
            response = interaction["response"]

            # User message
            st.markdown(f"""
                <div style="background-color:#f8f9fa; padding:15px; border-radius:10px; 
                            margin-bottom:10px; border-left:4px solid {config['color']};">
                    <strong>🗣️ You:</strong> {interaction["user_input"]}
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
                        <strong>{response['title']}</strong><br/>
                        {response['content']}
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
                for i, step in enumerate(response["thought_steps"]):
                    st.markdown(f"""
                        <div style="padding:10px; margin:8px 0; border-left:3px solid {config['secondary_color']}; 
                                    background-color:{config['color']}10; border-radius:5px;">
                            <b>Step {i+1}:</b> {step}
                        </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("No interactions recorded yet.")

# RIGHT COLUMN: Agent Overview
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

# Debug Raw Interaction Data
with st.expander("🔍 Debug: Raw Interaction Data"):
    if st.session_state.interactions:
        st.write(st.session_state.interactions)
    else:
        st.write("No data yet.")
