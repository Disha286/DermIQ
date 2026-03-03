from src.preprocess import get_data_generators

print("Loading data generators...")
train_gen, val_gen = get_data_generators()
print("Classes:", train_gen.class_indices)
print("Training samples:", train_gen.samples)
print("Validation samples:", val_gen.samples)
print("All good!")