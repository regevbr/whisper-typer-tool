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
- **Two operation modes**: One-off mode (immediate recording) and server mode (hotkey activation)

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

**Step 5 - Run in One-off Mode:**

    uv run whisper-typer-tool.py

**Step 5 - Run in Server Mode:**

    uv run whisper-typer-server.py

## Operation Modes

### One-off Mode (Default)

The traditional mode where the application starts recording immediately when executed and exits after completing one transcription session.

**Usage:**
```bash
uv run whisper-typer-tool.py
# or use the background script:
./stt-toggle.sh
```

**Characteristics:**
- Starts recording immediately
- Exits after one transcription session  
- Loads model each time it's run
- Suitable for occasional use

### Server Mode

A persistent server that runs continuously in the background, pre-loads the Whisper model at startup, and waits for the Menu key to be pressed to start recording sessions.

**Usage:**
```bash
uv run whisper-typer-server.py
# or use the server script:
./stt-server.sh
```

**Characteristics:**
- Runs continuously in the background
- Pre-loads Whisper model once at startup (faster subsequent recordings)
- Press Menu key to start recording (toggles on/off)
- Automatic silence detection stops each recording session
- Can handle multiple recording sessions without restart
- Press Ctrl+C to stop the server

**Server Mode Benefits:**
- **Faster response**: Model is pre-loaded, so recordings start instantly
- **Better for frequent use**: No startup delay between sessions  
- **Hotkey activation**: No need to run commands repeatedly
- **Resource efficient**: Single persistent process instead of multiple startups

## Background Process Scripts

### One-off Mode Script

For convenient keyboard shortcut access, use the included `stt-toggle.sh` script:

This script:
- Sets up the Python environment (pyenv)
- Changes to the script's directory automatically
- Runs the tool in the background (`&`)
- Detaches it from the terminal (`disown`)

### Server Mode Script

For server mode, use the included `stt-server.sh` script:

```bash
./stt-server.sh
```

This script:
- Sets up the Python environment (pyenv)
- Changes to the script's directory automatically  
- Starts the persistent server (does not detach)
- Server continues running until manually stopped

**Note**: The server script runs in the foreground. To run it in the background, use:
```bash
./stt-server.sh &
```

### Setting Up Keyboard Shortcuts

#### For One-off Mode

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

#### For Server Mode

Server mode uses the Menu key as the default hotkey for recording activation. Once the server is running:

1. **Start the server**: Run `./stt-server.sh` or set up a system startup script
2. **Recording activation**: Press the Menu key to start recording  
3. **Automatic stop**: Recording stops after silence is detected
4. **Multiple sessions**: Press Menu key again for additional recordings
5. **Stop server**: Press Ctrl+C in the terminal where server is running

**Custom Hotkey**: The hotkey can be modified in `whisper-typer-server.py` by changing the `HOTKEY` variable.

**System Startup** (Optional):
- **Linux**: Add `./stt-server.sh &` to your shell's startup script (`~/.bashrc`, `~/.profile`)
- **Windows**: Add the server script to startup folder or create a Windows service
- **macOS**: Use launchd or add to login items

**Server Mode Recommendation**: Server mode is ideal for users who need voice typing frequently throughout the day, as it eliminates startup delays and provides instant activation via hotkey.
