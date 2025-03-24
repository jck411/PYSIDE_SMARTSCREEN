#!/usr/bin/env python3
import logging
from PySide6.QtCore import QObject, Signal

from frontend.config import logger

class MessageHandler(QObject):
    """
    Manages chat message processing and history.
    """
    # Signals
    messageReceived = Signal(str)           # Emitted when a new text message arrives
    messageChunkReceived = Signal(str, bool)  # Emitted when a message chunk is received (text, is_final)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._messages = []
        self._current_response = ""  # Track the current response text
        self._interrupted_response = ""  # Track interrupted response for continuity
        self._last_request_messages = []  # Track messages from last request
        logger.info("[MessageHandler] Initialized")

    def process_message(self, data):
        """
        Process incoming message data from WebSocket.
        
        Args:
            data: Dictionary containing message data
        """
        msg_type = data.get("type")
        
        if "content" in data:
            # Check if this is a chunk or a complete message
            is_chunk = data.get("is_chunk", False)
            is_final = data.get("is_final", False)
            content = data["content"]

            if is_chunk:
                # Accumulate text for streaming
                self._current_response += content
                # Signal that this is a chunk (not final)
                self.messageChunkReceived.emit(self._current_response, False)
                logger.debug(f"[MessageHandler] Received chunk, current length: {len(self._current_response)}")
            elif is_final:
                # This is the final state of a streamed message
                self.messageChunkReceived.emit(self._current_response, True)
                if self._current_response.strip():
                    self.add_message("assistant", self._current_response)
                # Clear interrupted response since we've completed normally
                self._interrupted_response = ""
                self._current_response = ""
                logger.info("[MessageHandler] Received final chunk, message complete")
            else:
                # This is a complete non-chunked message
                self.messageReceived.emit(content)
                # Clear interrupted response since we've completed normally
                self._interrupted_response = ""
                self._current_response = ""
                if content.strip():
                    self.add_message("assistant", content)
                logger.info("[MessageHandler] Received complete message")
            
            return True
        return False

    def add_message(self, sender, text):
        """
        Add a message to the history.
        
        Args:
            sender: String identifying the sender ('user' or 'assistant')
            text: The message content
        """
        if text.strip():
            self._messages.append({"sender": sender, "text": text})
            logger.info(f"[MessageHandler] Added message from {sender}, length: {len(text)}")

    def get_messages(self):
        """
        Get the message history.
        
        Returns:
            List of message dictionaries
        """
        return self._messages

    def store_last_request_state(self):
        """
        Store the current state of messages for continuity.
        This should be called before a new request.
        """
        self._last_request_messages = self._messages.copy()
        logger.info(f"[MessageHandler] Stored message history state with {len(self._last_request_messages)} messages")

    def has_interrupted_response(self):
        """
        Check if there's an interrupted response that can be continued.
        
        Returns:
            Boolean indicating if there's an interrupted response
        """
        return bool(self._interrupted_response.strip())

    def mark_response_as_interrupted(self):
        """
        Mark the current response as interrupted for later continuation.
        This should be called when stopping a response.
        """
        if self._current_response.strip():
            self._interrupted_response = self._current_response
            logger.info(f"[MessageHandler] Marked response as interrupted, length: {len(self._interrupted_response)}")
            return True
        return False

    def get_current_response(self):
        """
        Get the current accumulated response text.
        
        Returns:
            String containing the current response
        """
        return self._current_response

    def get_interrupted_response(self):
        """
        Get the stored interrupted response text.
        
        Returns:
            String containing the interrupted response
        """
        return self._interrupted_response

    def clear_history(self):
        """
        Clear the message history.
        """
        logger.info("[MessageHandler] Clearing message history")
        self._messages.clear()
        self._current_response = ""
        self._interrupted_response = ""
        self._last_request_messages = []

    def reset_current_response(self):
        """
        Reset the current response accumulator.
        """
        prev_len = len(self._current_response)
        self._current_response = ""
        logger.info(f"[MessageHandler] Reset current response. Previous length: {prev_len}")

    def clear_interrupted_response(self):
        """
        Clear the interrupted response state.
        """
        prev_len = len(self._interrupted_response)
        self._interrupted_response = ""
        logger.info(f"[MessageHandler] Cleared interrupted response. Previous length: {prev_len}")