import logging
import coloredlogs
import inspect
import os
import sys
from functools import wraps
from pathlib import Path
import atexit
import tempfile
from datetime import datetime

def handle_recursion(func):
    """Decorator to handle potential recursion errors in logging functions"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Check if we're already in a recursion error state
        if getattr(self, '_in_recursion_error', False):
            return  # Silently return without logging
            
        try:
            # Set a lower recursion limit temporarily to catch issues early
            original_limit = sys.getrecursionlimit()
            sys.setrecursionlimit(50)  # Lower limit for logging operations
            
            result = func(self, *args, **kwargs)
            
            # Restore original limit
            sys.setrecursionlimit(original_limit)
            return result
            
        except RecursionError:
            # Mark that we're in a recursion error state
            self._in_recursion_error = True
            
            # If recursion occurs, fall back to basic logging
            sys.setrecursionlimit(original_limit)  # Restore limit
            basic_msg = f"RECURSION ERROR while logging: {args[0] if args else ''}"
            try:
                # Try to log without any formatting or caller info
                self.logger.log(logging.ERROR, basic_msg)
            except:
                # Last resort - app_logger.info to stderr
                app_logger.info(basic_msg, file=sys.stderr)
            
            # Reset the recursion error state after handling
            self._in_recursion_error = False
            
        except Exception as e:
            sys.setrecursionlimit(original_limit)  # Restore limit
            app_logger.info(f"Logging error: {str(e)}", file=sys.stderr)

    return wrapper

class Logger:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self, name='OllamaDesktop', log_level=logging.INFO, exc_info=True):
        if not hasattr(self, 'initialized'):
            self.logger = logging.getLogger(name)
            self.logger.setLevel(log_level)
            
            # Ensure logger doesn't duplicate handlers
            if not self.logger.handlers:
                try:
                    # Get the log directory path
                    self.logs_dir = self._get_logs_directory()
                    self.logs_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Create rotating file handler
                    self._setup_file_handler()
                    
                    # Create console handler for development
                    if not getattr(sys, 'frozen', False):
                        self._setup_console_handler()
                    
                    # Register cleanup handler
                    atexit.register(self._cleanup_old_logs)
                    
                except Exception as e:
                    # Fallback to temporary directory if standard location fails
                    self._setup_fallback_logging()
                    
            self.initialized = True
            self._recursion_guard = False

    def _get_logs_directory(self):
        """Get the appropriate logs directory based on whether running as exe or script"""
        if getattr(sys, 'frozen', False):
            # If running as exe, use AppData
            base_dir = Path(os.getenv('APPDATA')) / 'ollama_desktop' / 'logs'
        else:
            # If running as script, use local logs directory
            base_dir = Path(__file__).parent.parent / 'logs'
        return base_dir

    def _setup_file_handler(self):
        """Setup the main file handler with rotation"""
        try:
            # Create log file with timestamp
            timestamp = datetime.now().strftime('%Y%m%d')
            log_file = self.logs_dir / f'app_{timestamp}.log'
            
            # Create file handler with UTF-8 encoding and immediate flush
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            # Simplified formatter
            file_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            
            # Enable immediate flushing
            file_handler.flush = lambda: True
            
            # Add handler to logger
            self.logger.addHandler(file_handler)
            
        except Exception as e:
            sys.stderr.write(f"Failed to setup file handler: {str(e)}\n")
            self._setup_fallback_logging()

    def _setup_console_handler(self):
        """Setup colored console output for development"""
        try:
            coloredlogs.install(
                level=self.logger.level,
                logger=self.logger,
                fmt='%(name)s - %(levelname)s - %(message)s',
                level_styles={
                    'debug': {'color': 'cyan', 'bold': True},
                    'info': {'color': 'green', 'bold': True}, 
                    'warning': {'color': 'yellow', 'bold': True},
                    'error': {'color': 'red', 'bold': True},
                    'critical': {'color': 'magenta', 'bold': True, 'background': 'red'},
                }
            )
        except Exception as e:
            sys.stderr.write(f"Failed to setup console handler: {str(e)}\n")

    def _setup_fallback_logging(self):
        """Setup fallback logging to temporary directory"""
        try:
            temp_dir = tempfile.gettempdir()
            fallback_log = os.path.join(temp_dir, 'ollama_desktop_fallback.log')
            
            # Create basic file handler
            handler = logging.FileHandler(fallback_log)
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            
            self.logger.addHandler(handler)
            self.logger.warning(f"Using fallback logging to: {fallback_log}")
            
        except Exception as e:
            sys.stderr.write(f"Failed to setup fallback logging: {str(e)}\n")

    def _cleanup_old_logs(self):
        """Clean up old log files (keeping last 7 days)"""
        try:
            if self.logs_dir.exists():
                current_time = datetime.now()
                for log_file in self.logs_dir.glob('app_*.log'):
                    try:
                        # Parse timestamp from filename
                        timestamp_str = log_file.stem.split('_')[1]
                        file_date = datetime.strptime(timestamp_str, '%Y%m%d')
                        
                        # Remove if older than 7 days
                        if (current_time - file_date).days > 7:
                            log_file.unlink()
                    except Exception:
                        continue
        except Exception:
            pass  # Silently fail cleanup

    def _get_caller_info(self):
        """Get the caller's frame info, handling potential recursion errors"""
        frame = None
        caller_frame = None
        try:
            # Get the caller's frame info, skipping this function and the logging function
            frame = inspect.currentframe()
            if frame is None:
                return "unknown", "unknown"
            
            # Navigate up the call stack safely
            for _ in range(3):  # Skip decorator, logging method, and this function
                if frame.f_back is None:
                    return "unknown", "unknown"
                frame = frame.f_back
            
            filename = os.path.split(frame.f_code.co_filename)[1]
            func_name = frame.f_code.co_name
            
            return filename, func_name
            
        except Exception:
            return "unknown", "unknown"
        finally:
            # Clean up frames to prevent reference cycles
            del frame
            if caller_frame:
                del caller_frame

    @handle_recursion
    def debug(self, message, exc_info=True):
        try:
            filename, func_name = self._get_caller_info()
            self.logger.debug(f"[{filename}:{func_name}] {message}")
        except Exception:
            self.logger.debug(str(message))

    @handle_recursion
    def info(self, message, exc_info=True):
        try:
            filename, func_name = self._get_caller_info()
            self.logger.info(f"[{filename}:{func_name}] {message}")
        except Exception:
            self.logger.info(str(message))

    @handle_recursion
    def warning(self, message, exc_info=True):
        try:
            filename, func_name = self._get_caller_info()
            self.logger.warning(f"[{filename}:{func_name}] {message}")
        except Exception:
            self.logger.warning(str(message))

    @handle_recursion
    def error(self, message, exc_info=True):
        try:
            filename, func_name = self._get_caller_info()
            self.logger.error(f"[{filename}:{func_name}] {message}", exc_info=exc_info)
        except Exception:
            self.logger.error(str(message), exc_info=exc_info)

    @handle_recursion
    def critical(self, message, exc_info=True):
        try:
            filename, func_name = self._get_caller_info()
            self.logger.critical(f"[{filename}:{func_name}] {message}")
        except Exception:
            self.logger.critical(str(message))

# Create a global logger instance
app_logger = Logger()

# Usage example:
# from utils.logger import app_logger
# app_logger.info("This is an info message")
