# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a real-time streaming voice-to-text typing tool that uses faster-whisper for efficient speech transcription. The application starts recording immediately when executed, provides live transcription feedback as you speak, automatically stops after detecting silence, and types the transcribed text at the current cursor position.

## Development Commands

### Setup and Installation
```bash
# System dependencies (Linux - Ubuntu, Debian)
sudo apt-get install python3 python3-pip git ffmpeg portaudio19-dev python3-pyaudio

# Install Python dependencies using uv (preferred)
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

### Real-Time Streaming Architecture

This is a **producer-consumer threaded system** with real-time audio processing:

1. **Recording Thread**: Captures audio chunks → feeds to queue → detects silence
2. **Transcription Thread**: Processes chunks with overlap → types partial results → handles word boundaries
3. **Main Thread**: Coordinates lifecycle → handles errors → manages cleanup

### Threading Model

```python
# Two concurrent threads:
recording_thread(audio_queue, stop_flag)    # Producer
transcription_thread(model, audio_queue)    # Consumer
```

**Key synchronization**:
- `queue.Queue` for thread-safe audio chunk passing
- `threading.Event` for coordinated shutdown
- Daemon threads for clean exit on interruption

### Core Components

#### StreamingTranscriber Class
- **Audio overlap handling**: Prevents word splits between chunks
- **Text deduplication**: Avoids typing repeated content at boundaries
- **Context preservation**: Uses previous text as context for better accuracy

#### Recording Thread
- Captures 20ms audio chunks continuously
- Applies WebRTC VAD for speech/silence detection  
- Sends 1-second audio chunks to transcription queue
- Auto-stops after configurable silence threshold

#### Transcription Thread
- Processes audio chunks with 0.5s overlap from previous chunk
- Uses faster-whisper with CPU optimization
- Types only genuinely new content to avoid duplicates

### Audio Processing Pipeline

1. **Capture**: 16kHz mono audio in 20ms chunks (VAD analysis)
2. **Buffer**: Accumulate into 1-second processing chunks
3. **Overlap**: Combine with 0.5s tail from previous chunk
4. **Transcribe**: Process with faster-whisper + context
5. **Deduplicate**: Extract only new text via boundary detection
6. **Type**: Output new text character-by-character

### Configuration Constants

```python
# Core settings
WHISPER_MODEL = "base"           # Model: tiny, base, small, medium, large
SILENCE_THRESHOLD = 4            # Seconds before auto-stop
CHUNK_DURATION = 1.0             # Process every N seconds

# Streaming settings  
AUDIO_OVERLAP = 0.5              # Overlap between chunks (prevents word splits)
TEXT_OVERLAP_WINDOW = 50         # Characters to check for text deduplication
MIN_NEW_TEXT = 1                 # Minimum characters to type

# Audio format
SAMPLE_RATE = 16000              # 16kHz for Whisper optimization
INT16_MAX = 32768.0              # Audio normalization constant
```

### Word-Split Handling

The system handles words split between audio chunks using a **dual-layer approach**:

1. **Audio Layer**: 0.5s overlap ensures Whisper sees complete words
2. **Text Layer**: Boundary detection prevents duplicate typing

**Example**: "beautiful" split as "beau|tiful"
- Chunk 1: "beau" → transcribes as "beautiful" 
- Chunk 2: 0.5s overlap + "tiful" → transcribes as "beautiful sunrise"
- Deduplication: finds "beautiful" overlap → types only " sunrise"

### Error Handling Patterns

- **Audio device failures**: Graceful degradation with warnings
- **VAD failures**: Defaults to assuming speech present
- **Model loading errors**: Early exit with clear error message
- **Thread synchronization**: Timeout-based coordination
- **Transcription errors**: Continue processing, log errors