<<<<<<< HEAD
import streamlit as st
from datetime import datetime
import time
import requests
from audio_recorder_streamlit import audio_recorder

# Page configuration and custom CSS
st.set_page_config(page_title="Agent Dashboard", layout="wide")
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    .stExpander > summary {
        font-weight: 600;
        font-size: 1.1rem;
    }
    table.custom-table {
        font-size: 0.85rem;
        width: auto;
        max-width: 100%;
        border-collapse: collapse;
    }
    .custom-table th, .custom-table td {
        padding: 6px 10px;
    }
    .table-container {
        overflow-x: auto;
        max-width: 1000px;
        margin: 0 auto;
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

def determine_agent(user_input):
    user_input_lower = user_input.lower()
    for agent, config in AGENT_CONFIG.items():
        if any(keyword in user_input_lower for keyword in config["keywords"]):
            return agent
    return "WellnessBot"

def fetch_agent_logs():
    try:
        response = requests.get("http://192.168.0.71:8000/agent-log/timeline")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch agent logs: Status Code {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching agent logs: {e}")
        return []

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

            interaction = {
                "timestamp": datetime.now().isoformat(),
                "agent": selected_agent,
                "user_input": user_input,
                "response": {
                    "title": f"{selected_agent} Response",
                    "content": backend_response.get("message", "Processing your request..."),
                    "confidence": backend_response.get("confidence", 0.9),
                    "thought_steps": [
                        f"Received {selected_agent}-related query",
                        f"Routing to {selected_agent} backend",
                        "Waiting for backend response",
                        "Processing response for display"
                    ],
                    "backend_response": backend_response,
                    **backend_response.get("ui_elements", {})
                }
            }

            if "followup" in backend_response:
                interaction["response"]["followup"] = backend_response["followup"]
            if "action" in backend_response:
                interaction["response"]["action"] = backend_response["action"]
            if "link" in backend_response:
                interaction["response"]["link"] = backend_response["link"]

            st.session_state.interactions.append(interaction)
            st.success(f"Request sent to {selected_agent} backend!")
        else:
            st.warning(f"{selected_agent} is currently inactive. Please activate it in the configuration.")

# Page Title
st.title("📊 AI Agent Interaction Dashboard")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🧾 Recent Interactions")
    supabase_interactions = fetch_agent_logs()
    if supabase_interactions:
        table_data = []
        for interaction in reversed(supabase_interactions):
            if not isinstance(interaction, dict):
                st.warning(f"Skipping non-dict interaction: {interaction}")
                continue
            if "agent_name" not in interaction:
                st.warning(f"Skipping entry with missing agent_name: {interaction}")
                continue
            flat_row = {key.replace("_", " ").capitalize(): value for key, value in interaction.items()}
            table_data.append(flat_row)

        # HTML table only, heading removed
        table_html = """
        <div class="table-container">
        <table class="custom-table">
          <thead>
            <tr>
              {}
            </tr>
          </thead>
          <tbody>
        """.format("".join(f"<th>{col}</th>" for col in table_data[0].keys()))

        for row in table_data:
            agent_name = row.get("Agent name", "")
            agent_config = AGENT_CONFIG.get(agent_name, {})
            color = agent_config.get("color", "#ffffff") + "30"

            table_html += f"<tr style='background-color:{color};'>"
            for value in row.values():
                str_value = str(value)
                display_value = str_value[:25] + "..." if len(str_value) > 25 else str_value
                table_html += f"<td title='{str_value}'>{display_value}</td>"
            table_html += "</tr>"

        table_html += "</tbody></table></div>"
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.info("No interactions recorded yet.")

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

with st.expander("🔍 Debug: Raw Interaction Data"):
    if st.session_state.interactions:
        st.write(st.session_state.interactions)
    else:
        st.write("No data yet.")
=======
import streamlit as st
from datetime import datetime
import time
import requests
import pandas as pd
from audio_recorder_streamlit import audio_recorder
import random
import os

# FastAPI backend URL
BACKEND_URL = "http://192.168.0.66:8000"  # Update with your FastAPI backend URL

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
        "financial_crew": True,
        "edumentor": True,
        "wellness_bot": True
    }

# Agent configuration (Only UI relevant info)
AGENT_CONFIG = {
    "financial_crew": {
        "icon": "💰",
        "color": "#2ecc71",
        "secondary_color": "#27ae60",
        "thought_icon": "📈",
        "description": "Financial advisor specializing in investments and budgeting",
        "keywords": ["financial", "money", "invest", "budget", "stock"]
    },
    "edumentor": {
        "icon": "📚",
        "color": "#3498db",
        "secondary_color": "#2980b9",
        "thought_icon": "🧠",
        "description": "Educational guide for learning resources and courses",
        "keywords": ["learn", "education", "course", "study", "school"]
    },
    "wellness_bot": {
        "icon": "🧘",
        "color": "#e74c3c",
        "secondary_color": "#c0392b",
        "thought_icon": "❤️",
        "description": "Mental health and wellness support companion",
        "keywords": ["wellness", "mental", "health", "stress", "meditation"]
    }
}

def call_agent_backend(agent_name, user_input):
    """Function to call the specified agent's backend via FastAPI"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/call_agent/{agent_name}",  # Use the new FastAPI endpoint
            json={"message": user_input},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Backend returned status code {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def determine_agent(user_input):
    """Determine which agent to route to based on keywords (now via FastAPI)"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/route",  # Use the /route endpoint
            json={"message": user_input},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            routed_agents = data["routed_to"]
            # For simplicity, pick the first agent if multiple are routed
            return routed_agents[0] if routed_agents else None
        else:
            st.error(f"Error routing message: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")
        return None

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
    
    # Add a text input for user queries
    user_input = st.text_input("Ask a question:")
    if user_input and st.button("Submit"):
        selected_agent = determine_agent(user_input)
        
        if selected_agent and st.session_state.active_agents[selected_agent]:
            # Call the appropriate backend via FastAPI
            backend_response = call_agent_backend(selected_agent, user_input)
            
            # Create an interaction record
            interaction = {
                "timestamp": datetime.now().isoformat(),
                "agent": selected_agent,
                "user_input": user_input,
                "response": {
                    "title": f"{selected_agent} Response",
                    "content": backend_response.get("message", "Processing your request..."),
                    "confidence": backend_response.get("confidence", 0.9),
                    "thought_steps": [
                        f"Received {selected_agent}-related query",
                        f"Routing to {selected_agent} backend",
                        "Waiting for backend response",
                        "Processing response for display"
                    ],
                    "backend_response": backend_response,
                    **backend_response.get("ui_elements", {})  # Include any additional UI elements
                }
            }
            
            # Add any additional elements from backend response
            if "followup" in backend_response:
                interaction["response"]["followup"] = backend_response["followup"]
            if "action" in backend_response:
                interaction["response"]["action"] = backend_response["action"]
            if "link" in backend_response:
                interaction["response"]["link"] = backend_response["link"]
            
            st.session_state.interactions.append(interaction)
            st.success(f"Request sent to {selected_agent} backend!")
        else:
            st.warning(f"{selected_agent} is currently inactive or could not be determined. Please activate it in the configuration.")

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
                    </h4>   """, unsafe_allow_html=True)
            st.markdown(f"""
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
    else:
        st.info("No interactions recorded yet.")

# RIGHT COLUMN: Agent Overview + Confidence Scores
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

    st.markdown("### 📈 Agent Confidence Scores")
    if st.session_state.interactions:
        # Get the latest confidence score for each active agent
        latest_scores = {}
        for interaction in reversed(st.session_state.interactions):
            agent = interaction["agent"]
            if agent not in latest_scores and st.session_state.active_agents[agent]:
                latest_scores[agent] = interaction["response"]["confidence"]
        
        for agent, confidence in latest_scores.items():
            config = AGENT_CONFIG[agent]
            st.metric(
                label=f"{config['icon']} {agent}",
                value=f"{confidence:.0%}",
                help=f"Latest confidence score for {agent}"
            )
            st.progress(confidence, key=f"progress_{agent}")
    else:
        st.info("No confidence scores yet.")




>>>>>>> 10bd3819fec539bdc1992505f9a5b8ef7bbbbe6a
