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
        
    # Legacy chat message methods removed - use ChatHistoryManager instead

# Create singleton instance
_settings_manager = None

def get_settings_manager():
    """Get the singleton settings manager instance"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager
