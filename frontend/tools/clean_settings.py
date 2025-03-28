#!/usr/bin/env python3
"""
One-time utility to clean legacy structure from settings file.
"""
import json
import os
from pathlib import Path

def main():
    """Clean legacy chat structure from settings file"""
    settings_file = Path.home() / ".smartscreen_settings.json"
    
    if not settings_file.exists():
        print(f"Settings file {settings_file} not found.")
        return
    
    print(f"Cleaning settings file: {settings_file}")
    
    # Load settings
    with open(settings_file, 'r') as f:
        settings = json.load(f)
    
    # Remove legacy chat.messages if it exists
    if "chat" in settings and "messages" in settings["chat"]:
        print("Removing legacy chat.messages from settings")
        settings["chat"].pop("messages", None)
        
        # Save settings
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=4)
        
        print("Legacy chat structure removed from settings")
    else:
        print("No legacy chat structure found in settings")

if __name__ == "__main__":
    main() 