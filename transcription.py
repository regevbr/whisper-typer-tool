#!/usr/bin/env python3

import torch
from RealtimeSTT import AudioToTextRecorder


class TranscriptionHandler:
    """Handles Whisper model configuration and transcription setup"""
    
    def __init__(self, model_name="base", silence_threshold=4):
        self.model_name = model_name
        self.silence_threshold = silence_threshold
        self.device, self.compute_type = self._get_optimal_device()
    
    def _get_optimal_device(self):
        """Detect optimal device for Whisper inference"""
        if torch.cuda.is_available():
            print(f"✅ CUDA detected: {torch.cuda.get_device_name()}")
            return "cuda", "float16"
        else:
            print("⚠️ CUDA not available, using CPU with int8 quantization")
            return "cpu", "int8"
    
    def create_recorder(self, on_realtime_transcription_callback, on_recording_stop_callback):
        """Create and configure AudioToTextRecorder with optimized settings"""
        return AudioToTextRecorder(
            # Model configuration
            model=self.model_name,
            language="en",
            device=self.device,
            compute_type=self.compute_type,
            
            # VAD Configuration for better speech detection
            silero_sensitivity=0.4,          # Silero VAD sensitivity (0.0-1.0)
            webrtc_sensitivity=2,            # WebRTC VAD aggressiveness (0-3)
            
            # Recording behavior
            post_speech_silence_duration=self.silence_threshold,  # Stop after N seconds of silence
            min_length_of_recording=0.5,     # Minimum recording duration
            
            # Real-time transcription settings
            enable_realtime_transcription=True,
            realtime_processing_pause=0.1,   # Update every 100ms for better responsiveness
            realtime_model_type=self.model_name,  # Use same model for consistency
            
            # Callbacks
            on_recording_stop=on_recording_stop_callback,
            on_realtime_transcription_stabilized=on_realtime_transcription_callback,
            
            # Performance settings
            use_microphone=True,
            no_log_file=True,
            spinner=False,                   # Disable spinner for cleaner output
            early_transcription_on_silence=1,    # Faster transcription on silence
        )