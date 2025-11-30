"""Utility functions for goodass CLI.

This module provides common utility functions used across the application,
including signal handling, cleanup, and SSH keypair generation.
"""

import os
import sys
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend

if __package__ is None or __package__ == "":
    import logger as app_logger
else:
    from . import logger as app_logger

# Global references for cleanup - these are set by cli.py
directory = None
stderr_file = None


def signal_handler(sig, frame):
    """Handle Ctrl+C signal for graceful exit.
    
    In debug mode (verbosity 3), also creates a core dump.
    """
    try:
        log = app_logger.get_logger()
        log.print_minimal("\nYou pressed Ctrl+C! Exiting gracefully...")
        log.log_program("signal", "Received SIGINT (Ctrl+C)")
        
        # Create core dump in debug mode
        if log.verbosity == app_logger.LogLevel.DEBUG:
            log.print_debug("Creating core dump (debug mode)...")
            log.create_core_dump(trigger="SIGINT (Ctrl+C) in debug mode")
    except Exception:
        print("\nYou pressed Ctrl+C! Exiting gracefully...")
    
    exit_gracefully()


def exit_gracefully():
    """Cleans up temporary files and exits the program."""
    global stderr_file, directory
    
    try:
        log = app_logger.get_logger()
        log.log_program("exit", "Program exiting gracefully")
        log.record_program_state("Program exit")
    except Exception:
        pass
    
    if stderr_file is not None:
        try:
            stderr_file.close()
        except Exception:
            pass
    if directory is not None and os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
            except Exception as e:
                try:
                    log = app_logger.get_logger()
                    log.log_error("cleanup", f"Failed to delete {file_path}", e)
                except Exception:
                    print(f"Failed to delete {file_path}. Reason: {e}")
        try:
            os.rmdir(directory)
        except OSError as e:
            try:
                log = app_logger.get_logger()
                log.log_error("cleanup", f"Failed to remove directory {directory}", e)
            except Exception:
                print(f"Failed to remove directory {directory}. Reason: {e}")
    sys.exit()


def generate_ssh_keypair(path):
    """Generate an SSH keypair at the specified path.
    
    Parameters:
    - path (str): Path where the private key will be saved.
                  The public key will be saved at {path}.pub
    
    Returns:
    - tuple: (private_key_str, public_key_str)
    """
    key = rsa.generate_private_key(
        backend=crypto_default_backend(), public_exponent=65537, key_size=2048
    )

    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption(),
    )

    public_key = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH, crypto_serialization.PublicFormat.OpenSSH
    )

    with open(path, "w") as f:
        f.write(private_key.decode())
    os.chmod(path, 0o600)
    with open(f"{path}.pub", "w") as f:
        f.write(f"{public_key.decode()} goodass_key@generated")
    return private_key.decode(), public_key.decode()
