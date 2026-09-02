import os
import tempfile

import numpy as np

from cnn_model import FaceDocumentCNN


def test_model_builds_with_expected_output_shape():
    model = FaceDocumentCNN(input_shape=(64, 64, 3), num_classes=4)
    compiled = model.build_model()

    assert compiled.input_shape == (None, 64, 64, 3)
    assert compiled.output_shape == (None, 4)


def test_model_can_predict_on_dummy_batch():
    model = FaceDocumentCNN(input_shape=(64, 64, 3), num_classes=4)
    compiled = model.build_model()

    dummy_batch = np.random.randint(0, 255, size=(2, 64, 64, 3), dtype=np.uint8)
    logits = compiled(dummy_batch)

    assert logits.shape == (2, 4)


def test_model_directory_is_readable():
    with tempfile.TemporaryDirectory() as tmp_dir:
        assert os.path.isdir(tmp_dir)
        assert os.path.exists(tmp_dir)
