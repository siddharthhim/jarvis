import cv2
import os
import sys
import time
import threading
import pyttsx3
import customtkinter as ctk
from PIL import Image, ImageTk
from jarvis_auth_engine import FaceEngine

engine = pyttsx3.init()
def speak(text):
    def _speak():
        engine.say(text)
        engine.runAndWait()
    threading.Thread(target=_speak, daemon=True).start()

ctk.set_appearance_mode("dark")

class JarvisAuthGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("JARVIS | BIOMETRIC ACCESS")
        self.geometry("600x700")
        self.configure(fg_color="#020202")
        self.attributes("-topmost", True)

        self.engine = FaceEngine()
        self.cap = cv2.VideoCapture(0)
        
        self.lbl_title = ctk.CTkLabel(self, text="IDENTITY VERIFICATION", font=("Orbitron", 20, "bold"), text_color="#00d2ff")
        self.lbl_title.pack(pady=20)

        self.video_frame = ctk.CTkLabel(self, text="", fg_color="black", width=500, height=400)
        self.video_frame.pack(pady=10)

        self.lbl_status = ctk.CTkLabel(self, text="INITIALIZING...", font=("Arial", 16), text_color="#00d2ff")
        self.lbl_status.pack(pady=20)

        self.enroll_count = 0
        self.enroll_data = []
        self.is_authenticated = False
        
        if not self.engine.has_model:
            speak("I don't have your identity data yet. Please look at the camera.")
            self.lbl_status.configure(text="MODE: ENROLLING IDENTITY...")
        else:
            speak("Welcome back. Please look at the camera for identity scan.")
            self.lbl_status.configure(text="MODE: SCANNING...")

        self.update_video()

    def update_video(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            faces = self.engine.get_faces(frame)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 210, 255), 2)
                face_roi = gray[y:y+h, x:x+w]
                face_roi = cv2.resize(face_roi, (200, 200))

                if not self.engine.has_model:
                    if self.enroll_count < 20:
                        self.enroll_data.append(face_roi)
                        self.enroll_count += 1
                        self.lbl_status.configure(text=f"ENROLLING... {int((self.enroll_count/20)*100)}%")
                    elif self.enroll_count == 20:
                        self.engine.enroll(self.enroll_data)
                        self.enroll_count += 1
                        speak("Identity saved successfully.")
                        self.lbl_status.configure(text="IDENTITY SAVED! RESTARTING...")
                        self.after(2000, self.finish_auth)
                else:
                    label, confidence = self.engine.predict(face_roi)
                    if confidence < 75:
                        self.lbl_status.configure(text="MATCH CONFIRMED | ACCESS GRANTED")
                        if not self.is_authenticated:
                            self.is_authenticated = True
                            speak("Identity confirmed. Access granted.")
                            self.after(1500, self.finish_auth)
                    else:
                        self.lbl_status.configure(text="UNKNOWN IDENTITY | ANALYZING...")

            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            img_tk = ctk.CTkImage(light_image=img, dark_image=img, size=(500, 400))
            self.video_frame.configure(image=img_tk)
            self.video_frame.image = img_tk

        self.after(10, self.update_video)

    def finish_auth(self):
        self.cap.release()
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = JarvisAuthGUI()
    app.mainloop()