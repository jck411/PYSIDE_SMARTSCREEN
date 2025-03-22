#!/usr/bin/env python3
import json
import asyncio
import aiohttp
import websockets
import logging

from PySide6.QtCore import (
    QObject, Signal, Slot, Property, QMutex, QMutexLocker, QIODevice
)
from PySide6.QtMultimedia import QAudioFormat, QAudioSink, QMediaDevices, QAudio

from frontend.config import SERVER_HOST, SERVER_PORT, WEBSOCKET_PATH, HTTP_BASE_URL, logger
# Import your frontend STT implementation
from frontend.stt.deepgram_stt import DeepgramSTT

class QueueAudioDevice(QIODevice):
    """
    A queue-like QIODevice for feeding PCM audio data to QAudioSink.
    """
    def __init__(self):
        super().__init__()
        self.audio_buffer = bytearray()
        self.mutex = QMutex()
        self.end_of_stream = False
        self.is_active = False

    def open(self, mode):
        success = super().open(mode)
        if success:
            self.is_active = True
            self.end_of_stream = False
        return success

    def close(self):
        self.is_active = False
        super().close()

    def seek(self, pos):
        return False

    def readData(self, maxSize):
        with QMutexLocker(self.mutex):
            if not self.audio_buffer:
                if self.end_of_stream:
                    logger.debug("[QueueAudioDevice] End of stream reached with empty buffer")
                    return bytes()
                return bytes(maxSize)
            data = bytes(self.audio_buffer[:maxSize])
            self.audio_buffer = self.audio_buffer[maxSize:]
            return data

    def writeData(self, data):
        with QMutexLocker(self.mutex):
            self.audio_buffer.extend(data)
            return len(data)

    def bytesAvailable(self):
        with QMutexLocker(self.mutex):
            return len(self.audio_buffer) + super().bytesAvailable()

    def isSequential(self):
        return True

    def mark_end_of_stream(self):
        with QMutexLocker(self.mutex):
            logger.info(f"[QueueAudioDevice] Marking end of stream, buffer size: {len(self.audio_buffer)}")
            self.end_of_stream = True

    def clear_buffer(self):
        with QMutexLocker(self.mutex):
            logger.info(f"[QueueAudioDevice] Clearing buffer, previous size: {len(self.audio_buffer)}")
            self.audio_buffer.clear()

    def reset_end_of_stream(self):
        with QMutexLocker(self.mutex):
            prev_state = self.end_of_stream
            self.end_of_stream = False
            logger.info(f"[QueueAudioDevice] Reset end-of-stream flag from {prev_state} to {self.end_of_stream}")

