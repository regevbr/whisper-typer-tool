#!/usr/bin/env python3

import sys
import time
import pyaudio
import wave
import numpy as np
import webrtcvad
from pynput import keyboard
from faster_whisper import WhisperModel


# Global keyboard controller
pykeyboard = keyboard.Controller()

# Configuration
WHISPER_MODEL = "base"
SILENCE_THRESHOLD = 4  # seconds before auto-stop
VAD_AGGRESSIVENESS = 2   # 0-3, higher = more aggressive silence detection
SAMPLE_RATE = 16000      # 16kHz for optimal Whisper performance
CHUNK_SIZE = 320         # 20ms chunks for VAD (16000 * 0.02)
CHANNELS = 1             # Mono for Whisper


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


def type_text_live(text):
    """Type text at current cursor position"""
    if not text or not text.strip():
        return
        
    for char in text:
        try:
            pykeyboard.type(char)
            time.sleep(0.003)  # Slight delay for smooth typing
        except:
            print(f"Warning: Could not type character: {char}")


def record_with_silence_detection():
    """Record audio until silence is detected"""
    print("Loading Whisper model...")
    try:
        # Initialize Whisper model for CPU to avoid CUDA issues
        model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        print(f"{WHISPER_MODEL} model loaded")
    except Exception as e:
        print(f"Error loading Whisper model: {e}")
        sys.exit(1)
    
    # Initialize WebRTC VAD for silence detection
    try:
        vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
    except Exception as e:
        print(f"Error initializing VAD: {e}")
        sys.exit(1)
    
    # Start recording immediately
    print("Start speaking...")
    play_audio_file("on.wav")
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    stream = None
    
    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )
        
        silence_duration = 0
        audio_chunks = []
        chunk_count = 0
        
        print("🎤 Recording... (pause for 1.5s to stop)")
        
        while True:
            # Read audio chunk
            try:
                chunk_data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                chunk_count += 1
                audio_chunks.append(chunk_data)
            except Exception as e:
                print(f"Error reading audio: {e}")
                break
            
            # Check for speech using VAD (every 20ms)
            try:
                is_speech = vad.is_speech(chunk_data, SAMPLE_RATE)
            except:
                is_speech = True  # Assume speech if VAD fails
            
            if is_speech:
                silence_duration = 0
                if chunk_count % 50 == 0:  # Show activity every ~1 second
                    print("🎤", end="", flush=True)
            else:
                silence_duration += CHUNK_SIZE / SAMPLE_RATE  # 20ms per chunk
                if chunk_count % 50 == 0:  # Show silence every ~1 second
                    print("🔇", end="", flush=True)
            
            # Stop if silence detected for threshold duration
            if silence_duration >= SILENCE_THRESHOLD:
                print(f"\n🔇 Silence detected for {SILENCE_THRESHOLD}s, stopping...")
                break
        
        print("\n🎯 Processing transcription...")
        
        # Convert collected audio to format suitable for Whisper
        if audio_chunks:
            # Combine all chunks
            audio_data = b''.join(audio_chunks)
            
            # Convert to numpy array and normalize
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcribe using Whisper
            try:
                segments, info = model.transcribe(audio_np, beam_size=5)
                
                print(f"Detected language '{info.language}' with probability {info.language_probability:.2f}")
                
                # Collect all text
                full_text = ""
                for segment in segments:
                    full_text += segment.text
                
                if full_text.strip():
                    print(f"💬 Transcription: {full_text}")
                    
                    # Type the text
                    type_text_live(full_text)
                    
                    print("✅ Text typed successfully")
                else:
                    print("⚠️ No speech detected in recording")
                
            except Exception as e:
                print(f"Error during transcription: {e}")
                
    except Exception as e:
        print(f"Error during recording: {e}")
    
    finally:
        # Cleanup
        if stream:
            try:
                stream.stop_stream()
                stream.close()
            except:
                pass
        
        try:
            p.terminate()
        except:
            pass
        
        play_audio_file("off.wav")
        print("🎯 Recording complete")


def main():
    """Main entry point"""
    try:
        record_with_silence_detection()
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