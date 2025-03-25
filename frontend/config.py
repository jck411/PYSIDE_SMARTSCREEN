#!/usr/bin/env python3
import logging
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
WEBSOCKET_PATH = "/ws/chat"
HTTP_BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
def setup_logger(name=__name__, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # Clear any existing handlers to prevent duplicate logs
    logger.handlers = []
    # Only add a handler if none exists
    if not logger.handlers:
        ch = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False
    return logger
logger = setup_logger(level=logging.INFO)
