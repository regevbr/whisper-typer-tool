#!/usr/bin/env python3

import time
import statistics
from text_typing import TypeController


def benchmark_text_diff():
    """Benchmark the text diff algorithm performance"""
    type_controller = TypeController()
    
    # Test cases with varying complexity
    test_cases = [
        # (old_text, new_text, description)
        ("", "Hello", "Empty to short"),
        ("Hello", "Hello world", "Simple append"),
        ("Hello world", "Hello", "Simple delete"),
        ("The quick brown fox", "The fast brown fox", "Middle replacement"),
        ("A very long sentence with many words", "A very long paragraph with many words", "Long text replacement"),
        ("Short", "Completely different text", "Complete replacement"),
        ("The quick brown fox jumps over the lazy dog", 
         "The quick brown fox jumps over the sleeping dog", "Single word change"),
    ]
    
    print("🚀 Benchmarking text diff algorithm...")
    print("-" * 60)
    
    for old_text, new_text, description in test_cases:
        times = []
        
        # Run each test case multiple times
        for _ in range(1000):
            start_time = time.perf_counter()
            diff = type_controller.get_text_diff(old_text, new_text)
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"{description:<25} | Avg: {avg_time*1000:.3f}ms | Min: {min_time*1000:.3f}ms | Max: {max_time*1000:.3f}ms")
        print(f"                         | Operation: {diff['type']}")
        print()


def benchmark_typing_debouncing():
    """Benchmark typing with debouncing"""
    type_controller = TypeController(debounce_delay=0.1)
    
    print("🎯 Testing debouncing behavior...")
    print("-" * 60)
    
    start_time = time.time()
    
    # Simulate rapid updates (should be debounced)
    for i in range(10):
        type_controller.last_typed_text = ""  # Reset to force processing attempt
        with MockKeyboardAndClipboard():
            type_controller.type_text_realtime(f"Hello {i}")
        time.sleep(0.01)  # 10ms intervals (faster than debounce)
    
    end_time = time.time()
    print(f"Rapid updates test completed in {(end_time - start_time)*1000:.1f}ms")
    print()


class MockKeyboardAndClipboard:
    """Mock context manager for testing without actual keyboard/clipboard operations"""
    
    def __enter__(self):
        import unittest.mock
        self.clipboard_patch = unittest.mock.patch('text_typing.pyperclip.copy')
        self.keyboard_patch = unittest.mock.patch('text_typing.keyboard.Controller')
        self.time_patch = unittest.mock.patch('text_typing.time.sleep')
        
        self.clipboard_patch.start()
        self.keyboard_patch.start() 
        self.time_patch.start()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clipboard_patch.stop()
        self.keyboard_patch.stop()
        self.time_patch.stop()


def main():
    """Run all benchmarks"""
    print("🔥 Whisper Typer Tool Performance Benchmarks")
    print("=" * 60)
    print()
    
    benchmark_text_diff()
    benchmark_typing_debouncing()
    
    print("✅ Benchmarks completed!")


if __name__ == '__main__':
    main()