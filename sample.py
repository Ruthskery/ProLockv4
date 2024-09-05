def auto_scan_fingerprint(self):
    failed_attempts = 0  # Initialize the counter for failed attempts

    while self.running:
        if not self.finger:
            print("Fingerprint sensor not initialized.")
            return

        print("Waiting for fingerprint image...")

        # Check if the sensor is detecting a finger placed on it
        while True:
            image_status = self.finger.get_image()
            if image_status == adafruit_fingerprint.OK:
                print("Fingerprint image taken.")
                break
            elif image_status == adafruit_fingerprint.NOFINGER:
                # If no finger is detected, wait before retrying
                time.sleep(0.5)
                continue
            else:
                print("Error", "Failed to get image.")
                time.sleep(0.5)
                continue

        print("Templating...")
        template_status = self.finger.image_2_tz(1)
        if template_status != adafruit_fingerprint.OK:
            print("Error", "Failed to template the fingerprint image.")
            failed_attempts += 1
            self.check_failed_attempts(failed_attempts)  # Check failed attempts and trigger the buzzer if needed
            continue

        print("Searching for fingerprint match...")
        search_status = self.finger.finger_search()
        if search_status != adafruit_fingerprint.OK:
            print("Error", "Failed to search for fingerprint match.")
            failed_attempts += 1
            self.check_failed_attempts(failed_attempts)  # Check failed attempts and trigger the buzzer if needed
            continue

        # Reset failed attempts if successful
        failed_attempts = 0

        print(f"Detected fingerprint ID: {self.finger.finger_id} with confidence {self.finger.confidence}")

        # Fetch user details using API
        name = self.get_user_details(self.finger.finger_id)

        if name:
            if self.get_schedule(self.finger.finger_id):  # Check if the current time is within the allowed schedule
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
                    print(f"Welcome, {name}! Door unlocked.")
                    self.speak(f"Welcome, {name}! Door unlocked.")
                else:
                    self.record_time_out_fingerprint(self.finger.finger_id)
                    self.lock_door()
                    self.is_manual_unlock = False  # Reset flag as door is locked again
                    self.record_all_time_out()  # Record time-out for all entries without time-out
                    print(f"Goodbye, {name}! Door locked.")
                    self.speak(f"Goodbye, {name}! Door locked.")
            else:
                print("No Access", "Access denied due to schedule restrictions.")
                self.speak("Access denied due to schedule restrictions.")
        else:
            print("No Match", "No matching fingerprint found in the database.")
            self.speak("No matching fingerprint found.")
