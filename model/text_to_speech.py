from gtts import gTTS
import pygame
import os

def speak(text: str, lang="en"):
    tts = gTTS(text=text, lang=lang)
    return tts



