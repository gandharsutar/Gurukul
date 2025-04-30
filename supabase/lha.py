from pymongo import MongoClient
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
from sklearn.metrics import mean_squared_error
import joblib
import os

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["student_db"]
collection = db["subject_history"]
model_collection = db["ai_models"]

MODEL_SAVE_PATH = "ai_models/"
os.makedirs(MODEL_SAVE_PATH, exist_ok=True)

def prepare_training_data(update_model=False):
    """Prepare training data with time-series features"""
    all_students = list(collection.find({}))
    
    X = []
    y = []
    student_ids = []
    timestamps = []
    
    for student in all_students:
        for subject in student["subjects"]:
            if "history" in subject and len(subject["history"]) > 1:
                # Create time-series features from historical data
                for i in range(1, len(subject["history"])):
                    prev = subject["history"][i-1]
                    current = subject["history"][i]
                    
                    features = [
                        current["lessons_done"],
                        current["time_spent"],
                        current["attendance"],
                        prev["quiz_score"],  # Last week's score
                        (datetime.strptime(current["date"], "%Y-%m-%d") - 
                         datetime.strptime(prev["date"], "%Y-%m-%d")).days,
                        np.mean([h["quiz_score"] for h in subject["history"][:i]]),  # Moving average
                        subject["target_score"] - prev["quiz_score"],  # Gap to target
                        i  # Week number
                    ]
                    
                    target = current["quiz_score"]
                    
                    X.append(features)
                    y.append(target)
                    student_ids.append(student["student_id"])
                    timestamps.append(current["date"])
    
    if not X:
        return None, None, None, None
    
    X = np.array(X)
    y = np.array(y)
    
    if update_model or not os.path.exists(f"{MODEL_SAVE_PATH}scaler.pkl"):
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        joblib.dump(scaler, f"{MODEL_SAVE_PATH}scaler.pkl")
    else:
        scaler = joblib.load(f"{MODEL_SAVE_PATH}scaler.pkl")
        X_scaled = scaler.transform(X)
    
    return X_scaled, y, student_ids, timestamps

def train_or_load_model(force_retrain=False):
    """Train or load the prediction model with versioning"""
    model_version = "1.0"
    model_file = f"{MODEL_SAVE_PATH}model_v{model_version}.pkl"
    
    if not force_retrain and os.path.exists(model_file):
        model = joblib.load(model_file)
        scaler = joblib.load(f"{MODEL_SAVE_PATH}scaler.pkl")
        return model, scaler, model_version
    
    X, y, _, _ = prepare_training_data(update_model=True)
    
    if X is None:
        raise ValueError("Insufficient data to train model")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)
    train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
    test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
    
    print(f"Model trained - Version {model_version}")
    print(f"Train RMSE: {train_rmse:.2f}, Test RMSE: {test_rmse:.2f}")
    
    # Save model
    joblib.dump(model, model_file)
    
    # Store model metadata in MongoDB
    model_collection.update_one(
        {"version": model_version},
        {"$set": {
            "version": model_version,
            "train_rmse": train_rmse,
            "test_rmse": test_rmse,
            "train_size": len(X_train),
            "test_size": len(X_test),
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "features": [
                "lessons_done", "time_spent", "attendance", 
                "last_week_score", "days_since_last", 
                "moving_avg_score", "target_gap", "week_number"
            ]
        }},
        upsert=True
    )
    
    return model, joblib.load(f"{MODEL_SAVE_PATH}scaler.pkl"), model_version

def predict_with_confidence(model, scaler, student_data):
    """Predict performance with confidence intervals using tree variance"""
    predictions = {}
    
    for subject in student_data["subjects"]:
        # Get historical data if available
        history = subject.get("history", [])
        last_record = history[-1] if history else subject
        
        # Prepare features
        features = [
            last_record["lessons_done"],
            last_record["time_spent"],
            last_record["attendance"],
            last_record["quiz_score"],
            7,  # Assuming 1 week since last record
            np.mean([h["quiz_score"] for h in history]) if history else last_record["quiz_score"],
            subject["target_score"] - last_record["quiz_score"],
            len(history) + 1
        ]
        
        scaled_features = scaler.transform([features])
        
        # Get predictions from all trees
        individual_predictions = [tree.predict(scaled_features)[0] 
                                for tree in model.estimators_]
        
        mean_pred = np.mean(individual_predictions)
        std_pred = np.std(individual_predictions)
        
        predictions[subject["name"]] = {
            "predicted_score": max(0, min(100, mean_pred)),
            "confidence_interval": (
                max(0, mean_pred - 1.96 * std_pred),
                min(100, mean_pred + 1.96 * std_pred)
            ),
            "improvement_prob": np.mean(
                [1 if pred > last_record["quiz_score"] else 0 
                 for pred in individual_predictions]
            )
        }
    
    return predictions

def generate_basic_feedback(data):
    """Basic feedback generator without AI predictions"""
    print(f"\nBasic Feedback Report for {data['student_name']} (ID: {data['student_id']})\n")

    for subject in data["subjects"]:
        name = subject["name"]
        progress = subject["lessons_done"] / subject["total_lessons"] * 100
        score_diff = subject["target_score"] - subject["quiz_score"]
        score_trend = subject["quiz_score"] - subject["last_week_score"]

        print(f"Subject: {name}")
        print(f" - Lessons Completed: {subject['lessons_done']}/{subject['total_lessons']} ({progress:.1f}%)")
        print(f" - Time Spent: {subject['time_spent']} minutes")
        print(f" - Attendance: {subject['attendance']}%")
        print(f" - Quiz Score: {subject['quiz_score']} (Last week: {subject['last_week_score']}, Change: {score_trend:+})")

        if progress < 30:
            print("   ⚠️ Try to complete more lessons to keep up.")
        if subject["attendance"] < 85:
            print("   ⚠️ Attendance is low. Try to attend classes more consistently.")
        if score_diff > 5:
            print(f"   📈 Aim to improve your score by {score_diff} points to meet your target.")
        elif score_diff <= 5 and score_diff > 0:
            print("   ✅ You're close to your target score—keep it up!")
        else:
            print("   🎉 You've reached or exceeded your target score!")

        print()

