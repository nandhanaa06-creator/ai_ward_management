"""
Predict complaint category using trained AI model.
"""

import os
import pickle

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'complaint_categorizer.pkl')

# Cache the loaded model
_model = None


def load_model():
    """
    Load the trained model from disk.
    Uses caching to avoid loading multiple times.
    """
    global _model
    
    if _model is not None:
        return _model
    
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model file not found at {MODEL_PATH}. "
            "Please train the model first by running: python -m ai_model.train_model"
        )
    
    with open(MODEL_PATH, 'rb') as f:
        _model = pickle.load(f)
    
    return _model


def predict_category(complaint_text):
    """
    Predict the category of a complaint based on its text.
    
    Args:
        complaint_text (str): The complaint description
        
    Returns:
        dict: Dictionary containing:
            - category (str): Predicted category
            - confidence (float): Confidence score (0-100)
            - all_probabilities (dict): Probability for each category
    """
    if not complaint_text or not complaint_text.strip():
        return {
            'category': 'Other',
            'confidence': 0.0,
            'all_probabilities': {}
        }
    
    try:
        # Load model
        model = load_model()
        
        # Predict category
        predicted_category = model.predict([complaint_text])[0]
        
        # Get probability scores for all categories
        probabilities = model.predict_proba([complaint_text])[0]
        
        # Get category names from the model
        categories = model.classes_
        
        # Create probability dictionary
        prob_dict = {cat: float(prob * 100) for cat, prob in zip(categories, probabilities)}
        
        # Get confidence (max probability)
        confidence = max(probabilities) * 100
        
        return {
            'category': predicted_category,
            'confidence': round(confidence, 2),
            'all_probabilities': prob_dict
        }
    
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return {
            'category': 'Other',
            'confidence': 0.0,
            'all_probabilities': {},
            'error': str(e)
        }
    except Exception as e:
        print(f"Error predicting category: {e}")
        return {
            'category': 'Other',
            'confidence': 0.0,
            'all_probabilities': {},
            'error': str(e)
        }


def predict_category_simple(complaint_text):
    """
    Simple version that returns only the category name.
    
    Args:
        complaint_text (str): The complaint description
        
    Returns:
        str: Predicted category name
    """
    result = predict_category(complaint_text)
    return result['category']


# For testing
if __name__ == "__main__":
    print("Testing Complaint Categorization AI")
    print("=" * 60)
    
    test_complaints = [
        "Water supply is not available in our area",
        "Street light is not working near my house",
        "Road is full of potholes",
        "Garbage not collected for 3 days",
        "Power cut since morning",
        "Drainage is blocked and overflowing",
        "Stray dogs are creating problem",
    ]
    
    for complaint in test_complaints:
        result = predict_category(complaint)
        print(f"\nComplaint: {complaint}")
        print(f"Category: {result['category']}")
        print(f"Confidence: {result['confidence']:.2f}%")
        print(f"All Probabilities: {result['all_probabilities']}")
        print("-" * 60)
