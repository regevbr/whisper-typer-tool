# whisper-typer-tool

This is a real-time voice-to-text typing tool that uses [RealtimeSTT](https://github.com/KoljaB/RealtimeSTT) for efficient speech transcription. The application starts recording immediately when executed, provides live transcription feedback as you speak, automatically stops after detecting silence, and types the transcribed text at the current cursor position.

## Features

- **Real-time transcription**: Text appears as you speak with minimal latency
- **Automatic silence detection**: Stops recording after 4 seconds of silence
- **Intelligent VAD**: Uses dual Voice Activity Detection (WebRTC + Silero) for accurate speech detection
- **No manual chunking**: Built-in handling of audio streaming and word boundaries
- **Cross-platform**: Works on Linux, Windows, and macOS
- **Audio feedback**: Plays sounds when starting/stopping recording
- **Live typing**: Incrementally types text at cursor position in any application

## Setup Instructions

**Step 1 (Linux - Ubuntu, Debian):**

    sudo apt-get install ffmpeg portaudio19-dev python3-dev

**Step 1 (Windows):**

- Download ffmpeg from https://ffmpeg.org/ , unpack it and paste "ffmpeg.exe" in this folder
- Download and Install git from https://git-scm.com/download/win
- Download and Install python3 from https://www.python.org/downloads/windows/

**Step 1 (macOS):**

    brew install ffmpeg portaudio python3

**Step 2: (If you have not installed uv)**

```
pip install uv
```

**Step 3:**

    uv init

**Step 4:**

    uv add -r requirements.txt

**Step 5:**

    uv run whisper-typer-tool.py
