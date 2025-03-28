#!/usr/bin/env python3
import json
import time
import uuid
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from PySide6.QtCore import QObject, Signal

from frontend.config import logger

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
        self._conversations = []  # List of conversations
        self._current_conversation_id = None
        
        # Create directory for storing conversations
        # Store in project directory instead of home directory
        self._history_dir = Path(os.getcwd()) / "conversations"
        self._history_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or create initial conversation
        self._load_conversations()
        if not self._current_conversation_id or not self._get_current_conversation():
            self._create_new_conversation()
        
        logger.info("[ChatHistoryManager] Initialized")
    
    def _load_conversations(self):
        """Load available conversations from files"""
        try:
            # Load list of available conversations 
            index_file = self._history_dir / "index.json"
            if index_file.exists():
                with open(index_file, 'r') as f:
                    index_data = json.load(f)
                    self._conversations = index_data.get("conversations", [])
                    self._current_conversation_id = index_data.get("current_conversation_id")
            
            # If we have a current conversation ID, load its full content
            if self._current_conversation_id:
                self._load_conversation(self._current_conversation_id)
                
            logger.info(f"[ChatHistoryManager] Loaded {len(self._conversations)} conversations")
        except Exception as e:
            logger.error(f"[ChatHistoryManager] Error loading conversations: {e}")
            self._conversations = []
            self._current_conversation_id = None
    
    def _load_conversation(self, conversation_id):
        """Load a specific conversation file"""
        try:
            conversation_file = self._history_dir / f"{conversation_id}.json"
            if conversation_file.exists():
                with open(conversation_file, 'r') as f:
                    # Find the conversation in our list and update it
                    conversation_data = json.load(f)
                    for i, conv in enumerate(self._conversations):
                        if conv["id"] == conversation_id:
                            self._conversations[i] = conversation_data
                            break
        except Exception as e:
            logger.error(f"[ChatHistoryManager] Error loading conversation {conversation_id}: {e}")
    
    def _save_index(self):
        """Save the conversation index"""
        try:
            # Save only basic info about conversations to the index
            # (not including messages to keep the index small)
            index_conversations = []
            for conv in self._conversations:
                index_conversations.append({
                    "id": conv["id"],
                    "created_at": conv["created_at"],
                    "updated_at": conv["updated_at"]
                })
            
            index_data = {
                "conversations": index_conversations,
                "current_conversation_id": self._current_conversation_id
            }
            
            with open(self._history_dir / "index.json", 'w') as f:
                json.dump(index_data, f, indent=2)
                
            logger.info(f"[ChatHistoryManager] Saved conversation index with {len(index_conversations)} entries")
        except Exception as e:
            logger.error(f"[ChatHistoryManager] Error saving conversation index: {e}")
    
    def _save_current_conversation(self):
        """Save the current conversation to its file"""
        if not self._current_conversation_id:
            return
            
        try:
            conversation = self._get_current_conversation()
            if conversation:
                conversation_file = self._history_dir / f"{conversation['id']}.json"
                with open(conversation_file, 'w') as f:
                    json.dump(conversation, f, indent=2)
                logger.info(f"[ChatHistoryManager] Saved conversation {conversation['id']}")
        except Exception as e:
            logger.error(f"[ChatHistoryManager] Error saving conversation: {e}")
    
    def _create_new_conversation(self) -> str:
        """Create a new conversation and return its ID"""
        conversation_id = str(uuid.uuid4())
        conversation = {
            "id": conversation_id,
            "created_at": time.time(),
            "updated_at": time.time(),
            "messages": []
        }
        
        self._conversations.append(conversation)
        self._current_conversation_id = conversation_id
        
        # Save the new conversation
        self._save_index()
        self._save_current_conversation()
        
        logger.info(f"[ChatHistoryManager] Created new conversation with ID: {conversation_id}")
        return conversation_id
    
    def _get_current_conversation(self) -> Optional[Dict[str, Any]]:
        """Get the current conversation"""
        if not self._current_conversation_id:
            return None
        
        for conversation in self._conversations:
            if conversation["id"] == self._current_conversation_id:
                return conversation
        
        return None
    
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
        if not conversation:
            self._create_new_conversation()
            conversation = self._get_current_conversation()
        
        # Check if this is a duplicate of the last message
        if conversation["messages"] and conversation["messages"][-1]["sender"] == sender:
            last_msg = conversation["messages"][-1]
            # If the new message is very similar to the last one, replace it
            if self._is_similar(last_msg["text"], text):
                logger.info(f"[ChatHistoryManager] Replacing similar {sender} message")
                conversation["messages"][-1]["text"] = text
                conversation["updated_at"] = time.time()
                self._save_current_conversation()
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
        self._save_current_conversation()
        
        logger.info(f"[ChatHistoryManager] Added message from {sender}, length: {len(text)}")
        self.historyChanged.emit()
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages in the current conversation"""
        conversation = self._get_current_conversation()
        return conversation["messages"] if conversation else []
    
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
        if conversation:
            conversation["messages"] = []
            conversation["updated_at"] = time.time()
            self._save_current_conversation()
            
            logger.info("[ChatHistoryManager] Cleared current conversation history")
            self.historyChanged.emit()
    
    def new_conversation(self) -> None:
        """Start a new conversation"""
        self._create_new_conversation()
        self.historyChanged.emit()
        logger.info("[ChatHistoryManager] Started new conversation")
    
    def get_conversation_list(self) -> List[Dict[str, Any]]:
        """
        Get list of available conversations
        
        Returns:
            List of conversation summary objects with id, date, etc.
        """
        # Return basic info about each conversation for UI display
        result = []
        for conv in self._conversations:
            result.append({
                "id": conv["id"],
                "created_at": conv["created_at"],
                "updated_at": conv["updated_at"],
                "preview": self._get_conversation_preview(conv)
            })
        return sorted(result, key=lambda x: x["updated_at"], reverse=True)
    
    def _get_conversation_preview(self, conversation):
        """Get a short preview of the conversation"""
        if not conversation.get("messages"):
            return "Empty conversation"
            
        # Try to find a user message to use as preview
        for msg in conversation["messages"]:
            if msg["sender"] == "user" and msg["text"].strip():
                return msg["text"][:30] + "..." if len(msg["text"]) > 30 else msg["text"]
                
        # If no user message, use the first message
        first_msg = conversation["messages"][0]
        return first_msg["text"][:30] + "..." if len(first_msg["text"]) > 30 else first_msg["text"]
    
    def load_conversation(self, conversation_id) -> bool:
        """
        Load a specific conversation by ID
        
        Returns:
            True if successful, False otherwise
        """
        # Check if conversation exists in our list
        exists = False
        for conv in self._conversations:
            if conv["id"] == conversation_id:
                exists = True
                break
                
        if not exists:
            logger.error(f"[ChatHistoryManager] Conversation {conversation_id} not found")
            return False
            
        # Set as current and load its contents
        self._current_conversation_id = conversation_id
        self._load_conversation(conversation_id)
        self._save_index()
        
        self.historyChanged.emit()
        logger.info(f"[ChatHistoryManager] Loaded conversation {conversation_id}")
        return True
    
    def delete_conversation(self, conversation_id) -> bool:
        """
        Delete a conversation by ID
        
        Returns:
            True if successful, False otherwise
        """
        # Find the conversation in our list
        for i, conv in enumerate(self._conversations):
            if conv["id"] == conversation_id:
                # Remove from list
                self._conversations.pop(i)
                
                # Delete the file
                try:
                    conversation_file = self._history_dir / f"{conversation_id}.json"
                    if conversation_file.exists():
                        os.remove(conversation_file)
                except Exception as e:
                    logger.error(f"[ChatHistoryManager] Error deleting conversation file: {e}")
                
                # If it was the current conversation, create a new one
                if self._current_conversation_id == conversation_id:
                    self._create_new_conversation()
                
                # Save the updated index
                self._save_index()
                self.historyChanged.emit()
                logger.info(f"[ChatHistoryManager] Deleted conversation {conversation_id}")
                return True
                
        logger.error(f"[ChatHistoryManager] Conversation {conversation_id} not found for deletion")
        return False
    
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

# Singleton instance
_chat_history_manager = None

def get_chat_history_manager():
    """Get the singleton chat history manager instance"""
    global _chat_history_manager
    if _chat_history_manager is None:
        _chat_history_manager = ChatHistoryManager()
    return _chat_history_manager
