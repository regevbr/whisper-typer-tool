# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a real-time streaming voice-to-text typing tool that uses RealtimeSTT library for efficient speech transcription. The application starts recording immediately when executed, provides live transcription feedback as you speak, automatically stops after detecting silence, and types the transcribed text at the current cursor position.

**Key Architecture**: The project uses the RealtimeSTT library instead of custom chunking, which provides superior audio processing, dual VAD systems, and built-in streaming transcription capabilities.

**Local Processing**: All speech recognition is handled locally using OpenAI's Whisper models - no data is sent to external servers or APIs. The application downloads and runs Whisper models directly on your machine for complete privacy and offline operation.

## Development Commands

### Setup and Installation
```bash
# System dependencies (Linux - Ubuntu, Debian)
sudo apt-get install ffmpeg portaudio19-dev python3-dev

# System dependencies (Windows)
# Download ffmpeg from https://ffmpeg.org/ and place ffmpeg.exe in project root
# Install git from https://git-scm.com/download/win
# Install Python from https://www.python.org/downloads/windows/

# System dependencies (macOS)
brew install ffmpeg portaudio python3

# Install uv (if not already installed)
pip install uv

# Setup project with dependencies (preferred method)
uv sync

# Alternative setup from requirements.txt
uv add -r requirements.txt
```

### Running the Application
```bash
# Primary method with uv
uv run whisper-typer-tool.py

# Alternative direct execution (if dependencies installed globally)
python whisper-typer-tool.py
```

### Configuration Changes
The main configuration is at whisper-typer-tool.py:12-13:
- `WHISPER_MODEL`: Model size (tiny, base, small, medium, large)  
- `SILENCE_THRESHOLD`: Seconds before auto-stop

## Architecture

### Single-File Application Structure

The entire application is contained in `whisper-typer-tool.py` with these key components:

1. **Main Entry Point (`main()`)**: Initializes RealtimeSTT AudioToTextRecorder with callback configuration
2. **Real-time Text Processing (`type_text_realtime()`)**: Handles incremental typing with text deduplication
3. **Audio Feedback (`play_audio_file()`)**: Plays on.wav/off.wav for recording state changes
4. **Text Correction Logic (`find_common_prefix_length()`)**: Calculates text differences for smart corrections

### RealtimeSTT Integration Pattern

The application leverages RealtimeSTT's AudioToTextRecorder as a context manager:

- **Dual VAD Configuration**: WebRTC (sensitivity 0-3) + Silero (sensitivity 0.0-1.0) 
- **Callback-Driven Architecture**: `on_realtime_transcription_stabilized` → `type_text_realtime()`
- **CPU Optimization**: Uses `device="cpu"` and `compute_type="int8"` for performance
- **Model Consistency**: Same model for both real-time and final transcription

### Text Processing Pipeline

#### Real-time Text Correction (whisper-typer-tool.py:53-111)
1. **Deduplication Check**: Skip if text unchanged from `last_typed_text`
2. **Common Prefix Calculation**: Find divergence point between old and new text
3. **Backspace Correction**: Delete divergent characters using keyboard simulation
4. **Clipboard Insertion**: Copy new text to clipboard and paste with Ctrl+V
5. **State Tracking**: Update global `last_typed_text` for next comparison

#### Cross-Platform Typing Strategy
- **Primary Method**: pyperclip clipboard + Ctrl+V paste (works in all applications)
- **Fallback**: Individual character typing via pynput (not implemented)
- **Error Handling**: Graceful degradation with warning messages

### Audio System Components

#### Audio Files (on.wav, off.wav)
- Located in project root
- Played via pyaudio during recording state changes
- Error handling if files missing or audio system unavailable

#### Audio Device Handling
- RealtimeSTT manages microphone access automatically
- ALSA warnings are normal and can be ignored on Linux
- Fallback mechanisms handled internally by RealtimeSTT

## Key Implementation Details

### Global State Management
- `last_typed_text`: Global string tracking what's been typed for deduplication
- Reset on each new session in `main()`

### Configuration Constants in AudioToTextRecorder
```python
model=WHISPER_MODEL,                    # Currently "tiny" for speed
language="en",                          # English language
silero_sensitivity=0.4,                 # Speech detection threshold
webrtc_sensitivity=2,                   # VAD aggressiveness  
post_speech_silence_duration=SILENCE_THRESHOLD,  # Currently 4 seconds
realtime_processing_pause=0.2,          # 200ms update frequency
enable_realtime_transcription=True,     # Live transcription enabled
```

### Error Recovery Patterns
- **Audio Errors**: Try-catch around audio operations with warning messages
- **Keyboard Errors**: Try-catch around typing operations with fallback notifications  
- **Model Loading**: Exception handling with sys.exit(1) on fatal errors
- **Keyboard Interrupt**: Clean shutdown with audio feedback