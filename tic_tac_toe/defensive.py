import functools
import os
import traceback
from typing import Any, Callable


def defensive(print_fn: Callable = print) -> Callable:
    """
    Close program when thread raise exception
    Notes:
        doesn't support multiprocessing
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapped(  # pylint:disable=inconsistent-return-statements
                *args, **kwargs
        ) -> Any:

            try:
                return func(*args, **kwargs)
            except:  # pylint: disable=bare-except
                print_fn("Going down... :(")
                print_fn(traceback.format_exc())  # pylint:  disable=bare-except
                print_fn("Bye!")
                os.kill(os.getpid(), 9)

        return wrapped

    return decorator
