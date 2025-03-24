#!/usr/bin/env python3
import json
import asyncio
import aiohttp
import logging

from PySide6.QtCore import QObject, Signal, Slot, Property, QTimer

from frontend.config import HTTP_BASE_URL, logger
from frontend.logic.audio_manager import AudioManager
from frontend.logic.websocket_client import WebSocketClient
from frontend.logic.speech_manager import SpeechManager
from frontend.logic.message_handler import MessageHandler

class ChatController(QObject):
    """
    Main controller that coordinates all chat components.
    """
    # Signals for QML - these forward signals from the components
    messageReceived = Signal(str)           # From MessageHandler
    sttTextReceived = Signal(str)           # From SpeechManager
    sttStateChanged = Signal(bool)          # From SpeechManager
    audioReceived = Signal(bytes)           # From WebSocketClient
    connectionStatusChanged = Signal(bool)  # From WebSocketClient
    ttsStateChanged = Signal(bool)          # From TTS state queries
    messageChunkReceived = Signal(str, bool)  # From MessageHandler
    sttInputTextReceived = Signal(str)      # From SpeechManager

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True
        self._connected = False
        self._ttsEnabled = False
        self.is_toggling_tts = False
        
        # Get the event loop but don't start tasks immediately
        self._loop = asyncio.get_event_loop()
        
        # Initialize component managers
        self.audio_manager = AudioManager()
        self.speech_manager = SpeechManager()
        self.message_handler = MessageHandler()
        self.websocket_client = WebSocketClient()
        
        # Connect signals
        self._connect_signals()
        
        # Tasks for async operations
        self._ws_task = None
        self._audio_task = None
        
        # Start tasks with a small delay to ensure QML is set up
        QTimer = __import__('PySide6.QtCore', fromlist=['QTimer']).QTimer
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(100)  # 100ms delay
        timer.timeout.connect(self._startTasks)
        timer.start()
        
        # Query TTS state at startup
        tts_timer = QTimer(self)
        tts_timer.setSingleShot(True)
        tts_timer.setInterval(1000)  # 1 second delay
        tts_timer.timeout.connect(lambda: self._loop.create_task(self._queryTTSState()))
        tts_timer.start()
        
        logger.info("[ChatController] Initialized")

    def _connect_signals(self):
        """Connect signals between components"""
        # WebSocket client signals
        self.websocket_client.connectionStatusChanged.connect(self._handle_connection_change)
        self.websocket_client.messageReceived.connect(self._handle_websocket_message)
        # FIXED: Connect to a regular method that will schedule the coroutine
        self.websocket_client.audioReceived.connect(self._handle_audio_data_signal)
        
        # Speech manager signals
        self.speech_manager.sttTextReceived.connect(self.sttTextReceived)
        self.speech_manager.sttStateChanged.connect(self.sttStateChanged)
        self.speech_manager.sttInputTextReceived.connect(self.sttInputTextReceived)
        
        # MessageHandler signals
        self.message_handler.messageReceived.connect(self.messageReceived)
        self.message_handler.messageChunkReceived.connect(self.messageChunkReceived)
        
        # AudioManager sink state changes
        self.audio_manager.audioSink.stateChanged.connect(self.audio_manager.handle_audio_state_changed)

    def _startTasks(self):
        """Start the background tasks"""
        logger.info("[ChatController] Starting background tasks")
        self._ws_task = self._loop.create_task(self.websocket_client.start_connection_loop())
        self._audio_task = self._loop.create_task(self.audio_manager.start_audio_consumer())

    def _handle_connection_change(self, connected):
        """Handle WebSocket connection status changes"""
        self._connected = connected
        self.connectionStatusChanged.emit(connected)

    def _handle_websocket_message(self, data):
        """Process incoming WebSocket messages"""
        msg_type = data.get("type")
        
        if msg_type == "stt":
            stt_text = data.get("stt_text", "")
            logger.debug(f"[ChatController] Processing STT text immediately: {stt_text}")
            self.sttTextReceived.emit(stt_text)
        elif msg_type == "stt_state":
            is_listening = data.get("is_listening", False)
            logger.debug(f"[ChatController] Updating STT state: listening = {is_listening}")
            self.sttStateChanged.emit(is_listening)
        else:
            # Try to process as a message
            self.message_handler.process_message(data)

    # FIXED: Added a non-coroutine method to handle the signal
    def _handle_audio_data_signal(self, audio_data):
        """
        Non-coroutine method that schedules the async processing of audio data.
        This is what gets connected to the audioReceived signal.
        """
        self._loop.create_task(self._handle_audio_data(audio_data))
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
        
        # Add message to history
        self.message_handler.add_message("user", text)
        
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
            "messages": self.message_handler.get_messages()
        }
        
        # If we're continuing from an interrupted response, tell the server
        if has_interrupted:
            payload["continue_response"] = True
        
        # Send asynchronously
        self._loop.create_task(self.websocket_client.send_message(payload))
        logger.info(f"[ChatController] Sending message: {text}{' (continuing interrupted response)' if has_interrupted else ''}")

    @Slot()
    def toggleSTT(self):
        """Toggle speech-to-text functionality"""
        self.speech_manager.toggle_stt()

    @Slot()
    def toggleTTS(self):
        """Toggle text-to-speech functionality"""
        if self.is_toggling_tts:
            return
        self.is_toggling_tts = True
        self._loop.create_task(self._toggleTTSAsync())

    async def _toggleTTSAsync(self):
        """
        The actual async implementation of toggling TTS.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{HTTP_BASE_URL}/api/toggle-tts") as resp:
                    data = await resp.json()
                    self._ttsEnabled = data.get("tts_enabled", not self._ttsEnabled)
                    self.ttsStateChanged.emit(self._ttsEnabled)
                    logger.info(f"[ChatController] TTS toggled => {self._ttsEnabled}")
        except Exception as e:
            logger.error(f"[ChatController] Error toggling TTS: {e}")
        finally:
            self.is_toggling_tts = False

    @Slot()
    def stopAll(self):
        """Stop all ongoing operations"""
        logger.info("[ChatController] Stop all triggered.")
        # Mark the current response as interrupted before stopping
        self.message_handler.mark_response_as_interrupted()
        self._loop.create_task(self._stopAllAsync())

    async def _stopAllAsync(self):
        """
        Stop TTS/generation and clean up resources.
        """
        # Save current TTS state before stopping
        current_tts_state = self._ttsEnabled
        logger.info(f"[ChatController] Current TTS state before stopping: {current_tts_state}")
        
        try:
            # Stop server-side operations
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{HTTP_BASE_URL}/api/stop-audio") as resp1:
                    resp1_data = await resp1.json()
                    logger.info(f"[ChatController] Stop TTS response: {resp1_data}")

                async with session.post(f"{HTTP_BASE_URL}/api/stop-generation") as resp2:
                    resp2_data = await resp2.json()
                    logger.info(f"[ChatController] Stop generation response: {resp2_data}")

                # Restore TTS state if needed
                if current_tts_state:
                    logger.info("[ChatController] Restoring TTS state to enabled")
                    await asyncio.sleep(0.5)  # Small delay to avoid race condition
                    async with session.post(f"{HTTP_BASE_URL}/api/toggle-tts") as resp3:
                        data = await resp3.json()
                        restored_state = data.get("tts_enabled", False)
                        logger.info(f"[ChatController] TTS state after restore attempt: {restored_state}")
                        if restored_state != current_tts_state:
                            # Try once more if state doesn't match expected
                            await asyncio.sleep(0.5)
                            async with session.post(f"{HTTP_BASE_URL}/api/toggle-tts") as resp4:
                                final_data = await resp4.json()
                                self._ttsEnabled = final_data.get("tts_enabled", current_tts_state)
                                self.ttsStateChanged.emit(self._ttsEnabled)
                        else:
                            self._ttsEnabled = restored_state
                            self.ttsStateChanged.emit(self._ttsEnabled)
        except Exception as e:
            logger.error(f"[ChatController] Error stopping TTS and generation on server: {e}")
            # Still try to preserve TTS state
            self._ttsEnabled = current_tts_state
            self.ttsStateChanged.emit(self._ttsEnabled)

        # Stop client-side audio playback
        await self.audio_manager.stop_playback()
        logger.info("[ChatController] Audio resources cleaned up")

    @Slot()
    def clearChat(self):
        """Clear the chat history"""
        logger.info("[ChatController] Clearing chat history.")
        self.message_handler.clear_history()

    async def _queryTTSState(self):
        """Query the current TTS state from the server"""
        logger.info("[ChatController] Querying initial TTS state from server")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{HTTP_BASE_URL}/api/tts-state") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self._ttsEnabled = data.get("tts_enabled", False)
                        logger.info(f"[ChatController] Initial TTS state from server: {self._ttsEnabled}")
                        self.ttsStateChanged.emit(self._ttsEnabled)
                    else:
                        logger.warning(f"[ChatController] Failed to get TTS state: {resp.status}")
                        self._ttsEnabled = False
                        self.ttsStateChanged.emit(self._ttsEnabled)
        except Exception as e:
            logger.error(f"[ChatController] Error querying TTS state: {e}")
            self._ttsEnabled = False
            self.ttsStateChanged.emit(self._ttsEnabled)

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

        # Clean up speech manager
        self.speech_manager.cleanup()
        
        # Cancel WebSocket task
        if hasattr(self, "_ws_task") and self._ws_task and not self._ws_task.done():
            self._ws_task.cancel()
        
        # Clean up WebSocket client
        self.websocket_client.cleanup()

        # Cancel audio task
        if hasattr(self, "_audio_task") and self._audio_task and not self._audio_task.done():
            self._audio_task.cancel()
        
        # Clean up audio manager
        self.audio_manager.cleanup()
        
        logger.info("[ChatController] Cleanup complete.")