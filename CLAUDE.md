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

#### One-off Mode (Traditional)
```bash
# Primary method with uv
uv run whisper-typer-tool.py

# Alternative direct execution (if dependencies installed globally)
python whisper-typer-tool.py

# Background script for keyboard shortcuts
./stt-toggle.sh
```

#### Server Mode (Persistent)
```bash
# Primary method with uv
uv run whisper-typer-server.py

# Alternative direct execution (if dependencies installed globally)
python whisper-typer-server.py

# Background server script
./stt-server.sh

# Background server script (detached)
./stt-server.sh &
```

#### Testing and Benchmarking
```bash
# Run tests
uv run run_tests.py
# or
python run_tests.py

# Run performance benchmarks
uv run benchmark.py
# or
python benchmark.py
```

### Configuration Changes

#### One-off Mode Configuration
The main configuration is at whisper-typer-tool.py:7-8:
- `WHISPER_MODEL`: Model size (tiny, base, small, medium, large)  
- `SILENCE_THRESHOLD`: Seconds before auto-stop

#### Server Mode Configuration  
The server configuration is at whisper-typer-server.py:11-13:
- `WHISPER_MODEL`: Model size (tiny, base, small, medium, large)
- `SILENCE_THRESHOLD`: Seconds before auto-stop  
- `HOTKEY`: Keyboard key for recording activation (default: Menu key)

## Architecture

### Modular Application Structure

The application is now organized into several modules for better maintainability:

1. **whisper-typer-tool.py**: Main entry point for one-off mode
2. **whisper-typer-server.py**: Server mode entry point with persistent operation
3. **app.py**: WhisperTyperApp class with proper resource management (supports both modes)
4. **audio.py**: AudioManager class for non-blocking audio playback
5. **text_typing.py**: TypeController class with intelligent text correction
6. **transcription.py**: TranscriptionHandler class with GPU/CPU auto-detection

#### Key Components:
- **AudioManager**: Handles audio playback with pre-initialization and threading
- **TypeController**: Manages text typing with difflib-based corrections and debouncing  
- **TranscriptionHandler**: Configures Whisper models with optimal device detection
- **WhisperTyperApp**: Coordinates all components with proper resource cleanup (supports both one-off and server modes)

### Server Mode Architecture

Server mode introduces a persistent application architecture optimized for frequent use:

#### Additional Server Components:
- **WhisperTyperServer**: Main server class managing hotkey listening and recording coordination
- **Global Hotkey Listener**: Uses pynput to detect Menu key presses system-wide
- **Threading Coordination**: Separate threads for hotkey listening and recording operations
- **Persistent Model**: Pre-loaded Whisper model shared across multiple recording sessions
- **Signal Handlers**: Graceful shutdown handling for SIGINT/SIGTERM

#### Server Mode Operational Flow:
1. **Initialization**: Server loads Whisper model once and creates persistent recorder
2. **Idle State**: Global hotkey listener waits for Menu key press
3. **Recording Activation**: Menu key triggers recording session in separate thread  
4. **Recording Session**: Uses persistent recorder with real-time transcription and typing
5. **Auto-Stop**: Silence detection ends session, returns to idle state
6. **Resource Persistence**: Model and components remain loaded for next session
7. **Graceful Shutdown**: Signal handlers ensure proper cleanup on exit

#### Performance Benefits:
- **Instant Activation**: No model loading delay (typically 2-5 seconds saved per use)
- **Memory Efficiency**: Single persistent process vs. multiple short-lived processes
- **Resource Optimization**: Shared GPU/CPU resources across recording sessions

### RealtimeSTT Integration Pattern

The application leverages RealtimeSTT's AudioToTextRecorder as a context manager:

- **Dual VAD Configuration**: WebRTC (sensitivity 0-3) + Silero (sensitivity 0.0-1.0) 
- **Callback-Driven Architecture**: `on_realtime_transcription_stabilized` → `type_text_realtime()`
- **GPU/CPU Auto-Detection**: Automatically uses CUDA when available, fallback to CPU with int8
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
realtime_processing_pause=0.1,          # 100ms update frequency (optimized)
enable_realtime_transcription=True,     # Live transcription enabled
```

### Error Recovery Patterns
- **Audio Errors**: Try-catch around audio operations with warning messages
- **Keyboard Errors**: Try-catch around typing operations with fallback notifications  
- **Model Loading**: Exception handling with sys.exit(1) on fatal errors
- **Keyboard Interrupt**: Clean shutdown with audio feedback