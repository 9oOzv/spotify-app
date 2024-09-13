#!/usr/bin/env python3
import logging
from logging import (
    Logger,
    getLogger
)
import json
import os
import sys
from util import truncate
from functools import wraps

TRACE = 5

default_level = (
    TRACE
    if os.getenv('TRACE')
    else logging.DEBUG
    if os.getenv('DEBUG')
    else logging.INFO
)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        data = (
            {'message': str(record.msg)}
            if not isinstance(record.msg, dict)
            else record.msg
        )
        log = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'file': f"{record.filename}",
            'line': f"{record.lineno}",
            'function': f"{record.funcName}",
            **data
        }
        if record.exc_info:
            log['exception'] = self.formatException(record.exc_info)
        return json.dumps(log, default=str)


def setup_logger(
    level: int = default_level,
    name: str = None
):
    log = (
        getLogger(name)
        if name
        else logging.getLogger()
    )
    root = logging.getLogger()
    formatter = JsonFormatter()
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    log.name = name
    log.setLevel(level)
    for handler in root.handlers:
        root.removeHandler(handler)
    root.addHandler(handler)
    root.setLevel(level)

    def trace(message, *args, **kwargs):
        if log.isEnabledFor(TRACE):
            log._log(TRACE, message, args, **kwargs, stacklevel=1)
    log.trace = trace
    return log


def get_logger(name: str = None):
    log = (
        getLogger(name)
        if name
        else logging.getLogger()
    )
    if not hasattr(log, 'trace'):
        setup_logger(name=name)
    return log


def trace_args(
    log: Logger = getLogger(),
    max_value_len: int = 1024
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            log.trace(
                {
                    'message': 'Args trace',
                    'traced_function': func.__name__,
                    'traced_file': func.__code__.co_filename,
                    'traced_line': func.__code__.co_firstlineno,
                    'args': [
                        truncate(arg, max_value_len)
                        for arg in args
                    ],
                    'kwargs': kwargs
                }
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def trace_return(
    log: Logger = getLogger(),
    max_value_len: int = 1024
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ret = func(*args, **kwargs)
            log.trace(
                {
                    'message': 'Return trace',
                    'traced_function': func.__name__,
                    'traced_file': func.__code__.co_filename,
                    'traced_line': func.__code__.co_firstlineno,
                    'return': truncate(ret, max_value_len)
                }
            )
            return ret
        return wrapper
    return decorator


def trace_func(
    log: Logger = getLogger(),
    max_value_len: int = 1024
):
    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            log.trace(
                {
                    'message': 'Args trace',
                    'traced_function': func.__name__,
                    'traced_file': func.__code__.co_filename,
                    'traced_line': func.__code__.co_firstlineno,
                    'args': [
                        truncate(arg, max_value_len)
                        for arg in args
                    ],
                    'kwargs': {
                        k: truncate(v, max_value_len)
                        for k, v in kwargs.items()
                    }
                }
            )
            ret = func(*args, **kwargs)
            log.trace(
                {
                    'message': 'Return trace',
                    'traced_function': func.__name__,
                    'traced_file': func.__code__.co_filename,
                    'traced_line': func.__code__.co_firstlineno,
                    'return': truncate(ret, max_value_len)
                }
            )
            return ret
        return wrapper
    return decorator


def trace_funcname(
    log: Logger = getLogger()
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            log.trace({
                'message': 'Function trace',
                'traced_function': func.__name__,
                'traced_file': func.__code__.co_filename,
                'traced_line': func.__code__.co_firstlineno,
            })
            return func(*args, **kwargs)
        return wrapper
    return decorator


if __name__ == '__main__':
    for line in sys.stdin:
        try:
            print(json.dumps(json.loads(line), indent=2), file=sys.stderr)
        except json.JSONDecodeError:
            print(line, file=sys.stderr)

