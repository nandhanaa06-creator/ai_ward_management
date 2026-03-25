# AI-Based Complaint Categorization

## Overview
This module implements automatic complaint categorization using Machine Learning (NLP).

When a citizen submits a complaint, the system automatically predicts the category:
- **Water** - Water supply, leaks, pipes, tanks
- **Electricity** - Power cuts, transformers, electric wires
- **Street Light** - Street lights, lamps, lighting issues
- **Sanitation** - Garbage, drainage, sewage, waste
- **Roads** - Potholes, road damage, construction
- **Other** - All other complaints

## Technology Stack
- **Algorithm**: Multinomial Naive Bayes
- **Feature Extraction**: TF-IDF Vectorizer
- **Library**: scikit-learn
- **Language**: Python

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

This will install:
- scikit-learn==1.5.2
- numpy==1.26.4

### 2. Train the AI Model
```bash
python manage.py train_ai_model
```

This command will:
- Train the model on 120+ sample complaints
- Test the model accuracy
- Save the trained model to `ai_model/complaint_categorizer.pkl`
- Show prediction examples

Expected output:
```
🤖 Starting AI Model Training...
Training Complaint Categorization Model
Total training samples: 120
Model Accuracy: 95.83%
✅ Model trained successfully!
```

### 3. Test the Model (Optional)
```bash
python -m ai_model.predict
```

This will test the model with sample complaints and show predictions.

## How It Works

### 1. Training Phase
- Uses 120+ labeled complaint samples
- Extracts features using TF-IDF (Term Frequency-Inverse Document Frequency)
- Trains Multinomial Naive Bayes classifier
- Saves model to disk

### 2. Prediction Phase
When a citizen submits a complaint:
1. System combines title + description
2. AI model analyzes the text
3. Predicts category with confidence score
4. Saves category to `Complaint.category` field
5. Stores AI analysis in `Complaint.ai_analysis_reason` field

### 3. Fallback Mechanism
If AI model fails (not trained or error):
- System falls back to keyword-based categorization
- Ensures complaints are always categorized

## File Structure
```
ai_model/
├── __init__.py                    # Package init
├── training_data.py               # 120+ labeled samples
├── train_model.py                 # Training script
├── predict.py                     # Prediction functions
└── complaint_categorizer.pkl      # Trained model (generated)

complaints/
├── management/
│   └── commands/
│       └── train_ai_model.py      # Django command
└── views.py                       # Integrated AI prediction
```

## Integration in Views

The AI model is integrated in `complaints/views.py`:

```python
# Import AI prediction
from ai_model.predict import predict_category

# In report_complaint view
ai_result = predict_category(full_text)
complaint.category = ai_result['category']
complaint.ai_analysis_reason = f"AI Predicted: {ai_result['category']} ({ai_result['confidence']:.1f}%)"
```

## Model Performance

### Training Data
- **Total Samples**: 120 complaints
- **Categories**: 6 (Water, Electricity, Street Light, Sanitation, Roads, Other)
- **Samples per Category**: 20 each

### Expected Accuracy
- **Training Accuracy**: ~95-98%
- **Test Accuracy**: ~90-95%

### Confidence Scores
- High confidence (>80%): Very accurate prediction
- Medium confidence (60-80%): Good prediction
- Low confidence (<60%): May need manual review

## Testing the Model

### Test with Custom Text
```python
from ai_model.predict import predict_category

result = predict_category("Water pipe is leaking on the road")
print(result)
# Output: {'category': 'Water', 'confidence': 95.23, 'all_probabilities': {...}}
```

### Test via Django Shell
```bash
python manage.py shell
```

```python
from ai_model.predict import predict_category

# Test prediction
result = predict_category("Street light not working near my house")
print(f"Category: {result['category']}")
print(f"Confidence: {result['confidence']}%")
```

## Improving the Model

### Add More Training Data
Edit `ai_model/training_data.py` and add more samples:

```python
TRAINING_DATA = [
    # Add your samples
    ("Your complaint text here", "Category"),
    # ...
]
```

Then retrain:
```bash
python manage.py train_ai_model
```

### Tune Model Parameters
Edit `ai_model/train_model.py`:

```python
# Adjust TF-IDF parameters
TfidfVectorizer(
    max_features=1000,  # Increase features
    ngram_range=(1, 3),  # Use trigrams
)

# Adjust Naive Bayes alpha
MultinomialNB(alpha=0.5)  # Change smoothing
```

## Troubleshooting

### Error: Model file not found
**Solution**: Train the model first
```bash
python manage.py train_ai_model
```

### Error: scikit-learn not installed
**Solution**: Install dependencies
```bash
pip install scikit-learn numpy
```

### Low accuracy
**Solution**: Add more training samples in `training_data.py`

### Wrong predictions
**Solution**: 
1. Check if complaint text is clear
2. Add similar examples to training data
3. Retrain the model

## Future Enhancements

1. **Priority Prediction**: Predict High/Medium/Low priority
2. **Duplicate Detection**: Find similar complaints using text similarity
3. **Sentiment Analysis**: Detect urgency from text
4. **Multi-language Support**: Support regional languages
5. **Deep Learning**: Use BERT or transformers for better accuracy

## API Reference

### predict_category(complaint_text)
Predicts the category of a complaint.

**Parameters:**
- `complaint_text` (str): The complaint description

**Returns:**
- `dict`: 
  - `category` (str): Predicted category
  - `confidence` (float): Confidence score (0-100)
  - `all_probabilities` (dict): Probability for each category

**Example:**
```python
result = predict_category("Water supply not available")
# {'category': 'Water', 'confidence': 92.5, 'all_probabilities': {...}}
```

### predict_category_simple(complaint_text)
Simple version that returns only the category name.

**Parameters:**
- `complaint_text` (str): The complaint description

**Returns:**
- `str`: Predicted category name

**Example:**
```python
category = predict_category_simple("Power cut since morning")
# 'Electricity'
```

## License
Part of AI-Based Smart Ward Management System

## Support
For issues or questions, contact the development team.
