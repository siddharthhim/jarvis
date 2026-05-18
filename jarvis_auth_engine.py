import cv2
import os
import numpy as np
import logging

logger = logging.getLogger("JarvisAuthEngine")

# BUG FIX: default path assumed "assets/" directory existed in the repo —
# it doesn't. We now resolve it relative to this file and create it on init.
_DEFAULT_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "face_data.xml")


class FaceEngine:
    def __init__(self, data_path: str = _DEFAULT_DATA_PATH):
        self.data_path = data_path

        # BUG FIX: ensure the parent directory exists so save() never raises
        # FileNotFoundError.
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)

        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        # BUG FIX: original silently set self.recognizer = None on AttributeError
        # and then let callers do bare attribute access. Now we raise a clear
        # RuntimeError so the problem is immediately visible.
        try:
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        except AttributeError as exc:
            raise RuntimeError(
                "opencv-contrib-python is required for face recognition. "
                "Install it with: pip install opencv-contrib-python"
            ) from exc

        self.has_model = False
        if os.path.exists(self.data_path):
            self.recognizer.read(self.data_path)
            self.has_model = True
            logger.info(f"Face model loaded from {self.data_path}")
        else:
            logger.info("No existing face model found — enroll a user first.")

    def get_faces(self, frame: np.ndarray):
        """Detect faces in a BGR frame. Returns list of (x, y, w, h) tuples."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return self.face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    def enroll(self, faces_data: list, label: int = 1) -> bool:
        """
        Train the recognizer on a list of grayscale face arrays.

        Args:
            faces_data: List of grayscale numpy arrays (one per face sample).
            label: Integer label to assign to this person (default 1).

        Returns:
            True on success, raises on failure.
        """
        if not faces_data:
            raise ValueError("faces_data must not be empty.")
        labels = np.array([label] * len(faces_data))
        self.recognizer.train(faces_data, labels)
        self.recognizer.save(self.data_path)
        self.has_model = True
        logger.info(f"Model trained with {len(faces_data)} samples. Saved to {self.data_path}")
        return True

    def predict(self, face_gray: np.ndarray) -> tuple[int, float]:
        """
        Predict the label for a grayscale face crop.

        Returns:
            (label, confidence) — lower confidence = better match for LBPH.
            Returns (-1, 100.0) if no model is loaded.
        """
        if not self.has_model:
            logger.warning("predict() called but no face model is loaded — enroll first.")
            return -1, 100.0
        return self.recognizer.predict(face_gray)
