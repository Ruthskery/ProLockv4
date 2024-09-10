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

# API URLs for Fingerprint, NFC, and Current Date-Time
FINGERPRINT_API_URL = "https://prolocklogger.pro/api/getuserbyfingerprint/"
TIME_IN_FINGERPRINT_URL = "https://prolocklogger.pro/api/logs/time-in/fingerprint"
TIME_OUT_FINGERPRINT_URL = "https://prolocklogger.pro/api/logs/time-out/fingerprint"
RECENT_LOGS_FINGERPRINT_URL2 = 'https://prolocklogger.pro/api/recent-logs/by-fingerid'
LAB_SCHEDULE_FINGERPRINT_URL = 'https://prolocklogger.pro/api/lab-schedules/fingerprint/'

USER_INFO_URL = 'https://prolocklogger.pro/api/user-information/by-id-card'
RECENT_LOGS_URL = 'https://prolocklogger.pro/api/recent-logs'
TIME_IN_URL = 'https://prolocklogger.pro/api/logs/time-in'
TIME_OUT_URL = 'https://prolocklogger.pro/api/logs/time-out'
RECENT_LOGS_URL2 = 'https://prolocklogger.pro/api/recent-logs/by-uid'
CURRENT_DATE_TIME_URL = 'https://prolocklogger.pro/api/current-date-time'
LAB_SCHEDULE_URL = 'https://prolocklogger.pro/api/student/lab-schedule/rfid/'
LOGS_URL = 'https://prolocklogger.pro/api/logs'

# Faculty and Admin API endpoints
API_URL = 'https://prolocklogger.pro/api'
FACULTIES_URL = f'{API_URL}/users/role/2'
ENROLL_URL = f'{API_URL}/users/update-fingerprint'
ADMIN_URL = f'{API_URL}/admin/role/1'

# GPIO pin configuration for the solenoid lock and buzzer
SOLENOID_PIN = 17
BUZZER_PIN = 27

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(SOLENOID_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)


