from pymongo import MongoClient
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from datetime import datetime

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["student_db"]
collection = db["subject_history"]

def prepare_training_data():
    """Prepare training data from all students for the prediction model"""
    all_students = list(collection.find({}))
    
    X = []
    y = []
    
    for student in all_students:
        for subject in student["subjects"]:
            features = [
                subject["lessons_done"],
                subject["time_spent"],
                subject["attendance"],
                subject["last_week_score"],
                (datetime.now() - subject.get("last_study_date", datetime.now())).days
            ]
            target = subject["quiz_score"]
            
            X.append(features)
            y.append(target)
    
    return np.array(X), np.array(y)

def train_prediction_model(X, y):
    """Train a machine learning model to predict quiz scores"""
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate model (simplified for example)
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    print(f"Model trained - Train R²: {train_score:.2f}, Test R²: {test_score:.2f}")
    
    return model, scaler

def predict_future_performance(model, scaler, student_data):
    """Predict future performance for each subject"""
    predictions = {}
    
    for subject in student_data["subjects"]:
        features = np.array([
            subject["lessons_done"],
            subject["time_spent"],
            subject["attendance"],
            subject["quiz_score"],  # Using current score as last week's for prediction
            0  # Assuming they study today
        ]).reshape(1, -1)
        
        scaled_features = scaler.transform(features)
        predicted_score = model.predict(scaled_features)[0]
        predictions[subject["name"]] = max(0, min(100, predicted_score))
    
    return predictions

def generate_ai_feedback(data, predictions):
    """Generate AI-powered feedback with predictions and personalized recommendations"""
    print(f"\nAI-Powered Feedback Report for {data['student_name']} (ID: {data['student_id']})\n")
    
    for subject in data["subjects"]:
        name = subject["name"]
        progress = subject["lessons_done"] / subject["total_lessons"] * 100
        current_score = subject["quiz_score"]
        predicted_score = predictions[name]
        score_diff = subject["target_score"] - current_score
        score_trend = current_score - subject["last_week_score"]
        
        print(f"Subject: {name}")
        print(f" - Progress: {subject['lessons_done']}/{subject['total_lessons']} ({progress:.1f}%)")
        print(f" - Current Score: {current_score} (Last week: {subject['last_week_score']}, Trend: {score_trend:+})")
        print(f" - Predicted Next Score: {predicted_score:.1f}")
        print(f" - Target Score: {subject['target_score']}")
        
        # AI-generated insights
        if predicted_score < current_score:
            print("   ⚠️ Prediction: Your score may decrease next week without changes")
        elif predicted_score > current_score + 5:
            print("   📈 Prediction: Significant improvement expected!")
        else:
            print("   ➡️ Prediction: Steady performance expected")
            
        # Personalized recommendations
        if progress < 50 and current_score < subject["target_score"]:
            print("   💡 Recommendation: Focus on completing more lessons to improve fundamentals")
        elif subject["time_spent"] < 120:  # Less than 2 hours
            print("   💡 Recommendation: Increase study time to at least 2 hours per week")
        elif subject["attendance"] < 90:
            print("   💡 Recommendation: Higher attendance will likely improve your scores")
        elif score_diff > 10:
            print("   💡 Recommendation: Consider additional practice tests to close the gap")
        else:
            print("   💡 Recommendation: Maintain your current study habits")
        
        print()

# Main execution
if __name__ == "__main__":
    # Train the model (in a real app, this would be done separately and saved)
    X, y = prepare_training_data()
    if len(X) > 10:  # Only train if we have enough data
        model, scaler = train_prediction_model(X, y)
    else:
        print("Insufficient training data - using simple heuristics")
        model, scaler = None, None
    
    # Get student data
    student_id = int(input("Enter student ID: "))
    student_data = collection.find_one({"student_id": student_id})
    
    if student_data:
        if model:
            predictions = predict_future_performance(model, scaler, student_data)
            generate_ai_feedback(student_data, predictions)
        else:
            # Fallback to simpler feedback if no model
            print("\nUsing basic feedback (not AI-powered)")
            generate_feedback(student_data)
    else:
        print("Student not found in database.")