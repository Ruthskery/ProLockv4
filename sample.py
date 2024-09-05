def auto_scan_fingerprint(self):
    failed_attempts = 0  # Initialize the counter for failed attempts

    while self.running:
        if not self.finger:
            return

        print("Waiting for fingerprint image...")
        
        # Wait until a fingerprint is placed on the sensor
        while self.finger.get_image() != adafruit_fingerprint.OK:
            if not self.running:
                return
            time.sleep(0.5)  # Sleep to avoid too frequent checks

        # Attempt to template the fingerprint
        print("Templating...")
        if self.finger.image_2_tz(1) != adafruit_fingerprint.OK:
            print("Error", "Failed to template the fingerprint image.")
            failed_attempts += 1
            self.check_failed_attempts(failed_attempts)
            time.sleep(1)  # Delay before retrying
            continue

        # Search for a fingerprint match
        print("Searching...")
        if self.finger.finger_search() != adafruit_fingerprint.OK:
            print("Error", "Failed to search for fingerprint match.")
            failed_attempts += 1
            self.check_failed_attempts(failed_attempts)
            time.sleep(1)  # Delay before retrying
            continue

        # Reset failed attempts if a fingerprint match is successful
        failed_attempts = 0

        print("Detected fingerprint ID:", self.finger.finger_id, "with confidence", self.finger.confidence)

        # Handle the matched fingerprint, e.g., by unlocking the door or logging access
        name = self.get_user_details(self.finger.finger_id)

        if name:
            if self.get_schedule(self.finger.finger_id):  # Check schedule validity
                current_time_data = self.fetch_current_date_time()
                if not current_time_data:
                    return
                current_time = datetime.strptime(current_time_data['current_time'], "%H:%M")

                # Check if the user has no time-in record
                if not self.check_time_in_record_fingerprint(self.finger.finger_id):
                    self.record_time_in_fingerprint(self.finger.finger_id, name)
                    self.unlock_door()
                    self.is_manual_unlock = True
                    self.last_time_in[self.finger.finger_id] = current_time
                    print(f"Welcome, {name}! Door unlocked.")
                else:
                    self.record_time_out_fingerprint(self.finger.finger_id)
                    self.lock_door()
                    self.is_manual_unlock = False
                    self.record_all_time_out()
                    print(f"Goodbye, {name}! Door locked.")
            else:
                print("Access denied due to schedule restrictions.")

        else:
            print("No matching fingerprint found in the database.")

        # Ensure a pause before allowing another fingerprint scan
        print("Please remove your finger.")
        while self.finger.get_image() != adafruit_fingerprint.NOFINGER:
            time.sleep(0.5)  # Wait until the finger is removed

        # Small delay to avoid immediate re-scanning
        time.sleep(2)