class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fingerprint and NFC Reader")

        # Attempt to initialize the text-to-speech engine
        try:
            self.speech_engine = pyttsx3.init(driverName='espeak')  # Ensure the correct driver is used for Raspberry Pi
            self.speech_engine.setProperty('rate', 150)  # Set speech rate
            self.speech_engine.setProperty('volume', 0.9)  # Set volume level
        except Exception as e:
            print(f"Failed to initialize TTS engine: {e}")
            self.speech_engine = None  # Set to None to handle in speak method

        # Define custom fonts
        heading_font = font.Font(family="Helvetica", size=16, weight="bold")
        label_font = font.Font(family="Helvetica", size=12, weight="bold")

        # Create the main frame with specified dimensions
        self.main_frame = ttk.Frame(self.root, padding="20", width=1400, height=800, style="MainFrame.TFrame")
        self.main_frame.pack(fill="both", expand=True)
        self.main_frame.pack_propagate(False)  # Prevent the frame from resizing to fit its contents

        # Initialize the Attendance System UI
        self.create_attendance_ui(heading_font, label_font)

        # Initialize NFC reader
        try:
            self.clf = nfc.ContactlessFrontend('usb')
        except Exception as e:
            print("NFC Error", f"Failed to initialize NFC reader: {e}")
            self.clf = None

        self.running = True
        self.nfc_thread = threading.Thread(target=self.read_nfc_loop)
        self.nfc_thread.start()

        # Initialize serial connection for fingerprint sensor
        self.finger = self.initialize_serial()

        # Start fingerprint scanning in a separate thread
        self.fingerprint_thread = threading.Thread(target=self.auto_scan_fingerprint)
        self.fingerprint_thread.start()

        # Track the last time-in for each user by fingerprint ID
        self.last_time_in = {}
        self.is_manual_unlock = False  # Flag to check if the door was manually unlocked

        # Start periodic checking of log status
        self.root.after(1000, self.check_log_status_periodically)  # Check log status every 10 seconds

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_attendance_ui(self, heading_font, label_font):
        # Attendance System UI
        self.attendance_frame = ttk.Frame(self.main_frame, padding="20", style="MainFrame.TFrame")
        self.attendance_frame.pack(fill="both", expand=True)

        # Create the heading frame to organize images and heading text
        heading_frame = ttk.Frame(self.attendance_frame, padding="10", style="ContainerFrame.TFrame")
        heading_frame.pack(fill="x")

        # Load and place the left image (60x30)
        left_image_path = "prolockk.png"  # Replace with your left image file path
        left_image = Image.open(left_image_path).resize((170, 50))
        left_photo = ImageTk.PhotoImage(left_image)
        # Modify the left image to act as a button
        left_image_label = tk.Button(
            heading_frame, 
            image=left_photo, 
            bg="#F6F5FB", 
            command=self.open_enrollment_form
        )
        left_image_label.image = left_photo  # Keep a reference to avoid garbage collection
        left_image_label.pack(side="left", padx=1)

        # Create a separate frame for the main heading to center it
        center_frame = ttk.Frame(heading_frame, style="ContainerFrame.TFrame")
        center_frame.pack(side="left", fill="x", expand=True)

        # Create the main heading and center it
        main_heading = tk.Label(center_frame, text="Fingerprint and RFID Attendance System", font=heading_font, fg="#000000", bg="#F6F5FB")
        main_heading.pack(anchor="center")  # Center the label in the frame

        # Load and place the first right image (40x40)
        right_image1_path = "cspclogo.png"  # Replace with your first right image file path
        right_image1 = Image.open(right_image1_path).resize((60, 60))
        right_photo1 = ImageTk.PhotoImage(right_image1)
        right_image_label1 = tk.Label(heading_frame, image=right_photo1, bg="#F6F5FB")
        right_image_label1.image = right_photo1  # Keep a reference to avoid garbage collection
        right_image_label1.pack(side="right", padx=5)

        # Load and place the second right image (40x40)
        right_image2_path = "ccslogo.png"  # Replace with your second right image file path
        right_image2 = Image.open(right_image2_path).resize((60, 60))
        right_photo2 = ImageTk.PhotoImage(right_image2)
        right_image_label2 = tk.Label(heading_frame, image=right_photo2, bg="#F6F5FB")
        right_image_label2.image = right_photo2  # Keep a reference to avoid garbage collection
        right_image_label2.pack(side="right", padx=5)

        # Create the main container for the fingerprint and NFC components
        top_frame = ttk.Frame(self.attendance_frame, padding="10", style="ContainerFrame.TFrame")
        top_frame.pack(side="top", fill="x")

        # Fingerprint frame
        left_frame = ttk.Frame(top_frame, padding="10", style="ContainerFrame.TFrame")
        left_frame.pack(side="left", fill="y", expand=True)
        fingerprint_label = ttk.Label(left_frame, text="Fingerprint Sensor", font=("Arial", 16, "bold"), background="#F6F5FB")
        fingerprint_label.pack(pady=20)

        # Load and resize an image for fingerprint
        image_path = "fingericon.png"  # Replace with your image file path
        desired_width = 150
        desired_height = 130

        image = Image.open(image_path)
        image = image.resize((desired_width, desired_height))
        photo = ImageTk.PhotoImage(image)

        image_label = tk.Label(left_frame, image=photo, bg="#F6F5FB")
        image_label.image = photo  # Keep a reference to the image
        image_label.pack()

        # NFC frame
        right_frame = ttk.Frame(top_frame, padding="10", style="ContainerFrame.TFrame")
        right_frame.pack(side="right", fill="y", expand=True)

        # Student Number, Name, Year, Section labels and entries
        self.student_number_entry = self.create_label_entry(right_frame, "Student Number:", label_font)
        self.name_entry = self.create_label_entry(right_frame, "Name:", label_font)
        self.year_entry = self.create_label_entry(right_frame, "Year:", label_font)
        self.section_entry = self.create_label_entry(right_frame, "Section:", label_font)

        # Error Message Label
        self.error_label = tk.Label(self.attendance_frame, text="", font=("Helvetica", 10, "bold", "italic"), foreground="red", bg="#000000")
        self.error_label.pack(pady=10)

        # Logs Table
        self.create_logs_table(self.attendance_frame)

    def open_enrollment_form(self):
        # Hide the attendance frame
        self.attendance_frame.pack_forget()

        # Create and show the enrollment form
        self.enrollment_frame = FingerprintEnrollment(self.root, self.show_attendance_form)
        self.enrollment_frame.pack(fill="both", expand=True)

    def show_attendance_form(self):
        # Hide the enrollment frame and show the attendance form again
        self.enrollment_frame.pack_forget()
        self.attendance_frame.pack(fill="both", expand=True)

    def initialize_serial(self):
        try:
            uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)
            return adafruit_fingerprint.Adafruit_Fingerprint(uart)
        except serial.SerialException as e:
            print("Serial Error", f"Failed to connect to serial port: {e}")
            return None

    def auto_scan_fingerprint(self):
        failed_attempts = 0  # Initialize the counter for failed attempts

        while self.running:
            if not self.finger:
                return

            print("Waiting for fingerprint image...")
            while self.finger.get_image() != adafruit_fingerprint.OK:
                if not self.running:
                    return
                time.sleep(0.5)

            print("Templating...")
            if self.finger.image_2_tz(1) != adafruit_fingerprint.OK:
                print("Error", "Failed to template the fingerprint image.")
                continue

            print("Searching...")
            if self.finger.finger_search() != adafruit_fingerprint.OK:
                print("Error", "Failed to search for fingerprint match.")
                self.speak(f"Error, Failed to search for fingerprint match.")
                failed_attempts += 1
                self.check_failed_attempts(failed_attempts)  # Check failed attempts and trigger the buzzer if needed
                continue

            # Reset failed attempts if successful
            failed_attempts = 0

            print("Detected fingerprint ID:", self.finger.finger_id, "with confidence", self.finger.confidence)

            # Fetch user details using API
            name = self.get_user_details(self.finger.finger_id)

            if name:
                if self.get_schedule(self.finger.finger_id):  # Check if the current time is within the allowed schedule
                    # Fetch current time for comparison
                    current_time_data = self.fetch_current_date_time()
                    if not current_time_data:
                        return
                    current_time = datetime.strptime(current_time_data['current_time'], "%H:%M")

                    # Check if the user has no time-in record
                    if not self.check_time_in_record_fingerprint(self.finger.finger_id):
                        self.record_time_in_fingerprint(self.finger.finger_id, name)
                        self.unlock_door()
                        self.is_manual_unlock = True  # Set flag to indicate manual unlock
                        self.last_time_in[self.finger.finger_id] = current_time  # Store the time-in time
                        print("Welcome", f"Welcome, {name}! Door unlocked.")
                        self.speak(f"Welcome, {name}! Door unlocked.")
                    else:
                        self.record_time_out_fingerprint(self.finger.finger_id)
                        self.lock_door()
                        self.is_manual_unlock = False  # Reset flag as door is locked again
                        self.record_all_time_out()  # Record time-out for all entries without time-out
                        print("Goodbye", f"Goodbye, {name}! Door locked.")
                        self.speak(f"Goodbye, {name}! Door locked.")
                else:
                    print("No Access", "Access denied due to schedule restrictions.")
                    self.speak("Access denied due to schedule restrictions.")
            else:
                print("No Match", "No matching fingerprint found in the database.")
                self.speak("No matching fingerprint found.")

    def create_label_entry(self, frame, text, font_style):
        label = ttk.Label(frame, text=text, font=font_style, background="#F6F5FB")
        label.pack(pady=5)
        entry = ttk.Entry(frame, font=font_style)
        entry.pack(pady=5)
        return entry

    def create_logs_table(self, parent_frame):
        # Create a new style for the Treeview with background color set to #D3D1ED
        style = ttk.Style()
        style.configure("LogsTable.Treeview.Heading", background="#D3D1ED", font=("Helvetica", 10, "bold"))
        style.configure("LogsTable.Treeview", background="#F6F5FB", fieldbackground="#F6F5FB", rowheight=25)
        style.map("LogsTable.Treeview", background=[('selected', '#B0B0E0')])  # Optional: set a different color for selected rows
        table_frame = ttk.Frame(parent_frame, padding="10", style="ContainerFrame.TFrame")
        table_frame.pack(side="bottom", fill="both", expand=True)
        columns = ("Date", "Name", "PC", "Student Number", "Year", "Section", "Faculty", "Time-in", "Time-out")
        self.logs_tree = ttk.Treeview(table_frame, columns=columns, show='headings', style="LogsTable.Treeview")
        self.logs_tree.pack(pady=10, fill='both', expand=True)
        for col in columns:
            self.logs_tree.heading(col, text=col)
            self.logs_tree.column(col, minwidth=100, width=100, anchor='center')

    def fetch_current_date_time(self):
        try:
            response = requests.get(CURRENT_DATE_TIME_URL)
            response.raise_for_status()
            data = response.json()
            if 'day_of_week' in data and 'current_time' in data:
                return data
            else:
                print("Error: Missing expected keys in the API response.")
                return None
        except requests.RequestException as e:
            print(f"Error fetching current date and time from API: {e}")
            return None

    def get_user_details(self, fingerprint_id):
        try:
            response = requests.get(f"{FINGERPRINT_API_URL}{fingerprint_id}")
            response.raise_for_status()
            data = response.json()
            return data.get('name', None)
        except requests.RequestException as e:
            print("API Error", f"Failed to fetch data from API: {e}")
            return None

    def record_time_in_fingerprint(self, fingerprint_id, user_name, role_id="2"):
        try:
            current_time_data = self.fetch_current_date_time()
            if not current_time_data:
                return
            url = f"{TIME_IN_FINGERPRINT_URL}?fingerprint_id={fingerprint_id}&time_in={current_time_data['current_time']}&user_name={user_name}&role_id={role_id}"
            response = requests.put(url)
            response.raise_for_status()
            print("Time-In recorded successfully.")
            print("Success", "Time-In recorded successfully.")
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

    def check_log_status_periodically(self):
        self.fetch_latest_log_status()
        self.root.after(10000, self.check_log_status_periodically)  # Call again after 10 seconds

    def fetch_latest_log_status(self):
        try:
            response = requests.get(LOGS_URL)
            response.raise_for_status()
            logs = response.json().get("logs", [])

            if logs:
                latest_log = logs[-1]  # Get the latest log (assumes logs are in chronological order)
                status = latest_log.get("status", "")

                # Only lock the door if it was not manually unlocked
                if not self.is_manual_unlock:
                    if status == "close":
                        self.lock_door()
                    elif status == "open":
                        self.unlock_door()
        except requests.RequestException as e:
            print(f"Error fetching log status: {e}")

    def unlock_door(self):
        GPIO.output(SOLENOID_PIN, GPIO.LOW)
        print("Door unlocked.")

    def lock_door(self):
        GPIO.output(SOLENOID_PIN, GPIO.HIGH)
        print("Door locked.")

    def check_time_in_record_fingerprint(self, fingerprint_id):
        try:
            url = f"{RECENT_LOGS_FINGERPRINT_URL2}?fingerprint_id={fingerprint_id}"
            response = requests.get(url)
            response.raise_for_status()
            logs = response.json()
            return any(log.get('time_in') and not log.get('time_out') for log in logs)
        except requests.RequestException as e:
            print(f"Error checking Time-In record: {e}")
            return False

    def record_all_time_out(self):
        try:
            response = requests.get(RECENT_LOGS_URL)
            response.raise_for_status()
            logs = response.json()

            for log in logs:
                uid = log.get('UID')
                if log.get('time_in') and not log.get('time_out') and uid:
                    default_time_out = "00:00"
                    url = f"{TIME_OUT_URL}?rfid_number={uid}&time_out={default_time_out}"
                    response = requests.put(url)
                    response.raise_for_status()
                    print(f"Time-Out recorded for UID {uid} at {default_time_out}.")

            self.refresh_logs_table()

        except requests.RequestException as e:
            print(f"Error updating default time-out records: {e}")

    def refresh_logs_table(self):
        self.root.after(100, self.fetch_recent_logs)

    def fetch_recent_logs(self):
        try:
            response = requests.get(RECENT_LOGS_URL)
            response.raise_for_status()
            logs = response.json()
            for i in self.logs_tree.get_children():
                self.logs_tree.delete(i)
            for log in logs:
                self.logs_tree.insert("", "end", values=(
                    log.get('date', 'N/A'),
                    log.get('user_name', 'N/A'),
                    log.get('pc_name', 'N/A'),
                    log.get('user_number', 'N/A'),
                    log.get('year', 'N/A'),
                    log.get('block_name', 'N/A'),
                    log.get('role_name', 'N/A'),
                    log.get('time_in', 'N/A'),
                    log.get('time_out', 'N/A')
                ))
        except requests.RequestException as e:
            self.update_result(f"Error fetching recent logs: {e}")

    def read_nfc_loop(self):
        while self.running:
            try:
                tag = self.clf.connect(rdwr={'on-connect': lambda tag: False})
                if tag:
                    uid = tag.identifier.hex()
                    self.fetch_user_info(uid)
                    time.sleep(1)
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)

    def fetch_user_info(self, uid):
        try:
            url = f'{USER_INFO_URL}?id_card_id={uid}'
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            self.student_number_entry.delete(0, tk.END)
            self.student_number_entry.insert(0, data.get('user_number', 'None'))

            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, data.get('user_name', 'None'))

            self.year_entry.delete(0, tk.END)
            self.year_entry.insert(0, data.get('year', 'None'))

            self.section_entry.delete(0, tk.END)
            self.section_entry.insert(0, data.get('block', 'None'))

            self.error_label.config(text="")

            current_time_data = self.fetch_current_date_time()
            if not current_time_data:
                return

            current_time = datetime.strptime(current_time_data['current_time'], "%H:%M")

            if self.check_time_in_record(uid):
                self.record_time_out(uid)
            else:
                self.record_time_in(uid, data.get('user_name', 'None'), data.get('year', 'None'))
                self.last_time_in[uid] = current_time

        except requests.HTTPError as http_err:
            if response.status_code == 404:
                self.clear_data()
                self.update_result("Card is not registered, Please contact the administrator.")
            else:
                self.update_result(f"HTTP error occurred: {http_err}")
        except requests.RequestException as e:
            self.update_result(f"Error fetching user info: {e}")

    def check_time_in_record(self, rfid_number):
        try:
            url = f'{RECENT_LOGS_URL2}?rfid_number={rfid_number}'
            response = requests.get(url)
            response.raise_for_status()
            logs = response.json()
            return any(log.get('time_in') and not log.get('time_out') for log in logs)
        except requests.RequestException as e:
            self.update_result(f"Error checking Time-In record: {e}")
            return False

    def record_time_in(self, rfid_number, user_name, year):
        if not self.get_rfid_schedule(rfid_number):
            self.update_result("Access denied: Not within scheduled time.")
            return

        try:
            current_time_data = self.fetch_current_date_time()
            if not current_time_data:
                return
            url = f"{TIME_IN_URL}?rfid_number={rfid_number}&time_in={current_time_data['current_time']}&year={year}&user_name={user_name}&role_id=3"
            response = requests.put(url)
            response.raise_for_status()
            print("Time-In recorded successfully.")
            self.update_result("Time-In recorded successfully.")
            self.fetch_recent_logs()
        except requests.RequestException as e:
            self.update_result(f"Error recording Time-In: {e}")

    def record_time_out(self, rfid_number):
        if not self.get_rfid_schedule(rfid_number):
            self.update_result("Access denied: Not within scheduled time.")
            return

        try:
            current_time_data = self.fetch_current_date_time()
            if not current_time_data:
                return
            if not self.check_time_in_record(rfid_number):
                self.update_result("No Time-In record found for this RFID. Cannot record Time-Out.")
                return

            url = f"{TIME_OUT_URL}?rfid_number={rfid_number}&time_out={current_time_data['current_time']}"
            response = requests.put(url)
            response.raise_for_status()
            print("Time-Out recorded successfully.")
            self.update_result("Time-Out recorded successfully.")
            self.fetch_recent_logs()
        except requests.RequestException as e:
            self.update_result(f"Error recording Time-Out: {e}")

    def clear_data(self):
        self.student_number_entry.delete(0, tk.END)
        self.name_entry.delete(0, tk.END)
        self.year_entry.delete(0, tk.END)
        self.section_entry.delete(0, tk.END)
        self.error_label.config(text="")

    def update_result(self, message):
        self.error_label.config(text=message)

    def speak(self, message):
        """Function to use TTS engine to speak a given message."""
        if self.speech_engine:
            try:
                self.speech_engine.say(message)
                self.speech_engine.runAndWait()
            except Exception as e:
                print(f"Error in TTS speak: {e}")
        else:
            print("TTS engine is not available. Unable to speak.")

    def on_closing(self):
        self.running = False
        if self.nfc_thread.is_alive():
            self.nfc_thread.join()
        if self.fingerprint_thread.is_alive():
            self.fingerprint_thread.join()
        if self.clf is not None:
            self.clf.close()
        self.root.destroy()


