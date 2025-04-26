import pandas as pd
import streamlit as st 
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import plotly.graph_objects as go
from streamlit_extras.metric_cards import style_metric_cards

# StudentAnomalyDetector class (from your original code)
class StudentAnomalyDetector:
    def __init__(self, student_data: dict):
        self.data = student_data
        self.anomalies = []

    def detect_all_anomalies(self):
        """Run all anomaly checks and return results"""
        self._check_quiz_score_drops()
        self._check_attendance_low()
        self._check_time_management()
        self._check_progress_deviation()
        self._check_session_time_gaps()
        return self.get_anomaly_report()

    def _check_quiz_score_drops(self) -> None:
        """Detect >20% drop between last_week_scores and current quiz_scores"""
        for subj, last, current in zip(
            self.data['subjects'],
            self.data['last_week_scores'],
            self.data['quiz_scores']
        ):
            if last == 0:
                continue  # Avoid division by zero
            drop = (last - current) / last
            if drop > 0.2:
                self.anomalies.append(
                    f"📉 Score Drop: {subj} score dropped by {drop:.0%} "
                    f"(from {last} to {current})"
                )

    def _check_attendance_low(self) -> None:
        """Flag subjects with attendance <85%"""
        for subj, att in zip(self.data['subjects'], self.data['attendance']):
            if att < 85:
                self.anomalies.append(
                    f"⏰ Low Attendance: {subj} has only {att}% attendance"
                )

    def _check_time_management(self) -> None:
        """Identify subjects with high time spent but low lessons done"""
        avg_time_per_lesson = [
            t/l if l > 0 else 0 
            for t, l in zip(
                self.data['time_spent'], 
                self.data['lessons_done']
            )
        ]
        
        threshold = np.percentile(avg_time_per_lesson, 75)  # Top 25% slowest
        for subj, avg, time, lessons in zip(
            self.data['subjects'],
            avg_time_per_lesson,
            self.data['time_spent'],
            self.data['lessons_done']
        ):
            if avg > threshold:
                self.anomalies.append(
                    f"🐌 Time Sink: {subj} takes {avg:.1f} mins/lesson "
                    f"(total {time} mins for {lessons} lessons)"
                )

    def _check_progress_deviation(self) -> None:
        """Compare current scores to target scores"""
        for subj, current, target in zip(
            self.data['subjects'],
            self.data['quiz_scores'],
            self.data['target_scores']
        ):
            if current < target - 10:  # 10 points below target
                self.anomalies.append(
                    f"🎯 Off Target: {subj} is {target-current} points "
                    f"below target ({current} vs {target})"
                )
    
    def _check_session_time_gaps(self) -> None:
        """Detect unusually large gaps between study sessions"""
        if 'last_session_time' not in self.data or 'current_session_time' not in self.data:
            return
            
        last_session = datetime.strptime(self.data['last_session_time'], '%Y-%m-%d %H:%M:%S')
        current_session = datetime.strptime(self.data['current_session_time'], '%Y-%m-%d %H:%M:%S')
        
        gap = current_session - last_session
        if gap > timedelta(days=3):  # 3 days threshold for large gap
            self.anomalies.append(
                f"⏳ Large Time Gap: {gap.days} days between sessions "
                f"(last: {last_session.date()}, current: {current_session.date()})"
            )
            # Trigger mock alert message
            self.anomalies.append("🚨 ALERT: Student may need re-engagement!")            

    def get_anomaly_report(self) -> str:
        """Generate formatted report"""
        if not self.anomalies:
            return "✅ No anomalies detected"
        return "\n".join([
            f"ANOMALY REPORT for {self.data['student_name']} (ID:{self.data['student_id']})",
            "="*50,
            *self.anomalies,
            f"\nTotal anomalies found: {len(self.anomalies)}"
        ])

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

    

    # Sample Data
    default_data = {
        'student_id': 1,
        'student_name': 'John Doe',
        'subjects': ['Math', 'Science', 'English', 'History', 'Geography', 'Art'],
        'time_spent': [45, 60, 30, 50, 40, 35],
        'lessons_done': [2, 3, 1, 4, 2, 3],
        'total_lessons': [10, 10, 10, 10, 10, 10],
        'quiz_scores': [85, 92, 78, 85, 88, 90],
        'next_week_score': [88, 95, 80, 90, 92, 93],
        'attendance': [90, 95, 85, 100, 92, 88],
        'last_week_scores': [82, 88, 75, 80, 85, 87],
        'target_scores': [90, 95, 85, 90, 90, 92],
        'last_session_time': '2023-05-01 14:30:00',
        'current_session_time': '2023-05-05 15:45:00'
    }

    # Use the default data without any input modifications
    data = default_data.copy()  # This uses all the default values


    # Create DataFrame for visualizations
    df = pd.DataFrame({
        'subject': data['subjects'],
        'time_spent': data['time_spent'],
        'lessons_done': data['lessons_done'],
        'total_lessons': [10] * len(data['subjects']),  # Assuming 10 lessons per subject
        'quiz_scores': data['quiz_scores'],
        'next_week_score': [s + 3 for s in data['quiz_scores']],  # Simulated next week scores
        'attendance': data['attendance'],
        'last_week_scores': data['last_week_scores'],
        'target_scores': data['target_scores']
    })

    # Main content
    # Main title at the top of the page
    st.markdown("<div class='main-header'><h1>GURUKUL</h1></div>", unsafe_allow_html=True)

    # Student Profile Section
   
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
        
        for _, row in student_data.iterrows():
            name = student_data['student_name'] if 'student_name' in student_data else "Student"
            subject = row['subject']
            score = row['quiz_scores']
            time_spent = row['time_spent']
            lessons_done = row['lessons_done']

            if score < 80:
                if time_spent < 40:
                    rec = f"📌 {name} should spend more time on {subject} fundamentals (current: {time_spent} min)"
                    next_lesson = f"Core {subject} Concepts"
                else:
                    rec = f"📌 {name} needs targeted practice in {subject} (score: {score}%)"
                    next_lesson = f"{subject} Practice Exercises"
            elif lessons_done < row['total_lessons'] * 0.5:
                rec = f"📌 {name} should complete more {subject} lessons ({lessons_done}/{row['total_lessons']} done)"
                next_lesson = f"Continue {subject} Curriculum"
            else:
                if score >= 90:
                    rec = f"📌 {name} is excelling in {subject} - consider advanced material"
                    next_lesson = f"Advanced {subject} Topics"
                else:
                    rec = f"📌 {name} is progressing well in {subject} - reinforce learning"
                    next_lesson = f"{subject} Review & Application"

            recommendations.append({
                'Student': name,
                'Subject': subject,
                'Current Score': score,
                'Diagnosis': rec.split('📌 ')[1].split(' (')[0],
                'Recommended Lesson': next_lesson,
                'Priority': 'High' if score < 75 else 'Medium' if score < 85 else 'Low'
            })

        return pd.DataFrame(recommendations)

    # Generate and display recommendations
    recommendations_df = generate_recommendations(df)

    # Visualize recommendations
    st.markdown("## 🎯 Personalized Lesson Recommendations")
    tab1, tab2 = st.tabs(["📋 Recommendation List", "📊 Priority Matrix"])

    with tab1:
        st.dataframe(
            recommendations_df.style
            .applymap(lambda x: 'color: #e74c3c' if 'High' in str(x) else 
                                  ('color: #f39c12' if 'Medium' in str(x) else 
                                   'color: #2ecc71'),
                      subset=['Priority'])
            .set_properties(**{'font-size': '12pt'}),
            height=400,
            use_container_width=True
        )

    with tab2:
        fig = px.scatter(
            recommendations_df,
            x='Current Score',
            y='Priority',
            color='Subject',
            hover_name='Student',
            hover_data=['Diagnosis', 'Recommended Lesson'],
            symbol='Subject',
            title='Lesson Recommendation Priorities'
        )
        fig.update_layout(yaxis={'categoryorder':'array', 'categoryarray':['High','Medium','Low']})
        st.plotly_chart(fig, use_container_width=True)

    # Detailed explanation
    with st.expander("ℹ️ How recommendations are determined"):
        st.markdown("""
        
        - 🔴 **High Priority** (Score < 75%): Focus on foundational concepts
        - 🟠 **Medium Priority** (75% ≤ Score < 85%): Targeted practice
        - 🟢 **Low Priority** (Score ≥ 85%): Advanced/enrichment material

        
       
        """)

if __name__ == "__main__":
    main()
