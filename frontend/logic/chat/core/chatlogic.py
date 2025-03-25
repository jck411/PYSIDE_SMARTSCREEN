#!/usr/bin/env python3
import json
import asyncio
import logging

from PySide6.QtCore import (
    QObject, Signal, Slot, Property, QTimer
)

from frontend.config import logger
from frontend.logic.chat.core.chat_controller import ChatController

class ChatLogic(QObject):
    """
    Adapter class that maintains the same interface as the old monolithic ChatLogic
    but delegates all functionality to the new modular components.
    
    This class is maintained for backward compatibility.
    """

    # Signals for QML - forwarded from ChatController
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
        
        # Initialize the controller that manages all components
        self.controller = ChatController(parent)
        
        # Connect all signals from controller to this adapter
        self._connect_signals()
        
        logger.info("[ChatLogic] Initialized adapter to new modular components")

    def _connect_signals(self):
        """Connect signals from controller to this adapter class"""
        self.controller.messageReceived.connect(self.messageReceived)
        self.controller.sttTextReceived.connect(self.sttTextReceived)
        self.controller.sttStateChanged.connect(self.sttStateChanged)
        self.controller.audioReceived.connect(self.audioReceived)
        self.controller.connectionStatusChanged.connect(self.connectionStatusChanged)
        self.controller.ttsStateChanged.connect(self.ttsStateChanged)
        self.controller.messageChunkReceived.connect(self.messageChunkReceived)
        self.controller.sttInputTextReceived.connect(self.sttInputTextReceived)

    @Slot(str)
    def sendMessage(self, text):
        """Delegate to controller"""
        self.controller.sendMessage(text)

    @Slot()
    def toggleSTT(self):
        """Delegate to controller"""
        self.controller.toggleSTT()

    @Slot()
    def toggleTTS(self):
        """Delegate to controller"""
        self.controller.toggleTTS()

    @Slot()
    def stopAll(self):
        """Delegate to controller"""
        self.controller.stopAll()

    @Slot()
    def clearChat(self):
        """Delegate to controller"""
        self.controller.clearChat()

    def getConnected(self):
        """Get connection status from controller"""
        return self.controller._connected

    connected = Property(bool, fget=getConnected, notify=connectionStatusChanged)

    def cleanup(self):
        """Delegate cleanup to controller"""
        self.controller.cleanup()

# For backward compatibility with any code that might use QueueAudioDevice directly
from frontend.logic.audio_manager import QueueAudioDevice
