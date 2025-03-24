DARK_COLORS = {
    "background": "#1a1b26",
    "user_bubble": "#3b4261",
    "assistant_bubble": "transparent",
    "text_primary": "#a9b1d6",
    "text_secondary": "#565f89",
    "button_primary": "#7aa2f7",
    "button_hover": "#3d59a1",
    "button_pressed": "#2ac3de",
    "input_background": "#24283b",
    "input_border": "#414868"
}

LIGHT_COLORS = {
    "background": "#E8EEF5",
    "user_bubble": "#D0D7E1",
    "assistant_bubble": "#F7F9FB",
    "text_primary": "#3b4261",
    "text_secondary": "#65676B",
    "button_primary": "#0D8BD9",
    "button_hover": "#0A6CA8",
    "button_pressed": "#084E7A",
    "input_background": "#FFFFFF",
    "input_border": "#D3D7DC"
}

def generate_main_stylesheet(colors):
    return f"""
    QMainWindow {{
        background-color: {colors['background']};
        color: {colors['text_primary']};
    }}
    
    QWidget {{
        background-color: {colors['background']};
        color: {colors['text_primary']};
    }}
    
    QTextEdit {{
        background-color: {colors['input_background']};
        color: {colors['text_primary']};
        border: 1px solid {colors['input_border']};
        border-radius: 10px;
        padding: 10px;
    }}
    
    QPushButton {{
        background-color: {colors['button_primary']};
        color: white;
        border: none;
        border-radius: 10px;
        padding: 8px 16px;
        font-weight: bold;
    }}
    
    QPushButton:hover {{
        background-color: {colors['button_hover']};
    }}
    
    QPushButton:pressed {{
        background-color: {colors['button_pressed']};
    }}
    
    QPushButton#sttButton[isListening="true"] {{
        background-color: #0d8bd9;
    }}
    
    QPushButton#sttButton[isListening="false"] {{
        background-color: gray;
    }}
    
    QScrollArea {{
        border: none;
    }}
    """

def get_message_bubble_stylesheet(is_user, colors):
    if is_user:
        return f"""
        QFrame {{
            background-color: {colors['user_bubble']};
            border-radius: 15px;
            margin: 2px 8px 2px 40px;
            padding: 10px;
        }}
        QLabel {{
            background-color: transparent;
            color: {colors['text_primary']};
        }}
        """
    else:
        return f"""
        QFrame {{
            background-color: {colors['assistant_bubble']};
            border-radius: 15px;
            margin: 2px 40px 2px 8px;
            padding: 10px;
        }}
        QLabel {{
            background-color: transparent;
            color: {colors['text_primary']};
        }}
        """
