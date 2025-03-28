#!/usr/bin/env python3
import json
import os
import logging
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Property

from frontend.config import logger

class SettingsManager(QObject):
    """
    Manages application settings with persistent storage.
    """
    settingsChanged = Signal(str, object)  # key, value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = {}
        self._settings_file = Path.home() / ".smartscreen_settings.json"
        self._load_settings()
        
        # Initialize chat history if not present
        if "chat" not in self._settings:
            self._settings["chat"] = {
                "messages": []
            }
            self._save_settings()
        
    def _load_settings(self):
        """Load settings from file"""
        try:
            if self._settings_file.exists():
                with open(self._settings_file, 'r') as f:
                    self._settings = json.load(f)
                logger.info(f"[SettingsManager] Loaded settings from {self._settings_file}")
            else:
                logger.info(f"[SettingsManager] Settings file not found. Using defaults.")
                self._settings = {
                    "stt": {
                        "auto_send": False,
                    },
                    "tts": {
                        "enabled": True,
                    },
                    "ui": {
                        "theme": "dark",
                    }
                }
                self._save_settings()
        except Exception as e:
            logger.error(f"[SettingsManager] Error loading settings: {e}")
            self._settings = {
                "stt": {
                    "auto_send": False,
                },
                "tts": {
                    "enabled": True,
                },
                "ui": {
                    "theme": "dark",
                }
            }
    
    def _save_settings(self):
        """Save settings to file"""
        try:
            with open(self._settings_file, 'w') as f:
                json.dump(self._settings, f, indent=4)
            logger.info(f"[SettingsManager] Saved settings to {self._settings_file}")
        except Exception as e:
            logger.error(f"[SettingsManager] Error saving settings: {e}")
    
    def get_setting(self, section, key, default=None):
        """Get a setting value"""
        try:
            return self._settings.get(section, {}).get(key, default)
        except Exception as e:
            logger.error(f"[SettingsManager] Error getting setting {section}.{key}: {e}")
            return default
    
    def set_setting(self, section, key, value):
        """Set a setting value"""
        try:
            if section not in self._settings:
                self._settings[section] = {}
            
            if self._settings.get(section, {}).get(key) != value:
                self._settings[section][key] = value
                self._save_settings()
                self.settingsChanged.emit(f"{section}.{key}", value)
                logger.info(f"[SettingsManager] Updated setting {section}.{key} = {value}")
        except Exception as e:
            logger.error(f"[SettingsManager] Error setting {section}.{key} = {value}: {e}")
    
    def get_auto_send(self):
        """Get the auto-send setting"""
        return self.get_setting("stt", "auto_send", False)
    
    def set_auto_send(self, enabled):
        """Set the auto-send setting"""
        self.set_setting("stt", "auto_send", enabled)
    
    def get_tts_enabled(self):
        """Get the TTS enabled setting"""
        return self.get_setting("tts", "enabled", True)
    
    def set_tts_enabled(self, enabled):
        """Set the TTS enabled setting"""
        self.set_setting("tts", "enabled", enabled)
    
    def get_theme(self):
        """Get the UI theme setting"""
        return self.get_setting("ui", "theme", "dark")
    
    def set_theme(self, theme):
        """Set the UI theme setting"""
        self.set_setting("ui", "theme", theme)
        
    def get_chat_messages(self):
        """Get the chat message history"""
        return self.get_setting("chat", "messages", [])
    
    def set_chat_messages(self, messages):
        """Set the chat message history"""
        self.set_setting("chat", "messages", messages)
    
    def add_chat_message(self, message):
        """Add a message to the chat history"""
        messages = self.get_chat_messages()
        
        # Check for duplicates - if this is an assistant message that's very similar to the last one, replace it
        if messages and message["sender"] == "assistant" and len(messages) > 0:
            # Check the last few messages for duplicates or similar messages
            for i in range(len(messages) - 1, max(len(messages) - 4, -1), -1):
                existing_msg = messages[i]
                if existing_msg["sender"] == "assistant":
                    # If the new message starts with the old one or is very similar, replace it
                    if (message["text"].startswith(existing_msg["text"][:10]) or 
                        existing_msg["text"].startswith(message["text"][:10]) or
                        self._similarity_score(message["text"], existing_msg["text"]) > 0.7):
                        logger.info(f"[SettingsManager] Replacing similar assistant message at index {i}")
                        messages[i] = message
                        
                        # Remove any other assistant messages that might be duplicates
                        # (only keep the most recent user message and this assistant message)
                        last_user_index = -1
                        for j in range(len(messages) - 1, i, -1):
                            if messages[j]["sender"] == "user":
                                last_user_index = j
                                break
                        
                        if last_user_index > i:
                            # Keep the user message and remove everything between it and this assistant message
                            new_messages = messages[:i+1] + [messages[last_user_index]] + messages[last_user_index+1:]
                            messages = new_messages
                        else:
                            # Just remove any assistant messages after this one
                            new_messages = []
                            for j in range(len(messages)):
                                if j > i and messages[j]["sender"] == "assistant":
                                    continue
                                new_messages.append(messages[j])
                            messages = new_messages
                        
                        self.set_chat_messages(messages)
                        return
        
        # Otherwise, append as normal
        messages.append(message)
        self.set_chat_messages(messages)
        
    def _similarity_score(self, text1, text2):
        """Calculate a simple similarity score between two texts"""
        # Simple implementation - just check if one contains the other
        if text1 in text2 or text2 in text1:
            return 0.9
        
        # Check for common words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        common_words = words1.intersection(words2)
        
        if not words1 or not words2:
            return 0.0
            
        return len(common_words) / max(len(words1), len(words2))
        
    def clear_chat_messages(self):
        """Clear the chat message history"""
        self.set_chat_messages([])

# Create singleton instance
_settings_manager = None

def get_settings_manager():
    """Get the singleton settings manager instance"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager
