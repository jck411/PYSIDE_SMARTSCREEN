#!/usr/bin/env python3
import json
import time
from typing import List, Dict, Any, Optional
from PySide6.QtCore import QObject, Signal

from frontend.config import logger
from frontend.settings_manager import get_settings_manager

class ChatHistoryManager(QObject):
    """
    Dedicated manager for chat history persistence.
    
    This class is responsible for:
    1. Storing and retrieving chat messages
    2. Ensuring messages are properly persisted across screen changes
    3. Handling conversation state
    """
    # Signals
    historyChanged = Signal()  # Emitted when history changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings_manager = get_settings_manager()
        self._conversations = []  # List of conversations
        self._current_conversation_id = None
        self._load_from_settings()
        
        logger.info("[ChatHistoryManager] Initialized")
    
    def _load_from_settings(self):
        """Load conversations from settings"""
        try:
            stored_data = self._settings_manager.get_setting("chat", "history", {})
            if stored_data:
                self._conversations = stored_data.get("conversations", [])
                self._current_conversation_id = stored_data.get("current_conversation_id")
                
                # If no current conversation, create one
                if not self._current_conversation_id and self._conversations:
                    self._current_conversation_id = self._conversations[-1]["id"]
                elif not self._conversations:
                    self._create_new_conversation()
                    
                logger.info(f"[ChatHistoryManager] Loaded {len(self._conversations)} conversations from settings")
            else:
                # Initialize with empty conversation
                self._create_new_conversation()
                logger.info("[ChatHistoryManager] No stored conversations found, created new conversation")
        except Exception as e:
            logger.error(f"[ChatHistoryManager] Error loading from settings: {e}")
            self._create_new_conversation()
    
    def _save_to_settings(self):
        """Save conversations to settings"""
        try:
            data = {
                "conversations": self._conversations,
                "current_conversation_id": self._current_conversation_id
            }
            self._settings_manager.set_setting("chat", "history", data)
            logger.info(f"[ChatHistoryManager] Saved {len(self._conversations)} conversations to settings")
        except Exception as e:
            logger.error(f"[ChatHistoryManager] Error saving to settings: {e}")
    
    def _create_new_conversation(self) -> str:
        """Create a new conversation and return its ID"""
        import uuid
        
        conversation_id = str(uuid.uuid4())
        conversation = {
            "id": conversation_id,
            "created_at": time.time(),
            "updated_at": time.time(),
            "messages": []
        }
        
        self._conversations.append(conversation)
        self._current_conversation_id = conversation_id
        self._save_to_settings()
        
        logger.info(f"[ChatHistoryManager] Created new conversation with ID: {conversation_id}")
        return conversation_id
    
    def _get_current_conversation(self) -> Dict[str, Any]:
        """Get the current conversation"""
        if not self._current_conversation_id:
            self._create_new_conversation()
        
        for conversation in self._conversations:
            if conversation["id"] == self._current_conversation_id:
                return conversation
        
        # If conversation not found, create a new one
        logger.warning(f"[ChatHistoryManager] Current conversation ID {self._current_conversation_id} not found, creating new one")
        self._create_new_conversation()
        return self._get_current_conversation()
    
    def add_message(self, sender: str, text: str) -> None:
        """
        Add a message to the current conversation
        
        Args:
            sender: 'user' or 'assistant'
            text: Message content
        """
        if not text.strip():
            return
            
        conversation = self._get_current_conversation()
        
        # Check if this is a duplicate of the last message
        if conversation["messages"] and conversation["messages"][-1]["sender"] == sender:
            last_msg = conversation["messages"][-1]
            # If the new message is very similar to the last one, replace it
            if self._is_similar(last_msg["text"], text):
                logger.info(f"[ChatHistoryManager] Replacing similar {sender} message")
                conversation["messages"][-1]["text"] = text
                conversation["updated_at"] = time.time()
                self._save_to_settings()
                self.historyChanged.emit()
                return
        
        # Add new message
        message = {
            "sender": sender,
            "text": text,
            "timestamp": time.time()
        }
        
        conversation["messages"].append(message)
        conversation["updated_at"] = time.time()
        self._save_to_settings()
        
        logger.info(f"[ChatHistoryManager] Added message from {sender}, length: {len(text)}")
        self.historyChanged.emit()
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages in the current conversation"""
        conversation = self._get_current_conversation()
        return conversation["messages"]
    
    def get_messages_for_qml(self) -> List[Dict[str, Any]]:
        """
        Get messages formatted for QML ListView model
        
        Returns:
            List of dictionaries with 'text' and 'isUser' keys for QML
        """
        raw_messages = self.get_messages()
        
        # Simply convert to QML format without complex filtering
        qml_messages = []
        for msg in raw_messages:
            qml_messages.append({
                "text": msg["text"],
                "isUser": msg["sender"] == "user"
            })
        
        logger.info(f"[ChatHistoryManager] Returning {len(qml_messages)} messages for QML")
        return qml_messages
    
    def clear_history(self) -> None:
        """Clear the current conversation history"""
        # Clear the current conversation messages
        conversation = self._get_current_conversation()
        conversation["messages"] = []
        conversation["updated_at"] = time.time()
        
        # Save the updated conversation data
        self._save_to_settings()
        
        logger.info("[ChatHistoryManager] Cleared all chat history")
        self.historyChanged.emit()
    
    def _is_similar(self, text1: str, text2: str) -> bool:
        """Check if two texts are similar"""
        # If one is a substring of the other, they're similar
        if text1 in text2 or text2 in text1:
            return True
            
        # If they share a lot of words, they're similar
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
            
        common_words = words1.intersection(words2)
        similarity = len(common_words) / max(len(words1), len(words2))
        
        return similarity > 0.7
        
    def reset_all_history(self) -> None:
        """
        Completely reset all chat history and create a new conversation.
        """
        # Reset conversations list and current ID
        self._conversations = []
        self._current_conversation_id = None
        
        # Reset history data structure
        self._settings_manager.set_setting("chat", "history", {})
        
        # Create a new conversation
        self._create_new_conversation()
        
        logger.info("[ChatHistoryManager] Reset all chat history completely")
        self.historyChanged.emit()

# Singleton instance
_chat_history_manager = None

def get_chat_history_manager():
    """Get the singleton chat history manager instance"""
    global _chat_history_manager
    if _chat_history_manager is None:
        _chat_history_manager = ChatHistoryManager()
    return _chat_history_manager
