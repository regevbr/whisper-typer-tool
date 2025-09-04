#!/usr/bin/env python3

import pyaudio
import wave
import threading


class AudioManager:
    """Manages audio playback with pre-initialization and non-blocking operations"""
    
    def __init__(self):
        self.audio = None
        self.audio_data = {}
        self._init_audio_system()
        self._preload_audio_files()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self.cleanup()
        return False
    
    def _init_audio_system(self):
        """Initialize PyAudio once at startup"""
        try:
            self.audio = pyaudio.PyAudio()
        except Exception as e:
            print(f"Warning: Could not initialize audio system: {e}")
            self.audio = None
    
    def _preload_audio_files(self):
        """Preload audio files into memory"""
        for filename in ["on.wav", "off.wav"]:
            try:
                with wave.open(filename, 'rb') as wf:
                    self.audio_data[filename] = {
                        'frames': wf.readframes(wf.getnframes()),
                        'format': self.audio.get_format_from_width(wf.getsampwidth()) if self.audio else None,
                        'channels': wf.getnchannels(),
                        'rate': wf.getframerate()
                    }
            except Exception as e:
                print(f"Warning: Could not preload audio file {filename}: {e}")
    
    def play_audio_file(self, filename):
        """Play audio file non-blocking using threading"""
        if not self.audio or filename not in self.audio_data:
            return
        
        # Start playback in a separate thread to avoid blocking
        thread = threading.Thread(target=self._play_audio_thread, args=(filename,))
        thread.daemon = True
        thread.start()
    
    def _play_audio_thread(self, filename):
        """Internal method to play audio in a separate thread"""
        try:
            audio_info = self.audio_data[filename]
            
            stream = self.audio.open(
                format=audio_info['format'],
                channels=audio_info['channels'],
                rate=audio_info['rate'],
                output=True
            )
            
            # Play the preloaded audio data
            stream.write(audio_info['frames'])
            
            stream.stop_stream()
            stream.close()
        except Exception as e:
            print(f"Warning: Could not play audio file {filename}: {e}")
    
    def cleanup(self):
        """Clean up audio resources"""
        if self.audio:
            self.audio.terminate()