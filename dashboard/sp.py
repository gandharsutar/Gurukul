import streamlit as st
from datetime import datetime
import time
import random
import pandas as pd
import plotly.express as px
import requests  # Added for API calls
from io import BytesIO
import base64
from audio_recorder_streamlit import audio_recorder

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
if 'api_data' not in st.session_state:
    st.session_state.api_data = {
        "agent_actions": [],
        "last_fetch": None,
        "status": {}
    }

# API Configuration
API_CONFIG = {
    "BASE_URL": "https://api.example-agent-platform.com/v1",
    "ENDPOINTS": {
        "actions": "/agents/actions",
        "status": "/agents/status",
        "history": "/agents/history"
    },
    "API_KEY": "your_api_key_here",  # In production, use secrets management
    "POLL_INTERVAL": 30  # seconds
}

# Agent configurations (updated with API integration fields)
AGENT_CONFIG = {
    "FinancialCrew": {
        "icon": "💰",
        "color": "#2ecc71",
        "secondary_color": "#27ae60",
        "thought_icon": "📈",
        "description": "Financial advisor specializing in investments and budgeting",
        "api_id": "fin_agent_001"
    },
    "EduMentor": {
        "icon": "📚",
        "color": "#3498db",
        "secondary_color": "#2980b9",
        "thought_icon": "🧠",
        "description": "Educational guide for learning resources and courses",
        "api_id": "edu_agent_002"
    },
    "WellnessBot": {
        "icon": "🧘",
        "color": "#e74c3c",
        "secondary_color": "#c0392b",
        "thought_icon": "❤️",
        "description": "Mental health and wellness support companion",
        "api_id": "well_agent_003"
    }
}

# API Helper Functions
def fetch_agent_actions():
    """Fetch recent agent actions from API"""
    try:
        headers = {"Authorization": f"Bearer {API_CONFIG['API_KEY']}"}
        params = {"limit": 5, "sort": "desc"}
        
        response = requests.get(
            f"{API_CONFIG['BASE_URL']}{API_CONFIG['ENDPOINTS']['actions']}",
            headers=headers,
            params=params,
            timeout=5
        )
        response.raise_for_status()
        
        return response.json().get('data', [])
    
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return []

def fetch_agent_status():
    """Fetch current agent statuses from API"""
    try:
        headers = {"Authorization": f"Bearer {API_CONFIG['API_KEY']}"}
        
        response = requests.get(
            f"{API_CONFIG['BASE_URL']}{API_CONFIG['ENDPOINTS']['status']}",
            headers=headers,
            timeout=5
        )
        response.raise_for_status()
        
        return response.json().get('agents', {})
    
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return {}

def update_api_data():
    """Update all API data with rate limiting"""
    current_time = time.time()
    last_fetch = st.session_state.api_data.get('last_fetch', 0)
    
    if current_time - last_fetch > API_CONFIG['POLL_INTERVAL']:
        with st.spinner("Fetching real-time agent data..."):
            st.session_state.api_data['agent_actions'] = fetch_agent_actions()
            st.session_state.api_data['status'] = fetch_agent_status()
            st.session_state.api_data['last_fetch'] = current_time

# Modified UI to show real-time data
def render_realtime_actions():
    """Display real-time agent actions from API"""
    if not st.session_state.api_data['agent_actions']:
        st.info("No recent agent actions found")
        return
    
    st.subheader("🔄 Real-Time Agent Actions")
    
    for action in st.session_state.api_data['agent_actions'][:5]:  # Show most recent 5
        agent_name = next(
            (k for k, v in AGENT_CONFIG.items() if v['api_id'] == action['agent_id']),
            action['agent_id']
        )
        
        config = AGENT_CONFIG.get(agent_name, {
            'color': '#888',
            'secondary_color': '#666',
            'icon': '🤖'
        })
        
        with st.container():
            st.markdown(f"""
            <div style="background-color:{config['color']}10; padding:12px; border-radius:8px; 
                        border-left:4px solid {config['color']}; margin-bottom:10px">
                <div style="display:flex; justify-content:space-between; align-items:center">
                    <div>
                        <b>{config['icon']} {agent_name}</b> - {action['action_type']}
                    </div>
                    <small>{pd.to_datetime(action['timestamp']).strftime('%H:%M:%S')}</small>
                </div>
                <div style="margin-top:8px; font-size:0.9em">
                    {action.get('description', 'No description available')}
                </div>
            </div>
            """, unsafe_allow_html=True)

# Modified dashboard layout
st.title("🤖 Multi-Agent Interaction Dashboard")
st.markdown("Track specialized agents and their decision processes in real-time")

# Update API data
update_api_data()

