import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Union, Optional

class StudentAnomalyDetector:
    def __init__(self, student_data: Dict):
        self.data = student_data
        self.anomalies = []

    def detect_all_anomalies(self) :
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


# Example Usage
student_data = {
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
    'target_scores': [90, 95, 85, 90, 90, 92]
}

detector = StudentAnomalyDetector(student_data)
print(detector.detect_all_anomalies())