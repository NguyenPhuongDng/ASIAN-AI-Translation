from gtts import gTTS


def speak(text: str, lang="en"):
    tts = gTTS(text=text, lang=lang)
    return tts



