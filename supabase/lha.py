import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import textwrap

# Load environment variables from .env file
load_dotenv()

# Set up Supabase using environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

class LearningAnalyzerAgent:
    def __init__(self):
        self.today = datetime.now().date()
    
    def get_all_student_ids(self) -> List[str]:
        """Fetch all unique student IDs from the database"""
        try:
            # Distinct student IDs from learning history
            response = supabase.table("learning_history").select("student_id", count="exact").execute()
            return list(set([item["student_id"] for item in response.data]))
        except Exception as e:
            print(f"Error fetching student IDs: {str(e)}")
            return []
    
    def get_learning_history(self, student_id: str, days_back: Optional[int] = None) -> List[Dict]:
        """Fetch learning history for a specific student with optional time filter"""
        try:
            query = supabase.table("learning_history").select("*").eq("student_id", student_id)
            
            if days_back:
                start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
                query = query.gte("created_at", start_date)
            
            response = query.order("created_at", desc=True).execute()
            return response.data
        except Exception as e:
            print(f"Error fetching learning history for student {student_id}: {str(e)}")
            return []
    
    def analyze_progress_trends(self, history: List[Dict]) -> Dict:
        """Analyze learning trends over time"""
        if not history:
            return {}
            
        weekly_progress = {}
        monthly_progress = {}
        
        for item in history:
            if not item.get("created_at"):
                continue
                
            completed_date = datetime.fromisoformat(item["created_at"]).date()
            week_key = f"{completed_date.year}-W{completed_date.isocalendar()[1]}"
            month_key = f"{completed_date.year}-{completed_date.month:02d}"
            
            weekly_progress[week_key] = weekly_progress.get(week_key, 0) + 1
            monthly_progress[month_key] = monthly_progress.get(month_key, 0) + 1
        
        return {"weekly": weekly_progress, "monthly": monthly_progress}
    
    def calculate_engagement_score(self, history: List[Dict]) -> float:
        """Calculate a score (0-100) representing student engagement"""
        if not history:
            return 0
            
        # Recent activity (last 7 days)
        recent_history = [h for h in history 
                        if h.get("created_at") and 
                        (self.today - datetime.fromisoformat(h["created_at"]).date()).days <= 7]
        
        # Consistency (days with activity in last 30 days)
        last_30_days = set()
        for h in history:
            if h.get("created_at"):
                date = datetime.fromisoformat(h["created_at"]).date()
                if (self.today - date).days <= 30:
                    last_30_days.add(date)
        
        consistency = len(last_30_days) / 30 * 100 if last_30_days else 0
        completed = sum(1 for h in history if h.get("status") == "completed")
        completion_rate = (completed / len(history)) * 100 if history else 0
        
        return min(100, consistency * 0.4 + len(recent_history) * 0.3 + completion_rate * 0.3)
    
    def generate_personalized_feedback(self, student_id: str, full_report: bool = False) -> Dict:
        """Generate comprehensive feedback for the student"""
        all_history = self.get_learning_history(student_id)
        recent_history = self.get_learning_history(student_id, days_back=30)
        
        completed_lessons = sum(1 for item in all_history if item.get("status") == "completed")
        total_lessons = len(all_history)
        completion_rate = (completed_lessons / total_lessons * 100) if total_lessons else 0
        
        engagement_score = self.calculate_engagement_score(all_history)
        trends = self.analyze_progress_trends(all_history)
        
        last_activity = max(
            (item.get("created_at") for item in all_history if item.get("created_at")),
            default=None
        )
        
        feedback = self._generate_feedback_text(
            student_id=student_id,
            completed_lessons=completed_lessons,
            total_lessons=total_lessons,
            completion_rate=completion_rate,
            engagement_score=engagement_score,
            last_activity=last_activity,
            trends=trends,
            recent_history=recent_history,
            full_report=full_report
        )
        
        return {
            "student_id": student_id,
            "completion_rate": round(completion_rate, 1),
            "engagement_score": round(engagement_score, 1),
            "completed_lessons": completed_lessons,
            "total_lessons": total_lessons,
            "last_activity": last_activity,
            "trends": trends,
            "feedback": feedback
        }
    
    def _generate_feedback_text(self, student_id: str, completed_lessons: int, total_lessons: int,
                              completion_rate: float, engagement_score: float, last_activity: Optional[str],
                              trends: Dict, recent_history: List[Dict], full_report: bool) -> str:
        """Generate human-readable feedback text"""
        if not last_activity:
            return textwrap.dedent(f"""
            Hello Student {student_id}! It looks like you haven't started your learning journey yet.
            We're excited to have you here! Would you like to begin with our introductory lessons?
            """)
        
        try:
            days_since_last = (self.today - datetime.fromisoformat(last_activity).date()).days
        except:
            days_since_last = 0
        
        progress_report = []
        
        if completed_lessons == total_lessons:
            progress_report.append(f"🌟 Congratulations! You've completed all {total_lessons} available lessons!")
        else:
            progress_report.append(
                f"You've completed {completed_lessons} out of {total_lessons} lessons ({completion_rate:.1f}%). "
                f"Keep up the good work!"
            )
        
        if engagement_score > 80:
            progress_report.append("Your learning engagement is excellent! You're consistently making progress.")
        elif engagement_score > 50:
            progress_report.append("You're making steady progress. Try to maintain this momentum!")
        else:
            progress_report.append("Consider spending more regular time on learning to improve your progress.")
        
        if days_since_last == 0:
            progress_report.append("Great job learning today! Daily practice leads to mastery.")
        elif days_since_last <= 3:
            progress_report.append(f"You were last active {days_since_last} days ago. Nice recent activity!")
        elif days_since_last <= 7:
            progress_report.append(f"It's been {days_since_last} days since your last activity. Ready for another session?")
        else:
            progress_report.append(f"It's been {days_since_last} days since your last activity. Let's get back on track!")
        
        if full_report:
            progress_report.append("\n📊 Detailed Progress Analysis:")
            progress_report.append(f"- Completed {len(recent_history)} lessons in the last 30 days")
            
            if trends.get("weekly"):
                last_week = max(trends["weekly"].keys())
                last_week_count = trends["weekly"][last_week]
                progress_report.append(f"- Completed {last_week_count} lessons last week ({last_week})")
            
            progress_report.append("\n💡 Suggested Next Steps:")
            if completion_rate < 50:
                progress_report.append("- Focus on completing more lessons to build foundational knowledge")
            elif completion_rate < 80:
                progress_report.append("- Review completed lessons and practice weaker areas")
            else:
                progress_report.append("- Challenge yourself with advanced materials or practical applications")
        
        return "\n".join(progress_report)

def main():
    analyzer = LearningAnalyzerAgent()
    
    # Get all student IDs from database
    student_ids = analyzer.get_all_student_ids()
    
    if not student_ids:
        print("No students found in the database.")
        return
    
    print(f"Found {len(student_ids)} students. Generating reports...\n")
    
    for student_id in student_ids:
        print(f"\nGenerating learning report for student {student_id}...")
        report = analyzer.generate_personalized_feedback(student_id, full_report=True)
        
        print("\n=== LEARNING PROGRESS REPORT ===")
        print(f"Student ID: {report['student_id']}")
        print(f"Completion Rate: {report['completion_rate']}%")
        print(f"Engagement Score: {report['engagement_score']}/100")
        print(f"Last Activity: {report['last_activity'] or 'Never'}")
        print("\nFEEDBACK:")
        print(report['feedback'])
        print("\n" + "="*40 + "\n")

if __name__ == "__main__":
    main()