# Sidebar controls (unchanged from original)
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
            if selected_agent == "FinancialCrew":
                response = generate_financial_response()
            elif selected_agent == "EduMentor":
                response = generate_educational_response()
            elif selected_agent == "WellnessBot":
                response = generate_wellness_response()
            else:
                response = generate_general_response(selected_agent)
            
            mood = "neutral"
            for m, words in mood_indicators.items():
                if any(word in user_input.lower() for word in words):
                    mood = m
                    break
            
            interaction = {
                "user_input": user_input,
                "agent": selected_agent,
                "response": response,
                "timestamp": datetime.now(),
                "mood": mood
            }
            
            st.session_state.interactions.append(interaction)
            st.session_state.agent_mood = mood
        else:
            st.warning(f"{selected_agent} is currently inactive. Enable in sidebar.")
    
    st.subheader("Audio Input")
    audio_bytes = audio_recorder()
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")

# Main dashboard - updated with real-time section
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Agent Responses")
    
    if st.session_state.interactions:
        latest_interaction = st.session_state.interactions[-1]
        render_agent_response(
            latest_interaction["agent"],
            latest_interaction["response"]
        )
    else:
        st.info("No interactions yet. Send a message to begin.")
    
    # Add real-time actions section
    render_realtime_actions()
    
    st.subheader("Interaction History")
    if st.session_state.interactions:
        history_df = pd.DataFrame([{
            "Time": i["timestamp"].strftime("%H:%M:%S"),
            "Agent": i["agent"],
            "User Input": i["user_input"][:50] + ("..." if len(i["user_input"]) > 50 else ""),
            "Response": i["response"]["title"],
            "Confidence": i["response"]["confidence"]
        } for i in st.session_state.interactions])
        
        def color_row(row):
            color = AGENT_CONFIG[row["Agent"]]["color"] + "20"
            return [f"background-color: {color}"] * len(row)
        
        st.dataframe(
            history_df.style.apply(color_row, axis=1),
            hide_index=True,
            use_container_width=True
        )
    else:
        st.write("No history available")

with col2:
    st.subheader("Agent Status")
    
    # Current mood display
    mood_emoji = {
        "happy": "😊",
        "neutral": "😐",
        "sad": "😢"
    }.get(st.session_state.agent_mood, "🤖")
    
    st.metric("Overall Mood", f"{mood_emoji} {st.session_state.agent_mood.capitalize()}")
    
    # Active agents with API status
    st.markdown("### Agent Status")
    for agent, active in st.session_state.active_agents.items():
        api_status = st.session_state.api_data['status'].get(AGENT_CONFIG[agent]['api_id'], {})
        status = api_status.get('status', 'unknown').lower()
        
        status_icon = {
            'active': '🟢',
            'idle': '🟡',
            'busy': '🟠',
            'error': '🔴',
            'unknown': '⚪'
        }.get(status, '⚪')
        
        config = AGENT_CONFIG[agent]
        st.markdown(f"""
        <div style="background-color:{config['color']}20; padding:10px; border-radius:5px; 
                    margin:5px 0; border-left:3px solid {config['color']}">
            <div style="display:flex; justify-content:space-between; align-items:center">
                <div>
                    {config['icon']} <b>{agent}</b>
                </div>
                <div>
                    {status_icon} {status.capitalize()}
                </div>
            </div>
            <div style="font-size:0.8em; margin-top:5px">
                {api_status.get('current_task', 'No active task')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Response confidence
    if st.session_state.interactions:
        st.markdown("### Confidence Levels")
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

    # Add API status indicator
    st.markdown("### API Connection")
    last_fetch_time = st.session_state.api_data.get('last_fetch')
    if last_fetch_time:
        last_fetch_str = datetime.fromtimestamp(last_fetch_time).strftime('%H:%M:%S')
        st.metric("Last Update", last_fetch_str)
        
        time_since_update = time.time() - last_fetch_time
        if time_since_update > API_CONFIG['POLL_INTERVAL'] * 2:
            st.error("Connection stale - updates delayed")
        elif time_since_update > API_CONFIG['POLL_INTERVAL']:
            st.warning("Refreshing soon...")
        else:
            st.success("Connected and up-to-date")
    else:
        st.warning("Never fetched data")

# Raw data view (updated to show API data)
with st.expander("View Raw Data"):
    tab1, tab2 = st.tabs(["Interaction Data", "API Data"])
    
    with tab1:
        if st.session_state.interactions:
            st.write(st.session_state.interactions)
        else:
            st.write("No interaction data available")
    
    with tab2:
        st.write("Agent Actions:", st.session_state.api_data['agent_actions'])
        st.write("Agent Status:", st.session_state.api_data['status'])