"""
Logging utilities for chronicler_backend

Methods
-------
get_logger
"""

import logging
import logging.config
import os

from dotenv import load_dotenv

from chronicler_backend.utils.constants import ROOT_DIR


def _setup_logging(
    default_path="logging_config.ini",
    default_level=logging.INFO,
    env_key_path="LOG_CFG",
    env_key_level="LOG_LEVEL",
):
    """Setup logging configuration from an INI file.

    This function is automatically called when this module is imported.
    DO NOT call this function directly in your code unless you want to
    override the default logging configuration.

    Parameters
    ----------
    default_path : str, optional
        Path to the logging configuration file, by default "logging_config.ini"
    default_level : int, optional
        Default logging level if config file is not found, by default logging.INFO
    env_key_path : str, optional
        Environment variable that can override the config path, by default "LOG_CFG"
    env_key_level : str, optional
        Environment variable that can override the logging level, by default "LOG_LEVEL"
    """
    # Get config path from environment variable if available
    path = os.getenv(env_key_path, default_path)

    # Use absolute path for repository root
    if not os.path.isabs(path):
        path = ROOT_DIR / path

    # Get log level from environment variable if available
    log_level_name = os.getenv(env_key_level)
    if log_level_name:
        try:
            log_level = getattr(logging, log_level_name.upper().strip())
        except AttributeError:
            # Fall back to default if invalid level name
            log_level = default_level
            print(f"WARNING: Invalid log level '{log_level_name}', using default.")
    else:
        log_level = default_level

    # Load config file if exists
    if os.path.exists(path):
        logging.config.fileConfig(path, disable_existing_loggers=False)

        # Override with environment level if specified
        if log_level_name:
            # Override the root logger level
            root_logger = logging.getLogger()
            root_logger.setLevel(log_level)

            # Update the level for all handlers to maintain consistency
            for handler in root_logger.handlers:
                handler.setLevel(log_level)
    else:
        # Basic config if no config file
        logging.basicConfig(
            level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.

    This is the primary function you should use to obtain a logger in your module.
    Typically, you should pass `__name__` as the parameter to get a logger that
    shows your module's name in the logs.

    Parameters
    ----------
    name : str
        Name of the logger

    Returns
    -------
    logging.Logger
        Logger instance

    Examples
    --------
    >>> from chronicler_backend.utils.logging import get_logger
    >>> logger = get_logger("my_logger")
    >>> logger.info("This is an info message.")
    >>> logger.error("This is an error message.")
    """
    return logging.getLogger(name)


# Initialize logging configuration when module is imported
# This happens only once when the module is first imported
load_dotenv(str(ROOT_DIR / ".env"))
_setup_logging()
