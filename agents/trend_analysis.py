import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import StandardScaler
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from pymongo import MongoClient
from sklearn.model_selection import train_test_split

# MongoDB Connection
def connect_to_mongodb(connection_string, db_name, collection_name):
    """Connect to MongoDB and return the specified collection"""
    client = MongoClient(connection_string)
    db = client[db_name]
    return db[collection_name]

# Fetch and prepare data from MongoDB
def fetch_student_data(collection):
    """Fetch student data from MongoDB and convert to DataFrame"""
    cursor = collection.find({})
    data = []
    
    for student in cursor:
        for i, subject in enumerate(student['subjects']):
            data.append({
                'student_id': student['student_id'],
                'student_name': student['student_name'],
                'subject': subject,
                'time_spent': student['time_spent'][i],
                'lessons_done': student['lessons_done'][i],
                'total_lessons': student['total_lessons'][i],
                'quiz_scores': student['quiz_scores'][i],                
                'attendance': student['attendance'][i],
                'last_week_scores': student['last_week_scores'][i],
                'target_scores': student['target_scores'][i]
            })
    
    return pd.DataFrame(data)

# Main prediction workflow
def predict_student_performance(connection_string, db_name, collection_name):
    # Connect to MongoDB and fetch data
    collection = connect_to_mongodb(connection_string, db_name, collection_name)
    df = fetch_student_data(collection)
    
    # Create target variable (trend: improve/decline/stagnant)
    df['next_week_score'] = (df['quiz_scores'] + df['last_week_scores'])/2
    df['performance_trend'] = np.where(df['next_week_score'] > 2, 'improve',
                                     np.where(df['next_week_score'] < -2, 'decline', 'stagnant'))

    # Define Features and Target
    features = ['time_spent', 'lessons_done', 'quiz_scores', 'attendance', 'last_week_scores']
    target = 'performance_trend'

    X = df[features]
    y = df[target]

    # Split data into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train Logistic Regression Model (multi-class)
    model = LogisticRegression(multi_class='multinomial', solver='lbfgs', max_iter=1000)
    model.fit(X_train_scaled, y_train)

    # Make Predictions
    y_pred = model.predict(X_test_scaled)

    # Evaluate Model
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # Visualize the trends
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x='quiz_scores', y='next_week_score', hue='performance_trend', 
                   style='performance_trend', data=df, s=100)
    plt.plot([df['quiz_scores'].min(), df['quiz_scores'].max()], 
             [df['quiz_scores'].min(), df['quiz_scores'].max()], 'k--')  # Reference line
    plt.title('Performance Trend Visualization')
    plt.xlabel('Current Quiz Scores')
    plt.ylabel('Next Week Scores')
    plt.legend(title='Performance Trend')
    plt.show()

    # Return the trained model and scaler for future predictions
    return model, scaler

# Example usage
if __name__ == "__main__":
    # Replace with your MongoDB connection details
    CONNECTION_STRING = "mongodb://localhost:27017/"
    DB_NAME = "student_db"
    COLLECTION_NAME = "performance_data"
    
    model, scaler = predict_student_performance(CONNECTION_STRING, DB_NAME, COLLECTION_NAME)
    
    # Example prediction function
    def predict_performance_trend(time_spent, lessons_done, quiz_score, attendance, last_week_score):
        input_data = scaler.transform([[time_spent, lessons_done, quiz_score, attendance, last_week_score]])
        prediction = model.predict(input_data)[0]
        probabilities = model.predict_proba(input_data)[0]
        return prediction, probabilities
    
    # Example prediction
    trend, probs = predict_performance_trend(45, 3, 85, 90, 82)
    print(f"\nPredicted Trend: {trend}")
    print(f"Probabilities: {dict(zip(model.classes_, probs))}")
