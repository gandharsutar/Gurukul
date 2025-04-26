import pandas as pd
import streamlit as st 
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import plotly.graph_objects as go
from streamlit_extras.metric_cards import style_metric_cards
from pymongo import MongoClient

# MongoDB Connection Functions
def connect_to_mongodb(connection_string, db_name, collection_name):
    """Connect to MongoDB and return the specified collection"""
    client = MongoClient(connection_string)
    db = client[db_name]
    return db[collection_name]

def fetch_student_data(collection, student_id=None):
    """
    Fetch student data from MongoDB
    If student_id is provided, fetch only that student's data
    Otherwise, fetch all students
    """
    if student_id:
        return collection.find_one({"student_id": student_id})
    else:
        return list(collection.find({}))

# Main App
def main():
    # Set page config
    st.set_page_config(
        page_title=" Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS
    st.markdown("""
    <style>
        /* Main header */
        .main-header {
            text-align: center;
            color: #2c3e50;
            padding: 1rem;
            margin-bottom: 2rem;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* Student profile */
        .student-profile {
            display: flex;
            align-items: center;
            gap: 1.5rem;
            margin-bottom: 2rem;
            padding: 1.5rem;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .student-avatar {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: #3498db;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 2rem;
            font-weight: bold;
        }
        
        /* Card styling */
        .card {
            padding: 1.5rem;
            border-radius: 10px;
            background-color: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1.5rem;
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        
        /* Calendar event cards */
        .event-card {
            padding: 0.75rem;
            margin: 0.5rem 0;
            border-radius: 8px;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        /* Subject color mapping */
        .Math { color: #3498db; }
        .Science { color: #2ecc71; }
        .English { color: #e74c3c; }
        .History { color: #9b59b6; }
        .Geography { color: #f39c12; }
        .Art { color: #1abc9c; }
        
        /* Progress bars */
        .progress-container {
            width: 100%;
            background-color: #e0e0e0;
            border-radius: 5px;
            margin: 0.5rem 0;
        }
        
        .progress-bar {
            height: 20px;
            border-radius: 5px;
            background-color: #3498db;
            text-align: center;
            color: white;
            font-size: 12px;
            line-height: 20px;
        }
        
        /* Anomaly alerts */
        .anomaly-card {
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            background-color: #fff8e1;
            border-left: 4px solid #ffa000;
        }
        
        .critical-anomaly {
            background-color: #ffebee;
            border-left: 4px solid #f44336;
        }
        
        .warning-anomaly {
            background-color: #fff8e1;
            border-left: 4px solid #ffa000;
        }
        
        .info-anomaly {
            background-color: #e3f2fd;
            border-left: 4px solid #2196f3;
        }
    </style>
    """, unsafe_allow_html=True)

    # MongoDB Connection
    CONNECTION_STRING = "mongodb://localhost:27017/"
    DB_NAME = "student_db"
    COLLECTION_NAME = "performance_data"
    
    # Connect to MongoDB
    try:
        collection = connect_to_mongodb(CONNECTION_STRING, DB_NAME, COLLECTION_NAME)
        all_students = fetch_student_data(collection)
        
        if not all_students:
            st.error("No student data found in the database. Using sample data instead.")
            # Fall back to sample data if MongoDB is empty
            use_sample_data = True
        else:
            use_sample_data = False
            
            # Simply use the first student in the database
            data = all_students[0]
            
    except Exception as e:
        st.error(f"Error connecting to MongoDB: {e}. Using sample data instead.")
        use_sample_data = True

    # Sample Data (fallback)
    if use_sample_data:
        default_data = {
            'student_id': 1,
            'student_name': 'John Doe',
            'subjects': ['Math', 'Science', 'English', 'History', 'Geography', 'Art'],
            'time_spent': [45, 60, 30, 50, 40, 35],
            'lessons_done': [2, 3, 1, 4, 2, 3],
            'total_lessons': [10, 10, 10, 10, 10, 10],
            'quiz_scores': [85, 92, 78, 85, 88, 90],
            'attendance': [90, 95, 85, 100, 92, 88],
            'last_week_scores': [82, 88, 75, 80, 85, 87],
            'target_scores': [90, 95, 85, 90, 90, 92],
            'last_session_time': '2023-05-01 14:30:00',
            'current_session_time': '2023-05-05 15:45:00'
        }
        data = default_data

    # Display the main title
    st.markdown("<div class='main-header'><h1>GURUKUL</h1></div>", unsafe_allow_html=True)
    
    # Student Profile Section - removed ID from display
    st.markdown(f"<h2>Student Profile: {data['student_name']}</h2>", unsafe_allow_html=True)
    
    # Create DataFrame for visualizations
    df = pd.DataFrame({
        'subject': data['subjects'],
        'time_spent': data['time_spent'],
        'lessons_done': data['lessons_done'],
        'total_lessons': data['total_lessons'],
        'quiz_scores': data['quiz_scores'],
        'attendance': data['attendance'],
        'last_week_scores': data['last_week_scores'],
        'target_scores': data['target_scores']
    })
    
    # Add next_week_score - either from MongoDB or calculate it
    if 'next_week_score' in data and data['next_week_score']:
        df['next_week_score'] = data['next_week_score']
    else:
        # If not available, predict based on trend
        score_change = [(current - last) for current, last in zip(data['quiz_scores'], data['last_week_scores'])]
        df['next_week_score'] = [current + change for current, change in zip(data['quiz_scores'], score_change)]
    
    # Add student name to the dataframe for recommendations
    df['student_name'] = data['student_name']
    
    # Row 1: Key Metrics
    st.markdown("## 📊 Performance Overview")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_score = df['quiz_scores'].mean()
        last_week_avg = df['last_week_scores'].mean()
        st.metric(label="Average Score", value=f"{avg_score:.1f}%", delta=f"{(avg_score - last_week_avg):.1f}% from last week")
        
    with col2:
        target_avg = df['target_scores'].mean()
        st.metric(label="Target Score", value=f"{target_avg:.1f}%", delta=f"{(avg_score - target_avg):.1f}% to target")
        
    with col3:
        avg_time = df['time_spent'].mean()
        st.metric(label="Avg Study Time", value=f"{avg_time:.0f} mins", delta="+5 mins from last week")
        
    with col4:
        completion_rate = (df['lessons_done'].sum() / df['total_lessons'].sum()) * 100
        st.metric(label="Lesson Completion", value=f"{completion_rate:.1f}%", delta="+8% from last week")

    style_metric_cards()

    # Row 3: Detailed Metrics
    st.markdown("## 📚 Detailed Analysis")
    tab1, tab2, tab3, tab4 = st.tabs(["Time Analysis", "Score Comparison", "Attendance", "Progress"])

    with tab1:
        st.markdown("### Time Spent on Subjects")
        fig = px.bar(df, x='subject', y='time_spent', color='subject',
                     text='time_spent',
                     labels={'time_spent': 'Time Spent (minutes)', 'subject': 'Subject'},
                     color_discrete_map={
                         'Math': '#3498db',
                         'Science': '#2ecc71',
                         'English': '#e74c3c',
                         'History': '#9b59b6',
                         'Geography': '#f39c12',
                         'Art': '#1abc9c'
                     })
        fig.update_traces(texttemplate='%{text} min', textposition='outside')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown("### Score Comparison")
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df['subject'],
            y=df['last_week_scores'],
            name='Last Week',
            marker_color='#95a5a6'
        ))
        
        fig.add_trace(go.Bar(
            x=df['subject'],
            y=df['quiz_scores'],
            name='Current',
            marker_color='#3498db'
        ))
        
        fig.add_trace(go.Scatter(
            x=df['subject'],
            y=df['target_scores'],
            name='Target',
            mode='lines+markers',
            line=dict(color='#2ecc71', width=3),
            marker=dict(size=10)
        ))
        
        fig.update_layout(
            barmode='group',
            height=400,
            xaxis_title='Subject',
            yaxis_title='Score (%)',
            legend_title="Score Type"
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown("### Attendance by Subject")
        fig = px.bar(df, x='subject', y='attendance', color='subject',
                     text='attendance',
                     labels={'attendance': 'Attendance (%)', 'subject': 'Subject'},
                     color_discrete_map={
                         'Math': '#3498db',
                         'Science': '#2ecc71',
                         'English': '#e74c3c',
                         'History': '#9b59b6',
                         'Geography': '#f39c12',
                         'Art': '#1abc9c'
                     })
        fig.update_traces(texttemplate='%{text}%', textposition='outside')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.markdown("### Lesson Progress by Subject")
        df['progress'] = (df['lessons_done'] / df['total_lessons']) * 100
        
        for _, row in df.iterrows():
            st.markdown(f"<div class='{row['subject']}'><b>{row['subject']}</b></div>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class='progress-container'>
                <div class='progress-bar' style='width: {row['progress']}%; background-color: {'#2ecc71' if row['progress'] > 80 else '#f39c12' if row['progress'] > 50 else '#e74c3c'}'>
                    {row['lessons_done']}/{row['total_lessons']} ({row['progress']:.0f}%)
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Recommendations Section
    def generate_recommendations(student_data):
        recommendations = []
        
        # Check if student_data is a DataFrame or a dictionary
        if isinstance(student_data, pd.DataFrame):
            df_to_use = student_data
            student_name = student_data['student_name'].iloc[0] if 'student_name' in student_data else "Student"
        else:
            # If we got a dictionary, convert it to the same format as before
            df_to_use = pd.DataFrame({
                'subject': student_data['subjects'],
                'quiz_scores': student_data['quiz_scores'],
                'time_spent': student_data['time_spent'],
                'lessons_done': student_data['lessons_done'],
                'total_lessons': student_data['total_lessons'],
            })
            student_name = student_data.get('student_name', "Student")
            
        for _, row in df_to_use.iterrows():
            subject = row['subject']
            score = row['quiz_scores']
            time_spent = row['time_spent']
            lessons_done = row['lessons_done']
            total_lessons = row['total_lessons']

            # Calculate next chapter number based on lessons completed
            next_chapter = min(lessons_done + 1, total_lessons)
            
            if score < 80:
                if time_spent < 40:
                    rec = f"📌 {student_name} should spend more time on {subject} fundamentals (current: {time_spent} min)"
                    next_lesson = f"Core {subject} Concepts"
                else:
                    rec = f"📌 {student_name} needs targeted practice in {subject} (score: {score}%)"
                    next_lesson = f"{subject} Practice Exercises"
            elif lessons_done < total_lessons * 0.5:
                rec = f"📌 {student_name} should complete more {subject} lessons ({lessons_done}/{total_lessons} done)"
                next_lesson = f"Continue {subject} Curriculum"
            else:
                if score >= 90:
                    rec = f"📌 {student_name} is excelling in {subject} - consider advanced material"
                    next_lesson = f"Advanced {subject} Topics"
                else:
                    rec = f"📌 {student_name} is progressing well in {subject} - reinforce learning"
                    next_lesson = f"{subject} Review & Application"

            recommendations.append({
                'Subject': subject,
                'Current Score': score,
                'Recommended Lesson': next_lesson,
                'Chapter': f"Chapter {next_chapter}",
                'Priority': 'High' if score < 75 else 'Medium' if score < 85 else 'Low'
            })

        return pd.DataFrame(recommendations)

    # Generate and display recommendations
    recommendations_df = generate_recommendations(df)

    # Visualize recommendations
    st.markdown("## 🎯 Personalized Lesson Recommendations")
    
    # Create a priority value map to sort by priority
    priority_map = {'High': 1, 'Medium': 2, 'Low': 3}
    
    # Add a numeric priority column for sorting
    recommendations_df['priority_value'] = recommendations_df['Priority'].map(priority_map)
    
    # Sort by priority (high to low) and then by score (low to high) to find the most important lesson
    sorted_recommendations = recommendations_df.sort_values(by=['priority_value', 'Current Score'], 
                                                          ascending=[True, True])
    
    # Get the highest priority lesson
    next_lesson = sorted_recommendations.iloc[0]
    
    # Create three tabs: Next Lesson, Recommendation List, and Priority Matrix
    tab1, tab2, tab3 = st.tabs(["📋 Recommendation List","📊 Priority Matrix","📚 Next Lesson"])

    with tab1:
        # Show the complete recommendation list
        # Add index starting from 1 instead of 0
        recommendations_df_display = recommendations_df.copy()
        recommendations_df_display.index = range(1, len(recommendations_df_display) + 1)
        
        # Reorder columns to show Chapter after Recommended Lesson
        column_order = ['Subject', 'Current Score', 'Recommended Lesson', 'Chapter', 'Priority']
        recommendations_df_display = recommendations_df_display[column_order]
        
        st.dataframe(
            recommendations_df_display.style
            .applymap(lambda x: 'color: #e74c3c' if 'High' in str(x) else 
                                  ('color: #f39c12' if 'Medium' in str(x) else 
                                   'color: #2ecc71'),
                      subset=['Priority'])
            .set_properties(**{'font-size': '12pt'}),
            height=400,  # Restored full height for the standalone table
            use_container_width=True
        )

    with tab2:
        fig = px.scatter(
            recommendations_df,
            x='Current Score',
            y='Priority',
            color='Subject',
            symbol='Subject',
            size=[70] * len(recommendations_df),  # Make all points the same larger size
            hover_data={
                'Subject': True,
                'Current Score': True,
                'Recommended Lesson': True,
                'Chapter': True,
                'Priority': True
            },
            title='Lesson Recommendation Priorities'
        )
        fig.update_layout(
            yaxis={'categoryorder':'array', 'categoryarray':['High','Medium','Low']},
            height=400,
            showlegend=True,
            legend_title="Subject"
        )
        st.plotly_chart(fig, use_container_width=True)
    with tab3:
        # Show the next lesson recommendation
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown(
                f"""
                <div style="background-color: {'#ffebee' if next_lesson['Priority'] == 'High' else '#fff8e1' if next_lesson['Priority'] == 'Medium' else '#e8f5e9'}; 
                            padding: 20px; 
                            border-radius: 10px;
                            border-left: 5px solid {'#e53935' if next_lesson['Priority'] == 'High' else '#ffb300' if next_lesson['Priority'] == 'Medium' else '#43a047'};
                            text-align: center;">
                    <h3>Suggested Next Lesson</h3>
                    <h4>{next_lesson['Recommended Lesson']}</h4>
                    <h5>{next_lesson['Chapter']}</h5>
                    <p>Subject: <b>{next_lesson['Subject']}</b></p>
                    <p>Current Score: <b>{next_lesson['Current Score']}%</b></p>
                    <p>Priority: <b>{next_lesson['Priority']}</b></p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown(
                f"""
                <div style="background-color: #f5f5f5; 
                            padding: 20px; 
                            border-radius: 10px;
                            height: 100%;">
                    <h3>Why This Lesson?</h3>
                    <p>This lesson was selected because it's the highest priority based on:</p>
                    <ul>
                        <li>Current performance scores</li>
                        <li>Priority level classification</li>
                        <li>Subject progression needs</li>
                    </ul>
                    <p>{'Focus on building a strong foundation in this subject area.' if next_lesson['Priority'] == 'High' else 
                        'Strengthen your understanding with targeted practice.' if next_lesson['Priority'] == 'Medium' else 
                        'Extend your knowledge with advanced concepts.'}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )


    
    # Detailed explanation
    with st.expander("ℹ️ How recommendations are determined"):
        st.markdown("""
        
        - 🔴 **High Priority** (Score < 75%): Focus on foundational concepts
        - 🟠 **Medium Priority** (75% ≤ Score < 85%): Targeted practice
        - 🟢 **Low Priority** (Score ≥ 85%): Advanced/enrichment material

        
       
        """)

if __name__ == "__main__":
    main()
