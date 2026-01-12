"""Output handling - I/O layer for user-facing messages.

This module contains the OutputHandler class which is the ONLY place
that knows about output formatting (emoji, colors, etc).

All output goes through OutputHandler to keep the core logic pure.
"""

from typing import List


class OutputHandler:
    """Handles all output formatting and display.
    
    This is the ONLY place that knows about emoji and formatting.
    Core logic should record warnings/errors on SessionContext,
    then display them here after commit.
    """
    
    def __init__(self, quiet: bool = False):
        """Initialize output handler.
        
        Args:
            quiet: If True, suppress non-essential output.
        """
        self.quiet = quiet
    
    def display_warnings(self, warnings: List[str]) -> None:
        """Display collected warnings after commit.
        
        Args:
            warnings: List of warning messages.
        """
        if self.quiet:
            return
        for w in warnings:
            print(f"⚠️  Warning: {w}")
    
    def display_errors(self, errors: List[str]) -> None:
        """Display collected errors.
        
        Args:
            errors: List of error messages.
        """
        for e in errors:
            print(f"❌ Error: {e}")
    
    def error(self, message: str) -> None:
        """Display a single error message.
        
        Args:
            message: Error message to display.
        """
        print(f"❌ {message}")
    
    def warning(self, message: str) -> None:
        """Display a single warning message.
        
        Args:
            message: Warning message to display.
        """
        if not self.quiet:
            print(f"⚠️  {message}")
    
    def success(self, message: str) -> None:
        """Display a success message.
        
        Args:
            message: Success message to display.
        """
        if not self.quiet:
            print(f"✅ {message}")
    
    def info(self, message: str) -> None:
        """Display an informational message.
        
        Args:
            message: Info message to display.
        """
        if not self.quiet:
            print(f"ℹ️  {message}")
    
    def progress(self, message: str) -> None:
        """Display a progress message.
        
        Args:
            message: Progress message to display.
        """
        if not self.quiet:
            print(f"⏳ {message}")
    
    def detail(self, message: str) -> None:
        """Display a detail message (indented, for additional context).
        
        Args:
            message: Detail message to display.
        """
        if not self.quiet:
            print(f"   {message}")
    
    def plain(self, message: str) -> None:
        """Display a plain message without emoji.
        
        Args:
            message: Plain message to display.
        """
        if not self.quiet:
            print(message)
