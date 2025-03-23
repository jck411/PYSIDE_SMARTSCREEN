#!/usr/bin/env python3
import sys
import asyncio
import signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType, qmlRegisterSingletonInstance
from PySide6.QtCore import QTimer
from frontend.config import logger
from frontend.logic.chatlogic import ChatLogic  # Updated import path
from frontend.theme_manager import ThemeManager

def main():
    app = QGuiApplication(sys.argv)
    
    # Create an asyncio loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Create theme manager instance
    theme_manager = ThemeManager()
    
    # Register ChatLogic so QML can instantiate it
    qmlRegisterType(ChatLogic, "MyScreens", 1, 0, "ChatLogic")
    
    # Register ThemeManager as a singleton
    qmlRegisterSingletonInstance(ThemeManager, "MyTheme", 1, 0, "ThemeManager", theme_manager)
    
    engine = QQmlApplicationEngine()
    
    # Load QML from the correct relative path (from project root)
    engine.load("frontend/qml/MainWindow.qml")
    
    if not engine.rootObjects():
        logger.error("Failed to load QML. Exiting.")
        sys.exit(-1)
        
    # Make sure the root window is visible
    root_objects = engine.rootObjects()
    if root_objects:
        logger.info(f"Number of root objects loaded: {len(root_objects)}")
        main_window = root_objects[0]
        main_window.setVisible(True)
        logger.info(f"Main window size: {main_window.width()}x{main_window.height()}")
    
    # Set up a timer to process asyncio events
    timer = QTimer()
    timer.setInterval(10)  # 10ms
    
    # Process asyncio events on timer tick
    def process_asyncio_events():
        loop.call_soon(loop.stop)
        loop.run_forever()
    
    timer.timeout.connect(process_asyncio_events)
    timer.start()
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Signal received => shutting down.")
        app.quit()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start the Qt event loop
    exit_code = app.exec()
    
    # Cleanup
    chat_logic = None
    for obj in engine.rootObjects():
        chat_logic = obj.findChild(ChatLogic)
        if chat_logic:
            chat_logic.cleanup()
            break
    
    loop.close()
    logger.info("Application closed.")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
