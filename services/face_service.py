import numpy as np
import base64
import tempfile
import os
from io import BytesIO
from PIL import Image
import traceback


def capture_face_from_image(image_bytes):
    """
    Takes image bytes and returns face embedding using DeepFace.
    Returns (embedding, None) on success or (None, error_message) on failure.
    """
    tmp_path = None
    try:
        from deepface import DeepFace
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        image.save(tmp.name, format="JPEG")
        tmp.close()
        tmp_path = tmp.name

        result = DeepFace.represent(
            img_path          = tmp_path,
            model_name        = "Facenet",
            enforce_detection = False,
        )
        if not result or len(result) == 0:
            return None, "No face detected"
        return np.array(result[0]["embedding"]), None
    except Exception:
        traceback.print_exc()
        return None, "Face processing failed"
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def compare_faces(known_embedding, unknown_embedding, threshold=10.0):
    """
    Compares two embeddings using Euclidean distance.
    Returns True if same person.
    """
    a = np.array(known_embedding)
    b = np.array(unknown_embedding)
    distance = float(np.linalg.norm(a - b))
    return distance < threshold