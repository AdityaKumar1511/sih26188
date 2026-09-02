import json
import os
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageFilter
from torch import nn
from torch.utils.data import DataLoader, Dataset

from cnn_model import FaceDocumentCNN

CLASS_NAMES = [
    "authentic_document",
    "tampered_document",
    "live_face",
    "spoof_face",
]

MODEL_DIR = Path(__file__).resolve().parent / "models"
MODEL_PATH = MODEL_DIR / "face_document_cnn.pth"
METADATA_PATH = MODEL_DIR / "face_document_cnn_meta.json"
DEFAULT_DATASET_DIR = Path(__file__).resolve().parent / "datasets" / "face_document_screening"


def _make_synthetic_image(label_index: int, sample_index: int, width: int = 64, height: int = 64) -> np.ndarray:
    rng = np.random.default_rng((label_index + 1) * 101 + sample_index)
    image = np.zeros((height, width, 3), dtype=np.uint8)

    if label_index == 0:
        image[:, :, 0] = 140 + rng.integers(0, 30, size=(height, width))
        image[:, :, 1] = 170 + rng.integers(0, 30, size=(height, width))
        image[:, :, 2] = 210 + rng.integers(0, 25, size=(height, width))
        image[8:height - 8, 8:width - 8] += 30
    elif label_index == 1:
        image[:, :, 0] = 50 + rng.integers(0, 40, size=(height, width))
        image[:, :, 1] = 50 + rng.integers(0, 40, size=(height, width))
        image[:, :, 2] = 70 + rng.integers(0, 50, size=(height, width))
        image[10:height - 10, 10:width - 10] = 30
        # introduce diagonal tampering pattern
        for i in range(height):
            image[i, i:i + 6] = 255
    elif label_index == 2:
        face = (np.clip(np.sin(np.linspace(0, 2 * np.pi, width)) + 1, 0, 1) * 160).astype(np.uint8)
        for row in range(height):
            image[row, :, 0] = 120 + face
            image[row, :, 1] = 90 + face
            image[row, :, 2] = 80 + face
        overlay = np.full((height, width), 255, dtype=np.uint8)
        patch = overlay[height // 3:2 * height // 3, width // 4:3 * width // 4]
        patch_3 = np.stack([
            (patch * 0.7).astype(np.uint8),
            (patch * 0.6).astype(np.uint8),
            (patch * 0.5).astype(np.uint8),
        ], axis=-1)
        image[height // 3:2 * height // 3, width // 4:3 * width // 4] = patch_3
    else:
        image[:, :, 0] = 90 + rng.integers(0, 40, size=(height, width))
        image[:, :, 1] = 90 + rng.integers(0, 40, size=(height, width))
        image[:, :, 2] = 95 + rng.integers(0, 40, size=(height, width))
        image[:, :, 1] += 30
        image[::2, :] = 20

    image = np.clip(image + rng.integers(-12, 13, size=image.shape), 0, 255).astype(np.uint8)
    return image


class SyntheticScreeningDataset(Dataset):
    def __init__(self, samples_per_class: int = 180, input_shape=(64, 64, 3), classes=None):
        self.classes = classes or CLASS_NAMES
        self.samples = []
        for label_index, _ in enumerate(self.classes):
            for sample_index in range(samples_per_class):
                image = _make_synthetic_image(label_index, sample_index, width=input_shape[1], height=input_shape[0])
                self.samples.append((image, label_index))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        image, label = self.samples[idx]
        image = torch.tensor(image, dtype=torch.float32).permute(2, 0, 1) / 255.0
        label = torch.tensor(label, dtype=torch.long)
        return image, label


def _ensure_dataset_dir(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    for idx, name in enumerate(CLASS_NAMES):
        class_dir = root / name
        class_dir.mkdir(exist_ok=True)
        if not any(class_dir.iterdir()):
            for sample in range(30):
                image = _make_synthetic_image(idx, sample)
                pil_image = Image.fromarray(image, mode="RGB")
                pil_image = pil_image.filter(ImageFilter.GaussianBlur(0.2))
                pil_image.save(class_dir / f"sample_{sample:03d}.png")


def train_and_save_model(epochs: int = 6, batch_size: int = 32, learning_rate: float = 1e-3):
    os.makedirs(MODEL_DIR, exist_ok=True)
    dataset_root = DEFAULT_DATASET_DIR
    _ensure_dataset_dir(dataset_root)

    dataset = SyntheticScreeningDataset(samples_per_class=180)
    train_loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0)

    model = FaceDocumentCNN(input_shape=(64, 64, 3), num_classes=len(CLASS_NAMES))
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    model.train()
    for epoch in range(epochs):
        running_loss = 0.0
        correct = 0
        total = 0
        for images, labels in train_loader:
            optimizer.zero_grad()
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            predictions = logits.argmax(dim=1)
            correct += (predictions == labels).sum().item()
            total += labels.size(0)

        epoch_loss = running_loss / max(1, total)
        epoch_acc = correct / max(1, total)
        print(f"Epoch {epoch + 1}/{epochs} - loss: {epoch_loss:.4f} - acc: {epoch_acc:.4f}")

    model.save(str(MODEL_PATH))
    metadata = {
        "classes": CLASS_NAMES,
        "input_shape": [64, 64, 3],
        "num_classes": len(CLASS_NAMES),
        "epochs": epochs,
        "dataset_dir": str(dataset_root),
        "model_path": str(MODEL_PATH),
    }
    with open(METADATA_PATH, "w", encoding="utf-8") as fp:
        json.dump(metadata, fp, indent=2)

    return model


if __name__ == "__main__":
    print("Training synthetic face and document CNN...")
    model = train_and_save_model()
    print("Saved model to:", MODEL_PATH)
    print("Saved metadata to:", METADATA_PATH)
    print("Sample output shape:", tuple(model(torch.randn(2, 64, 64, 3)).shape))
