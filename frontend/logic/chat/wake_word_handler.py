#!/usr/bin/env python
# coding: utf-8

"""
Wake word handler module that activates TTS when wake words are detected
"""

import os
import threading
import asyncio
import azure.cognitiveservices.speech as speechsdk
from typing import Callable, Optional, Coroutine, Any

class WakeWordHandler:
    def __init__(self):
        self.is_listening = False
        self.done = False
        self._tts_callback: Optional[Callable[[], Coroutine[Any, Any, None]]] = None
        self._wake_word_thread: Optional[threading.Thread] = None
        self._loop = asyncio.get_event_loop()
        
        # Base path for wake word files - adjust if needed
        self.base_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 'wakeword', 'models'
        ))
        
        self.wake_word_model = os.path.join(self.base_path, "hey_computer.table")

    def set_tts_callback(self, callback: Callable[[], Coroutine[Any, Any, None]]):
        """Set the callback function to be called when wake word is detected"""
        self._tts_callback = callback

    def _recognize_keyword(self):
        """Internal method to perform wake word detection"""
        if not os.path.exists(self.wake_word_model):
            print(f"Error: Wake word model not found at {self.wake_word_model}")
            return

        model = speechsdk.KeywordRecognitionModel(self.wake_word_model)
        keyword_recognizer = speechsdk.KeywordRecognizer()

        def recognized_cb(evt):
            """Callback when a keyword is recognized"""
            result = evt.result
            if result.reason == speechsdk.ResultReason.RecognizedKeyword:
                print(f"Wake word detected: {result.text}")
                if self._tts_callback:
                    # Schedule the coroutine on the event loop
                    asyncio.run_coroutine_threadsafe(self._tts_callback(), self._loop)

        def canceled_cb(evt):
            """Callback when keyword recognition is canceled"""
            result = evt.result
            if result.reason == speechsdk.ResultReason.Canceled:
                print(f'CANCELED: {result.cancellation_details.reason}')
            self.done = True

        keyword_recognizer.recognized.connect(recognized_cb)
        keyword_recognizer.canceled.connect(canceled_cb)

        while not self.done and self.is_listening:
            result_future = keyword_recognizer.recognize_once_async(model)
            result_future.get()  # This blocks until the next keyword is recognized

        keyword_recognizer.stop_recognition_async()

    def start_listening(self):
        """Start listening for wake words"""
        if not self.is_listening:
            self.is_listening = True
            self.done = False
            self._wake_word_thread = threading.Thread(target=self._recognize_keyword)
            self._wake_word_thread.start()
            print("Started listening for wake words")

    def stop_listening(self):
        """Stop listening for wake words"""
        if self.is_listening:
            self.is_listening = False
            self.done = True
            if self._wake_word_thread:
                self._wake_word_thread.join()
            print("Stopped listening for wake words")

# Example usage:
if __name__ == "__main__":
    def on_wake_word():
        print("Wake word detected! Activating TTS...")

    handler = WakeWordHandler()
    handler.set_tts_callback(on_wake_word)
    handler.start_listening()
    
    try:
        # Keep the main thread running
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        handler.stop_listening() 