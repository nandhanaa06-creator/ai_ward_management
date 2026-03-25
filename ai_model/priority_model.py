"""
AI model for complaint priority prediction.
Uses complaint description + category to predict priority level (high/medium/low).
"""

import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import numpy as np

from .priority_training_data import (
    PRIORITY_TRAINING_DATA, 
    PRIORITY_LEVELS,
    EMERGENCY_KEYWORDS,
    HIGH_PRIORITY_LOCATIONS
)

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'priority_predictor.pkl')
LABEL_ENCODER_PATH = os.path.join(BASE_DIR, 'priority_label_encoder.pkl')

# Cache the loaded model
_model = None
_label_encoder = None


def create_combined_features(text, category):
    """
    Combine complaint text and category for better prediction.
    Format: "CATEGORY: text"
    """
    return f"{category}: {text}"


def train_priority_model():
    """
    Train the priority prediction model using Random Forest classifier.
    """
    print("=" * 60)
    print("Training Priority Prediction Model")
    print("=" * 60)
    
    # Prepare training data
    texts = []
    categories = []
    priorities = []
    
    for text, category, priority in PRIORITY_TRAINING_DATA:
        # Combine text and category
        combined = create_combined_features(text, category)
        texts.append(combined)
        categories.append(category)
        priorities.append(priority)
    
    print(f"\nTotal training samples: {len(texts)}")
    print(f"Priority levels: {PRIORITY_LEVELS}")
    
    # Count samples per priority
    from collections import Counter
    priority_counts = Counter(priorities)
    print("\nSamples per priority:")
    for priority, count in priority_counts.items():
        print(f"  {priority}: {count}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        texts, priorities, test_size=0.2, random_state=42, stratify=priorities
    )
    
    print(f"\nTraining samples: {len(X_train)}")
    print(f"Testing samples: {len(X_test)}")
    
    # Create pipeline with TF-IDF and Random Forest
    model = Pipeline([
        ('tfidf', TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 3),  # Use unigrams, bigrams, and trigrams
            stop_words='english',
            lowercase=True
        )),
        ('classifier', RandomForestClassifier(
            n_estimators=100,
            max_depth=20,
            random_state=42,
            class_weight='balanced'  # Handle class imbalance
        ))
    ])
    
    print("\nTraining model...")
    model.fit(X_train, y_train)
    
    # Evaluate model
    print("\nEvaluating model...")
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n{'=' * 60}")
    print(f"Model Accuracy: {accuracy * 100:.2f}%")
    print(f"{'=' * 60}")
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=PRIORITY_LEVELS, zero_division=0))
    
    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred, labels=PRIORITY_LEVELS)
    print(f"{'':10} {'high':>10} {'medium':>10} {'low':>10}")
    for i, priority in enumerate(PRIORITY_LEVELS):
        print(f"{priority:10} {cm[i][0]:>10} {cm[i][1]:>10} {cm[i][2]:>10}")
    
    # Save model
    print(f"\nSaving model to: {MODEL_PATH}")
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    
    print("\n✅ Priority prediction model trained and saved successfully!")
    print("=" * 60)
    
    return model, accuracy


def load_priority_model():
    """
    Load the trained priority prediction model from disk.
    """
    global _model
    
    if _model is not None:
        return _model
    
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Priority model file not found at {MODEL_PATH}. "
            "Please train the model first by running: python manage.py train_priority_model"
        )
    
    with open(MODEL_PATH, 'rb') as f:
        _model = pickle.load(f)
    
    return _model


def check_emergency_keywords(text):
    """
    Check if text contains emergency keywords.
    Returns (has_emergency, matched_keywords)
    """
    text_lower = text.lower()
    matched = [kw for kw in EMERGENCY_KEYWORDS if kw in text_lower]
    return len(matched) > 0, matched


def check_high_priority_location(text):
    """
    Check if text mentions high-priority locations.
    Returns (has_location, matched_locations)
    """
    text_lower = text.lower()
    matched = [loc for loc in HIGH_PRIORITY_LOCATIONS if loc in text_lower]
    return len(matched) > 0, matched


