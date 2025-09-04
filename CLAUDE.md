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

## Key Implementation Details

### Text Deduplication Logic (`find_new_content`)
The most critical function for preventing duplicate text output:

1. **Complete duplicate check**: Skips if current text already exists in `total_typed_text`
2. **Boundary overlap detection**: Finds common substrings at chunk boundaries
3. **Semantic duplicate detection**: Uses 70% word overlap threshold on last 20 words
4. **Smart filtering**: Only types genuinely new content

### Audio Input Processing
- Uses cross-platform clipboard pasting (`Ctrl+V`) for reliable text insertion
- Handles both pyperclip and fallback character-by-character typing
- Audio normalization: `int16 → float32` with `INT16_MAX` scaling

### Whisper Integration
- CPU-optimized with `device="cpu"` and `compute_type="int8"`
- Context preservation using last 200 characters as `initial_prompt`
- VAD filtering enabled for better quality
- `beam_size=1` for real-time performance

## Common Development Tasks

### Testing Audio Issues
- ALSA warnings are normal and can be ignored
- Jack server errors are expected when Jack is not running
- Test with different microphone devices if audio input fails

### Modifying Transcription Behavior
- Adjust `SILENCE_THRESHOLD` for different pause sensitivities
- Change `WHISPER_MODEL` size for accuracy vs speed trade-offs
- Modify `TEXT_OVERLAP_WINDOW` for different deduplication sensitivity

### Debugging Streaming Issues
- Monitor `💬 New:` output to see what content is being typed
- Check `total_typed_text` accumulation for deduplication logic
- Observe `🎤`/`🔇` patterns for VAD behavior