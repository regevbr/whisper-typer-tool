#!/usr/bin/env python3

import sys
import time
import pyaudio
import wave
from RealtimeSTT import AudioToTextRecorder
import pyperclip
from pynput import keyboard

# Configuration
WHISPER_MODEL = "tiny"
SILENCE_THRESHOLD = 4    # seconds before auto-stop

# Track what we've already typed to avoid duplicates
last_typed_text = ""

def play_audio_file(filename):
    """Play audio file using pyaudio"""
    try:
        audio = pyaudio.PyAudio()
        wf = wave.open(filename, 'rb')
        
        stream = audio.open(
            format=audio.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True
        )
        
        data = wf.readframes(1024)
        while data:
            stream.write(data)
            data = wf.readframes(1024)
        
        stream.stop_stream()
        stream.close()
        wf.close()
        audio.terminate()
    except Exception as e:
        print(f"Warning: Could not play audio file {filename}: {e}")


def find_common_prefix_length(text1, text2):
    """Find the length of the common prefix between two strings"""
    min_length = min(len(text1), len(text2))
    for i in range(min_length):
        if text1[i] != text2[i]:
            return i
    return min_length


def type_text_realtime(text):
    """Type text with corrections, deleting and retyping changed portions"""
    global last_typed_text
    
    if not text or not text.strip():
        return
    
    # Skip if text is exactly the same
    if text == last_typed_text:
        print(f"💭 No change: '{text}' (skipping)")
        return
    
    # Find the common prefix length
    common_prefix_length = find_common_prefix_length(last_typed_text, text)
    
    try:
        kb = keyboard.Controller()
        
        # If there's a difference, we need to correct the text
        if common_prefix_length < len(last_typed_text):
            # Calculate how many characters to delete (divergent part of old text)
            chars_to_delete = len(last_typed_text) - common_prefix_length
            
            print(f"🔄 Correcting: deleting {chars_to_delete} chars, typing '{text[common_prefix_length:]}'")
            
            # Send backspace keystrokes to delete the divergent part
            for _ in range(chars_to_delete):
                kb.press(keyboard.Key.backspace)
                kb.release(keyboard.Key.backspace)
                time.sleep(0.001)  # Small delay between keystrokes
            
            # Type the corrected text after the common prefix
            new_text_to_type = text[common_prefix_length:]
        else:
            # Text only got longer (append case)
            new_text_to_type = text[common_prefix_length:]

        # Type the new/corrected text if there is any
        if new_text_to_type:

            print(f"💬 Appending: '{new_text_to_type}'")

            # Use pyperclip for cross-platform clipboard operations
            pyperclip.copy(new_text_to_type)
            
            # Small delay to ensure clipboard is set
            time.sleep(0.01)
            
            # Paste using Ctrl+V (cross-platform)
            with kb.pressed(keyboard.Key.ctrl):
                kb.press('v')
                kb.release('v')
        
        # Update what we've typed
        last_typed_text = text
        
    except Exception as e:
        print(f"Warning: Could not type/correct text: {e}")


def on_recording_stop():
    """Callback when recording stops"""  
    print("\n🔇 Recording stopped")
    play_audio_file("off.wav")


def main():
    """Main entry point"""
    global last_typed_text
    
    print("Loading Whisper model...")
    
    # Reset typed text for new session
    last_typed_text = ""
    
    try:
        # Initialize RealtimeSTT recorder with optimized settings
        with AudioToTextRecorder(
            # Model configuration
            model=WHISPER_MODEL,
            language="en",
            device="cpu",
            compute_type="int8",
            
            # VAD Configuration for better speech detection
            silero_sensitivity=0.4,          # Silero VAD sensitivity (0.0-1.0)
            webrtc_sensitivity=2,            # WebRTC VAD aggressiveness (0-3)
            
            # Recording behavior
            post_speech_silence_duration=SILENCE_THRESHOLD,  # Stop after N seconds of silence
            min_length_of_recording=0.5,     # Minimum recording duration
            
            # Real-time transcription settings
            enable_realtime_transcription=True,
            realtime_processing_pause=0.2,   # Update every 200ms for responsiveness
            realtime_model_type=WHISPER_MODEL,  # Use same model for consistency
            
            # Callbacks
            on_recording_stop=on_recording_stop,
            on_realtime_transcription_stabilized=type_text_realtime,
            
            # Performance settings
            use_microphone=True,
            no_log_file=True,
            spinner=False,                   # Disable spinner for cleaner output
            early_transcription_on_silence=1,    # Faster transcription on silence
        ) as recorder:
            
            print(f"✅ {WHISPER_MODEL} model loaded")
            print(f"🎤 Start speaking... (will auto-stop after {SILENCE_THRESHOLD}s of silence)")
            play_audio_file("on.wav")

            recorder.start()
            # Record and get final text
            final_text = recorder.text()

            type_text_realtime(final_text)
            
            print(f"\n✅ Complete transcription: '{final_text}'")
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        play_audio_file("off.wav")
    except Exception as e:
        print(f"Fatal error: {e}")
        play_audio_file("off.wav")
        sys.exit(1)
    
    print("✅ Exiting...")
    sys.exit(0)


if __name__ == "__main__":
    main()