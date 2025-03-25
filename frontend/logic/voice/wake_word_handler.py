#!/usr/bin/env python
# coding: utf-8

"""
Wake word handler module that detects wake words and triggers appropriate actions
"""

import os
import threading
import asyncio
import time
import azure.cognitiveservices.speech as speechsdk
from typing import Callable, Optional, Coroutine, Any

class WakeWordHandler:
    def __init__(self):
        self.is_listening = False
        self.done = False
        self._hey_computer_callback: Optional[Callable[[], Coroutine[Any, Any, None]]] = None
        self._stop_there_callback: Optional[Callable[[], Coroutine[Any, Any, None]]] = None
        self._wake_word_threads = {}
        self._loop = asyncio.get_event_loop()
        
        # Base path for wake word files - adjust if needed
        self.base_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 'wakeword', 'models'
        ))
        
        # Wake word model paths
        self.hey_computer_model = os.path.join(self.base_path, "hey_computer.table")
        self.stop_there_model = os.path.join(self.base_path, "stop_there.table")
        
        # External state references
        self.stt_enabled = False

    def set_tts_callback(self, callback: Callable[[], Coroutine[Any, Any, None]]):
        """Set the callback function to be called when 'hey computer' wake word is detected"""
        self._hey_computer_callback = callback
        
    def set_stop_callback(self, callback: Callable[[], Coroutine[Any, Any, None]]):
        """Set the callback function to be called when 'stop there' wake word is detected"""
        self._stop_there_callback = callback
    
    def update_stt_state(self, is_enabled):
        """Update the STT state"""
        self.stt_enabled = is_enabled
        print(f"Wake word handler updated STT state: {is_enabled}")

    def _recognize_keyword(self, model_path, model_name):
        """Internal method to perform wake word detection"""
        if not os.path.exists(model_path):
            print(f"Error: Wake word model not found at {model_path}")
            return

        model = speechsdk.KeywordRecognitionModel(model_path)
        keyword_recognizer = speechsdk.KeywordRecognizer()

        def recognized_cb(evt):
            """Callback when a keyword is recognized"""
            result = evt.result
            if result.reason == speechsdk.ResultReason.RecognizedKeyword:
                print(f"Wake word detected: {model_name} - {result.text}")
                
                # For "hey computer", only trigger if STT is not already enabled
                if model_name == "hey_computer" and not self.stt_enabled and self._hey_computer_callback:
                    print("Triggering hey_computer callback")
                    asyncio.run_coroutine_threadsafe(self._hey_computer_callback(), self._loop)
                
                # For "stop there", always trigger
                elif model_name == "stop_there" and self._stop_there_callback:
                    print("Triggering stop_there callback")
                    asyncio.run_coroutine_threadsafe(self._stop_there_callback(), self._loop)

        def canceled_cb(evt):
            """Callback when keyword recognition is canceled"""
            result = evt.result
            if result.reason == speechsdk.ResultReason.Canceled:
                print(f'CANCELED: {model_name} - {result.cancellation_details.reason}')
            
            # Mark this specific thread as done but don't affect other threads
            thread_id = threading.get_ident()
            if thread_id in self._wake_word_threads:
                self._wake_word_threads[thread_id] = False

        keyword_recognizer.recognized.connect(recognized_cb)
        keyword_recognizer.canceled.connect(canceled_cb)
        
        thread_id = threading.get_ident()
        self._wake_word_threads[thread_id] = True
        
        while self._wake_word_threads.get(thread_id, False) and self.is_listening:
            try:
                result_future = keyword_recognizer.recognize_once_async(model)
                result_future.get()  # This blocks until the next keyword is recognized
            except Exception as e:
                print(f"Error in {model_name} recognition: {e}")
                # Brief pause to prevent CPU spinning in case of repeated errors
                time.sleep(0.1)
                
        print(f"Stopping {model_name} recognition thread")
        try:
            keyword_recognizer.stop_recognition_async()
        except Exception as e:
            print(f"Error stopping {model_name} recognition: {e}")
            
        # Clean up thread reference
        if thread_id in self._wake_word_threads:
            del self._wake_word_threads[thread_id]

    def start_listening(self):
        """Start listening for both wake words simultaneously"""
        if not self.is_listening:
            self.is_listening = True
            
            # Start two separate threads for each wake word model
            hey_computer_thread = threading.Thread(
                target=self._recognize_keyword, 
                args=(self.hey_computer_model, "hey_computer"),
                daemon=True
            )
            
            stop_there_thread = threading.Thread(
                target=self._recognize_keyword, 
                args=(self.stop_there_model, "stop_there"),
                daemon=True
            )
            
            hey_computer_thread.start()
            stop_there_thread.start()
            
            print("Started listening for both wake words in separate threads")

    def stop_listening(self):
        """Stop listening for wake words"""
        if self.is_listening:
            self.is_listening = False
            
            # Signal all threads to stop
            for thread_id in list(self._wake_word_threads.keys()):
                self._wake_word_threads[thread_id] = False
            
            # Don't join threads as they might be blocked - they'll exit on their next iteration
            # Clear the thread dictionary
            self._wake_word_threads.clear()
            
            print("Signaled all wake word threads to stop")
