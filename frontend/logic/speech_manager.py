#!/usr/bin/env python3
import asyncio
import logging

from PySide6.QtCore import QObject, Signal, Slot

from frontend.config import logger
from frontend.stt.deepgram_stt import DeepgramSTT
from frontend.settings_manager import get_settings_manager

class SpeechManager(QObject):
    """
    Manages speech recognition and synthesis states.
    """
    # Signals
    sttTextReceived = Signal(str)           # Emitted when partial or final STT text arrives
    sttStateChanged = Signal(bool)          # Emitted when STT state toggles
    sttInputTextReceived = Signal(str)      # Emitted when complete STT utterance should be set as input text
    sttAutoSubmitText = Signal(str)         # Emitted when text should be automatically submitted to chat

    def __init__(self, parent=None):
        super().__init__(parent)
        self.stt_listening = False
        self.is_toggling_stt = False
        self.tts_audio_playing = False
        
        # Get settings manager
        self.settings_manager = get_settings_manager()
        
        # Initialize Deepgram STT
        self.frontend_stt = DeepgramSTT()

        # Configure initial auto-send state from settings
        auto_send_enabled = self.settings_manager.get_auto_send()
        self.frontend_stt.set_auto_send(auto_send_enabled)
        logger.info(f"[SpeechManager] Initialized with auto-send: {auto_send_enabled}")

        # Connect to STT signals
        self.frontend_stt.transcription_received.connect(self.handle_interim_stt_text)
        self.frontend_stt.complete_utterance_received.connect(self.handle_frontend_stt_text)
        self.frontend_stt.state_changed.connect(self.handle_frontend_stt_state)
        self.frontend_stt.auto_send_utterance.connect(self.handle_auto_send_text)
        
        logger.info("[SpeechManager] Initialized with Deepgram STT")

    def handle_interim_stt_text(self, text):
        """Handle partial transcription updates"""
        if text.strip():
            logger.debug(f"[SpeechManager] Interim STT text: {text}")
            self.sttTextReceived.emit(text)

    def handle_frontend_stt_text(self, text):
        """Handle final transcription results"""
        if text.strip():
            logger.info(f"[SpeechManager] Complete utterance: {text}")
            self.sttTextReceived.emit(text)
            self.sttInputTextReceived.emit(text)

    def handle_frontend_stt_state(self, is_listening):
        """Handle STT state changes"""
        try:
            self.stt_listening = is_listening
            self.sttStateChanged.emit(is_listening)
            logger.info(f"[SpeechManager] STT state changed: {is_listening}")
        except asyncio.exceptions.CancelledError:
            logger.warning("[SpeechManager] STT state update task was cancelled - expected during shutdown")
        except Exception as e:
            logger.error(f"[SpeechManager] Error updating STT state: {e}")

    def handle_auto_send_text(self, text):
        """Handle auto-send text"""
        if text.strip():
            logger.info(f"[SpeechManager] Auto-send utterance: {text}")
            self.sttAutoSubmitText.emit(text)

    @Slot()
    def toggle_stt(self):
        """
        Toggles STT capture using the Deepgram STT implementation.
        """
        if self.is_toggling_stt:
            return
        self.is_toggling_stt = True
        try:
            if hasattr(self.frontend_stt, 'toggle'):
                self.frontend_stt.toggle()
            else:
                logger.error("[SpeechManager] Frontend STT implementation missing toggle method")
                self.handle_frontend_stt_state(not self.stt_listening)
        except asyncio.exceptions.CancelledError:
            logger.warning("[SpeechManager] STT toggle task was cancelled - expected during shutdown")
        except Exception as e:
            logger.error(f"[SpeechManager] Error toggling STT: {e}")
            self.handle_frontend_stt_state(not self.stt_listening)
        finally:
            self.is_toggling_stt = False
    
    def is_stt_enabled(self):
        """Returns whether STT is currently enabled"""
        return self.frontend_stt.is_enabled

    def set_paused(self, paused):
        """Pause or resume STT without changing the enabled state"""
        self.frontend_stt.set_paused(paused)
        logger.info(f"[SpeechManager] STT paused: {paused}")

    @Slot(bool)
    def set_auto_send(self, enabled):
        """Enable or disable automatic sending of transcribed text to chat"""
        self.frontend_stt.set_auto_send(enabled)
        # Save setting to make it persistent
        self.settings_manager.set_auto_send(enabled)
        logger.info(f"[SpeechManager] Auto-send {'enabled' if enabled else 'disabled'}")

    def is_auto_send_enabled(self):
        """Returns whether auto-send is currently enabled"""
        return self.frontend_stt.get_auto_send()

    def cleanup(self):
        """Clean up resources"""
        if hasattr(self.frontend_stt, 'stop'):
            self.frontend_stt.stop()
            logger.info("[SpeechManager] Stopped Deepgram STT")