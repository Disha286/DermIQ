import tensorflow as tf
import numpy as np
from sklearn.utils.class_weight import compute_class_weight
from src.preprocess import get_data_generators
from src.model import build_model

EPOCHS_FROZEN = 10
EPOCHS_FINE_TUNE = 10
MODEL_SAVE_PATH = "models/dermiq_model.h5"

def train():
    train_gen, val_gen = get_data_generators()
    num_classes = len(train_gen.class_indices)
    print("Classes:", train_gen.class_indices)

    # Compute class weights to handle imbalance
    labels = train_gen.classes
    class_weights = compute_class_weight(
        class_weight='balanced',
        classes=np.unique(labels),
        y=labels
    )
    class_weight_dict = dict(enumerate(class_weights))
    print("Class weights:", class_weight_dict)

    model, base_model = build_model(num_classes)

    print("\n--- Phase 1: Training top layers ---")
    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS_FROZEN,
        class_weight=class_weight_dict,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(
                patience=3,
                restore_best_weights=True
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                factor=0.5,
                patience=2,
                verbose=1
            )
        ]
    )

    print("\n--- Phase 2: Fine-tuning ---")
    base_model.trainable = True
    for layer in base_model.layers[:-30]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS_FINE_TUNE,
        class_weight=class_weight_dict,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(
                patience=3,
                restore_best_weights=True
            ),
            tf.keras.callbacks.ModelCheckpoint(
                MODEL_SAVE_PATH,
                save_best_only=True,
                verbose=1
            )
        ]
    )

    print(f"\nModel saved to {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    train()