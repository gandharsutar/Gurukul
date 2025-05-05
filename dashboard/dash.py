import streamlit as st


# Apply some custom CSS
st.markdown("""
    <style>
        .main {
            background-color: #f8f9fa;
        }
        .sidebar .sidebar-content {
            background-color: #e9ecef;
            padding: 1rem;
        }
        h1 {
            color: #2c3e50;
        }
        .stRadio > label {
            font-size: 18px;
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar selection with emojis/icons
page = st.sidebar.radio(
    "🤖 Choose Your Assistant",
    ["💰 Financial Crew", "🎓 EduMentor", "🧘 Wellness Bot"]
)

# Clean header rendering
if page == "💰 Financial Crew":
    st.title("💰 Financial Crew")
    st.write("Welcome to your personal finance assistant. Let's manage your money wisely!")

elif page == "🎓 EduMentor":
    st.title("🎓 EduMentor")
    st.write("Your academic guide and study planner. Let's boost those grades!")

elif page == "🧘 Wellness Bot":
    st.title("🧘 Wellness Bot")
    st.write("Here to support your mental and physical well-being. Breathe, relax, and thrive.")
