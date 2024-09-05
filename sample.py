import pyttsx3  # Add this import for text-to-speech

# Inside the AttendanceApp class
class AttendanceApp:
    def __init__(self, root):
        # Existing code...

        # Initialize the text-to-speech engine
        self.speech_engine = pyttsx3.init()
        self.speech_engine.setProperty('rate', 150)  # Set speed of speech
        self.speech_engine.setProperty('volume', 0.9)  # Set volume level (0.0 to 1.0)

        # Existing code continues...

    def speak(self, message):
        """Function to speak the provided message."""
        self.speech_engine.say(message)
        self.speech_engine.runAndWait()

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
        # Existing auto_scan_fingerprint code...
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