class FingerprintEnrollment(tk.Frame):
    def __init__(self, parent, go_back_callback):
        super().__init__(parent)
        self.go_back_callback = go_back_callback
        self.configure(bg='#2D3F7C')
        self.create_enrollment_ui()

    def create_enrollment_ui(self):
        panel = tk.Frame(self, bg='#F6F5FB')
        panel.place(x=50, y=50, width=600, height=400)

        # Create Treeview for displaying faculty data
        columns = ("name", "email")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", style="LogsTable.Treeview")

        # Configure column widths
        self.tree.column("name", width=250)  # Set width for "name" column
        self.tree.column("email", width=250)  # Set width for "email" column

        # Set headings
        self.tree.heading("name", text="Name")
        self.tree.heading("email", text="Email")

        # Set height (number of visible rows)
        self.tree.configure(height=10)  # Number of visible rows
        self.tree.place(x=100, y=80)

        bold_font = font.Font(size=10, weight="bold")

        # Refresh Button
        refresh_button = tk.Button(self, text="Refresh Data", font=bold_font, width=20, height=2, command=self.refresh_table)
        refresh_button.place(x=150, y=380)

        # Enroll Button
        enroll_button = tk.Button(self, text="Enroll Fingerprint", font=bold_font, width=20, height=2, command=self.on_enroll_button_click)
        enroll_button.place(x=400, y=380)

        # Add a "Back to Main" button
        back_button = tk.Button(self, text="Back to Main", font=bold_font, width=20, height=2, command=self.go_back_callback)
        back_button.place(x=275, y=440)  # Position it below the existing buttons

        # Load initial data
        self.refresh_table()

    def refresh_table(self):
        """Refresh the table with data from the Laravel API."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        faculty_data = self.fetch_faculty_data()
        for faculty in faculty_data:
            self.tree.insert("", tk.END, values=(faculty['name'], faculty['email']))

        admin_data = self.fetch_admin_data()
        for admin in admin_data:
            self.tree.insert("", tk.END, values=(admin['name'], admin['email']))

    def fetch_faculty_data(self):
        try:
            response = requests.get(FACULTIES_URL)
            response.raise_for_status()
            data = response.json()
            return [faculty for faculty in data if faculty.get('fingerprint_id') is None or len(faculty.get('fingerprint_id', []) )< 2]
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Error fetching faculty data: {e}")
            return []

    def fetch_admin_data(self):
        try:
            response = requests.get(ADMIN_URL)
            response.raise_for_status()
            data = response.json()
            return [admin for admin in data if admin.get('fingerprint_id') is None or len(admin.get('fingerprint_id', []) )< 2]
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Error fetching admin data: {e}")
            return []

    def on_enroll_button_click(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a row from the table.")
            return

        item = self.tree.item(selected_item)
        name = item['values'][0]  # Assuming name is in the first column
        email = item['values'][1]  # Assuming email is in the second column

        # Enroll fingerprint with the selected email
        success = self.enroll_fingerprint(email)
        if not success:
            messagebox.showwarning("Enrollment Error", "Failed to enroll fingerprint.")
        else:
            self.refresh_table()

    def enroll_fingerprint(self, email):
        """Enroll a fingerprint for a faculty member, ensuring it's not already registered."""
        # Attempt to capture the first image
        print("Waiting for image...")
        while finger.get_image() != adafruit_fingerprint.OK:
            pass

        print("Templating first image...")
        if finger.image_2_tz(1) != adafruit_fingerprint.OK:
            messagebox.showwarning("Error", "Failed to template the first fingerprint image.")
            return False

        print("Checking if fingerprint is already registered...")
        if finger.finger_search() == adafruit_fingerprint.OK:
            existing_user = get_user(finger.finger_id)
            if existing_user:
                messagebox.showwarning("Error", f"Fingerprint already registered to {existing_user}")
                return False

        # Prompt to place the finger again for verification
        print("Place the same finger again...")
        while finger.get_image() != adafruit_fingerprint.OK:
            pass

        print("Templating second image...")
        if finger.image_2_tz(2) != adafruit_fingerprint.OK:
            messagebox.showwarning("Error", "Failed to template the second fingerprint image.")
            return False

        print("Re-Checking if fingerprint is already registered...")
        if finger.finger_search() == adafruit_fingerprint.OK:
            existing_user = get_user(finger.finger_id)
            if existing_user:
                messagebox.showwarning("Error", f"Fingerprint already registered to {existing_user}")
                return False

        print("Creating model from images...")
        if finger.create_model() != adafruit_fingerprint.OK:
            messagebox.showwarning("Error", "Failed to create fingerprint model from images.")
            return False

        next_fingerprint_id = get_highest_fingerprint_id() + 1

        print(f"Storing model at location #{next_fingerprint_id}...")
        if finger.store_model(next_fingerprint_id) != adafruit_fingerprint.OK:
            messagebox.showwarning("Error", "Failed to store fingerprint model.")
            return False

        # Post the fingerprint data to the API
        post_fingerprint(email, next_fingerprint_id)
        return True


