 # Initialize the text-to-speech engine with eSpeak driver for Raspberry Pi
        try:
            self.speech_engine = pyttsx3.init(driverName='espeak')
            self.speech_engine.setProperty('rate', 150)  # Set speech rate
            self.speech_engine.setProperty('volume', 0.9)  # Set volume level
        except Exception as e:
            print(f"Failed to initialize TTS engine: {e}")

def speak(self, message):
        """Function to use TTS engine to speak a given message."""
        try:
            self.speech_engine.say(message)
            self.speech_engine.runAndWait()
        except Exception as e:
            print(f"Error in TTS speak: {e}")
