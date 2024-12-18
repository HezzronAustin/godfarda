# Utils Package

This package contains utility modules that provide common functionality across the Godfarda system.

## Modules

### logging_config.py

Provides centralized logging configuration for the entire application.

#### Features
- Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- Multiple output handlers:
  - Console output for immediate feedback
  - Rotating file handler for general logs
  - Separate rotating file handler for errors
- Daily log files with timestamps
- Automatic log rotation (10MB max size, 5 backups)
- UTF-8 encoding support
- Exception tracebacks in error logs
- Performance metrics logging

#### Usage
```python
from src.utils.logging_config import setup_logging

# Initialize logging system
setup_logging(log_dir="logs")  # Default directory is "logs"

# Get logger for your module
logger = logging.getLogger('your_module_name')

# Use the logger
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message", exc_info=True)  # Include traceback
```

#### Potential Improvements
1. Configuration File Support
   - Add support for loading logging configuration from YAML/JSON files
   - Allow runtime configuration updates

2. Enhanced Monitoring
   - Add metrics collection for log events
   - Implement log aggregation support
   - Add support for external logging services

3. Security Enhancements
   - Add log encryption options
   - Implement log integrity verification
   - Add sensitive data masking

4. Performance Optimizations
   - Implement async logging
   - Add batch logging support
   - Optimize file I/O operations

5. Additional Features
   - Add structured logging support (JSON format)
   - Implement log forwarding to external services
   - Add log compression for archived logs
   - Add log search and analysis tools

## Adding New Utilities

When adding new utility modules:
1. Create the module file in the `utils` directory
2. Add comprehensive documentation
3. Include usage examples
4. Update this README with module information
5. Add appropriate tests in the test suite

## Best Practices

1. Keep utility functions focused and single-purpose
2. Maintain comprehensive documentation
3. Include type hints for better code clarity
4. Write unit tests for all utilities
5. Follow the project's logging standards
6. Handle errors appropriately
7. Include performance considerations in documentation
