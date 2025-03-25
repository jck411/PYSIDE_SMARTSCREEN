#!/usr/bin/env python
# coding: utf-8

"""
Script to convert MP3 files to PCM format compatible with the frontend audio system.
Converts files from /frontend/wakeword/ to 16-bit, mono, 24000Hz PCM 
and saves them in /frontend/wakeword/sounds/
"""

import os
import sys
import glob
import wave
import array
import io
from pathlib import Path
import struct
from pydub import AudioSegment

# Define source and target directories
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = SCRIPT_DIR
TARGET_DIR = os.path.join(SCRIPT_DIR, "sounds")

# Ensure target directory exists
os.makedirs(TARGET_DIR, exist_ok=True)

def convert_mp3_to_pcm(source_file, target_file):
    """
    Convert an MP3 file to 16-bit, mono, 24000Hz PCM format using pydub
    
    Args:
        source_file: Path to the source MP3 file
        target_file: Path where the PCM data will be saved
    
    Returns:
        bool: True if conversion was successful, False otherwise
    """
    try:
        print(f"Converting {os.path.basename(source_file)} to PCM format...")
        
        # Load the MP3 file
        audio = AudioSegment.from_mp3(source_file)
        
        # Get original duration
        original_duration = len(audio)
        
        # Convert to the required format
        audio = audio.set_frame_rate(24000)  # 24kHz sample rate
        audio = audio.set_channels(1)       # Mono
        audio = audio.set_sample_width(2)   # 16-bit
        
        # Add 100ms of silence to the end to prevent cutoff
        silence = AudioSegment.silent(duration=100, frame_rate=24000)
        audio = audio + silence
        
        # Print the format and duration information
        print(f"Converted format: {audio.channels} channels, {audio.sample_width*8}-bit, {audio.frame_rate}Hz")
        print(f"Original duration: {original_duration}ms, New duration with padding: {len(audio)}ms")
        
        # Get the raw PCM data
        pcm_data = audio.raw_data
        
        # Write the PCM data to the target file
        with open(target_file, 'wb') as f:
            f.write(pcm_data)
        
        print(f"Successfully converted to PCM: {os.path.basename(target_file)} ({len(pcm_data)} bytes)")
        return True
        
    except Exception as e:
        print(f"Error converting {source_file}: {e}")
        return False

def main():
    # Find all MP3 files in the source directory
    mp3_files = glob.glob(os.path.join(SOURCE_DIR, "*.mp3"))
    
    if not mp3_files:
        print(f"No MP3 files found in {SOURCE_DIR}")
        return
    
    print(f"Found {len(mp3_files)} MP3 file(s) to convert")
    
    # Process each MP3 file
    for mp3_file in mp3_files:
        base_name = os.path.basename(mp3_file)
        name_without_ext = os.path.splitext(base_name)[0]
        target_file = os.path.join(TARGET_DIR, f"{name_without_ext}.pcm")
        
        # Convert the file
        success = convert_mp3_to_pcm(mp3_file, target_file)
        
        if success:
            print(f"Converted {base_name} to {os.path.basename(target_file)}")
        else:
            print(f"Failed to convert {base_name}")

if __name__ == "__main__":
    main()