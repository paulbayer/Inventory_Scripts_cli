#!/usr/bin/env python3
"""
Timing utilities for AWS Inventory CLI operations
"""

from time import time
from colorama import Fore, init

init()

class TimingContext:
    """
    Centralized timing context for operations
    Provides consistent timing functionality across all operations
    """
    
    def __init__(self, operation_name: str = None, enable_timing: bool = False):
        """
        Initialize timing context
        
        Args:
            operation_name: Name of the operation for timing messages
            enable_timing: Whether to display timing information
        """
        self.operation_name = operation_name or "Operation"
        self.enable_timing = enable_timing
        self.start_time = time()
        self.milestones = {}
        self.last_milestone = self.start_time
    
    def milestone(self, name: str, message: str = None):
        """
        Record a timing milestone
        
        Args:
            name: Unique name for this milestone
            message: Optional custom message to display
        """
        current_time = time()
        elapsed_from_start = current_time - self.start_time
        elapsed_from_last = current_time - self.last_milestone
        
        self.milestones[name] = {
            'time': current_time,
            'elapsed_from_start': elapsed_from_start,
            'elapsed_from_last': elapsed_from_last,
            'message': message
        }
        
        if self.enable_timing:
            if message:
                print(f"{Fore.GREEN}{message}: {elapsed_from_last:.3f} seconds{Fore.RESET}")
            else:
                print(f"{Fore.GREEN}{name}: {elapsed_from_last:.3f} seconds{Fore.RESET}")
        
        self.last_milestone = current_time
        return elapsed_from_start
    
    def total_elapsed(self):
        """Get total elapsed time since start"""
        return time() - self.start_time
    
    def get_milestone(self, name: str):
        """Get timing information for a specific milestone"""
        return self.milestones.get(name)
    
    def summary(self):
        """Print timing summary if timing is enabled"""
        if self.enable_timing:
            total_time = self.total_elapsed()
            print(f"{Fore.GREEN}{self.operation_name} completed in {total_time:.2f} seconds{Fore.RESET}")
            
            if self.milestones:
                print(f"{Fore.CYAN}Timing breakdown:{Fore.RESET}")
                for name, info in self.milestones.items():
                    print(f"  {name}: {info['elapsed_from_last']:.3f}s")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically show summary"""
        if self.enable_timing:
            self.summary()


def create_timing_context(args, operation_name: str = None):
    """
    Create a timing context based on CLI arguments
    
    Args:
        args: Parsed CLI arguments
        operation_name: Name of the operation
        
    Returns:
        TimingContext instance
    """
    enable_timing = getattr(args, 'Time', False)
    return TimingContext(operation_name=operation_name, enable_timing=enable_timing)