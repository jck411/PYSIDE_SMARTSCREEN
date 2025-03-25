# Frontend Logic Documentation

This directory contains the core logic components of the frontend application. Below is a detailed description of each module and its purpose.

## Core Modules

### audio_manager.py
- Manages audio processing and playback functionality
- Provides `QueueAudioDevice` class for handling PCM audio data with QAudioSink
- Handles audio streaming, buffering, and playback control
- Manages audio state changes and cleanup

### service_manager.py
- Manages service-level operations and API endpoints
- Handles stopping message generation and other server-side services
- Provides methods for stopping audio and generation services
- Manages communication with backend services

### speech_manager.py
- Manages speech recognition and synthesis states
- Handles STT (Speech-to-Text) functionality using Deepgram
- Controls STT state changes and text processing
- Manages pausing/resuming STT during TTS playback

### task_manager.py
- Manages asynchronous tasks and provides utilities for task execution
- Handles creation, tracking, and cancellation of named tasks
- Provides methods for scheduling coroutines
- Manages cleanup of running tasks

### tts_controller.py
- Manages Text-to-Speech functionality
- Handles TTS state management and server interactions
- Controls TTS toggling and playback
- Manages TTS state restoration and cleanup

### websocket_client.py
- Manages WebSocket connection and message handling
- Handles real-time communication with the backend server
- Processes incoming messages and audio data
- Manages connection state and reconnection logic

## Chat Components

### chat/core/chat_controller.py
- Main controller coordinating all chat components
- Manages interaction between different modules
- Handles message processing and audio handling
- Controls STT/TTS states and wake word detection

### chat/core/chatlogic.py
- Adapter class maintaining backward compatibility
- Delegates functionality to modular components
- Provides interface for QML frontend
- Manages signal connections between components

### chat/handlers/message_handler.py
- Manages chat message processing and history
- Handles message streaming and chunked responses
- Maintains chat history and message state
- Manages interrupted responses and continuity

## Voice Components

### voice/wake_word_handler.py
- Handles wake word detection using Azure Cognitive Services
- Manages "hey computer" and "stop there" wake words
- Controls wake word listening states
- Handles callbacks for wake word detection

## Directory Structure
```
frontend/logic/
├── Core Modules
│   ├── audio_manager.py
│   ├── service_manager.py
│   ├── speech_manager.py
│   ├── task_manager.py
│   ├── tts_controller.py
│   └── websocket_client.py
├── chat/
│   ├── core/
│   │   ├── chat_controller.py
│   │   └── chatlogic.py
│   └── handlers/
│       └── message_handler.py
└── voice/
    └── wake_word_handler.py
```

This modular architecture allows for clear separation of concerns and maintainable code structure. Each module handles specific functionality while working together to provide a complete chat and voice interaction system.
