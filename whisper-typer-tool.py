#!/usr/bin/env python3

import sys
import time
import pyaudio
import wave
import numpy as np
import webrtcvad
import threading
import queue
from faster_whisper import WhisperModel
from pynput import keyboard

# Global keyboard controller
pykeyboard = keyboard.Controller()

# Configuration
WHISPER_MODEL = "base"
SILENCE_THRESHOLD = 4    # seconds before auto-stop
VAD_AGGRESSIVENESS = 2   # 0-3, higher = more aggressive silence detection
SAMPLE_RATE = 16000      # 16kHz for optimal Whisper performance
CHUNK_SIZE = 320         # 20ms chunks for VAD (16000 * 0.02)
CHANNELS = 1             # Mono for Whisper

# Streaming configuration
CHUNK_DURATION = 1.0     # Process audio every 1 second
AUDIO_OVERLAP = 0.5      # 0.5 second overlap between chunks
TEXT_OVERLAP_WINDOW = 50 # Check last 50 chars for text overlap
MIN_NEW_TEXT = 1         # Minimum characters to type

# Audio format constants
INT16_MAX = 32768.0      # Maximum value for 16-bit signed integer (2^15)
                         # Used to normalize int16 audio samples to float32 range [-1.0, 1.0]
MIN_AUDIO_DURATION = 0.2 # Minimum audio duration (seconds) to send for transcription
                         # Below this threshold, audio chunks are too short to be meaningful


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
    """Type text at current cursor position using cross-platform clipboard method"""
    if not text or not text.strip():
        return
        
    try:
        # Use pyperclip for cross-platform clipboard operations
        import pyperclip
        
        # Copy our text to clipboard
        pyperclip.copy(text)
        
        # Small delay to ensure clipboard is set
        time.sleep(0.01)
        
        # Paste using Ctrl+V (cross-platform)
        with pykeyboard.pressed(keyboard.Key.ctrl):
            pykeyboard.press('v')
            pykeyboard.release('v')
            
    except ImportError:
        # Fallback to character-by-character typing if pyperclip not available
        print("Warning: pyperclip not available, using character typing (may have issues with special chars)")
        for char in text:
            try:
                pykeyboard.type(char)
                time.sleep(0.003)
            except Exception as e:
                print(f"Warning: Could not type character '{char}': {e}")
    except Exception as e:
        print(f"Warning: Could not type text '{text}': {e}")


class StreamingTranscriber:
    """Handles real-time transcription with audio overlap to prevent word splits"""
    
    def __init__(self, model):
        self.model = model
        self.previous_audio_tail = None
        self.previous_text = ""
        self.total_typed_text = ""
        
    def process_chunk(self, new_audio):
        """
        Process new audio chunk with overlap from previous chunk
        to handle words that were split between chunks
        """
        # Build audio with overlap to capture split words
        if self.previous_audio_tail is not None:
            overlap_samples = int(SAMPLE_RATE * AUDIO_OVERLAP)
            tail_length = min(len(self.previous_audio_tail), overlap_samples)
            
            # Concatenate: [last 0.5s of previous] + [new audio]
            full_audio = np.concatenate([
                self.previous_audio_tail[-tail_length:],
                new_audio
            ])
        else:
            full_audio = new_audio
        
        try:
            # Transcribe the combined audio
            segments, info = self.model.transcribe(
                full_audio,
                initial_prompt=self.total_typed_text[-200:] if self.total_typed_text else "",
                vad_filter=True,
                beam_size=1  # Faster for real-time
            )
            
            # Get transcribed text
            chunk_text = ''.join(segment.text for segment in segments)
            
            if chunk_text.strip():
                # Find new content that hasn't been typed yet
                new_content = self.find_new_content(chunk_text)
                
                if new_content and len(new_content) >= MIN_NEW_TEXT:
                    print(f"💬 New: '{new_content}'")
                    type_text_live(new_content)
                    self.total_typed_text += new_content

                # Update for next iteration
                self.previous_text = chunk_text
                
        except Exception as e:
            print(f"Error in transcription: {e}")
        
        # Save audio tail for next chunk (to handle word boundaries)
        overlap_samples = int(SAMPLE_RATE * AUDIO_OVERLAP)
        if len(new_audio) > overlap_samples:
            self.previous_audio_tail = new_audio[-overlap_samples:]
        else:
            self.previous_audio_tail = new_audio.copy()
    
    def find_new_content(self, current_text):
        """
        Smart detection of new content by checking for overlap at boundaries
        This handles words split between chunks properly
        """
        if not self.previous_text:
            return current_text
        
        # Look for common substring at the boundary
        window = min(TEXT_OVERLAP_WINDOW, len(self.previous_text))
        
        for i in range(window, 0, -1):
            # Check if end of previous matches start of current
            prev_end = self.previous_text[-i:]
            if current_text.startswith(prev_end):
                # Found overlap - return only the new part
                return current_text[i:]
        
        # No overlap found at boundary - might be a complete replacement
        # or correction, return the difference
        return current_text
    
    def finalize(self):
        """Called when recording is complete to get final text"""
        print(f"✅ Final transcription: '{self.total_typed_text}'")


