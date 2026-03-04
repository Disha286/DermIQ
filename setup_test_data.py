"""Setup script to create synthetic test data and train a simple model."""

import os
import numpy as np
from PIL import Image, ImageDraw
import tensorflow as tf
from tensorflow import keras
from src.preprocess import get_data_generators, IMG_SIZE
from src.model import build_model

# Create dataset directory structure
DATASET_PATH = "dataset"
CLASSES = ["clear", "mild", "moderate", "severe"]

def create_synthetic_images(num_per_class=20):
    """Create synthetic skin condition images with varying characteristics."""
    
    print("Creating synthetic dataset...")
    os.makedirs(DATASET_PATH, exist_ok=True)
    
    for class_name in CLASSES:
        class_dir = os.path.join(DATASET_PATH, class_name)
        os.makedirs(class_dir, exist_ok=True)
        
        for i in range(num_per_class):
            # Create base skin-tone color
            base_color = (230, 190, 150)  # Skin tone
            
            # Add imperfections based on severity
            img = Image.new('RGB', IMG_SIZE, base_color)
            draw = ImageDraw.Draw(img)
            
            # Add noise/spots based on severity
            np.random.seed(i + hash(class_name) % 10000)
            
            if class_name == "clear":
                # Mostly clean with minimal spots
                num_spots = np.random.randint(0, 3)
                spot_color = (220, 180, 140)
                
            elif class_name == "mild":
                # Few red spots
                num_spots = np.random.randint(3, 8)
                spot_color = (200, 150, 150)
                
            elif class_name == "moderate":
                # More red spots and patches
                num_spots = np.random.randint(8, 15)
                spot_color = (180, 120, 120)
                
            else:  # severe
                # Many spots and patches
                num_spots = np.random.randint(15, 25)
                spot_color = (150, 80, 80)
            
            # Draw random spots
            for _ in range(num_spots):
                x = np.random.randint(20, IMG_SIZE[0] - 20)
                y = np.random.randint(20, IMG_SIZE[1] - 20)
                size = np.random.randint(5, 30)
                draw.ellipse(
                    [x - size, y - size, x + size, y + size],
                    fill=spot_color
                )
            
            # Save image
            filename = os.path.join(class_dir, f"{class_name}_{i:03d}.png")
            img.save(filename)
    
    print(f"[OK] Created synthetic dataset with {num_per_class} images per class")

def train_simple_model():
    """Train a simple model on the synthetic dataset."""
    
    print("\nTraining model...")
    
    # Get data generators
    train_gen, val_gen = get_data_generators()
    
    # Build model
    num_classes = len(train_gen.class_indices)
    model, _ = build_model(num_classes)
    
    # Train
    _ = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=5,
        verbose=1
    )
    
    # Save model
    os.makedirs("models", exist_ok=True)
    model.save("models/dermiq_model.h5")
    print("[OK] Model saved to models/dermiq_model.h5")
    
    return model

if __name__ == "__main__":
    create_synthetic_images(num_per_class=15)
    train_simple_model()
    print("\n[OK] Setup complete! You can now run: python app.py")
