import os
import glob
import io
import numpy as np
import torch
from PIL import Image

from cnn_model import (
    FaceDocumentCNN,
    CLASS_NAMES,
    MODEL_PATH,
    get_model,
    predict_screening_image,
    preprocess_image_bytes,
)


def test_model_builds_with_expected_output_shape():
    model = FaceDocumentCNN(input_shape=(64, 64, 3), num_classes=4)
    compiled = model.build_model()

    assert compiled.input_shape == (None, 64, 64, 3)
    assert compiled.output_shape == (None, 4)


def test_model_can_predict_on_various_input_shapes():
    model = FaceDocumentCNN(input_shape=(64, 64, 3), num_classes=4)

    # 1. (B, H, W, C) numpy uint8
    dummy_nhwc = np.random.randint(0, 255, size=(2, 64, 64, 3), dtype=np.uint8)
    out1 = model(dummy_nhwc)
    assert out1.shape == (2, 4)

    # 2. (B, C, H, W) torch float32
    dummy_nchw = torch.randn(3, 3, 64, 64)
    out2 = model(dummy_nchw)
    assert out2.shape == (3, 4)

    # 3. (H, W, C) single 3D image
    dummy_hwc = torch.randn(64, 64, 3)
    out3 = model(dummy_hwc)
    assert out3.shape == (1, 4)


def test_trained_model_checkpoint_exists_and_loads():
    assert os.path.exists(MODEL_PATH), f"Trained weights must exist at {MODEL_PATH}"
    model = get_model(MODEL_PATH)
    assert model is not None
    assert isinstance(model, FaceDocumentCNN)


def test_predict_screening_image_on_classes():
    dataset_base = os.path.join(os.path.dirname(__file__), "datasets", "face_document_screening")
    if not os.path.exists(dataset_base):
        return

    for class_name in CLASS_NAMES:
        files = glob.glob(os.path.join(dataset_base, class_name, "*.png"))
        if files:
            with open(files[0], "rb") as fp:
                img_bytes = fp.read()
            res = predict_screening_image(img_bytes)
            assert res["predicted_label"] == class_name
            assert res["confidence"] > 0.5
            assert "class_scores" in res
            assert len(res["class_scores"]) == 4
            if class_name in {"authentic_document", "live_face"}:
                assert res["is_safe"] is True
            else:
                assert res["is_safe"] is False


def test_predict_screening_image_handles_corrupt_data():
    res = predict_screening_image(b"corrupted_non_image_bytes")
    assert res["is_safe"] is False
    assert res["predicted_label"] == "invalid_image"
    assert res["confidence"] == 0.0


def test_predict_screening_image_on_generated_image():
    img = Image.new("RGB", (128, 128), color=(200, 220, 240))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    res = predict_screening_image(buf.getvalue())
    assert "predicted_label" in res
    assert "confidence" in res
    assert isinstance(res["is_safe"], bool)
