import tensorflow as tf
import numpy as np
from PIL import Image
import os

MODEL_PATH = "dermiq_model.h5"
IMG_SIZE = (224, 224)

CLASS_LABELS = {
    0: "clear",
    1: "mild",
    2: "moderate",
    3: "severe"
}

def load_model():
    if os.path.exists(MODEL_PATH):
        return tf.keras.models.load_model(MODEL_PATH)
    return None

def preprocess_image(image_path):
    img = Image.open(image_path).convert("RGB")
    img = img.resize(IMG_SIZE)
    img_array = np.array(img) / 255.0
    return np.expand_dims(img_array, axis=0)

def simulate_prediction(image_path=None):
    """Simulate prediction when model is not available. 
    Deterministic based on image path for consistent testing."""
    import hashlib
    
    if image_path:
        # Create a seed from the image path to make it deterministic
        seed = int(hashlib.md5(str(image_path).encode()).hexdigest(), 16) % (2**32)
        random_gen = np.random.RandomState(seed)
    else:
        random_gen = np.random
        
    severities = ["clear", "mild", "moderate", "severe"]
    # Fixed probabilities: 40% clear, 30% mild, 20% moderate, 10% severe
    severity = random_gen.choice(severities, p=[0.4, 0.3, 0.2, 0.1])
    confidence = random_gen.uniform(70, 95)
    
    severity2 = random_gen.choice([s for s in severities if s != severity])
    severity3 = random_gen.choice([s for s in severities if s not in [severity, severity2]])
    
    top3 = [
        (severity, confidence),
        (severity2, confidence - random_gen.uniform(5, 15)),
        (severity3, confidence - random_gen.uniform(15, 25))
    ]
    return {
        "condition": severity,
        "confidence": f"{confidence:.2f}%",
        "top3": top3
    }

def predict(image_path, model=None):
    if model is None:
        model = load_model()

    if model is None:
        # Simulate if model not available
        return simulate_prediction(image_path)

    img = preprocess_image(image_path)
    predictions = model.predict(img)

    confidence = float(np.max(predictions) * 100)
    predicted_index = int(np.argmax(predictions))
    predicted_class = CLASS_LABELS[predicted_index]

    top3 = sorted(
        [(CLASS_LABELS[i], float(predictions[0][i] * 100)) for i in range(4)],
        key=lambda x: x[1],
        reverse=True
    )[:3]

    return {
        "condition": predicted_class,
        "confidence": f"{confidence:.2f}%",
        "top3": top3
    }

def preprocess_pil_image(pil_image):
    """Preprocess a PIL image (from Gradio)."""
    img = pil_image.convert("RGB")
    img = img.resize(IMG_SIZE)
    img_array = np.array(img) / 255.0
    return np.expand_dims(img_array, axis=0)

def predict_image(pil_image, model=None):
    """Predict condition from a PIL Image object (used by Gradio)."""
    if model is None:
        model = load_model()
    
    img = preprocess_pil_image(pil_image)
    predictions = model.predict(img)
    
    confidence = float(np.max(predictions) * 100)
    predicted_index = int(np.argmax(predictions))
    predicted_class = CLASS_LABELS[predicted_index]
    
    top3 = sorted(
        [(CLASS_LABELS[i], float(predictions[0][i] * 100)) for i in range(4)],
        key=lambda x: x[1],
        reverse=True
    )[:3]
    
    return {
        "class": predicted_class,
        "confidence": confidence,
        "top3": top3
    }