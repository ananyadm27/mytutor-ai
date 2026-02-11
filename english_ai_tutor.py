import tkinter as tk
from tkinter import scrolledtext
import ollama
import pyttsx3
import threading
import speech_recognition as sr

# ---------------- SPEAK FUNCTION ----------------
def speak(text):
    def run():
        engine = pyttsx3.init()
        engine.setProperty('rate', 165)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    threading.Thread(target=run, daemon=True).start()

# ---------------- LISTEN FUNCTION ----------------
def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        status_label.config(text="🎤 Listening...")
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        status_label.config(text="")
        return text
    except:
        status_label.config(text="")
        return ""

# ---------------- AI PROCESS ----------------
def process_message(user_input):

    if user_input.strip() == "":
        return

    chat_area.insert(tk.END, "You:\n" + user_input + "\n\n", "user")
    chat_area.see(tk.END)

    status_label.config(text="🤖 Thinking...")

    def run_ai():
        level = level_var.get()

        prompt = f"""
You are a friendly English tutor.

Student level: {level}

1. Answer naturally.
2. Check grammar.
3. If mistake:
   - Correct sentence
   - Explain simply
4. If correct, say it is grammatically correct.
5. Encourage student.

Student sentence:
{user_input}
"""

        response = ollama.chat(
            model="mistral",
            messages=[{"role": "user", "content": prompt}]
        )

        bot_reply = response["message"]["content"]

        window.after(0, lambda: update_ui(bot_reply))

    threading.Thread(target=run_ai, daemon=True).start()

# ---------------- UPDATE UI ----------------
def update_ui(bot_reply):
    chat_area.insert(tk.END, "Tutor:\n" + bot_reply + "\n\n", "bot")
    chat_area.see(tk.END)
    status_label.config(text="")
    speak(bot_reply)

# ---------------- BUTTONS ----------------
def send_text():
    user_input = entry.get()
    entry.delete(0, tk.END)
    process_message(user_input)

def use_voice():
    user_input = listen()
    if user_input:
        process_message(user_input)

# ---------------- GUI SETUP ----------------
window = tk.Tk()
window.title("🎓 AI Voice English Tutor")
window.geometry("750x650")
window.configure(bg="#1e1e1e")

# LEVEL SELECTOR
level_var = tk.StringVar(value="Beginner")
level_menu = tk.OptionMenu(window, level_var, "Beginner", "Intermediate", "Advanced")
level_menu.config(bg="#2d2d2d", fg="white", font=("Arial", 11))
level_menu.pack(pady=10)

# CHAT AREA
chat_area = scrolledtext.ScrolledText(
    window,
    wrap=tk.WORD,
    font=("Arial", 12),
    bg="#252526",
    fg="white",
    insertbackground="white"
)
chat_area.pack(padx=15, pady=10, fill=tk.BOTH, expand=True)

# TAG STYLES
chat_area.tag_config("user", foreground="#4FC3F7")
chat_area.tag_config("bot", foreground="#A5D6A7")

# ENTRY
entry = tk.Entry(
    window,
    font=("Arial", 12),
    bg="#2d2d2d",
    fg="white",
    insertbackground="white"
)
entry.pack(padx=15, pady=10, fill=tk.X)

# BUTTON FRAME
button_frame = tk.Frame(window, bg="#1e1e1e")
button_frame.pack(pady=5)

send_button = tk.Button(
    button_frame,
    text="Send",
    command=send_text,
    bg="#4CAF50",
    fg="white",
    font=("Arial", 11),
    width=10
)
send_button.pack(side=tk.LEFT, padx=10)

voice_button = tk.Button(
    button_frame,
    text="🎤 Speak",
    command=use_voice,
    bg="#2196F3",
    fg="white",
    font=("Arial", 11),
    width=10
)
voice_button.pack(side=tk.LEFT, padx=10)

# STATUS
status_label = tk.Label(window, text="", fg="#FFC107", bg="#1e1e1e", font=("Arial", 10))
status_label.pack(pady=5)

window.mainloop()
