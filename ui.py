import tkinter as tk
from tkinter import messagebox
import pvporcupine
from pvrecorder import PvRecorder
import threading
from chatbot import listen_and_process, speak
import queue
import subprocess
import tempfile

# Replace with your Picovoice AccessKey
ACCESS_KEY = "txaNHIV5YLy8x3OFqlGLaxMWRYwacB41al+Vh41aYLPo+9SoNHDhPQ=="

class ChatbotUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Assistant")
        self.root.geometry("500x400")
        
        # Status indicators
        self.status_label = tk.Label(root, text="Status: Off", fg="red")
        self.status_label.pack(pady=10)
        
        # Response display
        self.response_text = tk.Text(root, height=10, width=50)
        self.response_text.pack(pady=10)
        
        # Image placeholder (replace with your image)
        self.image_label = tk.Label(root)
        self.image_label.place(x=10, y=10)
        
        # Start wake word detection
        self.message_queue = queue.Queue()
        self.start_wake_word_detection()
        self.root.after(100, self.process_messages)
        
    def update_status(self, message, color="black"):
        self.status_label.config(text=f"Status: {message}", fg=color)
        
    def add_response(self, message):
        self.response_text.insert(tk.END, f"Assistant: {message}\n")
        self.response_text.see(tk.END)
        
    def process_messages(self):
        while not self.message_queue.empty():
            message = self.message_queue.get()
            if message.startswith("STATUS:"):
                self.update_status(message[7:], "green" if "Listening" in message else "red")
            else:
                self.add_response(message)
        self.root.after(100, self.process_messages)
        
    def wake_word_detected(self):
        self.message_queue.put("STATUS: Listening...")
        response = listen_and_process()
        self.message_queue.put(response)
        self.message_queue.put("STATUS: Ready")

    def start_wake_word_detection(self):
        def detection_loop():
            porcupine = pvporcupine.create(
                access_key=ACCESS_KEY,
                keywords=["porcupine"]
            )
            recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
            
            try:
                recorder.start()
                self.message_queue.put("STATUS: Ready")
                while True:
                    pcm = recorder.read()
                    keyword_index = porcupine.process(pcm)
                    if keyword_index >= 0:
                        self.root.event_generate("<<WakeWord>>", when="tail")
            finally:
                recorder.stop()
                porcupine.delete()
                recorder.delete()

        self.root.bind("<<WakeWord>>", lambda e: self.wake_word_detected())
        threading.Thread(target=detection_loop, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatbotUI(root)
    root.mainloop()
