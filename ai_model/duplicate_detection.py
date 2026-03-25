"""
AI-based duplicate complaint detection using TF-IDF and Cosine Similarity.
Detects similar complaints to prevent duplicate submissions.
"""

import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Similarity threshold (0.8 = 80% similar)
SIMILARITY_THRESHOLD = 0.8

# Time window for checking duplicates (in days)
TIME_WINDOW_DAYS = 30

# Distance threshold for location-based duplicate detection (in meters)
DISTANCE_THRESHOLD = 100  # 100 meters


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two GPS coordinates using Haversine formula.
    Returns distance in meters.
    """
    if not all([lat1, lon1, lat2, lon2]):
        return float('inf')
    
    import math
    R = 6371000  # Earth's radius in meters
    
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    dphi = math.radians(float(lat2 - lat1))
    dlambda = math.radians(float(lon2 - lon1))
    
    a = math.sin(dphi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def preprocess_text(text):
    """
    Preprocess complaint text for better similarity detection.
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text


def find_duplicate_complaints(new_complaint_text, new_complaint_title="", 
                              existing_complaints=None, category=None,
                              latitude=None, longitude=None):
    """
    Find duplicate complaints using TF-IDF and Cosine Similarity.
    
    Args:
        new_complaint_text (str): Description of the new complaint
        new_complaint_title (str): Title of the new complaint
        existing_complaints (list): List of dicts with 'id', 'text', 'title', 'category', 'lat', 'lon'
        category (str): Category of the new complaint
        latitude (float): Latitude of the new complaint
        longitude (float): Longitude of the new complaint
        
    Returns:
        dict: {
            'is_duplicate': bool,
            'similar_complaints': list of dicts with complaint info and similarity scores,
            'highest_similarity': float,
            'duplicate_complaint_id': int or None
        }
    """
    if not new_complaint_text or not existing_complaints:
        return {
            'is_duplicate': False,
            'similar_complaints': [],
            'highest_similarity': 0.0,
            'duplicate_complaint_id': None
        }
    
    # Combine title and description for better matching
    new_text = preprocess_text(f"{new_complaint_title} {new_complaint_text}")
    
    # Prepare existing complaint texts
    existing_texts = []
    complaint_ids = []
    complaint_info = []
    
    for complaint in existing_complaints:
        # Combine title and description
        existing_text = preprocess_text(
            f"{complaint.get('title', '')} {complaint.get('text', '')}"
        )
        existing_texts.append(existing_text)
        complaint_ids.append(complaint.get('id'))
        complaint_info.append(complaint)
    
    if not existing_texts:
        return {
            'is_duplicate': False,
            'similar_complaints': [],
            'highest_similarity': 0.0,
            'duplicate_complaint_id': None
        }
    
    try:
        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(
            max_features=500,
            ngram_range=(1, 2),  # Use unigrams and bigrams
            stop_words='english',
            lowercase=True
        )
        
        # Combine new complaint with existing complaints for vectorization
        all_texts = [new_text] + existing_texts
        
        # Fit and transform
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        
        # Calculate cosine similarity between new complaint and all existing complaints
        # First row is the new complaint, rest are existing complaints
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        
        # Find similar complaints
        similar_complaints = []
        highest_similarity = 0.0
        duplicate_complaint_id = None
        
        for idx, similarity_score in enumerate(similarities):
            complaint = complaint_info[idx]
            
            # Apply additional filters
            is_similar = similarity_score >= SIMILARITY_THRESHOLD
            
            # Check category match (if provided)
            if category and complaint.get('category'):
                if complaint.get('category') != category:
                    is_similar = False
            
            # Check location proximity (if GPS coordinates provided)
            if latitude and longitude and complaint.get('latitude') and complaint.get('longitude'):
                distance = calculate_distance(
                    latitude, longitude,
                    complaint.get('latitude'), complaint.get('longitude')
                )
                # If complaints are far apart, they're likely not duplicates
                if distance > DISTANCE_THRESHOLD:
                    is_similar = False
            
            if similarity_score > highest_similarity:
                highest_similarity = similarity_score
            
            if is_similar:
                similar_complaints.append({
                    'id': complaint.get('id'),
                    'title': complaint.get('title', ''),
                    'similarity_score': round(float(similarity_score), 4),
                    'similarity_percentage': round(float(similarity_score) * 100, 2),
                    'category': complaint.get('category', ''),
                    'status': complaint.get('status', ''),
                    'created_at': complaint.get('created_at', ''),
                })
                
                # Mark the highest similarity complaint as the duplicate
                if not duplicate_complaint_id or similarity_score > similarities[complaint_ids.index(duplicate_complaint_id)]:
                    duplicate_complaint_id = complaint.get('id')
        
        # Sort by similarity score (highest first)
        similar_complaints.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return {
            'is_duplicate': len(similar_complaints) > 0,
            'similar_complaints': similar_complaints,
            'highest_similarity': round(float(highest_similarity), 4),
            'highest_similarity_percentage': round(float(highest_similarity) * 100, 2),
            'duplicate_complaint_id': duplicate_complaint_id
        }
    
    except Exception as e:
        print(f"Error in duplicate detection: {e}")
        return {
            'is_duplicate': False,
            'similar_complaints': [],
            'highest_similarity': 0.0,
            'duplicate_complaint_id': None,
            'error': str(e)
        }


