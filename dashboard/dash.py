import streamlit as st

# Apply custom CSS for styling
st.markdown("""
    <style>
        .main {
            background-color: #f0f4f8;
        }
        .sidebar .sidebar-content {
            background-color: #34495e;
            color: white;
            padding: 1rem;
        }
        .sidebar .sidebar-content h1 {
            color: #ecf0f1;
        }
        h1 {
            color: #2c3e50;
            font-size: 2.5rem;
        }
        h2 {
            color: #16a085;
            font-size: 2rem;
        }
        .stRadio > label {
            font-size: 18px;
            font-weight: bold;
            color: #34495e;
        }
        .stButton button {
            background-color: #1abc9c;
            color: white;
            font-size: 18px;
            padding: 10px 20px;
            border-radius: 5px;
            border: none;
        }
        .stButton button:hover {
            background-color: #16a085;
        }
        .stMarkdown {
            color: #34495e;
            font-size: 1.1rem;
            font-family: 'Arial', sans-serif;
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar with emojis/icons
page = st.sidebar.radio(
    "🤖 Choose Your Assistant",
    ["💰 Financial Crew", "🎓 EduMentor", "🧘 Wellness Bot"],
    key="assistant_selection"
)

# Clean and engaging content rendering based on sidebar selection
if page == "💰 Financial Crew":
    st.title("💰 Financial Crew")
    st.write("Welcome to your personal finance assistant. Here's how we can help:")
    st.write("""
        - Track your spending and savings
        - Set financial goals
        - Budgeting tools and resources
    """)
    st.button("Get Started", on_click=lambda: st.write("Let's take control of your finances!"))

elif page == "🎓 EduMentor":
    st.title("🎓 EduMentor")
    st.write("Your academic guide and study planner. Here's what I can help with:")
    st.write("""
        - Create a personalized study schedule
        - Study resources and tips
        - Track academic progress and performance
    """)
    st.button("Let's Improve Your Grades!", on_click=lambda: st.write("Study smart, not hard!"))

elif page == "🧘 Wellness Bot":
    st.title("🧘 Wellness Bot")
    st.write("Your mental and physical well-being assistant. I can help with:")
    st.write("""
        - Guided relaxation exercises
        - Fitness routines and tips
        - Stress management techniques
    """)
    st.button("Start Your Wellness Journey", on_click=lambda: st.write("Take a deep breath, you're in good hands!"))

