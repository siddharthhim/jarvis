import cv2
import os
import numpy as np
import logging

logger = logging.getLogger("JarvisAuthEngine")

# FIX: ensure the assets directory exists so the model path is always valid
_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
os.makedirs(_ASSETS_DIR, exist_ok=True)


class FaceEngine:
    """
    Face detection and recognition using OpenCV LBPH.

    NOTE: This requires opencv-contrib-python (not opencv-python).
    Install with: pip install opencv-contrib-python

    SECURITY NOTE: face_data.xml stores biometric model weights.
    Do NOT commit assets/ to version control — add it to .gitignore.
    """

    # FIX: confidence threshold — lower = stricter. LBPH returns distance (0 = perfect match).
    CONFIDENCE_THRESHOLD = 70

    def __init__(self, data_path: str | None = None):
        self.data_path = data_path or os.path.join(_ASSETS_DIR, "face_data.xml")

        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        self.recognizer  = None
        self.has_model   = False

        try:
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
            if os.path.exists(self.data_path):
                self.recognizer.read(self.data_path)
                self.has_model = True
                logger.info("Face model loaded.")
        except AttributeError:
            logger.error(
                "opencv-contrib-python is required for LBPH face recognition. "
                "Install with: pip install opencv-contrib-python"
            )

    def get_faces(self, frame: np.ndarray):
        """Returns list of (x, y, w, h) bounding boxes detected in frame."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return self.face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    def enroll(self, faces_data: list[np.ndarray], label: int = 1) -> bool:
        """
        Train the recognizer on a set of face images.
        faces_data: list of grayscale face arrays (cropped to face region).
        label: integer ID for the person being enrolled.
        """
        if not self.recognizer:
            logger.error("Cannot enroll — recognizer not initialized.")
            return False
        # FIX: validate input before training
        if not faces_data or len(faces_data) < 5:
            logger.error("Need at least 5 face samples for reliable enrollment.")
            return False

        labels = np.array([label] * len(faces_data))
        self.recognizer.train(faces_data, labels)
        self.recognizer.save(self.data_path)
        self.has_model = True
        logger.info(f"Face model saved ({len(faces_data)} samples, label={label}).")
        return True

    def predict(self, face_gray: np.ndarray) -> tuple[int, float]:
        """
        Predict the label for a face image.
        Returns (label, confidence). Higher confidence = worse match in LBPH.
        """
        if not self.recognizer or not self.has_model:
            return -1, 100.0
        return self.recognizer.predict(face_gray)

    def is_authorized(self, face_gray: np.ndarray) -> bool:
        """
        Convenience method — returns True if face matches within confidence threshold.
        FIX: added this so auth check is a single readable call in the agent.
        """
        label, confidence = self.predict(face_gray)
        return label != -1 and confidence < self.CONFIDENCE_THRESHOLD
