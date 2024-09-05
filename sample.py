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

Traceback (most recent call last):
  File "/home/miko/Documents/prolock/myenv/lib/python3.11/site-packages/pyttsx3/__init__.py", line 20, in init
    eng = _activeEngines[driverName]
  File "/usr/lib/python3.11/weakref.py", line 136, in __getitem__
    o = self.data[key]()
KeyError: None

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/miko/Downloads/prolockv2/test/prolock_voice.py", line 631, in <module>
    app = AttendanceApp(root)
  File "/home/miko/Downloads/prolockv2/test/prolock_voice.py", line 46, in __init__
    self.speech_engine = pyttsx3.init()
  File "/home/miko/Documents/prolock/myenv/lib/python3.11/site-packages/pyttsx3/__init__.py", line 22, in init
    eng = Engine(driverName, debug)
  File "/home/miko/Documents/prolock/myenv/lib/python3.11/site-packages/pyttsx3/engine.py", line 30, in __init__
    self.proxy = driver.DriverProxy(weakref.proxy(self), driverName, debug)
  File "/home/miko/Documents/prolock/myenv/lib/python3.11/site-packages/pyttsx3/driver.py", line 50, in __init__
    self._module = importlib.import_module(name)
  File "/usr/lib/python3.11/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
  File "<frozen importlib._bootstrap>", line 1206, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1178, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1149, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 940, in exec_module
  File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
  File "/home/miko/Documents/prolock/myenv/lib/python3.11/site-packages/pyttsx3/drivers/espeak.py", line 9, in <module>
    from . import _espeak, toUtf8, fromUtf8
  File "/home/miko/Documents/prolock/myenv/lib/python3.11/site-packages/pyttsx3/drivers/_espeak.py", line 101, in <module>
    Initialize = cfunc('espeak_Initialize', dll, c_int,
  File "/home/miko/Documents/prolock/myenv/lib/python3.11/site-packages/pyttsx3/drivers/_espeak.py", line 15, in cfunc
    return CFUNCTYPE(result, *atypes)((name, dll), tuple(aflags))
AttributeError: 'NoneType' object has no attribute '_handle

