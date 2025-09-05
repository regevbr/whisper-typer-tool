#!/bin/bash

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

echo "Starting Whisper Typer Server..."
cd "$(dirname "${BASH_SOURCE[0]}")"
uv run whisper-typer-server.py