def check_duplicate_simple(new_text, existing_texts):
    """
    Simple version that returns True/False for duplicate detection.
    
    Args:
        new_text (str): New complaint text
        existing_texts (list): List of existing complaint texts
        
    Returns:
        bool: True if duplicate found, False otherwise
    """
    if not new_text or not existing_texts:
        return False
    
    try:
        vectorizer = TfidfVectorizer(
            max_features=500,
            ngram_range=(1, 2),
            stop_words='english'
        )
        
        all_texts = [preprocess_text(new_text)] + [preprocess_text(t) for t in existing_texts]
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        
        return np.max(similarities) >= SIMILARITY_THRESHOLD
    
    except Exception as e:
        print(f"Error in simple duplicate check: {e}")
        return False


# For testing
if __name__ == "__main__":
    print("Testing Duplicate Complaint Detection")
    print("=" * 60)
    
    # Test data
    existing_complaints = [
        {
            'id': 1,
            'title': 'Water pipe leaking',
            'text': 'Water pipe is leaking on main road near my house',
            'category': 'Water',
            'status': 'pending',
            'latitude': 10.8505,
            'longitude': 76.2711,
            'created_at': '2024-01-01'
        },
        {
            'id': 2,
            'title': 'Street light not working',
            'text': 'Street light near school is not working since 3 days',
            'category': 'Street Light',
            'status': 'pending',
            'latitude': 10.8510,
            'longitude': 76.2715,
            'created_at': '2024-01-02'
        },
        {
            'id': 3,
            'title': 'Road pothole',
            'text': 'Big pothole on main road causing accidents',
            'category': 'Roads',
            'status': 'pending',
            'latitude': 10.8520,
            'longitude': 76.2720,
            'created_at': '2024-01-03'
        }
    ]
    
    # Test 1: Duplicate complaint (high similarity)
    print("\nTest 1: Duplicate Complaint")
    print("-" * 60)
    new_complaint = "Water pipe leaking on main road near my house"
    result = find_duplicate_complaints(
        new_complaint,
        "Water leak",
        existing_complaints,
        category='Water',
        latitude=10.8506,
        longitude=76.2712
    )
    print(f"New Complaint: {new_complaint}")
    print(f"Is Duplicate: {result['is_duplicate']}")
    print(f"Highest Similarity: {result['highest_similarity_percentage']}%")
    if result['similar_complaints']:
        print(f"Similar to Complaint #{result['similar_complaints'][0]['id']}")
        print(f"  Title: {result['similar_complaints'][0]['title']}")
        print(f"  Similarity: {result['similar_complaints'][0]['similarity_percentage']}%")
    
    # Test 2: Similar but not duplicate (medium similarity)
    print("\n\nTest 2: Similar Complaint (Below Threshold)")
    print("-" * 60)
    new_complaint = "Water supply not available in our area"
    result = find_duplicate_complaints(
        new_complaint,
        "No water supply",
        existing_complaints,
        category='Water'
    )
    print(f"New Complaint: {new_complaint}")
    print(f"Is Duplicate: {result['is_duplicate']}")
    print(f"Highest Similarity: {result['highest_similarity_percentage']}%")
    
    # Test 3: Completely different complaint
    print("\n\nTest 3: Different Complaint")
    print("-" * 60)
    new_complaint = "Garbage not collected for 5 days"
    result = find_duplicate_complaints(
        new_complaint,
        "Garbage issue",
        existing_complaints,
        category='Sanitation'
    )
    print(f"New Complaint: {new_complaint}")
    print(f"Is Duplicate: {result['is_duplicate']}")
    print(f"Highest Similarity: {result['highest_similarity_percentage']}%")
    
    print("\n" + "=" * 60)
