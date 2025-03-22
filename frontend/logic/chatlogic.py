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

    def open(self, mode):
        success = super().open(mode)
        return success

    def close(self):
        super().close()

    def seek(self, pos):
        return False

    def readData(self, maxSize):
        with QMutexLocker(self.mutex):
            if not self.audio_buffer:
                if self.end_of_stream:
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
            self.end_of_stream = True

    def clear_buffer(self):
        with QMutexLocker(self.mutex):
            self.audio_buffer.clear()
            self.end_of_stream = False

    def reset_end_of_stream(self):
        with QMutexLocker(self.mutex):
            self.end_of_stream = False

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
        self.stt_listening = True
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
        self.audioDevice = QueueAudioDevice()
        self.audioDevice.open(QIODevice.ReadOnly)
        audio_format = QAudioFormat()
        audio_format.setSampleRate(24000)
        audio_format.setChannelCount(1)
        audio_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)

        self.audioOutputDevice = QMediaDevices.defaultAudioOutput()
        if not self.audioOutputDevice:
            logger.warning("[ChatLogic] No default audio output device found.")
        self.audioSink = QAudioSink(self.audioOutputDevice, audio_format)
        self.audioSink.setVolume(1.0)
        self.audioSink.start(self.audioDevice)

        self._audio_queue = asyncio.Queue()

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

    def _startTasks(self):
        logger.info("[ChatLogic] Starting background tasks")
        self._ws_task = self._loop.create_task(self._websocketLoop())
        self._audio_task = self._loop.create_task(self._audioConsumerLoop())

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
                        raw_msg = await ws.recv()
                        if isinstance(raw_msg, bytes):
                            # Check if the message is exactly the audio prefix (indicating end-of-stream)
                            if raw_msg == b'audio:' or (raw_msg.startswith(b'audio:') and not raw_msg[len(b'audio:'):]):
                                # Enqueue a None marker to signal end-of-stream
                                await self._audio_queue.put(None)
                            elif raw_msg.startswith(b'audio:'):
                                pcm_data = raw_msg[len(b'audio:'):]
                                # If after stripping the prefix the data is empty, treat it as end-of-stream
                                if not pcm_data:
                                    await self._audio_queue.put(None)
                                else:
                                    await self._audio_queue.put(pcm_data)
                            else:
                                logger.warning("[ChatLogic] Unknown binary message.")
                        else:
                            try:
                                data = json.loads(raw_msg)
                            except json.JSONDecodeError:
                                logger.error(f"[ChatLogic] Non-JSON text: {raw_msg}")
                                continue

                            msg_type = data.get("type")
                            if msg_type == "stt":
                                stt_text = data.get("stt_text", "")
                                self.sttTextReceived.emit(stt_text)
                            elif msg_type == "stt_state":
                                is_listening = data.get("is_listening", False)
                                self.sttStateChanged.emit(is_listening)
                            elif msg_type == "tts_state":
                                self._ttsEnabled = data.get("tts_enabled", self._ttsEnabled)
                                self.ttsStateChanged.emit(self._ttsEnabled)
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
                                logger.info(f"[ChatLogic] Unknown data: {data}")
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
        Handles TTS audio playback and STT pausing/resuming.
        """
        logger.info("[ChatLogic] Starting audio consumer loop.")
        while self._running:
            try:
                pcm_data = await self._audio_queue.get()
                if pcm_data is None:
                    logger.info("[ChatLogic] Received end-of-stream marker.")
                    self.audioDevice.mark_end_of_stream()
                    if self._ws and hasattr(self, "_ws"):
                        try:
                            await self._ws.send(json.dumps({"action": "playback-complete"}))
                            logger.info("[ChatLogic] Sent playback-complete to server")
                        except Exception as e:
                            logger.error(f"[ChatLogic] Error sending playback-complete: {e}")
                    if self.frontend_stt.is_enabled and self.tts_audio_playing:
                        await self.resume_stt_after_tts()
                    self.tts_audio_playing = False
                    continue

                # If this is the first audio chunk of a TTS response, pause STT
                if not self.tts_audio_playing:
                    self.tts_audio_playing = True
                    if self.frontend_stt.is_enabled:
                        logger.info("[ChatLogic] Pausing STT using KeepAlive mechanism due to TTS audio starting")
                        self.frontend_stt.set_paused(True)

                if self.audioSink.state() != QAudio.State.ActiveState:
                    logger.debug("[ChatLogic] Restarting audio sink.")
                    self.audioDevice.close()
                    self.audioDevice.open(QIODevice.ReadOnly)
                    self.audioSink.start(self.audioDevice)

                self.audioDevice.writeData(pcm_data)
                await asyncio.sleep(0)
            except Exception as e:
                logger.error(f"[ChatLogic] Audio consumer error: {e}")
                await asyncio.sleep(0.1)
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
        self._loop.create_task(self._toggleTTSAsync())

    async def _toggleTTSAsync(self):
        """
        The actual async implementation of toggling TTS.
        """
        if not self._connected or not hasattr(self, "_ws"):
            logger.warning("[ChatLogic] Not connected; cannot toggle TTS.")
            return
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{HTTP_BASE_URL}/api/toggle-tts") as resp:
                    data = await resp.json()
                    self._ttsEnabled = data.get("tts_enabled", not self._ttsEnabled)
                    self.ttsStateChanged.emit(self._ttsEnabled)
                    logger.info(f"[ChatLogic] TTS toggled => {self._ttsEnabled}")
        except Exception as e:
            logger.error(f"[ChatLogic] Error toggling TTS: {e}")

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
        """
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(f"{HTTP_BASE_URL}/api/stop-audio")
                await session.post(f"{HTTP_BASE_URL}/api/stop-generation")
        except Exception as e:
            logger.error(f"[ChatLogic] Error in stopAll: {e}")

        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        self.audioDevice.clear_buffer()
        self._audio_queue.put_nowait(None)

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
