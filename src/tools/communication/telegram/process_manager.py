"""
Process Manager Module

This module provides process management utilities for the Telegram bot.
"""

import os
import psutil
import functools
import logging
from typing import List
import signal

logger = logging.getLogger(__name__)

def ensure_single_instance(func):
    """Decorator to ensure only one instance of the bot is running.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function that checks for other running instances
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        current_process = psutil.Process()
        current_pid = current_process.pid
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if (proc.pid != current_pid and 
                    proc.info['name'] == current_process.name() and 
                    proc.info['cmdline'] == current_process.cmdline()):
                    logger.warning(f"Another instance is already running (PID: {proc.pid})")
                    return
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return await func(*args, **kwargs)
    
    return wrapper

def get_bot_processes() -> List[psutil.Process]:
    """Find all running Python processes that match our Telegram bot pattern"""
    bot_processes = []
    current_pid = os.getpid()
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Skip the current process
            if proc.pid == current_pid:
                continue
                
            cmdline = proc.info['cmdline']
            if not cmdline:
                continue
                
            # Look specifically for our telegram bot module
            if ('python' in proc.info['name'].lower() and 
                any('src.tools.communication.telegram.bot' in str(cmd) for cmd in cmdline)):
                bot_processes.append(proc)
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return bot_processes

def kill_existing_bots() -> bool:
    """Kill any existing Telegram bot processes
    
    Returns:
        bool: True if any processes were killed, False otherwise
    """
    killed = False
    for proc in get_bot_processes():
        try:
            # Get process details for logging
            pid = proc.pid
            cmdline = ' '.join(proc.cmdline())
            
            # Kill the process
            os.kill(pid, signal.SIGTERM)
            logger.info(f"Terminated existing bot process {pid}: {cmdline}")
            killed = True
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, ProcessLookupError) as e:
            logger.warning(f"Failed to kill process {proc.pid}: {str(e)}")
            continue
            
    return killed
