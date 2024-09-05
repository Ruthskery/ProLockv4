import pyttsx3

# Initialize the TTS engine
engine = pyttsx3.init()

# Retrieve all available voices
voices = engine.getProperty('voices')

# Print out the voice IDs along with their names
print("Complete List of Available Voice IDs:")
for index, voice in enumerate(voices):
    print(f"Voice {index}:")
    print(f" - Name: {voice.name}")
    print(f" - ID: {voice.id}")
    print(f" - Languages: {voice.languages}")
    print(f" - Gender: {voice.gender}")
    print(f" - Age: {voice.age}")
    print("-" * 40)
