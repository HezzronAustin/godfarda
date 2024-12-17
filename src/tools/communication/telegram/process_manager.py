import psutil
import os
import logging
import signal
from typing import List

logger = logging.getLogger(__name__)

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

def ensure_single_instance():
    """Ensure only one instance of the bot is running"""
    if kill_existing_bots():
        logger.info("Killed existing bot processes")
    else:
        logger.info("No existing bot processes found")
