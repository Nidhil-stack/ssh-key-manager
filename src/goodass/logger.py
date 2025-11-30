"""Robust logging system for GOODASS CLI.

This module provides a comprehensive logging system with:
- 4 verbosity levels for console output (minimal, default, verbose, debug)
- 4 separate log files (server, program, error, core dump)
- Secure file signing with hash chain for integrity verification
- Human-readable and parseable log format
"""

import os
import sys
import logging
import hashlib
import datetime
import traceback
import atexit
from typing import Optional, TextIO
from enum import IntEnum

import platformdirs

if __package__ is None or __package__ == "":
    import gpgManager
else:
    from . import gpgManager


class LogLevel(IntEnum):
    """Verbosity levels for console output."""
    MINIMAL = 0   # Only essential prints, no tables
    DEFAULT = 1   # Normal output similar to current behavior
    VERBOSE = 2   # More detailed output with tables
    DEBUG = 3     # Full debug output for every process


class SecureLogger:
    """A secure logging system with multiple log files and integrity verification.
    
    This class provides:
    - Console output with configurable verbosity levels
    - Server log: All server-related activities
    - Program log: All program activities with integrity verification
    - Error log: Crashes and errors
    - Core dump: Triggered by crash or Ctrl+C in debug mode
    """
    
    _instance: Optional['SecureLogger'] = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure only one logger instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance to allow creating a new logger.
        
        This is useful for testing or when you need to reinitialize
        the logger with different settings.
        """
        if cls._instance is not None:
            # Try to cleanup before resetting
            try:
                cls._instance._cleanup()
            except Exception:
                pass
        cls._instance = None
    
    def __init__(self, config_dir: Optional[str] = None, verbosity: int = 1):
        """Initialize the secure logger.
        
        Parameters:
        - config_dir (str): Path to the configuration directory
        - verbosity (int): Verbosity level (0-3)
        """
        # Skip re-initialization for singleton
        if self._initialized:
            return
            
        self._initialized = True
        self.verbosity = LogLevel(min(max(verbosity, 0), 3))
        self.config_dir = config_dir or platformdirs.user_config_dir("goodass")
        self.logs_dir = os.path.join(self.config_dir, "logs")
        self._user_typing = False
        self._gpg_home: Optional[str] = None
        
        # Create logs directory if it doesn't exist
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Log file paths
        self.server_log_path = os.path.join(self.logs_dir, "server.log")
        self.program_log_path = os.path.join(self.logs_dir, "program.log")
        self.error_log_path = os.path.join(self.logs_dir, "error.log")
        self.coredump_path = os.path.join(self.logs_dir, "coredump.log")
        
        # Hash chain files for integrity verification
        self.program_hash_chain_path = os.path.join(self.logs_dir, "program_hashes.txt")
        self.config_hash_chain_path = os.path.join(self.logs_dir, "config_hashes.txt")
        
        # Setup file handlers
        self._setup_loggers()
        
        # Register cleanup on exit
        atexit.register(self._cleanup)
    
    def _setup_loggers(self):
        """Setup logging handlers for each log file."""
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-12s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-12s | %(pathname)s:%(lineno)d\n%(message)s\n',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Server logger
        self.server_logger = logging.getLogger('goodass.server')
        self.server_logger.setLevel(logging.DEBUG)
        server_handler = logging.FileHandler(self.server_log_path, mode='a')
        server_handler.setFormatter(detailed_formatter)
        self.server_logger.addHandler(server_handler)
        
        # Program logger
        self.program_logger = logging.getLogger('goodass.program')
        self.program_logger.setLevel(logging.DEBUG)
        program_handler = logging.FileHandler(self.program_log_path, mode='a')
        program_handler.setFormatter(detailed_formatter)
        self.program_logger.addHandler(program_handler)
        
        # Error logger
        self.error_logger = logging.getLogger('goodass.error')
        self.error_logger.setLevel(logging.DEBUG)
        error_handler = logging.FileHandler(self.error_log_path, mode='a')
        error_handler.setFormatter(error_formatter)
        self.error_logger.addHandler(error_handler)
        
        # Log session start
        session_start = f"{'='*60}\nSession started at {datetime.datetime.now().isoformat()}\n{'='*60}"
        self.program_logger.info(session_start)
        self.server_logger.info(session_start)
    
    def set_verbosity(self, level: int):
        """Set the verbosity level for console output.
        
        Parameters:
        - level (int): Verbosity level (0-3)
        """
        self.verbosity = LogLevel(min(max(level, 0), 3))
    
    def set_gpg_home(self, gpg_home: Optional[str]):
        """Set the GPG home directory for signing operations.
        
        Parameters:
        - gpg_home (str): Path to GPG home directory
        """
        self._gpg_home = gpg_home
    
    def set_user_typing(self, typing: bool):
        """Set whether the user is currently typing.
        
        When the user is typing, console output is suppressed in debug mode.
        
        Parameters:
        - typing (bool): Whether the user is typing
        """
        self._user_typing = typing
    
    def _should_print(self, min_level: LogLevel) -> bool:
        """Check if console output should be printed based on verbosity.
        
        Parameters:
        - min_level (LogLevel): Minimum verbosity level required
        
        Returns:
        - bool: Whether to print the message
        """
        if self._user_typing and self.verbosity == LogLevel.DEBUG:
            return False
        return self.verbosity >= min_level
    
    def _compute_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content.
        
        Parameters:
        - content (str): Content to hash
        
        Returns:
        - str: Hex digest of hash
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _append_hash_chain(self, hash_chain_path: str, file_path: str, 
                          description: str) -> str:
        """Append a hash entry to the hash chain file.
        
        Parameters:
        - hash_chain_path (str): Path to the hash chain file
        - file_path (str): Path to the file being hashed
        - description (str): Description of the operation
        
        Returns:
        - str: The computed hash
        """
        # Read current file content
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = ""
        
        # Compute hash
        file_hash = self._compute_hash(content)
        
        # Get previous hash chain entry hash for chaining
        previous_chain_hash = ""
        if os.path.exists(hash_chain_path):
            with open(hash_chain_path, 'r', encoding='utf-8') as f:
                chain_content = f.read()
                if chain_content.strip():
                    previous_chain_hash = self._compute_hash(chain_content)
        
        # Create human-readable entry
        timestamp = datetime.datetime.now().isoformat()
        entry = (
            f"--- Entry ---\n"
            f"Timestamp: {timestamp}\n"
            f"File: {os.path.basename(file_path)}\n"
            f"Description: {description}\n"
            f"File Hash (SHA-256): {file_hash}\n"
            f"Previous Chain Hash: {previous_chain_hash if previous_chain_hash else 'GENESIS'}\n"
            f"--- End Entry ---\n\n"
        )
        
        # Append to hash chain file
        with open(hash_chain_path, 'a', encoding='utf-8') as f:
            f.write(entry)
        
        return file_hash
    
    def sign_hash_chain(self, hash_chain_path: str) -> bool:
        """Sign the hash chain file with GPG.
        
        Creates a detached signature for the hash chain file.
        
        Parameters:
        - hash_chain_path (str): Path to the hash chain file
        
        Returns:
        - bool: True if signing succeeded
        """
        if not os.path.exists(hash_chain_path):
            return False
        
        try:
            # Get secret keys
            secret_keys = gpgManager.list_secret_keys(self._gpg_home)
            if not secret_keys:
                # No GPG keys available - not an error, just can't sign
                return False
            
            gpg = gpgManager.get_gpg(self._gpg_home)
            with open(hash_chain_path, 'rb') as f:
                data = f.read()
            
            signed = gpg.sign(data, detach=True, armor=True)
            
            if signed.data:
                sig_path = hash_chain_path + ".sig"
                with open(sig_path, 'wb') as f:
                    f.write(signed.data)
                return True
            # Signing failed but GPG didn't raise an exception
            return False
        except ImportError:
            # GPG module not available
            return False
        except (IOError, OSError) as e:
            # File operation errors - log but don't fail
            self.error_logger.warning(f"Could not sign hash chain: {e}")
            return False
        except Exception as e:
            # Unexpected errors - log for debugging
            self.error_logger.warning(f"GPG signing error: {type(e).__name__}: {e}")
            return False
    
    def record_config_signing(self, config_path: str):
        """Record when a config file is signed.
        
        Appends the hash of the config file to the config hash chain
        and signs the resulting file.
        
        Parameters:
        - config_path (str): Path to the signed config file
        """
        self._append_hash_chain(
            self.config_hash_chain_path,
            config_path,
            "Config file signed"
        )
        self.sign_hash_chain(self.config_hash_chain_path)
        self.log_program("config_signing", f"Config signed: {config_path}")
    
    def record_program_state(self, description: str):
        """Record the current program log state in the hash chain.
        
        This provides integrity verification for the program log.
        
        Parameters:
        - description (str): Description of the state
        """
        self._append_hash_chain(
            self.program_hash_chain_path,
            self.program_log_path,
            description
        )
        self.sign_hash_chain(self.program_hash_chain_path)
    
    # Console output methods
    
    def print_minimal(self, message: str, end: str = '\n'):
        """Print message at minimal verbosity level (always shown).
        
        Parameters:
        - message (str): Message to print
        - end (str): End character
        """
        if self._should_print(LogLevel.MINIMAL):
            print(message, end=end)
    
    def print_default(self, message: str, end: str = '\n'):
        """Print message at default verbosity level (1+).
        
        Parameters:
        - message (str): Message to print
        - end (str): End character
        """
        if self._should_print(LogLevel.DEFAULT):
            print(message, end=end)
    
    def print_verbose(self, message: str, end: str = '\n'):
        """Print message at verbose level (2+).
        
        Parameters:
        - message (str): Message to print
        - end (str): End character
        """
        if self._should_print(LogLevel.VERBOSE):
            print(message, end=end)
    
    def print_debug(self, message: str, end: str = '\n'):
        """Print message at debug level (3).
        
        Parameters:
        - message (str): Message to print
        - end (str): End character
        """
        if self._should_print(LogLevel.DEBUG):
            print(f"[DEBUG] {message}", end=end)
    
    def print_table(self, table, min_level: LogLevel = LogLevel.DEFAULT):
        """Print a prettytable at the specified minimum verbosity level.
        
        At MINIMAL level, tables are not shown.
        
        Parameters:
        - table: PrettyTable object to print
        - min_level (LogLevel): Minimum verbosity level to show the table
        """
        if self.verbosity == LogLevel.MINIMAL:
            return
        if self._should_print(min_level):
            print(table)
    
    # File logging methods
    
    def log_server(self, operation: str, message: str, level: str = 'INFO'):
        """Log a server-related activity.
        
        Parameters:
        - operation (str): The operation being performed
        - message (str): Detailed message
        - level (str): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        log_method = getattr(self.server_logger, level.lower(), self.server_logger.info)
        log_method(f"[{operation}] {message}")
    
    def log_program(self, operation: str, message: str, level: str = 'INFO'):
        """Log a program activity.
        
        Parameters:
        - operation (str): The operation being performed
        - message (str): Detailed message
        - level (str): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        log_method = getattr(self.program_logger, level.lower(), self.program_logger.info)
        log_method(f"[{operation}] {message}")
    
    def log_error(self, error_type: str, message: str, 
                  exception: Optional[Exception] = None):
        """Log an error or crash.
        
        Parameters:
        - error_type (str): Type of error
        - message (str): Error message
        - exception (Exception): Optional exception object
        """
        error_msg = f"[{error_type}] {message}"
        if exception:
            error_msg += f"\nException: {type(exception).__name__}: {str(exception)}"
            error_msg += f"\nTraceback:\n{traceback.format_exc()}"
        
        self.error_logger.error(error_msg)
        self.program_logger.error(f"[ERROR] {error_type}: {message}")
        
        # Print to console in debug mode
        if self.verbosity == LogLevel.DEBUG:
            print(f"[ERROR] {error_type}: {message}")
            if exception:
                traceback.print_exc()
    
    def create_core_dump(self, trigger: str = "unknown"):
        """Create a core dump file with system state.
        
        This is triggered by:
        - Program crash
        - Ctrl+C in debug mode
        
        Parameters:
        - trigger (str): What triggered the core dump
        """
        timestamp = datetime.datetime.now().isoformat()
        
        dump_content = [
            f"{'='*60}",
            f"GOODASS Core Dump",
            f"{'='*60}",
            f"Timestamp: {timestamp}",
            f"Trigger: {trigger}",
            f"Verbosity Level: {self.verbosity.name} ({self.verbosity})",
            f"Config Directory: {self.config_dir}",
            f"Python Version: {sys.version}",
            f"Platform: {sys.platform}",
            "",
            "--- Environment Variables ---",
        ]
        
        # Add safe environment variables (filter out sensitive ones)
        safe_env_vars = ['PATH', 'HOME', 'USER', 'SHELL', 'PWD', 'LANG', 'TERM']
        for var in safe_env_vars:
            value = os.environ.get(var, 'Not set')
            dump_content.append(f"{var}: {value}")
        
        dump_content.extend([
            "",
            "--- Recent Traceback (if any) ---",
            traceback.format_exc() if sys.exc_info()[0] else "No active exception",
            "",
            "--- Log File Sizes ---",
            f"Server log: {self._get_file_size(self.server_log_path)}",
            f"Program log: {self._get_file_size(self.program_log_path)}",
            f"Error log: {self._get_file_size(self.error_log_path)}",
            "",
            f"{'='*60}",
            "End of Core Dump",
            f"{'='*60}",
        ])
        
        # Write core dump
        with open(self.coredump_path, 'a', encoding='utf-8') as f:
            f.write('\n'.join(dump_content))
            f.write('\n\n')
        
        self.log_program("core_dump", f"Core dump created: trigger={trigger}")
    
    def _get_file_size(self, path: str) -> str:
        """Get human-readable file size.
        
        Parameters:
        - path (str): Path to file
        
        Returns:
        - str: Human-readable file size
        """
        if not os.path.exists(path):
            return "N/A"
        size = os.path.getsize(path)
        if size < 1024:
            return f"{int(size)} B"
        for unit in ['KB', 'MB', 'GB']:
            size /= 1024
            if size < 1024:
                return f"{size:.1f} {unit}"
        return f"{size:.1f} TB"
    
    def _cleanup(self):
        """Cleanup handler called on program exit."""
        try:
            # Only record state if the logs directory still exists
            if os.path.exists(self.logs_dir):
                # Record final program state
                self.record_program_state("Session ended normally")
                
                # Log session end
                session_end = f"{'='*60}\nSession ended at {datetime.datetime.now().isoformat()}\n{'='*60}"
                self.program_logger.info(session_end)
                self.server_logger.info(session_end)
        except Exception:
            pass  # Don't fail during cleanup
        
        # Close all handlers
        try:
            for logger_obj in [self.server_logger, self.program_logger, self.error_logger]:
                for handler in logger_obj.handlers[:]:
                    try:
                        handler.close()
                        logger_obj.removeHandler(handler)
                    except Exception:
                        pass
        except Exception:
            pass


# Global logger instance
_logger: Optional[SecureLogger] = None


def get_logger() -> SecureLogger:
    """Get the global logger instance.
    
    Returns:
    - SecureLogger: The global logger instance
    """
    global _logger
    if _logger is None:
        _logger = SecureLogger()
    return _logger


def init_logger(config_dir: Optional[str] = None, verbosity: int = 1) -> SecureLogger:
    """Initialize the global logger.
    
    Parameters:
    - config_dir (str): Path to the configuration directory
    - verbosity (int): Verbosity level (0-3)
    
    Returns:
    - SecureLogger: The initialized logger instance
    """
    global _logger
    # Force new instance by using class method
    SecureLogger.reset_instance()
    _logger = SecureLogger(config_dir, verbosity)
    return _logger


# Convenience functions for direct usage

def log_server(operation: str, message: str, level: str = 'INFO'):
    """Log a server activity."""
    get_logger().log_server(operation, message, level)


def log_program(operation: str, message: str, level: str = 'INFO'):
    """Log a program activity."""
    get_logger().log_program(operation, message, level)


def log_error(error_type: str, message: str, exception: Optional[Exception] = None):
    """Log an error."""
    get_logger().log_error(error_type, message, exception)


def print_minimal(message: str, end: str = '\n'):
    """Print at minimal verbosity."""
    get_logger().print_minimal(message, end)


def print_default(message: str, end: str = '\n'):
    """Print at default verbosity."""
    get_logger().print_default(message, end)


def print_verbose(message: str, end: str = '\n'):
    """Print at verbose verbosity."""
    get_logger().print_verbose(message, end)


def print_debug(message: str, end: str = '\n'):
    """Print at debug verbosity."""
    get_logger().print_debug(message, end)


def print_table(table, min_level: LogLevel = LogLevel.DEFAULT):
    """Print a table at specified verbosity level."""
    get_logger().print_table(table, min_level)


def create_core_dump(trigger: str = "unknown"):
    """Create a core dump."""
    get_logger().create_core_dump(trigger)


def record_config_signing(config_path: str):
    """Record config file signing."""
    get_logger().record_config_signing(config_path)
