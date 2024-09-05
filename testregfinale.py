import tkinter as tk
from tkinter import messagebox, ttk, font
import requests
import serial
import adafruit_fingerprint

# Laravel API endpoint URLs
api_url = "https://prolocklogger.pro/api/getuserbyfingerprint/"
API_URL = 'https://prolocklogger.pro/api'
FACULTIES_URL = f'{API_URL}/users/role/2'
ENROLL_URL = f'{API_URL}/users/update-fingerprint'

# Initialize serial connection for the fingerprint sensor
uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

def get_user(fingerprint_id):
    """Fetch user information by fingerprint ID."""
    try:
        response = requests.get(f"{api_url}{fingerprint_id}")
        response.raise_for_status()
        data = response.json()
        if 'name' in data:
            return data['name']
        return None
    except requests.RequestException as e:
        messagebox.showerror("Request Error", f"Failed to connect to API: {e}")
        return None

def fetch_faculty_data():
    """Fetch faculty data from the Laravel API, excluding those with exactly two or more registered fingerprint IDs."""
    try:
        response = requests.get(FACULTIES_URL)
        response.raise_for_status()
        data = response.json()

        # Filter out faculty members who have exactly two or more fingerprints registered
        filtered_data = [
            faculty for faculty in data 
            if faculty.get('fingerprint_id') is None or len(faculty.get('fingerprint_id', [])) < 2
        ]

        return filtered_data

    except requests.RequestException as e:
        messagebox.showerror("Error", f"Error fetching faculty data: {e}")
        return []

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

# Set the next fingerprint ID based on the highest ID found in the sensor
next_fingerprint_id = get_highest_fingerprint_id() + 1

def check_fingerprint_exists():
    """Check if the current fingerprint is already registered."""
    print("Searching for existing fingerprint...")
    if finger.finger_search() == adafruit_fingerprint.OK:
        existing_user = get_user(finger.finger_id)
        if existing_user:
            messagebox.showwarning("Error", f"Fingerprint already registered to {existing_user}")
            return True
    return False

def enroll_fingerprint(email):
    """Enroll a fingerprint for a faculty member, ensuring it's not already registered."""
    global next_fingerprint_id

    print("Waiting for image...")
    # Attempt to capture the first image
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

    print("Creating model from images...")
    if finger.create_model() != adafruit_fingerprint.OK:
        messagebox.showwarning("Error", "Failed to create fingerprint model from images.")
        return False

    print(f"Storing model at location #{next_fingerprint_id}...")
    if finger.store_model(next_fingerprint_id) != adafruit_fingerprint.OK:
        messagebox.showwarning("Error", "Failed to store fingerprint model.")
        return False

    # Post the fingerprint data to the API
    post_fingerprint(email, next_fingerprint_id)
    next_fingerprint_id += 1  # Increment the ID for the next registration
    return True

def on_enroll_button_click():
    """Callback function for the enroll button."""
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Selection Error", "Please select a row from the table.")
        return

    item = tree.item(selected_item)
    table_name = item['values'][0]  # Assuming name is in the first column
    email = item['values'][1]  # Assuming email is in the second column

    # Enroll fingerprint with the selected email
    success = enroll_fingerprint(email)
    if not success:
        messagebox.showwarning("Enrollment Error", "Failed to enroll fingerprint.")
    else:
        # Refresh the table to update or remove the faculty if they now have 2 fingerprints
        refresh_table()

def refresh_table():
    """Refresh the table with data from the Laravel API."""
    for row in tree.get_children():
        tree.delete(row)

    faculty_data = fetch_faculty_data()
    for faculty in faculty_data:
        # Only display faculty who have less than 2 fingerprints registered
        tree.insert("", tk.END, values=(faculty['name'], faculty['email']))

# Initialize Tkinter window
def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')

root = tk.Tk()
root.configure(bg='#135D66')
root.title("Faculty Fingerprint Enrollment")

panel = tk.Frame(root, bg='#77B0AA')
panel.place(x=50, y=50, width=600, height=400)

# Create Treeview for displaying faculty data
columns = ("name", "email")
tree = ttk.Treeview(root, columns=columns, show="headings")

# Configure column widths
tree.column("name", width=250)  # Set width for "name" column
tree.column("email", width=250)  # Set width for "email" column

# Set headings
tree.heading("name", text="Name")
tree.heading("email", text="Email")

# Set height (number of visible rows)
tree.configure(height=10)  # Number of visible rows
tree.place(x=100, y=80)

bold_font = font.Font(size=10, weight="bold")

# Refresh Button
refresh_button = tk.Button(root, text="Refresh Data", font=bold_font, width=20, height=2, command=refresh_table)
refresh_button.place(x=150, y=380)

# Enroll Button
enroll_button = tk.Button(root, text="Enroll Fingerprint", font=bold_font, width=20, height=2,
                          command=on_enroll_button_click)
enroll_button.place(x=400, y=380)

# Load initial data
refresh_table()

center_window(root, 700, 500)

# Run the Tkinter event loop
root.mainloop()
