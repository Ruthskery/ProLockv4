import pyttsx3

def test_tts_with_voice():
    try:
        engine = pyttsx3.init(driverName='espeak')  # Explicitly specify the eSpeak driver
        engine.setProperty('rate', 150)  # Set speech rate
        engine.setProperty('volume', 0.9)  # Set volume level
        
        # List available voices
        voices = engine.getProperty('voices')
        for voice in voices:
            print(f"Voice ID: {voice.id}, Name: {voice.name}")

        # Set a specific voice if needed
        engine.setProperty('voice', voices[0].id)  # Use the first available voice
        
        engine.say("Testing text to speech on Raspberry Pi with a specific voice.")
        engine.runAndWait()
    except Exception as e:
        print(f"Error initializing TTS engine: {e}")

test_tts_with_voice()

Error initializing TTS engine: 'NoneType' object has no attribute '_handle'

