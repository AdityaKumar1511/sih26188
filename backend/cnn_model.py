import os
import logging
from io import BytesIO
from typing import Dict, Tuple, Optional

import numpy as np
import torch
from PIL import Image
from torch import nn

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "face_document_cnn.pth")
CLASS_NAMES = [
    "authentic_document",
    "tampered_document",
    "live_face",
    "spoof_face",
]

_MODEL_CACHE: Dict[str, "FaceDocumentCNN"] = {}


class FaceDocumentCNN(nn.Module):
    """CNN for face identity matching and document authenticity screening."""

    def __init__(self, input_shape: Tuple[int, int, int] = (64, 64, 3), num_classes: int = 4):
        super().__init__()
        self.input_shape = (None, *input_shape)
        self.output_shape = (None, num_classes)
        self.num_classes = num_classes
        self.channels = input_shape[-1]
        self.height = input_shape[0]
        self.width = input_shape[1]

        self.feature_extractor = nn.Sequential(
            nn.Conv2d(self.channels, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.BatchNorm2d(32),
            nn.Conv2d(32, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Dropout(0.2),

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.BatchNorm2d(64),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Dropout(0.25),

            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.BatchNorm2d(128),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.35),
            nn.Linear(64, self.num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if not isinstance(x, torch.Tensor):
            x = torch.tensor(x, dtype=torch.float32)

        if x.dtype != torch.float32:
            x = x.to(torch.float32)

        if x.dim() == 3:
            # (H, W, C) -> (1, C, H, W) or (C, H, W) -> (1, C, H, W)
            if x.shape[-1] == self.channels:
                x = x.permute(2, 0, 1).unsqueeze(0).contiguous()
            else:
                x = x.unsqueeze(0).contiguous()
        elif x.dim() == 4:
            # (B, H, W, C) -> (B, C, H, W)
            if x.shape[-1] == self.channels and x.shape[1] != self.channels:
                x = x.permute(0, 3, 1, 2).contiguous()

        return self.classifier(self.feature_extractor(x))

    def build_model(self):
        return self

    def save(self, path: str):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        torch.save(self.state_dict(), path)

    @classmethod
    def load_model(cls, path: str, input_shape=(64, 64, 3), num_classes: int = 4):
        model = cls(input_shape=input_shape, num_classes=num_classes)
        state = torch.load(path, map_location="cpu")
        model.load_state_dict(state)
        model.eval()
        return model


def preprocess_image_bytes(image_bytes: bytes, image_size=(64, 64)) -> torch.Tensor:
    """Convert raw image bytes into a model-ready tensor sized for CNN inference."""
    image = Image.open(BytesIO(image_bytes)).convert("RGB").resize(image_size)
    array = np.asarray(image, dtype=np.float32) / 255.0
    tensor = torch.from_numpy(array).permute(2, 0, 1).unsqueeze(0)
    return tensor


def get_model(model_path: str = MODEL_PATH, image_size=(64, 64)) -> Optional[FaceDocumentCNN]:
    """Return a cached model instance so repeated screening requests avoid reloading weights."""
    cache_key = f"{model_path}:{image_size[0]}x{image_size[1]}"
    if not os.path.exists(model_path):
        return None

    if cache_key not in _MODEL_CACHE:
        model = FaceDocumentCNN(input_shape=(image_size[0], image_size[1], 3), num_classes=len(CLASS_NAMES))
        state = torch.load(model_path, map_location="cpu")
        model.load_state_dict(state)
        model.eval()
        _MODEL_CACHE[cache_key] = model

    return _MODEL_CACHE[cache_key]


def predict_screening_image(image_bytes: bytes, model_path: str = MODEL_PATH, image_size=(64, 64)) -> Dict[str, object]:
    """Runs the trained screening CNN on a single image and returns an interpretable prediction dict."""
    model = get_model(model_path=model_path, image_size=image_size)
    if model is None:
        return {
            "predicted_label": "unknown",
            "confidence": 0.0,
            "class_scores": {label: 0.0 for label in CLASS_NAMES},
            "is_safe": False,
            "details": f"No trained CNN model found at {model_path}.",
        }

    try:
        tensor = preprocess_image_bytes(image_bytes, image_size=image_size)
    except Exception as e:
        logger.warning(f"CNN image preprocessing failed: {e}")
        return {
            "predicted_label": "invalid_image",
            "confidence": 0.0,
            "class_scores": {label: 0.0 for label in CLASS_NAMES},
            "is_safe": False,
            "details": f"Corrupted or unreadable image data: {str(e)}",
        }

    with torch.inference_mode():
        logits = model(tensor)
        probabilities = torch.softmax(logits, dim=1)[0]

    scores = {label: float(probabilities[idx].item()) for idx, label in enumerate(CLASS_NAMES)}
    label_index = int(torch.argmax(probabilities).item())
    predicted_label = CLASS_NAMES[label_index]
    confidence = float(probabilities[label_index].item())

    return {
        "predicted_label": predicted_label,
        "confidence": round(confidence, 4),
        "class_scores": {k: round(v, 4) for k, v in scores.items()},
        "is_safe": predicted_label in {"authentic_document", "live_face"},
        "details": (
            "Human face or authentic document pattern detected with high confidence."
            if predicted_label in {"authentic_document", "live_face"}
            else "Potential spoof, document tampering, or low-quality synthetic pattern detected."
        ),
    }


if __name__ == "__main__":
    model = FaceDocumentCNN(input_shape=(64, 64, 3), num_classes=4)
    dummy = torch.randn(2, 64, 64, 3)
    logits = model(dummy)
    print("input_shape:", model.input_shape)
    print("output_shape:", model.output_shape)
    print("logits_shape:", tuple(logits.shape))
