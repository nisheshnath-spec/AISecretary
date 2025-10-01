# classify.py
import pickle
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
import os

# Global variables for model and tokenizer
model = None
tokenizer = None

def load_classifier():
    """Load the model and tokenizer if they exist."""
    global model, tokenizer
    
    if not os.path.exists("email_classifier.h5") or not os.path.exists("tokenizer.pkl"):
        print("⚠️  Model files not found. Please run train_model.py first.")
        return False
    
    try:
        model = load_model("email_classifier.h5")
        with open("tokenizer.pkl", "rb") as f:
            tokenizer = pickle.load(f)
        print("✅ Email classifier loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Error loading classifier: {e}")
        return False

# Label mapping for 3 categories
categories = {
    0: "spam/no reply", 
    1: "Reply", 
    2: "urgent"
}

def classify_email(text):
    """
    Classify email text into importance categories.
    """
    global model, tokenizer
    
    # Load model if not already loaded
    if model is None or tokenizer is None:
        if not load_classifier():
            return "unknown"
    
    try:
        # Preprocess text
        seq = tokenizer.texts_to_sequences([text])
        padded = pad_sequences(seq, maxlen=50)  # Match training maxlen
        
        # Make prediction
        pred = model.predict(padded, verbose=0)
        label = pred.argmax(axis=1)[0]
        confidence = pred[0][label]
        
        # Return classification (no forced fallback to "reply needed")
        return categories[label]
        
    except Exception as e:
        print(f"❌ Error classifying email: {e}")
        return "spam/no reply"  # fallback if crash


def get_classification_confidence(text):
    """
    Get classification with confidence score.
    
    Args:
        text (str): Plain text content of the email
        
    Returns:
        tuple: (classification, confidence_score)
    """
    global model, tokenizer
    
    if model is None or tokenizer is None:
        if not load_classifier():
            return "unknown", 0.0
    
    try:
        seq = tokenizer.texts_to_sequences([text])
        padded = pad_sequences(seq, maxlen=50)
        pred = model.predict(padded, verbose=0)
        label = pred.argmax(axis=1)[0]
        confidence = pred[0][label]
        
        return categories[label], float(confidence)
        
    except Exception as e:
        print(f"❌ Error getting classification confidence: {e}")
        return "spam/no reply", 0.0

# Try to load the classifier when module is imported
load_classifier()
