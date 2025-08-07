# /department_of_market_intelligence/utils/logger.py
"""Centralized logging configuration for the DOMI workflow."""

import logging
import sys
import re
from .. import config

def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    if config.VERBOSE_LOGGING:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        
    return logger

class OutputFilter:
    """A stream wrapper to filter out unwanted log messages."""
    def __init__(self, stream):
        self.stream = stream
        # Compile a single regex for efficiency
        suppress_patterns = [
            "auth_config or auth_config.auth_scheme is missing",
            "Will skip authentication.Using FunctionTool",
            "Generating tools list",
            r"\[EXPERIMENTAL\] BaseAuthenticatedTool",
            "UserWarning",
            "Loading server.ts",
            "Setting up request handlers",
            r"\[desktop-commander\] Initialized",
            "Loading configuration",
            "Configuration loaded successfully",
            "Connecting server",
            "Server connected successfully",
            "stdio_client",
            "cancel scope",
            "GeneratorExit",
            "BaseExceptionGroup",
            r"RuntimeError: Attempted to exit cancel scope"
        ]
        self.suppress_regex = re.compile('|'.join(suppress_patterns))

    def write(self, text):
        if not self.suppress_regex.search(text):
            self.stream.write(text)

    def flush(self):
        self.stream.flush()

    def __getattr__(self, name):
        return getattr(self.stream, name)


def apply_output_filtering():
    """Apply the output filter to stdout and stderr if not in verbose mode."""
    if not config.VERBOSE_LOGGING:
        sys.stdout = OutputFilter(sys.stdout)
        sys.stderr = OutputFilter(sys.stderr)