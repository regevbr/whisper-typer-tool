# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a real-time streaming voice-to-text typing tool that uses RealtimeSTT library for efficient speech transcription. The application starts recording immediately when executed, provides live transcription feedback as you speak, automatically stops after detecting silence, and types the transcribed text at the current cursor position.

**Key Change**: The project has been refactored from a custom chunking implementation to use the RealtimeSTT library, which provides superior audio processing, dual VAD systems, and built-in streaming transcription capabilities.

## Development Commands

### Setup and Installation
```bash
# System dependencies (Linux - Ubuntu, Debian)
sudo apt-get install python3 python3-pip git ffmpeg portaudio19-dev python3-dev

# Install Python dependencies using uv (preferred)
uv sync

# Alternative with pip (if requirements.txt exists)
pip install -r requirements.txt
```

### Running the Application
```bash
# Run with uv (preferred)
uv run whisper-typer-tool.py

# Alternative direct execution
python whisper-typer-tool.py
```

## Architecture

### Simplified RealtimeSTT Architecture

The application now uses **RealtimeSTT library** which handles all complex audio processing internally:

1. **Main Thread**: Initializes RealtimeSTT recorder with callbacks
2. **RealtimeSTT Internal**: Handles audio capture, VAD, streaming transcription
3. **Callback Functions**: Process transcription updates and type text

### Core Components

#### RealtimeSTT AudioToTextRecorder
- **Dual VAD System**: Uses both WebRTC VAD and Silero VAD for accurate speech detection
- **Built-in Audio Processing**: Handles chunking, overlap, and streaming internally
- **Real-time Callbacks**: Provides incremental transcription updates
- **Automatic Stopping**: Stops after configurable silence duration

#### Text Processing Pipeline
1. **Speech Detection**: Dual VAD detects speech start/stop
2. **Real-time Transcription**: Incremental transcription updates via callbacks
3. **Text Deduplication**: Simple string comparison to avoid retyping
4. **Cross-platform Typing**: Uses clipboard paste for reliable text insertion

#### Key Simplifications
- **No manual threading**: RealtimeSTT handles all audio processing threads
- **No chunk management**: Built-in overlap and boundary handling
- **No VAD implementation**: Uses battle-tested VAD systems
- **No audio format handling**: Automatic sample rate and format conversion

### Configuration Constants

```python
# Core settings
WHISPER_MODEL = "base"           # Model: tiny, base, small, medium, large  
SILENCE_THRESHOLD = 4            # Seconds before auto-stop

# RealtimeSTT Configuration
silero_sensitivity = 0.4         # Silero VAD sensitivity (0.0-1.0)
webrtc_sensitivity = 2           # WebRTC VAD aggressiveness (0-3)
realtime_processing_pause = 0.2  # Update frequency (seconds)
post_speech_silence_duration = 4 # Silence threshold for stopping
enable_realtime_transcription = True  # Enable live transcription
realtime_model_type = "base"     # Model for real-time updates (matches WHISPER_MODEL)
```

### Built-in Features

RealtimeSTT provides these capabilities automatically:

1. **Smart Audio Processing**: Automatic chunking with optimal overlap
2. **Word Boundary Detection**: Prevents word splits without manual intervention
3. **Dual VAD System**: WebRTC for fast detection + Silero for accuracy
4. **Real-time Feedback**: Incremental transcription as you speak
5. **Automatic Stopping**: Configurable silence detection
6. **Model Optimization**: Uses appropriate models for real-time vs final transcription

### Error Handling Patterns

- **Audio device failures**: RealtimeSTT handles gracefully with fallback options
- **Model loading errors**: Clear error messages and early exit
- **Transcription errors**: Built-in error handling with retry logic
- **Keyboard input errors**: Fallback to character-by-character typing

## Key Implementation Details

### Text Deduplication Logic (`type_text_realtime`)
Simple and effective approach for preventing duplicate text output:

1. **String comparison**: Checks if new text starts with already typed text
2. **Length-based filtering**: Only types genuinely new content
3. **Whitespace handling**: Filters out empty or whitespace-only additions
4. **Global tracking**: Uses global `last_typed_text` variable to track progress

### Cross-Platform Text Input
- Uses pyperclip + `Ctrl+V` for reliable text insertion across platforms
- Works in any application with text input (editors, browsers, terminals)
- Small delay ensures clipboard is properly set before pasting
- Error handling with detailed warning messages

### RealtimeSTT Integration
- CPU-optimized with `device="cpu"` and `compute_type="int8"`  
- Uses same model (base) for both real-time and final transcription for consistency
- Dual VAD system for robust speech detection
- Automatic audio format conversion and sample rate handling

## Common Development Tasks

### Testing Audio Issues  
- ALSA warnings are normal and can be ignored
- First run may be slow due to model downloads (Silero VAD, Whisper models)
- Test with different microphone devices if audio input fails
- Check `pulseaudio` or `alsa` settings if no audio input detected

### Modifying Transcription Behavior
- Adjust `SILENCE_THRESHOLD` for different pause sensitivities
- Change `WHISPER_MODEL` size for accuracy vs speed trade-offs
- Modify `silero_sensitivity` and `webrtc_sensitivity` for VAD tuning
- Change `realtime_processing_pause` for update frequency

### Debugging Issues
- Monitor `💬 New:` output to see what content is being typed
- Check RealtimeSTT logs for audio processing issues
- Verify clipboard functionality with `pyperclip.paste()` in Python console
- Use `realtime_model_type="small"` or `realtime_model_type="medium"` for better real-time accuracy (slower)