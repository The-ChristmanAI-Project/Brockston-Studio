# /speech/transcriber.py
# Hybrid VOSK + BROCKSTON Speech Recognition + BROCKSTON Brain Integration
# Adds "Hey BROCKSTON" wake word mode and Voice Activity Detection (VAD)
# Auto-detects model folder safely

import os
import sys
import json
import queue
import sounddevice as sd
import vosk
import webrtcvad

# -------------------------------------------------------------
# Add project root to Python path BEFORE local imports
# -------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# -------------------------------------------------------------
# Now import BROCKSTON's brain and TTS safely
# -------------------------------------------------------------
from tts_bridge import speak_response

try:
    from brockston_core import brain as brockston
except ImportError:
    brockston = None

# -------------------------------------------------------------
# Configuration (clean version — no extra validation)
# -------------------------------------------------------------
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEECH_DIR = os.path.join(PROJECT_ROOT, "speech")

# Direct path to your actual model folder
MODEL_PATH = os.path.join(SPEECH_DIR, "vosk-model-small-en-us-0.15")

# Tell Python to just use this path — with error handling for missing models
print(f"🎯 Loading Vosk model directly from: {MODEL_PATH}")

# Initialize the model with fallback for missing models
try:
    model = vosk.Model(MODEL_PATH)
    print("✅ Vosk model loaded successfully")
except Exception as e:
    print(f"⚠️ Vosk model not available: {e}")
    print("🔄 Transcriber will use fallback mode")
    model = None

# -------------------------------------------------------------
# Load custom BROCKSTON vocabulary (optional)
# -------------------------------------------------------------
CUSTOM_VOCAB_PATH = os.path.join(PROJECT_ROOT, "speech", "vocab-alpha.json")
custom_vocab = {"terms": []}
if os.path.exists(CUSTOM_VOCAB_PATH):
    try:
        with open(CUSTOM_VOCAB_PATH, "r") as f:
            custom_vocab = json.load(f)
        print(
            f"📘 Loaded custom vocabulary ({len(custom_vocab.get('terms', []))} terms)"
        )
    except Exception as e:
        print(f"⚠️ Failed to load custom vocab: {e}")
else:
    print("⚠️ No custom vocabulary found (optional).")

# -------------------------------------------------------------
# Audio + VAD setup
# -------------------------------------------------------------
SAMPLE_RATE = 16000
FRAME_DURATION = 30  # ms
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION / 1000) * 2

q = queue.Queue()
vad = webrtcvad.Vad(2)


def callback(indata, frames, time_info, status):
    if status:
        print(f"[Audio Warning] {status}", flush=True)
    q.put(bytes(indata))


# -------------------------------------------------------------
# Wake Word Detection
# -------------------------------------------------------------
WAKE_WORDS = ["hey brockston", "okay brockston", "hi brockston"]


def detect_wake_word(text: str) -> bool:
    text = text.lower().strip()
    return any(ww in text for ww in WAKE_WORDS)


# -------------------------------------------------------------
# Passive Listening
# -------------------------------------------------------------
def passive_listen():
    """Idle mode — listens for 'Hey BROCKSTON' without responding to everything."""
    if model is None:
        print("⚠️ Cannot start passive listening - Vosk model not available")
        print("💬 Using text input mode instead")
        return text_input_mode()

    print("👂 Passive listening... (Say 'Hey BROCKSTON' to wake me)")
    rec = vosk.KaldiRecognizer(model, SAMPLE_RATE)
    buffer = b""

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=FRAME_SIZE,
        dtype="int16",
        channels=1,
        callback=callback,
    ):
        while True:
            frame = q.get()
            buffer += frame

            if len(buffer) >= FRAME_SIZE:
                chunk = buffer[:FRAME_SIZE]
                buffer = buffer[FRAME_SIZE:]

                if vad.is_speech(chunk, SAMPLE_RATE):
                    rec.AcceptWaveform(chunk)
                    result = json.loads(rec.Result())
                    text = result.get("text", "")
                    if text:
                        sys.stdout.write(f"\r🗣️ Heard: {text}     ")
                        sys.stdout.flush()

                        if detect_wake_word(text):
                            print("\n🚀 Wake word detected! BROCKSTON is listening...")
                            speak_response("Yes?")
                            active_listen()
                            print("👂 Back to passive listening...\n")
                            if model:
                                rec = vosk.KaldiRecognizer(model, SAMPLE_RATE)


