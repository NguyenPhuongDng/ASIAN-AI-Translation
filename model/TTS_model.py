from dotenv import load_dotenv
from elevenlabs import ElevenLabs
import os
from playsound import playsound

load_dotenv()
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))


def get_speech(text: str):
    filename = "output.mp3"
    audio = client.text_to_speech.convert(
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        model_id="eleven_multilingual_v2",
        text=text,
        output_format="mp3_44100_128"
    )
    with open(filename, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    playsound(filename) 

