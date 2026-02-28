import face_recognition
import cv2
import numpy as np
import base64
import io

def capture_face_from_image(image_bytes):
    """
    Takes image bytes (from upload) and returns face encoding
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    face_locations = face_recognition.face_locations(img)
    if len(face_locations) != 1:
        return None, "No face or multiple faces detected"
    face_encoding = face_recognition.face_encodings(img, known_face_locations=face_locations)[0]
    return face_encoding, None

def encode_face_to_str(face_encoding):
    """
    Converts numpy array to base64 string for storing in Firebase
    """
    return base64.b64encode(face_encoding.tobytes()).decode('utf-8')

def decode_face_from_str(face_str):
    """
    Converts base64 string back to numpy array
    """
    face_bytes = base64.b64decode(face_str)
    return np.frombuffer(face_bytes, dtype=np.float64)

def compare_faces(known_encoding, unknown_encoding, tolerance=0.5):
    """
    Compares two face encodings, returns True if match
    """
    return face_recognition.compare_faces([known_encoding], unknown_encoding, tolerance=tolerance)[0]
