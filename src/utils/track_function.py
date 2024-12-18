def track_function(func: Callable) -> Callable:
    """Decorator to track function inputs and outputs"""
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        function_name = func.__name__
        
        # Format input args and kwargs
        args_str = [_to_serializable(arg) for arg in args[1:]]  # Skip self
        kwargs_str = {k: _to_serializable(v) for k, v in kwargs.items()}
        input_data = {"args": args_str, "kwargs": kwargs_str}
        
        logger.info(f"[FUNCTION_START] {function_name}")
        logger.info(f"[FUNCTION_INPUT] {function_name}: {json.dumps(input_data, indent=2)}")
        
        try:
            result = await func(*args, **kwargs)
            
            # Format output
            output_data = _to_serializable(result)
            
            execution_time = time.time() - start_time
            logger.info(f"[FUNCTION_OUTPUT] {function_name}: {json.dumps(output_data, indent=2)}")
            logger.info(f"[FUNCTION_END] {function_name} - Execution time: {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"[FUNCTION_ERROR] {function_name}: {str(e)}", exc_info=True)
            raise
            
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        function_name = func.__name__
        
        # Format input args and kwargs
        args_str = [_to_serializable(arg) for arg in args[1:]]  # Skip self
        kwargs_str = {k: _to_serializable(v) for k, v in kwargs.items()}
        input_data = {"args": args_str, "kwargs": kwargs_str}
        
        logger.info(f"[FUNCTION_START] {function_name}")
        logger.info(f"[FUNCTION_INPUT] {function_name}: {json.dumps(input_data, indent=2)}")
        
        try:
            result = func(*args, **kwargs)
            
            # Format output
            output_data = _to_serializable(result)
            
            execution_time = time.time() - start_time
            logger.info(f"[FUNCTION_OUTPUT] {function_name}: {json.dumps(output_data, indent=2)}")
            logger.info(f"[FUNCTION_END] {function_name} - Execution time: {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"[FUNCTION_ERROR] {function_name}: {str(e)}", exc_info=True)
            raise
            
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
