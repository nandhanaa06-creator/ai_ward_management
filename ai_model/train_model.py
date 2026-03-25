"""
Train AI model for complaint categorization.
Uses TF-IDF Vectorizer and Multinomial Naive Bayes classifier.
"""

import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from .training_data import TRAINING_DATA, CATEGORIES

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'complaint_categorizer.pkl')


def train_model():
    """
    Train the complaint categorization model and save it to disk.
    """
    print("=" * 60)
    print("Training Complaint Categorization Model")
    print("=" * 60)
    
    # Prepare training data
    texts = [text for text, category in TRAINING_DATA]
    labels = [category for text, category in TRAINING_DATA]
    
    print(f"\nTotal training samples: {len(texts)}")
    print(f"Categories: {CATEGORIES}")
    
    # Count samples per category
    from collections import Counter
    category_counts = Counter(labels)
    print("\nSamples per category:")
    for category, count in category_counts.items():
        print(f"  {category}: {count}")
    
    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    
    print(f"\nTraining samples: {len(X_train)}")
    print(f"Testing samples: {len(X_test)}")
    
    # Create pipeline with TF-IDF and Naive Bayes
    model = Pipeline([
        ('tfidf', TfidfVectorizer(
            max_features=500,
            ngram_range=(1, 2),  # Use unigrams and bigrams
            stop_words='english',
            lowercase=True
        )),
        ('classifier', MultinomialNB(alpha=0.1))
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
    print(classification_report(y_test, y_pred, target_names=CATEGORIES, zero_division=0))
    
    # Save model to disk
    print(f"\nSaving model to: {MODEL_PATH}")
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    
    print("\n✅ Model trained and saved successfully!")
    print("=" * 60)
    
    return model, accuracy


def test_model_predictions():
    """
    Test the trained model with sample predictions.
    """
    print("\n" + "=" * 60)
    print("Testing Model Predictions")
    print("=" * 60)
    
    # Load the trained model
    if not os.path.exists(MODEL_PATH):
        print("❌ Model not found. Please train the model first.")
        return
    
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    
    # Test samples
    test_samples = [
        "Water is not coming from tap since morning",
        "Street light near my house is not working",
        "Road has big potholes and is dangerous",
        "Garbage not collected for 5 days",
        "Power cut for 6 hours daily",
        "Drainage water overflowing on street",
    ]
    
    print("\nTest Predictions:")
    print("-" * 60)
    for text in test_samples:
        prediction = model.predict([text])[0]
        # Get probability scores
        proba = model.predict_proba([text])[0]
        confidence = max(proba) * 100
        
        print(f"\nComplaint: {text}")
        print(f"Predicted Category: {prediction}")
        print(f"Confidence: {confidence:.2f}%")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Train the model
    train_model()
    
    # Test predictions
    test_model_predictions()
