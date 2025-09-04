#!/usr/bin/env python3

import unittest
from unittest.mock import Mock, patch, MagicMock
from text_typing import TypeController


class TestTypeController(unittest.TestCase):
    """Test cases for TypeController class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.type_controller = TypeController(debounce_delay=0.0)  # No debouncing for tests
    
    def test_get_text_diff_append(self):
        """Test append case in text diff"""
        old_text = "Hello"
        new_text = "Hello world"
        diff = self.type_controller.get_text_diff(old_text, new_text)
        
        self.assertEqual(diff['type'], 'append')
        self.assertEqual(diff['text'], ' world')
    
    def test_get_text_diff_delete_all(self):
        """Test delete all case in text diff"""
        old_text = "Hello world"
        new_text = ""
        diff = self.type_controller.get_text_diff(old_text, new_text)
        
        self.assertEqual(diff['type'], 'delete_all')
        self.assertEqual(diff['chars_to_delete'], 11)
    
    def test_get_text_diff_delete_suffix(self):
        """Test delete suffix case in text diff"""
        old_text = "Hello world"
        new_text = "Hello"
        diff = self.type_controller.get_text_diff(old_text, new_text)
        
        self.assertEqual(diff['type'], 'delete_suffix')
        self.assertEqual(diff['chars_to_delete'], 6)
    
    def test_get_text_diff_replace_suffix(self):
        """Test replace suffix case in text diff"""
        old_text = "Hello world"
        new_text = "Hello there"
        diff = self.type_controller.get_text_diff(old_text, new_text)
        
        self.assertEqual(diff['type'], 'replace_suffix')
        self.assertEqual(diff['chars_to_delete'], 6)
        self.assertEqual(diff['text'], ' there')
    
    def test_get_text_diff_replace_all(self):
        """Test replace all case in text diff"""
        old_text = "Hello world"
        new_text = "Goodbye universe"
        diff = self.type_controller.get_text_diff(old_text, new_text)
        
        self.assertEqual(diff['type'], 'replace_all')
        self.assertEqual(diff['chars_to_delete'], 11)
        self.assertEqual(diff['text'], 'Goodbye universe')
    
    def test_get_text_diff_empty_old_text(self):
        """Test diff with empty old text"""
        old_text = ""
        new_text = "Hello"
        diff = self.type_controller.get_text_diff(old_text, new_text)
        
        self.assertEqual(diff['type'], 'append')
        self.assertEqual(diff['text'], 'Hello')
    
    def test_reset(self):
        """Test reset functionality"""
        self.type_controller.last_typed_text = "Some text"
        self.type_controller.last_update_time = 123456789
        
        self.type_controller.reset()
        
        self.assertEqual(self.type_controller.last_typed_text, "")
        self.assertEqual(self.type_controller.last_update_time, 0)
    
    @patch('text_typing.pyperclip.copy')
    @patch('text_typing.keyboard.Controller')
    def test_type_text_realtime_skip_empty(self, mock_keyboard, mock_clipboard):
        """Test that empty text is skipped"""
        self.type_controller.type_text_realtime("")
        self.type_controller.type_text_realtime(None)
        self.type_controller.type_text_realtime("   ")
        
        mock_keyboard.assert_not_called()
        mock_clipboard.assert_not_called()
    
    @patch('text_typing.pyperclip.copy')
    @patch('text_typing.keyboard.Controller')
    def test_type_text_realtime_skip_duplicate(self, mock_keyboard, mock_clipboard):
        """Test that duplicate text is skipped"""
        self.type_controller.last_typed_text = "Hello"
        self.type_controller.type_text_realtime("Hello")
        
        mock_keyboard.assert_not_called()
        mock_clipboard.assert_not_called()


class TestTextDiffAlgorithm(unittest.TestCase):
    """Test cases specifically for text diff algorithm performance"""
    
    def setUp(self):
        self.type_controller = TypeController()
    
    def test_word_boundary_handling(self):
        """Test that word boundaries are handled correctly"""
        old_text = "The quick brown"
        new_text = "The quick brown fox"
        diff = self.type_controller.get_text_diff(old_text, new_text)
        
        self.assertEqual(diff['type'], 'append')
        self.assertEqual(diff['text'], ' fox')
    
    def test_partial_word_correction(self):
        """Test correction of partial words"""
        old_text = "The qui"
        new_text = "The quick"
        diff = self.type_controller.get_text_diff(old_text, new_text)
        
        self.assertEqual(diff['type'], 'append')
        self.assertEqual(diff['text'], 'ck')
    
    def test_middle_word_correction(self):
        """Test correction in middle of sentence"""
        old_text = "The quick brown fox"
        new_text = "The fast brown fox"
        diff = self.type_controller.get_text_diff(old_text, new_text)
        
        self.assertEqual(diff['type'], 'replace_suffix')
        self.assertEqual(diff['chars_to_delete'], 15)  # " quick brown fox"
        self.assertEqual(diff['text'], ' fast brown fox')


if __name__ == '__main__':
    unittest.main()