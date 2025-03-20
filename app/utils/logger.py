# app/utils/logger.py
import logging

# Set up detailed logging
def setup_logger():
    logger = logging.getLogger("chat-app")
    logger.setLevel(logging.DEBUG)
    
    # Create console handler for logging to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    # Create formatter to format the log messages
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Add the handler to the logger
    logger.addHandler(console_handler)
    
    return logger

# Initialize logger
logger = setup_logger()
