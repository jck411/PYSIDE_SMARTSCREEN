#!/usr/bin/env python3
import asyncio
import aiohttp
import logging

from PySide6.QtCore import QObject, Signal, QTimer

from frontend.config import HTTP_BASE_URL, logger

class TTSController(QObject):
    """
    Manages Text-to-Speech functionality including state and server interactions.
    """
    # Signals
    ttsStateChanged = Signal(bool)  # Emitted when TTS state toggles

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ttsEnabled = False
        self.is_toggling_tts = False
        self._loop = asyncio.get_event_loop()
        
        # Query TTS state at startup
        tts_timer = QTimer(self)
        tts_timer.setSingleShot(True)
        tts_timer.setInterval(1000)  # 1 second delay
        tts_timer.timeout.connect(lambda: self._loop.create_task(self._queryTTSState()))
        tts_timer.start()
        
        logger.info("[TTSController] Initialized")

    async def _queryTTSState(self):
        """Query the current TTS state from the server"""
        logger.info("[TTSController] Querying initial TTS state from server")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{HTTP_BASE_URL}/api/tts-state") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self._ttsEnabled = data.get("tts_enabled", False)
                        logger.info(f"[TTSController] Initial TTS state from server: {self._ttsEnabled}")
                        self.ttsStateChanged.emit(self._ttsEnabled)
                    else:
                        logger.warning(f"[TTSController] Failed to get TTS state: {resp.status}")
                        self._ttsEnabled = False
                        self.ttsStateChanged.emit(self._ttsEnabled)
        except Exception as e:
            logger.error(f"[TTSController] Error querying TTS state: {e}")
            self._ttsEnabled = False
            self.ttsStateChanged.emit(self._ttsEnabled)

    async def toggleTTS(self):
        """
        Toggle Text-to-Speech functionality on the server
        """
        if self.is_toggling_tts:
            return
            
        self.is_toggling_tts = True
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{HTTP_BASE_URL}/api/toggle-tts") as resp:
                    data = await resp.json()
                    self._ttsEnabled = data.get("tts_enabled", not self._ttsEnabled)
                    self.ttsStateChanged.emit(self._ttsEnabled)
                    logger.info(f"[TTSController] TTS toggled => {self._ttsEnabled}")
        except Exception as e:
            logger.error(f"[TTSController] Error toggling TTS: {e}")
        finally:
            self.is_toggling_tts = False

    async def stop_tts(self):
        """Stop TTS playback on the server"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{HTTP_BASE_URL}/api/stop-audio") as resp:
                    resp_data = await resp.json()
                    logger.info(f"[TTSController] Stop TTS response: {resp_data}")
            return True
        except Exception as e:
            logger.error(f"[TTSController] Error stopping TTS: {e}")
            return False

    async def restore_tts_state(self, state_to_restore):
        """Restore TTS to a specific state"""
        logger.info(f"[TTSController] Attempting to restore TTS state to: {state_to_restore}")
        if self._ttsEnabled == state_to_restore:
            logger.info("[TTSController] TTS already in desired state, no action needed")
            return True
            
        try:
            async with aiohttp.ClientSession() as session:
                await asyncio.sleep(0.5)  # Small delay to avoid race condition
                async with session.post(f"{HTTP_BASE_URL}/api/toggle-tts") as resp:
                    data = await resp.json()
                    restored_state = data.get("tts_enabled", False)
                    
                    # If state doesn't match expected, try once more
                    if restored_state != state_to_restore:
                        await asyncio.sleep(0.5)
                        async with session.post(f"{HTTP_BASE_URL}/api/toggle-tts") as resp2:
                            final_data = await resp2.json()
                            self._ttsEnabled = final_data.get("tts_enabled", state_to_restore)
                    else:
                        self._ttsEnabled = restored_state
                        
                    self.ttsStateChanged.emit(self._ttsEnabled)
                    logger.info(f"[TTSController] TTS state after restore: {self._ttsEnabled}")
                    return self._ttsEnabled == state_to_restore
        except Exception as e:
            logger.error(f"[TTSController] Error restoring TTS state: {e}")
            self._ttsEnabled = state_to_restore  # Still update local state
            self.ttsStateChanged.emit(self._ttsEnabled)
            return False

    def get_tts_enabled(self):
        """Get current TTS state"""
        return self._ttsEnabled
