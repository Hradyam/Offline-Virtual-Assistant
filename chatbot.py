from gtts import gTTS
import re
import os
from datetime import datetime
import subprocess
import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import speech_recognition as sr
import time
import pygame
import tempfile
import pyautogui
import winreg


def speak(text):
    """Convert text to speech and play it."""
    pygame.init()
    pygame.mixer.init()
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        temp_filename = temp_file.name
        tts = gTTS(text=text, lang='en')
        tts.save(temp_filename)

    pygame.mixer.music.load(temp_filename)
    pygame.mixer.music.play()
    
    # Wait for the audio to finish playing
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)


def listen_and_process():
    """Listen to microphone and process command."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for command...")
        try:
            audio = recognizer.listen(source, timeout=5)
            query = recognizer.recognize_google(audio).lower()
            print(f"User said: {query}")
            return respond_to_query(query)
        except sr.WaitTimeoutError:
            return "No input detected"
        except Exception as e:
            return f"Error: {str(e)}"
    

def respond_to_query(query):
    """Process user query and respond."""
    query = query.lower()
    if "time" in query:
        current_time = datetime.now().strftime("%H:%M %p")
        speak(f"The current time is {current_time}")
        return f"The current time is {current_time}"
    elif "brightness" in query:
        return control_brightness(query)
    elif "volume" in query:
        return control_volume(query)
    elif any(word in query for word in ["play", "pause", "next", "previous", "song"]):
        return control_media(query)
    elif "open" in query:
        app_name = query.split("open")[-1].strip()
        return open_application(app_name)
    else:
        speak("I couldn't understand the command.")
        return "I couldn't understand the command."


def control_brightness(command):
    """Control screen brightness based on voice commands."""

    match = re.search(r'\d+', command)
    if match:
        level = int(match.group())
        if 0 <= level <= 100:
            sbc.set_brightness(level)
            speak(f"Brightness set to {level}%.")
            return f"Brightness set to {level}%."
        
    current_brightness = sbc.get_brightness()[0]
    if "up" in command:
        sbc.set_brightness(min(current_brightness + 10, 100))
        speak(f"Brightness increased to {min(current_brightness + 10, 100)}%.")
        return f"Brightness increased to {min(current_brightness + 10, 100)}%."
    elif "down" in command:
        sbc.set_brightness(max(current_brightness - 10, 0))
        speak(f"Brightness decreased to {max(current_brightness - 10, 0)}%.")
        return f"Brightness decreased to {max(current_brightness - 10, 0)}%."
    elif "half" in command:
        sbc.set_brightness(50)
        speak(f"Brightness set to half.")
        return f"Brightness set to half."
    elif "one-fourth" in command:
        sbc.set_brightness(25)
        speak(f"Brightness set to 25%.")
        return f"Brightness set to 25%."
    elif "max" or "full" in command:
        sbc.set_brightness(100)
        speak(f"Brightness increased to full.")
        return f"Brightness increased to full."
    elif "minimum" or "zero" in command:
        sbc.set_brightness(0)
        speak(f"Brightness decreased to zero.")
        return f"Brightness decreased to zero."


def control_volume(command):
    """Control system volume based on voice commands."""
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))

    match = re.search(r'\d+', command)
    if match:
        level = int(match.group())
        if 0 <= level <= 100:
            volume.SetMasterVolumeLevelScalar(level / 100, None)
            speak(f"Volume set to {level}%.")
            return f"Volume set to {level}%."
    
    current_volume = volume.GetMasterVolumeLevelScalar()
    if "up" in command:
        volume.SetMasterVolumeLevelScalar(min(current_volume + 0.1, 1.0), None)
        speak(f"Volume increased to {int((min(current_volume + 0.1, 1.0)) * 100)}%.")
        return f"Volume increased to {int((min(current_volume + 0.1, 1.0)) * 100)}%."
    elif "down" in command:
        volume.SetMasterVolumeLevelScalar(max(current_volume - 0.1, 0.0), None)
        speak(f"Volume decreased to {int((max(current_volume - 0.1, 0.0)) * 100)}%.")
        return f"Volume decreased to {int((max(current_volume - 0.1, 0.0)) * 100)}%."
    elif "max" or "full" in command:
        volume.SetMasterVolumeLevelScalar((1), None)
        speak(f"Volume Increased to 100%.")
        return f"Volume increased to 100%."
    elif "zero" in command:
        volume.SetMasterVolumeLevelScalar((0), None)
        speak(f"Volume decreased to 0%.")
        return f"Volume decreased to 0%."
    elif "half" in command:
        volume.SetMasterVolumeLevelScalar((.5), None)
        speak(f"Volume decreased to 50%.")
        return f"Volume decreased to 50%."
    elif "one-fourth" in command:
        volume.SetMasterVolumeLevelScalar((.25), None)
        speak(f"Volume decreased to 25%.")
        return f"Volume decreased to 25%."

def control_media(command):
    if "play" in command or "pause" in command:
        pyautogui.press('playpause')
        return "Media played/paused"
    elif "next" in command:
        pyautogui.press('nexttrack')
        return "Skipped to next track"
    elif "previous" in command:
        pyautogui.press('prevtrack')
        return "Returned to previous track"
    elif "volume up" in command:
        pyautogui.press('volumeup')
        return "Volume increased"
    elif "volume down" in command:
        pyautogui.press('volumedown')
        return "Volume decreased"
    else:
        return "Unrecognized media command"

def search_start_menu(app_name):
    start_menu_paths = [
        os.path.join(os.environ["PROGRAMDATA"], "Microsoft", "Windows", "Start Menu", "Programs"),
        os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs")
    ]
    
    for start_menu in start_menu_paths:
        for root, dirs, files in os.walk(start_menu):
            for file in files:
                if file.lower().startswith(app_name.lower()) and file.endswith(('.lnk', '.exe')):
                    return os.path.join(root, file)
    return None

def open_application(app_name):
    # First, try to find the app in the Start Menu
    app_path = search_start_menu(app_name)
    
    if app_path:
        try:
            subprocess.Popen(app_path)
            return f"Opening {app_name}"
        except subprocess.CalledProcessError:
            return f"Error opening {app_name}"
    else:
        # If not found in Start Menu, try to launch directly (for built-in Windows apps)
        try:
            subprocess.Popen(app_name)
            return f"Opening {app_name}"
        except FileNotFoundError:
            return f"Could not find {app_name}. Please check if it's installed."