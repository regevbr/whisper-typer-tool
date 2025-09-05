#!/usr/bin/env python3

import unittest
from unittest.mock import Mock, patch, MagicMock
import threading
import time
from app import WhisperTyperApp


class TestServerMode(unittest.TestCase):
    """Test server mode functionality"""
    
    def test_server_mode_initialization(self):
        """Test that server mode initializes correctly"""
        with patch('app.AudioManager'), \
             patch('app.TypeController'), \
             patch('app.TranscriptionHandler') as mock_transcription:
            
            # Mock the transcription handler and recorder
            mock_recorder = Mock()
            mock_recorder.__enter__ = Mock(return_value=mock_recorder)
            mock_recorder.__exit__ = Mock(return_value=False)
            mock_transcription.return_value.create_recorder.return_value = mock_recorder
            
            app = WhisperTyperApp(server_mode=True)
            
            # Test server mode flag is set
            self.assertTrue(app.server_mode)
            
            # Initialize the app
            with app:
                # Verify persistent recorder is created in server mode
                self.assertIsNotNone(app.recorder)
                mock_transcription.return_value.create_recorder.assert_called_once()
                mock_recorder.__enter__.assert_called_once()
    
    def test_non_server_mode_has_persistent_recorder(self):
        """Test that non-server mode also creates persistent recorder (unified architecture)"""
        with patch('app.AudioManager'), \
             patch('app.TypeController'), \
             patch('app.TranscriptionHandler') as mock_transcription:
            
            # Mock the recorder for unified architecture
            mock_recorder = Mock()
            mock_recorder.__enter__ = Mock(return_value=mock_recorder)
            mock_recorder.__exit__ = Mock(return_value=False)
            mock_transcription.return_value.create_recorder.return_value = mock_recorder
            
            app = WhisperTyperApp(server_mode=False)
            
            # Test server mode flag is not set
            self.assertFalse(app.server_mode)
            
            # Initialize the app
            with app:
                # Verify persistent recorder is created in both modes (unified architecture)
                self.assertIsNotNone(app.recorder)
                mock_transcription.return_value.create_recorder.assert_called_once()
    
    def test_record_once_works_in_both_modes(self):
        """Test that record_once works in both server and non-server modes (unified architecture)"""
        with patch('app.AudioManager') as mock_audio_manager, \
             patch('app.TypeController') as mock_type_controller, \
             patch('app.TranscriptionHandler') as mock_transcription:
            
            # Setup mocks for unified architecture
            mock_recorder = Mock()
            mock_recorder.__enter__ = Mock(return_value=mock_recorder)
            mock_recorder.__exit__ = Mock(return_value=False)
            mock_recorder.text.return_value = "test transcription"
            mock_transcription.return_value.create_recorder.return_value = mock_recorder
            
            mock_audio = Mock()
            mock_audio_manager.return_value = mock_audio
            
            mock_typer = Mock()
            mock_type_controller.return_value = mock_typer
            
            # Test non-server mode works too (unified architecture)
            app = WhisperTyperApp(server_mode=False)
            with app:
                app.record_once()
                
                # Verify expected method calls
                mock_typer.reset.assert_called()
                mock_audio.play_audio_file.assert_any_call("on.wav")
                mock_recorder.start.assert_called_once()
                mock_recorder.text.assert_called_once()
                mock_typer.type_text_realtime.assert_called_with("test transcription")
    
    def test_record_once_functionality(self):
        """Test record_once method functionality"""
        with patch('app.AudioManager') as mock_audio_manager, \
             patch('app.TypeController') as mock_type_controller, \
             patch('app.TranscriptionHandler') as mock_transcription:
            
            # Setup mocks
            mock_recorder = Mock()
            mock_recorder.__enter__ = Mock(return_value=mock_recorder)
            mock_recorder.__exit__ = Mock(return_value=False)
            mock_recorder.text.return_value = "test transcription"
            mock_transcription.return_value.create_recorder.return_value = mock_recorder
            
            mock_audio = Mock()
            mock_audio_manager.return_value = mock_audio
            
            mock_typer = Mock()
            mock_type_controller.return_value = mock_typer
            
            # Create server mode app
            app = WhisperTyperApp(server_mode=True)
            
            with app:
                # Call record_once
                app.record_once()
                
                # Verify expected method calls
                mock_typer.reset.assert_called()
                mock_audio.play_audio_file.assert_any_call("on.wav")
                mock_recorder.start.assert_called_once()
                mock_recorder.text.assert_called_once()
                mock_typer.type_text_realtime.assert_called_with("test transcription")
    
    def test_cleanup_with_persistent_recorder(self):
        """Test proper cleanup of persistent recorder"""
        with patch('app.AudioManager'), \
             patch('app.TypeController'), \
             patch('app.TranscriptionHandler') as mock_transcription:
            
            # Mock the recorder
            mock_recorder = Mock()
            mock_recorder.__enter__ = Mock(return_value=mock_recorder)
            mock_recorder.__exit__ = Mock(return_value=False)
            mock_transcription.return_value.create_recorder.return_value = mock_recorder
            
            app = WhisperTyperApp(server_mode=True)
            
            # Initialize and cleanup
            app.__enter__()
            app.__exit__(None, None, None)
            
            # Verify recorder cleanup was called
            mock_recorder.__exit__.assert_called_once()


class TestWhisperTyperServerModule(unittest.TestCase):
    """Test the server module functionality"""
    
    def test_server_initialization(self):
        """Test server initialization (import test)"""
        # This test mainly ensures the module can be imported and basic structure is correct
        try:
            import sys
            import os
            
            # Add current directory to path for importing the server module
            server_path = os.path.join(os.path.dirname(__file__), 'whisper-typer-server.py')
            
            # Import the module using importlib
            import importlib.util
            spec = importlib.util.spec_from_file_location("whisper_typer_server", server_path)
            server_module = importlib.util.module_from_spec(spec)
            
            # Mock dependencies before loading
            with patch('pynput.keyboard'), \
                 patch('app.WhisperTyperApp'):
                
                spec.loader.exec_module(server_module)
                
                # Test basic class exists and can be instantiated  
                WhisperTyperServer = server_module.WhisperTyperServer
                server = WhisperTyperServer()
                
                # Check basic attributes
                self.assertEqual(server.model_name, "tiny")
                self.assertEqual(server.silence_threshold, 4)
                self.assertFalse(server.is_recording)
                self.assertFalse(server.is_shutting_down)
                
        except Exception as e:
            self.fail(f"Could not import or test WhisperTyperServer: {e}")


if __name__ == '__main__':
    unittest.main()