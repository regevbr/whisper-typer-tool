# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a streamlined voice-to-text typing tool that uses faster-whisper for efficient speech transcription. The application starts recording immediately when executed, provides real-time feedback, automatically stops after detecting silence, transcribes the audio, and types the result at the current cursor position.

## Development Commands

### Setup and Installation
```bash
# Install dependencies using uv (preferred)
uv add -r requirements.txt

# Alternative with pip
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

### Single-Execution Flow

1. **Execute script** → Loads Whisper model → Plays "model_loaded.wav"
2. **Auto-start recording** → Plays "on.wav" → Begins capturing audio
3. **Real-time silence detection** → Uses WebRTC VAD to detect speech/silence
4. **Auto-stop on silence** → Stops after 1.5s of silence detected
5. **Transcribe & type** → Processes audio with faster-whisper → Types result → Exits

### Core Components

- **whisper-typer-tool.py**: Main single-file application with simplified architecture
- **No threading complexity**: Linear execution flow without background threads
- **No hotkey handling**: Immediate recording start, no keyboard listeners

### Key Dependencies

- **faster-whisper**: Efficient Whisper implementation (CPU-optimized)
- **webrtcvad**: Voice activity detection for silence detection
- **pyaudio**: Audio recording and playback
- **pynput**: Text injection at cursor position
- **numpy**: Audio data processing

### Audio Processing Flow

1. Script execution loads faster-whisper model (base, CPU, int8 quantization)
2. WebRTC VAD initialized for silence detection
3. PyAudio stream opens for real-time audio capture (16kHz mono)
4. 20ms audio chunks processed continuously for VAD
5. Speech detection resets silence counter, silence increments it
6. Auto-stop triggers after 1.5 seconds of continuous silence
7. Complete audio buffer transcribed with faster-whisper
8. Transcribed text typed character-by-character with cursor injection

### Configuration

```python
WHISPER_MODEL = "base"           # Model size: tiny, base, small, medium, large
SILENCE_THRESHOLD = 1.5          # Seconds of silence before auto-stop
VAD_AGGRESSIVENESS = 2           # 0-3, higher = more sensitive silence detection
SAMPLE_RATE = 16000              # 16kHz optimal for Whisper
CHUNK_SIZE = 320                 # 20ms chunks (16000 * 0.02)
```

### Audio Files

- `model_loaded.wav`: Played when Whisper model loads successfully
- `on.wav`: Played when recording starts
- `off.wav`: Played when recording stops and processing completes

### File Management

- `transcribe.log`: UTF-8 encoded log with timestamps and transcriptions
- No temporary WAV files created (processes audio in memory)
- Immediate cleanup after transcription completion

### Error Handling

- CPU fallback for CUDA issues
- Graceful VAD failure handling (assumes speech if VAD fails)
- Audio device error handling with warnings
- Keyboard interrupt support (Ctrl+C)