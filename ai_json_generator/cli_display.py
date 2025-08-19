#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI Display module for beautiful output and progress indicators.
"""

import logging
import sys
import time
from typing import Optional, Any
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.status import Status
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich import box

# Initialize Rich Console
console = Console()

class ColoredFormatter(logging.Formatter):
    """Custom formatter for colored log messages in debug mode."""
    
    def format(self, record):
        # Add color codes based on level
        if record.levelno >= logging.ERROR:
            record.levelname = f"[bold red]{record.levelname}[/bold red]"
        elif record.levelno >= logging.WARNING:
            record.levelname = f"[bold yellow]{record.levelname}[/bold yellow]"
        elif record.levelno >= logging.INFO:
            record.levelname = f"[bold blue]{record.levelname}[/bold blue]"
        else:
            record.levelname = f"[dim]{record.levelname}[/dim]"
        
        return super().format(record)

class CLIDisplay:
    """Enhanced CLI display manager with beautiful output and progress indicators."""
    
    def __init__(self, debug: bool = False, quiet: bool = False):
        self.debug_mode = debug
        self.quiet = quiet
        self.console = console
        self.logger = None
        self._setup_logging()
        
    def _setup_logging(self):
        """Set up logging with appropriate level and handlers."""
        # Remove existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Set logging level
        if self.debug_mode:
            level = logging.DEBUG
        elif self.quiet:
            level = logging.WARNING
        else:
            level = logging.INFO
        
        # Create Rich handler
        rich_handler = RichHandler(
            console=self.console,
            rich_tracebacks=True,
            show_path=self.debug,
            show_time=self.debug,
            markup=True
        )
        
        # Set format based on debug mode
        if self.debug_mode:
            format_str = "[%(name)s] %(levelname)s %(message)s"
        else:
            format_str = "%(message)s"
        
        rich_handler.setFormatter(logging.Formatter(format_str))
        
        # Configure root logger
        logging.basicConfig(
            level=level,
            format=format_str,
            handlers=[rich_handler]
        )
        
        self.logger = logging.getLogger('ai_json_generator')
    
    def info(self, message: str, **kwargs):
        """Display info message."""
        if not self.quiet:
            if self.debug_mode:
                self.logger.info(f"[bold blue]ℹ️[/bold blue] {message}", extra={"markup": True})
            else:
                self.console.print(f"[bold blue]ℹ️[/bold blue] {message}", **kwargs)
    
    def success(self, message: str, **kwargs):
        """Display success message."""
        if not self.quiet:
            self.console.print(f"[bold green]✅[/bold green] {message}", **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Display warning message."""
        self.console.print(f"[bold yellow]⚠️[/bold yellow] {message}", **kwargs)
    
    def error(self, message: str, **kwargs):
        """Display error message."""
        self.console.print(f"[bold red]❌[/bold red] {message}", **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Display debug message."""
        if self.debug_mode:
            self.logger.debug(f"[dim]🔍[/dim] {message}", extra={"markup": True})
    
    def print_header(self, title: str, subtitle: Optional[str] = None):
        """Print a beautiful header."""
        if self.quiet:
            return
            
        header_text = Text(title, style="bold magenta")
        if subtitle:
            header_text.append(f"\n{subtitle}", style="dim")
        
        panel = Panel(
            header_text,
            box=box.DOUBLE,
            padding=(1, 2),
            style="magenta"
        )
        self.console.print(panel)
    
    def print_config_info(self, config: dict):
        """Print configuration information in a beautiful table."""
        if self.quiet:
            return
            
        if self.debug_mode:
            table = Table(title="[bold blue]🔧 Configuration[/bold blue]", box=box.ROUNDED)
            table.add_column("Setting", style="cyan", no_wrap=True)
            table.add_column("Value", style="white")
            
            # Show important config items
            important_keys = ['model', 'api_url', 'max_tokens', 'temperature']
            for key in important_keys:
                if key in config:
                    value = str(config[key])
                    if key == 'api_url' and len(value) > 50:
                        value = value[:47] + "..."
                    table.add_row(key, value)
            
            self.console.print(table)
        else:
            # Simple one-line info in normal mode
            model = config.get('model', 'Unknown')
            self.info(f"Using model: [bold cyan]{model}[/bold cyan]")
    
    def print_generation_start(self, operator: str, output_dir: str):
        """Print generation start information."""
        if self.quiet:
            return
            
        if operator:
            self.info(f"Generating test case for operator: [bold cyan]{operator}[/bold cyan]")
        else:
            self.info("Generating test case with custom requirements")
        
        if self.debug_mode:
            self.debug(f"Output directory: {output_dir}")
    
    def create_llm_progress(self, initial_status: str = "Connecting to LLM...") -> 'LLMProgress':
        """Create a progress indicator for LLM operations."""
        return LLMProgress(self.console, self.quiet, initial_status)
    
    def print_file_saved(self, file_path: str, file_type: str = "file"):
        """Print file saved message."""
        if self.debug_mode:
            self.success(f"Saved {file_type}: [bold cyan]{file_path}[/bold cyan]")
        else:
            self.success(f"Generated {file_type}")
    
    def print_summary(self, success: bool, details: Optional[str] = None):
        """Print operation summary."""
        if success:
            self.success("✨ Operation completed successfully!")
        else:
            self.error("💥 Operation failed")
        
        if details and (self.debug_mode or not success):
            self.console.print(f"[dim]{details}[/dim]")

class LLMProgress:
    """Progress indicator specifically for LLM operations with thinking visualization."""
    
    def __init__(self, console: Console, quiet: bool = False, initial_status: str = "Initializing..."):
        self.console = console
        self.quiet = quiet
        self.status = None
        self.current_line = ""
        self.thinking_chars = ["🤔", "💭", "🧠", "⚡", "✨"]
        self.thinking_idx = 0
        
        if not quiet:
            self.status = Status(initial_status, console=console, spinner="dots")
    
    def __enter__(self):
        if self.status:
            self.status.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.status:
            self.status.stop()
    
    def update_connecting(self):
        """Update status to show connecting."""
        if self.status:
            self.status.update("⚡ Connecting to LLM...")
    
    def update_thinking(self, thinking_text: str):
        """Update status to show thinking process."""
        if self.status:
            # Cycle through thinking emojis
            emoji = self.thinking_chars[self.thinking_idx % len(self.thinking_chars)]
            self.thinking_idx += 1
            
            # Truncate thinking text to fit in one line
            display_text = thinking_text.replace('\n', ' ').strip()
            if len(display_text) > 80:
                display_text = display_text[:77] + "..."
            
            self.status.update(f"{emoji} [bold blue]思考中[/bold blue]: {display_text}")
    
    def update_generating(self):
        """Update status to show generation process."""
        if self.status:
            self.status.update("🚀 [bold green]生成中[/bold green]: 正在生成JSON内容...")
    
    def update_complete(self):
        """Update status to show completion."""
        if self.status:
            self.status.update("✅ [bold green]完成[/bold green]!")
            # Give a moment to see the completion status
            time.sleep(0.5)
    
    def update_custom(self, message: str, emoji: str = "⚙️"):
        """Update with custom message."""
        if self.status:
            self.status.update(f"{emoji} {message}")

class ConversionProgress:
    """Progress indicator for ONNX conversion operations."""
    
    def __init__(self, console: Console, quiet: bool = False):
        self.console = console
        self.quiet = quiet
        self.progress = None
        
    def __enter__(self):
        if not self.quiet:
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TimeElapsedColumn(),
                console=self.console,
                transient=False
            )
            self.progress.start()
            self.task = self.progress.add_task("🔄 Converting to ONNX...", total=None)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.progress:
            self.progress.stop()
    
    def update(self, description: str):
        """Update conversion progress description."""
        if self.progress:
            self.progress.update(self.task, description=description)
    
    def complete(self, success: bool = True):
        """Mark conversion as complete."""
        if self.progress:
            if success:
                self.progress.update(self.task, description="✅ ONNX conversion completed!")
            else:
                self.progress.update(self.task, description="❌ ONNX conversion failed!")
            time.sleep(0.5)

# Global display instance
_display_instance = None

def get_display() -> CLIDisplay:
    """Get the global display instance."""
    global _display_instance
    if _display_instance is None:
        _display_instance = CLIDisplay()
    return _display_instance

def setup_display(debug: bool = False, quiet: bool = False) -> CLIDisplay:
    """Setup the global display instance with specific settings."""
    global _display_instance
    _display_instance = CLIDisplay(debug=debug, quiet=quiet)
    return _display_instance
