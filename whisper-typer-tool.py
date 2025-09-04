#!/usr/bin/env python3

import sys
from app import WhisperTyperApp

# Configuration
WHISPER_MODEL = "tiny"
SILENCE_THRESHOLD = 4    # seconds before auto-stop

def main():
    """Main entry point with proper resource management"""
    try:
        with WhisperTyperApp(WHISPER_MODEL, SILENCE_THRESHOLD) as app:
            app.run()
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
    
    print("✅ Exiting...")
    sys.exit(0)


if __name__ == "__main__":
    main()