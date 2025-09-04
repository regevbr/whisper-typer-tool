# whisper-typer-tool

This is a real-time voice-to-text typing tool that uses [RealtimeSTT](https://github.com/KoljaB/RealtimeSTT) for efficient speech transcription. The application starts recording immediately when executed, provides live transcription feedback as you speak, automatically stops after detecting silence, and types the transcribed text at the current cursor position.

**🔒 Privacy**: All speech recognition is handled locally using OpenAI's Whisper models - no data is sent to external servers or APIs. Complete offline operation.

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

## Background Process Script

For convenient keyboard shortcut access, use the included `stt-toggle.sh` script:

This script:
- Sets up the Python environment (pyenv)
- Changes to the script's directory automatically
- Runs the tool in the background (`&`)
- Detaches it from the terminal (`disown`)

### Setting Up Keyboard Shortcut

**Linux (GNOME):**
1. Open Settings → Keyboard → Keyboard Shortcuts → Custom Shortcuts
2. Click "+" to add new shortcut
3. Name: "Voice Typing"
4. Command: `/path/to/whisper-typer-tool/stt-toggle.sh`
5. Click "Set Shortcut" and press your desired key combination (e.g., Ctrl+Alt+V)

**Linux (KDE):**
1. System Settings → Shortcuts → Custom Shortcuts
2. Right-click → New → Global Shortcut → Command/URL
3. Name: "Voice Typing"
4. Command: `/path/to/whisper-typer-tool/stt-toggle.sh`
5. Set trigger key combination

**Windows:**
1. Right-click `stt-toggle.sh` → Create shortcut
2. Right-click shortcut → Properties → Shortcut tab
3. Click in "Shortcut key" field and press desired combination
4. Click OK

**macOS:**
1. System Preferences → Keyboard → Shortcuts → App Shortcuts
2. Click "+" → All Applications
3. Menu Title: (leave blank)
4. Keyboard Shortcut: Press desired combination
5. Use Automator to create a service that runs the shell script
