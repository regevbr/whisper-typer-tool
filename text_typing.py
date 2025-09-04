#!/usr/bin/env python3

import time
import pyperclip
from pynput import keyboard
import difflib


class TypeController:
    """Handles intelligent text typing with corrections and debouncing"""
    
    def __init__(self, debounce_delay=0.1):
        self.last_typed_text = ""
        self.last_update_time = 0
        self.debounce_delay = debounce_delay
    
    def get_text_diff(self, old_text, new_text):
        """Get optimal edit operations using difflib for more efficient text correction"""
        if not old_text:
            return {'type': 'append', 'text': new_text}
        
        if not new_text:
            return {'type': 'delete_all', 'chars_to_delete': len(old_text)}
        
        # Use SequenceMatcher for optimal diff
        matcher = difflib.SequenceMatcher(None, old_text, new_text)
        
        # Get the longest common subsequence
        matching_blocks = matcher.get_matching_blocks()
        
        if not matching_blocks or matching_blocks[0] == (len(old_text), len(new_text), 0):
            # No common parts, replace everything
            return {
                'type': 'replace_all',
                'chars_to_delete': len(old_text),
                'text': new_text
            }
        
        # Find the longest common prefix
        first_match = matching_blocks[0]
        if first_match.a == 0 and first_match.b == 0:
            # Common prefix exists
            prefix_length = first_match.size
            
            if prefix_length == len(old_text):
                # Old text is a prefix of new text, just append
                return {
                    'type': 'append',
                    'text': new_text[prefix_length:]
                }
            elif prefix_length == len(new_text):
                # New text is a prefix of old text, delete excess
                return {
                    'type': 'delete_suffix',
                    'chars_to_delete': len(old_text) - prefix_length
                }
            else:
                # Replace suffix after common prefix
                return {
                    'type': 'replace_suffix',
                    'chars_to_delete': len(old_text) - prefix_length,
                    'text': new_text[prefix_length:]
                }
        else:
            # No common prefix, replace everything
            return {
                'type': 'replace_all',
                'chars_to_delete': len(old_text),
                'text': new_text
            }
    
    def type_text_realtime(self, text):
        """Type text with corrections, deleting and retyping changed portions"""
        if not text or not text.strip():
            return
        
        # Skip if text is exactly the same
        if text == self.last_typed_text:
            return
        
        # Debouncing: avoid rapid consecutive updates
        current_time = time.time()
        if current_time - self.last_update_time < self.debounce_delay:
            return
        
        self.last_update_time = current_time
        
        # Get optimal diff operations using difflib
        diff = self.get_text_diff(self.last_typed_text, text)
        
        try:
            kb = keyboard.Controller()
            
            if diff['type'] == 'append':
                # Simple append case
                new_text_to_type = diff['text']
                print(f"💬 Appending: '{new_text_to_type}'")
                
            elif diff['type'] == 'delete_all':
                # Delete all existing text
                chars_to_delete = diff['chars_to_delete']
                print(f"🗑️ Deleting all {chars_to_delete} characters")
                
                for _ in range(chars_to_delete):
                    kb.press(keyboard.Key.backspace)
                    kb.release(keyboard.Key.backspace)
                
                new_text_to_type = ""
                
            elif diff['type'] == 'delete_suffix':
                # Delete suffix only
                chars_to_delete = diff['chars_to_delete']
                print(f"🗑️ Deleting {chars_to_delete} suffix characters")
                
                for _ in range(chars_to_delete):
                    kb.press(keyboard.Key.backspace)
                    kb.release(keyboard.Key.backspace)
                
                new_text_to_type = ""
                
            elif diff['type'] in ['replace_suffix', 'replace_all']:
                # Delete and replace
                chars_to_delete = diff['chars_to_delete']
                new_text_to_type = diff['text']
                
                print(f"🔄 Replacing: deleting {chars_to_delete} chars, typing '{new_text_to_type}'")
                
                # Send backspace keystrokes to delete the divergent part
                for _ in range(chars_to_delete):
                    kb.press(keyboard.Key.backspace)
                    kb.release(keyboard.Key.backspace)
            
            else:
                new_text_to_type = ""

            # Type the new/corrected text if there is any
            if new_text_to_type:
                # Use pyperclip for cross-platform clipboard operations
                pyperclip.copy(new_text_to_type)
                
                # Small delay to ensure clipboard is set
                time.sleep(0.01)
                
                # Paste using Ctrl+V (cross-platform)
                with kb.pressed(keyboard.Key.ctrl):
                    kb.press('v')
                    kb.release('v')
            
            # Update what we've typed
            self.last_typed_text = text
            
        except Exception as e:
            print(f"Warning: Could not type/correct text: {e}")
    
    def reset(self):
        """Reset typing state for new session"""
        self.last_typed_text = ""
        self.last_update_time = 0