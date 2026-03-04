import tensorflow as tf
import numpy as np
from PIL import Image

MODEL_PATH = "models/dermiq_model.h5"
IMG_SIZE = (224, 224)

CLASS_LABELS = {
    0: "clear",
    1: "mild",
    2: "moderate",
    3: "severe"
}

def load_model():
    return tf.keras.models.load_model(MODEL_PATH)

def preprocess_image(image_path):
    img = Image.open(image_path).convert("RGB")
    img = img.resize(IMG_SIZE)
    img_array = np.array(img) / 255.0
    return np.expand_dims(img_array, axis=0)

def predict(image_path, model=None):
    if model is None:
        model = load_model()

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