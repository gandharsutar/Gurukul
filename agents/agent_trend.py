import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from pymongo import MongoClient
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
import json
import logging
from datetime import datetime
import os

# Configure logging
def setup_logging():
    """Configure logging for the application"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"student_performance_predictor_{current_time}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()

# MongoDB Connection
def connect_to_mongodb(connection_string, db_name, collection_name):
    """Connect to MongoDB and return the specified collection"""
    try:
        logger.info(f"Connecting to MongoDB: {db_name}.{collection_name}")
        client = MongoClient(connection_string)
        db = client[db_name]
        collection = db[collection_name]
        logger.info("Successfully connected to MongoDB")
        return collection
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise

# Process different data types
def process_audio_features(audio_data):
    """Process audio features from stored JSON"""
    try:
        if isinstance(audio_data, str):
            audio_data = json.loads(audio_data)
        features = {
            'audio_pitch': audio_data.get('pitch', 0),
            'audio_energy': audio_data.get('energy', 0),
            'audio_speech_rate': audio_data.get('speech_rate', 0)
        }
        logger.debug(f"Processed audio features: {features}")
        return features
    except Exception as e:
        logger.error(f"Error processing audio features: {str(e)}")
        return {
            'audio_pitch': 0,
            'audio_energy': 0,
            'audio_speech_rate': 0
        }

def process_image_features(image_data):
    """Process image features from stored JSON"""
    try:
        if isinstance(image_data, str):
            image_data = json.loads(image_data)
        features = {
            'image_brightness': image_data.get('brightness', 0),
            'image_attention_score': image_data.get('attention_score', 0),
            'image_engagement': image_data.get('engagement', 0)
        }
        logger.debug(f"Processed image features: {features}")
        return features
    except Exception as e:
        logger.error(f"Error processing image features: {str(e)}")
        return {
            'image_brightness': 0,
            'image_attention_score': 0,
            'image_engagement': 0
        }

def process_video_features(video_data):
    """Process video features from stored JSON"""
    try:
        if isinstance(video_data, str):
            video_data = json.loads(video_data)
        features = {
            'video_movement': video_data.get('movement', 0),
            'video_engagement': video_data.get('engagement', 0),
            'video_attention': video_data.get('attention', 0)
        }
        logger.debug(f"Processed video features: {features}")
        return features
    except Exception as e:
        logger.error(f"Error processing video features: {str(e)}")
        return {
            'video_movement': 0,
            'video_engagement': 0,
            'video_attention': 0
        }

# Fetch and prepare multi-modal data from MongoDB
def fetch_student_data(collection):
    """Fetch student data from MongoDB and convert to DataFrame with multi-modal features"""
    try:
        logger.info("Fetching student data from MongoDB")
        cursor = collection.find({})
        data = []
        
        for student in cursor:
            for i, subject in enumerate(student['subjects']):
                # Process multi-modal data
                audio_features = process_audio_features(student.get('audio_features', [{}])[i])
                image_features = process_image_features(student.get('image_features', [{}])[i])
                video_features = process_video_features(student.get('video_features', [{}])[i])
                
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
                    'target_scores': student['target_scores'][i],
                    'text_feedback': student.get('text_feedback', [''])[i],
                    **audio_features,
                    **image_features,
                    **video_features
                })
        
        df = pd.DataFrame(data)
        logger.info(f"Successfully created DataFrame with {len(df)} records")
        return df
    except Exception as e:
        logger.error(f"Error fetching student data: {str(e)}")
        raise

# Main prediction workflow
def predict_student_performance(connection_string, db_name, collection_name):
    try:
        logger.info("Starting student performance prediction workflow")
        
        # Connect to MongoDB and fetch data
        collection = connect_to_mongodb(connection_string, db_name, collection_name)
        df = fetch_student_data(collection)
        
        # Create target variable (trend: improve/decline/stagnant)
        logger.info("Creating target variable")
        df['score_change'] = (df['quiz_scores'] - df['last_week_scores'])/2
        df['performance_trend'] = np.where(df['score_change'] > 2, 'improve',
                                         np.where(df['score_change'] < -2, 'decline', 'stagnant'))
        logger.debug(f"Target distribution:\n{df['performance_trend'].value_counts()}")

        # Define Features and Target
        numeric_features = ['time_spent', 'lessons_done', 'quiz_scores',
                           'audio_pitch', 'audio_energy', 'audio_speech_rate',
                           'image_brightness', 'image_attention_score', 'image_engagement',
                           'video_movement', 'video_engagement', 'video_attention']
        
        text_feature = 'text_feedback'
        target = 'performance_trend'

        # Split data into train and test sets
        logger.info("Splitting data into train and test sets")
        X = df[numeric_features + [text_feature]]
        y = df[target]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

        # Create preprocessing pipeline for different data types
        logger.info("Creating preprocessing pipeline")
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), numeric_features),
                ('text', TfidfVectorizer(max_features=100), text_feature)
            ])
        
        # Create model pipeline
        logger.info("Building model pipeline")
        model = Pipeline([
            ('preprocessor', preprocessor),
            ('pca', PCA(n_components=10)),  # Reduce dimensionality
            ('classifier', LogisticRegression(multi_class='multinomial', solver='lbfgs', max_iter=1000))
        ])

        # Train model
        logger.info("Training model")
        model.fit(X_train, y_train)
        logger.info("Model training completed")

        # Make Predictions
        logger.info("Making predictions")
        y_pred = model.predict(X_test)
        
        # Store predictions
        test_indices = y_test.index
        df.loc[test_indices, 'next_week_score'] = y_pred
        
        # Predict for remaining data points
        train_indices = y_train.index
        y_train_pred = model.predict(X_train)
        df.loc[train_indices, 'next_week_score'] = y_train_pred
        
        # Create a numerical representation for visualization
        df['score_numerical'] = df['quiz_scores']  # Start with current scores
        # Adjust based on prediction category
        df.loc[df['next_week_score'] == 'improve', 'score_numerical'] += 5
        df.loc[df['next_week_score'] == 'decline', 'score_numerical'] -= 5

        # Evaluate Model
        logger.info("Evaluating model performance")
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred)
        
        print("Accuracy:", accuracy)
        print("\nClassification Report:")
        print(report)
        
        logger.info(f"Model accuracy: {accuracy}")
        logger.info("Classification Report:\n" + report)

        # Visualize the trends
        logger.info("Generating visualizations")
        plt.figure(figsize=(10, 6))
        sns.scatterplot(x='quiz_scores', y='score_numerical', hue='performance_trend', 
                       style='performance_trend', data=df, s=100)
        plt.plot([df['quiz_scores'].min(), df['quiz_scores'].max()], 
                 [df['quiz_scores'].min(), df['quiz_scores'].max()], 'k--')  # Reference line
        plt.title('Student Performance Prediction with Multi-Modal Data')
        plt.xlabel('Current Quiz Scores')
        plt.ylabel('Predicted Next Week Scores')
        plt.legend(title='Performance')
        plt.savefig("performance_prediction.png")
        plt.show()
        logger.info("Saved performance prediction visualization")

        # Feature importance analysis (for numeric features only)
        logger.info("Analyzing feature importance")
        numeric_model = model.named_steps['classifier']
        numeric_feature_names = numeric_features  # + top text features if needed
        
        # Get coefficients for each class
        if hasattr(numeric_model, 'coef_'):
            coef_df = pd.DataFrame(numeric_model.coef_, columns=numeric_feature_names)
            coef_df['class'] = numeric_model.classes_
            
            plt.figure(figsize=(12, 6))
            sns.heatmap(coef_df.set_index('class').T, annot=True, cmap='coolwarm')
            plt.title('Feature Importance by Class')
            plt.savefig("feature_importance.png")
            plt.show()
            logger.info("Saved feature importance visualization")

        return model

    except Exception as e:
        logger.error(f"Error in prediction workflow: {str(e)}", exc_info=True)
        raise

# Example usage
if __name__ == "__main__":
    try:
        logger.info("Starting student performance prediction application")
        
        # Replace with your MongoDB connection details
        CONNECTION_STRING = "mongodb://localhost:27017/"
        DB_NAME = "student_db"
        COLLECTION_NAME = "performance_data"
        
        logger.info(f"Using MongoDB: {DB_NAME}.{COLLECTION_NAME}")
        
        model = predict_student_performance(CONNECTION_STRING, DB_NAME, COLLECTION_NAME)
        logger.info("Application completed successfully")
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        print("An error occurred. Please check the logs for details.")