import cv2
import os
import numpy as np
import logging

logger = logging.getLogger("JarvisAuthEngine")

class FaceEngine:
    def __init__(self, data_path="assets/face_data.xml"):
        self.data_path = data_path
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        try:
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
            self.has_model = False
            if os.path.exists(self.data_path):
                self.recognizer.read(self.data_path)
                self.has_model = True
                logger.info("Face model loaded.")
        except AttributeError:
            logger.error("opencv-contrib-python required for LBPH.")
            self.recognizer = None

    def get_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return self.face_cascade.detectMultiScale(gray, 1.3, 5)

    def enroll(self, faces_data, label=1):
        if not self.recognizer: return False
        labels = np.array([label] * len(faces_data))
        self.recognizer.train(faces_data, labels)
        self.recognizer.save(self.data_path)
        self.has_model = True
        logger.info(f"Model saved to {self.data_path}")
        return True

    def predict(self, face_gray):
        if not self.recognizer or not self.has_model:
            return -1, 100
        return self.recognizer.predict(face_gray)