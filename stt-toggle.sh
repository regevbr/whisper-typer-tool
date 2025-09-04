#!/bin/bash

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

echo "Starting dictation..."
cd /home/regevbr/Downloads/whisper-typer-tool
uv run whisper-typer-tool.py &
disown
