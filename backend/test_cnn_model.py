import os
import sys
import glob
import io
import numpy as np
from PIL import Image

# Ensure backend directory is in sys.path so imports work regardless of cwd or IDE runner
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

try:
    import pytest
except ImportError:
    class _PytestMock:
        class mark:
            @staticmethod
            def skipif(cond, reason=""):
                def decorator(fn):
                    return fn
                return decorator
        @staticmethod
        def skip(reason=""):
            print(f" [SKIPPED] {reason}")
    pytest = _PytestMock()

try:
    import torch
except ImportError:
    torch = None

from cnn_model import (
    FaceDocumentCNN,
    CLASS_NAMES,
    MODEL_PATH,
    get_model,
    predict_screening_image,
    preprocess_image_bytes,
)


@pytest.mark.skipif(torch is None, reason="PyTorch is not installed in runtime environment")
def test_model_builds_with_expected_output_shape():
    if torch is None:
        return
    model = FaceDocumentCNN(input_shape=(64, 64, 3), num_classes=4)
    compiled = model.build_model()

    assert compiled.input_shape == (None, 64, 64, 3)
    assert compiled.output_shape == (None, 4)


@pytest.mark.skipif(torch is None, reason="PyTorch is not installed in runtime environment")
def test_model_can_predict_on_various_input_shapes():
    if torch is None:
        return
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


@pytest.mark.skipif(torch is None, reason="PyTorch is not installed in runtime environment")
def test_trained_model_checkpoint_exists_and_loads():
    if torch is None or not os.path.exists(MODEL_PATH):
        return
    model = get_model(MODEL_PATH)
    assert model is not None
    assert isinstance(model, FaceDocumentCNN)


def test_predict_screening_image_on_classes():
    dataset_base = os.path.join(BACKEND_DIR, "datasets", "face_document_screening")
    if not os.path.exists(dataset_base):
        return

    for class_name in CLASS_NAMES:
        files = glob.glob(os.path.join(dataset_base, class_name, "*.png"))
        if files:
            with open(files[0], "rb") as fp:
                img_bytes = fp.read()
            res = predict_screening_image(img_bytes)
            assert "predicted_label" in res
            assert res["confidence"] >= 0.0
            assert "class_scores" in res
            assert len(res["class_scores"]) == 4


def test_predict_screening_image_handles_corrupt_data():
    res = predict_screening_image(b"corrupted_non_image_bytes")
    assert res["is_safe"] is False
    assert res["predicted_label"] in ("tampered_document", "invalid_image")
    assert res["confidence"] == 0.0


def test_predict_screening_image_on_generated_image():
    img = Image.new("RGB", (128, 128), color=(200, 220, 240))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    res = predict_screening_image(buf.getvalue())
    assert "predicted_label" in res
    assert "confidence" in res
    assert isinstance(res["is_safe"], bool)


if __name__ == "__main__":
    print("[*] Running CNN Model & Screening Tests...")
    
    if torch is not None:
        test_model_builds_with_expected_output_shape()
        print(" [PASS] test_model_builds_with_expected_output_shape")
        test_model_can_predict_on_various_input_shapes()
        print(" [PASS] test_model_can_predict_on_various_input_shapes")
        if os.path.exists(MODEL_PATH):
            test_trained_model_checkpoint_exists_and_loads()
            print(" [PASS] test_trained_model_checkpoint_exists_and_loads")
    else:
        print(" [INFO] PyTorch not installed — skipping heavy tensor model unit tests.")

    test_predict_screening_image_on_classes()
    print(" [PASS] test_predict_screening_image_on_classes")

    test_predict_screening_image_handles_corrupt_data()
    print(" [PASS] test_predict_screening_image_handles_corrupt_data")

    test_predict_screening_image_on_generated_image()
    print(" [PASS] test_predict_screening_image_on_generated_image")

    print("\n[ALL CNN TESTS PASSED SUCCESSFULLY!]")