# -------------------------------------------------------------
# Active Listening
# -------------------------------------------------------------
def active_listen():
    """Active mode — listens for full sentences until silence is detected."""
    if model is None:
        print("⚠️ Cannot start active listening - Vosk model not available")
        return

    print("🎤 Active listening mode. Speak your command...")

    rec = vosk.KaldiRecognizer(model, SAMPLE_RATE)
    silence_counter = 0
    speaking = False
    buffer = b""

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=FRAME_SIZE,
        dtype="int16",
        channels=1,
        callback=callback,
    ):
        while True:
            frame = q.get()
            buffer += frame

            if len(buffer) >= FRAME_SIZE:
                chunk = buffer[:FRAME_SIZE]
                buffer = buffer[FRAME_SIZE:]
                speech_detected = vad.is_speech(chunk, SAMPLE_RATE)

                if speech_detected:
                    speaking = True
                    silence_counter = 0
                    rec.AcceptWaveform(chunk)
                else:
                    if speaking:
                        silence_counter += 1
                        # about 0.8s silence ends capture
                        if silence_counter > int(800 / FRAME_DURATION):
                            speaking = False
                            process_audio(rec)
                            return  # Go back to passive listening


# -------------------------------------------------------------
# Process Audio with BROCKSTON
# -------------------------------------------------------------
def process_audio(rec):
    """Send recognized speech to BROCKSTON’s brain and speak back."""
    result = json.loads(rec.FinalResult())
    text = result.get("text", "").strip()
    if not text:
        print("⚠️ No speech detected.")
        return

    corrected = postprocess(text)
    print(f"\n🧠 You said: {corrected}")

    try:
        print("🧩 Sending to BROCKSTON.think()...")
        response = brockston.think(corrected)
        print(f"🧩 BROCKSTON.think() returned: {response}")

        reply = response.get("response", "I'm here.")
        print(f"🤖 BROCKSTON: {reply}\n")

        print("🔊 Sending to speak_response()...")
        speak_response(reply)
        print("✅ Finished TTS playback.")

    except Exception as e:
        print(f"⚠️ BROCKSTON response error: {e}")


# -------------------------------------------------------------
# Post-processing (fix misheard words)
# -------------------------------------------------------------
def postprocess(text):
    corrections = {
        "ice cream": "I scream",
        "help me now": "emergency help",
    }
    for wrong, right in corrections.items():
        text = text.replace(wrong, right)
    for term in custom_vocab.get("terms", []):
        alias = term.get("alias")
        canonical = term.get("canonical")
        if alias and canonical and alias in text:
            text = text.replace(alias, canonical)
    return text


# -------------------------------------------------------------
# Text Input Fallback Mode
# -------------------------------------------------------------
def text_input_mode():
    """Fallback text mode when speech recognition is not available"""
    print("📝 Text Input Mode - BROCKSTON is ready!")
    print("Type your messages (type 'quit' to exit)")

    while True:
        try:
            user_input = input("\n🧑 You: ").strip()

            if user_input.lower() in ["quit", "exit", "bye"]:
                print("👋 BROCKSTON: Goodbye!")
                break

            if user_input:
                print("🧠 Processing...")
                try:
                    response = brockston.think(user_input)
                    reply = response.get("response", "I'm here.")
                    print(f"🤖 BROCKSTON: {reply}")
                    speak_response(reply)
                except Exception as e:
                    print(f"⚠️ BROCKSTON response error: {e}")

        except KeyboardInterrupt:
            print("\n👋 BROCKSTON: Goodbye!")
            break


# -------------------------------------------------------------
# Main Entry
# -------------------------------------------------------------
if __name__ == "__main__":
    try:
        passive_listen()
    except KeyboardInterrupt:
        print("\n🛑 Exiting voice system.")

# ==============================================================================
# © 2025 Everett Nathaniel Christman
# The Christman AI Project — Luma Cognify AI
# All rights reserved. Unauthorized use, replication, or derivative training
# of this material is prohibited.
#
# Core Directive: "How can I help you love yourself more?"
# Autonomy & Alignment Protocol v3.0
# ==============================================================================