def generate_dynamic_feedback(data, predictions):
    """Generate AI-powered feedback with predictions and personalized recommendations"""
    print(f"\nAI-Powered Feedback Report for {data['student_name']} (ID: {data['student_id']})\n")
    print("📊 Performance Overview:")
    
    overall_trend = 0
    subjects_below_target = 0
    total_subjects = len(data["subjects"])
    
    for subject in data["subjects"]:
        name = subject["name"]
        pred = predictions[name]
        current_score = subject["quiz_score"]
        target = subject["target_score"]
        progress = subject["lessons_done"] / subject["total_lessons"] * 100
        
        if current_score < target:
            subjects_below_target += 1
        
        trend = pred["predicted_score"] - current_score
        overall_trend += trend
        
        print(f"\n📚 Subject: {name}")
        print(f"   Current Score: {current_score}")
        print(f"   Predicted Next Score: {pred['predicted_score']:.1f}")
        print(f"   Confidence Range: {pred['confidence_interval'][0]:.1f}-{pred['confidence_interval'][1]:.1f}")
        print(f"   Target Score: {target}")
        print(f"   Improvement Probability: {pred['improvement_prob']*100:.1f}%")
        print(f"   Progress: {progress:.1f}% complete")
        
        # Generate dynamic recommendations
        recommendations = []
        
        # Progress-based recommendations
        if progress < 50:
            recommendations.append(f"Increase lesson completion (currently {progress:.1f}%)")
        
        # Score-based recommendations
        if pred["improvement_prob"] < 0.4:
            recommendations.append("Focus on weak areas identified in last quiz")
            if subject["time_spent"] < 120:
                recommendations.append("Increase study time by at least 30 minutes daily")
        
        # Attendance-based
        if subject["attendance"] < 85:
            recommendations.append("Improve attendance (currently {}%)".format(subject["attendance"]))
        
        # Time management
        if subject["time_spent"] > 300 and pred["improvement_prob"] < 0.6:
            recommendations.append("Consider studying more effectively rather than longer")
        
        # Target gap
        if (target - current_score) > 15:
            recommendations.append("Break target into smaller weekly goals")
        
        # Print recommendations if any
        if recommendations:
            print("   💡 Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"      {i}. {rec}")
    
    # Overall summary
    print("\n🌟 Overall Summary:")
    avg_trend = overall_trend / total_subjects
    if avg_trend > 5:
        print(f"   ➕ Strong positive trend predicted (+{avg_trend:.1f} points average improvement)")
    elif avg_trend < -2:
        print(f"   ⚠️ Caution: Negative trend predicted ({avg_trend:.1f} points average decline)")
    else:
        print("   ➡️ Stable performance predicted overall")
    
    if subjects_below_target > 0:
        print(f"   🎯 Focus needed: {subjects_below_target}/{total_subjects} subjects below target")
    else:
        print("   ✅ All subjects at or above target score!")
    
    # Time management analysis
    total_study_time = sum(s["time_spent"] for s in data["subjects"])
    avg_study_per_subject = total_study_time / total_subjects
    
    print(f"\n⏳ Time Management Analysis:")
    print(f"   Total study time: {total_study_time} minutes ({total_study_time/60:.1f} hours)")
    print(f"   Average per subject: {avg_study_per_subject:.1f} minutes")
    
    if avg_study_per_subject < 120:
        print("   ⚠️ Consider increasing study time per subject")
    elif avg_study_per_subject > 240:
        print("   ℹ️ You're studying extensively - ensure you're taking breaks")

def update_student_history(student_data):
    """Update student history with current data for time-series analysis"""
    update_date = datetime.now().strftime("%Y-%m-%d")
    
    for subject in student_data["subjects"]:
        if "history" not in subject:
            subject["history"] = []
        
        # Add current state to history
        subject["history"].append({
            "date": update_date,
            "lessons_done": subject["lessons_done"],
            "time_spent": subject["time_spent"],
            "attendance": subject["attendance"],
            "quiz_score": subject["quiz_score"],
            "last_week_score": subject["last_week_score"]
        })
    
    # Update in database
    collection.update_one(
        {"student_id": student_data["student_id"]},
        {"$set": {"subjects": student_data["subjects"]}}
    )

# Main execution with dynamic data handling
if __name__ == "__main__":
    student_id = int(input("Enter student ID: "))
    student_data = collection.find_one({"student_id": student_id})
    
    if student_data:
        try:
            # Update history before prediction
            update_student_history(student_data)
            
            # Load or train model
            model, scaler, version = train_or_load_model()
            
            # Make predictions
            predictions = predict_with_confidence(model, scaler, student_data)
            
            # Generate dynamic feedback
            generate_dynamic_feedback(student_data, predictions)
            
            # Store predictions in database
            collection.update_one(
                {"student_id": student_id},
                {"$set": {
                    "last_prediction": {
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "version": version,
                        "predictions": predictions
                    }
                }}
            )
            
        except Exception as e:
            print(f"\nAI system error: {str(e)}")
            print("Falling back to basic feedback with current data...\n")
            generate_basic_feedback(student_data)
    else:
        print("Student not found in database.")