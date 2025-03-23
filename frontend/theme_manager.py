#!/usr/bin/env python3
from PySide6.QtCore import QObject, Signal, Property, Slot
from PySide6.QtGui import QColor
from frontend.style import DARK_COLORS, LIGHT_COLORS
from frontend.config import logger
import json
import os

class ThemeManager(QObject):
    themeChanged = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_dark_mode = True
        self._colors = DARK_COLORS.copy()
        self._load_theme_preferences()
        
        # QML color properties
        self._background_color = QColor(self._colors["background"])
        self._user_bubble_color = QColor(self._colors["user_bubble"])
        self._assistant_bubble_color = QColor(self._colors["assistant_bubble"])
        self._text_primary_color = QColor(self._colors["text_primary"])
        self._text_secondary_color = QColor(self._colors["text_secondary"])
        self._button_primary_color = QColor(self._colors["button_primary"])
        self._button_hover_color = QColor(self._colors["button_hover"])
        self._button_pressed_color = QColor(self._colors["button_pressed"])
        self._input_background_color = QColor(self._colors["input_background"])
        self._input_border_color = QColor(self._colors["input_border"])
    
    def _load_theme_preferences(self):
        """Load theme preferences from file if it exists"""
        try:
            config_path = os.path.expanduser("~/.smartscreen_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    if 'is_dark_mode' in config:
                        self._is_dark_mode = config['is_dark_mode']
                        self._colors = DARK_COLORS if self._is_dark_mode else LIGHT_COLORS
                        logger.info(f"Loaded theme preference: {'dark' if self._is_dark_mode else 'light'} mode")
        except Exception as e:
            logger.error(f"Error loading theme preferences: {e}")
    
    def _save_theme_preferences(self):
        """Save theme preferences to file"""
        try:
            config_path = os.path.expanduser("~/.smartscreen_config.json")
            config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
            
            config['is_dark_mode'] = self._is_dark_mode
            
            with open(config_path, 'w') as f:
                json.dump(config, f)
            
            logger.info(f"Saved theme preference: {'dark' if self._is_dark_mode else 'light'} mode")
        except Exception as e:
            logger.error(f"Error saving theme preferences: {e}")
    
    def _get_is_dark_mode(self):
        return self._is_dark_mode
    
    def _set_is_dark_mode(self, value):
        if self._is_dark_mode != value:
            self._is_dark_mode = value
            self._colors = DARK_COLORS if value else LIGHT_COLORS
            self._save_theme_preferences()
            
            # Update all QML colors
            self._background_color = QColor(self._colors["background"])
            self._user_bubble_color = QColor(self._colors["user_bubble"])
            self._assistant_bubble_color = QColor(self._colors["assistant_bubble"])
            self._text_primary_color = QColor(self._colors["text_primary"])
            self._text_secondary_color = QColor(self._colors["text_secondary"])
            self._button_primary_color = QColor(self._colors["button_primary"])
            self._button_hover_color = QColor(self._colors["button_hover"])
            self._button_pressed_color = QColor(self._colors["button_pressed"])
            self._input_background_color = QColor(self._colors["input_background"])
            self._input_border_color = QColor(self._colors["input_border"])
            
            self.themeChanged.emit()
            logger.info(f"Theme changed to {'dark' if value else 'light'} mode")
    
    # Define properties for direct QML use
    def _get_background_color(self):
        return self._background_color
    
    def _get_user_bubble_color(self):
        return self._user_bubble_color
    
    def _get_assistant_bubble_color(self):
        return self._assistant_bubble_color
    
    def _get_text_primary_color(self):
        return self._text_primary_color
    
    def _get_text_secondary_color(self):
        return self._text_secondary_color
    
    def _get_button_primary_color(self):
        return self._button_primary_color
    
    def _get_button_hover_color(self):
        return self._button_hover_color
    
    def _get_button_pressed_color(self):
        return self._button_pressed_color
    
    def _get_input_background_color(self):
        return self._input_background_color
    
    def _get_input_border_color(self):
        return self._input_border_color
    
    @Slot()
    def toggle_theme(self):
        self.is_dark_mode = not self._is_dark_mode
    
    # Define the properties
    is_dark_mode = Property(bool, _get_is_dark_mode, _set_is_dark_mode, notify=themeChanged)
    
    # QML color properties
    background_color = Property(QColor, _get_background_color, notify=themeChanged)
    user_bubble_color = Property(QColor, _get_user_bubble_color, notify=themeChanged)
    assistant_bubble_color = Property(QColor, _get_assistant_bubble_color, notify=themeChanged)
    text_primary_color = Property(QColor, _get_text_primary_color, notify=themeChanged)
    text_secondary_color = Property(QColor, _get_text_secondary_color, notify=themeChanged)
    button_primary_color = Property(QColor, _get_button_primary_color, notify=themeChanged)
    button_hover_color = Property(QColor, _get_button_hover_color, notify=themeChanged)
    button_pressed_color = Property(QColor, _get_button_pressed_color, notify=themeChanged)
    input_background_color = Property(QColor, _get_input_background_color, notify=themeChanged)
    input_border_color = Property(QColor, _get_input_border_color, notify=themeChanged)