def recording_thread(audio_queue, stop_flag):
    """
    Records audio in chunks and feeds them to the transcription queue
    """
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    stream = None

    # Start recording
    print("Start speaking...")
    play_audio_file("on.wav")

    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )
        
        # Initialize WebRTC VAD for silence detection
        vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
        
        print(f"🎤 Recording... (pause for {SILENCE_THRESHOLD}s to stop)")
        
        chunk_buffer = []
        silence_duration = 0
        samples_per_chunk = int(SAMPLE_RATE * CHUNK_DURATION)
        
        while not stop_flag.is_set():
            try:
                # Read small audio chunk
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                audio_samples = np.frombuffer(data, dtype=np.int16)
                chunk_buffer.extend(audio_samples)
                
                # Check for speech using VAD
                try:
                    is_speech = vad.is_speech(data, SAMPLE_RATE)
                except:
                    is_speech = True  # Assume speech if VAD fails
                
                if is_speech:
                    silence_duration = 0
                    print("🎤", end="", flush=True)
                else:
                    silence_duration += CHUNK_SIZE / SAMPLE_RATE
                    print("🔇", end="", flush=True)
                    
                    # Stop if silence detected for threshold duration
                    if silence_duration >= SILENCE_THRESHOLD:
                        print(f"\n🔇 Silence detected for {SILENCE_THRESHOLD}s, stopping...")
                        stop_flag.set()
                        break
                
                # Send chunk for transcription when we have enough audio
                if len(chunk_buffer) >= samples_per_chunk:
                    # Convert to float32 and normalize
                    audio_chunk = np.array(chunk_buffer[:samples_per_chunk], dtype=np.float32) / INT16_MAX
                    audio_queue.put(audio_chunk)
                    
                    # Remove processed samples (no overlap here - StreamingTranscriber handles overlap)
                    chunk_buffer = chunk_buffer[samples_per_chunk:]
                    
            except Exception as e:
                print(f"Error reading audio: {e}")
                break
        
        # Send any remaining audio
        if chunk_buffer and len(chunk_buffer) > SAMPLE_RATE * MIN_AUDIO_DURATION:
            audio_chunk = np.array(chunk_buffer, dtype=np.float32) / INT16_MAX
            audio_queue.put(audio_chunk)
        
        # Signal end of recording
        audio_queue.put(None)
        
    except Exception as e:
        print(f"Error in recording thread: {e}")
        stop_flag.set()
        
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


def transcription_thread(model, audio_queue, stop_flag):
    """
    Processes audio chunks from queue and performs real-time transcription
    """
    transcriber = StreamingTranscriber(model)
    
    print("🎯 Transcription thread started")
    
    try:
        while True:
            try:
                # Get audio chunk from queue (with timeout to check stop flag)
                audio_chunk = audio_queue.get(timeout=0.1)
                
                if audio_chunk is None:
                    # End of recording signal
                    break
                    
                # Process the chunk
                transcriber.process_chunk(audio_chunk)
                
            except queue.Empty:
                if stop_flag.is_set():
                    break
                continue
            except Exception as e:
                print(f"Error in transcription: {e}")
                
        # Finalize transcription
        transcriber.finalize()
        
    except Exception as e:
        print(f"Error in transcription thread: {e}")


def record_with_streaming_transcription():
    """Main function that coordinates recording and real-time transcription"""
    print("Loading Whisper model...")
    try:
        # Initialize Whisper model for CPU to avoid CUDA issues
        model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        print(f"{WHISPER_MODEL} model loaded")
    except Exception as e:
        print(f"Error loading Whisper model: {e}")
        sys.exit(1)

    # Create shared resources
    audio_queue = queue.Queue(maxsize=10)  # Limit queue size to prevent memory buildup
    stop_flag = threading.Event()
    
    # Start threads
    record_thread = threading.Thread(
        target=recording_thread,
        args=(audio_queue, stop_flag),
        daemon=True
    )
    
    transcribe_thread = threading.Thread(
        target=transcription_thread,
        args=(model, audio_queue, stop_flag),
        daemon=True
    )
    
    try:
        record_thread.start()
        transcribe_thread.start()
        
        # Wait for recording to complete
        record_thread.join()
        
        # Wait for transcription to finish processing
        transcribe_thread.join()
        
        print("\n🎯 Streaming transcription complete")
        
    except Exception as e:
        print(f"Error in main coordination: {e}")
        stop_flag.set()
    
    finally:
        play_audio_file("off.wav")


def main():
    """Main entry point"""
    try:
        record_with_streaming_transcription()
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