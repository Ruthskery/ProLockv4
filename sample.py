import pyttsx3

engine = pyttsx3.init()

# Set a specific voice by ID (replace 'voice_id' with the actual ID you want)
desired_voice_id = 'english_rp+f4'  # Example voice ID, change based on your list
engine.setProperty('voice', desired_voice_id)

# Adjust additional properties as needed
engine.setProperty('rate', 150)  # Speech speed (words per minute)
engine.setProperty('volume', 1)  # Volume level (0.0 to 1.0)

# Test the selected voice
engine.say("Hello, this is a test using the selected voice.")
engine.runAndWait()
