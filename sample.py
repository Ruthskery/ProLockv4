import threading
import time
import serial
import adafruit_fingerprint
import nfc
import tkinter as tk
from tkinter import ttk, font, messagebox
from PIL import Image, ImageTk
import RPi.GPIO as GPIO
import requests
from datetime import datetime
import pyttsx3  # Import pyttsx3 for text-to-speech

# API URLs and GPIO configurations
# [Include all your existing constants and GPIO setup code here]

class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fingerprint and NFC Reader")

        # Initialize the text-to-speech engine with eSpeak driver for Raspberry Pi
        try:
            self.speech_engine = pyttsx3.init(driverName='espeak')
            self.speech_engine.setProperty('rate', 150)  # Set speech rate
            self.speech_engine.setProperty('volume', 0.9)  # Set volume level
        except Exception as e:
            print(f"Failed to initialize TTS engine: {e}")

        # Define custom fonts and UI setup
        heading_font = font.Font(family="Helvetica", size=16, weight="bold")
        label_font = font.Font(family="Helvetica", size=12, weight="bold")
        
        # Create and configure UI elements
        # [Include the UI setup code from your provided code]

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def speak(self, message):
        """Function to use TTS engine to speak a given message."""
        try:
            self.speech_engine.say(message)
            self.speech_engine.runAndWait()
        except Exception as e:
            print(f"Error in TTS speak: {e}")

    # Implement TTS in relevant methods
    def record_time_in_fingerprint(self, fingerprint_id, user_name, role_id="2"):
        try:
            current_time_data = self.fetch_current_date_time()
            if not current_time_data:
                return
            url = f"{TIME_IN_FINGERPRINT_URL}?fingerprint_id={fingerprint_id}&time_in={current_time_data['current_time']}&user_name={user_name}&role_id={role_id}"
            response = requests.put(url)
            response.raise_for_status()
            print("Time-In recorded successfully.")
            self.speak(f"Time-In recorded successfully for {user_name}. Welcome!")
        except requests.RequestException as e:
            print("Error", f"Error recording Time-In: {e}")
            self.speak("Error recording Time-In.")

    def record_time_out_fingerprint(self, fingerprint_id):
        try:
            current_time_data = self.fetch_current_date_time()
            if not current_time_data:
                return
            url = f"{TIME_OUT_FINGERPRINT_URL}?fingerprint_id={fingerprint_id}&time_out={current_time_data['current_time']}"
            response = requests.put(url)
            response.raise_for_status()
            print("Time-Out recorded successfully.")
            self.speak("Time-Out recorded successfully. Goodbye!")
        except requests.RequestException as e:
            print(f"Error recording Time-Out: {e}")
            self.speak("Error recording Time-Out.")

    def auto_scan_fingerprint(self):
        # Existing fingerprint scanning logic...
        if name:
            if self.get_schedule(self.finger.finger_id):
                if not self.check_time_in_record_fingerprint(self.finger.finger_id):
                    self.record_time_in_fingerprint(self.finger.finger_id, name)
                    self.unlock_door()
                    self.is_manual_unlock = True
                    self.last_time_in[self.finger.finger_id] = current_time
                    print("Welcome", f"Welcome, {name}! Door unlocked.")
                    self.speak(f"Welcome, {name}! Door unlocked.")
                else:
                    self.record_time_out_fingerprint(self.finger.finger_id)
                    self.lock_door()
                    self.is_manual_unlock = False
                    self.record_all_time_out()
                    print("Goodbye", f"Goodbye, {name}! Door locked.")
                    self.speak(f"Goodbye, {name}! Door locked.")
            else:
                print("No Access", "Access denied due to schedule restrictions.")
                self.speak("Access denied due to schedule restrictions.")
        else:
            print("No Match", "No matching fingerprint found in the database.")
            self.speak("No matching fingerprint found.")

    # Additional methods with TTS integration where needed
    # [Include the rest of your methods with relevant TTS speak calls]

    def on_closing(self):
        self.running = False
        if self.nfc_thread.is_alive():
            self.nfc_thread.join()
        if self.fingerprint_thread.is_alive():
            self.fingerprint_thread.join()
        if self.clf is not None:
            self.clf.close()
        self.root.destroy()

# Create the main window
root = tk.Tk()
app = AttendanceApp(root)

# Run the application
root.mainloop()
