#!/usr/bin/env python3
import json
import asyncio
import logging
import os

from PySide6.QtCore import QObject, Signal, Slot, Property, QTimer

from frontend.config import logger
from frontend.logic.audio_manager import AudioManager
from frontend.logic.websocket_client import WebSocketClient
from frontend.logic.speech_manager import SpeechManager
from frontend.logic.chat.handlers.message_handler import MessageHandler
from frontend.logic.chat.history import get_chat_history_manager
from frontend.logic.voice.wake_word_handler import WakeWordHandler
from frontend.logic.tts_controller import TTSController
from frontend.logic.task_manager import TaskManager
from frontend.logic.service_manager import ServiceManager
from frontend.settings_manager import get_settings_manager

class ChatController(QObject):
    """
    Main controller that coordinates all chat components.
    Uses modular components to manage different aspects of the chat functionality.
    """
    # Signals for QML - these forward signals from the components
    messageReceived = Signal(str)           # From MessageHandler
    sttTextReceived = Signal(str)           # From SpeechManager
    sttStateChanged = Signal(bool)          # From SpeechManager
    audioReceived = Signal(bytes)           # From WebSocketClient
    connectionStatusChanged = Signal(bool)  # From WebSocketClient
    ttsStateChanged = Signal(bool)          # From TTSController
    messageChunkReceived = Signal(str, bool)  # From MessageHandler
    sttInputTextReceived = Signal(str)      # From SpeechManager
    sttAutoSubmitText = Signal(str)         # For auto-submitting STT text to chat

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True
        self._connected = False
        
        # Get the event loop but don't start tasks immediately
        self._loop = asyncio.get_event_loop()
        
        # Initialize task manager for async operations
        self.task_manager = TaskManager(self._loop)
        
        # Get the settings manager
        self.settings_manager = get_settings_manager()
        
        # Initialize component managers
        self.audio_manager = AudioManager()
        self.speech_manager = SpeechManager()
        self.message_handler = MessageHandler()
        self.chat_history_manager = get_chat_history_manager()
        self.websocket_client = WebSocketClient()
        self.tts_controller = TTSController(parent)
        self.service_manager = ServiceManager()
        
        # Always start with a fresh conversation when the app loads
        self.chat_history_manager.new_conversation()
        logger.info("[ChatController] Started a fresh conversation")
        
        # Initialize settings from settings manager
        auto_send_enabled = self.settings_manager.get_auto_send()
        self.speech_manager.set_auto_send(auto_send_enabled)
        logger.info(f"[ChatController] Initialized with auto-send: {auto_send_enabled}")
        
        # Initialize wake word handler
        self.wake_word_handler = WakeWordHandler()
        self.wake_word_handler.set_tts_callback(self._enable_tts_on_wake_word)
        
        # Connect signals
        self._connect_signals()
        
        # Start tasks with a small delay to ensure QML is set up
        QTimer = __import__('PySide6.QtCore', fromlist=['QTimer']).QTimer
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(100)  # 100ms delay
        timer.timeout.connect(self._startTasks)
        timer.start()
        
        logger.info("[ChatController] Initialized")

    def _connect_signals(self):
        """Connect signals between components"""
        # WebSocket client signals
        self.websocket_client.connectionStatusChanged.connect(self._handle_connection_change)
        self.websocket_client.messageReceived.connect(self._handle_websocket_message)
        self.websocket_client.audioReceived.connect(self._handle_audio_data_signal)
        
        # Speech manager signals
        self.speech_manager.sttTextReceived.connect(self.sttTextReceived)
        self.speech_manager.sttStateChanged.connect(self.sttStateChanged)
        self.speech_manager.sttInputTextReceived.connect(self.sttInputTextReceived)
        self.speech_manager.sttAutoSubmitText.connect(self._handle_auto_submit)
        
        # MessageHandler signals
        self.message_handler.messageReceived.connect(self.messageReceived)
        self.message_handler.messageChunkReceived.connect(self.messageChunkReceived)
        
        # TTS controller signals
        self.tts_controller.ttsStateChanged.connect(self.ttsStateChanged)
        
        # AudioManager sink state changes
        self.audio_manager.audioSink.stateChanged.connect(self.audio_manager.handle_audio_state_changed)

    def _startTasks(self):
        """Start the background tasks"""
        logger.info("[ChatController] Starting background tasks")
        self.task_manager.create_task("websocket", self.websocket_client.start_connection_loop())
        self.task_manager.create_task("audio", self.audio_manager.start_audio_consumer())
        
        # Start wake word detection
        self.wake_word_handler.start_listening()
        logger.info("[ChatController] Wake word detection started")

    def _handle_connection_change(self, connected):
        """Handle WebSocket connection status changes"""
        self._connected = connected
        self.connectionStatusChanged.emit(connected)

    def _handle_websocket_message(self, data):
        """Process incoming WebSocket messages"""
        msg_type = data.get("type")
        
        # Log all incoming messages for debugging
        logger.info(f"[ChatController] Received WebSocket message: {msg_type}")
        if "content" in data:
            content_preview = data["content"][:50] + "..." if len(data.get("content", "")) > 50 else data.get("content", "")
            logger.info(f"[ChatController] Message content: {content_preview}")
        
        if msg_type == "stt":
            stt_text = data.get("stt_text", "")
            logger.debug(f"[ChatController] Processing STT text immediately: {stt_text}")
            self.sttTextReceived.emit(stt_text)
        elif msg_type == "stt_state":
            is_listening = data.get("is_listening", False)
            logger.debug(f"[ChatController] Updating STT state: listening = {is_listening}")
            self.sttStateChanged.emit(is_listening)
        else:
            # Process the message through the message handler for streaming
            result = self.message_handler.process_message(data)
            logger.info(f"[ChatController] Message processed: {result}")
            
            # If this is a final message or a complete message, save it to chat history
            if data.get("is_final", False) or (not data.get("is_chunk", False) and "content" in data):
                # This is a complete message, make sure to save it
                logger.info(f"[ChatController] Detected complete message, ensuring it's saved")
                if "content" in data and data["content"].strip():
                    # Save the complete message to chat history
                    self.chat_history_manager.add_message("assistant", data["content"])
                    logger.info(f"[ChatController] Saved complete assistant message: {data['content'][:30]}...")
            
            # If this is a message with punctuation at the end, it might be a complete thought
            elif "content" in data and data["content"].strip():
                content = data["content"].strip()
                if content.endswith(".") or content.endswith("!") or content.endswith("?"):
                    # Save the current accumulated response
                    current_response = self.message_handler.get_current_response()
                    if current_response.strip():
                        logger.info(f"[ChatController] Detected end of thought, saving current response")
                        self.chat_history_manager.add_message("assistant", current_response)
                        logger.info(f"[ChatController] Saved assistant message: {current_response[:30]}...")

    def _handle_audio_data_signal(self, audio_data):
        """
        Non-coroutine method that schedules the async processing of audio data.
        This is what gets connected to the audioReceived signal.
        """
        self.task_manager.schedule_coroutine(self._handle_audio_data(audio_data))
        logger.debug(f"[ChatController] Scheduled audio processing task for {len(audio_data)} bytes")

    async def _handle_audio_data(self, audio_data):
        """Process incoming audio data"""
        # Process the audio in the AudioManager
        is_active = await self.audio_manager.process_audio_data(audio_data)
        
        # Manage STT pausing/resuming during TTS
        if is_active:  # Audio started or continuing
            if self.speech_manager.is_stt_enabled():
                logger.info("[ChatController] Pausing STT during TTS audio playback")
                self.speech_manager.set_paused(True)
        else:  # Audio ended
            if self.speech_manager.is_stt_enabled():
                # Wait for audio to finish playing before resuming STT
                await self.audio_manager.resume_after_audio()
                logger.info("[ChatController] Resuming STT after TTS audio finished")
                self.speech_manager.set_paused(False)
            
            # Notify server that playback is complete
            await self.websocket_client.send_playback_complete()

    @Slot(str)
    def sendMessage(self, text):
        """
        Send a user message.
        """
        text = text.strip()
        if not text or not self.websocket_client.is_connected():
            return
        
        # Check if we have an interrupted response that needs to be continued
        has_interrupted = self.message_handler.has_interrupted_response()
        
        # Add message to chat history
        self.chat_history_manager.add_message("user", text)
        
        # If there's interrupted content, we want to continue from where we left off
        # instead of resetting the current response
        if not has_interrupted:
            self.message_handler.reset_current_response()
        else:
            # Initialize the current response with the interrupted content
            interrupted_text = self.message_handler.get_interrupted_response()
            logger.info(f"[ChatController] Continuing from interrupted response of length: {len(interrupted_text)}")
            
            # Emit the interrupted text as the starting point for the current response
            self.message_handler.messageChunkReceived.emit(interrupted_text, False)
            
            # Clear the interrupted state now that we're continuing
            self.message_handler.clear_interrupted_response()
        
        # Prepare payload
        payload = {
            "action": "chat",
            "messages": self.chat_history_manager.get_messages()
        }
        
        # If we're continuing from an interrupted response, tell the server
        if has_interrupted:
            payload["continue_response"] = True
        
        # Send asynchronously
        self.task_manager.schedule_coroutine(self.websocket_client.send_message(payload))
        logger.info(f"[ChatController] Sending message: {text}{' (continuing interrupted response)' if has_interrupted else ''}")

    @Slot()
    def toggleSTT(self):
        """Toggle speech-to-text functionality"""
        self.speech_manager.toggle_stt()

    @Slot()
    def toggleTTS(self):
        """Toggle text-to-speech functionality"""
        self.task_manager.schedule_coroutine(self.tts_controller.toggleTTS())

    @Slot()
    def stopAll(self):
        """Stop all ongoing operations"""
        logger.info("[ChatController] Stop all triggered.")
        # Mark the current response as interrupted before stopping
        self.message_handler.mark_response_as_interrupted()
        self.task_manager.schedule_coroutine(self._stopAllAsync())

    async def _stopAllAsync(self):
        """
        Stop TTS/generation and clean up resources.
        """
        # Save current TTS state before stopping
        current_tts_state = self.tts_controller.get_tts_enabled()
        logger.info(f"[ChatController] Current TTS state before stopping: {current_tts_state}")
        
        # Stop server-side operations
        await self.service_manager.stop_all_services()
        
        # Restore TTS state if needed
        if current_tts_state:
            logger.info("[ChatController] Restoring TTS state to enabled")
            await self.tts_controller.restore_tts_state(current_tts_state)

        # Stop client-side audio playback
        await self.audio_manager.stop_playback()
        logger.info("[ChatController] Audio resources cleaned up")

    @Slot()
    def clearChat(self):
        """Clear the chat history"""
        logger.info("[ChatController] Clearing chat history.")
        self.chat_history_manager.clear_history()
        
    @Slot()
    def newConversation(self):
        """Start a new conversation"""
        logger.info("[ChatController] Starting a new conversation.")
        self.chat_history_manager.new_conversation()

    @Slot(bool)
    def setAutoSend(self, enabled):
        """Enable or disable automatic sending of transcribed text to chat"""
        logger.info(f"[ChatController] Setting auto-send to {enabled}")
        
        # Save current state for comparison
        current_before = self.speech_manager.is_auto_send_enabled()
        
        # Apply the setting to speech manager
        self.speech_manager.set_auto_send(enabled)
        
        # Double-check the setting was applied
        current_after = self.speech_manager.is_auto_send_enabled()
        logger.info(f"[ChatController] Auto-send setting before change: {current_before}, after: {current_after}")
        
        if current_after != enabled:
            logger.warning(f"[ChatController] Auto-send setting failed to apply! Expected: {enabled}, Actual: {current_after}")
            # Try one more direct approach as a last resort
            try:
                from frontend.settings_manager import get_settings_manager
                settings_manager = get_settings_manager()
                settings_manager.set_auto_send(enabled)
                self.speech_manager.frontend_stt.auto_send = enabled
                logger.info(f"[ChatController] Forced auto-send setting directly to: {enabled}")
            except Exception as e:
                logger.error(f"[ChatController] Error forcing auto-send setting: {e}")

    @Slot()
    def toggleAutoSend(self):
        """Toggle auto-send functionality"""
        current = self.speech_manager.is_auto_send_enabled()
        logger.info(f"[ChatController] Toggling auto-send from {current} to {not current}")
        self.speech_manager.set_auto_send(not current)
        
    def isAutoSendEnabled(self):
        """Get the current auto-send setting"""
        result = self.speech_manager.is_auto_send_enabled()
        logger.info(f"[ChatController] isAutoSendEnabled called, returning: {result}")
        return result
        
    def getChatMessagesForQml(self):
        """Get chat messages formatted for QML"""
        return self.chat_history_manager.get_messages_for_qml()

    def getConnected(self):
        """Get the connection status for Property binding"""
        return self._connected

    connected = Property(bool, fget=getConnected, notify=connectionStatusChanged)

    def cleanup(self):
        """
        Clean up resources on shutdown.
        """
        logger.info("[ChatController] Cleanup called. Stopping tasks.")
        self._running = False

        # Clean up all managers
        self.speech_manager.cleanup()
        self.websocket_client.cleanup()
        self.audio_manager.cleanup()
        self.wake_word_handler.stop_listening()
        
        # Cancel all tasks
        self.task_manager.cleanup()
        
        logger.info("[ChatController] Cleanup complete.")

    async def _enable_tts_on_wake_word(self):
        """Enable STT when wake word is detected"""
        logger.info("[ChatController] Wake word detected - enabling STT")
        
        # Play the wake sound
        try:
            # Construct the path to the wakesound PCM file
            wakesound_path = os.path.join(
                os.path.dirname(__file__), 
                '..', '..', '..', 'wakeword', 'sounds', 'Wakesound.pcm'
            )
            
            # Check if the file exists
            if (wakesound_path):
                logger.info(f"[ChatController] Playing wake sound from {wakesound_path}")
                # Read the PCM data
                with open(wakesound_path, 'rb') as f:
                    pcm_data = f.read()
                
                # Process the PCM audio data
                await self.audio_manager.process_audio_data(pcm_data)
                logger.info("[ChatController] Wake sound playback initiated")
                
                # Send end-of-stream marker to ensure playback completes properly
                await self.audio_manager.process_audio_data(b'')
                logger.info("[ChatController] Wake sound playback completed")
            else:
                logger.error(f"[ChatController] Wake sound file not found at {wakesound_path}")
        except Exception as e:
            logger.error(f"[ChatController] Error playing wake sound: {e}")
        
        # Enable STT if it's not already enabled
        if not self.speech_manager.is_stt_enabled():
            self.toggleSTT()
            logger.info("[ChatController] STT enabled after wake word")

    @Slot(str)
    def _handle_auto_submit(self, text):
        """Handle automatic submission of text from STT to chat"""
        if text.strip():
            # Double-check if auto-send is enabled
            is_auto_send = self.speech_manager.is_auto_send_enabled()
            logger.info(f"[ChatController] Auto-submit triggered, auto-send is: {is_auto_send}")
            
            # Submit only if auto-send is enabled
            if is_auto_send:
                logger.info(f"[ChatController] Auto-submitting text to chat: {text}")
                self.sttAutoSubmitText.emit(text)  # Forward to QML
                self.sendMessage(text)  # Send to backend immediately
                logger.info(f"[ChatController] Auto-submit complete for: {text}")
            else:
                logger.warning(f"[ChatController] Auto-submit was triggered but auto-send is disabled ({is_auto_send}). Not submitting: {text}")