def get_user(fingerprint_id):
    """Fetch user information by fingerprint ID."""
    try:
        response = requests.get(f"{FINGERPRINT_API_URL}{fingerprint_id}")
        response.raise_for_status()
        data = response.json()
        if 'name' in data:
            return data['name']
        return None
    except requests.RequestException as e:
        messagebox.showerror("Request Error", f"Failed to connect to API: {e}")
        return None

def post_fingerprint(email, fingerprint_id):
    """Post fingerprint data to the Laravel API."""
    try:
        url = f"{ENROLL_URL}?email={email}&fingerprint_id={fingerprint_id}"
        response = requests.put(url)
        response.raise_for_status()
        messagebox.showinfo("Success", "Fingerprint enrolled successfully")
    except requests.RequestException as e:
        messagebox.showerror("Error", f"Error posting fingerprint data: {e}")

def get_highest_fingerprint_id():
    """Fetch the highest fingerprint ID stored in the sensor."""
    try:
        # Read all stored fingerprint templates
        if finger.read_templates() != adafruit_fingerprint.OK:
            return 0  # Return 0 if no fingerprints are stored

        # Find the highest ID among the stored fingerprints
        if finger.templates:
            return max(finger.templates)
        else:
            return 0
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read stored fingerprints: {e}")
        return 0


# Create the main window
root = tk.Tk()
app = AttendanceApp(root)

# Run the application
root.mainloop()
