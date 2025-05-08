import logging
from pymongo import MongoClient
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Union, Optional
import os
from PIL import Image
import cv2
import librosa
import speech_recognition as sr

# Configure logging
def setup_logging():
    """Configure logging for the application"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.mkdirs(log_dir)
    
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"multimodal_anomaly_detection_{current_time}.log")
    
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

class MultiModalDataConnector:
    def __init__(self, connection_string: str, db_name: str):
        """Initialize connection to MongoDB with multimodal data"""
        try:
            logger.info(f"Initializing MongoDB connection to {db_name}")
            self.client = MongoClient(connection_string)
            self.db = self.client[db_name]
            logger.info("MongoDB connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    def get_text_data(self, collection_name: str, query: Dict = {}) -> List[Dict]:
        """Retrieve processed text data from MongoDB"""
        try:
            logger.debug(f"Retrieving text data from collection {collection_name}")
            data = list(self.db[collection_name].find(query))
            logger.info(f"Retrieved {len(data)} text documents from {collection_name}")
            return data
        except Exception as e:
            logger.error(f"Error retrieving text data: {str(e)}")
            return []

    def get_audio_metadata(self, collection_name: str) -> List[Dict]:
        """Retrieve audio file metadata"""
        try:
            logger.debug(f"Retrieving audio metadata from collection {collection_name}")
            data = list(self.db[collection_name].find({}, {"audio_path": 1, "duration": 1, "transcript": 1}))
            logger.info(f"Retrieved {len(data)} audio metadata records from {collection_name}")
            return data
        except Exception as e:
            logger.error(f"Error retrieving audio metadata: {str(e)}")
            return []

    def get_video_metadata(self, collection_name: str) -> List[Dict]:
        """Retrieve video file metadata"""
        try:
            logger.debug(f"Retrieving video metadata from collection {collection_name}")
            data = list(self.db[collection_name].find({}, {"video_path": 1, "duration": 1, "keyframes": 1}))
            logger.info(f"Retrieved {len(data)} video metadata records from {collection_name}")
            return data
        except Exception as e:
            logger.error(f"Error retrieving video metadata: {str(e)}")
            return []

    def get_image_metadata(self, collection_name: str) -> List[Dict]:
        """Retrieve image file metadata"""
        try:
            logger.debug(f"Retrieving image metadata from collection {collection_name}")
            data = list(self.db[collection_name].find({}, {"image_path": 1, "features": 1, "annotations": 1}))
            logger.info(f"Retrieved {len(data)} image metadata records from {collection_name}")
            return data
        except Exception as e:
            logger.error(f"Error retrieving image metadata: {str(e)}")
            return []

    def process_audio_file(self, file_path: str) -> Dict:
        """Process audio file to extract features"""
        try:
            logger.info(f"Processing audio file: {file_path}")
            
            # Load audio file
            y, sr = librosa.load(file_path)
            
            # Extract features
            duration = librosa.get_duration(y=y, sr=sr)
            mfcc = librosa.feature.mfcc(y=y, sr=sr)
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            
            # Speech recognition
            r = sr.Recognizer()
            with sr.AudioFile(file_path) as source:
                audio = r.record(source)
                try:
                    transcript = r.recognize_google(audio)
                except sr.UnknownValueError:
                    transcript = "Could not understand audio"
                except Exception as e:
                    logger.warning(f"Speech recognition error: {str(e)}")
                    transcript = f"Recognition error: {str(e)}"
            
            result = {
                "duration": duration,
                "mfcc_mean": np.mean(mfcc),
                "chroma_mean": np.mean(chroma),
                "transcript": transcript,
                "status": "processed"
            }
            
            logger.info(f"Successfully processed audio file: {file_path}")
            return result
        except Exception as e:
            error_msg = f"Error processing audio file {file_path}: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "status": "failed"}

    def process_video_file(self, file_path: str) -> Dict:
        """Process video file to extract key frames and features"""
        try:
            logger.info(f"Processing video file: {file_path}")
            cap = cv2.VideoCapture(file_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps
            
            # Extract key frames (every 5 seconds)
            keyframes = []
            for i in range(0, frame_count, int(5 * fps)):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if ret:
                    # Convert to RGB and get dominant color
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    avg_color = np.mean(frame_rgb, axis=(0, 1))
                    keyframes.append({
                        "frame_number": i,
                        "timestamp": i/fps,
                        "dominant_color": avg_color.tolist()
                    })
            
            cap.release()
            
            result = {
                "duration": duration,
                "fps": fps,
                "frame_count": frame_count,
                "keyframes": keyframes,
                "status": "processed"
            }
            
            logger.info(f"Successfully processed video file: {file_path}")
            return result
        except Exception as e:
            error_msg = f"Error processing video file {file_path}: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "status": "failed"}

    def process_image_file(self, file_path: str) -> Dict:
        """Process image file to extract features"""
        try:
            logger.info(f"Processing image file: {file_path}")
            img = Image.open(file_path)
            width, height = img.size
            dominant_color = np.array(img).mean(axis=(0, 1)).tolist()
            
            result = {
                "width": width,
                "height": height,
                "dominant_color": dominant_color,
                "format": img.format,
                "mode": img.mode,
                "status": "processed"
            }
            
            logger.info(f"Successfully processed image file: {file_path}")
            return result
        except Exception as e:
            error_msg = f"Error processing image file {file_path}: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "status": "failed"}

class MultiModalAnomalyDetector:
    def __init__(self, data_connector: MultiModalDataConnector):
        self.connector = data_connector
        self.anomalies = []
        logger.info("MultiModalAnomalyDetector initialized")

    def detect_text_anomalies(self, collection_name: str) -> List[str]:
        """Detect anomalies in processed text data"""
        logger.info(f"Starting text anomaly detection on collection: {collection_name}")
        text_data = self.connector.get_text_data(collection_name)
        anomalies = []
        
        for doc in text_data:
            doc_id = str(doc.get('_id', 'unknown'))
            
            # Check for sentiment anomalies
            if "sentiment" in doc:
                score = doc["sentiment"].get("score", 0)
                if score < -0.7:
                    msg = f"⚠️ Negative sentiment detected in document {doc_id}: {score}"
                    anomalies.append(msg)
                    logger.warning(msg)
                
            # Check for toxicity
            if "toxicity" in doc:
                score = doc["toxicity"].get("score", 0)
                if score > 0.8:
                    msg = f"🚨 High toxicity detected in document {doc_id}: {score}"
                    anomalies.append(msg)
                    logger.warning(msg)
        
        self.anomalies.extend(anomalies)
        logger.info(f"Detected {len(anomalies)} text anomalies in {collection_name}")
        return anomalies

    def detect_audio_anomalies(self, collection_name: str) -> List[str]:
        """Detect anomalies in audio data"""
        logger.info(f"Starting audio anomaly detection on collection: {collection_name}")
        audio_data = self.connector.get_audio_metadata(collection_name)
        anomalies = []
        
        for doc in audio_data:
            file_path = doc.get('audio_path', 'unknown')
            
            # Check for long durations
            if "duration" in doc and doc["duration"] > 300:  # >5 minutes
                msg = f"⏱️ Long audio duration ({doc['duration']}s) in file {file_path}"
                anomalies.append(msg)
                logger.warning(msg)
            
            # Check for empty transcripts
            if "transcript" in doc and len(doc["transcript"].strip()) < 10:
                msg = f"🔇 Very short transcript in file {file_path}"
                anomalies.append(msg)
                logger.warning(msg)
        
        self.anomalies.extend(anomalies)
        logger.info(f"Detected {len(anomalies)} audio anomalies in {collection_name}")
        return anomalies

    def detect_video_anomalies(self, collection_name: str) -> List[str]:
        """Detect anomalies in video data"""
        logger.info(f"Starting video anomaly detection on collection: {collection_name}")
        video_data = self.connector.get_video_metadata(collection_name)
        anomalies = []
        
        for doc in video_data:
            file_path = doc.get('video_path', 'unknown')
            
            # Check for very short videos
            if "duration" in doc and doc["duration"] < 5:
                msg = f"🎬 Very short video ({doc['duration']}s) in file {file_path}"
                anomalies.append(msg)
                logger.warning(msg)
            
            # Check for missing keyframes
            if "keyframes" in doc and len(doc["keyframes"]) < 3:
                msg = f"🖼️ Few keyframes ({len(doc['keyframes'])}) in file {file_path}"
                anomalies.append(msg)
                logger.warning(msg)
        
        self.anomalies.extend(anomalies)
        logger.info(f"Detected {len(anomalies)} video anomalies in {collection_name}")
        return anomalies

    def detect_image_anomalies(self, collection_name: str) -> List[str]:
        """Detect anomalies in image data"""
        logger.info(f"Starting image anomaly detection on collection: {collection_name}")
        image_data = self.connector.get_image_metadata(collection_name)
        anomalies = []
        
        for doc in image_data:
            file_path = doc.get('image_path', 'unknown')
            
            # Check for very large images
            if "width" in doc and "height" in doc:
                megapixels = (doc["width"] * doc["height"]) / 1_000_000
                if megapixels > 10:
                    msg = f"📷 Large image ({megapixels:.1f} MP) in file {file_path}"
                    anomalies.append(msg)
                    logger.warning(msg)
            
            # Check for potential NSFW content
            if "annotations" in doc and "nsfw_score" in doc["annotations"]:
                if doc["annotations"]["nsfw_score"] > 0.8:
                    msg = f"🚫 Potentially NSFW image ({doc['annotations']['nsfw_score']}) in file {file_path}"
                    anomalies.append(msg)
                    logger.warning(msg)
        
        self.anomalies.extend(anomalies)
        logger.info(f"Detected {len(anomalies)} image anomalies in {collection_name}")
        return anomalies

    def generate_report(self) -> str:
        """Generate comprehensive anomaly report"""
        logger.info("Generating anomaly detection report")
        if not self.anomalies:
            logger.info("No anomalies detected")
            return "✅ No anomalies detected across all modalities"
        
        report = [
            "MULTIMODAL ANOMALY REPORT",
            "="*50,
            f"Total anomalies detected: {len(self.anomalies)}",
            "\nDETAILED FINDINGS:",
            *self.anomalies,
            "\nRECOMMENDATIONS:",
            "1. Review high-severity anomalies first",
            "2. Check original files for flagged items",
            "3. Consider reprocessing problematic files",
            "4. Update processing pipelines if patterns emerge"
        ]
        
        report_str = "\n".join(report)
        logger.info(f"Report generated with {len(self.anomalies)} anomalies")
        return report_str

# Example Usage
if __name__ == "__main__":
    try:
        logger.info("Starting multimodal anomaly detection process")
        
        # Initialize the multimodal connector
        connector = MultiModalDataConnector("mongodb://localhost:27017/", "multimedia_db")
        
        # Initialize the anomaly detector
        detector = MultiModalAnomalyDetector(connector)
        
        # Run anomaly detection across different modalities
        logger.info("Running text anomaly detection")
        detector.detect_text_anomalies("processed_text")
        
        logger.info("Running audio anomaly detection")
        detector.detect_audio_anomalies("processed_audio")
        
        logger.info("Running video anomaly detection")
        detector.detect_video_anomalies("processed_video")
        
        logger.info("Running image anomaly detection")
        detector.detect_image_anomalies("processed_images")
        
        # Generate and print the report
        report = detector.generate_report()
        print(report)
        
        logger.info("Anomaly detection process completed successfully")
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
        raise