def predict_priority(complaint_text, category="Other"):
    """
    Predict the priority of a complaint based on text and category.
    
    Args:
        complaint_text (str): The complaint description
        category (str): The complaint category
        
    Returns:
        dict: Dictionary containing:
            - priority (str): Predicted priority (high/medium/low)
            - confidence (float): Confidence score (0-100)
            - all_probabilities (dict): Probability for each priority
            - emergency_keywords (list): Detected emergency keywords
            - high_priority_location (list): Detected high-priority locations
            - reason (str): Explanation for the prediction
    """
    if not complaint_text or not complaint_text.strip():
        return {
            'priority': 'medium',
            'confidence': 0.0,
            'all_probabilities': {},
            'emergency_keywords': [],
            'high_priority_location': [],
            'reason': 'Empty complaint text'
        }
    
    try:
        # Check for emergency keywords
        has_emergency, emergency_kws = check_emergency_keywords(complaint_text)
        
        # Check for high-priority locations
        has_location, priority_locs = check_high_priority_location(complaint_text)
        
        # Load model
        model = load_priority_model()
        
        # Create combined features
        combined_text = create_combined_features(complaint_text, category)
        
        # Predict priority
        predicted_priority = model.predict([combined_text])[0]
        
        # Get probability scores
        probabilities = model.predict_proba([combined_text])[0]
        
        # Get priority names from the model
        priority_names = model.classes_
        
        # Create probability dictionary
        prob_dict = {priority: float(prob * 100) for priority, prob in zip(priority_names, probabilities)}
        
        # Get confidence (max probability)
        confidence = max(probabilities) * 100
        
        # Override to high priority if emergency keywords or critical locations detected
        original_priority = predicted_priority
        if has_emergency or has_location:
            if predicted_priority != 'high':
                predicted_priority = 'high'
                confidence = min(confidence + 20, 100)  # Boost confidence
        
        # Generate reason
        reason_parts = []
        if has_emergency:
            reason_parts.append(f"Emergency keywords detected: {', '.join(emergency_kws[:3])}")
        if has_location:
            reason_parts.append(f"High-priority location: {', '.join(priority_locs[:2])}")
        if not reason_parts:
            reason_parts.append(f"ML model prediction based on text analysis")
        
        reason = "; ".join(reason_parts)
        
        return {
            'priority': predicted_priority,
            'confidence': round(confidence, 2),
            'all_probabilities': prob_dict,
            'emergency_keywords': emergency_kws,
            'high_priority_location': priority_locs,
            'reason': reason,
            'original_ml_prediction': original_priority
        }
    
    except FileNotFoundError as e:
        print(f"Error: {e}")
        # Fallback to keyword-based prediction
        has_emergency, emergency_kws = check_emergency_keywords(complaint_text)
        if has_emergency:
            return {
                'priority': 'high',
                'confidence': 80.0,
                'all_probabilities': {},
                'emergency_keywords': emergency_kws,
                'high_priority_location': [],
                'reason': 'Fallback: Emergency keywords detected',
                'error': str(e)
            }
        return {
            'priority': 'medium',
            'confidence': 50.0,
            'all_probabilities': {},
            'emergency_keywords': [],
            'high_priority_location': [],
            'reason': 'Fallback: Model not trained',
            'error': str(e)
        }
    except Exception as e:
        print(f"Error predicting priority: {e}")
        return {
            'priority': 'medium',
            'confidence': 0.0,
            'all_probabilities': {},
            'emergency_keywords': [],
            'high_priority_location': [],
            'reason': f'Error: {str(e)}',
            'error': str(e)
        }


def predict_priority_simple(complaint_text, category="Other"):
    """
    Simple version that returns only the priority level.
    
    Args:
        complaint_text (str): The complaint description
        category (str): The complaint category
        
    Returns:
        str: Predicted priority (high/medium/low)
    """
    result = predict_priority(complaint_text, category)
    return result['priority']


def test_priority_predictions():
    """
    Test the trained model with sample predictions.
    """
    print("\n" + "=" * 60)
    print("Testing Priority Prediction Model")
    print("=" * 60)
    
    # Load the trained model
    if not os.path.exists(MODEL_PATH):
        print("❌ Model not found. Please train the model first.")
        return
    
    # Test samples
    test_samples = [
        ("Electric wire hanging dangerously near school", "Electricity"),
        ("Water supply irregular in our area", "Water"),
        ("Street light not working", "Street Light"),
        ("Open manhole on main road very dangerous", "Sanitation"),
        ("Road has some potholes", "Roads"),
        ("Sewage overflow near hospital", "Sanitation"),
        ("Power cut for 2 hours", "Electricity"),
        ("Request for new water connection", "Water"),
        ("Deep pothole causing accidents", "Roads"),
        ("Garbage not collected for 2 days", "Sanitation"),
    ]
    
    print("\nTest Predictions:")
    print("-" * 60)
    for text, category in test_samples:
        result = predict_priority(text, category)
        
        print(f"\nComplaint: {text}")
        print(f"Category: {category}")
        print(f"Predicted Priority: {result['priority'].upper()}")
        print(f"Confidence: {result['confidence']:.2f}%")
        print(f"Reason: {result['reason']}")
        if result['emergency_keywords']:
            print(f"Emergency Keywords: {', '.join(result['emergency_keywords'][:3])}")
        if result['high_priority_location']:
            print(f"Critical Locations: {', '.join(result['high_priority_location'][:2])}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Train the model
    train_priority_model()
    
    # Test predictions
    test_priority_predictions()
