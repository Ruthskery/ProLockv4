def auto_scan_fingerprint(self):
    failed_attempts = 0  # Initialize the counter for failed attempts

    while self.running:
        if not self.finger:
            return

        print("Waiting for fingerprint image...")
        while self.running and self.finger.get_image() != adafruit_fingerprint.OK:
            time.sleep(0.5)

        if not self.running:
            break

        print("Templating...")
        if self.finger.image_2_tz(1) != adafruit_fingerprint.OK:
            print("Error", "Failed to template the fingerprint image.")
            failed_attempts += 1
            self.check_failed_attempts(failed_attempts)  # Check failed attempts and trigger the buzzer if needed
            continue

        # Rest of the function...

def read_nfc_loop(self):
    while self.running:
        try:
            tag = self.clf.connect(rdwr={'on-connect': lambda tag: False})
            if tag and self.running:
                uid = tag.identifier.hex()
                self.fetch_user_info(uid)
                time.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)
        if not self.running:
            break


def on_closing(self):
    self.running = False  # Stop the loops
    if self.nfc_thread.is_alive():
        self.nfc_thread.join()  # Wait for NFC thread to stop
    if self.fingerprint_thread.is_alive():
        self.fingerprint_thread.join()  # Wait for fingerprint thread to stop
    if self.clf is not None:
        try:
            self.clf.close()  # Close the NFC reader properly
        except Exception as e:
            print(f"Error closing NFC reader: {e}")
    GPIO.cleanup()  # Clean up GPIO pins
    self.root.destroy()  # Destroy the main window
