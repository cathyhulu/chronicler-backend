"""
Logging utilities for chronicler_backend

Methods
-------
get_logger
"""

import logging
import logging.config
import os

from chronicler_backend.utils.constants import ROOT_DIR


def _setup_logging(
    default_path="logging_config.ini",
    default_level=logging.INFO,
    env_key="LOG_CFG",
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
    env_key : str, optional
        Environment variable that can override the config path, by default "LOG_CFG"
    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value

    # Use absolute path for repository root
    if not os.path.isabs(path):
        path = ROOT_DIR / path

    if os.path.exists(path):
        logging.config.fileConfig(path, disable_existing_loggers=False)
    else:
        logging.basicConfig(level=default_level)


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
    >>> from cvi.ds.utils.logging_setup import get_logger
    >>> logger = get_logger("my_logger")
    >>> logger.info("This is an info message.")
    >>> logger.error("This is an error message.")
    """
    return logging.getLogger(name)


# Initialize logging configuration when module is imported
# This happens only once when the module is first imported
_setup_logging()
