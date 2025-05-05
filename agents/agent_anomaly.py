from pymongo import MongoClient
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Union, Optional

# MongoDB Connection
def connect_to_mongodb(connection_string, db_name, collection_name):
    """Connect to MongoDB and return the specified collection"""
    client = MongoClient(connection_string)
    db = client[db_name]
    return db[collection_name]

# Fetch student data from MongoDB
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

class StudentAnomalyDetector:
    def __init__(self, student_data: Dict):
        self.data = student_data
        self.anomalies = []
        self.revision_subjects = {}  # Track subjects needing revision

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
                # Add to revision list with reason and severity
                self.revision_subjects[subj] = {
                    "reason": "significant score drop",
                    "severity": "high" if drop > 0.3 else "medium",
                    "current_score": current
                }

    def _check_attendance_low(self) -> None:
        """Flag subjects with attendance <85%"""
        for subj, att in zip(self.data['subjects'], self.data['attendance']):
            if att < 85:
                self.anomalies.append(
                    f"⏰ Low Attendance: {subj} has only {att}% attendance"
                )
                # Low attendance may indicate need for revision
                if subj not in self.revision_subjects:
                    self.revision_subjects[subj] = {
                        "reason": "poor attendance",
                        "severity": "medium" if att < 75 else "low",
                        "attendance": att
                    }

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
                # Subject is difficult for student, may need revision
                if subj not in self.revision_subjects:
                    self.revision_subjects[subj] = {
                        "reason": "efficiency issues",
                        "severity": "medium",
                        "time_per_lesson": avg
                    }

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
                # High priority for revision if far from target
                severity = "high" if (target - current) > 20 else "medium"
                self.revision_subjects[subj] = {
                    "reason": "below target score",
                    "severity": severity,
                    "gap": target - current,
                    "current_score": current
                }
    
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

    def get_revision_recommendations(self) -> str:
        """Generate recommendations for subjects needing revision"""
        if not self.revision_subjects:
            return "✅ Great job! You're on track with all subjects."
        
        # Sort subjects by severity
        high_priority = []
        medium_priority = []
        low_priority = []
        
        for subject, details in self.revision_subjects.items():
            if details["severity"] == "high":
                high_priority.append((subject, details))
            elif details["severity"] == "medium":
                medium_priority.append((subject, details))
            else:
                low_priority.append((subject, details))
        
        recommendations = [
            f"REVISION RECOMMENDATIONS FOR {self.data['student_name']}",
            "="*50,
            "\n🔴 HIGH PRIORITY SUBJECTS:"
        ]
        
        if high_priority:
            for subj, details in high_priority:
                reason = details["reason"]
                if "current_score" in details:
                    score_info = f" (Current score: {details['current_score']}%)"
                else:
                    score_info = ""
                recommendations.append(f"  • {subj}: {reason.capitalize()}{score_info}")
        else:
            recommendations.append("  No high priority subjects")
        
        recommendations.append("\n🟠 MEDIUM PRIORITY SUBJECTS:")
        if medium_priority:
            for subj, details in medium_priority:
                recommendations.append(f"  • {subj}: {details['reason'].capitalize()}")
        else:
            recommendations.append("  No medium priority subjects")
            
        recommendations.append("\n🟢 LOW PRIORITY SUBJECTS:")
        if low_priority:
            for subj, details in low_priority:
                recommendations.append(f"  • {subj}: {details['reason'].capitalize()}")
        else:
            recommendations.append("  No low priority subjects")
        
        recommendations.append("\nACTION STEPS:")
        if high_priority:
            for subj, _ in high_priority[:2]:  # Top 2 high priority subjects
                recommendations.append(f"  1. Schedule immediate revision sessions for {subj}")
                
        if len(self.revision_subjects) > 0:
            recommendations.append(f"  2. Review your study schedule to allocate more time to priority subjects")
            recommendations.append(f"  3. Consider seeking help from your teacher for difficult topics")
        
        return "\n".join(recommendations)

    def get_anomaly_report(self) -> str:
        """Generate formatted report"""
        if not self.anomalies:
            return "✅ No anomalies detected"
        
        report = "\n".join([
            f"ANOMALY REPORT for {self.data['student_name']} (ID:{self.data['student_id']})",
            "="*50,
            *self.anomalies,
            f"\nTotal anomalies found: {len(self.anomalies)}"
        ])
        
        # Add revision recommendations
        report += "\n\n" + self.get_revision_recommendations()
        
        return report


# Example Usage with MongoDB
if __name__ == "__main__":
    # MongoDB connection details
    CONNECTION_STRING = "mongodb://localhost:27017/"
    DB_NAME = "student_db"
    COLLECTION_NAME = "performance_data"
    
    # Connect to MongoDB
    collection = connect_to_mongodb(CONNECTION_STRING, DB_NAME, COLLECTION_NAME)
    
    # Option 2: Run anomaly detection for all students
    all_students = fetch_student_data(collection)
    for student in all_students:
        detector = StudentAnomalyDetector(student)
        print(detector.detect_all_anomalies())
        print("\n" + "="*60 + "\n")  # Separator between reports
