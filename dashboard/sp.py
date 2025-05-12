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
    .workflow-step {
        padding: 10px;
        margin: 8px 0;
        border-radius: 5px;
        background-color: #f8f9fa;
    }
    .workflow-step.system {
        border-left: 3px solid #6c757d;
    }
    .workflow-step.action {
        border-left: 3px solid #28a745;
    }
    .workflow-step.query {
        border-left: 3px solid #17a2b8;
    }
    .workflow-step.result {
        border-left: 3px solid #ffc107;
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

# Agent configuration with backend URLs
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
    """Function to call the specified agent's backend"""
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
            return response.json()  # Assuming the backend returns JSON
        else:
            return {"error": f"Backend returned status code {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def determine_agent(user_input):
    """Determine which agent to route to based on keywords"""
    user_input_lower = user_input.lower()
    for agent, config in AGENT_CONFIG.items():
        if any(keyword in user_input_lower for keyword in config["keywords"]):
            return agent
    return "WellnessBot"  # Default to WellnessBot if no keywords match

def format_workflow_steps(workflow_data):
    """Format the workflow steps from backend into a displayable format"""
    if not workflow_data:
        return ["No workflow data available"]
    
    steps = []
    for step in workflow_data:
        if isinstance(step, dict):
            step_type = step.get("type", "system")
            content = step.get("content", "")
            timestamp = step.get("timestamp", "")
            
            if step_type == "system":
                icon = "⚙️"
                step_class = "system"
            elif step_type == "action":
                icon = "🔧"
                step_class = "action"
            elif step_type == "query":
                icon = "❓"
                step_class = "query"
            elif step_type == "result":
                icon = "✅"
                step_class = "result"
            else:
                icon = "➡️"
                step_class = "system"
            
            step_text = f"{icon} {content}"
            if timestamp:
                step_text += f" <small>({timestamp})</small>"
            
            steps.append({
                "text": step_text,
                "class": step_class
            })
        else:
            steps.append({
                "text": f"➡️ {step}",
                "class": "system"
            })
    return steps

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
        
        if st.session_state.active_agents[selected_agent]:
            # Call the appropriate backend
            backend_response = call_agent_backend(selected_agent, user_input)
            
            # Format workflow steps from backend
            workflow_steps = format_workflow_steps(backend_response.get("workflow", []))
            
            # Create an interaction record
            interaction = {
                "timestamp": datetime.now().isoformat(),
                "agent": selected_agent,
                "user_input": user_input,
                "response": {
                    "title": f"{selected_agent} Response",
                    "content": backend_response.get("message", "Processing your request..."),
                    "confidence": backend_response.get("confidence", 0.9),
                    "workflow_steps": workflow_steps,
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
            st.warning(f"{selected_agent} is currently inactive. Please activate it in the configuration.")

# Page Title
st.title("📊 AI Agent Interaction Dashboard")

# Swapped layout: LEFT = Confidence + Interactions, RIGHT = Agent Overview
col1, col2 = st.columns([2, 1])

# ... (keep all the previous code until the column definitions) ...

# Swapped layout: LEFT = Interactions, RIGHT = Agent Overview + Confidence
col1, col2 = st.columns([2, 1])

# LEFT COLUMN: Interactions
with col1:
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

            # Workflow process
            with st.expander(f"{config['thought_icon']} Agent Workflow"):
                if response.get("workflow_steps"):
                    for step in response["workflow_steps"]:
                        st.markdown(f"""
                            <div class="workflow-step {step['class']}">
                                {step['text']}
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No workflow data available for this interaction.")
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

# ... (keep the rest of the code the same) ...
# Debug Raw Interaction Data
with st.expander("🔍 Debug: Raw Interaction Data"):
    if st.session_state.interactions:
        st.write(st.session_state.interactions)
    else:
        st.write("No data yet.")