#!/usr/bin/env python3
import asyncio
import logging

from PySide6.QtCore import QMutex, QMutexLocker, QIODevice
from PySide6.QtMultimedia import QAudioFormat, QAudioSink, QMediaDevices, QAudio

from frontend.config import logger

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


class AudioManager:
    """
    Manages audio processing and playback.
    """
    def __init__(self):
        self._audio_queue = asyncio.Queue()
        self._running = True
        self.tts_audio_playing = False
        self.setup_audio()

    def setup_audio(self):
        """Set up audio devices and sink"""
        self.audioDevice = QueueAudioDevice()
        self.audioDevice.open(QIODevice.ReadOnly)
        
        audio_format = QAudioFormat()
        audio_format.setSampleRate(24000)
        audio_format.setChannelCount(1)
        audio_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)

        device = QMediaDevices.defaultAudioOutput()
        if device is None:
            logger.error("[AudioManager] No audio output device found!")
        else:
            logger.info("[AudioManager] Default audio output device found.")

        self.audioSink = QAudioSink(device, audio_format)
        self.audioSink.setVolume(1.0)
        self.audioSink.start(self.audioDevice)
        logger.info("[AudioManager] Audio sink started with audio device")

    def handle_audio_state_changed(self, state):
        """Handle audio state changes"""
        logger.info(f"[AudioManager] Audio state changed to: {state}")
        
        def get_audio_state():
            with QMutexLocker(self.audioDevice.mutex):
                return len(self.audioDevice.audio_buffer), self.audioDevice.end_of_stream
        buffer_size, is_end_of_stream = get_audio_state()
        logger.info(f"[AudioManager] Buffer size: {buffer_size}, End of stream: {is_end_of_stream}")

    async def start_audio_consumer(self):
        """
        Continuously writes PCM audio data from the queue to the audio device.
        """
        logger.info("[AudioManager] Starting audio consumer loop.")
        while self._running:
            try:
                pcm_chunk = await self._audio_queue.get()
                if pcm_chunk is None:
                    logger.info("[AudioManager] Received end-of-stream marker.")
                    await asyncio.to_thread(self.audioDevice.mark_end_of_stream)
                    
                    # Wait until buffer is empty
                    while True:
                        buffer_len = await asyncio.to_thread(lambda: len(self.audioDevice.audio_buffer))
                        if buffer_len == 0:
                            logger.info("[AudioManager] Audio buffer is empty, stopping sink.")
                            self.audioSink.stop()
                            break
                        await asyncio.sleep(0.05)
                    
                    # Reset end-of-stream flag
                    await asyncio.to_thread(self.audioDevice.reset_end_of_stream)
                    continue

                # Check if audio sink needs to be restarted
                if self.audioSink.state() != QAudio.State.ActiveState:
                    logger.debug("[AudioManager] Restarting audio sink from non-active state.")
                    self.audioDevice.close()
                    self.audioDevice.open(QIODevice.ReadOnly)
                    self.audioSink.start(self.audioDevice)

                # Write data to device
                bytes_written = await asyncio.to_thread(self.audioDevice.writeData, pcm_chunk)
                logger.debug(f"[AudioManager] Wrote {bytes_written} bytes to device.")
                await asyncio.sleep(0)

            except Exception as e:
                logger.error(f"[AudioManager] Audio consumer error: {e}")
                await asyncio.sleep(0.05)
        
        logger.info("[AudioManager] Audio consumer loop exited.")

    async def process_audio_data(self, audio_data):
        """Process incoming audio data"""
        if audio_data == b'' or len(audio_data) == 0:
            logger.info("[AudioManager] Received empty audio message, marking end-of-stream")
            await self._audio_queue.put(None)
            self.tts_audio_playing = False
            return False  # Return False to indicate end of stream
        else:
            # Process audio data
            await self._audio_queue.put(audio_data)
            # If first chunk, indicate TTS has started
            if not self.tts_audio_playing:
                self.tts_audio_playing = True
            return True  # Return True to indicate active audio

    async def resume_after_audio(self):
        """
        Wait for audio to finish playing
        """
        logger.info("[AudioManager] Waiting for audio to finish playing...")
        while self.audioSink.state() != QAudio.State.StoppedState:
            await asyncio.sleep(0.1)
        logger.info("[AudioManager] Audio finished playing")
        return True

    async def stop_playback(self):
        """
        Stop all audio playback and clear buffers
        """
        logger.info("[AudioManager] Stopping playback and cleaning audio resources")
        current_state = self.audioSink.state()
        logger.info(f"[AudioManager] Audio sink state before stopping: {current_state}")
        if current_state == QAudio.State.ActiveState:
            logger.info("[AudioManager] Audio sink is active; stopping it")
            self.audioSink.stop()
            logger.info("[AudioManager] Audio sink stopped")
        else:
            logger.info(f"[AudioManager] Audio sink not active; current state: {current_state}")

        # Clear the buffer and mark end of stream
        await asyncio.to_thread(self.audioDevice.clear_buffer)
        await asyncio.to_thread(self.audioDevice.mark_end_of_stream)
        
        # Clear the queue
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        self._audio_queue.put_nowait(None)
        logger.info("[AudioManager] End-of-stream marker placed in audio queue; audio resources cleaned up")

    def cleanup(self):
        """Clean up resources"""
        self._running = False
        if self.audioSink.state() == QAudio.State.ActiveState:
            self.audioSink.stop()
        self.audioDevice.close()
        logger.info("[AudioManager] Cleanup complete")