class ChatLogic(QObject):
    """
    Comprehensive chat logic with:
      - A single persistent WebSocket connection for sending and receiving messages.
      - STT toggling, TTS toggling, and stop-all functionality.
      - Audio playback via QAudioSink.
      - Signals for partial tokens, final messages, and state changes.
    """

    # Signals for QML
    messageReceived = Signal(str)           # Emitted when a new text message/chunk arrives
    sttTextReceived = Signal(str)           # Emitted when partial or final STT text arrives
    sttStateChanged = Signal(bool)          # Emitted when STT state toggles
    audioReceived = Signal(bytes)           # Emitted when PCM audio is received
    connectionStatusChanged = Signal(bool)  # Emitted when WebSocket connects/disconnects
    ttsStateChanged = Signal(bool)          # Emitted when TTS state toggles
    messageChunkReceived = Signal(str, bool)  # Emitted when a message chunk is received (text, is_final)
    sttInputTextReceived = Signal(str)      # Emitted when complete STT utterance should be set as input text

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True
        self._connected = False
        self._messages = []
        self._sttEnabled = False
        self._ttsEnabled = False
        self._current_response = ""  # Track the current response text
        self.stt_listening = False
        self.is_toggling_stt = False
        self.is_toggling_tts = False
        self.tts_audio_playing = False

        # Get the event loop but don't start tasks immediately
        self._loop = asyncio.get_event_loop()

        # Initialize Deepgram STT
        self.frontend_stt = DeepgramSTT()

        # Connect to STT signals
        self.frontend_stt.transcription_received.connect(self.handle_interim_stt_text)
        self.frontend_stt.complete_utterance_received.connect(self.handle_frontend_stt_text)
        self.frontend_stt.state_changed.connect(self.handle_frontend_stt_state)

        # Audio playback setup
        self.setup_audio()

        # Start tasks in a safe way
        self._ws_task = None
        self._audio_task = None

        # Use a small delay to ensure QML is set up before starting tasks
        QTimer = __import__('PySide6.QtCore', fromlist=['QTimer']).QTimer
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(100)  # 100ms delay
        timer.timeout.connect(self._startTasks)
        timer.start()
        
        # Also query TTS state at startup after a short delay
        tts_timer = QTimer(self)
        tts_timer.setSingleShot(True)
        tts_timer.setInterval(1000)  # 1 second delay to allow connection to establish
        tts_timer.timeout.connect(lambda: self._loop.create_task(self._queryTTSState()))
        tts_timer.start()

    def setup_audio(self):
        """Set up audio devices and sink, matching client.py implementation"""
        self.audioDevice = QueueAudioDevice()
        self.audioDevice.open(QIODevice.ReadOnly)
        
        audio_format = QAudioFormat()
        audio_format.setSampleRate(24000)
        audio_format.setChannelCount(1)
        audio_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)

        device = QMediaDevices.defaultAudioOutput()
        if device is None:
            logger.error("[ChatLogic] No audio output device found!")
        else:
            logger.info("[ChatLogic] Default audio output device found.")

        self.audioSink = QAudioSink(device, audio_format)
        self.audioSink.setVolume(1.0)
        self.audioSink.start(self.audioDevice)
        logger.info("[ChatLogic] Audio sink started with audio device")
        
        self._audio_queue = asyncio.Queue()
        
        # Connect to audio state changes
        self.audioSink.stateChanged.connect(self.handle_audio_state_changed)

    def _startTasks(self):
        logger.info("[ChatLogic] Starting background tasks")
        self._ws_task = self._loop.create_task(self._websocketLoop())
        self._audio_task = self._loop.create_task(self._audioConsumerLoop())

    def handle_audio_state_changed(self, state):
        """Handle audio state changes, matching client.py implementation"""
        logger.info(f"[ChatLogic] Audio state changed to: {state}")
        
        def get_audio_state():
            with QMutexLocker(self.audioDevice.mutex):
                return len(self.audioDevice.audio_buffer), self.audioDevice.end_of_stream
        buffer_size, is_end_of_stream = get_audio_state()
        logger.info(f"[ChatLogic] Buffer size: {buffer_size}, End of stream: {is_end_of_stream}")

    async def _websocketLoop(self):
        """
        Persistent WebSocket loop for sending and receiving data.
        """
        ws_url = f"ws://{SERVER_HOST}:{SERVER_PORT}{WEBSOCKET_PATH}"
        while self._running:
            logger.info(f"[ChatLogic] Attempting WS connection to {ws_url}...")
            try:
                async with websockets.connect(ws_url) as ws:
                    self._connected = True
                    self.connectionStatusChanged.emit(True)
                    logger.info("[ChatLogic] WebSocket connected.")

                    self._ws = ws  # Store reference for sending

                    while self._running:
                        try:
                            raw_msg = await ws.recv()
                            if isinstance(raw_msg, bytes):
                                if raw_msg.startswith(b'audio:'):
                                    audio_data = raw_msg[len(b'audio:'):]
                                    logger.debug(f"[ChatLogic] Received audio chunk of size: {len(audio_data)} bytes")
                                    self.audioReceived.emit(raw_msg)
                                    
                                    # If empty audio message (end of stream)
                                    if raw_msg == b'audio:' or len(audio_data) == 0:
                                        logger.info("[ChatLogic] Received empty audio message, marking end-of-stream")
                                        await self._audio_queue.put(None)
                                        if self.frontend_stt.is_enabled and self.tts_audio_playing:
                                            await self.resume_stt_after_tts()
                                        self.tts_audio_playing = False
                                    else:
                                        # Process audio data
                                        await self._audio_queue.put(audio_data)
                                        
                                        # If first chunk, handle STT pause
                                        if not self.tts_audio_playing:
                                            self.tts_audio_playing = True
                                            if self.frontend_stt.is_enabled:
                                                logger.info("[ChatLogic] Pausing STT using KeepAlive mechanism due to TTS audio starting")
                                                self.frontend_stt.set_paused(True)
                                else:
                                    logger.warning("[ChatLogic] Unknown binary message")
                                    self.audioReceived.emit(b'audio:' + raw_msg)
                            else:
                                try:
                                    data = json.loads(raw_msg)
                                    logger.debug(f"[ChatLogic] Received message: {data}")
                                    
                                    msg_type = data.get("type")
                                    if msg_type == "stt":
                                        stt_text = data.get("stt_text", "")
                                        logger.debug(f"[ChatLogic] Processing STT text immediately: {stt_text}")
                                        self.sttTextReceived.emit(stt_text)
                                    elif msg_type == "stt_state":
                                        is_listening = data.get("is_listening", False)
                                        logger.debug(f"[ChatLogic] Updating STT state: listening = {is_listening}")
                                        self.sttStateChanged.emit(is_listening)
                                    elif "content" in data:
                                        # Check if this is a chunk or a complete message
                                        is_chunk = data.get("is_chunk", False)
                                        is_final = data.get("is_final", False)
                                        content = data["content"]

                                        if is_chunk:
                                            # Accumulate text for streaming
                                            self._current_response += content
                                            # Signal that this is a chunk (not final)
                                            self.messageChunkReceived.emit(self._current_response, False)
                                        elif is_final:
                                            # This is the final state of a streamed message
                                            self.messageChunkReceived.emit(self._current_response, True)
                                            if self._current_response.strip():
                                                self._messages.append({"sender": "assistant", "text": self._current_response})
                                            self._current_response = ""
                                        else:
                                            self.messageReceived.emit(content)
                                            self._current_response = ""
                                            if content.strip():
                                                self._messages.append({"sender": "assistant", "text": content})
                                    else:
                                        logger.warning(f"[ChatLogic] Unknown message type: {data}")
                                except json.JSONDecodeError:
                                    logger.error("[ChatLogic] Failed to parse JSON message")
                                    logger.error(f"[ChatLogic] Raw message: {raw_msg}")
                        except Exception as e:
                            logger.error(f"[ChatLogic] WebSocket message processing error: {e}")
                            await asyncio.sleep(0.1)
                            continue
            except (ConnectionRefusedError, websockets.exceptions.InvalidURI) as e:
                logger.error(f"[ChatLogic] WS connection failed: {e}")
                self._connected = False
                self.connectionStatusChanged.emit(False)
                await asyncio.sleep(2)
            except websockets.exceptions.ConnectionClosedError as e:
                logger.warning(f"[ChatLogic] WS closed: {e}")
                self._connected = False
                self.connectionStatusChanged.emit(False)
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"[ChatLogic] WS error: {e}")
                self._connected = False
                self.connectionStatusChanged.emit(False)
                await asyncio.sleep(2)

        logger.info("[ChatLogic] Exiting WebSocket loop.")
        self._connected = False
        self.connectionStatusChanged.emit(False)

    async def _audioConsumerLoop(self):
        """
        Continuously writes PCM audio data from the queue to the audio device.
        Rewritten to match client.py implementation.
        """
        logger.info("[ChatLogic] Starting audio consumer loop.")
        while self._running:
            try:
                pcm_chunk = await self._audio_queue.get()
                if pcm_chunk is None:
                    logger.info("[ChatLogic] Received end-of-stream marker.")
                    await asyncio.to_thread(self.audioDevice.mark_end_of_stream)
                    
                    # Wait until buffer is empty
                    while True:
                        buffer_len = await asyncio.to_thread(lambda: len(self.audioDevice.audio_buffer))
                        if buffer_len == 0:
                            logger.info("[ChatLogic] Audio buffer is empty, stopping sink.")
                            self.audioSink.stop()
                            break
                        await asyncio.sleep(0.05)
                    
                    # Notify server that playback is complete
                    if hasattr(self, "_ws") and self._ws:
                        await self._ws.send(json.dumps({"action": "playback-complete"}))
                        logger.info("[ChatLogic] Sent playback-complete to server")
                    
                    # Reset end-of-stream flag
                    await asyncio.to_thread(self.audioDevice.reset_end_of_stream)
                    continue

                # Check if audio sink needs to be restarted
                if self.audioSink.state() != QAudio.State.ActiveState:
                    logger.debug("[ChatLogic] Restarting audio sink from non-active state.")
                    self.audioDevice.close()
                    self.audioDevice.open(QIODevice.ReadOnly)
                    self.audioSink.start(self.audioDevice)

                # Write data to device
                bytes_written = await asyncio.to_thread(self.audioDevice.writeData, pcm_chunk)
                logger.debug(f"[ChatLogic] Wrote {bytes_written} bytes to device.")
                await asyncio.sleep(0)

            except Exception as e:
                logger.error(f"[ChatLogic] Audio consumer error: {e}")
                await asyncio.sleep(0.05)
        
        logger.info("[ChatLogic] Audio consumer loop exited.")

    async def resume_stt_after_tts(self):
        """
        Wait for TTS audio to finish playing before resuming STT.
        """
        logger.info("[ChatLogic] Waiting for TTS audio to finish playing to resume STT...")
        while self.audioSink.state() != QAudio.State.StoppedState:
            await asyncio.sleep(0.1)
        if self.frontend_stt.is_enabled:
            logger.info("[ChatLogic] Resuming STT after TTS finished playing")
            self.frontend_stt.set_paused(False)

    @Slot(str)
    def sendMessage(self, text):
        """
        Schedules sending a user message over the persistent WebSocket.
        """
        text = text.strip()
        if not text or not self._connected or not hasattr(self, "_ws"):
            return
        self._loop.create_task(self._sendMessageAsync(text))

    async def _sendMessageAsync(self, text):
        """
        The actual async implementation of sending a message.
        """
        logger.info(f"[ChatLogic] Sending message: {text}")
        self._messages.append({"sender": "user", "text": text})
        self._current_response = ""
        payload = {
            "action": "chat",
            "messages": self._messages
        }
        try:
            await self._ws.send(json.dumps(payload))
        except Exception as e:
            logger.error(f"[ChatLogic] Error sending message: {e}")

    def handle_interim_stt_text(self, text):
        if text.strip():
            logger.debug(f"[ChatLogic] Interim STT text: {text}")
            self.sttTextReceived.emit(text)

    def handle_frontend_stt_text(self, text):
        if text.strip():
            logger.info(f"[ChatLogic] Complete utterance: {text}")
            self.sttTextReceived.emit(text)
            self.sttInputTextReceived.emit(text)

    def handle_frontend_stt_state(self, is_listening):
        try:
            self.stt_listening = is_listening
            self._sttEnabled = is_listening
            self.sttStateChanged.emit(is_listening)
            logger.info(f"[ChatLogic] STT state changed: {is_listening}")
        except asyncio.exceptions.CancelledError:
            logger.warning("[ChatLogic] STT state update task was cancelled - expected during shutdown")
        except Exception as e:
            logger.error(f"[ChatLogic] Error updating STT state: {e}")

    @Slot()
    def toggleSTT(self):
        """
        Toggles STT capture using the Deepgram STT implementation.
        Implementing exact same logic as client.py
        """
        if self.is_toggling_stt:
            return
        self.is_toggling_stt = True
        try:
            if hasattr(self.frontend_stt, 'toggle'):
                self.frontend_stt.toggle()
                self.handle_frontend_stt_state(not self.stt_listening)
            else:
                logger.error("[ChatLogic] Frontend STT implementation missing toggle method")
                self.handle_frontend_stt_state(not self.stt_listening)
        except asyncio.exceptions.CancelledError:
            logger.warning("[ChatLogic] STT toggle task was cancelled - expected during shutdown")
        except Exception as e:
            logger.error(f"[ChatLogic] Error toggling STT: {e}")
            self.handle_frontend_stt_state(not self.stt_listening)
        finally:
            self.is_toggling_stt = False

    @Slot()
    def toggleTTS(self):
        """
        Schedules toggling TTS on the server.
        """
        if self.is_toggling_tts:
            return
        self.is_toggling_tts = True
        self._loop.create_task(self._toggleTTSAsync())

    async def _toggleTTSAsync(self):
        """
        The actual async implementation of toggling TTS.
        Exactly matching client.py implementation.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{HTTP_BASE_URL}/api/toggle-tts") as resp:
                    data = await resp.json()
                    self._ttsEnabled = data.get("tts_enabled", not self._ttsEnabled)
                    self.ttsStateChanged.emit(self._ttsEnabled)
                    logger.info(f"[ChatLogic] TTS toggled => {self._ttsEnabled}")
        except Exception as e:
            logger.error(f"[ChatLogic] Error toggling TTS: {e}")
        finally:
            self.is_toggling_tts = False

    @Slot()
    def stopAll(self):
        """
        Schedules instructing the server to stop TTS/generation and clears local audio buffers.
        """
        logger.info("[ChatLogic] Stop all triggered.")
        self._loop.create_task(self._stopAllAsync())

    async def _stopAllAsync(self):
        """
        The actual async implementation of stopping all.
        Updated to match client.py's implementation exactly.
        """
        logger.info("[ChatLogic] Stop button pressed - stopping TTS and generation")
        
        # Save current TTS state before stopping
        current_tts_state = self._ttsEnabled
        logger.info(f"[ChatLogic] Current TTS state before stopping: {current_tts_state}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{HTTP_BASE_URL}/api/stop-audio") as resp1:
                    resp1_data = await resp1.json()
                    logger.info(f"[ChatLogic] Stop TTS response: {resp1_data}")

                async with session.post(f"{HTTP_BASE_URL}/api/stop-generation") as resp2:
                    resp2_data = await resp2.json()
                    logger.info(f"[ChatLogic] Stop generation response: {resp2_data}")

                # Restore TTS state if needed
                if current_tts_state:
                    logger.info("[ChatLogic] Restoring TTS state to enabled")
                    await asyncio.sleep(0.5)  # Small delay to avoid race condition
                    async with session.post(f"{HTTP_BASE_URL}/api/toggle-tts") as resp3:
                        data = await resp3.json()
                        restored_state = data.get("tts_enabled", False)
                        logger.info(f"[ChatLogic] TTS state after restore attempt: {restored_state}")
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
            logger.error(f"[ChatLogic] Error stopping TTS and generation on server: {e}")
            # Still try to preserve TTS state
            self._ttsEnabled = current_tts_state
            self.ttsStateChanged.emit(self._ttsEnabled)

        logger.info("[ChatLogic] Cleaning frontend audio resources")
        current_state = self.audioSink.state()
        logger.info(f"[ChatLogic] Audio sink state before stopping: {current_state}")
        if current_state == QAudio.State.ActiveState:
            logger.info("[ChatLogic] Audio sink is active; stopping it")
            self.audioSink.stop()
            logger.info("[ChatLogic] Audio sink stopped")
        else:
            logger.info(f"[ChatLogic] Audio sink not active; current state: {current_state}")

        # Use the correct methods from QueueAudioDevice
        await asyncio.to_thread(self.audioDevice.clear_buffer)
        await asyncio.to_thread(self.audioDevice.mark_end_of_stream)
        
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        self._audio_queue.put_nowait(None)
        logger.info("[ChatLogic] End-of-stream marker placed in audio queue; audio resources cleaned up")

    @Slot()
    def clearChat(self):
        """
        Clears the local chat history.
        """
        logger.info("[ChatLogic] Clearing local chat history.")
        self._messages.clear()
        self._current_response = ""

    def getConnected(self):
        return self._connected

    connected = Property(bool, fget=getConnected, notify=connectionStatusChanged)

    def cleanup(self):
        """
        Call on shutdown to cancel tasks and clean up audio.
        Updated to match client.py's implementation.
        """
        logger.info("[ChatLogic] Cleanup called. Stopping tasks.")
        self._running = False

        if hasattr(self, 'frontend_stt') and self.frontend_stt:
            self.frontend_stt.stop()
            logger.info("[ChatLogic] Stopped Deepgram STT")

        if hasattr(self, "_ws_task") and self._ws_task and not self._ws_task.done():
            self._ws_task.cancel()

        if hasattr(self, "_audio_task") and self._audio_task and not self._audio_task.done():
            self._audio_task.cancel()

        if self.audioSink.state() == QAudio.State.ActiveState:
            self.audioSink.stop()

        self.audioDevice.close()
        logger.info("[ChatLogic] Cleanup complete.")

    async def _queryTTSState(self):
        """Query the current TTS state from the server"""
        logger.info("[ChatLogic] Querying initial TTS state from server")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{HTTP_BASE_URL}/api/tts-state") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self._ttsEnabled = data.get("tts_enabled", False)
                        logger.info(f"[ChatLogic] Initial TTS state from server: {self._ttsEnabled}")
                        self.ttsStateChanged.emit(self._ttsEnabled)
                    else:
                        logger.warning(f"[ChatLogic] Failed to get TTS state: {resp.status}")
                        # Just set to False instead of doing fallback
                        self._ttsEnabled = False
                        self.ttsStateChanged.emit(self._ttsEnabled)
        except Exception as e:
            logger.error(f"[ChatLogic] Error querying TTS state: {e}")
            # Set default state instead of toggling twice
            self._ttsEnabled = False
            self.ttsStateChanged.emit(self._ttsEnabled)

    # Remove the _toggleTTSTwice method that was causing issues
